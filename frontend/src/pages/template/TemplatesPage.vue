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
import { useToast } from 'vue-toastification'
import { useTemplatesStore } from '@/store/templates'
import QePagination from '@/components/QePagination.vue'

const fileInput = ref(null)
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
    const preview = await store.previewTemplateImport(json)

    if (!preview.valid) {
      const topErrors = (preview.errors || []).slice(0, 5).map(
        (err) => `${err.path}: ${err.message}`
      )
      toast.error(topErrors[0] || 'Шаблон не прошел валидацию')
      if (topErrors.length > 1) {
        console.error('Template import validation errors:', topErrors)
      }
      return
    }

    const summary = preview.summary
    const confirmMessage = [
      `Импортировать шаблон «${summary?.name || 'Без названия'}»?`,
      `Позиции: ${summary?.item_count ?? 0}`,
      `Категории: ${summary?.category_count ?? 0}`,
      summary?.name_exists ? 'Внимание: шаблон с таким названием уже существует.' : ''
    ].filter(Boolean).join('\n')

    if (!confirm(confirmMessage)) return

    await store.importTemplate(json)
    toast.success('Шаблон успешно импортирован')
    await store.fetchTemplates({ ...currentFilters.value, page: currentPage.value, limit: perPage })

  } catch (e) {
    console.error(e)
    const detail = e?.response?.data?.detail
    if (detail?.errors?.length) {
      const firstError = detail.errors[0]
      toast.error(`${firstError.path}: ${firstError.message}`)
    } else {
      toast.error('Ошибка при чтении или импорте файла')
    }
  } finally {
    event.target.value = ''
  }
}
</script>
