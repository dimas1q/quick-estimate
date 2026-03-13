<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useToast } from 'vue-toastification'

import { getApiErrorMessage } from '@/lib/api-error'
import { useEstimatesStore } from '@/store/estimates'

const props = defineProps({
  estimateId: {
    type: [Number, String],
    required: true
  },
  readOnly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['workflow-updated'])

const store = useEstimatesStore()
const toast = useToast()

const isLoading = ref(false)
const isSaving = ref(false)
const isStarting = ref(false)
const approvers = ref([])
const workflow = ref(null)
const formSteps = ref([])

const defaultSteps = [
  { step_order: 1, stage_key: 'manager', stage_label: 'Менеджер', approver_user_id: null },
  { step_order: 2, stage_key: 'finance', stage_label: 'Финансы', approver_user_id: null },
  { step_order: 3, stage_key: 'director', stage_label: 'Директор', approver_user_id: null }
]

const canEdit = computed(() => workflow.value?.status !== 'in_review' && !props.readOnly)
const canStart = computed(() => {
  if (props.readOnly) return false
  if (!workflow.value) return false
  if (workflow.value.status === 'in_review') return false
  return (workflow.value.steps || []).length > 0
})

function resetFormFromWorkflow() {
  if (workflow.value?.steps?.length) {
    formSteps.value = workflow.value.steps.map((step) => ({
      step_order: step.step_order,
      stage_key: step.stage_key,
      stage_label: step.stage_label,
      approver_user_id: step.approver_user_id
    }))
    return
  }
  formSteps.value = defaultSteps.map((step) => ({ ...step }))
}

async function loadData() {
  isLoading.value = true
  try {
    const [approverList, wf] = await Promise.all([
      store.fetchApprovers(),
      store.getApprovalWorkflow(props.estimateId)
    ])
    approvers.value = approverList || []
    workflow.value = wf
    resetFormFromWorkflow()
  } catch (error) {
    toast.error(getApiErrorMessage(error, 'Не удалось загрузить маршрут согласования'))
  } finally {
    isLoading.value = false
  }
}

function normalizeStepOrder() {
  formSteps.value = [...formSteps.value]
    .sort((a, b) => Number(a.step_order || 0) - Number(b.step_order || 0))
    .map((step, index) => ({
      ...step,
      step_order: index + 1
    }))
}

function addStep() {
  if (!canEdit.value) return
  formSteps.value.push({
    step_order: formSteps.value.length + 1,
    stage_key: `stage_${formSteps.value.length + 1}`,
    stage_label: `Этап ${formSteps.value.length + 1}`,
    approver_user_id: null
  })
}

function removeStep(index) {
  if (!canEdit.value) return
  formSteps.value.splice(index, 1)
  normalizeStepOrder()
}

async function saveWorkflow() {
  if (!canEdit.value) return
  if (!formSteps.value.length) {
    toast.error('Добавьте хотя бы один шаг согласования')
    return
  }
  if (formSteps.value.some((step) => !step.approver_user_id)) {
    toast.error('Выберите согласующего для каждого шага')
    return
  }

  isSaving.value = true
  try {
    normalizeStepOrder()
    workflow.value = await store.saveApprovalWorkflow(props.estimateId, {
      steps: formSteps.value.map((step) => ({
        step_order: step.step_order,
        stage_key: step.stage_key?.trim() || `stage_${step.step_order}`,
        stage_label: step.stage_label?.trim() || `Этап ${step.step_order}`,
        approver_user_id: Number(step.approver_user_id)
      }))
    })
    resetFormFromWorkflow()
    toast.success('Маршрут согласования сохранен')
    emit('workflow-updated')
  } catch (error) {
    toast.error(getApiErrorMessage(error, 'Не удалось сохранить маршрут согласования'))
  } finally {
    isSaving.value = false
  }
}

async function startWorkflow() {
  if (!canStart.value) return
  isStarting.value = true
  try {
    workflow.value = await store.startApprovalWorkflow(props.estimateId)
    toast.success('Согласование запущено')
    await loadData()
    emit('workflow-updated')
  } catch (error) {
    toast.error(getApiErrorMessage(error, 'Не удалось запустить согласование'))
  } finally {
    isStarting.value = false
  }
}

function workflowStatusLabel(value) {
  if (value === 'in_review') return 'На согласовании'
  if (value === 'approved') return 'Согласовано'
  if (value === 'rejected') return 'Отклонено'
  return 'Черновик'
}

function stepStatusLabel(value) {
  if (value === 'approved') return 'Одобрен'
  if (value === 'rejected') return 'Отклонен'
  return 'Ожидает подписи'
}

function stepStatusClass(value) {
  if (value === 'approved') return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
  if (value === 'rejected') return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
  return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
}

onMounted(loadData)
watch(() => props.estimateId, loadData)
</script>

<template>
  <section class="mt-8 rounded-2xl border border-gray-200 dark:border-qe-black2 bg-white dark:bg-qe-black3 p-5 shadow-sm">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h3 class="text-lg font-bold text-gray-900 dark:text-white">Маршрут согласования и ЭП</h3>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Многоэтапное согласование сметы с электронной подписью каждого шага.
        </p>
      </div>
      <span class="inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold"
        :class="workflow?.status === 'approved'
          ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
          : workflow?.status === 'rejected'
            ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
            : workflow?.status === 'in_review'
              ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
              : 'bg-gray-100 text-gray-700 dark:bg-qe-black2 dark:text-gray-300'">
        {{ workflowStatusLabel(workflow?.status) }}
      </span>
    </div>

    <div v-if="isLoading" class="mt-4 text-sm text-gray-500 dark:text-gray-400">Загрузка маршрута...</div>

    <div v-else class="mt-4 space-y-4">
      <div class="space-y-3">
        <div v-for="(step, index) in formSteps" :key="`${step.step_order}-${index}`"
          class="rounded-xl border border-gray-200 dark:border-qe-black2 p-3">
          <div class="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
            <div class="md:col-span-1">
              <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">№</label>
              <input v-model.number="step.step_order" type="number" min="1" class="qe-input w-full"
                :disabled="!canEdit" />
            </div>
            <div class="md:col-span-3">
              <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">Ключ этапа</label>
              <input v-model.trim="step.stage_key" type="text" class="qe-input w-full" placeholder="manager"
                :disabled="!canEdit" />
            </div>
            <div class="md:col-span-4">
              <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">Название этапа</label>
              <input v-model.trim="step.stage_label" type="text" class="qe-input w-full" placeholder="Менеджер"
                :disabled="!canEdit" />
            </div>
            <div class="md:col-span-3">
              <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">Согласующий</label>
              <select v-model="step.approver_user_id" class="qe-input w-full" :disabled="!canEdit">
                <option :value="null">Выберите пользователя</option>
                <option v-for="approver in approvers" :key="approver.id" :value="approver.id">
                  {{ approver.name || approver.login }} ({{ approver.email }})
                </option>
              </select>
            </div>
            <div class="md:col-span-1 flex md:justify-end">
              <button class="qe-btn-danger px-3 py-2 text-xs" @click="removeStep(index)" :disabled="!canEdit || formSteps.length <= 1">
                Удалить
              </button>
            </div>
          </div>

          <div v-if="workflow?.steps?.[index]" class="mt-2 flex flex-wrap items-center gap-2">
            <span class="inline-flex rounded-full px-2 py-1 text-xs font-semibold" :class="stepStatusClass(workflow.steps[index].status)">
              {{ stepStatusLabel(workflow.steps[index].status) }}
            </span>
            <span v-if="workflow.steps[index].signature_name" class="text-xs text-gray-600 dark:text-gray-300">
              Подписал: {{ workflow.steps[index].signature_name }}
            </span>
            <span v-if="workflow.steps[index].signed_at" class="text-xs text-gray-500 dark:text-gray-400">
              {{ new Date(workflow.steps[index].signed_at).toLocaleString('ru-RU') }}
            </span>
          </div>
        </div>
      </div>

      <div class="flex flex-wrap gap-2">
        <button class="qe-btn-secondary px-3 py-2 text-sm" @click="addStep" :disabled="!canEdit">Добавить этап</button>
        <button class="qe-btn px-4 py-2 text-sm" @click="saveWorkflow" :disabled="!canEdit || isSaving">
          {{ isSaving ? 'Сохранение...' : 'Сохранить маршрут' }}
        </button>
        <button class="qe-btn-success px-4 py-2 text-sm" @click="startWorkflow" :disabled="!canStart || isStarting">
          {{
            workflow?.status === 'in_review'
              ? 'Согласование запущено'
              : isStarting
                ? 'Запуск...'
                : 'Запустить согласование'
          }}
        </button>
      </div>
      <p
        v-if="workflow?.status === 'in_review'"
        class="text-xs text-blue-600 dark:text-blue-300"
      >
        Согласование уже запущено. Для изменения маршрута дождитесь завершения процесса.
      </p>
    </div>
  </section>
</template>
