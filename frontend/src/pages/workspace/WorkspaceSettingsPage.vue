<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import { getApiErrorMessage } from '@/lib/api-error'
import { useAuthStore } from '@/store/auth'
import { useWorkspacesStore } from '@/store/workspaces'

const auth = useAuthStore()
const workspacesStore = useWorkspacesStore()
const toast = useToast()
const router = useRouter()

const isLoading = ref(false)
const isSubmitting = ref(false)
const switchingWorkspaceId = ref(null)
const workingUserId = ref(null)
const workingInvitationId = ref(null)
const incomingWorkingId = ref(null)
const transferOwnerUserId = ref(null)
const deleteConfirmName = ref('')

const createWorkspaceForm = reactive({
  name: '',
  domain: ''
})

const workspaceForm = reactive({
  name: '',
  domain: ''
})

const inviteForm = reactive({
  email: '',
  role: 'estimator',
  expires_in_hours: 72
})

const roleLabels = {
  owner: 'Владелец',
  admin: 'Администратор',
  approver: 'Подписант',
  estimator: 'Сметчик',
  guest: 'Гость'
}

const invitationStatusLabels = {
  pending: 'Ожидает',
  accepted: 'Принято',
  revoked: 'Отклонено/отозвано',
  expired: 'Истекло'
}

const editableRoles = [
  { value: 'admin', label: 'Администратор' },
  { value: 'approver', label: 'Подписант' },
  { value: 'estimator', label: 'Сметчик' },
  { value: 'guest', label: 'Гость' }
]

const currentWorkspace = computed(() => workspacesStore.current)
const members = computed(() => workspacesStore.members)
const invitations = computed(() => workspacesStore.invitations)
const incomingInvitations = computed(() => workspacesStore.incomingInvitations)
const currentRole = computed(() => currentWorkspace.value?.role || 'guest')
const hasCurrentWorkspace = computed(() => Boolean(currentWorkspace.value?.organization_id))
const isOwner = computed(() => currentRole.value === 'owner')
const canManageMembers = computed(() => currentRole.value === 'owner' || currentRole.value === 'admin')
const canManageInvites = computed(() => currentRole.value === 'owner' || currentRole.value === 'admin')
const canEditWorkspace = computed(() => currentRole.value === 'owner' || currentRole.value === 'admin')
const isCurrentWorkspaceDefault = computed(() => {
  if (!currentWorkspace.value?.organization_id) return false
  if (typeof currentWorkspace.value.is_default === 'boolean') {
    return currentWorkspace.value.is_default
  }
  return auth.user?.default_organization_id === currentWorkspace.value.organization_id
})

const ownershipCandidates = computed(() =>
  members.value.filter(
    (member) => !member.is_current_user && member.role !== 'owner' && member.is_active
  )
)

function roleLabel(role) {
  return roleLabels[role] || role || '—'
}

function invitationStatusLabel(status) {
  return invitationStatusLabels[status] || status
}

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleString('ru-RU')
}

function fillWorkspaceForm() {
  workspaceForm.name = currentWorkspace.value?.name || ''
  workspaceForm.domain = currentWorkspace.value?.domain || ''
}

function workspaceHint(workspace) {
  if (!workspace?.organization_slug) return 'Идентификатор не задан'
  return `Идентификатор: ${workspace.organization_slug}`
}

async function switchWorkspace(workspace) {
  if (!workspace?.organization_id || workspace.is_current) return
  if (switchingWorkspaceId.value) return

  switchingWorkspaceId.value = workspace.organization_id
  try {
    await auth.switchWorkspace(workspace.organization_id)
    await loadWorkspaceSettings()
    toast.success('Рабочее пространство переключено')
  } catch (error) {
    toast.error(getApiErrorMessage(error, 'Не удалось переключить рабочее пространство'))
  } finally {
    switchingWorkspaceId.value = null
  }
}

async function loadWorkspaceSettings() {
  isLoading.value = true
  try {
    await auth.fetchWorkspaces()
    let hasCurrentWorkspace = true
    try {
      await workspacesStore.fetchCurrent()
      fillWorkspaceForm()
    } catch {
      hasCurrentWorkspace = false
      workspacesStore.current = null
      workspacesStore.members = []
      workspacesStore.invitations = []
    }

    if (hasCurrentWorkspace) {
      await workspacesStore.fetchMembers()

      if (canManageInvites.value) {
        await workspacesStore.fetchInvitations()
      } else {
        workspacesStore.invitations = []
      }
    }

    await workspacesStore.fetchIncomingInvitations()
  } catch (error) {
    toast.error(getApiErrorMessage(error, 'Не удалось загрузить настройки рабочего пространства'))
  } finally {
    isLoading.value = false
  }
}

async function createWorkspace() {
  if (isSubmitting.value) return
  isSubmitting.value = true
  try {
    const payload = {
      name: createWorkspaceForm.name.trim(),
      domain: createWorkspaceForm.domain.trim() || null
    }
    await workspacesStore.createWorkspace(payload)
    createWorkspaceForm.name = ''
    createWorkspaceForm.domain = ''
    await auth.fetchUser()
    await auth.fetchWorkspaces()
    await loadWorkspaceSettings()
    toast.success('Рабочее пространство создано')
  } catch (error) {
    toast.error(getApiErrorMessage(error, 'Не удалось создать рабочее пространство'))
  } finally {
    isSubmitting.value = false
  }
}

async function saveWorkspaceInfo() {
  if (!canEditWorkspace.value || isSubmitting.value) return
  isSubmitting.value = true
  try {
    await workspacesStore.updateCurrentWorkspace({
      name: workspaceForm.name.trim(),
      domain: workspaceForm.domain.trim() || null
    })
    await auth.fetchWorkspaces()
    toast.success('Данные рабочего пространства сохранены')
  } catch (error) {
    toast.error(getApiErrorMessage(error, 'Не удалось обновить рабочее пространство'))
  } finally {
    isSubmitting.value = false
  }
}

async function changeMemberRole(member, role) {
  if (!canManageMembers.value || workingUserId.value || member.role === role) return
  workingUserId.value = member.user_id
  try {
    await workspacesStore.updateMemberRole(member.user_id, role)
    toast.success('Роль участника обновлена')
    await auth.fetchWorkspaces()
  } catch (error) {
    toast.error(getApiErrorMessage(error, 'Не удалось изменить роль участника'))
  } finally {
    workingUserId.value = null
  }
}

async function removeMember(member) {
  if (!canManageMembers.value || workingUserId.value) return
  if (!window.confirm(`Удалить участника ${member.login} из пространства?`)) return

  workingUserId.value = member.user_id
  try {
    await workspacesStore.removeMember(member.user_id)
    toast.success('Участник удален')
  } catch (error) {
    toast.error(getApiErrorMessage(error, 'Не удалось удалить участника'))
  } finally {
    workingUserId.value = null
  }
}

async function createInvitation() {
  if (!canManageInvites.value || isSubmitting.value) return
  isSubmitting.value = true
  try {
    const payload = {
      email: inviteForm.email.trim(),
      role: inviteForm.role,
      expires_in_hours: Number(inviteForm.expires_in_hours || 72)
    }
    const created = await workspacesStore.createInvitation(payload)
    inviteForm.email = ''
    inviteForm.role = 'estimator'
    inviteForm.expires_in_hours = 72

    if (created?.email_sent) {
      toast.success('Приглашение отправлено на email')
    } else {
      toast.warning('Приглашение создано, но email не отправлен. Проверьте SMTP')
    }
  } catch (error) {
    toast.error(getApiErrorMessage(error, 'Не удалось создать приглашение'))
  } finally {
    isSubmitting.value = false
  }
}

async function revokeInvitation(invitationId) {
  if (!canManageInvites.value || workingInvitationId.value) return
  workingInvitationId.value = invitationId
  try {
    await workspacesStore.revokeInvitation(invitationId)
    toast.success('Приглашение отозвано')
  } catch (error) {
    toast.error(getApiErrorMessage(error, 'Не удалось отозвать приглашение'))
  } finally {
    workingInvitationId.value = null
  }
}

async function acceptIncoming(invitationId) {
  if (incomingWorkingId.value) return
  incomingWorkingId.value = invitationId
  try {
    await workspacesStore.acceptIncomingInvitation(invitationId)
    await auth.fetchUser()
    await auth.fetchWorkspaces()
    await loadWorkspaceSettings()
    toast.success('Приглашение принято')
  } catch (error) {
    toast.error(getApiErrorMessage(error, 'Не удалось принять приглашение'))
  } finally {
    incomingWorkingId.value = null
  }
}

async function rejectIncoming(invitationId) {
  if (incomingWorkingId.value) return
  incomingWorkingId.value = invitationId
  try {
    await workspacesStore.rejectIncomingInvitation(invitationId)
    await loadWorkspaceSettings()
    toast.success('Приглашение отклонено')
  } catch (error) {
    toast.error(getApiErrorMessage(error, 'Не удалось отклонить приглашение'))
  } finally {
    incomingWorkingId.value = null
  }
}

async function transferOwnership() {
  if (!isOwner.value || isSubmitting.value || !transferOwnerUserId.value) return
  if (!window.confirm('Передать роль владельца выбранному участнику?')) return

  isSubmitting.value = true
  try {
    await workspacesStore.transferOwnership(Number(transferOwnerUserId.value))
    transferOwnerUserId.value = null
    await auth.fetchWorkspaces()
    await loadWorkspaceSettings()
    toast.success('Роль владельца передана')
  } catch (error) {
    toast.error(getApiErrorMessage(error, 'Не удалось передать роль владельца'))
  } finally {
    isSubmitting.value = false
  }
}

async function deleteWorkspace() {
  if (!isOwner.value || isSubmitting.value || !currentWorkspace.value?.name) return
  if (deleteConfirmName.value.trim() !== currentWorkspace.value.name) {
    toast.error('Введите точное название пространства для удаления')
    return
  }
  if (!window.confirm('Удалить рабочее пространство? Действие необратимо.')) return

  isSubmitting.value = true
  try {
    await workspacesStore.deleteWorkspace(deleteConfirmName.value.trim())
    await auth.fetchUser()
    await auth.fetchWorkspaces()
    await loadWorkspaceSettings()
    toast.success('Рабочее пространство удалено')
    router.push('/estimates')
  } catch (error) {
    toast.error(getApiErrorMessage(error, 'Не удалось удалить рабочее пространство'))
  } finally {
    isSubmitting.value = false
  }
}

onMounted(async () => {
  await loadWorkspaceSettings()
})
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-8 space-y-6">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Настройки пространств</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Управление рабочими пространствами, участниками и приглашениями.
        </p>
      </div>
      <button class="qe-btn px-4" :disabled="isLoading" @click="loadWorkspaceSettings">Обновить</button>
    </div>

    <section class="rounded-2xl border border-gray-200 dark:border-qe-black2 bg-white dark:bg-qe-black3 p-4 sm:p-5 space-y-4">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Мои рабочие пространства</h2>
      <p class="text-xs text-gray-500 dark:text-gray-400">
        Переключайтесь между рабочими пространствами, чтобы управлять разными проектами или командами.
      </p>

      <div class="rounded-xl border border-gray-200 dark:border-qe-black2 overflow-x-auto">
        <table class="min-w-full text-sm bg-white dark:bg-qe-black3">
          <thead class="bg-gray-50 dark:bg-qe-black2 text-gray-600 dark:text-gray-300">
            <tr>
              <th class="px-4 py-3 text-left font-semibold">Название</th>
              <th class="px-4 py-3 text-left font-semibold">Роль</th>
              <th class="px-4 py-3 text-left font-semibold">Домен</th>
              <th class="px-4 py-3 text-left font-semibold">Идентификатор</th>
              <th class="px-4 py-3 text-right font-semibold">Действие</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="workspace in auth.workspaces"
              :key="workspace.organization_id"
              class="border-t border-gray-100 dark:border-qe-black2"
            >
              <td class="px-4 py-3 font-medium text-gray-900 dark:text-white">
                <span>{{ workspace.organization_name }}</span>
              </td>
              <td class="px-4 py-3">{{ roleLabel(workspace.role) }}</td>
              <td class="px-4 py-3">{{ workspace.organization_domain || '—' }}</td>
              <td class="px-4 py-3 text-xs text-gray-500 dark:text-gray-400">
                {{ workspaceHint(workspace) }}
              </td>
              <td class="px-4 py-3">
                <div class="flex justify-end">
                  <button
                    v-if="!workspace.is_current"
                    class="qe-btn-secondary px-3 py-1 text-xs"
                    :disabled="Boolean(switchingWorkspaceId)"
                    @click="switchWorkspace(workspace)"
                  >
                    {{ switchingWorkspaceId === workspace.organization_id ? 'Переключение...' : 'Сделать текущим' }}
                  </button>
                  <span v-else class="inline-flex rounded-full px-2.5 py-1 text-xs font-semibold bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300">
                    Текущее
                  </span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <input v-model.trim="createWorkspaceForm.name" class="qe-input" type="text" placeholder="Название нового пространства" />
        <input v-model.trim="createWorkspaceForm.domain" class="qe-input" type="text" placeholder="Домен компании (необязательно)" />
        <button class="qe-btn" :disabled="isSubmitting" @click="createWorkspace">Создать пространство</button>
      </div>
    </section>

    <section
      v-if="!hasCurrentWorkspace"
      class="rounded-2xl border border-amber-200 dark:border-amber-900 bg-amber-50/60 dark:bg-amber-950/20 p-4 sm:p-5 space-y-2"
    >
      <h2 class="text-lg font-semibold text-amber-700 dark:text-amber-300">Рабочее пространство не выбрано</h2>
      <p class="text-sm text-amber-700/80 dark:text-amber-300/80">
        Выберите пространство в таблице «Мои рабочие пространства», чтобы работать со сметами, клиентами и шаблонами.
      </p>
    </section>

    <section v-if="hasCurrentWorkspace" class="rounded-2xl border border-gray-200 dark:border-qe-black2 bg-white dark:bg-qe-black3 p-4 sm:p-5 space-y-3">
      <div class="flex flex-wrap items-center gap-2">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Текущее пространство</h2>
        <span class="inline-flex rounded-full px-2.5 py-1 text-xs font-semibold bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
          {{ roleLabel(currentRole) }}
        </span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <input v-model.trim="workspaceForm.name" type="text" class="qe-input" placeholder="Название пространства" :disabled="!canEditWorkspace" />
        <input v-model.trim="workspaceForm.domain" type="text" class="qe-input" placeholder="Домен компании (необязательно)" :disabled="!canEditWorkspace" />
      </div>
      <p class="text-xs text-gray-500 dark:text-gray-400">
        Идентификатор пространства: <strong>{{ currentWorkspace?.slug || '—' }}</strong>.
      </p>

      <div class="flex justify-end">
        <button class="qe-btn px-4" :disabled="!canEditWorkspace || isSubmitting" @click="saveWorkspaceInfo">Сохранить изменения</button>
      </div>
    </section>

    <section v-if="hasCurrentWorkspace" class="space-y-3">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Участники</h2>
      <div class="rounded-2xl border border-gray-200 dark:border-qe-black2 bg-white dark:bg-qe-black3 overflow-x-auto">
        <table class="min-w-full text-sm">
          <thead class="bg-gray-50 dark:bg-qe-black2 text-gray-600 dark:text-gray-300">
            <tr>
              <th class="px-4 py-3 text-left font-semibold">Пользователь</th>
              <th class="px-4 py-3 text-left font-semibold">Роль</th>
              <th class="px-4 py-3 text-left font-semibold">Статус</th>
              <th class="px-4 py-3 text-left font-semibold">Вступил</th>
              <th class="px-4 py-3 text-right font-semibold">Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="member in members" :key="member.user_id" class="border-t border-gray-100 dark:border-qe-black2">
              <td class="px-4 py-3">
                <p class="font-medium text-gray-900 dark:text-white">{{ member.name || member.login }}</p>
                <p class="text-xs text-gray-500 dark:text-gray-400">{{ member.email }}</p>
              </td>
              <td class="px-4 py-3">
                <template v-if="canManageMembers && member.role !== 'owner'">
                  <select class="qe-input-sm max-w-[180px]" :value="member.role" :disabled="workingUserId === member.user_id" @change="changeMemberRole(member, $event.target.value)">
                    <option v-for="roleOption in editableRoles" :key="roleOption.value" :value="roleOption.value">{{ roleOption.label }}</option>
                  </select>
                </template>
                <span v-else class="text-sm text-gray-700 dark:text-gray-200">{{ roleLabel(member.role) }}</span>
              </td>
              <td class="px-4 py-3">
                <span class="inline-flex rounded-full px-2.5 py-1 text-xs font-semibold" :class="member.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'">
                  {{ member.is_active ? 'Активен' : 'Отключен' }}
                </span>
              </td>
              <td class="px-4 py-3 text-gray-600 dark:text-gray-300">{{ formatDate(member.joined_at) }}</td>
              <td class="px-4 py-3">
                <div class="flex justify-end">
                  <button v-if="canManageMembers && !member.is_current_user && member.role !== 'owner'" class="qe-btn-danger px-3 py-1 text-xs" :disabled="workingUserId === member.user_id" @click="removeMember(member)">
                    Удалить
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="rounded-2xl border border-gray-200 dark:border-qe-black2 bg-white dark:bg-qe-black3 p-4 sm:p-5 space-y-4">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Входящие приглашения</h2>
      <div v-if="incomingInvitations.length === 0" class="text-sm text-gray-500 dark:text-gray-400">
        Нет входящих приглашений.
      </div>
      <div v-else class="rounded-xl border border-gray-200 dark:border-qe-black2 overflow-x-auto">
        <table class="min-w-full text-sm bg-white dark:bg-qe-black3">
          <thead class="bg-gray-50 dark:bg-qe-black2 text-gray-600 dark:text-gray-300">
            <tr>
              <th class="px-4 py-3 text-left font-semibold">Пространство</th>
              <th class="px-4 py-3 text-left font-semibold">Роль</th>
              <th class="px-4 py-3 text-left font-semibold">Пригласил</th>
              <th class="px-4 py-3 text-left font-semibold">Действует до</th>
              <th class="px-4 py-3 text-right font-semibold">Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="invite in incomingInvitations" :key="invite.id" class="border-t border-gray-100 dark:border-qe-black2">
              <td class="px-4 py-3">
                <p class="font-medium text-gray-900 dark:text-white">{{ invite.organization_name }}</p>
                <p class="text-xs text-gray-500 dark:text-gray-400">Идентификатор: {{ invite.organization_slug }}</p>
              </td>
              <td class="px-4 py-3">{{ roleLabel(invite.role) }}</td>
              <td class="px-4 py-3">{{ invite.invited_by_login || invite.invited_by_email || '—' }}</td>
              <td class="px-4 py-3">{{ formatDate(invite.expires_at) }}</td>
              <td class="px-4 py-3">
                <div class="flex justify-end gap-2">
                  <button class="qe-btn-success px-3 py-1 text-xs" :disabled="incomingWorkingId === invite.id" @click="acceptIncoming(invite.id)">Принять</button>
                  <button class="qe-btn-danger px-3 py-1 text-xs" :disabled="incomingWorkingId === invite.id" @click="rejectIncoming(invite.id)">Отклонить</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section v-if="hasCurrentWorkspace && canManageInvites" class="rounded-2xl border border-gray-200 dark:border-qe-black2 bg-white dark:bg-qe-black3 p-4 sm:p-5 space-y-4">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Исходящие приглашения</h2>

      <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
        <input v-model.trim="inviteForm.email" type="email" class="qe-input md:col-span-2" placeholder="Email участника" />
        <select v-model="inviteForm.role" class="qe-input">
          <option v-for="roleOption in editableRoles" :key="roleOption.value" :value="roleOption.value">{{ roleOption.label }}</option>
        </select>
        <input v-model.number="inviteForm.expires_in_hours" type="number" min="1" max="720" class="qe-input" placeholder="Срок (часы)" />
      </div>

      <div class="flex justify-end">
        <button class="qe-btn px-4" :disabled="isSubmitting" @click="createInvitation">Отправить приглашение</button>
      </div>

      <div class="rounded-xl border border-gray-200 dark:border-qe-black2 overflow-x-auto">
        <table class="min-w-full text-sm bg-white dark:bg-qe-black3">
          <thead class="bg-gray-50 dark:bg-qe-black2 text-gray-600 dark:text-gray-300">
            <tr>
              <th class="px-4 py-3 text-left font-semibold">Email</th>
              <th class="px-4 py-3 text-left font-semibold">Роль</th>
              <th class="px-4 py-3 text-left font-semibold">Статус</th>
              <th class="px-4 py-3 text-left font-semibold">Действует до</th>
              <th class="px-4 py-3 text-right font-semibold">Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="invite in invitations" :key="invite.id" class="border-t border-gray-100 dark:border-qe-black2">
              <td class="px-4 py-3">{{ invite.email }}</td>
              <td class="px-4 py-3">{{ roleLabel(invite.role) }}</td>
              <td class="px-4 py-3">{{ invitationStatusLabel(invite.status) }}</td>
              <td class="px-4 py-3">{{ formatDate(invite.expires_at) }}</td>
              <td class="px-4 py-3">
                <div class="flex justify-end">
                  <button v-if="invite.status === 'pending'" class="qe-btn-danger px-3 py-1 text-xs" :disabled="workingInvitationId === invite.id" @click="revokeInvitation(invite.id)">
                    Отозвать
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section v-if="hasCurrentWorkspace && isOwner" class="rounded-2xl border border-gray-200 dark:border-qe-black2 bg-white dark:bg-qe-black3 p-4 sm:p-5 space-y-4">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Передача роли владельца</h2>
      <div class="flex flex-col sm:flex-row gap-3">
        <select v-model="transferOwnerUserId" class="qe-input flex-1">
          <option :value="null">Выберите нового владельца</option>
          <option v-for="member in ownershipCandidates" :key="member.user_id" :value="member.user_id">
            {{ member.name || member.login }} ({{ roleLabel(member.role) }})
          </option>
        </select>
        <button class="qe-btn-warning px-4" :disabled="isSubmitting || !transferOwnerUserId" @click="transferOwnership">Передать</button>
      </div>
    </section>

    <section v-if="hasCurrentWorkspace && isOwner && !isCurrentWorkspaceDefault" class="rounded-2xl border border-red-200 dark:border-red-900 bg-red-50/60 dark:bg-red-950/20 p-4 sm:p-5 space-y-3">
      <h2 class="text-lg font-semibold text-red-700 dark:text-red-300">Удаление рабочего пространства</h2>
      <p class="text-sm text-red-700/80 dark:text-red-300/80">
        Для подтверждения введите точное название: <strong>{{ currentWorkspace?.name || '—' }}</strong>
      </p>
      <div class="flex flex-col sm:flex-row gap-3">
        <input v-model.trim="deleteConfirmName" type="text" class="qe-input flex-1" />
        <button class="qe-btn-danger px-4" :disabled="isSubmitting" @click="deleteWorkspace">Удалить пространство</button>
      </div>
    </section>

  </div>
</template>
