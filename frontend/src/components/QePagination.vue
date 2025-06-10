<template>
  <nav v-if="totalPages > 1" class="flex justify-center mt-4">
    <ul class="inline-flex space-x-1">
      <li>
        <button
          class="px-3 py-1 rounded-lg text-sm font-medium"
          :class="page === 1 ? 'text-gray-400 cursor-not-allowed' : 'text-blue-600 hover:bg-blue-50 dark:hover:bg-qe-black2'"
          :disabled="page === 1"
          @click="$emit('update:page', page - 1)"
        >
          Prev
        </button>
      </li>
      <li v-for="p in pages" :key="p">
        <button
          class="px-3 py-1 rounded-lg text-sm font-medium"
          :class="p === page ? 'bg-blue-600 text-white' : 'text-gray-700 dark:text-gray-300 hover:bg-blue-50 dark:hover:bg-qe-black2'"
          @click="$emit('update:page', p)"
        >
          {{ p }}
        </button>
      </li>
      <li>
        <button
          class="px-3 py-1 rounded-lg text-sm font-medium"
          :class="page === totalPages ? 'text-gray-400 cursor-not-allowed' : 'text-blue-600 hover:bg-blue-50 dark:hover:bg-qe-black2'"
          :disabled="page === totalPages"
          @click="$emit('update:page', page + 1)"
        >
          Next
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
  const start = Math.max(1, props.page - 2)
  const end = Math.min(totalPages.value, props.page + 2)
  for (let i = start; i <= end; i++) result.push(i)
  return result
})
</script>
