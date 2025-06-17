<script setup>
import { ref, computed, onMounted } from 'vue'
import { useClientsStore } from '@/store/clients'
import QePagination from '@/components/QePagination.vue'

const store = useClientsStore()
const isLoading = ref(true)
const filters = ref({
  name: '',
  company: ''
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
    company: filters.value.company
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

<template>
  <div class="space-y-6 px-6 py-8 max-w-5xl mx-auto center-with-sidebar">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Клиенты</h1>
      <!-- Можно добавить импорт/экспорт позже -->
    </div>
    <div class="flex gap-6 items-start">
      <!-- Список клиентов -->
      <div class="flex-1 space-y-4">
        <div v-if="isLoading" class="flex flex-col gap-5">
          <div v-for="n in 3" :key="n"
            class="border rounded-xl shadow-sm p-5 bg-white dark:bg-gray-900 animate-pulse flex flex-col gap-3 relative">
            <div class="h-6 bg-gray-200 dark:bg-gray-800 rounded w-2/3 mb-2"></div>
            <div class="h-4 bg-gray-100 dark:bg-gray-700 rounded w-1/4 mb-2"></div>
            <div class="h-4 bg-gray-100 dark:bg-gray-700 rounded w-1/2"></div>
          </div>
        </div>
        <template v-else>
          <div v-for="c in store.clients" :key="c.id"
            class="border border-gray-200 dark:border-qe-black2 rounded-xl shadow-sm p-5 bg-white dark:bg-qe-black3 transition hover:shadow-md flex flex-col gap-1">
            <div class="font-semibold text-lg">{{ c.name }}</div>
            <div class="text-sm text-gray-600 dark:text-gray-400">Компания: {{ c.company || '—' }}</div>
            <div class="text-sm text-gray-600 dark:text-gray-400">Контакт: {{ c.email || c.phone || '—' }}</div>
            <router-link :to="`/clients/${c.id}`"
              class="text-blue-600 dark:text-blue-400 text-sm hover:underline mt-2 inline-block">
              Подробнее →
            </router-link>
          </div>
          <div v-if="store.clients.length === 0"
            class="text-center text-gray-500 border border-gray-200 dark:border-gray-800 p-4 rounded-2xl py-8">
            Клиенты отсутствуют.
          </div>
          <QePagination
            :total="totalClients"
            :per-page="perPage"
            :page="currentPage"
            @update:page="changePage"
            class="mt-4" />
        </template>
      </div>

      <!-- Правая панель: добавление и фильтры -->
      <div class="w-72 space-y-4">
        <router-link to="/clients/create" class="qe-btn block w-full text-center">
          Добавить клиента
        </router-link>
        <div
          class="border border-gray-200 dark:border-qe-black2 rounded-xl p-4 shadow-sm space-y-4 text-center bg-white dark:bg-qe-black3">
          <h2 class="font-semibold text-lg">Фильтры</h2>
          <div>
            <label class="text-sm text-gray-600 dark:text-gray-300">Имя</label>
            <input v-model="filters.name" class="qe-input w-full mt-2" type="text" placeholder="Поиск по имени" />
          </div>
          <div>
            <label class="text-sm text-gray-600 dark:text-gray-300">Компания</label>
            <input v-model="filters.company" class="qe-input w-full mt-2" type="text" placeholder="Поиск по компании" />
          </div>
          <div class="flex gap-2 pt-2">
            <button @click="applyFilters" class="qe-btn w-full">Применить</button>
            <button @click="resetFilters" class="qe-btn-secondary w-full">Сбросить</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@media (min-width: 768px) {
  .center-with-sidebar {
    transform: translateX(calc(var(--sidebar-width) / -2));
  }
}
</style>
