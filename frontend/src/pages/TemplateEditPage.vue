<template>
  <div v-if="error" class="text-red-500 text-center text-lg font-medium mt-10">
    {{ error }}
  </div>
  <div v-if="template" class="space-y-6 max-w-7xl mx-auto px-16 py-8">
    <h1 class="text-2xl font-bold mb-4 text-center">Редактирование шаблона {{ template?.name }}</h1>
    <TemplateForm v-if="template" :initial="template" mode="edit" @updated="goToDetails" />
  </div>
</template>
  
  <script setup>
  import { onMounted, ref } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import { useTemplatesStore } from '@/store/templates'
  import { useToast } from 'vue-toastification'
  import TemplateForm from '@/components/TemplateForm.vue'
  
  const route = useRoute()
  const router = useRouter()
  const store = useTemplatesStore()
  const template = ref(null)
  const toast = useToast()
  const error = ref(null)
  
  onMounted(async () => {
    try {
      template.value = await store.getTemplateById(route.params.id)
    } catch (e) {
      if (e.response?.status === 403) {
        error.value = '🚫 У вас нет доступа к этому шаблону.'
      } else if (e.response?.status === 404) {
        error.value = '❌ Шаблон не найден.'
      } else {
        error.value = '⚠️ Ошибка при загрузке шаблона.'
      }
    }
    
  })
  
  function goToDetails() {
    toast.success('Шаблон сохранен')
    router.push(`/templates/${route.params.id}`)
  }
  </script>
  