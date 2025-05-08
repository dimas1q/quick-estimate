## frontend/src/pages/EstimateDetailsPage.vue
<template>
    <div class="px-16 py-8 max-w-6xl mx-auto">

        <div v-if="error" class="text-center text-red-500 text-lg font-medium mt-10">
            {{ error }}
        </div>
        <div v-if="estimate" class="space-y-6">
            <div class="flex justify-between items-center pb-2 mb-6">
                <h1 class="text-3xl font-bold text-gray-800">{{ estimate.name }}</h1>

                <div class="flex space-x-3 items-center relative">
                    <!-- если мы в режиме версии, показываем другие кнопки -->
                    <template v-if="isVersionView">
                        <span
                            class="inline-flex items-center px-4 py-2 rounded-md bg-gray-300 text-gray-800 hover:bg-gray-400 transition-all text-sm font-medium shadow">Предпросмотр
                            версии #{{ currentVersion }}</span>
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
                                🖨️ Экспорт
                                <svg class="w-4 h-4 ml-2" fill="none" stroke="currentColor" stroke-width="2"
                                    viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                                </svg>
                            </button>

                            <div v-if="showExport"
                                class="absolute right-0 mt-2 w-34 bg-white rounded-xl shadow-xl ring-1 ring-black/5 backdrop-blur-sm border border-gray-100 animate-fade-in z-50">
                                <button @click="downloadJson(estimate.id)"
                                    class="block w-full text-left px-4 py-2 hover:bg-gray-50 transition-colors text-sm text-gray-700">
                                    Скачать JSON
                                </button>
                                <button @click="downloadExcel(estimate)"
                                    class="block w-full text-left px-4 py-2 hover:bg-gray-50 transition-colors text-sm text-gray-700 rounded-b-xl">
                                    Скачать Excel
                                </button>
                                <button @click="downloadPdf(estimate)"
                                    class="block w-full text-left px-4 py-2 hover:bg-gray-50 transition-colors text-sm text-gray-700 rounded-t-xl">
                                    Скачать PDF
                                </button>
                            </div>

                        </div>

                        <!-- Основные кнопки -->
                        <RouterLink :to="`/estimates/${estimate.id}/edit`"
                            class="inline-flex items-center px-4 py-2 rounded-md bg-yellow-500 text-white hover:bg-yellow-600 transition-all text-sm font-medium shadow">
                            ✏️ Редактировать
                        </RouterLink>
                        <button @click="copyEstimate"
                            class="inline-flex items-center px-4 py-2 rounded-md bg-blue-500 text-white hover:bg-blue-600 transition-all text-sm font-medium shadow">
                            📋 Копировать
                        </button>
                        <button @click="confirmDelete"
                            class="inline-flex items-center px-4 py-2 rounded-md bg-red-500 text-white hover:bg-red-600 transition-all text-sm font-medium shadow">
                            🗑️ Удалить
                        </button>
                    </template>
                </div>
            </div>

            <div class="flex border-b mb-6">
                <button @click="activeTab = 'details'" :class="tabClass('details')"
                    class="px-4 py-2 -mb-px font-medium">
                    Сведения
                </button>
                <button @click="activeTab = 'history'" :class="tabClass('history')"
                    class="px-4 py-2 -mb-px font-medium">
                    История
                </button>
            </div>


            <div v-if="activeTab === 'details'">
                <div class="grid gap-3 text-sm text-gray-800">
                    <div class="grid grid-cols-2 gap-4">
                        <p><strong>Клиент:</strong> {{ estimate.client?.name || '—' }}</p>
                        <p><strong>Ответственный:</strong> {{ estimate.responsible || '—' }}</p>

                        <p><strong>Контакт:</strong> {{ estimate.client?.email || '—' }}</p>
                        <p><strong>НДС:</strong> {{ estimate.vat_enabled ? 'Включён (20%)' : 'Не включён' }}</p>

                        <p><strong>Компания клиента:</strong> {{ estimate.client?.company || '—' }}</p>
                        <p class="text-sm text-gray-600">
                            Дата создания: {{ new Date(estimate.date).toLocaleString() }}
                        </p>
                        <p><strong>Заметки:</strong> {{ estimate.notes || '—' }}</p>

                        <p class="text-sm text-gray-600">
                            Последнее обновление: {{ new Date(estimate.updated_at).toLocaleString() }}
                        </p>
                    </div>

                    <div class="border bg-gray-50 rounded-2xl shadow-md p-6 mt-8">
                        <div v-for="(groupItems, category) in groupedItems" :key="category" class="mb-10">
                            <h3 class="text-lg font-semibold text-gray-800 mb-4 text-center pb-1">{{ category }}</h3>

                            <div class="space-y-4">
                                <div v-for="(row, rowIndex) in chunkArray(groupItems, 3)" :key="rowIndex"
                                    class="flex gap-4">
                                    <div v-for="item in row" :key="item.id"
                                        :class="`flex-1 ${row.length === 1 ? 'max-w-full' : row.length === 2 ? 'max-w-1/2' : 'max-w-1/3'}`"
                                        class="bg-gray border border-gray-200 rounded-xl shadow-sm p-4 hover:shadow-md transition-shadow duration-200">
                                        <div class="flex justify-between items-start mb-2">
                                            <div>
                                                <p class="text-base font-semibold text-gray-900">{{ item.name }}</p>
                                                <p class="text-sm text-gray-600">{{ item.description }}</p>
                                            </div>
                                            <div class="text-sm text-gray-500 text-right whitespace-nowrap">
                                                {{ item.quantity }} {{ item.unit }}
                                            </div>
                                        </div>
                                        <div class="flex justify-between text-sm text-gray-700 pt-2">
                                            <span>Цена за единицу:</span>
                                            <span>{{ formatCurrency(item.unit_price) }}</span>
                                        </div>
                                        <div class="flex justify-between font-semibold text-sm text-gray-900">
                                            <span>Итог:</span>
                                            <span>{{ formatCurrency(getItemTotal(item)) }}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="text-right font-semibold text-base text-gray-700 mt-4">
                                Сумма по категории: {{ formatCurrency(getGroupTotal(groupItems)) }}
                            </div>
                        </div>


                        <div v-if="estimate?.items?.length" class="pt-6">
                            <p class="text-right font-semibold text-lg pt-4 border-t">
                                Общая сумма: {{ formatCurrency(total) }}
                            </p>
                            <p class="text-right text-gray-700">
                                НДС (20%): {{ formatCurrency(vat) }} <br />
                                Итого с НДС: {{ formatCurrency(totalWithVat) }}
                            </p>
                        </div>

                    </div>


                </div>
            </div>

            <div v-else>

                <div v-if="logs.length" class="text-sm w-full mt-6">
                    <h3 class="font-semibold text-gray-800 text-sm mb-4 flex items-center gap-2">
                        История изменений
                    </h3>

                    <div class="overflow-x-auto rounded-lg shadow-sm ">
                        <table class="w-full text-sm text-gray-700">
                            <thead class="bg-gray-100 border-b text-left">
                                <tr>
                                    <th class="px-4 py-2 font-medium text-gray-600 whitespace-nowrap">Дата и время</th>
                                    <th class="px-4 py-2 font-medium text-gray-600 whitespace-nowrap">Действие</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="log in logs" :key="log.id" class="hover:bg-gray-50 border-b">
                                    <td class="px-4 py-2 text-gray-600 whitespace-nowrap">{{ new
                                        Date(log.timestamp).toLocaleString() }}</td>
                                    <td class="px-4 py-2 text-gray-600">{{ log.description }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>


                <!-- 5. Версии -->
                <div v-if="versions.length" class="mt-8 border-t pt-6 text-sm">
                    <h3 class="font-semibold text-gray-700 mb-4">История версий</h3>
                    <div class="overflow-x-auto rounded-lg shadow-sm ">
                        <table class="w-full text-left text-gray-700">
                            <thead class="bg-gray-100 ">
                                <tr>
                                    <th class="px-4 py-2 font-medium text-gray-600">Версия</th>
                                    <th class="px-4 py-2 font-medium text-gray-600">Дата создания</th>
                                    <th class="px-4 py-2 font-medium text-gray-600 text-right">Действия</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="v in versions" :key="v.version" class="border-b hover:bg-gray-50">
                                    <td class="px-4 py-2 text-gray-600">№{{ v.version }}</td>
                                    <td class="px-4 py-2 text-gray-600"> {{ new Date(v.created_at).toLocaleString() }}
                                    </td>
                                    <td class="px-4 py-2 text-right space-x-2">
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
            <div class="bg-white p-6 rounded shadow max-w-sm w-full text-center">
                <p class="mb-4 font-semibold">Вы уверены, что хотите удалить данную смету?</p>
                <div class="flex justify-center gap-4">
                    <button @click="deleteEstimate" class="bg-red-500 text-white px-4 py-2 rounded-md">Да,
                        удалить</button>
                    <button @click="showConfirm = false" class="bg-gray-300 px-4 py-2 rounded-md">Отмена</button>
                </div>
            </div>
        </div>

    </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useEstimatesStore } from '@/store/estimates'
import { onClickOutside } from '@vueuse/core'
import { useToast } from 'vue-toastification'

import axios from 'axios'
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
            // загрузка конкретной версии
            const { data: ver } = await axios.get(
                `http://localhost:8000/api/versions/${versionParam.value}`,
                { params: { estimate_id: id } }
            )
            currentVersion.value = versionParam.value
            estimate.value = ver.payload
            activeTab.value = 'details'
        } else {
            // обычная смета
            estimate.value = await store.getEstimateById(id)
        }
        logs.value = await store.getEstimateLogs(id)
        versions.value = (await axios.get(`http://localhost:8000/api/versions`, {
            params: { estimate_id: id }
        })).data
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

function getGroupTotal(items) {
    return items.reduce((sum, item) => sum + getItemTotal(item), 0)
}

const getItemTotal = (item) => {
    const raw = item.quantity * item.unit_price
    return raw
}

const total = computed(() => {
    return estimate.value?.items?.reduce((sum, item) => sum + getItemTotal(item), 0) || 0
})

const vat = computed(() =>
    estimate.value?.vat_enabled ? total.value * 0.2 : 0
)
const totalWithVat = computed(() => total.value + vat.value)

function formatCurrency(val) {
    return `${val.toFixed(2)} ₽`
}

async function downloadExcel(estimate) {
    try {
        const res = await axios.get(`http://localhost:8000/api/estimates/${estimate.id}/export/excel`, {
            responseType: 'blob'
        })
        fileDownload(res.data, `${estimate.name}.xlsx`)
        toast.success('Excel успешно загружен')
    } catch (e) {
        console.error(e)
        toast.error('Ошибка при загрузке Excel')
    }
}

async function downloadJson(id) {
    await store.exportEstimate(id)
}

async function downloadPdf(estimate) {
    try {
        const res = await axios.get(`http://localhost:8000/api/estimates/${estimate.id}/export/pdf`, {
            responseType: 'blob'
        })
        fileDownload(res.data, `${estimate.name}.pdf`)
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
    // 4. Перезагрузить данные (чтобы loadAll учёл новый query.version)
    await loadAll()
}

async function restoreVersion(version) {
    const id = route.params.id
    try {
        await axios.post(
            `http://localhost:8000/api/versions/${version}/restore`,
            null,
            { params: { estimate_id: estimate.value.id } }
        )

        toast.success(`Версия №${version} восстановлена`)
        // Сбросить query и вернуть на основную версию сметы
        await router.push({ path: `/estimates/${id}` })
        await loadAll()
    } catch (err) {
        console.error(err)
        toast.error('Не удалось восстановить версию')
    }
}

async function copyVersion(version) {
    const id = route.params.id
    store.setCopiedEstimate({ ...estimate.value })
    router.push('/estimates/create')
}

async function deleteVersion(version) {
    if (!confirm(`Вы точно хотите удалить версию №${version}?`)) return

  try {
    await axios.delete(
      `http://localhost:8000/api/versions/${version}`, 
      { params: { estimate_id: estimate.value.id } }
    )
    toast.success(`Версия №${version} удалена`)
    // Сбросить query и вернуть на основную версию сметы
    await router.push({ path: `/estimates/${estimate.value.id}` })
    await loadAll()
  } catch (err) {
    console.error(err)
    toast.error('Не удалось удалить версию')
  }
}
</script>