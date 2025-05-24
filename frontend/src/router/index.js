import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'

import DefaultLayout from '@/layouts/DefaultLayout.vue'
import AuthLayout from '@/layouts/AuthLayout.vue'

// auth
import LoginPage from '@/pages/auth/LoginPage.vue'
import RegisterPage from '@/pages/auth/RegisterPage.vue'

// pages
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
import AnalyticsPage from '@/pages/analytics/AnalyticsPage.vue'
import NotFoundPage from '@/pages/errors/NotFoundPage.vue'


const routes = [
  // AUTH PAGES
  {
    path: '/login',
    component: LoginPage,
    meta: { layout: AuthLayout }
  },
  {
    path: '/register',
    component: RegisterPage,
    meta: { layout: AuthLayout }
  },

  // APP PAGES — каждая страница указывает layout явно
  { path: '/', redirect: '/estimates' },

  { path: '/estimates', component: EstimatesPage, meta: { layout: DefaultLayout } },
  { path: '/estimates/create', component: EstimateCreatePage, meta: { layout: DefaultLayout } },
  { path: '/estimates/:id', component: EstimateDetailsPage, meta: { layout: DefaultLayout } },
  { path: '/estimates/:id/edit', component: EstimateEditPage, meta: { layout: DefaultLayout } },

  { path: '/templates', component: TemplatesPage, meta: { layout: DefaultLayout } },
  { path: '/templates/create', component: TemplateCreatePage, meta: { layout: DefaultLayout } },
  { path: '/templates/:id/edit', component: TemplateEditPage, meta: { layout: DefaultLayout } },
  { path: '/templates/:id', component: TemplateDetailsPage, meta: { layout: DefaultLayout } },

  { path: '/clients', component: ClientsPage, meta: { layout: DefaultLayout } },
  { path: '/clients/create', component: ClientCreatePage, meta: { layout: DefaultLayout } },
  { path: '/clients/:id', component: ClientDetailsPage, meta: { layout: DefaultLayout } },
  { path: '/clients/:id/edit', component: ClientEditPage, meta: { layout: DefaultLayout } },

  {
    path: '/profile',
    component: ProfilePage,
    meta: { layout: DefaultLayout },
    children: [
      { path: '', redirect: '/profile/account' },
      { path: 'account', component: () => import('@/pages/profile/AccountTab.vue'), meta: { layout: DefaultLayout } },
      { path: 'password', component: () => import('@/pages/profile/PasswordTab.vue'), meta: { layout: DefaultLayout } }
    ]
  },

  {
    path: '/analytics',
    component: AnalyticsPage,
    meta: { layout: DefaultLayout }
  },

  // 404
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFoundPage,
    meta: { layout: AuthLayout }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// защита маршрутов
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
