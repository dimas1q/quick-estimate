<script setup>
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useEstimatesStore } from '@/store/estimates'
import EstimateItemsEditor from '@/components/EstimateItemsEditor.vue'
import { useToast } from 'vue-toastification'

const router = useRouter()
const toast = useToast()
const store = useEstimatesStore()

const estimate = reactive({
  name: '',
  client_name: '',
  client_company: '',
  client_contact: '',
  responsible: '',
  notes: '',
  items: [] // создаём как новый объект, чтобы не ломался v-model
})

async function submit() {
  const created = await store.createEstimate(estimate)
  toast.success('Смета успешно создана!')
  router.push(`/estimates/${created.id}`)
}

function cancel() {
  router.push('/estimates')
}
</script>

<template>
  <form @submit.prevent="submit" class="space-y-4">

    <div>
      <label class="block font-semibold mb-1">Название сметы</label>
      <input v-model="estimate.name" class="input" required />
    </div>

    <div>
      <label class="block font-semibold mb-1">Имя клиента</label>
      <input v-model="estimate.client_name" class="input" />
    </div>

    <div>
      <label class="block font-semibold mb-1">Компания клиента</label>
      <input v-model="estimate.client_company" class="input" />
    </div>

    <div>
      <label class="block font-semibold mb-1">Контакты</label>
      <input v-model="estimate.client_contact" class="input" />
    </div>

    <div>
      <label class="block font-semibold mb-1">Ответственный</label>
      <input v-model="estimate.responsible" class="input" />
    </div>

    <div>
      <label class="block font-semibold mb-1">Заметки</label>
      <textarea v-model="estimate.notes" class="input" />
    </div>

    <EstimateItemsEditor v-model="estimate.items" />

    <div class="flex gap-4 pt-4">
      <button type="submit" class="bg-blue-500 text-white px-4 py-2 rounded">Сохранить</button>
      <button type="button" @click="cancel" class="bg-gray-200 text-black px-4 py-2 rounded">Отмена</button>
    </div>
  </form>
</template>
  
  <style scoped>
  .input {
    @apply border p-2 w-full rounded mb-2;
  }
  </style>
  
