<script setup>
import { ref, onMounted } from 'vue'
import { Sun, Moon } from 'lucide-vue-next'

const isDark = ref(false)

onMounted(() => {
  isDark.value = document.documentElement.classList.contains('dark')
})

function toggleTheme() {
  isDark.value = !isDark.value
  if (isDark.value) {
    document.documentElement.classList.add('dark')
    localStorage.setItem('theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('theme', 'light')
  }
}
</script>

<template>
    <button @click="toggleTheme"
        class="relative w-16 h-8 flex items-center rounded-full bg-gray-100 dark:bg-gray-700 transition-colors border-2 border-transparent  outline-none"
        :aria-label="isDark ? 'Светлая тема' : 'Темная тема'" tabindex="0" style="min-width:56px; min-height:32px;">
        <!-- Солнце (слева, поверх бегунка) -->
        <Sun class="absolute left-1.5 top-1/2 -translate-y-1/2 w-5 h-5 text-yellow-400 transition-opacity duration-200 pointer-events-none"
            :class="isDark ? 'opacity-0' : 'opacity-100'" :stroke-width="2" style="z-index:3" />
        <!-- Луна (справа, поверх бегунка) -->
        <Moon
            class="absolute right-1.5 top-1/2 -translate-y-1/2 w-5 h-5 text-blue-400 transition-opacity duration-200 pointer-events-none"
            :class="isDark ? 'opacity-100' : 'opacity-0'" :stroke-width="2" style="z-index:3" />
        <!-- Бегунок -->
        <span
            class="absolute left-1 w-6 h-6 rounded-full  transition-all duration-200 bg-gray-200 dark:bg-gray-900"
            :class="isDark ? 'translate-x-7' : 'translate-x-0'" style="z-index:2"></span>
    </button>
</template>
