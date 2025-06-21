<template>
  <Listbox v-model="model" multiple>
    <div class="relative">
      <ListboxButton class="qe-input w-full text-left">
        <span v-if="model.length" class="truncate">{{ selectedLabels.join(', ') }}</span>
        <span v-else class="text-gray-400">{{ placeholder }}</span>
        <ChevronDown class="w-4 h-4 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
      </ListboxButton>
      <Transition
        enter="transition ease-out duration-100"
        enter-from="transform opacity-0 scale-95"
        enter-to="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leave-from="transform opacity-100 scale-100"
        leave-to="transform opacity-0 scale-95"
      >
        <ListboxOptions
          class="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-lg bg-white dark:bg-qe-black3 border border-gray-200 dark:border-gray-700 shadow-lg focus:outline-none text-sm py-1"
        >
          <ListboxOption
            v-for="opt in options"
            :key="opt.value"
            :value="opt.value"
            class="cursor-pointer select-none relative py-2 pl-8 pr-3 hover:bg-gray-100 dark:hover:bg-qe-black2"
          >
            <span class="block truncate">{{ opt.label }}</span>
            <Check
              v-if="model.includes(opt.value)"
              class="absolute left-2 top-2 w-4 h-4 text-blue-600"
            />
          </ListboxOption>
        </ListboxOptions>
      </Transition>
    </div>
  </Listbox>
</template>

<script setup>
import { computed } from 'vue'
import { Listbox, ListboxButton, ListboxOptions, ListboxOption } from '@headlessui/vue'
import { Check, ChevronDown } from 'lucide-vue-next'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  options: { type: Array, required: true },
  placeholder: { type: String, default: 'Выберите' }
})
const emit = defineEmits(['update:modelValue'])

const model = computed({
  get: () => props.modelValue,
  set: val => emit('update:modelValue', val)
})

const selectedLabels = computed(() => props.options.filter(o => model.value.includes(o.value)).map(o => o.label))
</script>
