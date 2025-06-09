# frontend/src/components/EstimateItemsEditor.vue
<template>
  <div class="space-y-8">
    <!-- Категории -->
    <transition-group name="fade" tag="div" class="space-y-8">
      <div v-for="(cat, idx) in categories" :key="cat.id"
        class="rounded-2xl border bg-white dark:bg-qe-black3 dark:border-qe-black2 shadow-md p-4 space-y-4">
        <!-- Категория: название и действия -->
        <div class="flex items-center gap-3 mb-2">
          <input v-model="cat.name" placeholder="Название категории"
            class="flex-1 border-0 border-b dark:border-qe-black2 text-lg font-semibold bg-transparent focus:ring-0 focus:border-blue-400" />
          <button @click="removeCategory(idx)" type="button" class="text-red-500 hover:text-red-700 text-sm">Удалить
            категорию</button>
        </div>

        <!-- Таблица услуг -->
        <div>
          <div class="grid grid-cols-9 gap-5 text-gray-600 text-xs dark:text-white font-semibold mb-2 text-center">
            <div>Название</div>
            <div>Описание</div>
            <div>Кол-во</div>
            <div>Ед.</div>
            <div>Внутр. цена</div>
            <div>Внеш. цена</div>
            <div>Итог (внутр.)</div>
            <div>Итог (внеш.)</div>
            <div>Действие</div>
          </div>

          <transition-group name="fade" tag="div">
            <div v-for="(item, itemIdx) in cat.items" :key="itemIdx" class="grid grid-cols-9 items-center py-1 gap-4">
              <input v-model="item.name" class="qe-input-sm" placeholder="Название" />
              <input v-model="item.description" class="qe-input-sm" placeholder="Описание" />
              <input type="number" min="0" step="any" v-model.number="item.quantity" class="qe-input-sm"
                placeholder="Кол-во" />
              <select v-model="item.unit" class="qe-input-sm">
                <option v-for="u in units" :key="u">{{ u }}</option>
              </select>
              <input type="number" min="0" step="any" v-model.number="item.internal_price" class="qe-input-sm"
                placeholder="Внутр. цена" />
              <input type="number" min="0" step="any" v-model.number="item.external_price" class="qe-input-sm"
                placeholder="Внеш. цена" />
              <div class="text-sm font-semibold text-center pr-2">
                {{ formatCurrency(getItemInternal(item)) }}
              </div>
              <div class="text-sm font-semibold text-center pr-2">
                {{ formatCurrency(getItemExternal(item)) }}
              </div>
              <button type="button" @click="removeItem(idx, itemIdx)" class="text-red-600 hover:underline text-xs">
                Удалить
              </button>
            </div>
          </transition-group>
        </div>

        <!-- Итоги по категории -->
        <div class="flex flex-col text-sm font-semibold mt-3 border-t dark:border-qe-black2 pt-2 items-end text-right">
          <span>Итог по категории (внутр.): {{ formatCurrency(getCategoryInternal(cat)) }}</span>
          <span>Итог по категории (внешн.): {{ formatCurrency(getCategoryExternal(cat)) }}</span>
        </div>

        <!-- Кнопка добавления услуги внутри категории -->
        <div class="flex justify-end">
          <button type="button" class="qe-btn-secondary" @click="addItem(idx)">
            + Добавить услугу
          </button>
        </div>
      </div>
    </transition-group>

    <!-- Использовать шаблон -->
    <div class="flex flex-wrap items-center gap-4 min-h-[40px]">
      <button type="button" @click="addCategory" class="qe-btn-secondary">
        Добавить категорию
      </button>

      <button type="button" class="qe-btn-secondary" @click="showTemplateSelect = !showTemplateSelect">
        Добавить из шаблона
      </button>

      <transition name="fade">
        <select v-if="showTemplateSelect" v-model="selectedTemplateId" @change="applyTemplate" class="qe-input "
          style="margin-left: 0">
          <option :value="null" disabled selected>Выберите шаблон</option>
          <option v-for="t in templatesStore.templates" :key="t.id" :value="t.id">
            {{ t.name }}
          </option>
        </select>
      </transition>


    </div>


    <!-- Итоги по всем категориям -->
    <div v-if="categories.some(cat => (cat.items && cat.items.length > 0)) && props.showSummary"
      class="pt-6 border-t dark:border-qe-black2">
      <p class="text-right font-semibold text-lg">
        Общая сумма (внутр.): {{ formatCurrency(totalInternal) }}
      </p>
      <p class="text-right font-semibold text-lg">
        Общая сумма (внешн.): {{ formatCurrency(totalExternal) }}
      </p>
      <p class="text-right font-semibold text-lg">
        Разница: {{ formatCurrency(totalDiff) }}
      </p>
      <p class="text-right text-gray-700 dark:text-white" v-if="props.vatEnabled">
        НДС ({{ props.vatRate }}%): {{ formatCurrency(vat) }}<br />
        Итог с НДС: {{ formatCurrency(totalWithVat) }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useTemplatesStore } from '@/store/templates'

const templatesStore = useTemplatesStore()
const units = [
  "шт", "час", "день", "м²", "м", "чел.", "комп.", "усл.", "чел/час", "чел/смена", "проект", "пог.м", "рейс", "машина"
]

const props = defineProps({
  modelValue: Array,
  vatEnabled: Boolean,
  vatRate: Number,
  showSummary: {
    type: Boolean,
    default: true
  },
})
const emit = defineEmits(['update:modelValue'])

// Категории для работы
const categories = ref([])

// --- Инициализация и преобразование modelValue (важно!)
onMounted(() => {
  templatesStore.fetchTemplates() // Загружаем шаблоны при монтировании
  if (props.modelValue && Array.isArray(props.modelValue)) {
    if (props.modelValue.length && props.modelValue[0]?.items) {
      // Уже новая структура
      categories.value = JSON.parse(JSON.stringify(props.modelValue))
    } else {
      // Плоский массив услуг — преобразуем в категории
      const groups = {}
      for (const item of props.modelValue) {
        const cat = (item.category || 'Без категории').trim()
        if (!groups[cat]) groups[cat] = []
        groups[cat].push({ ...item })
      }
      categories.value = Object.entries(groups).map(([name, items]) => ({
        id: Date.now() + Math.random(),
        name,
        items,
      }))
    }
  }
})

// Всегда синхронизируем наружу
watch(categories, () => {
  emit('update:modelValue', categories.value)
}, { deep: true })

// Категории/услуги
function addCategory() {
  categories.value.push({
    id: 'cat_' + Date.now() + Math.random(),
    name: '',
    items: [],
  })
}
function removeCategory(idx) {
  categories.value.splice(idx, 1)
}
function addItem(catIdx) {
  categories.value[catIdx].items.push({
    name: '',
    description: '',
    quantity: 1,
    unit: 'шт',
    internal_price: 0,
    external_price: 0,
  })
}
function removeItem(catIdx, itemIdx) {
  categories.value[catIdx].items.splice(itemIdx, 1)
}

// --- Итоги
function getItemInternal(item) {
  return (item.quantity || 0) * (item.internal_price || 0)
}
function getItemExternal(item) {
  return (item.quantity || 0) * (item.external_price || 0)
}
function getCategoryInternal(cat) {
  return (cat.items || []).reduce((sum, item) => sum + getItemInternal(item), 0)
}
function getCategoryExternal(cat) {
  return (cat.items || []).reduce((sum, item) => sum + getItemExternal(item), 0)
}
const totalInternal = computed(() => categories.value.reduce((sum, cat) => sum + getCategoryInternal(cat), 0))
const totalExternal = computed(() => categories.value.reduce((sum, cat) => sum + getCategoryExternal(cat), 0))
const totalDiff = computed(() => totalExternal.value - totalInternal.value)
const vat = computed(() => props.vatEnabled ? totalExternal.value * (props.vatRate / 100) : 0)
const totalWithVat = computed(() => totalExternal.value + vat.value)

function formatCurrency(value) {
  return `${(value || 0).toFixed(2)} ₽`
}


const showTemplateSelect = ref(false)
const selectedTemplateId = ref(null)

function applyTemplate() {
  const template = templatesStore.templates.find(t => t.id === selectedTemplateId.value)
  if (template) {
    // Группируем услуги по категориям из шаблона
    const tplCats = getTemplateCategories(template)

    for (const tplCat of tplCats) {
      // Проверяем — есть такая категория уже?
      let cat = categories.value.find(c => c.name.trim() === tplCat.name.trim())
      if (!cat) {
        cat = {
          id: Date.now() + Math.random(),
          name: tplCat.name,
          items: [],
        }
        categories.value.push(cat)
      }
      cat.items.push(...tplCat.items.map(item => {
        const { id, ...rest } = item
        return rest // Копируем без id
      }))
    }

    // Сброс селектора
    showTemplateSelect.value = false
    selectedTemplateId.value = null
  }
}

// вспомогательная функция группировки
function getTemplateCategories(template) {
  // Если template.items плоский, сгруппировать
  const groups = {}
  for (const item of template.items) {
    const cat = (item.category || 'Без категории').trim()
    if (!groups[cat]) groups[cat] = []
    groups[cat].push({ ...item })
  }
  return Object.entries(groups).map(([name, items]) => ({
    name,
    items,
  }))
}


</script>
