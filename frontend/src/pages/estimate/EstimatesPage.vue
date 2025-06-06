<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import { useEstimatesStore } from '@/store/estimates'
import { useClientsStore } from '@/store/clients'
import { Star } from 'lucide-vue-next'

import QeDatePicker from '@/components/QeDatePicker.vue'

function formatDateToYYYYMMDD(date) {
  if (!date) return ''
  const d = new Date(date)
  const month = `${d.getMonth() + 1}`.padStart(2, '0')
  const day = `${d.getDate()}`.padStart(2, '0')
  return `${d.getFullYear()}-${month}-${day}`
}

const router = useRouter()
const toast = useToast()

const isLoading = ref(true)
const viewMode = ref('my')
const fileInput = ref(null)
const filters = ref({
  name: '',
  client: '',
  date_from: '',
  date_to: ''
})

const estimatesStore = useEstimatesStore()
const clientsStore = useClientsStore()

const clients = computed(() => clientsStore.clients)

const filteredEstimates = computed(() => {
  if (viewMode.value === 'fav') {
    return estimatesStore.estimates.filter(e => e.is_favorite)
  }
  return estimatesStore.estimates
})

onMounted(async () => {
  isLoading.value = true
  await clientsStore.fetchClients()
  await estimatesStore.fetchEstimates()
  isLoading.value = false
})

const format = (date) => {
  if (!date) return ''
  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const year = date.getFullYear()
  return `${day}.${month}.${year}`
}


async function applyFilters() {
  isLoading.value = true
  const query = {
    name: filters.value.name,
    client: filters.value.client ? Number(filters.value.client) : undefined,
    date_from: filters.value.date_from ? formatDateToYYYYMMDD(filters.value.date_from) + 'T00:00:00Z' : undefined,
    date_to: filters.value.date_to ? formatDateToYYYYMMDD(filters.value.date_to) + 'T23:59:59Z' : undefined
  }
  await estimatesStore.fetchEstimates(query)
  isLoading.value = false
}

async function resetFilters() {
  isLoading.value = true
  filters.value = {
    name: '',
    client: '',
    date_from: '',
    date_to: ''
  }
  await estimatesStore.fetchEstimates()
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
    const { name, quantity, unit, unit_price } = item
    if (!name || typeof name !== 'string' || !name.trim()) {
      toast.error(`Ошибка в услуге №${i + 1}: отсутствует название`)
      return false
    }
    if (!['шт', 'час', 'день', 'м²', 'м'].includes(unit)) {
      toast.error(`Ошибка в услуге №${i + 1}: недопустимая единица измерения`)
      return false
    }
    if (typeof quantity !== 'number' || quantity <= 0) {
      toast.error(`Ошибка в услуге №${i + 1}: количество должно быть > 0`)
      return false
    }
    if (typeof unit_price !== 'number' || unit_price <= 0) {
      toast.error(`Ошибка в услуге №${i + 1}: цена должна быть > 0`)
      return false
    }
  }
  return true
}

function setViewMode(mode) {
  viewMode.value = mode
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
</script>

<template>
  <div class="space-y-6 px-6 py-8 max-w-5xl mx-auto">
    <!-- Навигационный переключатель -->
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-1 bg-gray-100 dark:bg-qe-black2 rounded-xl p-1">
        <button
          :class="['px-5 py-2 rounded-lg text-sm font-semibold transition', viewMode === 'my' ? 'bg-white dark:bg-gray-900 text-blue-600 shadow' : 'text-gray-500 hover:text-blue-600']"
          @click="setViewMode('my')">Мои сметы</button>
        <button
          :class="['px-5 py-2 rounded-lg text-sm font-semibold transition', viewMode === 'fav' ? 'bg-white dark:bg-gray-900 text-blue-600 shadow' : 'text-gray-500 hover:text-blue-600']"
          @click="setViewMode('fav')">Избранное</button>
      </div>
    </div>

    <input type="file" ref="fileInput" accept="application/json" @change="handleFile" class="hidden" />

    <div class="flex gap-6 items-start">
      <div class="flex-1 space-y-4">
        <!-- Скелетон-карточки -->
        <div v-if="isLoading" class="flex flex-col gap-5">
          <div v-for="n in 3" :key="n"
            class="border rounded-xl shadow-sm p-5 bg-white dark:bg-gray-900 animate-pulse flex flex-col gap-3 relative">
            <div class="h-6 bg-gray-200 dark:bg-gray-800 rounded w-2/3 mb-2"></div>
            <div class="h-4 bg-gray-100 dark:bg-gray-700 rounded w-1/4 mb-2"></div>
            <div class="h-4 bg-gray-100 dark:bg-gray-700 rounded w-1/2 mb-2"></div>
            <div class="h-3 bg-gray-100 dark:bg-gray-700 rounded w-1/4"></div>
          </div>
        </div>

        <!-- Список смет -->
        <template v-else>

          <div v-for="e in filteredEstimates" :key="e.id"
            class="border border-gray-200 dark:border-qe-black2 rounded-xl shadow-sm p-5 bg-white dark:bg-qe-black3 transition hover:shadow-md flex flex-col gap-1 relative ">
            <!-- Звезда -->
            <button
              class="absolute top-2 right-2 rounded-full bg-transparent p-1 transition flex items-center justify-center"
              style="width: 44px; height: 44px; overflow: visible;"
              :aria-label="e.is_favorite ? 'Убрать из избранного' : 'Добавить в избранное'" @click="toggleFavorite(e)">
              <Star v-if="e.is_favorite" class="w-6 h-6 text-yellow-400 fill-yellow-400" :stroke-width="1.5" />
              <Star v-else class="w-6 h-6 text-gray-300 hover:text-yellow-400 transition" :stroke-width="1.5" />
            </button>
            <div class="font-semibold text-lg">{{ e.name }}</div>
            <div class="text-sm">
              Клиент: {{ e.client?.name || '—' }}
              <span v-if="e.client?.company">({{ e.client.company }})</span>
            </div>
            <div class="text-sm">Ответственный: {{ e.responsible || '—' }}</div>
            <div class="text-xs text-gray-500">Создана: {{ new Date(e.date).toLocaleString() }}</div>
            <router-link :to="`/estimates/${e.id}`" class="text-blue-600 text-sm hover:underline mt-2 inline-block">
              Подробнее →
            </router-link>
          </div>
          <div v-if="filteredEstimates.length === 0"
            class="text-center text-gray-500 border border-gray-200 dark:border-gray-800 p-4 rounded py-8">
            <p>Сметы отсутствуют.</p>
          </div>
        </template>
      </div>

      <!-- Боковая панель с фильтрами и импортом -->
      <div class="w-72 space-y-4">
        <router-link to="/estimates/create" class="qe-btn block w-full text-center">
          Создать смету
        </router-link>
        <button @click="triggerFileInput" class="qe-btn block w-full text-center">Импорт сметы</button>
        <div
          class="border border-gray-200 dark:border-qe-black2 rounded-xl p-4 shadow-sm space-y-4 text-center bg-white dark:bg-qe-black3">
          <h2 class="font-semibold text-lg">Фильтры</h2>
          <div>
            <label class="text-sm text-gray-600 dark:text-gray-300">Название</label>
            <input v-model="filters.name" class="qe-input w-full mt-2" type="text" placeholder="Название сметы" />
          </div>
          <div>
            <label class="text-sm text-gray-600 dark:text-gray-300">Клиент</label>
            <select v-model="filters.client" class="qe-input w-full mt-2">
              <option :value="''">Все клиенты</option>
              <option v-for="c in clients" :key="c.id" :value="c.id">
                {{ c.name }}<span v-if="c.company"> ({{ c.company }})</span>
              </option>
            </select>
          </div>

          <div>
            <label class="text-sm text-gray-600 dark:text-gray-300">Дата с</label>
            <QeDatePicker v-model="filters.date_from" label="Дата с" placeholder="Выберите дату с" :format="format"
              class="mt-2" />
          </div>
          <div>
            <label class="text-sm text-gray-600 dark:text-gray-300">Дата по</label>
            <QeDatePicker v-model="filters.date_to" label="Дата по" placeholder="Выберите дату по" :format="format"
              class="mt-2" />
          </div>

          <div class="flex gap-2 pt-2">
            <button @click="applyFilters" class="qe-btn w-full">Применить</button>
            <button @click="resetFilters" class="qe-btn-secondary w-full ">Сбросить</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>


<style scoped>
.dp__theme_dark {
  --dp-background-color: #1a1d1f;
}

.dp__input {
  width: 100% !important;
  padding: 0.5rem 1rem !important;
  border-radius: 0.5rem !important;
  /* rounded-lg */
  border: 1px solid #d1d5db !important;
  /* gray-300 */
  font-size: 1rem !important;
  background: #fff !important;
  color: #18181b !important;
  box-sizing: border-box;
  transition: border-color 0.2s;
}

.dark .dp__input {
  background: #1a1d1f !important;
  /* твой qe-black */
  color: #f3f4f6 !important;
  /* text-gray-100 */
  border-color: #374151 !important;
  /* dark:border-gray-700 */
}
</style>