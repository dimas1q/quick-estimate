<script setup>
import { Frown } from 'lucide-vue-next'
</script>

<template>
    <div class="flex flex-col items-center justify-center min-h-screen bg-gray-50 dark:bg-qe-black text-center px-4">
        <Frown class="w-20 h-20 text-gray-400 mb-4" />
        <div class="text-7xl font-extrabold text-gray-300 select-none leading-none mb-2">404</div>
        <p class="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-2">Страница не найдена</p>
        <p class="text-gray-500 dark:text-gray-400 mb-8">Кажется, вы попали не туда. Такой страницы не существует.</p>
        <router-link to="/" class="qe-btn">
            Вернуться на главную
        </router-link>
    </div>
</template>
