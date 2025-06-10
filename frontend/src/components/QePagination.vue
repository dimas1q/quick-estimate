<template>
  <div class="flex items-center justify-between mt-4" v-if="totalPages > 1">
    <div v-if="showLimit" class="text-sm flex items-center gap-2">
      <span>На странице:</span>
      <select v-model.number="localLimit" @change="updateLimit" class="qe-input w-20">
        <option v-for="s in pageSizes" :key="s" :value="s">{{ s }}</option>
      </select>
    </div>
    <div class="flex items-center gap-1 ml-auto">
      <button class="qe-pagination-btn" :disabled="current === 1" @click="setPage(current-1)">←</button>
      <button v-for="p in pages" :key="p" @click="setPage(p)"
        :class="['qe-pagination-btn', { 'qe-pagination-btn-active': p === current }]">
        {{ p }}
      </button>
      <button class="qe-pagination-btn" :disabled="current === totalPages" @click="setPage(current+1)">→</button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
const props = defineProps({
  total: { type: Number, required: true },
  limit: { type: Number, required: true },
  offset: { type: Number, required: true },
  showLimit: { type: Boolean, default: true },
  pageSizes: { type: Array, default: () => [10, 20, 50] }
})
const emit = defineEmits(['update:page', 'update:limit'])
const current = computed(() => Math.floor(props.offset / props.limit) + 1)
const totalPages = computed(() => Math.ceil(props.total / props.limit))
const pages = computed(() => {
  const n = totalPages.value
  const cur = current.value
  const arr = []
  let start = Math.max(1, cur - 2)
  let end = Math.min(n, cur + 2)
  if (cur <= 3) end = Math.min(n, 5)
  if (cur >= n - 2) start = Math.max(1, n - 4)
  for (let i = start; i <= end; i++) arr.push(i)
  return arr
})
const localLimit = ref(props.limit)
watch(() => props.limit, v => (localLimit.value = v))
function setPage(p) {
  if (p < 1 || p > totalPages.value || p === current.value) return
  emit('update:page', p)
}
function updateLimit() {
  emit('update:limit', localLimit.value)
}
</script>
