## frontend/src/pages/EstimateDetailsPage.vue
<template>
    <div class="py-8 max-w-6xl mx-auto">

        <div v-if="error" class="text-center text-red-500 text-lg font-medium mt-10">
            {{ error }}
        </div>
        <div v-if="estimate" class="space-y-6">
            <div class="flex justify-between items-center pb-2 mb-6">
                <div class="items-center">
                    <h1 class="text-3xl font-bold text-gray-800 dark:text-white">
                        Смета: {{ estimate.name }}
                        <span :class="[
                            'inline-block align-middle rounded-full px-2 py-0.5 text-xs font-semibold ml-1',
                            {
                                'bg-gray-200 text-gray-800': estimate.status === 'draft',
                                'bg-yellow-200 text-yellow-800': estimate.status === 'sent',
                                'bg-green-200 text-green-800': estimate.status === 'approved',
                                'bg-blue-200 text-blue-800': estimate.status === 'paid',
                                'bg-red-200 text-red-800': estimate.status === 'cancelled'
                            }
                        ]">
                            {{
                            {
                            draft: 'Черновик',
                            sent: 'Отправлена',
                            approved: 'Согласована',
                            paid: 'Оплачена',
                            cancelled: 'Отменена'
                            }[estimate.status]
                            }}
                        </span>

                    </h1>

                    <!-- здесь индикатор режима -->
                    <p v-if="isVersionView" class="mt-1 text-sm text-gray-500">
                        Просмотр версии №{{ currentVersion }}
                    </p>
                </div>

                <div class="flex space-x-3 items-center relative">
                    <!-- если мы в режиме версии, показываем другие кнопки -->
                    <template v-if="isVersionView">

                        <button @click="restoreVersion(currentVersion)"
                            class="inline-flex items-center px-4 py-2 rounded-md bg-yellow-500 text-white hover:bg-yellow-600 transition-all text-sm font-medium shadow">
                            Восстановить
                        </button>
                        <button @click="copyVersion(currentVersion)"
                            class="inline-flex items-center px-4 py-2 rounded-md bg-blue-500 text-white hover:bg-blue-600 transition-all text-sm font-medium shadow">
                            Копировать
                        </button>
                        <button @click="deleteVersion(currentVersion)"
                            class="inline-flex items-center px-4 py-2 rounded-md bg-red-500 text-white hover:bg-red-600 transition-all text-sm font-medium shadow">
                            Удалить версию
                        </button>
                        <button @click="() => router.push({ path: `/estimates/${estimate.id}` })"
                            class="btn-secondary inline-flex items-center px-4 py-2 rounded-md bg-gray-300 text-gray-800 hover:bg-gray-400 transition-all text-sm font-medium shadow">
                            Вернуться
                        </button>
                    </template>
                    <template v-else>

                        <!-- Выпадающее меню -->
                        <div class="relative" ref="menuRef">
                            <button @click="showExport = !showExport"
                                class="inline-flex items-center px-4 py-2 rounded-md bg-green-600 text-white hover:bg-green-700 transition-all text-sm font-medium shadow">
                                Экспортировать
                                <svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" stroke-width="2"
                                    viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                                </svg>
                            </button>
                            <div v-if="showExport"
                                class="absolute right-0 mt-2 w-38 bg-white rounded-xl shadow-xl ring-1 ring-black/5 backdrop-blur-sm border border-gray-100 animate-fade-in z-50">
                                <button @click="downloadJson(estimate.id)"
                                    class="block w-full text-left px-4 py-2 hover:bg-gray-50 transition-colors text-center text-sm text-gray-700">
                                    JSON
                                </button>
                                <button @click="downloadExcel(estimate)"
                                    class="block w-full text-left px-4 py-2 hover:bg-gray-50 transition-colors text-sm text-center text-gray-700 rounded-b-xl">
                                    Excel
                                </button>
                                <button @click="downloadPdf(estimate)"
                                    class="block w-full text-left px-4 py-2 hover:bg-gray-50 transition-colors text-sm text-center text-gray-700 rounded-t-xl">
                                    PDF
                                </button>
                            </div>

                        </div>

                        <!-- Основные кнопки -->
                        <RouterLink :to="`/estimates/${estimate.id}/edit`"
                            class="inline-flex items-center px-4 py-2 rounded-md bg-yellow-500 text-white hover:bg-yellow-600 transition-all text-sm font-medium shadow">
                            Редактировать
                        </RouterLink>
                        <button @click="copyEstimate"
                            class="inline-flex items-center px-4 py-2 rounded-md bg-blue-500 text-white hover:bg-blue-600 transition-all text-sm font-medium shadow">
                            Копировать
                        </button>
                        <button @click="confirmDelete"
                            class="inline-flex items-center px-4 py-2 rounded-md bg-red-500 text-white hover:bg-red-600 transition-all text-sm font-medium shadow">
                            Удалить
                        </button>
                    </template>
                </div>
            </div>

            <!-- СОВРЕМЕННЫЙ ТАБ-ПЕРЕКЛЮЧАТЕЛЬ -->
            <div class="flex items-center gap-1 bg-gray-100 dark:bg-qe-black2 rounded-xl p-1 mb-6 w-fit">
                <button
                    :class="['px-5 py-2 rounded-lg text-sm font-semibold transition', activeTab === 'details' ? 'bg-white dark:bg-gray-900 text-blue-600 shadow' : 'text-gray-500 hover:text-blue-600']"
                    @click="activeTab = 'details'">
                    Сведения
                </button>
                <button
                    :class="['px-5 py-2 rounded-lg text-sm font-semibold transition', activeTab === 'history' ? 'bg-white dark:bg-gray-900 text-blue-600 shadow' : 'text-gray-500 hover:text-blue-600']"
                    @click="activeTab = 'history'">
                    История
                </button>
            </div>


            <div v-if="activeTab === 'details'">
                <div class="grid gap-3 text-sm text-gray-800 dark:text-gray-200">
                    <div
                        class="grid grid-cols-2 gap-4 border dark:border-qe-black2 bg-white dark:bg-qe-black rounded-2xl p-6">
                        <p>
                            <strong>Клиент:</strong>
                            <RouterLink :to="`/clients/${estimate.client.id}`"
                                class="ml-1 transition-colors text-gray-900 hover:text-blue-700">
                                {{ estimate.client.name }}
                            </RouterLink>
                        </p>
                        <p v-if="estimate.event_datetime"><strong>Дата и время мероприятия:</strong> {{ new
                            Date(estimate.event_datetime).toLocaleString() }}</p>

                        <p><strong>Ответственный:</strong> {{ estimate.responsible || '—' }}</p>
                        <p v-if="estimate.event_place"><strong>Место проведения мероприятия:</strong> {{
                            estimate.event_place }}</p>
                        <p>
                            <strong>НДС:</strong>
                            <span v-if="estimate.vat_enabled">
                                Включён ({{ estimate.vat_rate }}%)
                            </span>
                            <span v-else> Не включён</span>
                        </p>

                        <p>
                            <strong>Дата создания: </strong> {{ new Date(estimate.date).toLocaleString() }}
                        </p>
                        <p><strong>Примечания:</strong> {{ estimate.notes || '—' }}</p>

                        <p>
                            <strong>Последнее обновление:</strong> {{ new Date(estimate.updated_at).toLocaleString() }}
                        </p>
                    </div>

                    <div class="border bg-white dark:bg-qe-black dark:border-qe-black2 rounded-2xl p-6 mt-6 ">
                        <div v-for="(groupItems, category) in groupedItems" :key="category" class="mb-4">
                            <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-4 text-center pb-1 ">{{
                                category }}
                            </h3>

                            <div class="space-y-4 ">
                                <div v-for="(row, rowIndex) in chunkArray(groupItems, 3)" :key="rowIndex"
                                    class="flex gap-4">
                                    <div v-for="item in row" :key="item.id"
                                        :class="`flex-1 ${row.length === 1 ? 'max-w-full' : row.length === 2 ? 'max-w-1/2' : 'max-w-1/3'}`"
                                        class="bg-white border border-gray-200 dark:bg-qe-black dark:border-qe-black2 rounded-xl shadow-sm p-4 hover:shadow-md transition-shadow duration-200">
                                        <div class="flex justify-between items-start mb-2">
                                            <div>
                                                <p class="text-base font-semibold text-gray-900 dark:text-white">{{
                                                    item.name }}</p>
                                                <p class="text-sm text-gray-600 dark:text-white">{{ item.description }}
                                                </p>
                                            </div>
                                            <div
                                                class="text-sm text-gray-500 dark:text-white text-right whitespace-nowrap">
                                                {{ item.quantity }} {{ item.unit }}
                                            </div>
                                        </div>
                                        <div class="flex justify-between text-sm text-gray-700 dark:text-white pt-2">
                                            <span>Внутр. цена за единицу:</span>
                                            <span>{{ formatCurrency(item.internal_price) }}</span>
                                        </div>
                                        <div class="flex justify-between text-sm text-gray-700 dark:text-white">
                                            <span>Внешн. цена за единицу:</span>
                                            <span>{{ formatCurrency(item.external_price) }}</span>
                                        </div>
                                        <div
                                            class="flex justify-between font-semibold text-sm dark:text-white text-gray-900">
                                            <span>Итог (внутр.):</span>
                                            <span>{{ formatCurrency(getItemInternal(item)) }}</span>
                                        </div>
                                        <div
                                            class="flex justify-between font-semibold text-sm  dark:text-white text-gray-900">
                                            <span>Итог (внешн.):</span>
                                            <span>{{ formatCurrency(getItemExternal(item)) }}</span>
                                        </div>

                                    </div>
                                </div>
                            </div>

                            <div class="text-right font-semibold text-base text-gray-900 dark:text-white mt-4">
                                <div>Итог по категории (внутр.): {{ formatCurrency(getGroupInternal(groupItems)) }}
                                </div>
                                <div>Итог по категории (внешн.): {{ formatCurrency(getGroupExternal(groupItems)) }}
                                </div>
                            </div>
                        </div>


                        <div v-if="estimate?.items?.length" class="pt-6">
                            <p class="text-right font-semibold text-lg pt-4 border-t dark:border-qe-black2">
                                Общая сумма (внутр.): {{ formatCurrency(totalInternal) }}
                            </p>
                            <p class="text-right font-semibold text-lg">
                                Общая сумма (внешняя): {{ formatCurrency(totalExternal) }}
                            </p>
                            <p class="text-right font-semibold text-lg">
                                Разница: {{ formatCurrency(totalDiff) }}
                            </p>
                            <p class="text-right text-gray-700 dark:text-white" v-if="estimate.vat_enabled">
                                НДС ({{ estimate.vat_rate }}%): {{ formatCurrency(vat) }}<br />
                                Итого с НДС: {{ formatCurrency(totalWithVat) }}
                            </p>
                        </div>

                    </div>
                </div>
            </div>

            <div v-else>
                <div v-if="logs.length" class="text-sm w-full mt-6">
                    <h3 class="font-semibold mb-4 ">
                        История изменений
                    </h3>
                    <div
                        class="overflow-x-auto rounded-xl shadow border border-gray-200 dark:border-gray-800 bg-white dark:bg-qe-black">
                        <table class="w-full text-sm">
                            <thead>
                                <tr class="bg-gray-50 dark:bg-qe-black">
                                    <th class="qe-table-th text-left">Дата и время</th>
                                    <th class="qe-table-th text-left">Действие</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="log in logs" :key="log.id"
                                    class="hover:bg-gray-100 dark:hover:bg-gray-800 transition">
                                    <td class="qe-table-td">{{ new Date(log.timestamp).toLocaleString() }}</td>
                                    <td class="qe-table-td">{{ log.description }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <div v-if="versions.length" class="mt-2 pt-6 text-sm">
                    <h3 class="font-semibold mb-4">История версий</h3>
                    <div
                        class="overflow-x-auto rounded-xl shadow border border-gray-200 dark:border-gray-800 bg-white dark:bg-qe-black">
                        <table class="w-full text-sm qe-table">
                            <thead>
                                <tr class="bg-gray-50 dark:bg-qe-black">
                                    <th class="qe-table-th text-left">Версия</th>
                                    <th class="qe-table-th text-left">Дата создания</th>
                                    <th class="qe-table-th text-right">Действия</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="v in versions" :key="v.version"
                                    class="hover:bg-gray-100 dark:hover:bg-gray-800 border-b last:border-b-0 transition">
                                    <td class="qe-table-td">№{{ v.version }}</td>
                                    <td class="qe-table-td">{{ new Date(v.created_at).toLocaleString() }}</td>
                                    <td class="qe-table-td text-right space-x-2">
                                        <button @click="viewVersion(v.version)"
                                            class="px-3 py-1 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600 transition">
                                            Просмотр
                                        </button>
                                        <button @click="deleteVersion(v.version)"
                                            class="px-3 py-1 text-sm bg-red-500 text-white rounded-md hover:bg-red-600 transition">
                                            Удалить
                                        </button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        <!-- Модалка -->
        <div v-if="showConfirm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white p-6 rounded-lg shadow max-w-sm w-full text-center">
                <p class="mb-4 font-semibold">Вы уверены, что хотите удалить данную смету?</p>
                <div class="flex justify-center gap-4">
                    <button @click="deleteEstimate" class="bg-red-500 text-white px-4 py-2 rounded-lg">Да,
                        удалить</button>
                    <button @click="showConfirm = false" class="bg-gray-300 px-4 py-2 rounded-lg">Отмена</button>
                </div>
            </div>
        </div>

    </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, computed, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useEstimatesStore } from '@/store/estimates'
import { onClickOutside } from '@vueuse/core'
import { useToast } from 'vue-toastification'

import fileDownload from 'js-file-download'

const route = useRoute()
const router = useRouter()
const store = useEstimatesStore()
const toast = useToast()

const versionParam = computed(() => route.query.version ? Number(route.query.version) : null)
const isVersionView = computed(() => versionParam.value !== null)
const currentVersion = ref(null)

const showExport = ref(false)
const menuRef = ref(null)
const showConfirm = ref(false)

const estimate = ref(null)
const logs = ref([])
const versions = ref([])
const error = ref(null)

const activeTab = ref('details')

async function loadAll() {
    const id = route.params.id
    try {
        if (versionParam.value) {
            const ver = await store.getEstimateVersion(versionParam.value, id)
            currentVersion.value = versionParam.value
            estimate.value = ver.payload
            activeTab.value = 'details'
        } else {
            estimate.value = await store.getEstimateById(id)
        }

        logs.value = await store.getEstimateLogs(id)
        versions.value = await store.getEstimateVersions(id)
        error.value = null
    } catch (e) {
        if (e.response?.status === 404) error.value = '❌ Смета не найдена.'
        else if (e.response?.status === 403) error.value = '🚫 Нет доступа.'
        else error.value = '⚠️ Ошибка загрузки.'
    }
}

onMounted(loadAll)
watch(() => route.query.version, loadAll)

onUnmounted(() => {
    store.currentEstimate = null
})

onClickOutside(menuRef, () => { showExport.value = false })

function tabClass(tabName) {
    return activeTab.value === tabName
        ? 'border-b-2 border-blue-600 text-blue-600'
        : 'text-gray-600 hover:text-gray-800'
}

function confirmDelete() { showConfirm.value = true }


async function copyEstimate() {
    const original = await store.getEstimateById(estimate.value.id)
    store.setCopiedEstimate(original)
    router.push('/estimates/create')
}

async function deleteEstimate() {
    await store.deleteEstimate(route.params.id)
    toast.success('Смета удалена')
    router.push('/estimates')
}

function chunkArray(array) {
    const len = array.length
    let chunkSize = 3

    if (len === 1) {
        chunkSize = 1
    } else if (len % 2 === 0) {
        chunkSize = 2
    }

    const chunks = []
    for (let i = 0; i < len; i += chunkSize) {
        chunks.push(array.slice(i, i + chunkSize))
    }
    return chunks
}


const groupedItems = computed(() => {
    const groups = {}
    for (const item of estimate.value?.items || []) {
        const category = item.category?.trim() || 'Без категории'
        if (!groups[category]) groups[category] = []
        groups[category].push(item)
    }
    return groups
})

function getGroupInternal(group) {
    return group.reduce((sum, item) => sum + getItemInternal(item), 0)
}
function getGroupExternal(group) {
    return group.reduce((sum, item) => sum + getItemExternal(item), 0)
}

function getItemInternal(item) {
    return item.quantity * item.internal_price;
}

function getItemExternal(item) {
    return item.quantity * item.external_price;
}

const totalInternal = computed(() => estimate.value?.items?.reduce((sum, item) => sum + getItemInternal(item), 0) || 0)
const totalExternal = computed(() => estimate.value?.items?.reduce((sum, item) => sum + getItemExternal(item), 0) || 0)

const totalDiff = computed(() => totalExternal.value - totalInternal.value)

const vat = computed(() => estimate.value?.vat_enabled ? totalExternal.value * (estimate.value.vat_rate / 100) : 0)
const totalWithVat = computed(() => totalExternal.value + vat.value)

function formatCurrency(val) {
    return `${val.toFixed(2)} ₽`
}

async function downloadJson(id) {
    await store.exportEstimate(id)
}

async function downloadExcel(estimate) {
    try {
        const blob = await store.downloadEstimateExcel(estimate.id)
        fileDownload(blob, `${estimate.name}.xlsx`)
        toast.success('Excel успешно загружен')
    } catch (e) {
        console.error(e)
        toast.error('Ошибка при загрузке Excel')
    }
}


async function downloadPdf(estimate) {
    try {
        const blob = await store.downloadEstimatePdf(estimate.id)
        fileDownload(blob, `${estimate.name}.pdf`)
        toast.success('PDF успешно загружен')
    } catch (e) {
        console.error(e)
        toast.error('Ошибка при загрузке PDF')
    }
}

async function viewVersion(ver) {
    const id = route.params.id
    // 1. Навигация
    await router.push({ path: `/estimates/${id}`, query: { version: ver } })
    // 2. Перезагрузить данные (чтобы loadAll учёл новый query.version)
    await loadAll()
    setTimeout(() => {
        const layoutMain = document.querySelector('main.overflow-y-auto')
        if (layoutMain) {
            layoutMain.scrollTo({ top: 0, behavior: 'smooth' })
        }
    }, 50)
}

async function restoreVersion(version) {
    const id = route.params.id
    try {
        await store.restoreVersion(version, estimate.value.id)
        toast.success(`Версия №${version} восстановлена`)
        await router.push({ path: `/estimates/${id}` })
        await loadAll()
    } catch (err) {
        console.error(err)
        toast.error('Не удалось восстановить версию')
    }
}

async function deleteVersion(version) {
    if (!confirm(`Вы точно хотите удалить версию №${version}?`)) return

    try {
        await store.deleteVersion(version, estimate.value.id)
        toast.success(`Версия №${version} удалена`)
        await router.push({ path: `/estimates/${estimate.value.id}` })
        await loadAll()
    } catch (err) {
        console.error(err)
        toast.error('Не удалось удалить версию')
    }
}
</script>