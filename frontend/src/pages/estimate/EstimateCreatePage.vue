## frontend/src/pages/EstimateEditPage.vue
<template>
  <div class="space-y-6 max-w-6xl mx-auto px-16 py-8">
    <h1 class="text-2xl font-bold mb-6 text-center py-2">Создание сметы</h1>
    <EstimateForm :initial="copiedEstimate" mode="copy" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useEstimatesStore } from '@/store/estimates'
import EstimateForm from '@/components/EstimateForm.vue'

const route = useRoute()
const store = useEstimatesStore()

const copiedEstimate = computed(() => {
  if (route.query.copy === '1') {
    return store.getCopiedEstimate()
  }
  return null
})

if (route.query.copy !== '1') {
  store.clearCopiedEstimate()
}
</script>
