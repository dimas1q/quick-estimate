<script setup>
import { Listbox, ListboxButton, ListboxOptions, ListboxOption } from '@headlessui/vue'
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  options: { type: Array, required: true },
  label: { type: String, default: '' },
  placeholder: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue'])

const selected = computed({
  get: () => props.modelValue,
  set: v => emit('update:modelValue', v)
})

const labelMap = computed(() => Object.fromEntries(props.options.map(o => [o.value, o.label])))
</script>

<template>
  <div>
    <label v-if="label" class="text-sm text-gray-600 dark:text-gray-300 mb-1 block">{{ label }}</label>
    <Listbox v-model="selected" multiple>
      <div class="relative">
        <ListboxButton class="qe-input w-full text-left flex flex-wrap gap-1 min-h-[2.5rem]">
          <template v-if="selected.length">
            <span v-for="val in selected" :key="val" class="bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200 px-2 py-0.5 rounded text-sm">
              {{ labelMap[val] }}
            </span>
          </template>
          <span v-else class="text-gray-400">{{ placeholder }}</span>
        </ListboxButton>
        <transition leave-active-class="transition duration-100" leave-from-class="opacity-100" leave-to-class="opacity-0">
          <ListboxOptions class="absolute z-10 mt-1 w-full bg-white dark:bg-qe-black3 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-60 overflow-auto">
            <ListboxOption v-for="opt in options" :key="opt.value" :value="opt.value" class="cursor-pointer select-none relative py-2 pl-8 pr-4 hover:bg-gray-100 dark:hover:bg-gray-700">
              <span class="block truncate" :class="{ 'font-medium': selected.includes(opt.value) }">{{ opt.label }}</span>
              <span v-if="selected.includes(opt.value)" class="absolute inset-y-0 left-0 flex items-center pl-2 text-blue-600">✓</span>
            </ListboxOption>
          </ListboxOptions>
        </transition>
      </div>
    </Listbox>
  </div>
</template>
