<template>
  <div class="space-y-3">
    <div class="flex items-center justify-between">
      <h4 class="text-sm font-semibold text-gray-700 dark:text-gray-200">Позиции</h4>
      <button type="button" class="qe-btn-secondary px-3 py-1 text-xs" @click="addItem">Добавить позицию</button>
    </div>

    <div class="overflow-x-auto rounded-xl border border-gray-200 dark:border-qe-black2">
      <table class="min-w-full text-xs">
        <thead class="bg-gray-50 dark:bg-qe-black2 text-gray-600 dark:text-gray-300">
          <tr>
            <th class="px-2 py-2 text-left font-semibold">Название</th>
            <th class="px-2 py-2 text-left font-semibold">Описание</th>
            <th class="px-2 py-2 text-left font-semibold">Кол-во</th>
            <th class="px-2 py-2 text-left font-semibold">Ед.</th>
            <th v-if="showInternalPrice" class="px-2 py-2 text-left font-semibold">Внутр.</th>
            <th class="px-2 py-2 text-left font-semibold">Внешн.</th>
            <th class="px-2 py-2 text-left font-semibold">Категория</th>
            <th class="px-2 py-2 text-right font-semibold">Действия</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(item, idx) in items"
            :key="idx"
            class="border-t border-gray-100 dark:border-qe-black2 bg-white dark:bg-qe-black3"
          >
            <td class="px-2 py-2 min-w-[170px]">
              <input class="qe-input w-full h-9 text-xs" :value="item.name" @input="setField(idx, 'name', $event.target.value)" />
            </td>
            <td class="px-2 py-2 min-w-[180px]">
              <input class="qe-input w-full h-9 text-xs" :value="item.description" @input="setField(idx, 'description', $event.target.value)" />
            </td>
            <td class="px-2 py-2 min-w-[90px]">
              <input class="qe-input w-full h-9 text-xs" type="number" step="0.01" min="0" :value="item.quantity" @input="setNumberField(idx, 'quantity', $event.target.value)" />
            </td>
            <td class="px-2 py-2 min-w-[110px]">
              <input class="qe-input w-full h-9 text-xs" :value="item.unit" @input="setField(idx, 'unit', $event.target.value)" />
            </td>
            <td v-if="showInternalPrice" class="px-2 py-2 min-w-[110px]">
              <input class="qe-input w-full h-9 text-xs" type="number" step="0.01" min="0" :value="item.internal_price" @input="setNumberField(idx, 'internal_price', $event.target.value)" />
            </td>
            <td class="px-2 py-2 min-w-[110px]">
              <input class="qe-input w-full h-9 text-xs" type="number" step="0.01" min="0" :value="item.external_price" @input="setNumberField(idx, 'external_price', $event.target.value)" />
            </td>
            <td class="px-2 py-2 min-w-[140px]">
              <input class="qe-input w-full h-9 text-xs" :value="item.category" @input="setField(idx, 'category', $event.target.value)" />
            </td>
            <td class="px-2 py-2 text-right">
              <button type="button" class="qe-btn-danger px-2 py-1 text-xs" @click="removeItem(idx)">Удалить</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-if="items.length === 0" class="text-xs text-gray-500 dark:text-gray-400">Добавьте хотя бы одну позицию.</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  showInternalPrice: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue'])

const items = computed({
  get: () => props.modelValue || [],
  set: (value) => emit('update:modelValue', value)
})

function createEmptyItem() {
  return {
    name: '',
    description: '',
    quantity: 1,
    unit: 'шт',
    internal_price: 0,
    external_price: 0,
    category: ''
  }
}

function addItem() {
  items.value = [...items.value, createEmptyItem()]
}

function removeItem(index) {
  items.value = items.value.filter((_, idx) => idx !== index)
}

function setField(index, field, value) {
  const next = [...items.value]
  next[index] = { ...next[index], [field]: value }
  items.value = next
}

function setNumberField(index, field, value) {
  const parsed = Number(value)
  setField(index, field, Number.isFinite(parsed) ? parsed : 0)
}
</script>
