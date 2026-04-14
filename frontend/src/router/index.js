import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true }
    },
    {
      path: '/',
      component: () => import('@/views/AppLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', name: 'dashboard', component: () => import('@/views/DashboardView.vue') },
        { path: 'pos', name: 'pos', component: () => import('@/views/PosView.vue') },
        { path: 'menu', name: 'menu', component: () => import('@/views/MenuView.vue'), meta: { role: 'manager' } },
        { path: 'inventory', name: 'inventory', component: () => import('@/views/InventoryView.vue'), meta: { role: 'inventory' } },
        { path: 'sales', name: 'sales', component: () => import('@/views/SalesView.vue') },
        { path: 'expenses', name: 'expenses', component: () => import('@/views/ExpensesView.vue'), meta: { role: 'kasir' } },
        { path: 'debts', name: 'debts', component: () => import('@/views/DebtsView.vue') },
        { path: 'reservations', name: 'reservations', component: () => import('@/views/ReservationsView.vue') },
        { path: 'reports', name: 'reports', component: () => import('@/views/ReportsView.vue'), meta: { role: 'manager' } },
        { path: 'payroll', name: 'payroll', component: () => import('@/views/PayrollView.vue'), meta: { role: 'admin' } },
        { path: 'office', name: 'office', component: () => import('@/views/OfficeView.vue'), meta: { role: 'admin' } },
        { path: 'users', name: 'users', component: () => import('@/views/UsersView.vue'), meta: { role: 'admin' } },
        { path: 'tenants', name: 'tenants', component: () => import('@/views/TenantsView.vue'), meta: { role: 'superadmin' } },
        { path: 'watchlist', name: 'watchlist', component: () => import('@/views/WatchlistView.vue') },
        { path: 'ai', name: 'ai', component: () => import('@/views/AiView.vue') },
        { path: 'settings', name: 'settings', component: () => import('@/views/SettingsView.vue') },
      ]
    },
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ]
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()

  if (to.meta.public) return next()
  if (!auth.isAuthenticated) return next('/login')

  const requiredRole = to.meta.role
  if (requiredRole && !auth.can(requiredRole)) {
    return next('/')  // redirect ke dashboard kalau tidak punya akses
  }

  next()
})

export default router
