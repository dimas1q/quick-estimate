## frontend/src/components/ClientForm.vue
<template>
    <form @submit.prevent="submit"
        class="space-y-8 border bg-white dark:bg-qe-black3 dark:border-qe-black2 rounded-2xl shadow-md p-6">
        <!-- 1. Двухколоночные поля -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Имя клиента -->
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">Имя клиента</label>
                <input v-model="client.name" type="text" placeholder="ФИО или имя" class="w-full qe-input" />
            </div>
            <!-- Компания -->
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">Компания</label>
                <input v-model="client.company" type="text" placeholder="Название компании" class="w-full qe-input" />
            </div>
            <!-- Email -->
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">Email</label>
                <input v-model="client.email" type="email" placeholder="email@example.com" class="w-full qe-input" />
            </div>
            <!-- Телефон -->
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">Телефон</label>
                <input v-model="client.phone" type="tel" placeholder="+7 (999) 123-45-67" class="w-full qe-input" />
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">Юридический адрес</label>
                <input v-model="client.legal_address" type="text" class="w-full qe-input" />
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">Фактический адрес</label>
                <input v-model="client.actual_address" type="text" class="w-full qe-input" />
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">ИНН</label>
                <input v-model="client.inn" type="text" class="w-full qe-input" />
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">КПП</label>
                <input v-model="client.kpp" type="text" class="w-full qe-input" />
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">БИК</label>
                <input v-model="client.bik" type="text" class="w-full qe-input" />
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">Расчетный счет</label>
                <input v-model="client.account" type="text" class="w-full qe-input" />
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">Банк</label>
                <input v-model="client.bank" type="text" class="w-full qe-input" />
            </div>
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-1">Корреспондентский счет</label>
                <input v-model="client.corr_account" type="text" class="w-full qe-input" />
            </div>

        </div>

        <!-- 2. Кнопки -->
        <div class="flex justify-end space-x-2">
            <button type="button" @click="cancel" class="qe-btn-secondary">
                Отмена
            </button>
            <button type="submit" class="qe-btn">
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
    account: '',
    bank: '',
    corr_account: '',
    
})

watch(() => props.initial, v => {
    if (v) Object.assign(client, v)
}, { immediate: true })

async function submit() {
    if (!client.name.trim()) {
        toast.error('Имя обязательно')
        return
    }
    if (!(client.email || '').trim() && !(client.phone || '').trim()) {
        toast.error('Укажите хотя бы один контакт: Email или Телефон')
        return
    }

    // Готовим данные без пустых строк
    const dataToSend = { ...client }
    dataToSend.email = (dataToSend.email || '').trim() === '' ? null : dataToSend.email
    dataToSend.phone = (dataToSend.phone || '').trim() === '' ? null : dataToSend.phone

    let res
    if (props.mode === 'edit') {
        res = await store.updateClient(props.initial.id, dataToSend)
        emit('updated')
    } else {
        res = await store.createClient(dataToSend)
        toast.success('Клиент создан')
        router.push(`/clients/${res.id}`)
    }
}

function cancel() {
    router.back()
}
</script>
