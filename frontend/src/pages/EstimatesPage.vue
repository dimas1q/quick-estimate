<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold">Сметы</h1>
      <router-link
        to="/estimates/create"
        class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
      >
        + Создать смету
      </router-link>
    </div>

    <div v-for="e in store.estimates" :key="e.id" class="border p-4 rounded shadow-sm space-y-1">
      <div class="font-semibold text-lg">{{ e.name }}</div>
      <div class="text-sm text-gray-600">Клиент: {{ e.client_name || '—' }}</div>
      <div class="text-sm">Ответственный: {{ e.responsible || '—' }}</div>
      <div class="text-xs text-gray-500">Создана: {{ new Date(e.date).toLocaleString() }}</div>

      <router-link
        :to="`/estimates/${e.id}`"
        class="text-blue-600 text-sm hover:underline mt-2 inline-block"
      >
        Подробнее →
      </router-link>
    </div>
  </div>
</template>
  
  <script setup>
  import { onMounted } from 'vue'
  import { useEstimatesStore } from '@/store/estimates'
  import EstimateForm from '@/components/EstimateForm.vue'
  
  const store = useEstimatesStore()
  onMounted(() => store.fetchEstimates())
  </script>
  