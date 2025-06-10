<script setup>
import { computed } from 'vue'
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'
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
  <transition name="fade" mode="out-in">
    <div v-if="totalPages > 1" :key="currentPage" class="flex justify-center mt-4 gap-1 select-none">
      <button @click="go(currentPage - 1)" :disabled="currentPage === 1" class="qe-btn-secondary w-8 h-8 flex items-center justify-center">
        <ChevronLeft class="w-4 h-4" />
      </button>
      <button v-for="p in totalPages" :key="p" @click="go(p)"
        class="w-8 h-8 rounded-md font-medium text-sm transition-colors"
        :class="p === currentPage ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-qe-black2 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-qe-black3'">
        {{ p }}
      </button>
      <button @click="go(currentPage + 1)" :disabled="currentPage === totalPages" class="qe-btn-secondary w-8 h-8 flex items-center justify-center">
        <ChevronRight class="w-4 h-4" />
      </button>
    </div>
  </transition>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
