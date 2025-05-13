<template>
<div>
    <div v-if="error" class="text-red-500 text-center text-lg font-medium mt-10">
        {{ error }}
    </div>
    <div v-if="client" class="space-y-6 max-w-6xl mx-auto px-16 py-8">
        <h1 class="text-2xl font-bold mb-10 text-center py-2">Редактирование клиента {{ client?.name }}</h1>
        <ClientForm :mode="'edit'" :initial="client" @updated="onUpdated" />
    </div>
</div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useClientsStore } from '@/store/clients'
import ClientForm from '@/components/ClientForm.vue'    
import { useToast } from 'vue-toastification'

const route = useRoute()
const router = useRouter()
const store = useClientsStore()
const client = ref(null)
const toast = useToast()
const error = ref(null)

onMounted(async () => {
    try {
        client.value = await store.getClientById(route.params.id)
    } catch (e) {
        if (e.response?.status === 403) {
            error.value = '🚫 У вас нет доступа к этому клиенту.'
        } else if (e.response?.status === 404) {
            error.value = '❌ Клиент не найден.'
        } else {
            error.value = '⚠️ Ошибка при загрузке клиента.'
        }
    }
    
})

function onUpdated() {
    toast.success('Клиент сохранен')
    router.push(`/clients/${route.params.id}`)
}
</script>
