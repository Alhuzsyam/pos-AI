import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/composables/useApi'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('posai_user') || 'null'))
  const accessToken = ref(localStorage.getItem('posai_token') || null)

  const isAuthenticated = computed(() => !!accessToken.value)
  const isSuperAdmin = computed(() => user.value?.role === 'superadmin')
  const isAdmin = computed(() => ['superadmin', 'admin'].includes(user.value?.role))
  const isManager = computed(() => ['superadmin', 'admin', 'manager'].includes(user.value?.role))
  const isKasir = computed(() => ['superadmin', 'admin', 'manager', 'kasir'].includes(user.value?.role))

  const isDapur = computed(() => ['superadmin', 'admin', 'manager', 'dapur'].includes(user.value?.role))
  const isWaiter = computed(() => ['superadmin', 'admin', 'manager', 'waiter'].includes(user.value?.role))

  function can(role) {
    const hierarchy = { superadmin: 5, admin: 4, manager: 3, kasir: 2, inventory: 1, dapur: 1, waiter: 1 }
    const userLevel = hierarchy[user.value?.role] || 0
    const requiredLevel = hierarchy[role] || 0
    // dapur/waiter are special: they can only access their own station + dashboard
    if (['dapur', 'waiter'].includes(user.value?.role)) {
      return ['dapur', 'waiter'].includes(role) || requiredLevel <= userLevel
    }
    return userLevel >= requiredLevel
  }

  async function login(username, password) {
    // OAuth2PasswordRequestForm expects application/x-www-form-urlencoded.
    // URLSearchParams makes axios set the correct Content-Type automatically.
    const body = new URLSearchParams()
    body.append('username', username)
    body.append('password', password)

    const res = await api.post('/api/v1/auth/login', body)

    accessToken.value = res.data.access_token
    user.value = res.data.user

    localStorage.setItem('posai_token', res.data.access_token)
    localStorage.setItem('posai_user', JSON.stringify(res.data.user))
    localStorage.setItem('posai_refresh', res.data.refresh_token)

    return res.data
  }

  function logout() {
    accessToken.value = null
    user.value = null
    localStorage.removeItem('posai_token')
    localStorage.removeItem('posai_user')
    localStorage.removeItem('posai_refresh')
    router.push('/login')
  }

  return { user, accessToken, isAuthenticated, isSuperAdmin, isAdmin, isManager, isKasir, isDapur, isWaiter, can, login, logout }
})
