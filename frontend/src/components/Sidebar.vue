<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { FileText, Folder, Users, ChevronLeft, ChartNoAxesCombined, Shield, ClipboardCheck, Building2 } from 'lucide-vue-next'
import { useAuthStore } from '@/store/auth'

const route = useRoute()
const auth = useAuthStore()
const collapsed = ref(JSON.parse(localStorage.getItem('sidebar-collapsed')) || false)

function toggleSidebar() {
  collapsed.value = !collapsed.value
  localStorage.setItem('sidebar-collapsed', JSON.stringify(collapsed.value))
}

function isActive(path) {
  return route.path.startsWith(path)
}
</script>

<template>
  <aside :class="[
    'bg-white dark:bg-qe-black3 border-r dark:border-qe-black2 flex flex-col relative ',
    'transition-[width] duration-300 ease-in-out',
    collapsed ? 'w-16' : 'w-52'
  ]">
    <nav class="flex-1 space-y-2 px-3 py-4 text-sm">
      <RouterLink to="/estimates" class="flex items-center rounded transition-all rounded-lg" :class="[
        collapsed ? 'justify-center h-9 w-full' : ' px-3 py-2',
        isActive('/estimates')
          ? 'bg-blue-100 dark:bg-qe-black2 text-blue-700 dark:text-blue-600 font-semibold'
          : 'hover:bg-blue-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-100'
      ]">
        <FileText class="w-5 h-5 shrink-0" />
        <span class="inline-block transition-all duration-300"
          :class="collapsed ? 'opacity-0 max-w-0 ml-0' : 'opacity-100 max-w-xs ml-2'"
          style="overflow:hidden; white-space:nowrap;">Сметы</span>
      </RouterLink>
      <!-- Повторите для остальных пунктов меню -->
      <RouterLink to="/clients" class="flex items-center rounded transition-all rounded-lg" :class="[
        collapsed ? 'justify-center h-9 w-full' : ' px-3 py-2',
        isActive('/clients')
          ? 'bg-blue-100 dark:bg-qe-black2 text-blue-700 dark:text-blue-600 font-semibold'
          : 'hover:bg-blue-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-100'
      ]">
        <Users class="w-5 h-5 shrink-0" />
        <span class="inline-block transition-all duration-300"
          :class="collapsed ? 'opacity-0 max-w-0 ml-0' : 'opacity-100 max-w-xs ml-2'"
          style="overflow:hidden; white-space:nowrap;">Клиенты</span>
      </RouterLink>
      <RouterLink to="/templates" class="flex items-center rounded transition-all rounded-lg" :class="[
        collapsed ? 'justify-center h-9 w-full' : ' px-3 py-2',
        isActive('/templates')
          ? 'bg-blue-100 dark:bg-qe-black2 text-blue-700 dark:text-blue-600 font-semibold'
          : 'hover:bg-blue-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-100'
      ]">
        <Folder class="w-5 h-5 shrink-0" />
        <span class="inline-block transition-all duration-300"
          :class="collapsed ? 'opacity-0 max-w-0 ml-0' : 'opacity-100 max-w-xs ml-2'"
          style="overflow:hidden; white-space:nowrap;">Шаблоны</span>
      </RouterLink>
      <RouterLink to="/analytics" class="flex items-center rounded transition-all rounded-lg" :class="[
        collapsed ? 'justify-center h-9 w-full' : ' px-3 py-2',
        isActive('/analytics')
          ? 'bg-blue-100 dark:bg-qe-black2 text-blue-700 dark:text-blue-600 font-semibold'
          : 'hover:bg-blue-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-100'
      ]">
        <ChartNoAxesCombined class="w-5 h-5 shrink-0" />
        <span class="inline-block transition-all duration-300"
          :class="collapsed ? 'opacity-0 max-w-0 ml-0' : 'opacity-100 max-w-xs ml-2'"
          style="overflow:hidden; white-space:nowrap;">Аналитика</span>
      </RouterLink>
      <RouterLink to="/approvals" class="flex items-center rounded transition-all rounded-lg" :class="[
        collapsed ? 'justify-center h-9 w-full' : ' px-3 py-2',
        isActive('/approvals')
          ? 'bg-blue-100 dark:bg-qe-black2 text-blue-700 dark:text-blue-600 font-semibold'
          : 'hover:bg-blue-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-100'
      ]">
        <ClipboardCheck class="w-5 h-5 shrink-0" />
        <span class="inline-block transition-all duration-300"
          :class="collapsed ? 'opacity-0 max-w-0 ml-0' : 'opacity-100 max-w-xs ml-2'"
          style="overflow:hidden; white-space:nowrap;">Согласования</span>
      </RouterLink>
      <RouterLink to="/workspace/settings" class="flex items-center rounded transition-all rounded-lg" :class="[
        collapsed ? 'justify-center h-9 w-full' : ' px-3 py-2',
        isActive('/workspace/settings')
          ? 'bg-blue-100 dark:bg-qe-black2 text-blue-700 dark:text-blue-600 font-semibold'
          : 'hover:bg-blue-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-100'
      ]">
        <Building2 class="w-5 h-5 shrink-0" />
        <span class="inline-block transition-all duration-300"
          :class="collapsed ? 'opacity-0 max-w-0 ml-0' : 'opacity-100 max-w-xs ml-2'"
          style="overflow:hidden; white-space:nowrap;">Пространство</span>
      </RouterLink>
    </nav>

    <section
      v-if="auth.user?.is_admin"
      class="px-3 pb-4 text-sm"
      :class="collapsed ? 'pt-2' : 'pt-1'"
    >
      <div
        :class="collapsed
          ? 'border-t border-amber-200/70 pt-2 dark:border-amber-900/40'
          : 'rounded-xl border border-amber-200/70 bg-amber-50/70 p-2 dark:border-amber-900/40 dark:bg-amber-950/20'"
      >
        <p
          v-if="!collapsed"
          class="px-2 pb-1 text-[11px] font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-300"
        >
          Администрирование
        </p>

        <RouterLink
          to="/admin/users"
          class="flex items-center rounded-lg transition-all"
          :class="[
            collapsed ? 'justify-center h-9 w-full' : 'px-3 py-2',
            isActive('/admin/users')
              ? 'bg-amber-100 text-amber-800 font-semibold dark:bg-amber-900/40 dark:text-amber-200'
              : 'text-gray-700 hover:bg-amber-100/80 dark:text-gray-100 dark:hover:bg-amber-900/30'
          ]"
        >
          <Shield class="w-5 h-5 shrink-0" />
          <span
            class="inline-block transition-all duration-300"
            :class="collapsed ? 'opacity-0 max-w-0 ml-0' : 'opacity-100 max-w-xs ml-2'"
            style="overflow:hidden; white-space:nowrap;"
          >
            Админ-панель
          </span>
        </RouterLink>

        <RouterLink
          to="/admin/audit"
          class="flex items-center rounded-lg transition-all"
          :class="[
            collapsed ? 'justify-center h-9 w-full' : 'px-3 py-2',
            isActive('/admin/audit')
              ? 'bg-amber-100 text-amber-800 font-semibold dark:bg-amber-900/40 dark:text-amber-200'
              : 'text-gray-700 hover:bg-amber-100/80 dark:text-gray-100 dark:hover:bg-amber-900/30'
          ]"
        >
          <ClipboardCheck class="w-5 h-5 shrink-0" />
          <span
            class="inline-block transition-all duration-300"
            :class="collapsed ? 'opacity-0 max-w-0 ml-0' : 'opacity-100 max-w-xs ml-2'"
            style="overflow:hidden; white-space:nowrap;"
          >
            Аудит
          </span>
        </RouterLink>
      </div>
    </section>

    <button @click="toggleSidebar"
      class="absolute top-1/2 -right-3 transform -translate-y-1/2 bg-white dark:bg-qe-black3 border dark:border-gray-700 rounded-full shadow p-1 hover:bg-blue-100 dark:hover:bg-gray-800 transition z-50">
      <ChevronLeft class="h-4 w-4 text-gray-600 dark:text-gray-300 transition-transform duration-200"
        :class="{ 'rotate-180': collapsed }" />
    </button>
  </aside>
</template>
