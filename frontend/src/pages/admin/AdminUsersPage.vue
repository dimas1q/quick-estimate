<template>
  <div class="max-w-6xl mx-auto px-4 py-8 space-y-6">
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Админ-панель: Пользователи</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400">Управление ролями и доступом пользователей.</p>
      </div>
      <div class="flex items-center gap-2">
        <input
          v-model="search"
          class="qe-input w-64"
          type="text"
          autocomplete="off"
          placeholder="Поиск по email/login"
          @keyup.enter="loadUsers(1)"
        />
        <button class="qe-btn px-4" @click="loadUsers(1)" :disabled="isLoading">Найти</button>
      </div>
    </div>

    <div class="rounded-2xl border border-gray-200 dark:border-qe-black2 bg-white dark:bg-qe-black3 shadow-sm overflow-x-auto">
      <table class="min-w-full text-sm">
        <thead class="bg-gray-50 dark:bg-qe-black2 text-gray-600 dark:text-gray-300">
          <tr>
            <th class="px-4 py-3 text-left font-semibold">ID</th>
            <th class="px-4 py-3 text-left font-semibold">Логин</th>
            <th class="px-4 py-3 text-left font-semibold">Email</th>
            <th class="px-4 py-3 text-left font-semibold">Роль</th>
            <th class="px-4 py-3 text-left font-semibold">Статус</th>
            <th class="px-4 py-3 text-right font-semibold">Действия</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="u in store.users"
            :key="u.id"
            class="border-t border-gray-100 dark:border-qe-black2"
          >
            <td class="px-4 py-3 text-gray-500">{{ u.id }}</td>
            <td class="px-4 py-3 font-medium text-gray-900 dark:text-white">{{ u.login }}</td>
            <td class="px-4 py-3 text-gray-700 dark:text-gray-300">{{ u.email }}</td>
            <td class="px-4 py-3">
              <span :class="roleClass(u.is_admin)">{{ u.is_admin ? 'Администратор' : 'Пользователь' }}</span>
            </td>
            <td class="px-4 py-3">
              <span :class="statusClass(u.is_active)">{{ u.is_active ? 'Активен' : 'Отключен' }}</span>
            </td>
            <td class="px-4 py-3 whitespace-nowrap">
              <div class="flex items-center justify-end gap-1.5 whitespace-nowrap">
                <button
                  class="qe-btn-secondary px-2.5 py-1 text-xs whitespace-nowrap"
                  :title="u.is_admin ? 'Снять роль администратора' : 'Назначить администратором'"
                  @click="toggleRole(u)"
                  :disabled="isRowBusy(u.id)"
                >
                  {{ u.is_admin ? 'Снять роль администратора' : 'Назначить администратором' }}
                </button>
                <button
                  class="qe-btn-secondary px-2.5 py-1 text-xs whitespace-nowrap"
                  :title="u.is_active ? 'Отключить пользователя' : 'Активировать пользователя'"
                  @click="toggleActivation(u)"
                  :disabled="isRowBusy(u.id)"
                >
                  {{ u.is_active ? 'Отключить' : 'Включить' }}
                </button>
                <button
                  class="qe-btn px-2.5 py-1 text-xs whitespace-nowrap"
                  title="Открыть управление данными пользователя"
                  @click="openWorkspace(u)"
                  :disabled="isRowBusy(u.id)"
                >
                  Данные
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="!isLoading && store.users.length === 0"
      class="text-center text-gray-400 border border-gray-200 dark:border-qe-black2 p-6 rounded-2xl bg-white/70 dark:bg-qe-black2/80">
      Пользователи не найдены.
    </div>

    <QePagination
      :total="store.usersTotal"
      :per-page="perPage"
      :page="currentPage"
      @update:page="loadUsers"
      class="pt-1"
    />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

import QePagination from '@/components/QePagination.vue'
import { useAdminStore } from '@/store/admin'
import { getApiErrorMessage } from '@/lib/api-error'

const router = useRouter()
const toast = useToast()
const store = useAdminStore()

const perPage = 20
const currentPage = ref(1)
const search = ref('')
const isLoading = ref(false)
const busyUserId = ref(null)

function roleClass(isAdmin) {
  return [
    'inline-flex rounded-full px-2.5 py-1 text-xs font-semibold',
    isAdmin
      ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
      : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
  ]
}

function statusClass(isActive) {
  return [
    'inline-flex rounded-full px-2.5 py-1 text-xs font-semibold',
    isActive
      ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
      : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
  ]
}

async function loadUsers(page = currentPage.value) {
  currentPage.value = page
  isLoading.value = true
  try {
    await store.fetchUsers({
      page,
      limit: perPage,
      search: search.value || undefined
    })
  } catch (e) {
    toast.error(getApiErrorMessage(e, 'Не удалось загрузить пользователей'))
  } finally {
    isLoading.value = false
  }
}

async function toggleRole(user) {
  if (isRowBusy(user.id)) return
  busyUserId.value = user.id
  try {
    await store.updateUserRole(user.id, !user.is_admin)
    toast.success('Роль пользователя обновлена')
    await loadUsers(currentPage.value)
  } catch (e) {
    toast.error(getApiErrorMessage(e, 'Не удалось изменить роль'))
  } finally {
    busyUserId.value = null
  }
}

async function toggleActivation(user) {
  if (isRowBusy(user.id)) return
  busyUserId.value = user.id
  try {
    await store.updateUserActivation(user.id, !user.is_active)
    toast.success('Статус пользователя обновлен')
    await loadUsers(currentPage.value)
  } catch (e) {
    toast.error(getApiErrorMessage(e, 'Не удалось изменить статус'))
  } finally {
    busyUserId.value = null
  }
}

function isRowBusy(userId) {
  return busyUserId.value === userId
}

function openWorkspace(user) {
  router.push(`/admin/users/${user.id}/workspace`)
}

onMounted(() => {
  loadUsers(1)
})
</script>
