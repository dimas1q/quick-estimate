<template>
    <div class="py-10 max-w-5xl mx-auto space-y-8">
        <h1 class="text-2xl font-bold">Аналитика</h1>

        <!-- Фильтры (аккордеон) -->
        <section class="border border-gray-200 dark:border-gray-800 bg-white dark:bg-qe-black3 rounded-xl shadow p-6">
            <button type="button"
                class="flex justify-between items-center w-full text-xl font-semibold focus:outline-none"
                @click="filtersOpen = !filtersOpen">
                <span>Параметры фильтрации</span>
                <span class="text-lg select-none">{{ filtersOpen ? '−' : '+' }}</span>
            </button>
            <div v-show="filtersOpen" class="space-y-6 pt-4">
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    <!-- Клиент -->
                    <div>
                        <label class="text-sm text-gray-600 dark:text-gray-300 mb-1 block">Клиент</label>
                        <QeSingleSelect v-model="filters.clientId" :options="clientOptions" placeholder="Все клиенты"
                            class="w-full" />
                    </div>
                    <!-- Даты -->
                    <div>
                        <label class="text-sm text-gray-600 dark:text-gray-300 mb-1 block">Дата от</label>
                        <QeDatePicker v-model="filters.start_date" placeholder="Выберите дату от" :format="format"
                            class="mt-1" />
                    </div>
                    <div>
                        <label class="text-sm text-gray-600 dark:text-gray-300 mb-1 block">Дата до</label>
                        <QeDatePicker v-model="filters.end_date" placeholder="Выберите дату по" :format="format"
                            class="mt-1" />
                    </div>
                    <!-- Категории -->
                    <div>
                        <label class="text-sm text-gray-600 dark:text-gray-300 mb-1 block">Категории (через
                            запятую)</label>
                        <input :value="filters.categories_arr.join(', ')"
                            @input="filters.categories_arr = $event.target.value.split(',').map(s => s.trim()).filter(Boolean)"
                            type="text" class="qe-input w-full" placeholder="Оборудование, Свет" />
                    </div>
                    <!-- НДС -->
                    <div>
                        <label class="text-sm text-gray-600 dark:text-gray-300 mb-1 block">НДС включён</label>
                        <QeSingleSelect v-model="filters.vat_enabled" :options="vatOptions" placeholder="Все"
                            class="w-full" />
                    </div>
                    <!-- Гранулярность -->
                    <div>
                        <label class="text-sm text-gray-600 dark:text-gray-300 mb-1 block">Гранулярность</label>
                        <QeSingleSelect v-model="filters.granularity" :options="granularityOptions"
                            placeholder="Гранулярность" class="w-full" />
                    </div>
                    <!-- Статусы -->
                    <div class="sm:col-span-2 lg:col-span-3">
                        <label class="text-sm text-gray-600 dark:text-gray-300 mb-1 block">Статусы</label>
                        <QeMultiSelect v-model="filters.status" :options="statusOptions" placeholder="Все статусы"
                            class="w-full" />
                    </div>
                </div>
                <div class="flex gap-2 pt-2">
                    <button @click="applyFilters" class="qe-btn">Применить</button>
                    <button @click="resetFilters" class="qe-btn-secondary">Сбросить</button>
                </div>
            </div>
        </section>

        <!-- Сообщение об ошибке -->
        <div v-if="errorMessage" class="text-center text-red-600">{{ errorMessage }}</div>

        <!-- Метрики: карточки -->
        <section v-if="data" class="space-y-8">
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <MetricCard title="Всего смет" :value="data.total_estimates" :icon="FileText" />
                <MetricCard title="Выручка" :value="data.total_amount" :icon="DollarSign" suffix=" ₽" />
                <MetricCard title="Средняя сумма" :value="data.average_amount" :icon="Sliders" suffix=" ₽" />
                <MetricCard title="Медиана" :value="data.median_amount" :icon="BarChart2" suffix=" ₽" />
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <MetricCard title="Рост мес. к мес." :value="data.mom_growth" suffix=" %" :icon="TrendingUp"
                    :isPercent="true" />
                <MetricCard title="Рост год к году" :value="data.yoy_growth" suffix=" %" :icon="Calendar"
                    :isPercent="true" />
                <MetricCard v-if="!appliedFilters.clientId" title="ARPU" :value="data.arpu" :icon="Users" suffix=" ₽" />
                <MetricCard v-else title="ARPU" :value="'—'" :icon="Users" suffix="" />
            </div>
            <!-- График area -->
            <div class="bg-white dark:bg-qe-black3 border border-gray-200 dark:border-gray-800 p-6 rounded-xl shadow">
                <apexchart type="area" height="350" :options="chartOptionsWithTitles" :series="series" />
            </div>
            <!-- По ответственным -->
            <div>
                <h3 class="text-lg font-semibold mb-2">Статистика по ответственным</h3>
                <div
                    class="overflow-x-auto rounded-xl shadow border border-gray-200 dark:border-gray-800 bg-white dark:bg-qe-black3">
                    <table class="w-full text-sm">
                        <thead>
                            <tr class="bg-gray-50 dark:bg-qe-black2">
                                <th class="px-4 py-2 font-medium text-left text-gray-700 dark:text-gray-200">
                                    Ответственный</th>
                                <th class="px-4 py-2 font-medium text-left text-gray-700 dark:text-gray-200">Количество
                                    смет</th>
                                <th class="px-4 py-2 font-medium text-left text-gray-700 dark:text-gray-200">Выручка
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="r in data.by_responsible" :key="r.name"
                                class="hover:bg-gray-100 dark:hover:bg-gray-800 transition">
                                <td class="qe-table-td" :title="r.name">{{ r.name }}</td>
                                <td class="qe-table-td">{{ r.estimates_count }}</td>
                                <td class="qe-table-td">{{ formatCurrency(r.total_amount) }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            <!-- Топ клиентов -->
            <div v-if="!filters.clientId">
                <h3 class="text-lg font-semibold mb-2">Топ клиентов</h3>
                <div
                    class="overflow-x-auto rounded-xl shadow border border-gray-200 dark:border-gray-800 bg-white dark:bg-qe-black3">
                    <table class="w-full text-sm">
                        <thead class="bg-gray-50 dark:bg-qe-black2">
                            <tr>
                                <th class="px-4 py-2 font-medium text-left text-gray-700 dark:text-gray-200">Клиент</th>
                                <th class="px-4 py-2 font-medium text-left text-gray-700 dark:text-gray-200">Выручка
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="c in data.top_clients" :key="c.name"
                                class="hover:bg-gray-100 dark:hover:bg-gray-800 transition">
                                <td class="qe-table-td" :title="c.name">{{ c.name }}</td>
                                <td class="qe-table-td">{{ formatCurrency(c.total_amount) }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            <!-- Топ услуг -->
            <div>
                <h3 class="text-lg font-semibold mb-2">Топ услуг</h3>
                <div
                    class="overflow-x-auto rounded-xl shadow border border-gray-200 dark:border-gray-800 bg-white dark:bg-qe-black3">
                    <table class="w-full text-sm">
                        <thead class="bg-gray-50 dark:bg-qe-black2">
                            <tr>
                                <th class="px-4 py-2 font-medium text-left text-gray-700 dark:text-gray-200">Услуга</th>
                                <th class="px-4 py-2 font-medium text-left text-gray-700 dark:text-gray-200">Выручка
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="s in data.top_services" :key="s.name"
                                class="hover:bg-gray-100 dark:hover:bg-gray-800 transition ">
                                <td class="qe-table-td" :title="s.name">{{ s.name }}</td>
                                <td class="qe-table-td">{{ formatCurrency(s.total_amount) }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </section>
        <div v-if="!errorMessage && data" class="pb-10 flex justify-end">
            <div class="relative" ref="exportRef">
                <button @click="showExport = !showExport" class="qe-btn-success flex items-center">
                    <Download class="w-4 h-4 mr-1" />
                    <span>Экспорт</span>
                    <ChevronDown class="w-4 h-4 ml-1 transition-transform" :class="{ 'rotate-180': showExport }" />
                </button>
                <div v-if="showExport"
                    class="absolute right-0 mt-2 flex bg-white dark:bg-qe-black3 border border-gray-200 dark:border-gray-800 rounded-xl shadow z-50">
                    <button @click="downloadCsv"
                        class="px-4 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-800 rounded-l-xl">CSV</button>
                    <button @click="downloadExcel"
                        class="px-4 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-800">Excel</button>
                    <button @click="downloadPdf"
                        class="px-4 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-800 rounded-r-xl">PDF</button>
                </div>
            </div>
        </div>
    </div>
</template>


<script setup>
import { computed, ref, reactive, onMounted } from 'vue'
import { onClickOutside } from '@vueuse/core'
import { useClientsStore } from '@/store/clients'
import { useAnalyticsStore } from '@/store/analytics'

import QeSingleSelect from '@/components/QeSingleSelect.vue'
import QeDatePicker from '@/components/QeDatePicker.vue'
import MetricCard from '@/components/MetricCard.vue'
import QeMultiSelect from '@/components/QeMultiSelect.vue'
import fileDownload from 'js-file-download'

import {
    FileText,
    DollarSign,
    Sliders,
    BarChart2,
    Users,
    TrendingUp,
    Calendar,
    Download,
    ChevronDown
} from 'lucide-vue-next'


const clientsStore = useClientsStore()
const analyticsStore = useAnalyticsStore()

const clients = ref([]) 

const clientOptions = computed(() => [
    { value: null, label: 'Все клиенты' },
    ...clients.value.map(c => ({
        value: c.id,
        label: c.company ? `${c.name} (${c.company})` : c.name
    }))
])

const vatOptions = [
    { value: null, label: 'Все' },
    { value: true, label: 'Да' },
    { value: false, label: 'Нет' },
]

const statusOptions = [
    { value: 'draft', label: 'Черновик' },
    { value: 'sent', label: 'Отправлена' },
    { value: 'approved', label: 'Согласована' },
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

const filters = reactive({
    clientId: null,
    status: [],
    vat_enabled: null,
    categories_arr: [],
    start_date: '',
    end_date: '',
    granularity: 'month',
})

const appliedFilters = reactive({
    clientId: null,
    status: [],
    vat_enabled: null,
    categories_arr: [],
    start_date: '',
    end_date: '',
    granularity: 'month',
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

const data = ref(null)
const errorMessage = ref('')
const filtersOpen = ref(true)
const showExport = ref(false)
const exportRef = ref(null)
onClickOutside(exportRef, () => {
    showExport.value = false
})

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
    await applyFilters()
})

async function applyFilters() {
    errorMessage.value = ''
    const params = new URLSearchParams()
    params.append('granularity', filters.granularity)
    if (filters.start_date) params.append('start_date', formatDateToYYYYMMDD(filters.start_date) + 'T00:00:00Z')
    if (filters.end_date) params.append('end_date', formatDateToYYYYMMDD(filters.end_date) + 'T23:59:59Z')
    filters.status.forEach(s => params.append('status', s))
    if (filters.vat_enabled !== null) params.append('vat_enabled', String(filters.vat_enabled))
    filters.categories_arr.forEach(c => params.append('categories', c))
    Object.assign(appliedFilters, JSON.parse(JSON.stringify(filters)))
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

function buildParams(obj) {
    const p = new URLSearchParams()
    p.append('granularity', obj.granularity)
    if (obj.start_date) p.append('start_date', obj.start_date)
    if (obj.end_date) p.append('end_date', obj.end_date)
    obj.status.forEach(s => p.append('status', s))
    if (obj.vat_enabled !== null) p.append('vat_enabled', String(obj.vat_enabled))
    obj.categories_arr.forEach(c => p.append('categories', c))
    return p
}

async function downloadCsv() {
    const params = buildParams(appliedFilters)
    params.append('format', 'csv')
    const blob = await analyticsStore.downloadGlobalCsv(params)
    fileDownload(blob, 'analytics.csv')
}

async function downloadExcel() {
    const params = buildParams(appliedFilters)
    params.append('format', 'excel')
    const blob = await analyticsStore.downloadGlobalExcel(params)
    fileDownload(blob, 'analytics.xlsx')
}

async function downloadPdf() {
    const params = buildParams(appliedFilters)
    params.append('format', 'pdf')
    const blob = await analyticsStore.downloadGlobalPdf(params)
    fileDownload(blob, 'analytics.pdf')
}

function formatCurrency(val) {
    return new Intl.NumberFormat('ru-RU', {
        style: 'currency', currency: 'RUB', minimumFractionDigits: 0
    }).format(val)
}
</script>
