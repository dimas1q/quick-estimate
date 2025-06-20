<template>
  <div class="relative" ref="rootRef">
    <button type="button" @click="open = !open" class="qe-input w-full flex justify-between items-center cursor-pointer">
      <span class="truncate" :title="selectedLabels || placeholder">
        {{ selectedLabels || placeholder }}
      </span>
      <ChevronDown class="w-4 h-4 ml-2 transition-transform" :class="{ 'rotate-180': open }" />
    </button>
    <div v-if="open" class="absolute z-10 mt-1 w-full bg-white dark:bg-qe-black3 border border-gray-200 dark:border-gray-700 rounded-xl shadow max-h-60 overflow-auto animate-fade-in">
      <label v-for="opt in options" :key="opt.value" class="flex items-center gap-2 px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-800">
        <input type="checkbox" :value="opt.value" v-model="internalValue" class="accent-blue-500 dark:accent-blue-400" />
        <span class="text-sm">{{ opt.label }}</span>
      </label>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { onClickOutside } from '@vueuse/core'
import { ChevronDown } from 'lucide-vue-next'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  options: { type: Array, required: true },
  placeholder: { type: String, default: 'Выберите' }
})
const emit = defineEmits(['update:modelValue'])

const open = ref(false)
const internalValue = ref([...props.modelValue])

watch(() => props.modelValue, v => {
  internalValue.value = [...v]
})
watch(internalValue, v => {
  emit('update:modelValue', v)
})

const selectedLabels = computed(() => {
  const labels = props.options
    .filter(o => internalValue.value.includes(o.value))
    .map(o => o.label)
  return labels.join(', ')
})

const rootRef = ref(null)
onClickOutside(rootRef, () => { open.value = false })
</script>

<style scoped>
.animate-fade-in {
  animation: fade-in 0.15s ease-out;
}
@keyframes fade-in {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
