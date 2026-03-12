<template>
  <div class="flex flex-col items-center from-gray-50 via-white to-gray-100 px-2 py-10">
    <!-- Хедер и бар фильтров -->
    <div class="w-full max-w-6xl flex flex-col gap-4 mb-8">
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
    <div class="w-full max-w-6xl">
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

    <transition name="modal-fade">
      <div v-if="showImportPreviewModal" class="fixed inset-0 z-50 flex items-center justify-center px-4">
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="closeImportPreviewModal" />
        <div
          class="relative z-10 w-full max-w-2xl rounded-2xl bg-white dark:bg-qe-black2 shadow-2xl border border-gray-200 dark:border-qe-black3 p-6">
          <h3 class="text-xl font-bold text-gray-800 dark:text-white mb-3">Предпросмотр импорта шаблона</h3>
          <div v-if="importPreview?.valid" class="space-y-4">
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div class="rounded-lg border border-gray-200 dark:border-qe-black3 px-3 py-2">
                <p class="text-xs text-gray-500">Шаблон</p>
                <p class="font-semibold text-gray-800 dark:text-white">{{ importPreview?.summary?.name || '—' }}</p>
              </div>
              <div class="rounded-lg border border-gray-200 dark:border-qe-black3 px-3 py-2">
                <p class="text-xs text-gray-500">Позиции</p>
                <p class="font-semibold text-gray-800 dark:text-white">{{ importPreview?.summary?.item_count ?? 0 }}</p>
              </div>
              <div class="rounded-lg border border-gray-200 dark:border-qe-black3 px-3 py-2">
                <p class="text-xs text-gray-500">Категории</p>
                <p class="font-semibold text-gray-800 dark:text-white">{{ importPreview?.summary?.category_count ?? 0 }}</p>
              </div>
            </div>
            <div v-if="importPreview?.summary?.categories?.length"
              class="rounded-lg border border-gray-200 dark:border-qe-black3 px-3 py-2">
              <p class="text-xs text-gray-500 mb-1">Категории</p>
              <div class="flex flex-wrap gap-2">
                <span v-for="category in importPreview.summary.categories" :key="category"
                  class="inline-flex rounded-full bg-blue-50 text-blue-700 text-xs px-2 py-1 dark:bg-blue-900/30 dark:text-blue-300">
                  {{ category }}
                </span>
              </div>
            </div>
            <div v-if="importPreview?.warnings?.length"
              class="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 dark:bg-amber-900/20 dark:border-amber-900/40">
              <p class="text-sm font-semibold text-amber-700 dark:text-amber-300 mb-1">Предупреждения</p>
              <ul class="list-disc pl-5 space-y-1 text-sm text-amber-700 dark:text-amber-300">
                <li v-for="(warning, idx) in importPreview.warnings" :key="idx">{{ warning }}</li>
              </ul>
            </div>
          </div>
          <div v-else class="space-y-3">
            <div class="rounded-lg border border-red-200 bg-red-50 px-3 py-2 dark:bg-red-900/20 dark:border-red-900/40">
              <p class="text-sm font-semibold text-red-700 dark:text-red-300 mb-1">Ошибки валидации</p>
              <ul class="space-y-1 text-sm text-red-700 dark:text-red-300 max-h-64 overflow-auto pr-2">
                <li v-for="(error, idx) in importPreview?.errors || []" :key="idx">
                  <span class="font-semibold">{{ error.path }}:</span> {{ error.message }}
                </li>
              </ul>
            </div>
            <div v-if="importPreview?.warnings?.length"
              class="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 dark:bg-amber-900/20 dark:border-amber-900/40">
              <p class="text-sm font-semibold text-amber-700 dark:text-amber-300 mb-1">Предупреждения</p>
              <ul class="list-disc pl-5 space-y-1 text-sm text-amber-700 dark:text-amber-300">
                <li v-for="(warning, idx) in importPreview.warnings" :key="idx">{{ warning }}</li>
              </ul>
            </div>
          </div>
          <div class="mt-6 flex justify-end gap-3">
            <button class="qe-btn-secondary" @click="closeImportPreviewModal" :disabled="isImporting">
              Закрыть
            </button>
            <button v-if="importPreview?.valid" class="qe-btn" @click="confirmImportTemplate" :disabled="isImporting">
              {{ isImporting ? 'Импорт...' : 'Импортировать' }}
            </button>
          </div>
        </div>
      </div>
    </transition>
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
const showImportPreviewModal = ref(false)
const importPreview = ref(null)
const pendingImportPayload = ref(null)
const isImporting = ref(false)

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
    importPreview.value = preview
    pendingImportPayload.value = json
    showImportPreviewModal.value = true

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

function closeImportPreviewModal() {
  if (isImporting.value) return
  showImportPreviewModal.value = false
}

async function confirmImportTemplate() {
  if (!importPreview.value?.valid || !pendingImportPayload.value || isImporting.value) return
  try {
    isImporting.value = true
    await store.importTemplate(pendingImportPayload.value)
    toast.success('Шаблон успешно импортирован')
    await store.fetchTemplates({ ...currentFilters.value, page: currentPage.value, limit: perPage })
    showImportPreviewModal.value = false
  } catch (e) {
    console.error(e)
    const detail = e?.response?.data?.detail
    if (detail?.errors?.length) {
      const firstError = detail.errors[0]
      toast.error(`${firstError.path}: ${firstError.message}`)
    } else {
      toast.error('Ошибка импорта шаблона')
    }
  } finally {
    isImporting.value = false
  }
}
</script>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
</style>
