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

    <button type="submit" class="bg-blue-500 text-white px-4 py-2 rounded">Сохранить</button>
  </form>
</template>
  
  <script setup>
  import { reactive } from 'vue'
  import { useEstimatesStore } from '@/store/estimates'
  import EstimateItemsEditor from '@/components/EstimateItemsEditor.vue'
  
  const store = useEstimatesStore()
  
  const estimate = reactive({
    name: '',
    client_name: '',
    client_company: '',
    client_contact: '',
    responsible: '',
    notes: '',
    items: []
  })
  
  async function submit() {
    await store.createEstimate(estimate)
    Object.keys(estimate).forEach(k => estimate[k] = k === 'items' ? [] : '') // очистка
  }
  </script>
  
  <style scoped>
  .input {
    @apply border p-2 w-full rounded mb-2;
  }
  </style>
  