<template>
  <div ref="root" class="relative">
    <div @click="toggle" class="qe-input w-full flex flex-wrap items-center gap-1 cursor-pointer min-h-[40px]">
      <template v-if="selectedLabels.length">
        <span v-for="(label, idx) in selectedLabels" :key="idx" class="flex items-center bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-100 px-2 py-0.5 rounded gap-1 text-xs">
          {{ label }}
          <X class="w-3 h-3 cursor-pointer" @click.stop="remove(selectedValues[idx])" />
        </span>
      </template>
      <span v-else class="text-gray-400">{{ placeholder }}</span>
      <ChevronDown class="w-4 h-4 ml-auto text-gray-400" />
    </div>
    <transition name="fade">
      <div v-if="open" class="absolute z-10 mt-1 w-full bg-white dark:bg-qe-black3 border border-gray-200 dark:border-qe-black2 rounded-xl shadow max-h-52 overflow-auto">
        <ul class="py-1">
          <li v-for="opt in options" :key="opt.value" @click.stop="toggleOption(opt.value)" class="px-3 py-2 flex items-center gap-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800">
            <input type="checkbox" :checked="modelValue.includes(opt.value)" class="accent-blue-500" />
            <span>{{ opt.label }}</span>
          </li>
        </ul>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onClickOutside } from '@vueuse/core'
import { ChevronDown, X } from 'lucide-vue-next'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  options: { type: Array, default: () => [] },
  placeholder: { type: String, default: 'Выберите' }
})
const emit = defineEmits(['update:modelValue'])

const open = ref(false)
const root = ref(null)
onClickOutside(root, () => (open.value = false))

const selectedLabels = computed(() =>
  props.options.filter(o => props.modelValue.includes(o.value)).map(o => o.label)
)
const selectedValues = computed(() =>
  props.options.filter(o => props.modelValue.includes(o.value)).map(o => o.value)
)

function toggle() {
  open.value = !open.value
}

function toggleOption(val) {
  const arr = [...props.modelValue]
  const idx = arr.indexOf(val)
  if (idx >= 0) arr.splice(idx, 1)
  else arr.push(val)
  emit('update:modelValue', arr)
}

function remove(val) {
  const arr = props.modelValue.filter(v => v !== val)
  emit('update:modelValue', arr)
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
