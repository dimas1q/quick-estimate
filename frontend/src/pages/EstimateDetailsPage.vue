<template>
    <div v-if="estimate" class="space-y-6">
        <div class="flex justify-between items-center">
            <h1 class="text-2xl font-bold">{{ editing ? 'Редактирование сметы' : estimate.name }}</h1>

            <div class="space-x-2">
                <button v-if="!editing" @click="editing = true" class="bg-yellow-400 text-black px-4 py-2 rounded">
                    ✏️ Редактировать
                </button>
                <button @click="confirmDelete" class="bg-red-500 text-white px-4 py-2 rounded">
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

            <h2 class="font-semibold text-lg mt-6">Услуги</h2>
            <ul class="space-y-2">
                <li v-for="item in estimate.items" :key="item.id" class="border rounded p-3">
                    {{ item.name }} — {{ item.quantity }} {{ item.unit }} × {{ item.unit_price }} ₽
                    <span v-if="item.discount">– скидка {{ item.discount }} ({{ item.discount_type }})</span>
                </li>
            </ul>
        </div>
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
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useEstimatesStore } from '@/store/estimates'
import EstimateForm from '@/components/EstimateForm.vue'
import { useToast } from 'vue-toastification'

const route = useRoute()
const router = useRouter()
const store = useEstimatesStore()
const toast = useToast()

const estimate = ref(null)
const showConfirm = ref(false)
const editing = ref(false)

onMounted(async () => {
    estimate.value = await store.getEstimateById(route.params.id)
})

function confirmDelete() {
    showConfirm.value = true
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
</script>

<style scoped>
.input {
    @apply border p-2 w-full rounded mb-2;
}
</style>