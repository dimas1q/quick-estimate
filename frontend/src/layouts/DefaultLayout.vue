<!-- frontend/src/layouts/DefaultLayout.vue -->
<script setup>
import { ref, watch, nextTick } from 'vue'
import { useAuthStore } from '@/store/auth'
import { useRoute, useRouter } from 'vue-router'
import { onClickOutside } from '@vueuse/core'
import { LogOut, User, Settings, ChevronDown } from 'lucide-vue-next'
import Sidebar from '@/components/Sidebar.vue'

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
  <div class="flex flex-col h-screen bg-gray-50 text-gray-900">
    <!-- HEADER -->
    <header class="bg-white border-b shadow-sm px-6 py-3 flex justify-between items-center">
    <RouterLink to="/" class="text-xl font-bold text-blue-600">Quick Estimate</RouterLink>

    <div class="flex items-center gap-4">
      <RouterLink v-if="!auth.user" to="/login" class="text-sm text-blue-600 hover:underline">Войти</RouterLink>

      <div v-else class="relative" ref="menuRef">
        <button @click="showMenu = !showMenu"
          class="flex items-center gap-2 px-3 py-1.5 text-sm rounded-md bg-gray-100 hover:bg-blue-100 transition-all">
          <User class="w-4 h-4 text-gray-700" />
          <span class="text-gray-700">{{ auth.user.login }}</span>
          <ChevronDown
            class="w-3 h-3 text-gray-500 transition-transform duration-200"
            :class="{ 'rotate-180': showMenu }"
          />
        </button>

        <div v-show="showMenu"
          class="absolute right-0 mt-2 w-42 bg-white rounded-xl shadow-xl ring-1 ring-black/5 z-50 text-sm animate-fade-in">
          <RouterLink to="/profile"
            class="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-100 transition-all">
            <Settings class="w-4 h-4 text-gray-600" />
            <span>Настройки</span>
          </RouterLink>

          <button @click="logout"
            class="flex items-center gap-2 w-full text-left px-4 py-2 text-red-500 hover:bg-red-50 transition-all">
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
      <main class="flex-1 overflow-y-auto p-4">
        <slot /> <!-- Контент приходит из App.vue -->
      </main>
    </div>
  </div>
</template>
