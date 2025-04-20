<template>
    <form @submit.prevent="save" class="space-y-6 max-w-2xl">
      <div class="space-y-1">
        <label class="block text-sm font-medium text-gray-700">Текущий пароль</label>
        <input v-model="current" placeholder="Введите текущий пароль" type="password" class="input-field" />
      </div>
      <div class="space-y-1">
        <label class="block text-sm font-medium text-gray-700">Новый пароль</label>
        <input v-model="newPassword" placeholder="Введите новый пароль" type="password" class="input-field" />
      </div>
      <div class="space-y-1">
        <label class="block text-sm font-medium text-gray-700">Подтвердите новый пароль</label>
        <input v-model="confirm" placeholder="Повторите новый пароль" type="password" class="input-field" />
      </div>
  
      <button type="submit" class="btn-primary">Сохранить</button>
    </form>
  </template>
  
  <script setup>
  import { ref } from 'vue'
  import { useToast } from 'vue-toastification'
  import { useAuthStore } from '@/store/auth'
  
  const toast = useToast()
  const auth = useAuthStore()
  
  const current = ref('')
  const newPassword = ref('')
  const confirm = ref('')
  
  async function save() {
    if (newPassword.value !== confirm.value) {
      toast.error('Пароли не совпадают')
      return
    }
  
    try {
      await auth.changePassword({
        current_password: current.value,
        new_password: newPassword.value,
        confirm_password: confirm.value
      })
      toast.success('Пароль обновлён')
      current.value = newPassword.value = confirm.value = ''
    } catch (e) {
      const message = e?.response?.data?.detail || 'Ошибка при смене пароля'
      toast.error(message)
    }
  }
  </script>
  