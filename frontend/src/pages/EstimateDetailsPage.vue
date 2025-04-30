<template>
    <div class="px-16 py-8 max-w-6xl mx-auto">

        <div v-if="error" class="text-center text-red-500 text-lg font-medium mt-10">
            {{ error }}
        </div>
        <div v-if="estimate" class="space-y-6">
            <div class="flex justify-between items-center border-b pb-4 mb-6">
                <h1 class="text-3xl font-bold text-gray-800">{{ estimate.name }}</h1>

                <div class="flex space-x-3 items-center relative">
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

                    <!-- Остальные кнопки -->
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
                </div>

            </div>


            <div class="grid gap-3 text-sm text-gray-800">
                <p><strong>Клиент:</strong> {{ estimate.client_name }}</p>
                <p><strong>Компания клиента:</strong> {{ estimate.client_company }}</p>
                <p><strong>Контакт:</strong> {{ estimate.client_contact || '—' }} </p>
                <p><strong>Ответственный:</strong> {{ estimate.responsible || '—' }}</p>
                <p><strong>Заметки:</strong> {{ estimate.notes || '—' }}</p>
                <p><strong>НДС:</strong> {{ estimate.vat_enabled ? 'Включён (20%)' : 'Не включён' }}</p>

                <p class="text-sm text-gray-600">
                    Дата создания: {{ new Date(estimate.date).toLocaleString() }}
                </p>

                <p class="text-sm text-gray-600">
                    Последнее обновление: {{ new Date(estimate.updated_at).toLocaleString() }}
                </p>

                <h2 class="font-semibold text-lg mt-6">Услуги</h2>
                <ul class="space-y-2 ">
                    <div v-for="(groupItems, category) in groupedItems" :key="category" class="mb-6 space-y-3">
                        <h3 class="text-md font-semibold text-gray-700">{{ category }}</h3>

                        <ul class="space-y-2">
                            <li v-for="item in groupItems" :key="item.id"
                                class="border rounded p-3 text-sm flex flex-col gap-1">
                                <div><strong>{{ item.name }}</strong> — {{ item.description }}</div>
                                <div>Кол-во: {{ item.quantity }} {{ item.unit }}</div>
                                <div>Цена за единицу: {{ formatCurrency(item.unit_price) }}</div>
                                <div class="font-semibold text-right">
                                    Итог: {{ formatCurrency(getItemTotal(item)) }}
                                </div>
                            </li>
                        </ul>

                        <div class="text-right font-semibold text-sm text-gray-600 pt-2">
                            Итог по категории: {{ formatCurrency(getGroupTotal(groupItems)) }}
                        </div>
                    </div>

                </ul>
            </div>
        </div>

        <div v-if="estimate?.items?.length" class="pt-6">
            <p class="text-right font-semibold text-lg">
                Общая сумма: {{ formatCurrency(total) }}
            </p>
            <p class="text-right text-gray-700">
                НДС (20%): {{ formatCurrency(vat) }} <br />
                Итого с НДС: {{ formatCurrency(totalWithVat) }}
            </p>
        </div>

        <div v-if="logs.length" class="mt-8 border-t pt-4 text-sm">
            <h3 class="font-semibold text-gray-700 mb-2">История изменений</h3>
            <ul class="space-y-2">
                <li v-for="log in logs" :key="log.id" class="text-gray-600">
                    🕓 {{ new Date(log.timestamp).toLocaleString() }} — {{ log.description }}
                </li>
            </ul>
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
import { onMounted, onUnmounted, ref, computed } from 'vue'
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

const showExport = ref(false)
const menuRef = ref(null)
const showConfirm = ref(false)

const estimate = ref(null)
const logs = ref([])
const error = ref(null)

onMounted(async () => {
    try {
        estimate.value = await store.getEstimateById(route.params.id)
        logs.value = await store.getEstimateLogs(route.params.id)
    } catch (e) {
        if (e.response?.status === 403) {
            error.value = '🚫 У вас нет доступа к этой смете.'
        } else if (e.response?.status === 404) {
            error.value = '❌ Смета не найдена.'
        } else {
            error.value = '⚠️ Ошибка при загрузке сметы.'
        }
    }
})

onUnmounted(() => {
    store.currentEstimate = null
})

onClickOutside(menuRef, () => {
    showExport.value = false
})

function confirmDelete() {
    showConfirm.value = true
}

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
</script>