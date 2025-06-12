import { createApp } from 'vue'
import App from './App.vue'
import './assets/main.css'

import { createPinia } from 'pinia'
import VueApexCharts from 'vue3-apexcharts'
import router from './router'

import Toast, { POSITION } from 'vue-toastification'
import 'vue-toastification/dist/index.css'

import { useAuthStore } from '@/store/auth'
import { initRipple } from './lib/ripple'

const savedTheme = localStorage.getItem('theme')
if (
  savedTheme === 'dark' ||
  (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)
) {
  document.documentElement.classList.add('dark')
} else {
  document.documentElement.classList.remove('dark')
}

const app = createApp(App)

const pinia = createPinia()
app.use(pinia)

const auth = useAuthStore()

await auth.restoreSession()

app.use(router)

app.component('apexchart', VueApexCharts)

app.use(Toast, {
  position: POSITION.TOP_CENTER,
  timeout: 3000,
  closeOnClick: true,
  pauseOnHover: true,
  draggable: true,
  transition: 'Vue-Toastification__bounce',
  maxToasts: 5,
  newestOnTop: true
})

initRipple()

app.mount('#app')
