<!-- frontend/src/layouts/DefaultLayout.vue -->
<script setup>
import { ref, watch, nextTick } from 'vue'
import { useAuthStore } from '@/store/auth'
import { useRoute, useRouter } from 'vue-router'
import { onClickOutside } from '@vueuse/core'
import { LogOut, User, Settings, ChevronDown } from 'lucide-vue-next'
import Sidebar from '@/components/Sidebar.vue'
import ThemeSlider from '@/components/ThemeSlider.vue'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const showMenu = ref(false)
const menuRef = ref(null)
const showSidebar = ref(false)

watch(
  () => auth.user,
  async (user) => {
    if (user) {
      await nextTick()
      showSidebar.value = true
    } else {
      showSidebar.value = false
    }
  },
  { immediate: true }
)

async function logout() {
  showMenu.value = false
  await router.push('/login')
  await nextTick()
  auth.logout()
}

watch(() => route.path, () => {
  showMenu.value = false
})

onClickOutside(menuRef, () => {
  showMenu.value = false
})
</script>

<template>
  <div class="flex flex-col h-screen bg-gray-50 dark:bg-qe-black text-gray-900 dark:text-gray-100">
    <!-- HEADER -->
    <header
      class="bg-white/80 dark:bg-qe-black3 border-b border-gray-200 dark:border-qe-black2 shadow-sm px-6 py-3 flex justify-between items-center">
      <div class="flex items-center gap-3">
        <RouterLink to="/" class="flex items-center gap-2 text-xl font-extrabold text-blue-600 dark:text-blue-600">
          <img src="/vite.svg" class="h-7 w-7" alt="QuickEstimate" />
          QuickEstimate
        </RouterLink>
      </div>

      <div class="flex items-center gap-4">
        <ThemeSlider />

        <div class="relative" ref="menuRef">
          <!-- Кнопка вызова меню -->
          <button @click="showMenu = !showMenu"
            class="flex items-center gap-3 px-3 py-1 text-sm rounded-xl bg-gray-100 dark:bg-qe-black2 border border-gray-200 dark:border-qe-black2 hover:bg-blue-50 dark:hover:bg-blue-900 transition-all min-w-[140px]">
            <div
              class="w-6 h-6 rounded-full flex items-center justify-center bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 font-bold text-base uppercase select-none">
              {{ (auth.user.name || auth.user.login || auth.user.email).slice(0, 2) }}
            </div>
            <span class="font-semibold text-gray-800 dark:text-gray-200 truncate">{{ auth.user.name || auth.user.login
              }}</span>
            <ChevronDown class="w-4 h-4 text-gray-500 transition-transform duration-200"
              :class="{ 'rotate-180': showMenu }" />
          </button>

          <!-- Выпадающее меню -->
          <div v-show="showMenu"
            class="absolute right-0 mt-2 min-w-[200px] bg-white dark:bg-qe-black2 rounded-2xl shadow-2xl ring-1 ring-black/10 dark:ring-white/10 z-50 text-sm animate-fade-in px-0.5 py-2 border border-gray-100 dark:border-qe-black2">

            <!-- Крупное имя/логин, мелкий email -->
            <div class="px-5 pb-2 mb-2 flex flex-col gap-0.5 border-b border-gray-100 dark:border-qe-black2">
              <span class="font-semibold text-base text-gray-800 dark:text-gray-100">
                {{ auth.user.name || auth.user.login }}
              </span>
              <span v-if="auth.user.email" class="text-xs text-gray-500 dark:text-gray-400">{{ auth.user.email }}</span>
            </div>
            <RouterLink to="/profile"
              class="flex items-center gap-2 px-5 py-2 text-gray-700 dark:text-gray-200 rounded-xl hover:bg-gray-50 dark:hover:bg-blue-950 transition-all">
              <Settings class="w-4 h-4 text-gray-500" />
              <span>Профиль</span>
            </RouterLink>
            <button @click="logout"
              class="flex items-center gap-2 px-5 py-2 text-red-700 dark:text-red-500 rounded-xl w-full hover:bg-red-50 dark:hover:bg-red-900/20 mt-1 transition-all">
              <LogOut class="w-4 h-4" />
              <span>Выйти</span>
            </button>
          </div>
        </div>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden">
      <!-- SIDEBAR -->
      <Sidebar v-if="auth.user && showSidebar" />

      <!-- MAIN -->
      <main class="flex-1 overflow-y-auto dark:bg-qe-black3 bg-gray-50 p-4">
        <slot />
      </main>
    </div>
  </div>
</template>
