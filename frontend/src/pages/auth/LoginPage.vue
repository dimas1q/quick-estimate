<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/store/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()
const email = ref('')
const password = ref('')
const error = ref(null)

async function handleLogin() {
    try {
        await auth.login(email.value, password.value)
        router.push('/estimates')
    } catch (e) {
        error.value = 'Неверный email или пароль'
    }
}
</script>

<template>
    <div class="flex items-center justify-center h-full bg-gray-50">
        <div class="bg-white shadow-lg rounded-lg px-8 py-6 w-full max-w-sm">
            <h2 class="text-2xl font-bold mb-6 text-center text-gray-800">Вход</h2>

            <input v-model="email" type="email" placeholder="Email"
                class="w-full mb-4 px-4 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400" />

            <input v-model="password" type="password" placeholder="Пароль"
                class="w-full mb-4 px-4 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400" />

            <button @click="handleLogin"
                class="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 rounded-md">
                Войти
            </button>

            <p v-if="error" class="text-red-500 text-sm mt-4 text-center">{{ error }}</p>

            <p class="text-sm text-gray-600 mt-6 text-center">
                Нет аккаунта?
                <router-link to="/register" class="text-blue-500 hover:underline">Зарегистрироваться</router-link>
            </p>
        </div>
    </div>
</template>

<style scoped>
.input {
    @apply border rounded w-full px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400;
}
</style>
