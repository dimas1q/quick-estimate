
<template>
  <div class="flex flex-col items-center from-gray-50 via-white to-gray-100 px-2 py-10">
    <!-- Хедер и бар управления -->
    <div class="w-full max-w-5xl flex flex-col gap-4 mb-8">
      <!-- Навигационный переключатель -->
      <div class="flex items-center justify-between mb-2">
        <div class="flex items-center gap-1 bg-gray-100 dark:bg-qe-black2 rounded-xl p-1">
          <button
            :class="['px-5 py-2 rounded-lg text-sm font-semibold transition', viewMode === 'my' ? 'bg-white dark:bg-gray-900 text-blue-600 shadow' : 'text-gray-500 hover:text-blue-600']"
            @click="setViewMode('my')">Мои сметы</button>
          <button
            :class="['px-5 py-2 rounded-lg text-sm font-semibold transition', viewMode === 'fav' ? 'bg-white dark:bg-gray-900 text-blue-600 shadow' : 'text-gray-500 hover:text-blue-600']"
            @click="setViewMode('fav')">Избранное</button>
        </div>
        <div class="flex gap-2">
          <router-link to="/estimates/create" class="qe-btn px-4">
            Создать смету
          </router-link>
          <button @click="triggerFileInput" class="qe-btn px-4">
            Импорт сметы
          </button>
          <input type="file" ref="fileInput" accept="application/json" @change="handleFile" class="hidden" />
        </div>
      </div>
      <!-- Бар фильтров -->
      <div class="flex gap-2">
        <input v-model="filters.name" class="qe-input flex-1" type="text" autocomplete="off"
          placeholder="Название сметы" />
        <QeSingleSelect v-model="filters.client" :options="clientOptions" placeholder="Все клиенты" class="flex-1" />
        <QeSingleSelect v-model="filters.status" :options="statusOptions" placeholder="Все статусы" class="flex-1" />
        <QeDatePicker v-model="filters.date_from" placeholder="Дата с" :format="format" class="flex-1" />
        <QeDatePicker v-model="filters.date_to" placeholder="Дата по" :format="format" class="flex-1" />
        <button @click="applyFilters" class="qe-btn px-4 min-w-[100px]">Найти</button>
        <button @click="resetFilters" class="qe-btn-secondary px-4 min-w-[100px]">Сброс</button>
      </div>
    </div>

    <!-- Список смет -->
    <div class="w-full max-w-5xl space-y-5">
      <div v-if="isLoading" class="space-y-3">
        <div v-for="n in 3" :key="n" class="rounded-2xl bg-white/60 shadow animate-pulse p-6 h-24" />
      </div>
      <div v-else>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div v-for="e in filteredEstimates" :key="e.id"
            class="border border-gray-200 dark:border-qe-black2 rounded-2xl shadow-sm hover:shadow-lg p-5 bg-white dark:bg-qe-black3 transition flex flex-col relative">
            <button
              class="absolute top-2 right-2 rounded-full bg-transparent p-1 transition flex items-center justify-center"
              style="width: 44px; height: 44px; overflow: visible;"
              :aria-label="e.is_favorite ? 'Убрать из избранного' : 'Добавить в избранное'" @click="toggleFavorite(e)">
              <Star v-if="e.is_favorite" class="w-6 h-6 text-yellow-400 fill-yellow-400" :stroke-width="1.5" />
              <Star v-else class="w-6 h-6 text-gray-300 hover:text-yellow-400 transition" :stroke-width="1.5" />
            </button>
            <router-link :to="`/estimates/${e.id}`" class="font-semibold text-lg hover:text-blue-600">{{ e.name
              }}</router-link>
            <div class="text-sm dark:text-gray-400">
              Клиент: {{ e.client?.name || '—' }}
              <span v-if="e.client?.company">({{ e.client.company }})</span>
            </div>
            <div class="text-sm dark:text-gray-400">Ответственный: {{ e.responsible || '—' }}</div>
            <div class="text-xs text-gray-500 mt-2">Создана: {{ new Date(e.date).toLocaleString() }}</div>
            <div class="text-xs text-gray-500">Обновлена: {{ new Date(e.date).toLocaleString() }}</div>
          </div>
        </div>
        <div v-if="filteredEstimates.length === 0"
          class="text-center text-gray-400 border border-gray-200 dark:border-qe-black2 p-6 rounded-2xl bg-white/70 dark:bg-qe-black2/80 mt-4">
          <p>Сметы отсутствуют.</p>
        </div>
        <QePagination :total="totalEstimates" :per-page="perPage" :page="currentPage" @update:page="changePage"
          class="mt-6" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import { useEstimatesStore } from '@/store/estimates'
import { useClientsStore } from '@/store/clients'
import { Star } from 'lucide-vue-next'

import QeDatePicker from '@/components/QeDatePicker.vue'
import QePagination from '@/components/QePagination.vue'
import QeSingleSelect from '@/components/QeSingleSelect.vue'


const router = useRouter()
const toast = useToast()

const isLoading = ref(true)
const viewMode = ref('my')
const fileInput = ref(null)
const statusOptions = [
  { value: '', label: 'Все статусы' },
  { value: 'draft', label: 'Черновик' },
  { value: 'sent', label: 'Отправлена' },
  { value: 'approved', label: 'Согласована' },
  { value: 'paid', label: 'Оплачена' },
  { value: 'cancelled', label: 'Отменена' }
]
const clientOptions = computed(() => [
  { value: '', label: 'Все клиенты' },
  ...clients.value.map(c => ({
    value: c.id,
    label: c.company ? `${c.name} (${c.company})` : c.name
  }))
])
const filters = ref({
  name: '',
  client: '',
  status: '',
  date_from: '',
  date_to: ''
})

const estimatesStore = useEstimatesStore()
const clientsStore = useClientsStore()

const clients = computed(() => clientsStore.clients)

const perPage = 8
const currentPage = ref(1)
const currentFilters = ref({})
const totalEstimates = computed(() => estimatesStore.total)

const filteredEstimates = computed(() => {
  if (viewMode.value === 'fav') {
    return estimatesStore.estimates.filter(e => e.is_favorite)
  }
  return estimatesStore.estimates
})

onMounted(async () => {
  isLoading.value = true
  await clientsStore.fetchClients()
  await estimatesStore.fetchEstimates({ page: currentPage.value, limit: perPage })
  currentFilters.value = {}
  isLoading.value = false
})

const format = (date) => {
  if (!date) return ''
  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const year = date.getFullYear()
  return `${day}.${month}.${year}`
}

function formatDateToYYYYMMDD(date) {
  if (!date) return ''
  const d = new Date(date)
  const month = `${d.getMonth() + 1}`.padStart(2, '0')
  const day = `${d.getDate()}`.padStart(2, '0')
  return `${d.getFullYear()}-${month}-${day}`
}

async function applyFilters() {
  isLoading.value = true
  const params = new URLSearchParams()
  if (filters.value.name) params.append('name', filters.value.name)
  if (filters.value.client) params.append('client', filters.value.client)
  if (filters.value.date_from) params.append('date_from', formatDateToYYYYMMDD(filters.value.date_from) + 'T00:00:00Z')
  if (filters.value.date_to) params.append('date_to', formatDateToYYYYMMDD(filters.value.date_to) + 'T23:59:59Z')
  if (filters.value.status) params.append('status', filters.value.status)
  currentFilters.value = {
    name: filters.value.name,
    client: filters.value.client,
    date_from: filters.value.date_from ? formatDateToYYYYMMDD(filters.value.date_from) + 'T00:00:00Z' : '',
    date_to: filters.value.date_to ? formatDateToYYYYMMDD(filters.value.date_to) + 'T23:59:59Z' : '',
    status: [...filters.value.status]
  }
  currentPage.value = 1
  params.append('page', currentPage.value)
  params.append('limit', perPage)
  await estimatesStore.fetchEstimates(params)
  isLoading.value = false
}

async function resetFilters() {
  isLoading.value = true
  filters.value = {
    name: '',
    client: '',
    status: '',
    date_from: '',
    date_to: ''
  }
  currentFilters.value = {}
  currentPage.value = 1
  await estimatesStore.fetchEstimates({ page: currentPage.value, limit: perPage })
  isLoading.value = false
}

function triggerFileInput() {
  fileInput.value.click()
}

async function handleFile(event) {
  const file = event.target.files[0]
  if (!file) return

  try {
    const text = await file.text()
    const json = JSON.parse(text)
    if ('id' in json) delete json.id
    json.items?.forEach(item => delete item.id)

    if (!isValidEstimate(json)) {
      return
    }

    estimatesStore.setImportedEstimate(json)
    router.push({ path: '/estimates/create', state: { importedData: json } })

  } catch (e) {
    console.error(e)
    toast.error('Ошибка при чтении или разборе файла')
  }
}

function isValidEstimate(estimate) {
  if (typeof estimate !== 'object' || estimate === null) return false
  if (typeof estimate.name !== 'string' || !estimate.name.trim()) return false
  if (!Array.isArray(estimate.items)) return false

  for (const [i, item] of estimate.items.entries()) {
    if (!item || typeof item !== 'object') return false
    const { name, quantity, unit, internal_price, external_price } = item
    if (!name || typeof name !== 'string' || !name.trim()) {
      toast.error(`Ошибка в услуге №${i + 1}: отсутствует название`)
      return false
    }
    if (!['шт', 'час', 'день', 'м²', 'м'].includes(unit)) {
      toast.error(`Ошибка в услуге ${item.name}: недопустимая единица измерения`)
      return false
    }

    if (typeof quantity !== 'number' || quantity <= 0) {
      toast.error(`Ошибка в услуге ${item.name}: количество должно быть > 0`)
      return false
    }

    if (typeof internal_price !== 'number' || internal_price <= 0) {
      toast.error(`Ошибка в услуге ${item.name}: внутренняя цена должна быть > 0`)
      return false
    }

    if (typeof external_price !== 'number' || external_price <= 0) {
      toast.error(`Ошибка в услуге ${item.name}: внешняя цена должна быть > 0`)
      return false
    }
  }
  return true
}

async function fetchEstimatesPage() {
  isLoading.value = true
  const params = new URLSearchParams()
  params.append('page', currentPage.value)
  params.append('limit', perPage)
  if (viewMode.value === 'fav') params.append('favorite', 'true')
  if (currentFilters.value.name) params.append('name', currentFilters.value.name)
  if (currentFilters.value.client) params.append('client', currentFilters.value.client)
  if (currentFilters.value.date_from) params.append('date_from', currentFilters.value.date_from)
  if (currentFilters.value.date_to) params.append('date_to', currentFilters.value.date_to)
  currentFilters.value.status?.forEach(s => params.append('status', s))
  await estimatesStore.fetchEstimates(params)
  isLoading.value = false
}

function setViewMode(mode) {
  viewMode.value = mode
  currentPage.value = 1
  fetchEstimatesPage()
}

async function toggleFavorite(estimate) {
  try {
    if (estimate.is_favorite) {
      await estimatesStore.removeFavorite(estimate.id)
      estimate.is_favorite = false
      toast.success('Удалено из избранного')
    } else {
      await estimatesStore.addFavorite(estimate.id)
      estimate.is_favorite = true
      toast.success('Добавлено в избранное')
    }

  } catch (e) {
    toast.error('Ошибка при изменении избранного')
  }
}

function changePage(p) {
  currentPage.value = p
  fetchEstimatesPage()
}
</script>
