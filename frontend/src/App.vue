<!-- frontend/src/App.vue -->
<script setup>
import { useRoute } from 'vue-router'
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import AuthLayout from '@/layouts/AuthLayout.vue'

const route = useRoute()
</script>

<template>
  <Transition name="layout-fade" mode="out-in">
    <component :is="route.meta.layout || DefaultLayout" :key="route.meta.layout?.name || 'default'">
      <RouterView v-slot="{ Component }">
        <Transition name="page-fade" mode="out-in">
          <component :is="Component" :key="route.fullPath" />
        </Transition>
      </RouterView>
    </component>
  </Transition>
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
