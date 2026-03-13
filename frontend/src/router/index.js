import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'

import DefaultLayout from '@/layouts/DefaultLayout.vue'
import AuthLayout from '@/layouts/AuthLayout.vue'

// auth
import LoginPage from '@/pages/auth/LoginPage.vue'
import RegisterPage from '@/pages/auth/RegisterPage.vue'

const ProfilePage = () => import('@/pages/profile/ProfilePage.vue')
const EstimatesPage = () => import('@/pages/estimate/EstimatesPage.vue')
const EstimateCreatePage = () => import('@/pages/estimate/EstimateCreatePage.vue')
const EstimateDetailsPage = () => import('@/pages/estimate/EstimateDetailsPage.vue')
const EstimateEditPage = () => import('@/pages/estimate/EstimateEditPage.vue')
const TemplatesPage = () => import('@/pages/template/TemplatesPage.vue')
const TemplateCreatePage = () => import('@/pages/template/TemplateCreatePage.vue')
const TemplateEditPage = () => import('@/pages/template/TemplateEditPage.vue')
const TemplateDetailsPage = () => import('@/pages/template/TemplateDetailsPage.vue')
const ClientsPage = () => import('@/pages/client/ClientsPage.vue')
const ClientCreatePage = () => import('@/pages/client/ClientCreatePage.vue')
const ClientDetailsPage = () => import('@/pages/client/ClientDetailsPage.vue')
const ClientEditPage = () => import('@/pages/client/ClientEditPage.vue')
const AnalyticsPage = () => import('@/pages/analytics/AnalyticsPage.vue')
const MyApprovalsPage = () => import('@/pages/approval/MyApprovalsPage.vue')
const AdminUsersPage = () => import('@/pages/admin/AdminUsersPage.vue')
const AdminUserWorkspacePage = () => import('@/pages/admin/AdminUserWorkspacePage.vue')
const AdminAuditLedgerPage = () => import('@/pages/admin/AdminAuditLedgerPage.vue')
const NotFoundPage = () => import('@/pages/errors/NotFoundPage.vue')


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
  {
    path: '/approvals',
    component: MyApprovalsPage,
    meta: { layout: DefaultLayout }
  },
  {
    path: '/admin/users',
    component: AdminUsersPage,
    meta: { layout: DefaultLayout, requiresAdmin: true }
  },
  {
    path: '/admin/users/:userId/workspace',
    component: AdminUserWorkspacePage,
    meta: { layout: DefaultLayout, requiresAdmin: true }
  },
  {
    path: '/admin/audit',
    component: AdminAuditLedgerPage,
    meta: { layout: DefaultLayout, requiresAdmin: true }
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

  if (to.meta.requiresAdmin && !auth.user?.is_admin) {
    return next('/estimates')
  }

  next()
})

export default router
