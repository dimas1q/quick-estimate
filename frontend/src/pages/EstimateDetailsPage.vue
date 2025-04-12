<template>
    <div v-if="estimate" class="space-y-6">
        <div class="flex justify-between items-center">
            <h1 class="text-2xl font-bold">{{ editing ? 'Редактирование сметы' : estimate.name }}</h1>

            <div class="space-x-2">
                <RouterLink :to="`/estimates/${estimate.id}/edit`"
                    class="inline-flex justify-center items-center px-4 py-2 rounded-md bg-yellow-500 text-white hover:bg-yellow-600 transition-all text-sm font-medium">
                    ✏️ Редактировать
                </RouterLink>
                <button @click="copyEstimate"
                    class="inline-flex justify-center items-center px-4 py-2 rounded-md bg-blue-500 text-white hover:bg-blue-600 transition-all text-sm font-medium">
                    📄 Копировать
                </button>
                <button @click="confirmDelete"
                    class="inline-flex justify-center items-center px-4 py-2 rounded-md bg-red-500 text-white hover:bg-red-600 transition-all text-sm font-medium">
                    🗑️ Удалить
                </button>
            </div>
        </div>

        <div v-if="editing">
            <EstimateForm :initial="estimate" @updated="handleUpdate" />
        </div>

        <div v-else class="grid gap-3 text-sm text-gray-800">
            <p><strong>Клиент:</strong> {{ estimate.client_name }} ({{ estimate.client_company }})</p>
            <p><strong>Контакты:</strong> {{ estimate.client_contact }}</p>
            <p><strong>Ответственный:</strong> {{ estimate.responsible }}</p>
            <p><strong>Заметки:</strong> {{ estimate.notes }}</p>

            <p class="text-sm text-gray-600">
                НДС:
                <span class="font-semibold">
                    {{ estimate.vat_enabled ? 'Включён (20%)' : 'Не включён' }}
                </span>
            </p>

            <p class="text-sm text-gray-600">
                Дата создания: {{ new Date(estimate.date).toLocaleString() }}
            </p>

            <p class="text-sm text-gray-600">
                Последнее обновление: {{ new Date(estimate.updated_at).toLocaleString() }}
            </p>

            <h2 class="font-semibold text-lg mt-6">Услуги</h2>
            <ul class="space-y-2">
                <div v-for="(groupItems, category) in groupedItems" :key="category" class="mb-6 space-y-3">
                    <h3 class="text-md font-semibold text-gray-700">{{ category }}</h3>

                    <ul class="space-y-2">
                        <li v-for="item in groupItems" :key="item.id"
                            class="border rounded p-3 text-sm flex flex-col gap-1">
                            <div><strong>{{ item.name }}</strong> — {{ item.description }}</div>
                            <div>Кол-во: {{ item.quantity }} {{ item.unit }}</div>
                            <div>Цена за единицу: {{ formatCurrency(item.unit_price) }}</div>
                            <div>Скидка:
                                <span v-if="item.discount_type === 'percent'">{{ item.discount }}%</span>
                                <span v-else>{{ formatCurrency(item.discount) }}</span>
                            </div>
                            <div class="font-semibold text-right">
                                Итог: {{ formatCurrency(getItemTotal(item)) }}
                            </div>
                        </li>
                    </ul>

                    <div class="text-right font-semibold text-sm text-gray-600 pt-2">
                        Итог по категории "{{ category }}": {{ formatCurrency(getGroupTotal(groupItems)) }}
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

    <div class="mt-8 border-t pt-4 text-sm">
        <h3 class="font-semibold text-gray-700 mb-2">История изменений</h3>
        <ul class="space-y-2">
            <li v-for="log in logs" :key="log.id" class="text-gray-600">
                🕓 {{ new Date(log.timestamp).toLocaleString() }} — {{ log.action }}: {{ log.description }}
            </li>
        </ul>
    </div>

    <!-- Модалка -->
    <div v-if="showConfirm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white p-6 rounded shadow max-w-sm w-full text-center">
            <p class="mb-4 font-semibold">Вы уверены, что хотите удалить данную смету?</p>
            <div class="flex justify-center gap-4">
                <button @click="deleteEstimate" class="bg-red-500 text-white px-4 py-2 rounded">Да, удалить</button>
                <button @click="showConfirm = false" class="bg-gray-300 px-4 py-2 rounded">Отмена</button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useEstimatesStore } from '@/store/estimates'
import EstimateForm from '@/components/EstimateForm.vue'
import { useToast } from 'vue-toastification'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const store = useEstimatesStore()
const toast = useToast()

const estimate = ref(null)
const showConfirm = ref(false)
const editing = ref(false)
const logs = ref([])

onMounted(async () => {
    estimate.value = await store.getEstimateById(route.params.id)
    logs.value = await axios.get(`http://localhost:8000/api/estimates/${route.params.id}/logs`).then(res => res.data)
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

function handleUpdate(updated) {
    editing.value = false
    estimate.value = updated
    toast.success('Смета обновлена')
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
    if (item.discount_type === 'percent') {
        return raw * (1 - item.discount / 100)
    } else {
        return Math.max(0, raw - item.discount)
    }
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
</script>

<style scoped>
.input {
    @apply border p-2 w-full rounded mb-2;
}
</style>