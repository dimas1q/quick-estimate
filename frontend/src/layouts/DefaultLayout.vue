<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useAuthStore } from '@/store/auth'
import { useRoute, useRouter } from 'vue-router'
import Sidebar from '@/components/Sidebar.vue'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const showMenu = ref(false)

function logout() {
  showMenu.value = false
  auth.logout()
  router.push('/login')
}

watch(() => route.path, () => {
  showMenu.value = false
})

function handleClickOutside(event) {
  if (!showMenu.value) return

  const menu = document.getElementById('user-menu')
  if (menu && !menu.contains(event.target)) {
    showMenu.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="flex flex-col h-screen bg-gray-50 text-gray-900">
    <!-- HEADER -->
    <header class="bg-white border-b shadow-sm px-6 py-3 flex justify-between items-center">
      <RouterLink to="/" class="text-xl font-bold text-blue-600">Quick Estimate</RouterLink>
      <div class="flex items-center gap-4">
        <RouterLink v-if="!auth.user" to="/login" class="text-sm text-blue-600 hover:underline">Войти</RouterLink>
        <div v-else class="relative" id="user-menu">
          <button @click="showMenu = !showMenu"
            class="flex items-center gap-2 px-3 py-1.5 text-sm rounded-md bg-gray-100 hover:bg-blue-100 transition-all">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-700" viewBox="0 0 20 20"
              fill="currentColor">
              <path d="M10 2a5 5 0 100 10 5 5 0 000-10zM2 18a8 8 0 0116 0H2z" />
            </svg>
            <span class="text-gray-700">{{ auth.user.email }}</span>
            <svg class="w-3 h-3 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <div v-show="showMenu"
            class="absolute right-0 mt-2 w-42 bg-white rounded-lg shadow-lg border z-50 text-sm overflow-hidden transition-all">
            <RouterLink to="/profile"
              class="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-100 transition-all">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-600" fill="none" viewBox="0 0 24 24"
                stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M5.121 17.804A4 4 0 019 16h6a4 4 0 013.879 1.804M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span>Настройки</span>
            </RouterLink>

            <button @click="logout"
              class="flex items-center gap-2 w-full text-left px-4 py-2 text-red-500 hover:bg-red-50 transition-all">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24"
                stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1m0-10V5m0 0H5a2 2 0 00-2 2v10a2 2 0 002 2h6" />
              </svg>
              <span>Выйти</span>
            </button>
          </div>
        </div>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      <!-- SIDEBAR только для авторизованных -->
      <Sidebar v-if="auth.user" />

      <!-- MAIN -->
      <main class="flex-1 overflow-y-auto">
        <router-view />
      </main>
    </div>
  </div>
</template>
