<template>
  <form @submit.prevent="save" class="space-y-6 max-w-2xl">
    <div v-for="(value, key) in form" :key="key" class="space-y-1">
      <label class="block text-sm font-medium text-gray-700">
        {{ fieldLabels[key] }}
      </label>
      <input v-model="form[key]" :placeholder="fieldLabels[key]" class="qe-input w-full" type="text" />
    </div>

    <button type="submit" class="qe-btn">Сохранить</button>
  </form>
</template>
  
  <script setup>
  import { ref } from 'vue'
  import { useAuthStore } from '@/store/auth'
  import { useToast } from 'vue-toastification'
  
  const auth = useAuthStore()
  const toast = useToast()
  
  const form = ref({
    login: auth.user?.login || '',
    email: auth.user?.email || '',
    name: auth.user?.name || '',
    company: auth.user?.company || ''
  })
  
  const fieldLabels = {
    login: 'Логин',
    email: 'Электронная почта',
    name: 'Имя',
    company: 'Компания'
  }
  
  async function save() {
    try {
      await auth.updateProfile(form.value)
      toast.success('Профиль обновлён')
    } catch (e) {
      toast.error(e || 'Ошибка при обновлении')
    }
  }
  </script>
  