<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import { getApiErrorMessage } from '@/lib/api-error'
import { useApprovalsStore } from '@/store/approvals'

const store = useApprovalsStore()
const toast = useToast()
const router = useRouter()

const activeTab = ref('pending')
const isLoading = ref(false)
const isSubmitting = ref(false)
const loadingPreviewEstimateId = ref(null)
const pendingTasks = ref([])
const historyTasks = ref([])
const previewByEstimateId = ref({})
const openPreviewByEstimateId = ref({})

const signModal = ref({
  open: false,
  stepId: null,
  estimateId: null,
  estimateName: '',
  stageLabel: '',
  decision: 'approve',
  signatureName: '',
  comment: ''
})

function workflowStatusLabel(status) {
  if (status === 'in_review') return 'На согласовании'
  if (status === 'approved') return 'Согласовано'
  if (status === 'rejected') return 'Отклонено'
  return 'Черновик'
}

function stepStatusLabel(status) {
  if (status === 'pending') return 'Ожидает подписи'
  if (status === 'approved') return 'Одобрено'
  if (status === 'rejected') return 'Отклонено'
  return '—'
}

function estimateStatusLabel(status) {
  if (status === 'draft') return 'Черновик'
  if (status === 'sent') return 'Отправлена'
  if (status === 'approved') return 'Согласована'
  if (status === 'paid') return 'Оплачена'
  if (status === 'cancelled') return 'Отменена'
  return '—'
}

function formatCurrency(value) {
  return `${Number(value || 0).toFixed(2)} ₽`
}

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleString('ru-RU')
}

async function loadPending() {
  isLoading.value = true
  try {
    pendingTasks.value = await store.fetchMyTasks('pending')
  } catch (error) {
    toast.error(getApiErrorMessage(error, 'Не удалось загрузить задачи согласования'))
  } finally {
    isLoading.value = false
  }
}

async function loadHistory() {
  isLoading.value = true
  try {
    historyTasks.value = await store.fetchMyTasks('history')
  } catch (error) {
    toast.error(getApiErrorMessage(error, 'Не удалось загрузить историю согласований'))
  } finally {
    isLoading.value = false
  }
}

async function switchTab(tab) {
  activeTab.value = tab
  if (tab === 'pending') await loadPending()
  if (tab === 'history') await loadHistory()
}

function openSignModal(task, decision) {
  signModal.value = {
    open: true,
    stepId: task.step_id,
    estimateId: task.estimate_id,
    estimateName: task.estimate_name,
    stageLabel: task.stage_label,
    decision,
    signatureName: '',
    comment: ''
  }
}

function closeSignModal() {
  if (isSubmitting.value) return
  signModal.value.open = false
}

async function submitDecision() {
  if (isSubmitting.value) return
  if (!signModal.value.signatureName.trim()) {
    toast.error('Введите имя подписанта')
    return
  }
  isSubmitting.value = true
  try {
    await store.signStep(signModal.value.stepId, {
      decision: signModal.value.decision,
      signature_name: signModal.value.signatureName,
      comment: signModal.value.comment || null
    })
    toast.success(signModal.value.decision === 'approve' ? 'Этап согласован' : 'Этап отклонен')
    signModal.value.open = false
    await Promise.all([loadPending(), loadHistory()])
  } catch (error) {
    toast.error(getApiErrorMessage(error, 'Не удалось подписать этап'))
  } finally {
    isSubmitting.value = false
  }
}

async function togglePreview(task) {
  const estimateId = task.estimate_id
  const opened = !!openPreviewByEstimateId.value[estimateId]
  if (opened) {
    openPreviewByEstimateId.value[estimateId] = false
    return
  }

  if (previewByEstimateId.value[estimateId]) {
    openPreviewByEstimateId.value[estimateId] = true
    return
  }

  loadingPreviewEstimateId.value = estimateId
  try {
    const preview = await store.getEstimatePreview(estimateId)
    previewByEstimateId.value[estimateId] = preview
    openPreviewByEstimateId.value[estimateId] = true
  } catch (error) {
    toast.error(getApiErrorMessage(error, 'Не удалось загрузить предпросмотр сметы'))
  } finally {
    loadingPreviewEstimateId.value = null
  }
}

function goToEstimate(task) {
  if (!task.can_open_estimate) return
  router.push(`/estimates/${task.estimate_id}`)
}

onMounted(async () => {
  await Promise.all([loadPending(), loadHistory()])
})
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-8 space-y-6">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Мои согласования</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Подписание этапов согласования с электронной подписью.
        </p>
      </div>
      <button class="qe-btn-secondary px-3 py-2 text-sm" @click="switchTab(activeTab)">
        Обновить
      </button>
    </div>

    <div class="flex items-center gap-1 bg-gray-100 dark:bg-qe-black2 rounded-xl p-1 w-fit">
      <button
        class="px-4 py-2 rounded-lg text-sm font-semibold transition"
        :class="activeTab === 'pending' ? 'bg-white dark:bg-gray-900 text-blue-600 shadow' : 'text-gray-500 hover:text-blue-600'"
        @click="switchTab('pending')"
      >
        Ожидают подписи
      </button>
      <button
        class="px-4 py-2 rounded-lg text-sm font-semibold transition"
        :class="activeTab === 'history' ? 'bg-white dark:bg-gray-900 text-blue-600 shadow' : 'text-gray-500 hover:text-blue-600'"
        @click="switchTab('history')"
      >
        История
      </button>
    </div>

    <div v-if="isLoading" class="text-sm text-gray-500 dark:text-gray-400">Загрузка...</div>

    <div
      v-if="activeTab === 'pending' && !isLoading && pendingTasks.length === 0"
      class="rounded-2xl border border-gray-200 dark:border-qe-black2 p-6 text-center text-gray-500 dark:text-gray-400 bg-white dark:bg-qe-black3"
    >
      Нет этапов, ожидающих вашей подписи.
    </div>

    <div
      v-if="activeTab === 'history' && !isLoading && historyTasks.length === 0"
      class="rounded-2xl border border-gray-200 dark:border-qe-black2 p-6 text-center text-gray-500 dark:text-gray-400 bg-white dark:bg-qe-black3"
    >
      История подписаний пуста.
    </div>

    <div v-if="activeTab === 'pending' && pendingTasks.length" class="space-y-3">
      <article
        v-for="task in pendingTasks"
        :key="task.step_id"
        class="rounded-2xl border border-gray-200 dark:border-qe-black2 bg-white dark:bg-qe-black3 p-4 shadow-sm"
      >
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div class="space-y-1">
            <p class="text-sm text-gray-500 dark:text-gray-400">Смета №{{ task.estimate_id }}</p>
            <p class="text-lg font-semibold text-gray-900 dark:text-white">
              {{ task.estimate_name }}
            </p>
            <p class="text-sm text-gray-700 dark:text-gray-200">
              Этап №{{ task.step_order }}: {{ task.stage_label }}
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              Владелец: {{ task.estimate_owner_login || '—' }} · Клиент: {{ task.client_name || '—' }}
            </p>
          </div>
          <div class="text-right space-y-2">
            <p class="text-xs text-gray-500 dark:text-gray-400">Статус процесса: {{ workflowStatusLabel(task.workflow_status) }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">Статус этапа: {{ stepStatusLabel(task.step_status) }}</p>
          </div>
        </div>

        <div class="mt-3 grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-gray-600 dark:text-gray-300">
          <div class="rounded-lg bg-gray-50 dark:bg-qe-black2 px-3 py-2">
            <p class="text-[11px] text-gray-400">Ответственный</p>
            <p class="font-medium">{{ task.responsible || '—' }}</p>
          </div>
          <div class="rounded-lg bg-gray-50 dark:bg-qe-black2 px-3 py-2">
            <p class="text-[11px] text-gray-400">Дата</p>
            <p class="font-medium">{{ formatDate(task.event_datetime) }}</p>
          </div>
          <div class="rounded-lg bg-gray-50 dark:bg-qe-black2 px-3 py-2">
            <p class="text-[11px] text-gray-400">Сумма</p>
            <p class="font-medium">{{ formatCurrency(task.total_external) }}</p>
          </div>
          <div class="rounded-lg bg-gray-50 dark:bg-qe-black2 px-3 py-2">
            <p class="text-[11px] text-gray-400">С НДС</p>
            <p class="font-medium">{{ formatCurrency(task.total_with_vat) }}</p>
          </div>
        </div>

        <div v-if="task.items_preview?.length" class="mt-2 text-xs text-gray-500 dark:text-gray-400">
          Ключевые позиции: {{ task.items_preview.join(', ') }}
        </div>

        <div class="mt-4 flex flex-wrap items-center gap-2">
          <button class="qe-btn-secondary px-4 py-2 text-sm" @click="togglePreview(task)" :disabled="loadingPreviewEstimateId === task.estimate_id">
            {{
              openPreviewByEstimateId[task.estimate_id]
                ? 'Скрыть предпросмотр'
                : loadingPreviewEstimateId === task.estimate_id
                  ? 'Загрузка...'
                  : 'Предпросмотр'
            }}
          </button>
          <button v-if="task.can_open_estimate" class="qe-btn-secondary px-4 py-2 text-sm" @click="goToEstimate(task)">
            Перейти к смете
          </button>
          <button class="qe-btn-success px-4 py-2 text-sm" @click="openSignModal(task, 'approve')">Подписать и согласовать</button>
          <button class="qe-btn-danger px-4 py-2 text-sm" @click="openSignModal(task, 'reject')">Отклонить</button>
        </div>

        <div
          v-if="openPreviewByEstimateId[task.estimate_id] && previewByEstimateId[task.estimate_id]"
          class="mt-4 rounded-xl border border-gray-200 dark:border-qe-black2 bg-gray-50 dark:bg-qe-black2 p-4"
        >
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p class="text-sm font-semibold text-gray-900 dark:text-white">
                {{ previewByEstimateId[task.estimate_id].name }}
              </p>
              <p class="text-xs text-gray-500 dark:text-gray-400">
                Статус: {{ estimateStatusLabel(previewByEstimateId[task.estimate_id].status) }} ·
                Клиент: {{ previewByEstimateId[task.estimate_id].client_name || '—' }}
              </p>
              <p class="text-xs text-gray-500 dark:text-gray-400">
                Место: {{ previewByEstimateId[task.estimate_id].event_place || '—' }}
              </p>
            </div>
            <div class="text-right text-xs text-gray-600 dark:text-gray-300">
              <p>Сумма: {{ formatCurrency(previewByEstimateId[task.estimate_id].total_external) }}</p>
              <p>С НДС: {{ formatCurrency(previewByEstimateId[task.estimate_id].total_with_vat) }}</p>
            </div>
          </div>

          <div class="mt-3 grid gap-2">
            <div
              v-for="(item, idx) in previewByEstimateId[task.estimate_id].items_preview"
              :key="`${item.name}-${idx}`"
              class="rounded-lg bg-white dark:bg-qe-black3 px-3 py-2 border border-gray-100 dark:border-qe-black2 text-xs"
            >
              <p class="font-medium text-gray-900 dark:text-white">{{ item.name }}</p>
              <p class="text-gray-500 dark:text-gray-400">
                {{ item.quantity }} {{ item.unit }} · {{ formatCurrency(item.external_price) }} ·
                Итого: {{ formatCurrency(item.line_total) }}
              </p>
            </div>
          </div>
        </div>
      </article>
    </div>

    <div v-if="activeTab === 'history' && historyTasks.length" class="overflow-x-auto rounded-2xl border border-gray-200 dark:border-qe-black2 bg-white dark:bg-qe-black3">
      <table class="min-w-full text-sm">
        <thead class="bg-gray-50 dark:bg-qe-black2 text-gray-600 dark:text-gray-300">
          <tr>
            <th class="px-4 py-3 text-left font-semibold">Смета</th>
            <th class="px-4 py-3 text-left font-semibold">Этап</th>
            <th class="px-4 py-3 text-left font-semibold">Статус этапа</th>
            <th class="px-4 py-3 text-left font-semibold">Статус процесса</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in historyTasks" :key="task.step_id" class="border-t border-gray-100 dark:border-qe-black2">
            <td class="px-4 py-3">{{ task.estimate_name }}</td>
            <td class="px-4 py-3">№{{ task.step_order }}. {{ task.stage_label }}</td>
            <td class="px-4 py-3">{{ stepStatusLabel(task.step_status) }}</td>
            <td class="px-4 py-3">{{ workflowStatusLabel(task.workflow_status) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <Teleport to="body">
      <transition name="modal-fade">
        <div v-if="signModal.open" class="fixed inset-0 z-[80]">
          <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="closeSignModal" />
          <div class="relative flex min-h-full items-center justify-center px-4 py-6">
            <div class="w-full max-w-xl rounded-2xl bg-white dark:bg-qe-black2 shadow-2xl border border-gray-200 dark:border-qe-black3 p-6">
              <h3 class="text-xl font-bold text-gray-800 dark:text-white mb-1">
                {{ signModal.decision === 'approve' ? 'Согласование этапа' : 'Отклонение этапа' }}
              </h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                {{ signModal.estimateName }} · {{ signModal.stageLabel }}
              </p>

              <div class="mt-5 space-y-4">
                <div>
                  <label class="block text-sm font-semibold text-gray-700 dark:text-gray-200 mb-1">Имя подписанта</label>
                  <input v-model.trim="signModal.signatureName" type="text" class="qe-input w-full" placeholder="ФИО или отображаемое имя" />
                </div>
                <div>
                  <label class="block text-sm font-semibold text-gray-700 dark:text-gray-200 mb-1">Комментарий</label>
                  <textarea v-model.trim="signModal.comment" rows="4" class="qe-input w-full resize-y" placeholder="Необязательно" />
                </div>
              </div>

              <div class="mt-6 flex justify-end gap-3">
                <button class="qe-btn-secondary" @click="closeSignModal" :disabled="isSubmitting">Отмена</button>
                <button
                  :class="signModal.decision === 'approve' ? 'qe-btn-success' : 'qe-btn-danger'"
                  @click="submitDecision"
                  :disabled="isSubmitting"
                >
                  {{ isSubmitting ? 'Подписание...' : signModal.decision === 'approve' ? 'Подписать' : 'Подписать и отклонить' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

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
