# frontend/src/pages/auth/LoginPage.vue
<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/store/auth'
import { useRouter } from 'vue-router'
import { useToast } from 'vue-toastification'

const auth = useAuthStore()
const router = useRouter()
const email = ref('')
const password = ref('')
const showPassword = ref(false)
const error = ref(null)
const verify = ref(false)
const code = ref('')
const canResend = ref(false)
const timer = ref(60)
let interval
const toast = useToast()

async function handleLogin() {
    try {
        await auth.login(email.value, password.value)
        router.push('/estimates')
    } catch (e) {
        if (e.response?.status === 403 && e.response.data.verify_required) {
            verify.value = true
            email.value = e.response.data.email
            toast.success('Код отправлен на email')
            startTimer()
        } else {
            error.value = 'Неверный email или пароль'
        }
    }
}

function startTimer() {
    canResend.value = false
    timer.value = 60
    clearInterval(interval)
    interval = setInterval(() => {
        timer.value--
        if (timer.value <= 0) {
            canResend.value = true
            clearInterval(interval)
        }
    }, 1000)
}

async function submitCode() {
    error.value = null
    try {
        await auth.verifyCode(email.value, code.value)
        router.push('/estimates')
    } catch {
        error.value = 'Код не верный, попробуйте еще раз'
    }
}

async function resend() {
    try {
        await auth.resendCode(email.value)
        toast.success('Код отправлен')
        startTimer()
    } catch (e) {
        error.value = e.response?.data?.detail || 'Ошибка отправки'
    }
}
</script>

<template>
    <div class="w-full max-w-sm bg-white dark:bg-qe-black3 rounded-2xl shadow-xl p-8 border border-gray-100 dark:border-gray-800">
        <div class="flex flex-col items-center mb-6">
            <img src="/logo.svg" class="w-16 h-16" alt="QuickEstimate" />
            <span class="text-2xl font-extrabold text-blue-700 dark:text-blue-600">Quick Estimate</span>
        </div>
        <h2 v-if="!verify" class="text-xl font-medium mb-6 text-center text-gray-800 dark:text-gray-100">Вход в личный кабинет</h2>
        <form v-if="!verify" @submit.prevent="handleLogin" autocomplete="on">
            <div class="mb-4">
                <label class="block mb-1 text-sm font-semibold text-gray-800 dark:text-gray-300" for="identifier">
                    Email или логин
                </label>
                <div class="relative">
                    <input v-model="email" id="identifier" type="text" autocomplete="username"
                        class="qe-input w-full pr-10" placeholder="Введите email или логин" required />

                </div>
            </div>
            <div class="mb-6">
                <label class="block mb-1 text-sm font-semibold text-gray-800 dark:text-gray-300"
                    for="password">Пароль</label>
                <div class="relative">
                    <input :type="showPassword ? 'text' : 'password'" v-model="password" id="password"
                        autocomplete="current-password" class="qe-input w-full pr-12" placeholder="Введите пароль"
                        required />
                    <button type="button" class="absolute right-3 top-2.5 text-gray-400 hover:text-blue-500 transition"
                        @click="showPassword = !showPassword" tabindex="-1" aria-label="Показать пароль">
                        <svg v-if="!showPassword" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2"
                            viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path stroke-linecap="round" stroke-linejoin="round"
                                d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.478 0-8.268-2.943-9.542-7z" />
                        </svg>
                        <svg v-else class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2"
                            viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round"
                                d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.542-7a9.967 9.967 0 012.747-4.362M17.94 17.94A9.969 9.969 0 0021.542 12c-1.274-4.057-5.064-7-9.542-7a9.969 9.969 0 00-7.598 3.502M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path stroke-linecap="round" stroke-linejoin="round" d="M3 3l18 18" />
                        </svg>
                    </button>
                </div>
            </div>
            <button type="submit" class="qe-btn mb-2 w-full">Войти</button>
        </form>
        <div v-else class="space-y-4">
            <h2 class="text-xl font-medium text-center text-gray-800 dark:text-gray-100">Подтверждение аккаунта</h2>
            <form @submit.prevent="submitCode" class="space-y-4">
                <input v-model="code" class="qe-input w-full" placeholder="Код" />
                <button class="qe-btn w-full" type="submit">Подтвердить</button>
            </form>
            <button @click="resend" class="qe-btn w-full" :disabled="!canResend">
                Отправить еще раз <span v-if="!canResend">({{ timer }})</span>
            </button>
        </div>
        <p v-if="error" class="text-red-500 text-sm mt-3 text-center animate-pulse">{{ error }}</p>
        <p v-if="!verify" class="text-sm text-gray-600 mt-6 text-center dark:text-gray-400">
            Нет аккаунта?
            <router-link to="/register" class="text-blue-500 dark:text-blue-400 hover:underline transition">Зарегистрироваться</router-link>
        </p>
    </div>
</template>
