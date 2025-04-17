import { createApp } from 'vue'
import App from './App.vue'
import './assets/main.css'

import { createPinia } from 'pinia'
import router from './router'

import Toast, { POSITION } from 'vue-toastification'
import 'vue-toastification/dist/index.css'

import { useAuthStore } from '@/store/auth'

const app = createApp(App)

const pinia = createPinia()
app.use(pinia)

const auth = useAuthStore()

await auth.restoreSession()  // ⬅️ восстанавливаем сессию до mount()

app.use(router)

app.use(Toast, {
  position: POSITION.TOP_CENTER,
  timeout: 3000,
  hideProgressBar: true,
})

app.mount('#app')
