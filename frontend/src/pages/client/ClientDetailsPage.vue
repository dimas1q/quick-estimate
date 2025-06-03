## frontend/src/pages/client/ClientDetailsPage.vue
<template>
    <div class="py-8 max-w-6xl mx-auto">
        <div v-if="!client" class="text-center py-10 text-lg text-gray-500 dark:text-gray-400">Загрузка…</div>
        <div v-else class="space-y-6">
            <!-- Шапка и кнопки -->
            <div class="flex justify-between items-center pb-2 mb-6">
                <div>
                    <h1 class="text-3xl font-bold text-gray-800 dark:text-white">
                        Клиент: {{ client.name }}
                    </h1>
                </div>
                <div class="flex space-x-3 items-center">
                    <RouterLink :to="`/clients/${client.id}/edit`"
                        class="inline-flex items-center px-4 py-2 rounded-md bg-yellow-500 text-white hover:bg-yellow-600 transition-all text-sm font-medium shadow">
                        Редактировать
                    </RouterLink>
                    <button @click="confirmDelete"
                        class="inline-flex items-center px-4 py-2 rounded-md bg-red-500 text-white hover:bg-red-600 transition-all text-sm font-medium shadow">
                        Удалить
                    </button>
                </div>
            </div>

            <!-- Блок данных — такой же стиль как у сметы -->
            <div class="grid gap-3 text-sm text-gray-800 dark:text-gray-200">
                <div
                    class="grid grid-cols-2 gap-4 shadow-sm border dark:border-qe-black2 bg-white dark:bg-qe-black rounded-2xl p-6">
                    <p><strong>Компания:</strong> {{ client.company || '—' }}</p>

                    <p><strong>Расчетный счет:</strong> {{ client.account || '—' }}</p>
                    <p><strong>Email:</strong> {{ client.email || '—' }}</p>
                    <p><strong>Корр. счет:</strong> {{ client.corr_account || '—' }}</p>

                    <p><strong>Фактический адрес:</strong> {{ client.actual_address || '—' }}</p>
                    <p><strong>ИНН:</strong> {{ client.inn || '—' }}</p>
                    <p><strong>Юридический адрес:</strong> {{ client.legal_address || '—' }}</p>

                    <p><strong>БИК:</strong> {{ client.bik || '—' }}</p>
                    <p><strong>Телефон:</strong> {{ client.phone || '—' }}</p>
                    <p><strong>КПП:</strong> {{ client.kpp || '—' }}</p>
                    <p><strong>Примечания:</strong> {{ client.notes || '—' }}</p>
                    <p><strong>Банк:</strong> {{ client.bank || '—' }}</p>



                </div>
            </div>

            <!-- Сметы клиента -->
            <div class="border bg-white dark:bg-qe-black dark:border-qe-black2 rounded-2xl shadow-sm p-6 mt-6">
                <h2 class="text-xl font-semibold mb-4 text-gray-800 dark:text-white">Сметы клиента</h2>
                <div v-if="estimates.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div v-for="e in estimates" :key="e.id"
                        class="border bg-white dark:bg-qe-black dark:border-qe-black2 p-4 rounded-xl shadow-sm flex flex-col gap-2 hover:shadow-md transition">
                        <div class="flex justify-between items-center">
                            <RouterLink :to="`/estimates/${e.id}`" class="font-semibold ">
                                {{ e.name }}
                            </RouterLink>
                            <span class="text-gray-500 text-xs">{{ new Date(e.date).toLocaleDateString() }}</span>
                        </div>
                    </div>
                </div>
                <div v-else
                    class="text-center text-gray-500 border border-gray-200 dark:border-qe-black2 p-4 rounded-xl py-8 mt-2 bg-white dark:bg-qe-black">
                    Сметы отсутствуют.
                </div>
            </div>
        </div>

        <!-- Модалка подтверждения удаления -->
        <QeModal v-model="showConfirm" @confirm="deleteClient">
            Вы уверены, что хотите удалить данного клиента?
            <template #confirm>Да, удалить</template>
            <template #cancel>Отмена</template>
        </QeModal>
    </div>
</template>
  
  

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useClientsStore } from '@/store/clients'
import { useToast } from 'vue-toastification'
import QeModal from '@/components/QeModal.vue'

const route = useRoute()
const router = useRouter()
const client = ref(null)
const estimates = ref([])
const showConfirm = ref(false)
const store = useClientsStore()
const toast = useToast()

onMounted(async () => {
    const { client: c, estimates: e } = await store.getClientWithEstimates(route.params.id)
    client.value = c
    estimates.value = e
})

function confirmDelete() {
    showConfirm.value = true
}

async function deleteClient() {
    try {
        await store.deleteClient(route.params.id)
        toast.success('Клиент удален')
        router.push('/clients')
    } catch (e) {
        if (e.response?.data?.detail) {
            toast.error(e.response.data.detail)
        } else {
            toast.error('Ошибка удаления клиента')
        }
    }
}
</script>
