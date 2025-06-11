<template>
  <nav v-if="totalPages > 1" class="flex justify-center mt-6">
    <ul class="inline-flex items-center space-x-2 whitespace-nowrap">
      <li>
        <button
          class="w-8 h-8 flex items-center justify-center rounded-lg text-sm font-medium transition-colors duration-150"
          :class="page === 1 ? 'text-gray-400 bg-gray-100 cursor-not-allowed' : 'text-blue-600 bg-white hover:bg-blue-50 dark:bg-qe-black1 dark:hover:bg-qe-black2'"
          :disabled="page === 1" @click="$emit('update:page', page - 1)">
          ←
        </button>
      </li>
      <li v-for="p in pages" :key="p">
        <button
          class="w-8 h-8 flex items-center justify-center rounded-lg text-sm font-medium transition-colors duration-150"
          :class="p === page
            ? 'bg-blue-600 text-white shadow'
            : 'text-gray-700 dark:text-gray-300 bg-white hover:bg-blue-50 dark:bg-qe-black1 dark:hover:bg-qe-black2'"
          @click="$emit('update:page', p)">
          {{ p }}
        </button>
      </li>
      <li>
        <button
          class="w-8 h-8 flex items-center justify-center rounded-lg text-sm font-medium transition-colors duration-150"
          :class="page === totalPages ? 'text-gray-400 bg-gray-100 cursor-not-allowed' : 'text-blue-600 bg-white hover:bg-blue-50 dark:bg-qe-black1 dark:hover:bg-qe-black2'"
          :disabled="page === totalPages" @click="$emit('update:page', page + 1)">
          →
        </button>
      </li>
    </ul>
  </nav>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  total: { type: Number, required: true },
  perPage: { type: Number, required: true },
  page: { type: Number, required: true }
})

const totalPages = computed(() => Math.ceil(props.total / props.perPage))

const pages = computed(() => {
  const result = []
  let start = Math.max(1, props.page - 2)
  let end = Math.min(totalPages.value, props.page + 2)

  // Ensure always 5 pages if possible
  if (end - start < 4) {
    if (start === 1) {
      end = Math.min(totalPages.value, start + 4)
    } else if (end === totalPages.value) {
      start = Math.max(1, end - 4)
    }
  }

  for (let i = start; i <= end; i++) result.push(i)
  return result
})
</script>
