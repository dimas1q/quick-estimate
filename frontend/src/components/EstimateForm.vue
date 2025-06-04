# frontend/src/components/EstimateForm.vue
<template>
  <form @submit.prevent="submit"
    class="space-y-8 border dark:border-qe-black2 bg-white dark:bg-qe-black rounded-2xl shadow-md p-6">
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
        <select v-model="estimate.client_id" class="w-full qe-input">
          <option :value="null">Выберите клиента</option>
          <option v-for="c in clients" :key="c.id" :value="c.id">
            {{ c.name }} <span v-if="c.company">({{ c.company }})</span>
          </option>
        </select>
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
        <select v-model="estimate.status" class="w-full qe-input">
          <option value="draft">Черновик</option>
          <option value="sent">Отправлена</option>
          <option value="approved">Согласована</option>
          <option value="paid">Оплачена</option>
          <option value="cancelled">Отменена</option>
        </select>
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

      <!-- Заметки (на всю ширину) -->
      <div class="md:col-span-2">
        <label class="block text-sm font-semibold text-gray-700 dark:text-white mb-1">Заметки</label>
        <textarea v-model="estimate.notes" rows="2" placeholder="Дополнительная информация"
          class="w-full qe-textarea resize-none" />
      </div>



      <!-- НДС: современный и компактный блок -->
      <div class="md:col-span-2">
        <div :class="[
          'flex items-center gap-4 rounded-xl p-3 border dark:border-qe-black2 shadow-sm transition min-h-[64px]',
          estimate.vat_enabled
            ? 'bg-white-50  dark:bg-qe-black dark:border-blue-600'
            : 'bg-white-50  dark:bg-qe-black dark:border-qe-black2'
        ]">
          <label for="vat" class="flex items-center gap-3 cursor-pointer select-none">
            <input type="checkbox" v-model="estimate.vat_enabled" id="vat"
              class="h-5 w-5 accent-blue-600 rounded border-gray-300 transition focus:ring-blue-500" />
            <span class="text-base font-semibold text-gray-800 dark:text-white">НДС</span>
          </label>

          <transition name="fade">
            <div v-if="estimate.vat_enabled" class="flex items-center gap-2">
              <div class="relative">
                <input type="number" min="0" max="100" step="1" v-model.number="estimate.vat_rate"
                  class="w-22 pr-8 pl-3 py-1.5 border rounded-lg text-base font-semibold focus:outline-none focus:ring-2 focus:ring-blue-300 bg-white dark:bg-qe-black dark:border-qe-black2 dark:text-white dark:border-blue-800"
                  placeholder="%" @input="checkVatRate" />
                <span
                  class="absolute right-2 top-1/2 -translate-y-1/2 text-base text-gray-700 dark:text-white pointer-events-none">%</span>
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
      <EstimateItemsEditor v-model="estimate.items" :vat-enabled="estimate.vat_enabled" :vat-rate="estimate.vat_rate" />
    </div>

    <!-- 3. Кнопки -->
    <div class="flex justify-end space-x-2">
      <button type="button" @click="cancel" class="qe-btn-secondary">
        Отмена
      </button>
      <button type="submit" class="qe-btn">
        Сохранить
      </button>
    </div>
  </form>
</template>

<script setup>
import { reactive, watch, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useEstimatesStore } from '@/store/estimates'
import { useClientsStore } from '@/store/clients'
import EstimateItemsEditor from '@/components/EstimateItemsEditor.vue'
import { useToast } from 'vue-toastification'
import QeDatePicker from '@/components/QeDatePicker.vue'

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
  notes: '',
  event_datetime: '',
  event_place: '',
  items: [],
  vat_enabled: true,
  vat_rate: 20,
  status: 'draft'
})

const clients = computed(() => clientsStore.clients)

onMounted(async () => {
  await clientsStore.fetchClients()
  if (store.importedEstimate) {
    estimate.name = store.importedEstimate.name || ''
    estimate.client_id = store.importedEstimate.client?.id || null
    estimate.responsible = store.importedEstimate.responsible || ''
    estimate.event_datetime = store.importedEstimate.event_datetime || ''
    estimate.event_place = store.importedEstimate.event_place || ''
    estimate.notes = store.importedEstimate.notes || ''
    estimate.vat_enabled = store.importedEstimate.vat_enabled ?? true
    estimate.vat_rate = store.importedEstimate.vat_rate ?? 20.0
    estimate.status = store.importedEstimate.status || 'draft'

    estimate.items.splice(0)
    for (const item of store.importedEstimate.items || []) {
      estimate.items.push({
        ...item,
        category_input: item.category || ''
      })
    }

    store.importedEstimate = null
  }
})


watch(() => props.initial, (value) => {
  if (value) {
    Object.assign(estimate, {
      name: props.mode === 'copy' ? `Копия: ${value.name}` : value.name,
      client_id: value.client?.id || null,
      responsible: value.responsible || '',
      event_datetime: value.event_datetime || '',
      event_place: value.event_place || '',
      notes: value.notes || '',
      vat_enabled: value.vat_enabled ?? true,
      vat_rate: value.vat_rate ?? 20.0,
      status: value.status || 'draft',
      items: (value.items || []).map(item => ({
        ...item,
        category_input: item.category || ''
      }))
    })
  }
}, { immediate: true })

function flattenItems(categories) {
  // Возвращает плоский массив с подставленной категорией
  return categories.flatMap(cat =>
    cat.items.map(item => ({ ...item, category: cat.name }))
  )
}


async function submit() {
  // Преобразовать из categories в плоский массив услуг (если нужно)
  if (estimate.items.length && estimate.items[0]?.items) {
    estimate.items = flattenItems(estimate.items)
  }
  if (!validateEstimate()) return

  let result
  if (props.mode === 'edit') {
    result = await store.updateEstimate(props.initial.id, estimate)
    emit('updated')
  } else {
    result = await store.createEstimate(estimate)
    toast.success('Смета создана')
    router.push(`/estimates/${result.id}`)
  }
}

function cancel() {
  router.back()
}

const eventDateTimeInput = computed({
  get() {
    if (!estimate.event_datetime) return ''
    // Обрезать лишнее: только yyyy-MM-ddTHH:mm
    // Если приходит ISO: 2024-06-01T13:30:00.000Z
    const dt = estimate.event_datetime
    if (dt.length >= 16) return dt.slice(0, 16)
    return dt
  },
  set(val) {
    estimate.event_datetime = val
  }
})

function validateEstimate() {
  if (!estimate.name?.trim()) {
    toast.error("Название сметы обязательно")
    return false
  }
  if (!estimate.client_id) {
    toast.error("Выберите клиента")
    return false
  }
  if (!estimate.responsible?.trim()) {
    toast.error("Ответственный обязателен")
    return false
  }
  if (!estimate.items.length) {
    toast.error("Добавьте хотя бы одну услугу")
    return false
  }

  for (const [i, item] of estimate.items.entries()) {
    if (!item.name?.trim()) {
      toast.error(`Услуга №${i + 1}: название обязательно`)
      return false
    }
    if (!item.quantity || item.quantity <= 0) {
      toast.error(`Услуга ${item.name}: количество должно быть > 0`)
      return false
    }
    if (!item.internal_price || item.internal_price <= 0) {
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