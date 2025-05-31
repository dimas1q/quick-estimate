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
  <div class="flex flex-col h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100">
    <!-- HEADER -->
    <header
      class="bg-white/80 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 shadow-sm px-6 py-3 flex justify-between items-center">
      <div class="flex items-center gap-3">
        <RouterLink to="/" class="flex items-center gap-2 text-xl font-extrabold text-blue-600 dark:text-blue-400">
          <img src="/vite.svg" class="h-7 w-7" alt="QuickEstimate" />
          QuickEstimate
        </RouterLink>
      </div>

      <div class="flex items-center gap-4">
        <ThemeSlider />
        <RouterLink v-if="!auth.user" to="/login" class="text-sm text-blue-600 hover:underline">Войти</RouterLink>

        <div v-else class="relative" ref="menuRef">
          <button @click="showMenu = !showMenu"
            class="flex items-center gap-2 px-3 py-1.5 text-sm rounded-md bg-gray-100 dark:bg-gray-800 hover:bg-blue-100 transition-all">
            <User class="w-4 h-4" />
            <span>{{ auth.user.login }}</span>
            <ChevronDown class="w-3 h-3 text-gray-500 transition-transform duration-200"
              :class="{ 'rotate-180': showMenu }" />
          </button>

          <div v-show="showMenu"
            class="absolute right-0 mt-2 w-42 bg-white dark:bg-gray-900 rounded-xl shadow-xl ring-1 ring-black/10 dark:ring-white/10 z-50 text-sm animate-fade-in">
            <RouterLink to="/profile"
              class="flex items-center gap-2 px-4 py-2 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-all">
              <Settings class="w-4 h-4 text-gray-600" />
              <span>Настройки</span>
            </RouterLink>

            <button @click="logout"
              class="flex items-center gap-2 px-4 py-2 text-red-700 dark:text-red-700 w-full hover:bg-gray-100 dark:hover:bg-gray-800 transition-all">
              <LogOut class="w-4 h-4 " />
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
      <main class="flex-1 overflow-y-auto dark:bg-gray-900 bg-gray-50 p-4">
        <slot />
      </main>
    </div>
  </div>
</template>
