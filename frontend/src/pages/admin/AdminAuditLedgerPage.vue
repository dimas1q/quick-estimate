<template>
  <div class="max-w-6xl mx-auto px-4 py-8 space-y-6">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Аудит</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Журнал действий
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <button class="qe-btn px-4 py-2 text-sm" @click="runVerification" :disabled="isVerifying">
          {{ isVerifying ? 'Проверка...' : 'Проверить целостность' }}
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-5 gap-3">
      <input v-model.trim="filters.action" class="qe-input md:col-span-2" type="text" placeholder="action, напр. estimate.deleted" @keyup.enter="loadLedger(1)" />
      <input v-model.trim="filters.entity_type" class="qe-input" type="text" placeholder="entity_type" @keyup.enter="loadLedger(1)" />
      <input v-model.trim="filters.entity_id" class="qe-input" type="text" placeholder="entity_id" @keyup.enter="loadLedger(1)" />
      <button class="qe-btn" @click="loadLedger(1)" :disabled="isLoading">Найти</button>
    </div>

    <div v-if="verification" class="rounded-2xl border p-4" :class="verification.is_valid
      ? 'border-green-200 bg-green-50 dark:border-green-900/40 dark:bg-green-900/20'
      : 'border-red-200 bg-red-50 dark:border-red-900/40 dark:bg-red-900/20'">
      <p class="text-sm font-semibold" :class="verification.is_valid ? 'text-green-700 dark:text-green-300' : 'text-red-700 dark:text-red-300'">
        {{ verification.is_valid ? 'Цепочка целостна' : 'Найдена проблема в цепочке' }}
      </p>
      <p class="mt-1 text-xs text-gray-600 dark:text-gray-300">Проверено записей: {{ verification.checked_entries }}</p>
      <p v-if="!verification.is_valid" class="mt-1 text-xs text-red-700 dark:text-red-300">
        ID записи: {{ verification.broken_entry_id }}; причина: {{ verification.reason }}
      </p>
      <p class="mt-1 text-xs text-gray-500 dark:text-gray-400 break-all">Последний hash: {{ verification.latest_hash || '—' }}</p>
    </div>

    <div class="rounded-2xl border border-gray-200 dark:border-qe-black2 bg-white dark:bg-qe-black3 shadow-sm overflow-x-auto">
      <table class="min-w-full text-sm">
        <thead class="bg-gray-50 dark:bg-qe-black2 text-gray-600 dark:text-gray-300">
          <tr>
            <th class="px-4 py-3 text-left font-semibold">ID</th>
            <th class="px-4 py-3 text-left font-semibold">Время</th>
            <th class="px-4 py-3 text-left font-semibold">Пользователь</th>
            <th class="px-4 py-3 text-left font-semibold">Action</th>
            <th class="px-4 py-3 text-left font-semibold">Entity</th>
            <th class="px-4 py-3 text-left font-semibold">Path</th>
            <th class="px-4 py-3 text-left font-semibold">Hash</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in entries" :key="entry.id" class="border-t border-gray-100 dark:border-qe-black2 align-top">
            <td class="px-4 py-3 text-xs text-gray-500">{{ entry.id }}</td>
            <td class="px-4 py-3 text-xs text-gray-700 dark:text-gray-300 whitespace-nowrap">{{ formatDate(entry.occurred_at) }}</td>
            <td class="px-4 py-3 text-xs text-gray-700 dark:text-gray-300">
              <p>{{ entry.actor_login || 'system' }}</p>
              <p class="text-gray-500">{{ entry.actor_email || '—' }}</p>
            </td>
            <td class="px-4 py-3 text-xs font-medium text-gray-900 dark:text-white">{{ entry.action }}</td>
            <td class="px-4 py-3 text-xs text-gray-700 dark:text-gray-300">
              <p>{{ entry.entity_type }}: {{ entry.entity_id || '—' }}</p>
              <details class="mt-1" v-if="entry.details">
                <summary class="cursor-pointer text-blue-600">details</summary>
                <pre class="mt-1 max-w-xs whitespace-pre-wrap break-all text-[11px] text-gray-600 dark:text-gray-300">{{ stringify(entry.details) }}</pre>
              </details>
            </td>
            <td class="px-4 py-3 text-xs text-gray-700 dark:text-gray-300 break-all">{{ entry.request_path || '—' }}</td>
            <td class="px-4 py-3 text-[11px] text-gray-500 dark:text-gray-400 break-all">{{ entry.entry_hash }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="!isLoading && entries.length === 0" class="text-center text-gray-400 border border-gray-200 dark:border-qe-black2 p-6 rounded-2xl bg-white/70 dark:bg-qe-black2/80">
      Записи аудита отсутствуют.
    </div>

    <QePagination :total="total" :per-page="perPage" :page="currentPage" @update:page="loadLedger" class="pt-1" />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useToast } from 'vue-toastification'

import QePagination from '@/components/QePagination.vue'
import { getApiErrorMessage } from '@/lib/api-error'
import { useAdminStore } from '@/store/admin'

const store = useAdminStore()
const toast = useToast()

const perPage = 50
const currentPage = ref(1)
const total = ref(0)
const entries = ref([])
const isLoading = ref(false)
const isVerifying = ref(false)
const verification = ref(null)

const filters = ref({
  action: '',
  entity_type: '',
  entity_id: ''
})

function buildParams(page = currentPage.value) {
  return {
    page,
    limit: perPage,
    action: filters.value.action || undefined,
    entity_type: filters.value.entity_type || undefined,
    entity_id: filters.value.entity_id || undefined
  }
}

async function loadLedger(page = currentPage.value) {
  currentPage.value = page
  isLoading.value = true
  try {
    const res = await store.fetchAuditLedger(buildParams(page))
    entries.value = res.items
    total.value = res.total
  } catch (error) {
    toast.error(getApiErrorMessage(error, 'Не удалось загрузить журнал аудита'))
  } finally {
    isLoading.value = false
  }
}

async function runVerification() {
  if (isVerifying.value) return
  isVerifying.value = true
  try {
    verification.value = await store.verifyAuditLedger()
    if (verification.value?.is_valid) {
      toast.success('Цепочка аудита целостна')
    } else {
      toast.error('Цепочка аудита нарушена')
    }
  } catch (error) {
    toast.error(getApiErrorMessage(error, 'Не удалось проверить цепочку аудита'))
  } finally {
    isVerifying.value = false
  }
}

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleString('ru-RU')
}

function stringify(value) {
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

onMounted(() => {
  loadLedger(1)
})
</script>
