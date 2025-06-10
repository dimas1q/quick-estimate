<script setup>
import { computed } from 'vue'
const props = defineProps({
  total: { type: Number, required: true },
  limit: { type: Number, required: true },
  offset: { type: Number, required: true }
})
const emit = defineEmits(['update:offset'])
const totalPages = computed(() => Math.ceil(props.total / props.limit) || 1)
const currentPage = computed(() => Math.floor(props.offset / props.limit) + 1)
function go(p) {
  if (p < 1 || p > totalPages.value) return
  emit('update:offset', (p - 1) * props.limit)
}
</script>
<template>
  <div v-if="totalPages > 1" class="flex justify-center mt-4 gap-2">
    <button @click="go(currentPage - 1)" :disabled="currentPage === 1" class="qe-btn-secondary px-3 py-1 text-sm">
      ‹
    </button>
    <button v-for="p in totalPages" :key="p" @click="go(p)"
      class="px-3 py-1 rounded text-sm"
      :class="p === currentPage ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-qe-black2 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-qe-black3'">
      {{ p }}
    </button>
    <button @click="go(currentPage + 1)" :disabled="currentPage === totalPages" class="qe-btn-secondary px-3 py-1 text-sm">
      ›
    </button>
  </div>
</template>
