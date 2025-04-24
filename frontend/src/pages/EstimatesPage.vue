# frontend/src/pages/EstimatesPage.vue
# Component for displaying a list of estimates with filtering options.

<template>
  <div class="space-y-6 px-16 py-8 max-w-7xl mx-auto">

    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold">Сметы</h1>
    </div>

    <div class="flex gap-6 items-start">

      <div class="flex-1 space-y-4">
        <div v-for="e in store.estimates" :key="e.id" class="border p-4 rounded shadow-sm space-y-1">
          <div class="font-semibold text-lg">{{ e.name }}</div>
          <div class="text-sm">Клиент: {{ e.client_name || '—' }} ({{ e.client_company || '—' }})</div>
          <div class="text-sm">Ответственный: {{ e.responsible || '—' }}</div>
          <div class="text-xs text-gray-500">Создана: {{ new Date(e.date).toLocaleString() }}</div>
          <router-link :to="`/estimates/${e.id}`" class="text-blue-600 text-sm hover:underline mt-2 inline-block">
            Подробнее →
          </router-link>
        </div>
        <div v-if="store.estimates.length === 0" class="text-center text-gray-500 border p-4 rounded py-8">
          <p>Сметы отсутствуют.</p>
        </div>
      </div>

      <div class="w-64 space-y-4">
        <router-link to="/estimates/create" class="btn-primary block w-full text-center">
          Создать смету
        </router-link>
        
        <!-- Блок фильтров -->
        <div class="border rounded p-4 shadow-sm space-y-4 text-center">


          <h2 class="font-semibold text-lg">Фильтры</h2>
          <div>
            <label class="text-sm text-gray-600">Название</label>
            <input v-model="filters.name" class="input-field mt-1" type="text" />
          </div>

          <div>
            <label class="text-sm text-gray-600">Клиент</label>
            <input v-model="filters.client" class="input-field mt-1" type="text" />
          </div>

          <div>
            <label class="text-sm text-gray-600">Дата с</label>
            <input v-model="filters.date_from" class="input-field mt-1" type="date" />
          </div>

          <div>
            <label class="text-sm text-gray-600">Дата по</label>
            <input v-model="filters.date_to" class="input-field mt-1" type="date" />
          </div>

          <div class="flex gap-2 pt-2">
            <button @click="applyFilters" class="btn-secondary w-full">Применить</button>
            <button @click="resetFilters" class="btn-secondary w-full">Сбросить</button>
          </div>
        </div>

      </div>


    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useEstimatesStore } from '@/store/estimates'

const filters = ref({
  name: '',
  client: '',
  date_from: '',
  date_to: ''
})

const store = useEstimatesStore()
onMounted(() => store.fetchEstimates())

function applyFilters() {
  const query = {
    name: filters.value.name,
    client: filters.value.client,
    date_from: toUTCStart(filters.value.date_from),
    date_to: toUTCEnd(filters.value.date_to)
  }
  store.fetchEstimates(query)
}

function resetFilters() {
  filters.value = {
    name: '',
    client: '',
    date_from: '',
    date_to: ''
  }
  store.fetchEstimates()
}

function toUTCStart(dateStr) {
  if (!dateStr) return ''
  const local = new Date(dateStr + 'T00:00:00')
  return local.toISOString()
}

function toUTCEnd(dateStr) {
  if (!dateStr) return ''
  const local = new Date(dateStr + 'T00:00:00')
  const endOfDay = new Date(local.getTime() + 24 * 60 * 60 * 1000)
  return endOfDay.toISOString()
}

</script>
