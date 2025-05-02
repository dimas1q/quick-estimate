<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
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
        'bg-white border-r transition-all duration-300 ease-in-out flex flex-col relative',
        collapsed ? 'w-16' : 'w-52'
    ]">
        <nav class="flex-1 space-y-2 px-3 py-4 text-sm">
            <RouterLink to="/estimates" class="flex items-center gap-2 px-3 py-2 rounded hover:bg-blue-50 transition"
                :class="{ 'bg-blue-100 font-semibold text-blue-700': isActive('/estimates') }">
                📄 <span v-if="!collapsed">Сметы</span>
            </RouterLink>
            <RouterLink to="/templates" class="flex items-center gap-2 px-3 py-2 rounded hover:bg-blue-50 transition"
                :class="{ 'bg-blue-100 font-semibold text-blue-700': isActive('/templates') }">
                📁 <span v-if="!collapsed">Шаблоны</span>
            </RouterLink>
            <RouterLink to="/clients" class="flex items-center gap-2 px-3 py-2 rounded hover:bg-blue-50 transition"
                :class="{ 'bg-blue-100 font-semibold text-blue-700': isActive('/clients') }">
                👥 <span v-if="!collapsed">Клиенты</span>
            </RouterLink>
        </nav>

        <button @click="toggleSidebar"
            class="absolute top-1/2 -right-3 transform -translate-y-1/2 bg-white border rounded-full shadow p-1 hover:bg-blue-100 transition z-50">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-600 transition-transform duration-200"
                fill="none" viewBox="0 0 24 24" stroke="currentColor" :class="{ 'rotate-180': collapsed }">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
        </button>
    </aside>
</template>
