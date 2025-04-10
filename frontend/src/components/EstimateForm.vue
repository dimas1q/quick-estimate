<script setup>
import { reactive, watch, toRefs } from 'vue'
import { useRouter } from 'vue-router'
import { useEstimatesStore } from '@/store/estimates'
import EstimateItemsEditor from '@/components/EstimateItemsEditor.vue'
import { useToast } from 'vue-toastification'

const props = defineProps({
  initial: Object
})
const emit = defineEmits(['updated'])

const store = useEstimatesStore()
const toast = useToast()
const router = useRouter()

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
      name: value.name || '',
      client_name: value.client_name || '',
      client_company: value.client_company || '',
      client_contact: value.client_contact || '',
      responsible: value.responsible || '',
      notes: value.notes || '',
      items: value.items?.map(item => ({
        ...item,
        category_input: item.category || ''
      })) || [],
      vat_enabled: value.vat_enabled ?? true
    })
  }
}, { immediate: true })

async function submit() {
  let result
  if (props.initial?.id) {
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

</script>

<template>
  <form @submit.prevent="submit" class="space-y-4">
    <div v-for="(label, key) in fieldLabels" :key="key">
      <label class="block font-semibold mb-1">{{ label }}</label>
      <input v-if="key !== 'notes'" v-model="estimate[key]" class="input" />
      <textarea v-else v-model="estimate.notes" class="input" />
    </div>

    <div class="flex items-center gap-2">
      <input type="checkbox" v-model="estimate.vat_enabled" id="vat" />
      <label for="vat" class="text-sm">Включить НДС</label>
    </div>

    <EstimateItemsEditor v-model="estimate.items" :vat-enabled="estimate.vat_enabled" />

    <div class="flex gap-4 pt-4">
      <button type="submit" class="bg-blue-500 text-white px-4 py-2 rounded">Сохранить</button>
      <button type="button" @click="cancel" class="bg-gray-200 text-black px-4 py-2 rounded">Отмена</button>
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
</style>
