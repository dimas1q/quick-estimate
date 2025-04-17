<script setup>
import { useEstimatesStore } from '@/store/estimates'
import EstimateForm from '@/components/EstimateForm.vue'

const store = useEstimatesStore()
const copiedEstimate = store.copiedEstimate
store.clearCopiedEstimate()
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold">Создание сметы</h1>
    <EstimateForm :initial="copiedEstimate" mode="copy" />
  </div>
</template>
