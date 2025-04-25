<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/store/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

const login = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref(null)
const success = ref(false)

async function handleRegister() {
    error.value = null

    if (!login.value || !email.value || !password.value || !confirmPassword.value) {
        error.value = 'Пожалуйста, заполните все поля'
        return
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email.value)) {
        error.value = 'Введите корректный email'
        return
    }

    if (password.value !== confirmPassword.value) {
        error.value = 'Пароли не совпадают'
        return
    }

    try {
        await auth.register({ login: login.value, email: email.value, password: password.value })
        success.value = true
        setTimeout(() => router.push('/login'), 1500)
    } catch (e) {
        error.value = 'Ошибка при регистрации'
    }
}
</script>


<template>
    <div class="flex items-center justify-center h-full bg-gray-50">
        <div class="bg-white shadow-md rounded px-8 py-6 w-full max-w-sm">
            <h2 class="text-2xl font-bold mb-6 text-center text-gray-800">Регистрация</h2>

            <input v-model="login" type="text" placeholder="Логин"
                class="w-full mb-4 px-4 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400" />
            <input v-model="email" type="email" placeholder="Email"
                class="w-full mb-4 px-4 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400" />
            <input v-model="password" type="password" placeholder="Пароль"
                class="w-full mb-4 px-4 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400" />
            <input v-model="confirmPassword" type="password" placeholder="Повторите пароль"
                class="w-full mb-4 px-4 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400" />

            <button @click="handleRegister"
                class="w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 rounded-md">
                Зарегистрироваться
            </button>

            <p v-if="success" class="text-green-600 mt-4 text-center">Успешно! Перенаправляем...</p>
            <p v-if="error" class="text-red-500 text-sm mt-4 text-center">{{ error }}</p>

            <p class="text-sm text-gray-600 mt-6 text-center">
                Уже есть аккаунт?
                <router-link to="/login" class="text-blue-500 hover:underline">Войти</router-link>
            </p>
        </div>
    </div>
</template>

