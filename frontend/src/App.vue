<!-- frontend/src/App.vue -->
<script setup>
import { useRoute } from 'vue-router'
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import AuthLayout from '@/layouts/AuthLayout.vue'

const route = useRoute()
</script>

<template>
  <Transition name="layout-fade" mode="out-in">
    <component :is="route.meta.layout || DefaultLayout">
      <RouterView v-slot="{ Component }">
        <Transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </component>
  </Transition>
</template>

<style>
.layout-fade-enter-active,
.layout-fade-leave-active {
  transition: opacity 0.2s ease-in-out;
}

.layout-fade-enter-from,
.layout-fade-leave-to {
  opacity: 0.2s;
}

.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.2s ease;
}

.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0.2s;
}
</style>
