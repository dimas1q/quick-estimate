<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
const emit = defineEmits(['update:collapsed'])
const props = defineProps({ collapsed: { type: Boolean, default: null } })
import { FileText, Folder, Users, ChevronLeft, ChartNoAxesCombined } from 'lucide-vue-next'

const route = useRoute()
const collapsed = ref(
  props.collapsed !== null
    ? props.collapsed
    : JSON.parse(localStorage.getItem('sidebar-collapsed')) || false
)

watch(
  () => props.collapsed,
  (val) => {
    if (val !== null && val !== collapsed.value) {
      collapsed.value = val
    }
  }
)

watch(collapsed, (val) => {
  localStorage.setItem('sidebar-collapsed', JSON.stringify(val))
  emit('update:collapsed', val)
})

function toggleSidebar() {
  collapsed.value = !collapsed.value
}

function isActive(path) {
  return route.path.startsWith(path)
}
</script>

<template>
  <aside :class="[
    'bg-white dark:bg-qe-black3 border-r dark:border-qe-black2 transition-all duration-300 ease-in-out flex flex-col relative',
    collapsed ? 'w-16' : 'w-48'
  ]">
    <nav class="flex-1 space-y-2 px-3 py-4 text-sm">
      <RouterLink to="/estimates" class="flex items-center rounded transition-all rounded-lg" :class="[
        collapsed ? 'justify-center h-9 w-full' : 'gap-2 px-3 py-2',
        isActive('/estimates')
          ? 'bg-blue-100 dark:bg-qe-black2 text-blue-700 dark:text-blue-600 font-semibold'
          : 'hover:bg-blue-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-100'
      ]">
        <FileText class="w-5 h-5 shrink-0" />
        <span v-if="!collapsed">Сметы</span>
      </RouterLink>

      <RouterLink to="/clients" class="flex items-center rounded transition-all rounded-lg" :class="[
        collapsed ? 'justify-center h-9 w-full' : 'gap-2 px-3 py-2',
        isActive('/clients')
          ? 'bg-blue-100 dark:bg-qe-black2 text-blue-700 dark:text-blue-600 font-semibold'
          : 'hover:bg-blue-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-100'
      ]">
        <Users class="w-5 h-5 shrink-0" />
        <span v-if="!collapsed">Клиенты</span>
      </RouterLink>

      <RouterLink to="/templates" class="flex items-center rounded transition-all rounded-lg" :class="[
        collapsed ? 'justify-center h-9 w-full' : 'gap-2 px-3 py-2',
        isActive('/templates')
          ? 'bg-blue-100 dark:bg-qe-black2 text-blue-700 dark:text-blue-600 font-semibold'
          : 'hover:bg-blue-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-100'
      ]">
        <Folder class="w-5 h-5 shrink-0" />
        <span v-if="!collapsed">Шаблоны</span>
      </RouterLink>

      <RouterLink to="/analytics" class="flex items-center rounded transition-all rounded-lg" :class="[
        collapsed ? 'justify-center h-9 w-full' : 'gap-2 px-3 py-2',
        isActive('/analytics')
          ? 'bg-blue-100 dark:bg-qe-black2 text-blue-700 dark:text-blue-600 font-semibold'
          : 'hover:bg-blue-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-100'
      ]">
        <ChartNoAxesCombined class="w-5 h-5 shrink-0" />
        <span v-if="!collapsed">Аналитика</span>
      </RouterLink>
    </nav>

    <button @click="toggleSidebar"
      class="absolute top-1/2 -right-3 transform -translate-y-1/2 bg-white dark:bg-qe-black3 border dark:border-gray-700 rounded-full shadow p-1 hover:bg-blue-100 dark:hover:bg-gray-800 transition z-50">
      <ChevronLeft class="h-4 w-4 text-gray-600 dark:text-gray-300 transition-transform duration-200"
        :class="{ 'rotate-180': collapsed }" />
    </button>
  </aside>
</template>
