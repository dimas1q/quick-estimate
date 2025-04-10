<template>
  <div class="min-h-screen bg-gray-50 text-gray-900">
    <header class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center">
        <router-link to="/" class="text-xl font-bold text-blue-600">
          Quick Estimate
        </router-link>

        <nav class="space-x-4">
          <router-link
            to="/estimates"
            class="text-sm hover:underline"
            active-class="font-semibold text-blue-700"
          >
            Сметы
          </router-link>
          <router-link
            to="/templates"
            class="text-sm hover:underline"
            active-class="font-semibold text-blue-700"
          >
            Шаблоны
          </router-link>
          <router-link
            to="/login"
            class="text-sm hover:underline"
            active-class="font-semibold text-blue-700"
          >
            Войти
          </router-link>
        </nav>
      </div>
    </header>

    <main class="max-w-6xl mx-auto px-4 py-6">
      <router-view />
    </main>
  </div>
</template>
