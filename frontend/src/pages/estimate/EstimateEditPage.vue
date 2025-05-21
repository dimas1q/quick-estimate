## frontend/src/pages/EstimateEditPage.vue
<template>
    <div>
        <div v-if="error" class="text-red-500 text-center text-lg font-medium mt-10">
            {{ error }}
        </div>
        <div v-if="estimate" class="space-y-6 max-w-6xl mx-auto px-16 py-8">
            <h1 class="text-2xl font-bold mb-6 text-center py-2">Редактирование сметы: {{ estimate?.name }}</h1>
            <EstimateForm :initial="estimate" mode="edit" @updated="onUpdated" />
        </div>
    </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useEstimatesStore } from '@/store/estimates'
import EstimateForm from '@/components/EstimateForm.vue'
import { useToast } from 'vue-toastification'

const route = useRoute()
const router = useRouter()
const store = useEstimatesStore()
const toast = useToast()

const estimate = ref(null)
const error = ref(null)

onMounted(async () => {
    try {
        estimate.value = await store.getEstimateById(route.params.id)
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

function onUpdated() {
    toast.success('Смета сохранена')
    router.push(`/estimates/${route.params.id}`)
}
</script>
