<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import { useTemplatesStore } from '@/store/templates'

const fileInput = ref(null)
const router = useRouter()
const toast = useToast()
const isLoading = ref(true)

const store = useTemplatesStore()

const filters = ref({
  name: ''
})

onMounted(async () => {
  isLoading.value = true
  await store.fetchTemplates()
  isLoading.value = false
})

async function applyFilters() {
  isLoading.value = true
  const query = { name: filters.value.name }
  await store.fetchTemplates(query)
  isLoading.value = false
}

async function resetFilters() {
  isLoading.value = true
  filters.value.name = ''
  await store.fetchTemplates()
  isLoading.value = false
}

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

    if (!isValidTemplate(json)) return

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

<template>
  <div class="space-y-6 px-6 py-8 max-w-5xl mx-auto">
    <!-- Шапка -->
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Шаблоны смет</h1>
      <input type="file" ref="fileInput" accept="application/json" @change="handleFile" class="hidden" />
    </div>
    <div class="flex gap-6 items-start">
      <!-- Левая колонка — список шаблонов -->
      <div class="flex-1 space-y-4">
        <div v-if="isLoading" class="flex flex-col gap-5">
          <div v-for="n in 3" :key="n"
            class="border border-gray-200 dark:border-gray-800 rounded-xl shadow-sm p-5 bg-white dark:bg-gray-900 animate-pulse flex flex-col gap-3">
            <div class="h-6 bg-gray-200 dark:bg-gray-800 rounded w-2/3 mb-2"></div>
            <div class="h-4 bg-gray-100 dark:bg-gray-700 rounded w-1/3 mb-2"></div>
            <div class="h-4 bg-gray-100 dark:bg-gray-700 rounded w-1/2"></div>
          </div>
        </div>
        <template v-else>
          <div v-for="template in store.templates" :key="template.id"
            class="border border-gray-200 dark:border-qe-black2 rounded-xl shadow-sm p-5 bg-white dark:bg-qe-black3 transition hover:shadow-md flex flex-col gap-1">
            <div class="font-semibold text-lg">{{ template.name }}</div>
            <div class="text-sm text-gray-600 dark:text-gray-400">Описание: {{ template.description || '—' }}</div>
            <router-link :to="`/templates/${template.id}`"
              class="text-blue-600 dark:text-blue-400 text-sm hover:underline mt-2 inline-block">
              Подробнее →
            </router-link>
          </div>
          <div v-if="store.templates.length === 0"
            class="text-center text-gray-500 border border-gray-200 dark:border-gray-800 p-4 rounded-2xl py-8">
            <p>Шаблоны смет отсутствуют.</p>
          </div>
        </template>
      </div>
      <!-- Правая панель: кнопки и фильтры -->
      <div class="w-72 space-y-4">
        <router-link to="/templates/create" class="qe-btn block w-full text-center">
          Создать шаблон
        </router-link>
        <button type="button" class="qe-btn block w-full text-center" @click="triggerFileInput">
          Импорт шаблона
        </button>
        <div
          class="border border-gray-200 dark:border-qe-black2 rounded-xl p-4 shadow-sm space-y-4 text-center bg-white dark:bg-qe-black3">
          <h2 class="font-semibold text-lg">Фильтр</h2>
          <div>
            <label class="text-sm text-gray-600 dark:text-gray-300">Название</label>
            <input v-model="filters.name" class="qe-input w-full mt-2" type="text" placeholder="Название шаблона" />
          </div>
          <div class="flex gap-2 pt-2">
            <button @click="applyFilters" class="qe-btn w-full">Применить</button>
            <button @click="resetFilters" class="qe-btn-secondary w-full">Сбросить</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
