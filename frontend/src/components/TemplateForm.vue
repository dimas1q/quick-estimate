# frontend/src/components/TemplateForm.vue
<script setup>
import { reactive, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
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
  items: []
})

onMounted(() => {
  if (store.importedTemplate) {
    template.name = store.importedTemplate.name || ''
    template.description = store.importedTemplate.description || ''

    template.items.splice(0) // очищаем
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
      vat_enabled: value.vat_enabled ?? true,
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

<template>
  <form @submit.prevent="submit" class="space-y-6 max-w-8xl mx-auto bg-white rounded-lg p-6 shadow-sm">
    <div class="space-y-2">
      <label class="block text-sm font-medium text-gray-700">Название шаблона</label>
      <input v-model="template.name" type="text" class="input-field" />
    </div>

    <div class="space-y-2">
      <label class="block text-sm font-medium text-gray-700">Описание</label>
      <textarea v-model="template.description" rows="3" class="input-field resize-none" />
    </div>

    <EstimateItemsEditor v-model="template.items" :vat-enabled="false" :show-vat-summary="false"/>

    <div class="flex gap-2 pt-4 justify-end">
      <button type="submit" class="btn-primary">Сохранить</button>
      <button type="button" @click="cancel" class="btn-danger">Отмена</button>
    </div>
  </form>
</template>

