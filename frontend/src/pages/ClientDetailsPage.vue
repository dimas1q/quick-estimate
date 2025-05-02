<template>
    <div class="px-16 py-8 max-w-6xl mx-auto">
        <div v-if="!client" class="text-center py-10">Загрузка…</div>
        <div v-else class="space-y-6">
            <div class="flex justify-between items-center border-b pb-4 mb-6">
                <h1 class="text-3xl font-bold">{{ client.name }}</h1>
                <div class="flex space-x-3 items-center relative">
                    <RouterLink :to="`/clients/${client.id}/edit`"
                        class="inline-flex items-center px-4 py-2 rounded-md bg-yellow-500 text-white hover:bg-yellow-600 transition-all text-sm font-medium shadow">
                        ✏️ Редактировать</RouterLink>
                    <button @click="confirmDelete"
                        class="inline-flex items-center px-4 py-2 rounded-md bg-red-500 text-white hover:bg-red-600 transition-all text-sm font-medium shadow">
                        🗑️ Удалить
                    </button>
                </div>
            </div>
            <div class="grid grid-cols-2 gap-4 text-sm">
                <p><strong>Компания:</strong> {{ client.company || '—' }}</p>
                <p><strong>Email:</strong> {{ client.email || '—' }}</p>
                <p><strong>Телефон:</strong> {{ client.phone || '—' }}</p>
                <p><strong>Адрес:</strong> {{ client.address || '—' }}</p>
                <p><strong>Примечания:</strong> {{ client.notes || '—' }}</p>
            </div>
            <div class="mt-8">
                <h2 class="text-xl font-semibold mb-4">Сметы клиента</h2>
                <ul class="space-y-2">
                    <li v-for="e in estimates" :key="e.id" class="border p-4 rounded shadow-sm">
                        <RouterLink :to="`/estimates/${e.id}`" class="font-medium">{{ e.name }}</RouterLink>
                        <span class="text-gray-500 text-sm ml-2">{{ new Date(e.date).toLocaleDateString() }}</span>
                    </li>
                    <li v-if="estimates.length === 0" class="text-center text-gray-500 border p-4 rounded py-8">
                        Сметы отсутствуют.
                    </li>
                </ul>
            </div>
        </div>

        <div v-if="showConfirm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white p-6 rounded shadow max-w-sm w-full text-center">
                <p class="mb-4 font-semibold">Вы уверены, что хотите удалить данного клиента?</p>
                <div class="flex justify-center gap-4">
                    <button @click="deleteClient" class="bg-red-500 text-white px-4 py-2 rounded-md">Да,
                        удалить</button>
                    <button @click="showConfirm = false" class="bg-gray-300 px-4 py-2 rounded-md">Отмена</button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useClientsStore } from '@/store/Clients'
import { useToast } from 'vue-toastification'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const client = ref(null)
const estimates = ref([])
const showConfirm = ref(false)
const store = useClientsStore()
const toast = useToast()

onMounted(async () => {
    const { data } = await axios.get(`http://localhost:8000/api/clients/${route.params.id}`)
    client.value = data
    // подгружаем сметы этого клиента
    const res2 = await axios.get('http://localhost:8000/api/estimates', {
        params: { client: data.id }
    })
    estimates.value = res2.data
})

function confirmDelete() {
    showConfirm.value = true
}

async function deleteClient() {
    await store.deleteClient(route.params.id)
    toast.success('Клиент удален')
    router.push('/clients')
}
</script>
