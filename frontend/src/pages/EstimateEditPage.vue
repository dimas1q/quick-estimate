<template>
    <div v-if="estimate">
        <h1 class="text-2xl font-bold mb-4">Редактирование сметы {{ estimate?.name }}</h1>
        <EstimateForm :initial="estimate" mode="edit" @updated="onUpdated" />
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

onMounted(async () => {
    estimate.value = await store.getEstimateById(route.params.id)
})

function onUpdated() {
    toast.success('Смета сохранена')
    router.push(`/estimates/${route.params.id}`)
}
</script>

<style scoped>
.input {
    @apply border p-2 w-full rounded mb-2;
}
</style>