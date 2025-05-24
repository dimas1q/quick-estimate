<template>
    <div class="py-8 max-w-6xl mx-auto space-y-8">
        <h1 class="text-2xl font-bold">Аналитика</h1>

        <!-- Фильтры (аккордеон) -->
        <section class="bg-gray p-6 rounded-lg shadow space-y-4">
            <h2 class="text-xl font-semibold cursor-pointer flex justify-between items-center"
                @click="filtersOpen = !filtersOpen">
                Параметры фильтрации
                <span class="text-lg">{{ filtersOpen ? '−' : '+' }}</span>
            </h2>
            <div v-show="filtersOpen" class="space-y-6">
                <div class="grid grid-cols-3 gap-4">
                    <!-- Клиент -->
                    <div>
                        <label class="block text-sm font-medium mb-1">Клиент</label>
                        <select v-model="filters.clientId" class="w-full border rounded-lg p-2">
                            <option :value="null">Все клиенты</option>
                            <option v-for="c in clients" :key="c.id" :value="c.id">{{ c.name }}</option>
                        </select>
                    </div>
                    <!-- Даты -->
                    <div><label class="block text-sm font-medium mb-1">Дата от</label>
                        <input v-model="filters.start_date" type="date" class="w-full border rounded-lg p-2" />
                    </div>
                    <div><label class="block text-sm font-medium mb-1">Дата до</label>
                        <input v-model="filters.end_date" type="date" class="w-full border rounded-lg p-2" />
                    </div>
                    <!-- Категории -->
                    <div class="col-span-1">
                        <label class="block text-sm font-medium mb-1">Категории (через запятую)</label>
                        <input v-model="filters.categories" type="text" class="w-full border rounded-lg p-2"
                            placeholder="Оборудование, Свет" />
                    </div>
                    <!-- НДС -->
                    <div>
                        <label class="block text-sm font-medium mb-1">НДС включён</label>
                        <select v-model="filters.vat_enabled" class="w-full border rounded-lg p-2">
                            <option :value="null">Все</option>
                            <option :value="true">Да</option>
                            <option :value="false">Нет</option>
                        </select>
                    </div>
                    <!-- Гранулярность -->
                    <div>
                        <label class="block text-sm font-medium mb-1">Гранулярность</label>
                        <select v-model="filters.granularity" class="w-full border rounded-lg p-2">
                            <option v-for="g in granularityOptions" :key="g.value" :value="g.value">{{ g.label }}
                            </option>
                        </select>
                    </div>
                    <!-- Статусы -->

                    <!-- Статусы -->
                    <div>
                        <span class="block text-sm font-medium mb-2">Статусы</span>
                        <div class="flex flex-col gap-1 text-sm ">
                            <label v-for="opt in statusOptions" :key="opt.value"
                                class="inline-flex items-center space-x-1">
                                <input type="checkbox" :value="opt.value" v-model="filters.status" />
                                <span>{{ opt.label }}</span>
                            </label>
                        </div>
                    </div>
                </div>
                <div class="flex space-x-2">
                    <button @click="applyFilters" class="btn-primary flex items-center space-x-2">
                        <span>Применить</span>
                    </button>
                    <button @click="resetFilters" class="btn-danger flex items-center space-x-2">
                        <span>Сбросить</span>
                    </button>
                </div>
            </div>
        </section>

        <!-- Сообщение об ошибке -->
        <div v-if="errorMessage" class="text-center text-red-600">{{ errorMessage }}</div>

        <!-- Метрики: две группы карточек -->
        <section v-if="data" class="space-y-8">
            <!-- группа 1 -->
            <div class="grid grid-cols-2 gap-4">
                <MetricCard title="Всего смет" :value="data.total_estimates" :icon="FileText" />
                <MetricCard title="Выручка" :value="data.total_amount" :icon="DollarSign" suffix=" ₽" />
                <MetricCard title="Средняя сумма" :value="data.average_amount" :icon="Sliders" suffix=" ₽" />
                <MetricCard title="Медиана" :value="data.median_amount" :icon="BarChart2" suffix=" ₽" />
            </div>
            <!-- группа 2 -->
            <div class="grid grid-cols-3 gap-4">
                <MetricCard v-if="!filters.clientId" title="ARPU" :value="data.arpu" :icon="Users" suffix=" ₽" />
                <MetricCard title="Рост мес. к мес." :value="data.mom_growth" suffix=" %" :icon="TrendingUp"
                    :isPercent="true" />
                <MetricCard title="Рост год к году" :value="data.yoy_growth" suffix=" %" :icon="Calendar"
                    :isPercent="true" />
            </div>

            <!-- График area -->
            <div class="bg-gray p-6 rounded-lg shadow">
                <apexchart type="area" height="350" :options="chartOptionsWithTitles" :series="series" />
            </div>

            <!-- По ответственным -->
            <div>
                <h3 class="text-lg font-semibold mb-2">По ответственным</h3>
                <div class="overflow-x-auto rounded-lg shadow-sm">
                    <table class="w-full text-sm ">
                        <thead class="bg-gray-100 border-b text-left">
                            <tr>
                                <th class="px-4 py-2 font-medium  whitespace-nowrap">Ответственный</th>
                                <th class="px-4 py-2 font-medium  whitespace-nowrap">Количество смет</th>
                                <th class="px-4 py-2 font-medium  whitespace-nowrap">Выручка</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="r in data.by_responsible" :key="r.name" class="hover:bg-gray-50 border-b">
                                <td class="px-4 py-2  whitespace-nowrap" :title="r.name">
                                    {{ r.name }}
                                </td>
                                <td class="px-4 py-2  whitespace-nowrap">
                                    {{ r.estimates_count }}
                                </td>
                                <td class="px-4 py-2  whitespace-nowrap">
                                    {{ formatCurrency(r.total_amount) }}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Топ клиентов -->
            <div v-if="!filters.clientId">
                <h3 class="text-lg font-semibold mb-2">Топ клиентов</h3>
                <div class="overflow-x-auto rounded-lg shadow-sm">
                    <table class="w-full text-sm ">
                        <thead class="bg-gray-100 border-b text-left">
                            <tr>
                                <th class="px-4 py-2 font-medium  whitespace-nowrap">Клиент</th>
                                <th class="px-4 py-2 font-medium  whitespace-nowrap">Выручка</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="c in data.top_clients" :key="c.name" class="hover:bg-gray-50 border-b">
                                <td class="px-4 py-2  whitespace-nowrap" :title="c.name">
                                    {{ c.name }}
                                </td>
                                <td class="px-4 py-2  whitespace-nowrap">
                                    {{ formatCurrency(c.total_amount) }}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Топ услуг -->
            <div>
                <h3 class="text-lg font-semibold mb-2">Топ услуг</h3>
                <div class="overflow-x-auto rounded-lg shadow-sm">
                    <table class="w-full text-sm">
                        <thead class="bg-gray-100 border-b text-left">
                            <tr>
                                <th class="px-4 py-2 font-medium  whitespace-nowrap">Услуга</th>
                                <th class="px-4 py-2 font-medium  whitespace-nowrap">Выручка</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="s in data.top_services" :key="s.name" class="hover:bg-gray-50 border-b">
                                <td class="px-4 py-2  whitespace-nowrap" :title="s.name">
                                    {{ s.name }}
                                </td>
                                <td class="px-4 py-2  whitespace-nowrap">
                                    {{ formatCurrency(s.total_amount) }}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

        </section>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useClientsStore } from '@/store/clients'
import { useAnalyticsStore } from '@/store/analytics'
import MetricCard from '@/components/MetricCard.vue'
import Multiselect from 'vue-multiselect'

import {
    FileText,
    DollarSign,
    Sliders,
    BarChart2,
    Users,
    TrendingUp,
    Calendar
} from 'lucide-vue-next'

/* стили для multiselect */
import 'vue-multiselect/dist/vue-multiselect.min.css'

const clientsStore = useClientsStore()
const analyticsStore = useAnalyticsStore()

/* стейт */
const clients = ref([])
const statusOptions = [
    { value: 'draft', label: 'Черновик' },
    { value: 'sent', label: 'Отправлена' },
    { value: 'approved', label: 'Одобрена' },
    { value: 'paid', label: 'Оплачена' },
    { value: 'cancelled', label: 'Отменена' },
]
const granularityOptions = [
    { value: 'day', label: 'День' },
    { value: 'week', label: 'Неделя' },
    { value: 'month', label: 'Месяц' },
    { value: 'quarter', label: 'Квартал' },
    { value: 'year', label: 'Год' },
]
const categoriesOptions = ref([]) // можно загружать из API шаблонов/услуг

const filters = reactive({
    clientId: null,
    status: [],
    vat_enabled: null,
    categories_arr: [],  // теперь массив для multiselect
    start_date: '',
    end_date: '',
    granularity: 'month',
})
const data = ref(null)
const errorMessage = ref('')
const filtersOpen = ref(true)

/* ApexCharts */
const chartOptionsWithTitles = ref({
    chart: { id: 'analytics-chart', toolbar: { show: false } },
    xaxis: {
        title: { text: 'Период', style: { color: '#333' } },
        categories: [],
    },
    yaxis: {
        title: { text: 'Выручка, ₽', style: { color: '#333' } },
        labels: { formatter: v => v.toLocaleString() },
    },
    stroke: { curve: 'smooth' },
    tooltip: { y: { formatter: v => v.toLocaleString() } },
})
const series = ref([{ name: 'Выручка', data: [] }])

onMounted(async () => {
    await clientsStore.fetchClients()
    clients.value = clientsStore.clients
    // TODO: загрузить categoriesOptions из API при необходимости
    await applyFilters()
})

async function applyFilters() {
    errorMessage.value = ''
    const params = new URLSearchParams()
    params.append('granularity', filters.granularity)
    if (filters.start_date) params.append('start_date', filters.start_date)
    if (filters.end_date) params.append('end_date', filters.end_date)
    filters.status.forEach(s => params.append('status', s.value))
    if (filters.vat_enabled !== null) params.append('vat_enabled', String(filters.vat_enabled))
    filters.categories_arr.forEach(c => params.append('categories', c))
    try {
        if (filters.clientId) {
            data.value = await analyticsStore.fetchClient(filters.clientId, params)
        } else {
            data.value = await analyticsStore.fetchGlobal(params)
        }
        // обновляем график
        chartOptionsWithTitles.value.xaxis.categories = data.value.timeseries.map(p => p.period)
        series.value[0].data = data.value.timeseries.map(p => p.value)
    } catch (err) {
        if (err.response?.status === 404) {
            data.value = null
            errorMessage.value = 'Данных по выбранным фильтрам не найдено'
        } else {
            console.error(err)
            errorMessage.value = 'Ошибка при загрузке данных'
        }
    }
}

function resetFilters() {
    filters.clientId = null
    filters.status = []
    filters.vat_enabled = null
    filters.categories_arr = []
    filters.start_date = ''
    filters.end_date = ''
    filters.granularity = 'month'
    applyFilters()
}

function formatCurrency(val) {
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency', currency: 'RUB', minimumFractionDigits: 0
    }).format(val)
}
</script>

<style scoped>
/* override для multiselect */
.multiselect {
    width: 100%;
}
</style>
