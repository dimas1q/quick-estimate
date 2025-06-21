# frontend/src/components/EstimateItemsEditor.vue
<template>
  <div class="space-y-8">
    <!-- Категории -->

    <div class="flex flex-wrap items-center gap-4 min-h-[40px] justify-end">
      <button type="button" @click="addCategory" class="qe-btn-secondary">
        Добавить категорию
      </button>

      <button type="button" class="qe-btn-secondary" @click="showTemplateSelect = !showTemplateSelect">
        Добавить из шаблона
      </button>

      <transition name="fade">
        <select v-if="showTemplateSelect" v-model="selectedTemplateId" @change="applyTemplate" class="qe-input"
          style="margin-left: 0">
          <option :value="null" disabled selected>Выберите шаблон</option>
          <option v-for="t in templatesStore.templates" :key="t.id" :value="t.id">
            {{ t.name }}
          </option>
        </select>
      </transition>
    </div>

    <transition-group name="fade" tag="div" class="space-y-8">
      <div v-for="(cat, idx) in categories" :key="cat.id"
        class="rounded-2xl border bg-white dark:bg-qe-black3 dark:border-qe-black2 shadow-md p-4 space-y-4">
        <!-- Категория: название и действия -->
        <div class="flex items-center gap-3 mb-2">
          <input v-model="cat.name" placeholder="Название категории"
            class="flex-1 border-0 border-b dark:border-qe-black2 text-lg font-semibold bg-transparent focus:ring-0 focus:border-blue-400" />
          <button @click="removeCategory(idx)" type="button" class="text-sm text-red-600 hover:underline">Удалить
            категорию</button>
        </div>



        <!-- Таблица услуг -->
        <div>
          <div
            :class="['grid gap-5 text-gray-600 text-xs dark:text-white font-semibold mb-2 text-center', props.useInternalPrice ? 'grid-cols-9' : 'grid-cols-7']">
            <div>Название</div>
            <div>Описание</div>
            <div>Кол-во</div>
            <div>Ед.</div>
            <template v-if="props.useInternalPrice">
              <div>Внутр. цена</div>
            </template>
            <div>Внеш. цена</div>
            <template v-if="props.useInternalPrice">
              <div>Итог (внутр.)</div>
            </template>
            <div>Итог (внеш.)</div>
            <div></div>
          </div>

          <transition-group name="fade" tag="div">
            <div v-for="(item, itemIdx) in cat.items" :key="itemIdx"
              :class="['grid items-center py-1 gap-4', props.useInternalPrice ? 'grid-cols-9' : 'grid-cols-7']">
              <input v-model="item.name" class="qe-input-sm" placeholder="Название" />
              <input v-model="item.description" class="qe-input-sm" placeholder="Описание" />
              <input type="number" min="0" step="any" v-model.number="item.quantity" class="qe-input-sm"
                placeholder="Кол-во" />
              <select v-model="item.unit" class="qe-input-sm">
                <option v-for="u in units" :key="u">{{ u }}</option>
              </select>
              <input v-if="props.useInternalPrice" type="number" min="0" step="any" v-model.number="item.internal_price"
                class="qe-input-sm" placeholder="Внутр. цена" />
              <input type="number" min="0" step="any" v-model.number="item.external_price" class="qe-input-sm"
                placeholder="Внеш. цена" />
              <div v-if="props.useInternalPrice" class="text-sm font-semibold text-center pr-2">
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

        <div class="flex justify-end">
          <button type="button" class="qe-btn-secondary" @click="addItem(idx)">
            + Добавить услугу
          </button>
        </div>

        <!-- Итоги по категории -->
        <div class="flex flex-col text-sm font-semibold mt-3 border-t dark:border-qe-black2 pt-2 items-end text-right">
          <span v-if="props.useInternalPrice">Итог по категории (внутр.): {{ formatCurrency(getCategoryInternal(cat))
            }}</span>
          <span>Итог по категории (внешн.): {{ formatCurrency(getCategoryExternal(cat)) }}</span>
        </div>

        <!-- Кнопка добавления услуги внутри категории -->

      </div>
    </transition-group>

    <!-- Использовать шаблон -->



    <!-- Итоги по всем категориям -->
    <div v-if="categories.some(cat => (cat.items && cat.items.length > 0)) && props.showSummary"
      class="pt-6 border-t dark:border-qe-black2">
      <p v-if="props.useInternalPrice" class="text-right font-semibold text-lg">
        Себестоимость: {{ formatCurrency(totalInternal) }}
      </p>
      <p class="text-right font-semibold text-lg">
        Продажная стоимость: {{ formatCurrency(totalExternal) }}
      </p>
      <p v-if="props.useInternalPrice" class="text-right font-semibold text-lg">
        Маржа: {{ formatCurrency(totalDiff) }}
      </p>
      <p class="text-right text-gray-700 dark:text-white" v-if="props.vatEnabled">
        НДС ({{ props.vatRate }}%): {{ formatCurrency(vat) }}<br />
        Итого с НДС: {{ formatCurrency(totalWithVat) }}
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
  useInternalPrice: {
    type: Boolean,
    default: true
  }
})
const emit = defineEmits(['update:modelValue'])

// Категории для работы
const categories = ref([])

onMounted(() => {
  templatesStore.fetchTemplates()
})

function convertToCategories(val) {
  if (!Array.isArray(val)) return []
  if (val.length && val[0]?.items) {
    return JSON.parse(JSON.stringify(val))
  }
  const groups = {}
  for (const item of val) {
    const cat = (item.category || 'Без категории').trim()
    if (!groups[cat]) groups[cat] = []
    groups[cat].push({ ...item })
  }
  return Object.entries(groups).map(([name, items]) => {
    const existing = categories.value.find(c => c.name === name)
    return {
      id: existing ? existing.id : `cat_${name}_${Math.random()}`,
      name,
      items,
    }
  })
}

watch(
  () => props.modelValue,
  (val) => {
    const newCats = convertToCategories(val)
    if (JSON.stringify(newCats) !== JSON.stringify(categories.value)) {
      categories.value = newCats
    }
  },
  { immediate: true, deep: true }
)

// Всегда синхронизируем наружу
watch(categories, () => {
  emit('update:modelValue', categories.value)
}, { deep: true })

// Категории/услуги
function addCategory() {
  categories.value.unshift({
    id: 'cat_' + Date.now() + Math.random(),
    name: '',
    items: [
      {
        name: '',
        description: '',
        quantity: 1,
        unit: 'шт',
        internal_price: 0,
        external_price: 0,
      }
    ],
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
const totalInternal = computed(() =>
  props.useInternalPrice ? categories.value.reduce((sum, cat) => sum + getCategoryInternal(cat), 0) : 0
)
const totalExternal = computed(() => categories.value.reduce((sum, cat) => sum + getCategoryExternal(cat), 0))
const totalDiff = computed(() => props.useInternalPrice ? totalExternal.value - totalInternal.value : 0)
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
        categories.value.unshift(cat)
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

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: all 0.22s cubic-bezier(.4, 0, .2, 1);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(16px) scale(0.96);
}
</style>