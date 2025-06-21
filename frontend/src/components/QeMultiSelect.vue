<template>
  <Listbox v-model="internalValue" multiple>
    <div class="relative">
      <ListboxButton class="qe-input w-full text-left flex justify-between items-center">
        <span class="truncate">
          <template v-if="props.modelValue.length">
            {{ selectedLabels.join(', ') }}
          </template>
          <span v-else class="text-gray-400">{{ placeholder }}</span>
        </span>
        <ChevronDown class="w-4 h-4 ml-2 text-gray-500" />
      </ListboxButton>
      <Transition enter="transition duration-100" enter-from="opacity-0" enter-to="opacity-100"
        leave="transition duration-75" leave-from="opacity-100" leave-to="opacity-0">
        <ListboxOptions
          class="absolute z-10 mt-1 w-full bg-white dark:bg-qe-black3 rounded-lg shadow border border-gray-200 dark:border-gray-800 max-h-60 overflow-auto focus:outline-none text-sm">
          <ListboxOption v-for="opt in options" :key="opt.value" :value="opt.value"
            class="cursor-pointer select-none relative py-2 pl-8 pr-4 text-gray-700 dark:text-gray-200"
            :class="{ 'bg-gray-100 dark:bg-qe-black2': active }" v-slot="{ active, selected }">
            {{ opt.label }}
            <span v-if="selected" class="absolute left-2 inset-y-0 flex items-center">
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
  options: { type: Array, default: () => [] },
  placeholder: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue'])

const internalValue = computed({
  get: () => props.modelValue,
  set: v => emit('update:modelValue', v)
})

const selectedLabels = computed(() => {
  return props.options.filter(o => props.modelValue.includes(o.value)).map(o => o.label)
})
</script>
