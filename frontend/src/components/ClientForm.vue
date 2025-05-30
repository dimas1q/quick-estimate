## frontend/src/components/ClientForm.vue
<template>
    <form @submit.prevent="submit" class="space-y-8 border bg-gray rounded-2xl shadow-md p-6">
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
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">Юридический адрес</label>
                <input v-model="client.legal_address" type="text" class="w-full border rounded-lg px-4 py-2" />
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">Фактический адрес</label>
                <input v-model="client.actual_address" type="text" class="w-full border rounded-lg px-4 py-2" />
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">ИНН</label>
                <input v-model="client.inn" type="text" class="w-full border rounded-lg px-4 py-2" />
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">КПП</label>
                <input v-model="client.kpp" type="text" class="w-full border rounded-lg px-4 py-2" />
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">БИК</label>
                <input v-model="client.bik" type="text" class="w-full border rounded-lg px-4 py-2" />
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">Расчетный счет</label>
                <input v-model="client.account" type="text" class="w-full border rounded-lg px-4 py-2" />
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">Банк</label>
                <input v-model="client.bank" type="text" class="w-full border rounded-lg px-4 py-2" />
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">Корреспондентский счет</label>
                <input v-model="client.corr_account" type="text" class="w-full border rounded-lg px-4 py-2" />
            </div>

            <!-- Примечания -->
            <div class="md:col-span-2">
                <label class="block text-sm font-semibold text-gray-700 mb-1">Примечания</label>
                <textarea v-model="client.notes" rows="2" placeholder="Любые дополнительные данные"
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
    legal_address: '',
    actual_address: '',
    inn: '',
    kpp: '',
    bik: '',
    account_number: '',
    bank: '',
    corr_account: '',
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
