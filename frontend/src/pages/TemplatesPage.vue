<template>
  <div class="space-y-6 px-16 py-8 max-w-7xl mx-auto">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold">Шаблоны смет</h1>
      <router-link to="/templates/create"
        class="inline-flex justify-center items-center px-4 py-2 rounded-md bg-blue-500 text-white hover:bg-blue-600 transition-all text-sm font-medium">
        + Создать шаблон
      </router-link>
    </div>

    <div v-for="template in store.templates" :key="template.id" class="border p-4 rounded shadow-sm space-y-1">
      <div class="font-semibold text-lg">{{ template.name }}</div>
      <div class="text-sm text-gray-600">Описание: {{ template.description || '—' }}</div>

      <router-link :to="`/templates/${template.id}`" class="text-blue-600 text-sm hover:underline mt-2 inline-block">
        Подробнее →
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useTemplatesStore } from '@/store/templates'

const store = useTemplatesStore()

onMounted(() => {
  store.fetchTemplates()
})
</script>
