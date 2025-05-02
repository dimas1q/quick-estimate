<template>
    <form @submit.prevent="submit" class="space-y-6 max-w-2xl mx-auto bg-white rounded-lg p-6 shadow-sm">
        <div class="space-y-2">
            <label class="block text-sm font-medium text-gray-700">Имя клиента</label>
            <input v-model="client.name" type="text" class="input-field" />
        </div>
        <div class="space-y-2">
            <label class="block text-sm font-medium text-gray-700">Компания</label>
            <input v-model="client.company" type="text" class="input-field" />
        </div>
        <div class="space-y-2">
            <label class="block text-sm font-medium text-gray-700">Email</label>
            <input v-model="client.email" type="email" class="input-field" />
        </div>
        <div class="space-y-2">
            <label class="block text-sm font-medium text-gray-700">Телефон</label>
            <input v-model="client.phone" type="text" class="input-field" />
        </div>
        <div class="space-y-2">
            <label class="block text-sm font-medium text-gray-700">Адрес</label>
            <input v-model="client.address" type="text" class="input-field" />
        </div>
        <div class="space-y-2">
            <label class="block text-sm font-medium text-gray-700">Примечания</label>
            <textarea v-model="client.notes" class="input-field" rows="4"></textarea> 
        </div>
        <!-- здесь можно добавить ещё поля: адрес, примечания и т.п.-->
        <div class="flex gap-2 pt-4 justify-end">
            <button type="submit" class="btn-primary">Сохранить</button>
            <button type="button" @click="cancel" class="btn-danger">Отмена</button>
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
