## frontend/src/components/ClientForm.vue
<template>
    <form @submit.prevent="submit" class="space-y-8">
        <!-- 1. Двухколоночные поля -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Имя клиента -->
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">Имя клиента</label>
                <input v-model="client.name" type="text" placeholder="ФИО или имя"
                    class="w-full border border-gray-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300" />
            </div>
            <!-- Компания -->
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">Компания</label>
                <input v-model="client.company" type="text" placeholder="Название компании"
                    class="w-full border border-gray-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300" />
            </div>
            <!-- Email -->
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">Email</label>
                <input v-model="client.email" type="email" placeholder="email@example.com"
                    class="w-full border border-gray-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300" />
            </div>
            <!-- Телефон -->
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">Телефон</label>
                <input v-model="client.phone" type="tel" placeholder="+7 (999) 123-45-67"
                    class="w-full border border-gray-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300" />
            </div>
            <!-- Адрес (на всю ширину) -->
            <div class="md:col-span-2">
                <label class="block text-sm font-semibold text-gray-700 mb-1">Адрес</label>
                <input v-model="client.address" type="text" placeholder="Город, улица, дом"
                    class="w-full border border-gray-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300" />
            </div>
            <!-- Примечания -->
            <div class="md:col-span-2">
                <label class="block text-sm font-semibold text-gray-700 mb-1">Примечания</label>
                <textarea v-model="client.notes" rows="4" placeholder="Любые дополнительные данные"
                    class="w-full border border-gray-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none" />
            </div>
        </div>

        <!-- 2. Кнопки -->
        <div class="flex justify-end space-x-4">
            <button type="button" @click="cancel"
                class="px-6 py-2 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 transition">
                Отмена
            </button>
            <button type="submit" class="px-6 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition">
                Сохранить
            </button>
        </div>
    </form>
</template>

<script setup>
import { reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { defineProps, defineEmits } from 'vue'
import { useClientsStore } from '@/store/clients'
import { useToast } from 'vue-toastification'

const props = defineProps({ initial: Object, mode: { type: String, default: 'create' } })
const emit = defineEmits(['updated'])
const router = useRouter()
const toast = useToast()
const store = useClientsStore()

const client = reactive({
    name: '',
    company: '',
    email: '',
    phone: '',
    address: '',
    notes: ''
})

watch(() => props.initial, v => {
    if (v) Object.assign(client, v)
}, { immediate: true })

async function submit() {
    if (!client.name.trim()) {
        toast.error('Имя обязательно')
        return
    }
    let res
    if (props.mode === 'edit') {
        res = await store.updateClient(props.initial.id, client)
        emit('updated')
    } else {
        res = await store.createClient(client)
        toast.success('Клиент создан')
        router.push(`/clients/${res.id}`)
    }
}

function cancel() {
    router.back()
}
</script>
