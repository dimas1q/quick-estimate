<script setup>
import { reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useEstimatesStore } from '@/store/estimates'
import EstimateItemsEditor from '@/components/EstimateItemsEditor.vue'
import { useToast } from 'vue-toastification'

const props = defineProps({
  initial: Object,
  mode: {
    type: String,
    default: 'create'
  }
})
const emit = defineEmits(['updated'])

const store = useEstimatesStore()
const toast = useToast()
const router = useRouter()

const requiredFields = ['name', 'client_name', 'client_company']


const estimate = reactive({
  name: '',
  client_name: '',
  client_company: '',
  client_contact: '',
  responsible: '',
  notes: '',
  items: []
})

// если передали initial — заполним
watch(() => props.initial, (value) => {
  if (value) {
    Object.assign(estimate, {
      name: props.mode === 'copy' ? `Копия: ${value.name}` : value.name,
      client_name: value.client_name || '',
      client_company: value.client_company || '',
      client_contact: value.client_contact || '',
      responsible: value.responsible || '',
      notes: value.notes || '',
      vat_enabled: value.vat_enabled ?? true,
      items: (value.items || []).map(item => ({
        ...item,
        category_input: item.category || ''
      }))
    })
  }
}, { immediate: true })

async function submit() {
  if (!validateEstimate()) return

  let result
  if (props.mode === 'edit') {
    result = await store.updateEstimate(props.initial.id, estimate)
    emit('updated')
  } else {
    result = await store.createEstimate(estimate)
    toast.success('Смета создана')
    router.push(`/estimates/${result.id}`)
  }
}

function cancel() {
  router.back()
}

function validateEstimate() {
  if (!estimate.name?.trim()) {
    toast.error("Название сметы обязательно")
    return false
  }
  if (!estimate.client_name?.trim()) {
    toast.error("Имя клиента обязательно")
    return false
  }
  if (!estimate.client_company?.trim()) {
    toast.error("Компания клиента обязательна")
    return false
  }
  if (!estimate.items.length) {
    toast.error("Добавьте хотя бы одну услугу")
    return false
  }

  for (const [i, item] of estimate.items.entries()) {
    if (!item.name?.trim()) {
      toast.error(`Услуга №${i + 1}: название обязательно`)
      return false
    }
    if (!item.quantity || item.quantity <= 0) {
      toast.error(`Услуга №${i + 1}: количество должно быть > 0`)
      return false
    }
    if (!item.unit_price || item.unit_price <= 0) {
      toast.error(`Услуга №${i + 1}: цена должна быть > 0`)
      return false
    }
  }

  return true
}



</script>

<template>
  <form @submit.prevent="submit" class="space-y-6 max-w-8xl mx-auto bg-white rounded-lg p-6 shadow-sm">
    <div v-for="(label, key) in fieldLabels" :key="key" class="space-y-1">
      <label class="block text-sm font-medium text-gray-700">{{ label }}</label>
      <input
        v-if="key !== 'notes'"
        v-model="estimate[key]"
        type="text"
        class="input-field"
      />
      <textarea
        v-else
        v-model="estimate.notes"
        rows="3"
        class="input-field resize-none"
      />
    </div>

    <div class="flex items-center gap-2">
      <input type="checkbox" v-model="estimate.vat_enabled" id="vat" class="form-checkbox h-4 w-4 text-blue-600" />
      <label for="vat" class="text-sm font-medium text-gray-700">Включить НДС</label>
    </div>

    <EstimateItemsEditor v-model="estimate.items" :vat-enabled="estimate.vat_enabled" />

    <div class="flex gap-2 pt-4 justify-end">
      <button
        type="submit"
        class="btn-primary"
      >
        Сохранить
      </button>
      <button
        type="button"
        @click="cancel"
        class="btn-danger"
      >
        Отмена
      </button>
    </div>
  </form>
</template>


<script>
export default {
  data() {
    return {
      fieldLabels: {
        name: 'Название сметы',
        client_name: 'Имя клиента',
        client_company: 'Компания клиента',
        client_contact: 'Контакты',
        responsible: 'Ответственный',
        notes: 'Заметки'
      }
    }
  }
}
</script>

<style scoped>
.input {
  @apply border p-2 w-full rounded mb-2;
}

.input-field {
  @apply w-full border border-gray-300 rounded-md px-4 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition;
}

.btn-primary {
  @apply inline-flex justify-center items-center px-4 py-2 rounded-md bg-blue-500 text-white hover:bg-blue-600 transition text-sm font-medium;
}

.btn-danger {
  @apply inline-flex justify-center items-center px-4 py-2 rounded-md bg-red-500 text-white hover:bg-red-600 transition text-sm font-medium;
}
</style>
