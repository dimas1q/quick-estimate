<template>
    <div class="space-y-6 max-w-6xl mx-auto px-16 py-8">
        <h1 class="text-2xl font-bold text-center py-2">Создание клиента</h1>
        <ClientForm mode="create" />
    </div>
</template>
<script setup>
import ClientForm from '@/components/ClientForm.vue'
</script>
