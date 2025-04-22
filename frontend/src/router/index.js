import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'

import DefaultLayout from '@/layouts/DefaultLayout.vue'
import EstimatesPage from '@/pages/EstimatesPage.vue'
import EstimatesCreatePage from '@/pages/EstimatesCreatePage.vue'
import EstimateDetailsPage from '@/pages/EstimateDetailsPage.vue'
import EstimateEditPage from '@/pages/EstimateEditPage.vue'
import LoginPage from '@/pages/LoginPage.vue'
import RegisterPage from '@/pages/RegisterPage.vue'
import TemplatesPage from '@/pages/TemplatesPage.vue'
import TemplateCreatePage from '@/pages/TemplateCreatePage.vue'
import TemplateEditPage from '@/pages/TemplateEditPage.vue'
import TemplateDetailsPage from '@/pages/TemplateDetailsPage.vue'

const routes = [
  {
    path: '/',
    component: DefaultLayout,
    children: [
      {
        path: '/login',
        component: LoginPage
      },
      {
        path: '/register',
        component: RegisterPage
      },
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
        path: '/templates',
        name: 'TemplatesPage',
        component: TemplatesPage
      },
      {
        path: '/templates/create',
        component: TemplateCreatePage
      },
      {
        path: '/templates/:id/edit',
        component: TemplateEditPage
      },
      {
        path: '/templates/:id',
        component: TemplateDetailsPage
      },
      {
        path: 'login',
        component: {
          template: '<div>Страница входа 🔐</div>'
        }
      },
      {
        path: '/profile',
        component: () => import('@/pages/ProfilePage.vue'),
        children: [
          { path: '', redirect: '/profile/account' },
          { path: 'account', component: () => import('@/pages/profile/AccountTab.vue') },
          { path: 'password', component: () => import('@/pages/profile/PasswordTab.vue') }
        ]
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()
  const publicPages = ['/login', '/register']
  const authRequired = !publicPages.includes(to.path)

  if (authRequired && !auth.token) {
    return next('/login')
  }

  if (auth.token && !auth.user) {
    try {
      await auth.fetchUser()
    } catch {
      auth.logout()
      return next('/login')
    }
  }

  next()
})

export default router
