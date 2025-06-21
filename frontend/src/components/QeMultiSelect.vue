<template>
  <Listbox multiple :model-value="modelValue" @update:modelValue="onUpdate">
    <div class="relative">
      <ListboxButton class="qe-input w-full text-left flex justify-between items-center">
        <span class="truncate" :class="{ 'text-gray-400': !modelValue.length }">{{ selectedLabels }}</span>
        <ChevronDown class="w-4 h-4 text-gray-400" />
      </ListboxButton>
      <Transition name="fade">
        <ListboxOptions class="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white dark:bg-qe-black3 text-sm shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
          <ListboxOption v-for="opt in options" :key="opt.value" :value="opt.value" v-slot="{ active, selected }" :class="[active ? 'bg-blue-600 text-white' : 'text-gray-900 dark:text-gray-100', 'relative cursor-default select-none py-2 pl-8 pr-4']">
            <span :class="[selected ? 'font-semibold' : 'font-normal', 'block truncate']">{{ opt.label }}</span>
            <span v-if="selected" class="absolute inset-y-0 left-0 flex items-center pl-2">
              <Check class="w-4 h-4" />
            </span>
          </ListboxOption>
        </ListboxOptions>
      </Transition>
    </div>
  </Listbox>
</template>

<script setup>
import { computed } from 'vue'
import { Listbox, ListboxButton, ListboxOptions, ListboxOption } from '@headlessui/vue'
import { ChevronDown, Check } from 'lucide-vue-next'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  options: { type: Array, required: true },
  placeholder: { type: String, default: 'Не выбрано' }
})
const emit = defineEmits(['update:modelValue'])

function onUpdate(val) {
  emit('update:modelValue', val)
}

const selectedLabels = computed(() => {
  if (!props.modelValue.length) return props.placeholder
  const map = Object.fromEntries(props.options.map(o => [o.value, o.label]))
  return props.modelValue.map(v => map[v] || v).join(', ')
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
