# frontend/src/components/EstimateForm.vue
<template>
  <form @submit.prevent="submit" class="space-y-8 border bg-gray rounded-2xl shadow-md p-6">
    <!-- 1. Основные поля в две колонки -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Название -->
      <div>
        <label class="block text-sm font-semibold text-gray-700 mb-1">Название сметы</label>
        <input v-model="estimate.name" type="text" placeholder="Введите название"
          class="w-full border border-gray-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300" />
      </div>
      <!-- Клиент -->
      <div>
        <label class="block text-sm font-semibold text-gray-700 mb-1">Клиент</label>
        <select v-model="estimate.client_id"
          class="w-full border border-gray-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300">
          <option :value="null">Выберите клиента</option>
          <option v-for="c in clients" :key="c.id" :value="c.id">
            {{ c.name }} <span v-if="c.company">({{ c.company }})</span>
          </option>
        </select>
      </div>
      <!-- Ответственный (на всю ширину) -->
      <div>
        <label class="block text-sm font-semibold text-gray-700 mb-1">Ответственный</label>
        <input v-model="estimate.responsible" type="text" placeholder="Кто отвечает за выполнение"
          class="w-full border border-gray-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300" />
      </div>
      <!-- Статус -->
      <div>
        <label class="block text-sm font-semibold text-gray-700 mb-1">Статус</label>
        <select v-model="estimate.status"
          class="w-full border border-gray-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300">
          <option value="draft">Черновик</option>
          <option value="sent">Отправлена</option>
          <option value="approved">Согласована</option>
          <option value="paid">Оплачена</option>
          <option value="cancelled">Отменена</option>
        </select>
      </div>

      <!-- Дата и место проведения -->
      <div>
        <label class="block text-sm font-semibold text-gray-700 mb-1">Дата и время мероприятия</label>
        <input v-model="eventDateTimeInput" type="datetime-local"
          class="w-full border border-gray-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300"
          placeholder="Выберите дату и время" />
      </div>
      <div>
        <label class="block text-sm font-semibold text-gray-700 mb-1">Место проведения мероприятия</label>
        <input v-model="estimate.event_place" type="text" placeholder="Адрес или площадка"
          class="w-full border border-gray-200 rounded-lg px-4 py-2" />
      </div>

      <!-- Заметки (на всю ширину) -->
      <div class="md:col-span-2">
        <label class="block text-sm font-semibold text-gray-700 mb-1">Заметки</label>
        <textarea v-model="estimate.notes" rows="2" placeholder="Дополнительная информация"
          class="w-full border border-gray-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none" />
      </div>



      <!-- НДС: красивый flex-блок на всю ширину -->
      <div class="md:col-span-2">
        <div class="flex items-center gap-2 bg-gray-50 rounded-lg px-2">
          <input type="checkbox" v-model="estimate.vat_enabled" id="vat"
            class="h-5 w-5 text-blue-600 accent-blue-600 focus:ring-blue-500" />
          <label for="vat" class="text-sm font-medium text-gray-700 select-none cursor-pointer">
            НДС
          </label>
          <template v-if="estimate.vat_enabled">
            <input type="number" min="0" max="100" step="1" v-model.number="estimate.vat_rate"
              class="border border-gray-300 rounded-lg px-2 py-1 w-16 focus:outline-none focus:ring-2 focus:ring-blue-300"
              placeholder="%" @input="checkVatRate" />
            <span class="text-gray-600 select-none">%</span>
          </template>
        </div>
      </div>


    </div>

    <!-- 2. Редактор услуг — растягивается на всю ширину -->
    <div>
      <EstimateItemsEditor v-model="estimate.items" :vat-enabled="estimate.vat_enabled" :vat-rate="estimate.vat_rate" />
    </div>

    <!-- 3. Кнопки -->
    <div class="flex justify-end space-x-4">
      <button type="button" @click="cancel"
        class="px-6 py-2 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 transition">
        Отмена
      </button>
      <button type="submit" class="px-6 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition">
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

async function submit() {
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
      toast.error(`Услуга №${i + 1}: количество должно быть > 0`)
      return false
    }
    if (!item.unit_price || item.unit_price <= 0) {
      toast.error(`Услуга №${i + 1}: цена должна быть > 0`)
      return false
    }
  }

  return true
}

</script>
