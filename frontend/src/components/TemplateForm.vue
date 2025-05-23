# frontend/src/components/TemplateForm.vue
<template>
  <form @submit.prevent="submit" class="space-y-8 border bg-gray rounded-2xl shadow-md p-6">
    <!-- 1. Основные поля: название и описание -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div>
        <label class="block text-sm font-semibold text-gray-700 mb-1">Название шаблона</label>
        <input v-model="template.name" type="text" placeholder="Введите название"
          class="w-full border border-gray-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300" />
      </div>
      <div>
        <label class="block text-sm font-semibold text-gray-700 mb-1">Описание</label>
        <textarea v-model="template.description" rows="1" placeholder="Краткое описание шаблона"
          class="w-full border border-gray-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none" />
      </div>
      <div class="md:col-span-2">
        <label class="block text-sm font-semibold text-gray-700 mb-1">Примечания</label>
        <textarea v-model="template.notes" rows="2" placeholder="Примечания к шаблону"
          class="w-full border border-gray-200 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300 resize-none" />
      </div>
    </div>

    <!-- 2. Редактор услуг -->
    <div>
      <EstimateItemsEditor v-model="template.items" :vat-enabled="false" :show-vat-summary="false" />
    </div>

    <!-- 3. Кнопки -->
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
import { reactive, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTemplatesStore } from '@/store/templates'
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

const store = useTemplatesStore()
const toast = useToast()
const router = useRouter()

const template = reactive({
  name: '',
  description: '',
  notes: '',
  items: []
})

onMounted(() => {
  if (store.importedTemplate) {
    template.name = store.importedTemplate.name || ''
    template.description = store.importedTemplate.description || ''
    template.notes = store.importedTemplate.notes || ''

    template.items.splice(0)
    for (const item of store.importedTemplate.items || []) {
      template.items.push({
        ...item,
        category_input: item.category || ''
      })
    }

    store.importedTemplate = null
  }
})

watch(() => props.initial, (value) => {
  if (value) {
    Object.assign(template, {
      name: value.name || '',
      description: value.description || '',
      notes: value.notes || '',
      items: (value.items || []).map(item => ({
        ...item,
        category_input: item.category || ''
      }))
    })
  }
}, { immediate: true })

async function submit() {
  if (!validateTemplate()) return

  let result
  if (props.mode === 'edit') {
    result = await store.updateTemplate(props.initial.id, template)
    emit('updated')
  } else {
    result = await store.createTemplate(template)
    toast.success('Шаблон создан')
    router.push(`/templates/${result.id}`)
  }
}

function cancel() {
  router.back()
}

function validateTemplate() {
  if (!template.name?.trim()) {
    toast.error("Название шаблона обязательно")
    return false
  }
  if (!template.items.length) {
    toast.error("Добавьте хотя бы одну услугу")
    return false
  }

  for (const [i, item] of template.items.entries()) {
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
