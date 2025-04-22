<template>
    <div class="space-y-6 max-w-7xl mx-auto px-16 py-8">
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
  
  onMounted(async () => {
    template.value = await store.getTemplateById(route.params.id)
  })
  
  function goToDetails() {
    toast.success('Шаблон сохранен')
    router.push(`/templates/${route.params.id}`)
  }
  </script>
  