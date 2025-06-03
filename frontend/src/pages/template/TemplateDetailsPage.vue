# frontend/src/pages/template/TemplateDetailsPage.vue
<template>
  <div class="py-8 max-w-6xl mx-auto">
    <div v-if="error" class="text-center text-red-500 text-lg font-medium mt-10">
      {{ error }}
    </div>

    <div v-if="template" class="space-y-6">
      <div class="flex justify-between pb-4 items-center">
        <h1 class="text-3xl font-bold">Шаблон: {{ template.name }}</h1>

        <div class="space-x-2">
          <button @click="downloadJson"
            class="inline-flex justify-center items-center px-4 py-2 rounded-md bg-green-600 text-white hover:bg-green-700 transition-all text-sm font-medium">
            Экспортировать
          </button>
          <router-link :to="`/templates/${template.id}/edit`"
            class="inline-flex justify-center items-center px-4 py-2 rounded-md bg-yellow-500 text-white hover:bg-yellow-600 transition-all text-sm font-medium">
            Редактировать
          </router-link>
          <button @click="confirmDelete" class="qe-btn-danger">
            Удалить
          </button>
        </div>
      </div>


      <div class="grid gap-3 text-sm">

        <!-- Блок данных — такой же стиль как у сметы -->
        <div class="grid gap-3 text-sm text-gray-800 dark:text-gray-200">
          <div
            class="grid grid-cols-2 gap-4 shadow-sm border dark:border-qe-black2 bg-white dark:bg-qe-black rounded-2xl p-6">
            <p><strong>Описание:</strong> {{ template.description || '—' }}</p>
            <p><strong>Примечания:</strong> {{ template.notes || '—' }}</p>
          </div>
        </div>

        <div class="border bg-white dark:bg-qe-black dark:border-qe-black2 rounded-2xl p-6 mt-6 shadow-sm">
          <div v-for="(groupItems, category) in groupedItems" :key="category" class="mb-4">
            <h3 class="text-lg font-semibold text-gray-800 dark:text-white mb-4 text-center pb-1 ">{{
              category }}
            </h3>

            <div class="space-y-4 ">
              <div v-for="(row, rowIndex) in chunkArray(groupItems, 3)" :key="rowIndex" class="flex gap-4">
                <div v-for="item in row" :key="item.id"
                  :class="`flex-1 ${row.length === 1 ? 'max-w-full' : row.length === 2 ? 'max-w-1/2' : 'max-w-1/3'}`"
                  class="bg-white border border-gray-200 dark:bg-qe-black dark:border-qe-black2 rounded-xl shadow-sm p-4 hover:shadow-md transition-shadow duration-200">
                  <div class="flex justify-between items-start mb-2">
                    <div>
                      <p class="text-base font-semibold text-gray-900 dark:text-white">{{
                        item.name }}</p>
                      <p class="text-sm text-gray-600 dark:text-white">{{ item.description }}
                      </p>
                    </div>
                    <div class="text-sm text-gray-500 dark:text-white text-right whitespace-nowrap">
                      {{ item.quantity }} {{ item.unit }}
                    </div>
                  </div>
                  <div class="flex justify-between text-sm text-gray-700 dark:text-white pt-2">
                    <span>Внутр. цена за единицу:</span>
                    <span>{{ formatCurrency(item.internal_price) }}</span>
                  </div>
                  <div class="flex justify-between text-sm text-gray-700 dark:text-white">
                    <span>Внешн. цена за единицу:</span>
                    <span>{{ formatCurrency(item.external_price) }}</span>
                  </div>
                  <div class="flex justify-between font-semibold text-sm dark:text-white text-gray-900">
                    <span>Итог (внутр.):</span>
                    <span>{{ formatCurrency(getItemInternal(item)) }}</span>
                  </div>
                  <div class="flex justify-between font-semibold text-sm  dark:text-white text-gray-900">
                    <span>Итог (внешн.):</span>
                    <span>{{ formatCurrency(getItemExternal(item)) }}</span>
                  </div>

                </div>
              </div>
            </div>

            <div class="text-right font-semibold text-base text-gray-900 dark:text-white mt-4">
              <div>Итог по категории (внутр.): {{ formatCurrency(getGroupInternal(groupItems)) }}
              </div>
              <div>Итог по категории (внешн.): {{ formatCurrency(getGroupExternal(groupItems)) }}
              </div>
            </div>
          </div>


          <div v-if="template?.items?.length" class="pt-6">
            <p class="text-right font-semibold text-lg pt-4 border-t dark:border-qe-black2">
              Общая сумма (внутр.): {{ formatCurrency(totalInternal) }}
            </p>
            <p class="text-right font-semibold text-lg">
              Общая сумма (внешн.): {{ formatCurrency(totalExternal) }}
            </p>
            <p class="text-right font-semibold text-lg">
              Разница: {{ formatCurrency(totalDiff) }}
            </p>
          </div>

        </div>
      </div>
    </div>

    <QeModal v-model="showConfirm" @confirm="deleteTemplate">
      Вы уверены, что хотите удалить данный шаблон?
      <template #confirm>Да, удалить</template>
      <template #cancel>Отмена</template>
    </QeModal>
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTemplatesStore } from '@/store/templates'
import { useToast } from 'vue-toastification'

import QeModal from '@/components/QeModal.vue'


const route = useRoute()
const router = useRouter()
const store = useTemplatesStore()
const toast = useToast()

const template = ref(null)
const error = ref(null)

onMounted(async () => {
  try {
    template.value = await store.getTemplateById(route.params.id)
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

function chunkArray(array) {
  const len = array.length
  let chunkSize = 3

  if (len === 1) {
    chunkSize = 1
  } else if (len % 2 === 0) {
    chunkSize = 2
  }

  const chunks = []
  for (let i = 0; i < len; i += chunkSize) {
    chunks.push(array.slice(i, i + chunkSize))
  }
  return chunks
}


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

const totalInternal = computed(() => template.value?.items?.reduce((sum, item) => sum + getItemInternal(item), 0) || 0)
const totalExternal = computed(() => template.value?.items?.reduce((sum, item) => sum + getItemExternal(item), 0) || 0)

const totalDiff = computed(() => totalExternal.value - totalInternal.value)

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