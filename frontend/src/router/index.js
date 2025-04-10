import { createRouter, createWebHistory } from 'vue-router'
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import EstimatesPage from '@/pages/EstimatesPage.vue'
import EstimatesCreatePage from '@/pages/EstimatesCreatePage.vue'
import EstimateDetailsPage from '@/pages/EstimateDetailsPage.vue'
import EstimateEditPage from '@/pages/EstimateEditPage.vue'

const routes = [
  {
    path: '/',
    component: DefaultLayout,
    children: [
      {
        path: '',
        redirect: '/estimates'
      },
      {
        path: 'estimates',
        component: EstimatesPage
      },
      { path: 'estimates/create', component: EstimatesCreatePage },
      { path: 'estimates/:id', component: EstimateDetailsPage },
      { path: '/estimates/:id/edit', component: EstimateEditPage },
      {
        path: 'templates',
        component: {
          template: '<div>Тут скоро будут шаблоны 🧱</div>'
        }
      },
      {
        path: 'login',
        component: {
          template: '<div>Страница входа 🔐</div>'
        }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
