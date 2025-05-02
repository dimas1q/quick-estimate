# frontend/src/components/EstimateForm.vue
<template>
  <form @submit.prevent="submit" class="space-y-6 max-w-8xl mx-auto bg-white rounded-lg p-6 shadow-sm">
    <div v-for="(label, key) in fieldLabels" :key="key" class="space-y-2">
      <label class="block text-sm font-medium text-gray-700">{{ label }}</label>
      <input v-if="key !== 'notes'" v-model="estimate[key]" type="text" class="input-field" />
      <textarea v-else v-model="estimate.notes" rows="3" class="input-field resize-none" />
    </div>

    <div class="space-y-2">
      <label class="block text-sm font-medium text-gray-700">Клиент</label>
      <select v-model="estimate.client_id" class="input-field">
        <option :value="null">— Выберите клиента —</option>
        <option v-for="c in clients" :key="c.id" :value="c.id">
          {{ c.name }} {{ c.company ? `(${c.company})` : '' }}
        </option>
      </select>
    </div>


    <div class="flex items-center gap-2">
      <input type="checkbox" v-model="estimate.vat_enabled" id="vat" class="form-checkbox h-4 w-4 text-blue-600" />
      <label for="vat" class="text-sm font-medium text-gray-700">Включить НДС</label>
    </div>

    <EstimateItemsEditor v-model="estimate.items" :vat-enabled="estimate.vat_enabled" />

    <div class="flex gap-2 pt-4 justify-end">
      <button type="submit" class="btn-primary">
        Сохранить
      </button>
      <button type="button" @click="cancel" class="btn-danger">
        Отмена
      </button>
    </div>
  </form>
</template>

<script setup>
import { reactive, watch, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useEstimatesStore } from '@/store/estimates'
import { useClientsStore } from '@/store/clients'
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
const clientsStore = useClientsStore()
const toast = useToast()
const router = useRouter()

const estimate = reactive({
  name: '',
  client_id: null,
  responsible: '',
  notes: '',
  items: []
})

const clients = computed(() => clientsStore.clients)

onMounted(async () => {
  await clientsStore.fetchClients()
  if (store.importedEstimate) {
    estimate.name = store.importedEstimate.name || ''
    estimate.client_id = store.importedEstimate.client?.id || null
    estimate.responsible = store.importedEstimate.responsible || ''
    estimate.notes = store.importedEstimate.notes || ''
    estimate.vat_enabled = store.importedEstimate.vat_enabled ?? true

    estimate.items.splice(0)
    for (const item of store.importedEstimate.items || []) {
      estimate.items.push({
        ...item,
        category_input: item.category || ''
      })
    }

    store.importedEstimate = null
  }
})



watch(() => props.initial, (value) => {
  if (value) {
    Object.assign(estimate, {
      name: props.mode === 'copy' ? `Копия: ${value.name}` : value.name,
      client_id: value.client?.id || null,
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




<script>
export default {
  data() {
    return {
      fieldLabels: {
        name: 'Название сметы',
        responsible: 'Ответственный',
        notes: 'Заметки'
      }
    }
  }
}
</script>