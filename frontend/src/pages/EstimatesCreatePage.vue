<script setup>
import { useEstimatesStore } from '@/store/estimates'
import EstimateForm from '@/components/EstimateForm.vue'

const store = useEstimatesStore()
const copiedEstimate = store.copiedEstimate
store.clearCopiedEstimate()
</script>

<template>
  <div class="space-y-6 max-w-8xl mx-auto">
    <h1 class="text-2xl font-bold text-center py-2">Создание сметы</h1>
    <EstimateForm :initial="copiedEstimate" mode="copy" />
  </div>
</template>
