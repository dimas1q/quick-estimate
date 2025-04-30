# frontend/src/pages/TemplatesPage.vue
# Component for displaying and managing templates.
<template>
  <div class="space-y-6 px-24 py-8 max-w-6xl mx-auto">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold">Шаблоны смет</h1>
      <div class="flex items-center space-x-2 ">
        <input type="file" ref="fileInput" accept="application/json" @change="handleFile" class="hidden" />

      </div>
    </div>

    <div class="flex gap-6 items-start">
      <!-- Левая колонка — список шаблонов -->
      <div class="flex-1 space-y-4">

        <div v-for="template in store.templates" :key="template.id" class="border p-4 rounded shadow-sm space-y-1 py-4">
          <div class="font-semibold text-lg ">{{ template.name }}</div>
          <div class="text-sm text-gray-600 ">Описание: {{ template.description || '—' }}</div>

          <router-link :to="`/templates/${template.id}`"
            class="text-blue-600 text-sm hover:underline mt-2 inline-block">
            Подробнее →
          </router-link>
        </div>

        <div v-if="store.templates.length === 0" class="text-center text-gray-500 border p-4 rounded py-8">
          <p>Шаблоны смет отсутствуют.</p>
        </div>
      </div>

      <div class="w-64 space-y-4">
        <router-link to="/templates/create" class="btn-primary block w-full text-center">
          Создать шаблон
        </router-link>
        <button type="button" class="btn-primary block w-full text-center" @click="triggerFileInput">
          Импорт шаблона
        </button>
        <div class="border rounded p-4 shadow-sm space-y-4 text-center">
          <h2 class="font-semibold text-lg">Фильтр</h2>
          <div>
            <label class="text-sm text-gray-600">Название</label>
            <input v-model="filters.name" class="input-field mt-1" type="text" />
          </div>
          <div class="flex gap-2 pt-2">
            <button @click="applyFilters" class="btn-secondary w-full">Применить</button>
            <button @click="resetFilters" class="btn-secondary w-full">Сбросить</button>
          </div>
        </div>
      </div>
    </div>
  </div>

</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import { useTemplatesStore } from '@/store/templates'

const fileInput = ref(null)
const router = useRouter()
const toast = useToast()

const store = useTemplatesStore()

const filters = ref({
  name: ''
})

function applyFilters() {
  const query = {
    name: filters.value.name
  }
  store.fetchTemplates(query)
}

function resetFilters() {
  filters.value.name = ''
  store.fetchTemplates()
}

onMounted(() => {
  store.fetchTemplates()
})

function triggerFileInput() {
  fileInput.value.click()
}

async function handleFile(event) {
  const file = event.target.files[0]
  if (!file) return

  try {
    const text = await file.text()
    const json = JSON.parse(text)

    if ('id' in json) delete json.id
    json.items?.forEach(item => delete item.id)

    if (!isValidTemplate(json)) {
      return
    }

    store.importedTemplate = json
    router.push({ path: '/templates/create', state: { importedData: json } })

  } catch (e) {
    console.error(e)
    toast.error('Ошибка при чтении или разборе файла')
  }
}

function isValidTemplate(template) {
  if (typeof template !== 'object' || template === null) return false
  if (typeof template.name !== 'string' || !template.name.trim()) return false
  if (!Array.isArray(template.items)) return false

  for (const [i, item] of template.items.entries()) {
    if (!item || typeof item !== 'object') return false

    const { name, quantity, unit, unit_price } = item

    if (!name || typeof name !== 'string' || !name.trim()) {
      toast.error(`Ошибка в услуге №${i + 1}: отсутствует название`)
      return false
    }

    if (!['шт', 'час', 'день', 'м²', 'м'].includes(unit)) {
      toast.error(`Ошибка в услуге №${i + 1}: недопустимая единица измерения`)
      return false
    }

    if (typeof quantity !== 'number' || quantity <= 0) {
      toast.error(`Ошибка в услуге №${i + 1}: количество должно быть > 0`)
      return false
    }

    if (typeof unit_price !== 'number' || unit_price <= 0) {
      toast.error(`Ошибка в услуге №${i + 1}: цена должна быть > 0`)
      return false
    }
  }
  return true
}

</script>
