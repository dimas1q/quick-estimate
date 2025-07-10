<script setup>
import { ref, onUnmounted } from 'vue'
import { useAuthStore } from '@/store/auth'
import { useToast } from 'vue-toastification'

const props = defineProps({
  email: { type: String, required: true },
  initialSeconds: { type: Number, default: 60 }
})

const emit = defineEmits(['verified'])

const auth = useAuthStore()
const toast = useToast()

const code = ref('')
const error = ref(null)
const canResend = ref(props.initialSeconds === 0)
const seconds = ref(props.initialSeconds)
let timer = null

function startTimer() {
  canResend.value = false
  seconds.value = 60
  clearInterval(timer)
  timer = setInterval(() => {
    seconds.value--
    if (seconds.value <= 0) {
      canResend.value = true
      clearInterval(timer)
    }
  }, 1000)
}

async function verify() {
  error.value = null
  try {
    await auth.verifyCode({ email: props.email, code: code.value })
    emit('verified')
  } catch {
    error.value = 'Код не верный, попробуйте еще раз'
  }
}

async function resend() {
  try {
    await auth.resendCode(props.email)
    toast.success('Код отправлен')
    startTimer()
  } catch {
    error.value = 'Ошибка отправки кода'
  }
}

if (props.initialSeconds > 0) {
  startTimer()
}

onUnmounted(() => clearInterval(timer))
</script>

<template>
  <div>
    <h2 class="text-xl font-medium mb-6 text-center text-gray-800 dark:text-gray-100">Подтверждение аккаунта</h2>
    <div class="mb-4">
      <label class="block mb-1 text-sm font-semibold text-gray-800 dark:text-gray-300" for="otp">Код</label>
      <input v-model="code" id="otp" type="text" maxlength="6" class="qe-input w-full" placeholder="Введите код" />
    </div>
    <button class="qe-btn w-full" @click="verify">Подтвердить</button>
    <button class="qe-btn w-full mt-3" :disabled="!canResend" @click="resend">
      Отправить ещё раз
      <span v-if="!canResend">({{ seconds }})</span>
    </button>
    <p v-if="error" class="text-red-500 text-sm mt-3 text-center">{{ error }}</p>
  </div>
</template>
