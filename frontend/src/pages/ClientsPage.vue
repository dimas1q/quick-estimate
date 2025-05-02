<template>
    <div class="space-y-6 px-24 py-8 max-w-6xl mx-auto">
        <div class="flex justify-between items-center">
            <h1 class="text-2xl font-bold">Клиенты</h1>
            <!-- позже сюда можно кнопку импорта JSON -->
        </div>

        <div class="flex gap-6 items-start">
            <!-- Левый столбец: список клиентов -->
            <div class="flex-1 space-y-4">
                <div v-for="c in store.clients" :key="c.id" class="border p-4 rounded shadow-sm space-y-1 py-4">
                    <div class="font-semibold text-lg">{{ c.name }}</div>
                    <div class="text-sm text-gray-600">Компания: {{ c.company || '—' }}</div>
                    <div class="text-sm text-gray-600">Контакт: {{ c.email || c.phone || '—' }}</div>
                    <router-link :to="`/clients/${c.id}`" class="text-blue-600 text-sm hover:underline">
                        Подробнее →
                    </router-link>
                </div>
                <div v-if="store.clients.length === 0" class="text-center text-gray-500 border p-4 rounded py-8">
                    Клиенты отсутствуют.
                </div>
            </div>

            <!-- Правый столбец: кнопка добавления и фильтры -->
            <div class="w-64 space-y-4">
                <router-link to="/clients/create" class="btn-primary block w-full text-center">
                    Добавить клиента
                </router-link>
                <div class="border rounded p-4 shadow-sm space-y-4 text-center">
                    <h2 class="font-semibold text-lg">Фильтр</h2>
                    <div>
                        <label class="text-sm text-gray-600">Имя</label>
                        <input v-model="filters.name" class="input-field mt-1" type="text" placeholder="Поиск по имени" />
                    </div>
                    <div>
                        <label class="text-sm text-gray-600">Компания</label>
                        <input v-model="filters.company" class="input-field mt-1" type="text" placeholder="Поиск по компании" />
                    </div>
                    <div class="flex gap-2 pt-2">
                        <button @click="applyFilters" class="btn-secondary w-full">Применить</button>
                        <button @click="resetFilters" class="btn-secondary w-full">Сбросить</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useClientsStore } from '@/store/clients'

const store = useClientsStore()
const filters = ref({ q: '' })

function applyFilters() {
    const query = {
        name: filters.value.name,
        company: filters.value.company,
    }
    store.fetchClients(query)
}
function resetFilters() {
    filters.value.name = ''
    filters.value.company = ''
    store.fetchClients()
}

onMounted(() => {
    store.fetchClients()
})
</script>
