import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'

import NotFoundPage from '@/pages/errors/NotFoundPage.vue'

import DefaultLayout from '@/layouts/DefaultLayout.vue'
import LoginPage from '@/pages/auth/LoginPage.vue'
import RegisterPage from '@/pages/auth/RegisterPage.vue'
import ProfilePage from '@/pages/profile/ProfilePage.vue'
import EstimatesPage from '@/pages/estimate/EstimatesPage.vue'
import EstimateCreatePage from '@/pages/estimate/EstimateCreatePage.vue'
import EstimateDetailsPage from '@/pages/estimate/EstimateDetailsPage.vue'
import EstimateEditPage from '@/pages/estimate/EstimateEditPage.vue'
import TemplatesPage from '@/pages/template/TemplatesPage.vue'
import TemplateCreatePage from '@/pages/template/TemplateCreatePage.vue'
import TemplateEditPage from '@/pages/template/TemplateEditPage.vue'
import TemplateDetailsPage from '@/pages/template/TemplateDetailsPage.vue'
import ClientsPage from '@/pages/client/ClientsPage.vue'
import ClientCreatePage from '@/pages/client/ClientCreatePage.vue'
import ClientDetailsPage from '@/pages/client/ClientDetailsPage.vue'
import ClientEditPage from '@/pages/client/ClientEditPage.vue'

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
      { path: 'estimates/create', component: EstimateCreatePage },
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
      { path: '/clients', component: ClientsPage },
      { path: '/clients/create', component: ClientCreatePage },
      { path: '/clients/:id', component: ClientDetailsPage },
      { path: '/clients/:id/edit', component: ClientEditPage },
      {
        path: 'login',
        component: {
          template: '<div>Страница входа 🔐</div>'
        }
      },
      {
        path: '/profile',
        component: ProfilePage,
        children: [
          { path: '', redirect: '/profile/account' },
          { path: 'account', component: () => import('@/pages/profile/AccountTab.vue') },
          { path: 'password', component: () => import('@/pages/profile/PasswordTab.vue') }
        ]
      },
      {
        path: '/:pathMatch(.*)*',
        name: 'NotFound',
        component: NotFoundPage
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
