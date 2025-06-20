<template>
  <div class="relative" @keydown.escape="open=false">
    <button type="button" @click="toggle" class="qe-input w-full flex justify-between items-center cursor-pointer">
      <span class="truncate text-left">{{ selectedLabel }}</span>
      <ChevronDown class="w-4 h-4 ml-1 opacity-60" />
    </button>
    <transition name="fade">
      <div v-if="open" class="absolute z-10 mt-1 w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-qe-black3 shadow p-2 max-h-60 overflow-auto">
        <label v-for="opt in options" :key="opt.value" class="flex items-center gap-2 px-2 py-1 rounded hover:bg-gray-50 dark:hover:bg-gray-800">
          <input type="checkbox" :value="opt.value" v-model="localValue" class="accent-blue-500 dark:accent-blue-400" />
          <span class="text-sm">{{ opt.label }}</span>
        </label>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { ChevronDown } from 'lucide-vue-next'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  options: { type: Array, default: () => [] },
  placeholder: { type: String, default: 'Выбрать...' }
})
const emit = defineEmits(['update:modelValue'])

const open = ref(false)
const localValue = ref([...props.modelValue])

watch(() => props.modelValue, v => { localValue.value = [...v] })
watch(localValue, v => emit('update:modelValue', v))

function toggle() { open.value = !open.value }

const selectedLabel = computed(() => {
  if (!localValue.value.length) return props.placeholder
  return props.options
    .filter(o => localValue.value.includes(o.value))
    .map(o => o.label)
    .join(', ')
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active { transition: opacity 0.15s; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }
</style>
