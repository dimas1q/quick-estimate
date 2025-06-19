# frontend/src/components/TemplateForm.vue
<template>
  <form @submit.prevent="submit"
    class="space-y-8 border bg-white dark:bg-qe-black3 dark:border-qe-black2 rounded-2xl shadow-md p-6">
    <!-- 1. Основные поля: название и описание -->
  <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div>
        <label class="block text-sm font-semibold text-gray-700 dark:text-white mb-1">Название шаблона</label>
        <input v-model="template.name" type="text" placeholder="Введите название" class="w-full qe-input" />
  </div>

    <div>
      <label class="flex items-center gap-2 cursor-pointer select-none">
        <input type="checkbox" v-model="template.use_internal_price" class="h-4 w-4 accent-blue-600 rounded border-gray-300" />
        <span class="text-sm font-semibold text-gray-800 dark:text-white">Внутренняя цена</span>
      </label>
    </div>
      <div>
        <label class="block text-sm font-semibold text-gray-700 dark:text-white mb-1">Описание</label>
        <input v-model="template.description" placeholder="Краткое описание шаблона" class="w-full qe-input" />
      </div>
    </div>

    <!-- 2. Редактор услуг -->
    <div>
      <EstimateItemsEditor v-model="template.items" :vat-enabled="false" :show-summary="false" :use-internal-price="template.use_internal_price" />
    </div>

    <!-- 3. Кнопки -->
    <div class="flex justify-end space-x-2">
      <button type="button" @click="cancel" class="qe-btn-danger">
        Отмена
      </button>
      <button type="submit" class="qe-btn">
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
  items: [],
  use_internal_price: true
})

onMounted(() => {
  if (store.importedTemplate) {
    template.name = store.importedTemplate.name || ''
    template.description = store.importedTemplate.description || ''
    template.use_internal_price = store.importedTemplate.use_internal_price ?? true

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

function flattenItems(categories) {
  // Возвращает плоский массив с подставленной категорией
  return categories.flatMap(cat =>
    cat.items.map(item => ({ ...item, category: cat.name }))
  )
}

watch(() => props.initial, (value) => {
  if (value) {
    Object.assign(template, {
      name: value.name || '',
      description: value.description || '',
      use_internal_price: value.use_internal_price ?? true,
      items: (value.items || []).map(item => ({
        ...item,
        category_input: item.category || ''
      }))
    })
  }
}, { immediate: true })

async function submit() {

  if (template.items.length && template.items[0]?.items) {
    template.items = flattenItems(template.items)
  }
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
    if (template.use_internal_price && (!item.internal_price || item.internal_price <= 0)) {
      toast.error(`Услуга ${item.name}: внутренняя цена должна быть > 0`)
      return false
    }
    if (!item.external_price || item.external_price <= 0) {
      toast.error(`Услуга ${item.name}: внешняя цена должна быть > 0`)
      return false
    }
  }

  return true
}
</script>
