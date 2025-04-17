<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useAuthStore } from '@/store/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

const showMenu = ref(false)

function logout() {
  showMenu.value = false
  auth.logout()
  router.push('/login')
}

// Закрытие меню при клике вне блока
function handleClickOutside(event) {
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
  <div class="min-h-screen bg-gray-50 text-gray-900">
    <header class="bg-white border-b shadow-sm px-6 py-3 flex justify-between items-center">
      <!-- Левая часть -->
      <div class="flex items-center ">
        <RouterLink to="/" class="text-xl font-bold text-blue-600">Quick Estimate</RouterLink>

        <!-- Контейнер с навигацией -->
        <div class="flex items-center gap-2 ml-8">
          <RouterLink to="/estimates" class="text-s font-semibold text-gray-700 hover:text-blue-600"
            active-class="font-semibold text-blue-700">Сметы</RouterLink>
          <RouterLink to="/templates" class="text-s font-semibold text-gray-700 hover:text-blue-600"
            active-class="font-semibold text-blue-700">Шаблоны</RouterLink>
        </div>
      </div>

      <!-- Правая часть -->
      <div class="flex items-center gap-4">
        <RouterLink v-if="!auth.user" to="/login" class="text-sm text-blue-600 hover:underline">Войти</RouterLink>

        <div v-else class="relative" id="user-menu">
          <button @click="showMenu = !showMenu"
            class="flex items-center gap-2 px-3 py-1 text-sm rounded-md bg-gray-100 hover:bg-blue-100 transition text-s">
            👤 {{ auth.user.email }}
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <div v-show="showMenu"
            class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-xl border z-50 transition-all duration-200 text-sm">
            <RouterLink to="/profile" class="block px-4 py-2 text-gray-700 hover:bg-gray-100 transition">
              ⚙️ Настройки
            </RouterLink>
            <button @click="logout" class="w-full text-left px-4 py-2 text-red-500 hover:bg-red-50 transition">
              🚪 Выйти
            </button>
          </div>
        </div>
      </div>
    </header>
    <main class="container max-w-6xl mx-auto px-4 py-6">
      <router-view />
    </main>
  </div>
</template>