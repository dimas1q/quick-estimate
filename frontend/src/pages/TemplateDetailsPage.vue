<template>
  <div class="px-16 py-8 max-w-6xl mx-auto">
    <div v-if="error" class="text-center text-red-500 text-lg font-medium mt-10">
      {{ error }}
    </div>

    <div v-if="template" class="space-y-6">
      <div class="flex justify-between items-center">
        <h1 class="text-2xl font-bold">{{ template.name }}</h1>

        <div class="space-x-2">

          <router-link :to="`/templates/${template.id}/edit`"
            class="inline-flex justify-center items-center px-4 py-2 rounded-md bg-yellow-500 text-white hover:bg-yellow-600 transition-all text-sm font-medium">
            ✏️ Редактировать
          </router-link>
          <button @click="downloadJson"
            class="inline-flex justify-center items-center px-4 py-2 rounded-md bg-green-600 text-white hover:bg-green-700 transition-all text-sm font-medium">
            📥 Экспортировать
          </button>
          <button @click="confirmDelete"
            class="btn-danger">
            🗑️ Удалить
          </button>
        </div>
      </div>


      <div class="grid gap-3 text-sm text-gray-800">
        <p><strong>Описание:</strong> {{ template.description || '—' }}</p>
      </div>

      <div v-if="template.items?.length">
        <ul class="space-y-2">
          <h2 class="font-semibold text-lg mt-6">Услуги</h2>

          <div v-for="(groupItems, category) in groupedItems" :key="category" class="mb-6 space-y-3">
            <h3 class="text-md font-semibold text-gray-700">{{ category }}</h3>

            <ul class="space-y-2">
              <li v-for="item in groupItems" :key="item.id" class="border rounded p-3 text-sm flex flex-col gap-1">
                <div><strong>{{ item.name }}</strong> — {{ item.description }}</div>
                <div>Кол-во: {{ item.quantity }} {{ item.unit }}</div>
                <div>Цена за единицу: {{ formatCurrency(item.unit_price) }}</div>
                <div class="font-semibold text-right">Итог: {{ formatCurrency(getItemTotal(item)) }}</div>
              </li>
            </ul>

            <div class="text-right font-semibold text-sm text-gray-600 pt-2">
              Итог по категории: {{ formatCurrency(getGroupTotal(groupItems)) }}
            </div>
          </div>

        </ul>

        <div class="pt-6">
          <p class="text-right font-semibold text-lg">
            Общая сумма: {{ formatCurrency(total) }}
          </p>
        </div>
      </div>
    </div>
    <div v-if="showConfirm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded shadow max-w-sm w-full text-center">
        <p class="mb-4 font-semibold">Вы уверены, что хотите удалить данный шаблон?</p>
        <div class="flex justify-center gap-4">
          <button @click="deleteTemplate" class="bg-red-500 text-white px-4 py-2 rounded-md">Да, удалить</button>
          <button @click="showConfirm = false" class="bg-gray-300 px-4 py-2 rounded-md">Отмена</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTemplatesStore } from '@/store/templates'
import { useToast } from 'vue-toastification'

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

const groupedItems = computed(() => {
  const groups = {}
  for (const item of template.value?.items || []) {
    const category = item.category?.trim() || 'Без категории'
    if (!groups[category]) groups[category] = []
    groups[category].push(item)
  }
  return groups
})

function getItemTotal(item) {
  return item.quantity * item.unit_price
}

function getGroupTotal(items) {
  return items.reduce((sum, item) => sum + getItemTotal(item), 0)
}

const total = computed(() => {
  return template.value?.items?.reduce((sum, item) => sum + getItemTotal(item), 0) || 0
})

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