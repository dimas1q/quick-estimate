<template>
  <div class="flex flex-col items-center from-gray-50 via-white to-gray-100 px-2 py-10">
    <!-- Хедер и бар фильтров -->
    <div class="w-full max-w-5xl flex flex-col gap-4 mb-8">
      <div class="flex items-center justify-between mb-2">
        <h2 class="text-2xl font-bold">Шаблоны смет</h2>
        <div class="flex gap-2">
          <router-link to="/templates/create" class="qe-btn">Создать шаблон</router-link>
          <button @click="triggerFileInput" class="qe-btn">Импорт шаблона</button>
          <input type="file" ref="fileInput" accept="application/json" @change="handleFile" class="hidden" />
        </div>
      </div>
      <div class="flex gap-2">
        <input v-model="filters.name" class="qe-input flex-1" type="text" autocomplete="off"
          placeholder="Название шаблона" />
        <button @click="applyFilters" class="qe-btn min-w-[100px]">Найти</button>
        <button @click="resetFilters" class="qe-btn-secondary min-w-[100px]">Сброс</button>
      </div>
    </div>

    <!-- Список шаблонов -->
    <div class="w-full max-w-5xl">
      <div v-if="isLoading" class="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div v-for="n in 5" :key="n" class="rounded-2xl bg-white/60 shadow animate-pulse p-6 h-24" />
      </div>
      <template v-else>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div v-for="template in store.templates" :key="template.id"
            class="flex items-center border border-gray-200
 bg-white rounded-2xl shadow-sm hover:shadow-lg p-5 transition-all border border-gray-100 dark:bg-qe-black3 dark:border-qe-black2">
            <div class="flex flex-col flex-1 items-start justify-center">
              <router-link :to="`/templates/${template.id}`"
                class="text-lg font-semibold text-left hover:text-blue-600">{{ template.name }}
              </router-link>
              <div class="text-gray-500 text-sm text-left mb-1">
                {{ template.description || '—' }}
              </div>
            </div>
          </div>
        </div>
        <div v-if="store.templates.length === 0"
          class="text-center text-gray-400 border border-gray-200 dark:border-qe-black2 p-6 rounded-2xl bg-white/70 dark:bg-qe-black2/80 mt-4">
          Шаблоны смет отсутствуют.
        </div>
        <QePagination :total="totalTemplates" :per-page="perPage" :page="currentPage" @update:page="changePage"
          class="mt-6" />
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'
import { useTemplatesStore } from '@/store/templates'
import QePagination from '@/components/QePagination.vue'

import { FileDown, Plus } from 'lucide-vue-next'

const fileInput = ref(null)
const router = useRouter()
const toast = useToast()
const isLoading = ref(true)

const store = useTemplatesStore()

const filters = ref({
  name: ''
})

const perPage = 5
const currentPage = ref(1)
const currentFilters = ref({})
const totalTemplates = computed(() => store.total)

onMounted(async () => {
  isLoading.value = true
  await store.fetchTemplates({ page: currentPage.value, limit: perPage })
  currentFilters.value = {}
  isLoading.value = false
})

async function applyFilters() {
  isLoading.value = true
  const query = { name: filters.value.name }
  currentFilters.value = query
  currentPage.value = 1
  await store.fetchTemplates({ ...query, page: currentPage.value, limit: perPage })
  isLoading.value = false
}

async function resetFilters() {
  isLoading.value = true
  filters.value.name = ''
  currentFilters.value = {}
  currentPage.value = 1
  await store.fetchTemplates({ page: currentPage.value, limit: perPage })
  isLoading.value = false
}

async function changePage(p) {
  currentPage.value = p
  await store.fetchTemplates({ ...currentFilters.value, page: p, limit: perPage })
  window.scrollTo({ top: 0, behavior: 'smooth' })
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

    store.setImportedTemplate(json)
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

    const { name, quantity, unit, internal_price, external_price } = item

    if (!name || typeof name !== 'string' || !name.trim()) {
      toast.error(`Ошибка в услуге №${i + 1}: отсутствует название`)
      return false
    }

    if (!['шт', 'час', 'день', 'м²', 'м'].includes(unit)) {
      toast.error(`Ошибка в услуге ${item.name}: недопустимая единица измерения`)
      return false
    }

    if (typeof quantity !== 'number' || quantity <= 0) {
      toast.error(`Ошибка в услуге ${item.name}: количество должно быть > 0`)
      return false
    }

    if (typeof internal_price !== 'number' || internal_price <= 0) {
      toast.error(`Ошибка в услуге ${item.name}: внутренняя цена должна быть > 0`)
      return false
    }

    if (typeof external_price !== 'number' || external_price <= 0) {
      toast.error(`Ошибка в услуге ${item.name}: внешняя цена должна быть > 0`)
      return false
    }
  }
  return true
}
</script>
