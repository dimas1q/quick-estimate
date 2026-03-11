# frontend/src/components/EstimateForm.vue
<template>
  <form @submit.prevent="submit"
    class="space-y-8 border dark:border-qe-black2 bg-white dark:bg-qe-black3 rounded-2xl shadow-md p-6">
    <!-- 1. Основные поля в две колонки -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Название -->
      <div>
        <label class="block text-sm font-semibold text-gray-700 dark:text-white mb-1">Название сметы</label>
        <input v-model="estimate.name" type="text" placeholder="Введите название" class="w-full qe-input" />
      </div>
      <!-- Клиент -->
      <div>
        <label class="block text-sm font-semibold dark:text-white text-gray-700 mb-1">Клиент</label>
        <QeSingleSelect v-model="estimate.client_id" :options="clientOptions" placeholder="Без клиента"
          class="w-full mt-1" />
      </div>
      <!-- Ответственный (на всю ширину) -->
      <div>
        <label class="block text-sm font-semibold dark:text-white text-gray-700 mb-1">Ответственный</label>
        <input v-model="estimate.responsible" type="text" placeholder="Кто отвечает за выполнение"
          class="w-full qe-input" />
      </div>
      <!-- Статус -->
      <div>
        <label class="block text-sm font-semibold text-gray-700 dark:text-white mb-1">Статус</label>
        <QeSingleSelect v-model="estimate.status" :options="statusOptions" placeholder="Черновик" class="w-full mt-1" />
      </div>

      <!-- Дата и место проведения -->
      <div>
        <label class="block text-sm font-semibold text-gray-700 dark:text-white mb-1">Дата и время мероприятия</label>
        <QeDatePicker v-model="estimate.event_datetime" label="Дата и время мероприятия"
          placeholder="Дата и время мероприятия" :format="format" enableTimePicker=true />
      </div>
      <div>
        <label class="block text-sm font-semibold text-gray-700 dark:text-white mb-1">Место проведения
          мероприятия</label>
        <input v-model="estimate.event_place" type="text" placeholder="Адрес или площадка" class="w-full qe-input" />
      </div>

      <!-- Использовать внутреннюю цену -->
      <div class="md:col-span-2">
        <div :class="[
          'flex items-center gap-2 rounded-xl p-2 border dark:border-qe-black2 shadow-sm transition min-h-[64px]',
          estimate.use_internal_price
            ? 'bg-white-50  dark:bg-qe-black3 dark:border-blue-600'
            : 'bg-white-50  dark:bg-qe-black3 dark:border-qe-black2'
        ]">
          <div class="flex">
          </div>
          <label for="internal_price" class="flex items-center gap-2 cursor-pointer select-none">
            <input type="checkbox" v-model="estimate.use_internal_price" id="internal_price"
              class="h-4 w-4 accent-blue-600 rounded border-gray-300 transition focus:ring-blue-500" />
            <span class="text-sm font-semibold text-gray-800 dark:text-white">Внутренняя цена</span>
          </label>
          <span class="ml-auto text-xs text-gray-400 dark:text-gray-500 font-normal" v-if="estimate.use_internal_price">
            Внутренняя цена будет использоваться для расчёта маржи
          </span>
        </div>
      </div>


      <!-- НДС: современный и компактный блок -->
      <div class="md:col-span-2">
        <div :class="[
          'flex items-center gap-2 rounded-xl p-2 border dark:border-qe-black2 shadow-sm transition min-h-[64px]',
          estimate.vat_enabled
            ? 'bg-white-50  dark:bg-qe-black3 dark:border-blue-600'
            : 'bg-white-50  dark:bg-qe-black3 dark:border-qe-black2'
        ]">
          <div class="flex">
          </div>
          <label for="vat" class="flex items-center gap-2 cursor-pointer select-none">
            <input type="checkbox" v-model="estimate.vat_enabled" id="vat"
              class="h-4 w-4 accent-blue-600 rounded border-gray-300 transition focus:ring-blue-500" />
            <span class="text-sm font-semibold text-gray-800 dark:text-white">НДС</span>
          </label>

          <transition name="fade">
            <div v-if="estimate.vat_enabled" class="flex items-center">
              <div class="relative">
                <input maxlength="2" v-model.number="estimate.vat_rate"
                  class="w-16 pl-3 py-1.5 border rounded-lg text-sm  focus:outline-none focus:ring-2 focus:ring-blue-300 bg-white dark:bg-qe-black3 dark:border-qe-black2 dark:text-white dark:border-blue-800"
                  @input="checkVatRate" />
                <span
                  class="absolute right-3.5 top-1/2 -translate-y-1/2 text-sm text-gray-700 font-semibold dark:text-white pointer-events-none">%</span>
              </div>
            </div>
          </transition>
          <span class="ml-auto text-xs text-gray-400 dark:text-gray-500 font-normal" v-if="estimate.vat_enabled">НДС
            будет включён в итоговую сумму</span>
        </div>
      </div>



    </div>

    <!-- 2. Редактор услуг — растягивается на всю ширину -->
    <div>
      <EstimateItemsEditor v-model="estimate.items" :vat-enabled="estimate.vat_enabled" :vat-rate="estimate.vat_rate"
        :use-internal-price="estimate.use_internal_price" />
    </div>

    <!-- 3. Кнопки -->
    <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
      <span class="text-xs" :class="autosaveMessageClass">
        {{ autosaveMessage }}
      </span>
      <div class="flex justify-end space-x-2">
        <button type="button" @click="cancel" class="qe-btn-secondary">
          Отмена
        </button>
        <button type="submit" class="qe-btn" :disabled="isSubmitting">
          {{ isSubmitting ? 'Сохранение...' : 'Сохранить' }}
        </button>
      </div>
    </div>
  </form>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import EstimateItemsEditor from '@/components/EstimateItemsEditor.vue'
import QeDatePicker from '@/components/QeDatePicker.vue'
import QeSingleSelect from '@/components/QeSingleSelect.vue'
import { useClientsStore } from '@/store/clients'
import { useEstimatesStore } from '@/store/estimates'

const AUTOSAVE_DELAY_MS = 1200

const props = defineProps({
  initial: Object,
  mode: {
    type: String,
    default: 'create'
  }
})
const emit = defineEmits(['updated'])

const store = useEstimatesStore()
const clientsStore = useClientsStore()
const toast = useToast()
const router = useRouter()

const estimate = reactive({
  name: '',
  client_id: null,
  responsible: '',
  event_datetime: '',
  event_place: '',
  items: [],
  vat_enabled: true,
  vat_rate: 20,
  use_internal_price: true,
  status: 'draft'
})

const autosaveState = ref('idle')
const autosaveAt = ref(null)
const autosaveEnabled = ref(false)
const isHydrating = ref(false)
const isSubmitting = ref(false)
let autosaveTimer = null

const clients = computed(() => clientsStore.clients)
const draftStorageKey = computed(() => {
  if (props.mode === 'copy') {
    return `qe_estimate_draft_copy_${props.initial?.id || 'new'}`
  }
  return 'qe_estimate_draft_create'
})
const autosaveMessage = computed(() => {
  if (autosaveState.value === 'saving') return 'Автосохранение...'
  if (autosaveState.value === 'pending') return 'Есть несохраненные изменения'
  if (autosaveState.value === 'saved' && autosaveAt.value) {
    return `Черновик сохранен: ${formatAutosaveTime(autosaveAt.value)}`
  }
  if (autosaveState.value === 'local_saved' && autosaveAt.value) {
    return `Локальный черновик сохранен: ${formatAutosaveTime(autosaveAt.value)}`
  }
  if (autosaveState.value === 'restored') return 'Восстановлен черновик из браузера'
  if (autosaveState.value === 'error') return 'Ошибка автосохранения'
  return ''
})
const autosaveMessageClass = computed(() => {
  if (autosaveState.value === 'error') return 'text-red-500'
  if (autosaveState.value === 'pending') return 'text-amber-600'
  if (autosaveState.value === 'saving') return 'text-blue-500'
  if (autosaveState.value === 'saved' || autosaveState.value === 'local_saved' || autosaveState.value === 'restored') {
    return 'text-emerald-600'
  }
  return 'text-transparent'
})

const clientOptions = computed(() => [
  { value: null, label: 'Без клиента' },
  ...clients.value.map(c => ({
    value: c.id,
    label: c.company ? `${c.name} (${c.company})` : c.name
  }))
])

const statusOptions = [
  { value: 'draft', label: 'Черновик' },
  { value: 'sent', label: 'Отправлена' },
  { value: 'approved', label: 'Согласована' },
  { value: 'paid', label: 'Оплачена' },
  { value: 'cancelled', label: 'Отменена' }
]

onMounted(async () => {
  await clientsStore.fetchClients()

  if (store.importedEstimate) {
    applyEstimateData(store.importedEstimate)
    store.importedEstimate = null
  } else if (props.mode !== 'edit') {
    const localDraft = loadDraftFromLocal()
    if (localDraft) {
      applyEstimateData(localDraft)
      autosaveState.value = 'restored'
    }
  }

  autosaveEnabled.value = true
})

onUnmounted(() => {
  if (autosaveTimer) {
    clearTimeout(autosaveTimer)
  }
})

watch(() => props.initial, (value) => {
  if (!value) return
  applyEstimateData(value, { isCopy: props.mode === 'copy' })
}, { immediate: true })

watch(estimate, () => {
  if (!autosaveEnabled.value || isHydrating.value || isSubmitting.value) return
  scheduleAutosave()
}, { deep: true })

function mapItemsForForm(items = []) {
  return items.map(item => ({
    ...item,
    category_input: item.category || ''
  }))
}

function applyEstimateData(value, options = {}) {
  isHydrating.value = true
  Object.assign(estimate, {
    name: options.isCopy ? `Копия: ${value.name}` : (value.name || ''),
    client_id: value.client?.id ?? value.client_id ?? null,
    responsible: value.responsible || '',
    event_datetime: value.event_datetime || '',
    event_place: value.event_place || '',
    vat_enabled: value.vat_enabled ?? true,
    vat_rate: value.vat_rate ?? 20,
    use_internal_price: value.use_internal_price ?? true,
    status: value.status || 'draft',
    items: mapItemsForForm(value.items || [])
  })
  isHydrating.value = false
}

function flattenItems(categories) {
  return categories.flatMap(cat =>
    (cat.items || []).map(item => ({ ...item, category: cat.name || '' }))
  )
}

function prepareEstimatePayload(source) {
  const payload = JSON.parse(JSON.stringify(source))
  if (Array.isArray(payload.items) && payload.items.length && payload.items[0]?.items) {
    payload.items = flattenItems(payload.items)
  }

  payload.items = (payload.items || []).map(item => ({
    id: item.id ?? undefined,
    name: item.name || '',
    description: item.description || '',
    quantity: Number(item.quantity ?? 0),
    unit: item.unit || 'шт',
    internal_price: Number(item.internal_price ?? 0),
    external_price: Number(item.external_price ?? 0),
    category: item.category || item.category_input || ''
  }))
  payload.name = payload.name || ''
  payload.responsible = payload.responsible || ''
  payload.client_id = payload.client_id || null
  payload.event_datetime = payload.event_datetime || null
  payload.event_place = payload.event_place || null
  return payload
}

function scheduleAutosave() {
  if (autosaveTimer) {
    clearTimeout(autosaveTimer)
  }
  autosaveState.value = 'pending'
  autosaveTimer = setTimeout(() => {
    performAutosave()
  }, AUTOSAVE_DELAY_MS)
}

async function performAutosave() {
  const payload = prepareEstimatePayload(estimate)
  try {
    autosaveState.value = 'saving'
    if (props.mode === 'edit' && props.initial?.id) {
      await store.autosaveEstimate(props.initial.id, payload)
      autosaveState.value = 'saved'
      autosaveAt.value = new Date()
      return
    }

    localStorage.setItem(draftStorageKey.value, JSON.stringify(payload))
    autosaveState.value = 'local_saved'
    autosaveAt.value = new Date()
  } catch (e) {
    console.error(e)
    autosaveState.value = 'error'
  }
}

function loadDraftFromLocal() {
  try {
    const raw = localStorage.getItem(draftStorageKey.value)
    return raw ? JSON.parse(raw) : null
  } catch (e) {
    console.error(e)
    return null
  }
}

function clearDraftFromLocal() {
  localStorage.removeItem(draftStorageKey.value)
}

async function submit() {
  const payload = prepareEstimatePayload(estimate)
  if (!validateEstimate(payload)) return

  try {
    isSubmitting.value = true
    if (props.mode === 'edit') {
      await store.updateEstimate(props.initial.id, payload)
      autosaveState.value = 'saved'
      autosaveAt.value = new Date()
      emit('updated')
      return
    }

    const result = await store.createEstimate(payload)
    clearDraftFromLocal()
    toast.success('Смета создана')
    router.push(`/estimates/${result.id}`)
  } finally {
    isSubmitting.value = false
  }
}

function cancel() {
  router.back()
}

const format = (date) => {
  if (!date) return ''
  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const year = date.getFullYear()
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${day}.${month}.${year} ${hours}:${minutes}`
}

function formatAutosaveTime(date) {
  return date.toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

function checkVatRate() {
  estimate.vat_rate = Math.round(estimate.vat_rate)
  if (isNaN(estimate.vat_rate)) {
    estimate.vat_rate = ''
    return
  }
  if (estimate.vat_rate > 99) estimate.vat_rate = 99
  if (estimate.vat_rate < 1) estimate.vat_rate = ''
}

function validateEstimate(data) {
  if (!data.name?.trim()) {
    toast.error('Название сметы обязательно')
    return false
  }
  if (!data.responsible?.trim()) {
    toast.error('Ответственный обязателен')
    return false
  }

  if (data.vat_enabled) {
    if (
      typeof data.vat_rate !== 'number' ||
      !Number.isInteger(data.vat_rate) ||
      data.vat_rate < 1 ||
      data.vat_rate > 99
    ) {
      toast.error('НДС должен быть целым числом от 1 до 99')
      return false
    }
  }

  if (!data.items.length) {
    toast.error('Добавьте хотя бы одну услугу')
    return false
  }

  for (const [i, item] of data.items.entries()) {
    if (!item.name?.trim()) {
      toast.error(`Услуга №${i + 1}: название обязательно`)
      return false
    }
    if (!item.quantity || item.quantity <= 0) {
      toast.error(`Услуга ${item.name}: количество должно быть > 0`)
      return false
    }
    if (data.use_internal_price && (!item.internal_price || item.internal_price <= 0)) {
      toast.error(`Услуга ${item.name}: внутренняя цена должна быть > 0`)
      return false
    }
    if (!item.external_price || item.external_price <= 0) {
      toast.error(`Услуга ${item.name}: внешняя цена должна быть > 0`)
      return false
    }
  }

  return true
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
