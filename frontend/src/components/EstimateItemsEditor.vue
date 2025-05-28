# frontend/src/components/EstimateItemsEditor.vue
<template>
  <div class="space-y-4">

    <h2 class="text-lg font-semibold text-center">Услуги</h2>

    <div class="grid grid-cols-8 gap-4 font-semibold text-sm text-gray-600 py-2">
      <div class="w-full px-4 text-center">Название</div>
      <div class="w-full px-4 text-center">Описание</div>
      <div class="w-full px-4 text-center">Кол-во</div>
      <div class="w-full px-4 text-center">Ед. изм.</div>
      <div class="w-full px-4 text-center">Цена</div>
      <div class="w-full px-4 text-center">Категория</div>
      <div class="w-full px-4 text-center">Итог</div>
      <div class="w-full px-4 text-center">Действие</div>
    </div>

    <div v-for="(groupItems, category) in groupedItems" :key="category" class="space-y-4">
      <h3 class="text-md font-semibold text-gray-700 text-center">{{ category }}</h3>

      <div v-for="(item, index) in groupItems" :key="index" class="grid grid-cols-8 gap-3 items-center">
        <input v-model="item.name" class="input-field" placeholder="Название" />
        <input v-model="item.description" class="input-field" placeholder="Описание" />
        <input type="text" v-model="item.quantity" @blur="normalizeNumber(item, 'quantity')" class="input-field" min="1"
          placeholder="Кол-во" />


        <select v-model="item.unit" class="input-field">
          <option value="шт">шт</option>
          <option value="час">час</option>
          <option value="день">день</option>
          <option value="м²">м²</option>
          <option value="м">м</option>
        </select>

        <input type="text" v-model="item.unit_price" @blur="normalizeNumber(item, 'unit_price')" class="input-field"
          placeholder="Цена за единицу" />

        <input v-model="item.category_input" @blur="applyCategory(item)" class="input-field" placeholder="Категория" />

        <div class="text-sm font-semibold flex items-center justify-center h-full">
          {{ formatCurrency(getItemTotal(item)) }}
        </div>

        <div class="flex items-center justify-center">
          <button type="button" @click="removeItem(item)" class="text-red-600 hover:underline text-sm">
            Удалить
          </button>
        </div>

      </div>

      <!-- промежуточный итог -->
      <div class="text-right font-semibold text-sm text-gray-600 border-t pt-2">
        Итог: {{ formatCurrency(getGroupTotal(groupItems)) }}
      </div>
    </div>

    <div class="flex flex-wrap items-center gap-4">
      <select v-model="selectedTemplateId" class="input-field">
        <option :value="null" disabled>Выберите шаблон</option>
        <option v-for="template in templatesStore.templates" :key="template.id" :value="template.id">
          {{ template.name }}
        </option>
      </select>
      <button type="button" @click="applyTemplate" class="btn-secondary">
        Добавить услуги из шаблона
      </button>
      <button type="button" @click="addItem" class="btn-secondary">
        Добавить услугу
      </button>
    </div>

    <div class="pt-6 border-t">
      <p class="text-right font-semibold text-lg">
        Общая сумма: {{ formatCurrency(total) }}
      </p>
      <p class="text-right text-gray-700" v-if="showVatSummary">
        НДС ({{ vatRate }}%): {{ formatCurrency(vat) }}<br/>
        Итого с НДС: {{ formatCurrency(totalWithVat) }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, reactive, watch, computed } from 'vue'
import { useTemplatesStore } from '@/store/templates'
import { useToast } from 'vue-toastification'

const templatesStore = useTemplatesStore()
const toast = useToast()
const selectedTemplateId = ref(null)

onMounted(() => {
  templatesStore.fetchTemplates()
})

const props = defineProps({
  modelValue: Array,
  vatEnabled: {
    type: Boolean,
    default: true
  },
  vatRate: {
    type: Number,
    default: 20
  },
  showVatSummary: {
    type: Boolean,
    default: true
  }
})
const emit = defineEmits(['update:modelValue'])

const items = reactive(props.modelValue || [])

watch(items, () => {
  emit('update:modelValue', items)
}, { deep: true })

function addItem() {
  items.push({
    name: '',
    description: '',
    quantity: '',
    unit: 'шт',
    unit_price: '',
    category_input: '',
    category: ''
  })
}

function removeItem(itemToRemove) {
  const index = items.indexOf(itemToRemove)
  if (index !== -1) items.splice(index, 1)
}

function getItemTotal(item) {
  const raw = item.quantity * item.unit_price
  return raw
}

function getGroupTotal(group) {
  return group.reduce((sum, item) => sum + getItemTotal(item), 0)
}

const groupedItems = computed(() => {
  const groups = {}
  for (const item of items) {
    const category = item.category?.trim() || 'Без категории'
    if (!groups[category]) groups[category] = []
    groups[category].push(item)
  }
  return groups
})

function applyCategory(item) {
  item.category = item.category_input.trim()
}

const total = computed(() => {
  return items.reduce((sum, item) => sum + getItemTotal(item), 0)
})

const vat = computed(() => props.vatEnabled ? total.value * (props.vatRate / 100) : 0)
const totalWithVat = computed(() => total.value + vat.value)

function formatCurrency(value) {
  return `${value.toFixed(2)} ₽`
}

function normalizeNumber(item, field) {
  let value = item[field]
  if (value === '') {
    return
  }
  if (typeof value === 'string') {
    value = value.replace(',', '.')
  }
  const parsed = parseFloat(value)
  item[field] = isNaN(parsed) ? 0 : parsed
}

function applyTemplate() {
  const template = templatesStore.templates.find(t => t.id === selectedTemplateId.value)
  if (template) {
    items.push(
      ...template.items.map(item => ({
        ...item,
        category_input: item.category || ''
      }))
    )
    toast.success(`Добавлены услуги из шаблона "${template.name}"`)
    selectedTemplateId.value = null
  }
}
</script>
