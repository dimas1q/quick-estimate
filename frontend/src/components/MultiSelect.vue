<template>
  <Listbox as="div" class="relative" :modelValue="modelValue" @update:modelValue="val => emit('update:modelValue', val)">
    <ListboxButton class="qe-input w-full flex justify-between items-center">
      <span class="block truncate text-left">{{ selectedLabels }}</span>
      <ChevronDown class="w-4 h-4 text-gray-500" />
    </ListboxButton>
    <ListboxOptions class="absolute z-10 mt-1 w-full bg-white dark:bg-qe-black3 border border-gray-200 dark:border-gray-700 rounded-md shadow-lg max-h-60 overflow-auto">
      <ListboxOption v-for="opt in options" :key="opt.value" :value="opt.value" as="template">
        <li @click="toggle(opt.value)" class="cursor-pointer select-none relative py-2 pl-8 pr-4 hover:bg-gray-100 dark:hover:bg-gray-800">
          <span :class="modelValue.includes(opt.value) ? 'font-medium' : 'font-normal'" class="block truncate">{{ opt.label }}</span>
          <span v-if="modelValue.includes(opt.value)" class="absolute inset-y-0 left-0 flex items-center pl-1.5 text-blue-600">
            <Check class="w-4 h-4" />
          </span>
        </li>
      </ListboxOption>
    </ListboxOptions>
  </Listbox>
</template>

<script setup>
import { computed } from 'vue'
import { Listbox, ListboxButton, ListboxOptions, ListboxOption } from '@headlessui/vue'
import { ChevronDown, Check } from 'lucide-vue-next'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  options: { type: Array, default: () => [] },
  placeholder: { type: String, default: 'Выберите...' }
})
const emit = defineEmits(['update:modelValue'])

function toggle(val) {
  const arr = [...props.modelValue]
  const idx = arr.indexOf(val)
  if (idx >= 0) arr.splice(idx, 1)
  else arr.push(val)
  emit('update:modelValue', arr)
}

const selectedLabels = computed(() => {
  const labels = props.options.filter(o => props.modelValue.includes(o.value)).map(o => o.label)
  return labels.length ? labels.join(', ') : props.placeholder
})
</script>
