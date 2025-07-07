<template>
  <div class="flex flex-col items-center from-gray-50 via-white to-gray-100 py-10">
    <!-- Хедер и бар фильтров -->
    <div class="w-full max-w-5xl flex flex-col gap-4 mb-8">
      <div class="flex items-center justify-between mb-2">
        <h2 class="text-2xl font-bold">Клиенты</h2>
        <router-link to="/clients/create" class="qe-btn px-4">Добавить клиента</router-link>
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
    <div class="w-full max-w-5xl">
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
              <router-link :to="`/clients/${c.id}`" class="text-lg font-semibold truncate hover:text-blue-600">{{ c.name
                }}
              </router-link>
              <div class="text-gray-500 text-sm truncate">{{ c.company || '—' }}</div>
              <div class="text-gray-400 text-xs truncate">{{ c.email || c.phone || '—' }}</div>
            </div>
          </div>
        </div>
        <div v-if="store.clients.length === 0"
          class="text-center text-gray-400 border border-gray-100 p-6 rounded-2xl bg-white/70 mt-4">
          Клиенты отсутствуют.
        </div>
        <QePagination :total="totalClients" :per-page="perPage" :page="currentPage" @update:page="changePage"
          class="mt-6" />
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useClientsStore } from '@/store/clients'
import QePagination from '@/components/QePagination.vue'

import { LucideUser } from 'lucide-vue-next'

const store = useClientsStore()
const isLoading = ref(true)
const filters = ref({
  name: '',
  company: '',
  email: ''
})

const perPage = 5
const currentPage = ref(1)
const currentFilters = ref({})
const totalClients = computed(() => store.total)

onMounted(async () => {
  isLoading.value = true
  await store.fetchClients({ page: currentPage.value, limit: perPage })
  currentFilters.value = {}
  isLoading.value = false
})

async function applyFilters() {
  isLoading.value = true
  const query = {
    name: filters.value.name,
    company: filters.value.company,
    email: filters.value.email
  }
  currentFilters.value = query
  currentPage.value = 1
  await store.fetchClients({ ...query, page: currentPage.value, limit: perPage })
  isLoading.value = false
}

async function resetFilters() {
  isLoading.value = true
  filters.value = { name: '', company: '' }
  currentFilters.value = {}
  currentPage.value = 1
  await store.fetchClients({ page: currentPage.value, limit: perPage })
  isLoading.value = false
}

async function changePage(p) {
  currentPage.value = p
  await store.fetchClients({ ...currentFilters.value, page: p, limit: perPage })
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>
