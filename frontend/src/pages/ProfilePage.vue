<template>
    <div class="max-w-4xl mx-auto py-10 px-6">
      <h1 class="text-3xl font-semibold mb-8 text-gray-900">Настройки профиля</h1>
  
      <div class="flex border-b border-gray-200 mb-6 space-x-8">
        <RouterLink
          to="/profile/account"
          class="pb-2 text-sm font-medium transition"
          :class="route.path.includes('account') ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600 hover:text-blue-500'"
        >
          Аккаунт
        </RouterLink>
  
        <RouterLink
          to="/profile/password"
          class="pb-2 text-sm font-medium transition"
          :class="route.path.includes('password') ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600 hover:text-blue-500'"
        >
          Пароль
        </RouterLink>
      </div>
  
      <RouterView />
    </div>
  </template>
  
  <script setup>
  import { useRoute } from 'vue-router'
  const route = useRoute()
  </script>
  