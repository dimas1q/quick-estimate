<template>
  <div>
    <label v-if="label" class="text-sm text-gray-600 dark:text-gray-300 mb-1 block">{{ label }}</label>
    <Listbox v-model="model" multiple>
      <div class="relative">
        <ListboxButton class="qe-input w-full flex flex-wrap gap-1 items-center min-h-[40px]">
          <template v-if="model.length">
            <span v-for="val in model" :key="val" class="bg-blue-600 text-white text-xs px-2 py-0.5 rounded">{{ labelFor(val) }}</span>
          </template>
          <span v-else class="text-gray-400">{{ placeholder }}</span>
        </ListboxButton>
        <Transition
          enter="transition ease-out duration-100"
          enter-from="transform opacity-0 scale-95"
          enter-to="transform opacity-100 scale-100"
          leave="transition ease-in duration-75"
          leave-from="transform opacity-100 scale-100"
          leave-to="transform opacity-0 scale-95"
        >
          <ListboxOptions class="absolute z-10 mt-1 w-full rounded-md bg-white dark:bg-qe-black3 shadow-lg max-h-60 overflow-auto focus:outline-none text-sm">
            <ListboxOption v-for="opt in options" :key="opt.value" :value="opt.value" class="relative cursor-pointer select-none py-2 pl-8 pr-4">
              <span class="block truncate" :class="model.includes(opt.value) ? 'font-medium' : 'font-normal'">{{ opt.label }}</span>
              <span v-if="model.includes(opt.value)" class="absolute inset-y-0 left-0 flex items-center pl-2 text-blue-600">
                <Check class="w-4 h-4" />
              </span>
            </ListboxOption>
          </ListboxOptions>
        </Transition>
      </div>
    </Listbox>
  </div>
</template>

<script setup>
import { computed, Transition } from 'vue'
import { Listbox, ListboxButton, ListboxOptions, ListboxOption } from '@headlessui/vue'
import { Check } from 'lucide-vue-next'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  options: { type: Array, required: true },
  label: { type: String, default: '' },
  placeholder: { type: String, default: 'Выберите...' }
})
const emit = defineEmits(['update:modelValue'])

const model = computed({
  get: () => props.modelValue,
  set: v => emit('update:modelValue', v)
})
function labelFor(val) {
  const o = props.options.find(o => o.value === val)
  return o ? o.label : val
}
</script>
