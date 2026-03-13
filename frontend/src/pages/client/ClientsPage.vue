<template>
  <div class="flex flex-col items-center from-gray-50 via-white to-gray-100 py-10">
    <!-- Хедер и бар фильтров -->
    <div class="w-full max-w-6xl flex flex-col gap-4 mb-8">
      <div class="flex items-center justify-between mb-2">
        <h2 class="text-2xl font-bold">Клиенты</h2>
        <div class="flex items-center gap-2">
          <div class="flex items-center gap-1 rounded-xl bg-gray-100 p-1 dark:bg-qe-black2">
            <button @click="viewMode = 'list'" :class="[
              'rounded-lg px-3 py-1.5 text-sm font-semibold transition',
              viewMode === 'list'
                ? 'bg-white text-blue-600 shadow dark:bg-qe-black3'
                : 'text-gray-500 hover:text-blue-600',
            ]">
              Список
            </button>
            <button @click="viewMode = 'pipeline'" :class="[
              'rounded-lg px-3 py-1.5 text-sm font-semibold transition',
              viewMode === 'pipeline'
                ? 'bg-white text-blue-600 shadow dark:bg-qe-black3'
                : 'text-gray-500 hover:text-blue-600',
            ]">
              Воронка
            </button>
          </div>
          <router-link to="/clients/create" class="qe-btn px-4">Добавить клиента</router-link>
        </div>
      </div>
      <div class="flex gap-2">
        <input v-model="filters.name" class="qe-input flex-1" type="text" autocomplete="off"
          placeholder="Контактное лицо" />
        <input v-model="filters.company" class="qe-input flex-1" type="text" autocomplete="off"
          placeholder="Компания" />
        <input v-model="filters.email" class="qe-input flex-1" type="text" autocomplete="off" placeholder="Email" />
        <button @click="applyFilters" class="qe-btn min-w-[100px]">Найти</button>
        <button @click="resetFilters" class="qe-btn-secondary min-w-[100px]">Сброс</button>
      </div>
    </div>

    <!-- Список клиентов -->
    <div v-if="viewMode === 'list'" class="w-full max-w-6xl">
      <div v-if="isLoading" class="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div v-for="n in 5" :key="n" class="rounded-2xl bg-white/60 shadow animate-pulse p-6 h-24" />
      </div>
      <template v-else>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div v-for="c in store.clients" :key="c.id"
            class="flex items-center gap-5 bg-white rounded-2xl shadow-sm hover:shadow-lg border border-gray-200 p-5 transition-all border border-gray-100 dark:bg-qe-black3 dark:border-qe-black2">
            <div
              class="flex-shrink-0 w-12 h-12 rounded-full dark:bg-qe-black2 bg-gray-100 flex items-center justify-center text-xl font-bold text-gray-500">
              <!-- Lucide icon: user -->
              <LucideUser class="w-7 h-7" />
            </div>
            <div class="flex-1 min-w-0">
              <router-link :to="`/clients/${c.id}`" class="text-lg font-semibold truncate hover:text-blue-600">{{ c.name }}
              </router-link>
              <div class="mt-1 flex items-center gap-2">
                <span class="truncate text-gray-500 text-sm">{{ c.company || '—' }}</span>
                <span class="rounded-full px-2 py-0.5 text-[10px] font-semibold" :class="pipelineStageBadgeClass(c.pipeline_stage)">
                  {{ pipelineStageLabel(c.pipeline_stage) }}
                </span>
              </div>
              <div class="text-gray-400 text-xs truncate">{{ c.email || c.phone || '—' }}</div>
            </div>
          </div>
        </div>
        <div v-if="store.clients.length === 0"
          class="text-center text-gray-400 border border-gray-200 dark:border-qe-black2 p-6 rounded-2xl bg-white/70 dark:bg-qe-black2/80 mt-4">
          {{ hasCurrentWorkspace ? 'Клиенты отсутствуют.' : 'Не выбрано рабочее пространство.' }}
        </div>
        <QePagination :total="totalClients" :per-page="perPage" :page="currentPage" @update:page="changePage"
          class="mt-6" />
      </template>
    </div>

    <div v-else class="w-full max-w-6xl">
      <ClientPipelineBoard :pipeline="pipelineData" :loading="pipelineLoading" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useClientsStore } from '@/store/clients'
import { useAuthStore } from '@/store/auth'
import { useToast } from 'vue-toastification'
import { isWorkspaceNotSelectedError } from '@/lib/workspace-state'
import QePagination from '@/components/QePagination.vue'
import ClientPipelineBoard from '@/components/ClientPipelineBoard.vue'

import { LucideUser } from 'lucide-vue-next'

const store = useClientsStore()
const auth = useAuthStore()
const toast = useToast()
const isLoading = ref(true)
const pipelineLoading = ref(true)
const viewMode = ref('list')
const filters = ref({
  name: '',
  company: '',
  email: ''
})
const pipelineData = ref({
  summary: {
    lead_count: 0,
    quote_count: 0,
    approved_count: 0,
    paid_count: 0,
    total_expected_revenue: 0,
    weighted_forecast: 0
  },
  items: []
})

const perPage = 5
const currentPage = ref(1)
const currentFilters = ref({})
const totalClients = computed(() => store.total)
const currentWorkspaceId = computed(() => {
  const current = (auth.workspaces || []).find((workspace) => workspace.is_current)
  return current?.organization_id ?? null
})
const hasCurrentWorkspace = computed(() => Boolean(currentWorkspaceId.value))

function resetWorkspaceBoundState() {
  store.clients = []
  store.total = 0
  pipelineData.value = {
    summary: {
      lead_count: 0,
      quote_count: 0,
      approved_count: 0,
      paid_count: 0,
      total_expected_revenue: 0,
      weighted_forecast: 0
    },
    items: []
  }
}

async function loadInitialData() {
  try {
    await auth.fetchWorkspaces()
  } catch {
    auth.workspaces = []
  }
  if (!hasCurrentWorkspace.value) {
    resetWorkspaceBoundState()
    isLoading.value = false
    pipelineLoading.value = false
    return
  }
  isLoading.value = true
  pipelineLoading.value = true
  try {
    const query = buildFilterQuery()
    await Promise.all([
      store.fetchClients({ ...query, page: currentPage.value, limit: perPage }),
      fetchPipeline(query)
    ])
    currentFilters.value = {}
  } catch (error) {
    if (isWorkspaceNotSelectedError(error)) {
      try {
        await auth.fetchUser()
      } catch {
        auth.workspaces = []
      }
      resetWorkspaceBoundState()
    } else {
      toast.error('Не удалось загрузить список клиентов')
    }
  } finally {
    isLoading.value = false
    pipelineLoading.value = false
  }
}

onMounted(async () => {
  await loadInitialData()
})

watch(
  () => currentWorkspaceId.value,
  async () => {
    currentPage.value = 1
    currentFilters.value = {}
    await loadInitialData()
  }
)

function buildFilterQuery() {
  return {
    name: filters.value.name,
    company: filters.value.company,
    email: filters.value.email
  }
}

async function fetchPipeline(query = {}) {
  if (!hasCurrentWorkspace.value) {
    resetWorkspaceBoundState()
    pipelineLoading.value = false
    return
  }
  pipelineLoading.value = true
  try {
    pipelineData.value = await store.fetchClientsPipeline(query)
  } catch (error) {
    if (isWorkspaceNotSelectedError(error)) {
      resetWorkspaceBoundState()
      return
    }
    throw error
  } finally {
    pipelineLoading.value = false
  }
}

async function applyFilters() {
  if (!hasCurrentWorkspace.value) {
    resetWorkspaceBoundState()
    return
  }
  isLoading.value = true
  const query = buildFilterQuery()
  currentFilters.value = query
  currentPage.value = 1
  try {
    await Promise.all([
      store.fetchClients({ ...query, page: currentPage.value, limit: perPage }),
      fetchPipeline(query)
    ])
  } catch (error) {
    if (isWorkspaceNotSelectedError(error)) {
      await loadInitialData()
      return
    }
    toast.error('Не удалось применить фильтры')
  }
  isLoading.value = false
}

async function resetFilters() {
  if (!hasCurrentWorkspace.value) {
    resetWorkspaceBoundState()
    return
  }
  isLoading.value = true
  filters.value = { name: '', company: '', email: '' }
  currentFilters.value = {}
  currentPage.value = 1
  try {
    await Promise.all([
      store.fetchClients({ page: currentPage.value, limit: perPage }),
      fetchPipeline()
    ])
  } catch (error) {
    if (isWorkspaceNotSelectedError(error)) {
      await loadInitialData()
      return
    }
    toast.error('Не удалось сбросить фильтры')
  }
  isLoading.value = false
}

async function changePage(p) {
  if (!hasCurrentWorkspace.value) {
    resetWorkspaceBoundState()
    return
  }
  currentPage.value = p
  try {
    await store.fetchClients({ ...currentFilters.value, page: p, limit: perPage })
  } catch (error) {
    if (isWorkspaceNotSelectedError(error)) {
      await loadInitialData()
      return
    }
    toast.error('Не удалось загрузить страницу клиентов')
  }
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function pipelineStageLabel(stage) {
  const map = {
    lead: 'Лид',
    quote: 'КП',
    approved: 'Согласовано',
    paid: 'Оплачено'
  }
  return map[stage] || 'Лид'
}

function pipelineStageBadgeClass(stage) {
  const map = {
    lead: 'bg-slate-100 text-slate-700 dark:bg-slate-900/40 dark:text-slate-200',
    quote: 'bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-200',
    approved: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-200',
    paid: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-200'
  }
  return map[stage] || map.lead
}
</script>
