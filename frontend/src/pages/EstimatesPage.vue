<template>
  <div class="space-y-6 px-16 py-8 max-w-7xl mx-auto">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold">Сметы</h1>
      <router-link to="/estimates/create"
        class="inline-flex justify-center items-center px-4 py-2 rounded-md bg-blue-500 text-white hover:bg-blue-600 transition-all text-sm font-medium">
        Создать смету
      </router-link>
    </div>

    <div v-for="e in store.estimates" :key="e.id" class="border p-4 rounded shadow-sm space-y-1">
      <div class="font-semibold text-lg">{{ e.name }}</div>
      <div class="text-sm">Клиент: {{ e.client_name || '—' }}</div>
      <div class="text-sm">Ответственный: {{ e.responsible || '—' }}</div>
      <div class="text-xs text-gray-500">Создана: {{ new Date(e.date).toLocaleString() }}</div>

      <router-link :to="`/estimates/${e.id}`" class="text-blue-600 text-sm hover:underline mt-2 inline-block">
        Подробнее →
      </router-link>
    </div>
  </div>
</template>
  
  <script setup>
  import { onMounted } from 'vue'
  import { useEstimatesStore } from '@/store/estimates'
  
  const store = useEstimatesStore()
  onMounted(() => store.fetchEstimates())
  </script>
  