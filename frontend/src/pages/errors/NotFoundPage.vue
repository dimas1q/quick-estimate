<template>
    <div class="flex flex-col items-center justify-center min-h-screen bg-gray-50 text-center px-4">
        <div class="text-[10rem] font-bold text-gray-300 animate-pulse select-none leading-none">404</div>
        <p class="text-2xl font-semibold text-gray-800 mb-4">Страница не найдена</p>
        <p class="text-gray-500 mb-8">Кажется, вы попали не туда. Такой страницы не существует.</p>
        <router-link to="/"
            class="inline-block px-6 py-3 bg-blue-600 text-white font-medium rounded shadow hover:bg-blue-700 transition-all">
            Вернуться на главную
        </router-link>
    </div>
</template>
