# frontend/src/pages/template/TemplateDetailsPage.vue
<template>
  <div class="py-8 max-w-7xl mx-auto">
    <div v-if="error" class="text-center text-red-500 text-lg font-medium mt-10">
      {{ error }}
    </div>

    <div v-if="template" class="space-y-6">
      <div class="flex justify-between items-center pb-2 mb-6">
        <div>
          <h1 class="text-3xl font-bold text-gray-800 dark:text-white">
            Шаблон: {{ template.name }}
          </h1>
        </div>

        <div class="flex space-x-2 items-center">
          <button @click="downloadJson" class="qe-btn-success flex items-center">
            <Download class="w-4 h-4 mr-1" />
            <span>Экспортировать</span>
          </button>
          <RouterLink :to="`/templates/${template.id}/edit`" class="qe-btn-warning flex items-center">
            <LucidePencilLine class="w-4 h-4 mr-1" />
            <span>Редактировать</span>
          </RouterLink>
          <button @click="confirmDelete" class="qe-btn-danger flex items-center">
            <LucideTrash2 class="w-4 h-4 mr-1" />
            <span>Удалить</span>
          </button>
        </div>
      </div>


      <div class="grid gap-3 text-sm">

        <!-- Блок данных — такой же стиль как у сметы -->
        <div class="grid gap-3 text-sm text-gray-800 dark:text-gray-200">
          <div
            class="grid grid-cols-2 gap-4 shadow-sm border dark:border-qe-black2 bg-white dark:bg-qe-black3 rounded-2xl p-6">
            <p><strong>Описание:</strong> {{ template.description || '—' }}</p>
          </div>
          <NotesBlock class="mt-4" :notes="notes" @add="addNote" @update="updateNote" @delete="deleteNote" />
        </div>

        <div class="mt-4">
          <div v-for="(groupItems, category) in groupedItems" :key="category"
            class="mb-6 border  p-6 rounded-2xl bg-white dark:border-qe-black2 dark:bg-qe-black3 shadow-sm">
            <div class="flex items-center justify-center gap-2 mb-3">
              <LucideFolder class="w-6 h-6 text-blue-500" />
              <h3 class="text-xl font-semibold text-gray-800 dark:text-white pb-1">{{ category }}</h3>
            </div>

            <div class="space-y-4">
              <div v-for="item in groupItems" :key="item.id"
                class="bg-white dark:bg-qe-black3 border border-gray-100 dark:border-qe-black2 rounded-xl shadow p-4 transition flex flex-col">
                <div class="flex flex-wrap justify-between items-center gap-2">
                  <div>
                    <div class="text-base font-semibold text-gray-900 dark:text-white flex items-center">
                      {{ item.name }}
                    </div>
                    <div class="text-sm text-gray-500 dark:text-gray-300">
                      {{ item.description }}
                    </div>
                  </div>
                  <div class="text-sm text-gray-500 dark:text-gray-300 whitespace-nowrap">
                    {{ item.quantity }} {{ item.unit }}
                  </div>
                </div>
                <div v-if="template.use_internal_price" class="flex justify-between text-sm text-gray-600 dark:text-gray-300 mt-2">
                  <span>Внутр. цена за единицу:</span>
                  <span>{{ formatCurrency(item.internal_price) }}</span>
                </div>
                <div class="flex justify-between text-sm text-gray-600 dark:text-gray-300">
                  <span>Внешн. цена за единицу:</span>
                  <span>{{ formatCurrency(item.external_price) }}</span>
                </div>
                <div v-if="template.use_internal_price" class="flex justify-between font-semibold text-sm text-gray-900 dark:text-white">
                  <span>Итог (внутр.):</span>
                  <span>{{ formatCurrency(getItemInternal(item)) }}</span>
                </div>
                <div class="flex justify-between font-semibold text-sm text-gray-900 dark:text-white">
                  <span>Итог (внешн.):</span>
                  <span>{{ formatCurrency(getItemExternal(item)) }}</span>
                </div>
              </div>
            </div>
            <!-- Итоги по категории -->
            <div class="flex gap-3 justify-center mt-5">
              <div v-if="template.use_internal_price"
                class="flex items-center gap-1 bg-gray-50 dark:bg-qe-black2 rounded-xl px-3 py-1 shadow border border-gray-100 dark:border-qe-black2">
                <LucidePiggyBank class="w-4 h-4 text-green-500" />
                <span class="text-xs text-gray-600 dark:text-gray-300">Итог по категории
                  (внутр.):</span>
                <span class="font-semibold text-sm text-green-800 dark:text-green-300">{{
                  formatCurrency(getGroupInternal(groupItems)) }}</span>
              </div>
              <div
                class="flex items-center gap-1 bg-gray-50 dark:bg-qe-black2 rounded-xl px-3 py-1 shadow border border-gray-100 dark:border-qe-black2">
                <LucideReceipt class="w-4 h-4 text-blue-500" />
                <span class="text-xs text-gray-600 dark:text-gray-300">Итог по категории
                  (внешн.):</span>
                <span class="font-semibold text-sm text-blue-800 dark:text-blue-300">{{
                  formatCurrency(getGroupExternal(groupItems)) }}</span>
              </div>
            </div>

          </div>

        </div>
      </div>
    </div>

    <QeModal v-model="showConfirm" @confirm="deleteTemplate">
      Вы уверены, что хотите удалить данный шаблон?
      <template #confirm>Удалить</template>
      <template #cancel>Отмена</template>
    </QeModal>
  </div>
</template>

<script setup>
import { onMounted, ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTemplatesStore } from '@/store/templates'
import { useNotesStore } from '@/store/notes'
import { useToast } from 'vue-toastification'

import QeModal from '@/components/QeModal.vue'
import NotesBlock from '@/components/NotesBlock.vue'

import {
  LucidePiggyBank,
  LucideReceipt,
  LucideTrash2,
  Download,
  LucidePencilLine,
  LucideFolder

} from 'lucide-vue-next'


const route = useRoute()
const router = useRouter()
const store = useTemplatesStore()
const notesStore = useNotesStore()
const toast = useToast()

const template = ref(null)
const error = ref(null)
const notes = ref([])

onMounted(async () => {
  try {
    template.value = await store.getTemplateById(route.params.id)
    notes.value = await notesStore.fetchTemplateNotes(route.params.id)
  } catch (e) {
    if (e.response?.status === 403) {
      error.value = '🚫 У вас нет доступа к этому шаблону.'
    } else if (e.response?.status === 404) {
      error.value = '❌ Шаблон не найден.'
    } else {
      error.value = '⚠️ Ошибка при загрузке шаблона.'
    }
  }
})

watch(() => route.params.id, async () => {
  template.value = await store.getTemplateById(route.params.id)
  notes.value = await notesStore.fetchTemplateNotes(route.params.id)
})



const groupedItems = computed(() => {
  const groups = {}
  for (const item of template.value?.items || []) {
    const category = item.category?.trim() || 'Без категории'
    if (!groups[category]) groups[category] = []
    groups[category].push(item)
  }
  return groups
})

function getItemInternal(item) {
  return item.quantity * item.internal_price;
}

function getItemExternal(item) {
  return item.quantity * item.external_price;
}

function getGroupInternal(group) {
  return group.reduce((sum, item) => sum + getItemInternal(item), 0)
}
function getGroupExternal(group) {
  return group.reduce((sum, item) => sum + getItemExternal(item), 0)
}

const totalInternal = computed(() =>
  template.value?.use_internal_price ? template.value.items?.reduce((sum, item) => sum + getItemInternal(item), 0) || 0 : 0
)
const totalExternal = computed(() => template.value?.items?.reduce((sum, item) => sum + getItemExternal(item), 0) || 0)

const totalDiff = computed(() => template.value?.use_internal_price ? totalExternal.value - totalInternal.value : 0)

async function addNote(text) {
  const n = await notesStore.addTemplateNote(route.params.id, text)
  notes.value.unshift(n)
}

async function updateNote(payload) {
  const n = await notesStore.updateNote(payload.id, payload.text)
  const idx = notes.value.findIndex(n => n.id === payload.id)
  if (idx !== -1) notes.value[idx] = n
}

async function deleteNote(id) {
  await notesStore.deleteNote(id)
  notes.value = notes.value.filter(n => n.id !== id)
}

function formatCurrency(val) {
  return `${val.toFixed(2)} ₽`
}

const showConfirm = ref(false)

function confirmDelete() {
  showConfirm.value = true
}

async function deleteTemplate() {
  await store.deleteTemplate(template.value.id)
  toast.success('Шаблон удалён')
  router.push('/templates')
}

async function downloadJson() {
  await store.exportTemplate(template.value.id)
}
</script>