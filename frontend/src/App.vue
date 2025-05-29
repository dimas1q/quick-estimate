<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import AuthLayout from '@/layouts/AuthLayout.vue'

const route = useRoute()
const auth = useAuthStore()

const resolveLayout = computed(() => {
  if (!auth.user) return AuthLayout
  return route.meta.layout || DefaultLayout
})

const resolveLayoutName = computed(() => {
  if (!auth.user) return 'auth'
  return route.meta.layout?.name || 'default'
})
</script>

<template>
  <div v-if="auth.loading" class="min-h-screen flex items-center justify-center bg-gray-50">
    <span class="text-gray-400 text-sm">Загрузка...</span>
  </div>
  <template v-else>
    <Transition name="layout-fade" mode="out-in">
      <component :is="resolveLayout" :key="resolveLayoutName">
        <RouterView v-slot="{ Component }">
          <Transition name="page-fade" mode="out-in">
            <component :is="Component" :key="route.fullPath" />
          </Transition>
        </RouterView>
      </component>
    </Transition>
  </template>
</template>

<style>
.layout-fade-enter-active,
.layout-fade-leave-active {
  transition: opacity 120ms ease-in-out;
}

.layout-fade-enter-from,
.layout-fade-leave-to {
  opacity: 0;
}

.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 100ms ease-in;
}

.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
}
</style>
