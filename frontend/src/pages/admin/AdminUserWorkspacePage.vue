<template>
  <div class="max-w-6xl mx-auto px-4 py-8 space-y-6">
    <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Управление данными пользователя</h1>
        <p v-if="user" class="text-sm text-gray-500 dark:text-gray-400">
          {{ user.login }} · {{ user.email }}
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button class="qe-btn-secondary px-4" @click="goBack">Назад к пользователям</button>
        <button class="qe-btn px-4" @click="reloadAll">Обновить</button>
      </div>
    </div>

    <div class="inline-flex bg-gray-100 dark:bg-qe-black2 rounded-xl p-1 gap-1">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        class="px-4 py-2 rounded-lg text-sm font-semibold transition"
        :class="activeTab === tab.value ? 'bg-white dark:bg-qe-black3 text-blue-600 shadow-sm' : 'text-gray-500 hover:text-blue-600'"
        @click="activeTab = tab.value"
      >
        {{ tab.label }}
      </button>
    </div>

    <section class="rounded-2xl border border-gray-200 dark:border-qe-black2 bg-white dark:bg-qe-black3 p-4 sm:p-5 space-y-4">
      <div class="flex items-center justify-between gap-2">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Профиль пользователя</h2>
        <button class="qe-btn px-4" :disabled="savingProfile || loading" @click="saveUserProfile">
          Сохранить профиль
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-xs font-semibold mb-1">Логин</label>
          <input v-model="userForm.login" class="qe-input w-full" type="text" autocomplete="off" />
        </div>
        <div>
          <label class="block text-xs font-semibold mb-1">Электронная почта</label>
          <input v-model="userForm.email" class="qe-input w-full" type="email" autocomplete="off" />
        </div>
        <div>
          <label class="block text-xs font-semibold mb-1">Имя</label>
          <input v-model="userForm.name" class="qe-input w-full" type="text" autocomplete="off" />
        </div>
        <div>
          <label class="block text-xs font-semibold mb-1">Компания</label>
          <input v-model="userForm.company" class="qe-input w-full" type="text" autocomplete="off" />
        </div>
      </div>
    </section>

    <section v-if="activeTab === 'clients'" class="space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold">Клиенты</h2>
        <button class="qe-btn px-4" @click="openCreateClient">Создать клиента</button>
      </div>
      <div class="rounded-2xl border border-gray-200 dark:border-qe-black2 bg-white dark:bg-qe-black3 overflow-hidden">
        <table class="min-w-full text-sm">
          <thead class="bg-gray-50 dark:bg-qe-black2 text-gray-600 dark:text-gray-300">
            <tr>
              <th class="px-4 py-3 text-left font-semibold">Имя</th>
              <th class="px-4 py-3 text-left font-semibold">Компания</th>
              <th class="px-4 py-3 text-left font-semibold">Контакты</th>
              <th class="px-4 py-3 text-right font-semibold">Действия</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="client in clients" :key="client.id" class="border-t border-gray-100 dark:border-qe-black2">
              <td class="px-4 py-3 font-medium text-gray-900 dark:text-white">{{ client.name }}</td>
              <td class="px-4 py-3">{{ client.company || '—' }}</td>
              <td class="px-4 py-3">{{ client.email || client.phone || '—' }}</td>
              <td class="px-4 py-3">
                <div class="flex justify-end gap-2">
                  <button class="qe-btn-secondary px-3 py-1 text-xs" @click="openEditClient(client)">Редактировать</button>
                  <button class="qe-btn-danger px-3 py-1 text-xs" @click="deleteClient(client)">Удалить</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="clients.length === 0" class="text-sm text-gray-500 dark:text-gray-400">Клиенты отсутствуют.</div>
    </section>

    <section v-if="activeTab === 'templates'" class="space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold">Шаблоны</h2>
        <button class="qe-btn px-4" @click="openCreateTemplate">Создать шаблон</button>
      </div>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <article
          v-for="template in templates"
          :key="template.id"
          class="rounded-2xl border border-gray-200 dark:border-qe-black2 bg-white dark:bg-qe-black3 p-4 shadow-sm"
        >
          <div class="flex items-start justify-between gap-3">
            <div>
              <h3 class="font-semibold text-gray-900 dark:text-white">{{ template.name }}</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">{{ template.description || 'Без описания' }}</p>
              <p class="text-xs text-gray-500 mt-2">Позиции: {{ template.items?.length || 0 }}</p>
            </div>
            <div class="flex gap-2">
              <button class="qe-btn-secondary px-3 py-1 text-xs" @click="openEditTemplate(template)">Редактировать</button>
              <button class="qe-btn-danger px-3 py-1 text-xs" @click="deleteTemplate(template)">Удалить</button>
            </div>
          </div>
        </article>
      </div>
      <div v-if="templates.length === 0" class="text-sm text-gray-500 dark:text-gray-400">Шаблоны отсутствуют.</div>
    </section>

    <section v-if="activeTab === 'estimates'" class="space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold">Сметы</h2>
        <button class="qe-btn px-4" @click="openCreateEstimate">Создать смету</button>
      </div>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <article
          v-for="estimate in estimates"
          :key="estimate.id"
          class="rounded-2xl border border-gray-200 dark:border-qe-black2 bg-white dark:bg-qe-black3 p-4 shadow-sm"
        >
          <div class="flex items-start justify-between gap-3">
            <div>
              <h3 class="font-semibold text-gray-900 dark:text-white">{{ estimate.name }}</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">
                Клиент: {{ estimate.client?.name || '—' }} · Статус: {{ statusLabel(estimate.status) }}
              </p>
              <p class="text-xs text-gray-500 mt-2">Позиций: {{ estimate.items?.length || 0 }}</p>
            </div>
            <div class="flex gap-2">
              <button class="qe-btn-secondary px-3 py-1 text-xs" @click="openEditEstimate(estimate)">Редактировать</button>
              <button class="qe-btn-danger px-3 py-1 text-xs" @click="deleteEstimate(estimate)">Удалить</button>
            </div>
          </div>
        </article>
      </div>
      <div v-if="estimates.length === 0" class="text-sm text-gray-500 dark:text-gray-400">Сметы отсутствуют.</div>
    </section>

    <Teleport to="body">
      <transition name="modal-fade">
        <div v-if="showClientModal" class="fixed inset-0 z-[80]">
          <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="closeClientModal" />
          <div class="relative flex min-h-full items-center justify-center px-4 py-6">
            <div class="w-full max-w-2xl bg-white dark:bg-qe-black2 rounded-2xl shadow-2xl p-6 space-y-4 border border-gray-200 dark:border-qe-black3">
              <h3 class="text-lg font-bold">{{ editingClientId ? 'Редактирование клиента' : 'Создание клиента' }}</h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="block text-xs font-semibold mb-1">Имя</label>
                  <input v-model="clientForm.name" class="qe-input w-full" type="text" />
                </div>
                <div>
                  <label class="block text-xs font-semibold mb-1">Компания</label>
                  <input v-model="clientForm.company" class="qe-input w-full" type="text" />
                </div>
                <div>
                  <label class="block text-xs font-semibold mb-1">Email</label>
                  <input v-model="clientForm.email" class="qe-input w-full" type="email" />
                </div>
                <div>
                  <label class="block text-xs font-semibold mb-1">Телефон</label>
                  <input v-model="clientForm.phone" class="qe-input w-full" type="text" />
                </div>
              </div>
              <div class="flex justify-end gap-2">
                <button class="qe-btn-secondary px-4" @click="closeClientModal">Отмена</button>
                <button class="qe-btn px-4" :disabled="saving" @click="saveClient">Сохранить</button>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>

    <Teleport to="body">
      <transition name="modal-fade">
        <div v-if="showTemplateModal" class="fixed inset-0 z-[80]">
          <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="closeTemplateModal" />
          <div class="relative flex min-h-full items-center justify-center px-4 py-6">
            <div class="w-full max-w-6xl max-h-[90vh] overflow-auto bg-white dark:bg-qe-black2 rounded-2xl shadow-2xl p-6 space-y-4 border border-gray-200 dark:border-qe-black3">
              <h3 class="text-lg font-bold">{{ editingTemplateId ? 'Редактирование шаблона' : 'Создание шаблона' }}</h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="block text-xs font-semibold mb-1">Название</label>
                  <input v-model="templateForm.name" class="qe-input w-full" type="text" />
                </div>
                <div>
                  <label class="block text-xs font-semibold mb-1">Описание</label>
                  <input v-model="templateForm.description" class="qe-input w-full" type="text" />
                </div>
              </div>
              <label class="inline-flex items-center gap-2 text-sm font-medium">
                <input v-model="templateForm.use_internal_price" type="checkbox" class="h-4 w-4 accent-blue-600" />
                Использовать внутреннюю цену
              </label>

              <AdminItemsTable v-model="templateForm.items" :show-internal-price="templateForm.use_internal_price" />

              <div class="flex justify-end gap-2">
                <button class="qe-btn-secondary px-4" @click="closeTemplateModal">Отмена</button>
                <button class="qe-btn px-4" :disabled="saving" @click="saveTemplate">Сохранить</button>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>

    <Teleport to="body">
      <transition name="modal-fade">
        <div v-if="showEstimateModal" class="fixed inset-0 z-[80]">
          <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="closeEstimateModal" />
          <div class="relative flex min-h-full items-center justify-center px-4 py-6">
            <div class="w-full max-w-6xl max-h-[90vh] overflow-auto bg-white dark:bg-qe-black2 rounded-2xl shadow-2xl p-6 space-y-4 border border-gray-200 dark:border-qe-black3">
              <h3 class="text-lg font-bold">{{ editingEstimateId ? 'Редактирование сметы' : 'Создание сметы' }}</h3>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="block text-xs font-semibold mb-1">Название</label>
                  <input v-model="estimateForm.name" class="qe-input w-full" type="text" />
                </div>
                <div>
                  <label class="block text-xs font-semibold mb-1">Ответственный</label>
                  <input v-model="estimateForm.responsible" class="qe-input w-full" type="text" />
                </div>
                <div>
                  <label class="block text-xs font-semibold mb-1">Клиент</label>
                  <select v-model="estimateForm.client_id" class="qe-input w-full">
                    <option :value="null">Без клиента</option>
                    <option v-for="c in clients" :key="c.id" :value="c.id">{{ c.name }}</option>
                  </select>
                </div>
                <div>
                  <label class="block text-xs font-semibold mb-1">Статус</label>
                  <select v-model="estimateForm.status" class="qe-input w-full">
                    <option v-for="option in statusOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                  </select>
                </div>
                <div>
                  <label class="block text-xs font-semibold mb-1">Дата и время</label>
                  <input v-model="estimateForm.event_datetime" class="qe-input w-full" type="datetime-local" />
                </div>
                <div>
                  <label class="block text-xs font-semibold mb-1">Место проведения</label>
                  <input v-model="estimateForm.event_place" class="qe-input w-full" type="text" />
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <label class="inline-flex items-center gap-2 text-sm font-medium">
                  <input v-model="estimateForm.vat_enabled" type="checkbox" class="h-4 w-4 accent-blue-600" />
                  НДС включен
                </label>
                <label class="inline-flex items-center gap-2 text-sm font-medium">
                  <span>Ставка НДС</span>
                  <input v-model.number="estimateForm.vat_rate" type="number" min="0" max="100" class="qe-input w-20" />
                </label>
                <label class="inline-flex items-center gap-2 text-sm font-medium">
                  <input v-model="estimateForm.use_internal_price" type="checkbox" class="h-4 w-4 accent-blue-600" />
                  Использовать внутреннюю цену
                </label>
              </div>

              <AdminItemsTable v-model="estimateForm.items" :show-internal-price="estimateForm.use_internal_price" />

              <div class="flex justify-end gap-2">
                <button class="qe-btn-secondary px-4" @click="closeEstimateModal">Отмена</button>
                <button class="qe-btn px-4" :disabled="saving" @click="saveEstimate">Сохранить</button>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import AdminItemsTable from '@/components/admin/AdminItemsTable.vue'
import { useAdminStore } from '@/store/admin'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const store = useAdminStore()

const tabs = [
  { value: 'clients', label: 'Клиенты' },
  { value: 'templates', label: 'Шаблоны' },
  { value: 'estimates', label: 'Сметы' }
]

const statusOptions = [
  { value: 'draft', label: 'Черновик' },
  { value: 'sent', label: 'Отправлена' },
  { value: 'approved', label: 'Согласована' },
  { value: 'paid', label: 'Оплачена' },
  { value: 'cancelled', label: 'Отменена' }
]

const activeTab = ref('clients')
const loading = ref(false)
const saving = ref(false)
const savingProfile = ref(false)

const user = ref(null)
const clients = ref([])
const templates = ref([])
const estimates = ref([])

const showClientModal = ref(false)
const showTemplateModal = ref(false)
const showEstimateModal = ref(false)

const editingClientId = ref(null)
const editingTemplateId = ref(null)
const editingEstimateId = ref(null)

const userForm = reactive({
  login: '',
  email: '',
  name: '',
  company: ''
})

const clientForm = reactive({
  name: '',
  company: '',
  email: '',
  phone: ''
})

const templateForm = reactive({
  name: '',
  description: '',
  use_internal_price: true,
  items: []
})

const estimateForm = reactive({
  name: '',
  responsible: '',
  client_id: null,
  event_datetime: '',
  event_place: '',
  status: 'draft',
  vat_enabled: true,
  vat_rate: 20,
  use_internal_price: true,
  read_only: false,
  items: []
})

const userId = Number(route.params.userId)

function statusLabel(value) {
  return statusOptions.find(s => s.value === value)?.label || value
}

function goBack() {
  router.push('/admin/users')
}

function toInputDateTime(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function toIsoOrNull(value) {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date.toISOString()
}

function fillUserForm(value) {
  Object.assign(userForm, {
    login: value?.login || '',
    email: value?.email || '',
    name: value?.name || '',
    company: value?.company || ''
  })
}

function normalizeItems(items, useInternalPrice = true) {
  return (items || []).map((item) => ({
    name: item.name || '',
    description: item.description || '',
    quantity: Number(item.quantity || 0),
    unit: item.unit || 'шт',
    internal_price: useInternalPrice ? Number(item.internal_price || 0) : 1,
    external_price: Number(item.external_price || 0),
    category: item.category || ''
  }))
}

function resetClientForm() {
  editingClientId.value = null
  Object.assign(clientForm, { name: '', company: '', email: '', phone: '' })
}

function resetTemplateForm() {
  editingTemplateId.value = null
  Object.assign(templateForm, {
    name: '',
    description: '',
    use_internal_price: true,
    items: []
  })
}

function resetEstimateForm() {
  editingEstimateId.value = null
  Object.assign(estimateForm, {
    name: '',
    responsible: '',
    client_id: null,
    event_datetime: '',
    event_place: '',
    status: 'draft',
    vat_enabled: true,
    vat_rate: 20,
    use_internal_price: true,
    read_only: false,
    items: []
  })
}

function openCreateClient() {
  resetClientForm()
  showClientModal.value = true
}

function openEditClient(client) {
  editingClientId.value = client.id
  Object.assign(clientForm, {
    name: client.name || '',
    company: client.company || '',
    email: client.email || '',
    phone: client.phone || ''
  })
  showClientModal.value = true
}

function closeClientModal() {
  if (saving.value) return
  showClientModal.value = false
}

function openCreateTemplate() {
  resetTemplateForm()
  showTemplateModal.value = true
}

function openEditTemplate(template) {
  editingTemplateId.value = template.id
  Object.assign(templateForm, {
    name: template.name || '',
    description: template.description || '',
    use_internal_price: template.use_internal_price ?? true,
    items: normalizeItems(template.items || [], template.use_internal_price ?? true)
  })
  showTemplateModal.value = true
}

function closeTemplateModal() {
  if (saving.value) return
  showTemplateModal.value = false
}

function openCreateEstimate() {
  resetEstimateForm()
  showEstimateModal.value = true
}

function openEditEstimate(estimate) {
  editingEstimateId.value = estimate.id
  Object.assign(estimateForm, {
    name: estimate.name || '',
    responsible: estimate.responsible || '',
    client_id: estimate.client_id || null,
    event_datetime: toInputDateTime(estimate.event_datetime),
    event_place: estimate.event_place || '',
    status: estimate.status || 'draft',
    vat_enabled: estimate.vat_enabled ?? true,
    vat_rate: estimate.vat_rate ?? 20,
    use_internal_price: estimate.use_internal_price ?? true,
    read_only: estimate.read_only ?? false,
    items: normalizeItems(estimate.items || [], estimate.use_internal_price ?? true)
  })
  showEstimateModal.value = true
}

function closeEstimateModal() {
  if (saving.value) return
  showEstimateModal.value = false
}

async function reloadAll() {
  loading.value = true
  try {
    const [userData, clientsData, templatesData, estimatesData] = await Promise.all([
      store.getUser(userId),
      store.fetchUserClients(userId, { page: 1, limit: 200 }),
      store.fetchUserTemplates(userId, { page: 1, limit: 200 }),
      store.fetchUserEstimates(userId, { page: 1, limit: 200 })
    ])

    user.value = userData
    fillUserForm(userData)
    clients.value = clientsData.items || []
    templates.value = templatesData.items || []
    estimates.value = estimatesData.items || []
  } catch (e) {
    toast.error(e?.response?.data?.detail || 'Не удалось загрузить данные пользователя')
  } finally {
    loading.value = false
  }
}

async function saveUserProfile() {
  const login = userForm.login.trim()
  const email = userForm.email.trim()

  if (!login || login.length < 3) {
    toast.error('Логин должен быть не короче 3 символов')
    return
  }

  if (!email) {
    toast.error('Электронная почта обязательна')
    return
  }

  savingProfile.value = true
  try {
    const payload = {
      login,
      email,
      name: userForm.name.trim() || null,
      company: userForm.company.trim() || null
    }

    const updatedUser = await store.updateUserProfile(userId, payload)
    user.value = updatedUser
    fillUserForm(updatedUser)
    toast.success('Профиль пользователя обновлен')
  } catch (e) {
    toast.error(e?.response?.data?.detail || 'Не удалось обновить профиль пользователя')
  } finally {
    savingProfile.value = false
  }
}

async function saveClient() {
  if (!clientForm.name.trim()) {
    toast.error('Имя клиента обязательно')
    return
  }

  saving.value = true
  try {
    const payload = {
      name: clientForm.name,
      company: clientForm.company || null,
      email: clientForm.email || null,
      phone: clientForm.phone || null,
      legal_address: null,
      actual_address: null,
      inn: null,
      kpp: null,
      bik: null,
      account: null,
      bank: null,
      corr_account: null
    }

    if (editingClientId.value) {
      await store.updateUserClient(userId, editingClientId.value, payload)
      toast.success('Клиент обновлен')
    } else {
      await store.createUserClient(userId, payload)
      toast.success('Клиент создан')
    }

    await reloadAll()
    showClientModal.value = false
  } catch (e) {
    toast.error(e?.response?.data?.detail || 'Не удалось сохранить клиента')
  } finally {
    saving.value = false
  }
}

async function deleteClient(client) {
  if (!window.confirm(`Удалить клиента «${client.name}»?`)) return

  try {
    await store.deleteUserClient(userId, client.id)
    toast.success('Клиент удален')
    await reloadAll()
  } catch (e) {
    toast.error(e?.response?.data?.detail || 'Не удалось удалить клиента')
  }
}

async function saveTemplate() {
  if (!templateForm.name.trim()) {
    toast.error('Название шаблона обязательно')
    return
  }
  if (!templateForm.items.length) {
    toast.error('Добавьте хотя бы одну позицию в шаблон')
    return
  }

  saving.value = true
  try {
    const payload = {
      name: templateForm.name,
      description: templateForm.description || null,
      use_internal_price: templateForm.use_internal_price,
      items: normalizeItems(templateForm.items, templateForm.use_internal_price)
    }

    if (editingTemplateId.value) {
      await store.updateUserTemplate(userId, editingTemplateId.value, payload)
      toast.success('Шаблон обновлен')
    } else {
      await store.createUserTemplate(userId, payload)
      toast.success('Шаблон создан')
    }

    await reloadAll()
    showTemplateModal.value = false
  } catch (e) {
    toast.error(e?.response?.data?.detail || 'Не удалось сохранить шаблон')
  } finally {
    saving.value = false
  }
}

async function deleteTemplate(template) {
  if (!window.confirm(`Удалить шаблон «${template.name}»?`)) return

  try {
    await store.deleteUserTemplate(userId, template.id)
    toast.success('Шаблон удален')
    await reloadAll()
  } catch (e) {
    toast.error(e?.response?.data?.detail || 'Не удалось удалить шаблон')
  }
}

async function saveEstimate() {
  if (!estimateForm.name.trim()) {
    toast.error('Название сметы обязательно')
    return
  }
  if (!estimateForm.responsible.trim()) {
    toast.error('Ответственный обязателен')
    return
  }
  if (!estimateForm.items.length) {
    toast.error('Добавьте хотя бы одну позицию в смету')
    return
  }

  saving.value = true
  try {
    const payload = {
      name: estimateForm.name,
      client_id: estimateForm.client_id || null,
      responsible: estimateForm.responsible,
      event_datetime: toIsoOrNull(estimateForm.event_datetime),
      event_place: estimateForm.event_place || null,
      status: estimateForm.status,
      vat_enabled: estimateForm.vat_enabled,
      vat_rate: Number(estimateForm.vat_rate || 0),
      use_internal_price: estimateForm.use_internal_price,
      read_only: estimateForm.read_only,
      items: normalizeItems(estimateForm.items, estimateForm.use_internal_price)
    }

    if (editingEstimateId.value) {
      await store.updateUserEstimate(userId, editingEstimateId.value, payload)
      toast.success('Смета обновлена')
    } else {
      await store.createUserEstimate(userId, payload)
      toast.success('Смета создана')
    }

    await reloadAll()
    showEstimateModal.value = false
  } catch (e) {
    toast.error(e?.response?.data?.detail || 'Не удалось сохранить смету')
  } finally {
    saving.value = false
  }
}

async function deleteEstimate(estimate) {
  if (!window.confirm(`Удалить смету «${estimate.name}»?`)) return

  try {
    await store.deleteUserEstimate(userId, estimate.id)
    toast.success('Смета удалена')
    await reloadAll()
  } catch (e) {
    toast.error(e?.response?.data?.detail || 'Не удалось удалить смету')
  }
}

onMounted(() => {
  reloadAll()
})
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
