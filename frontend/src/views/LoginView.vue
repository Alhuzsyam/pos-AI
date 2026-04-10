<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-900 via-brand-800 to-brand-700 p-4">
    <div class="w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-white/20 rounded-2xl backdrop-blur mb-4">
          <svg class="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 11h.01M12 11h.01M15 11h.01M4 19h16a2 2 0 002-2V7a2 2 0 00-2-2H4a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>
        <h1 class="text-3xl font-bold text-white">POS-AI</h1>
        <p class="text-brand-200 mt-1 text-sm">Multi-Tenant Point of Sale</p>
      </div>

      <!-- Card -->
      <div class="card p-8">
        <h2 class="text-xl font-bold text-gray-900 mb-6">Masuk ke akun kamu</h2>

        <form @submit.prevent="handleLogin" class="space-y-4">
          <div>
            <label class="label">Username</label>
            <input v-model="form.username" type="text" class="input" placeholder="username" required autocomplete="username" />
          </div>
          <div>
            <label class="label">Password</label>
            <input v-model="form.password" type="password" class="input" placeholder="••••••••" required autocomplete="current-password" />
          </div>

          <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-xl">
            {{ error }}
          </div>

          <button type="submit" class="btn-primary w-full justify-center py-3 mt-2" :disabled="loading">
            <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            {{ loading ? 'Memproses...' : 'Masuk' }}
          </button>
        </form>

        <p class="text-center text-xs text-gray-400 mt-6">
          POS-AI SaaS &copy; {{ new Date().getFullYear() }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const error = ref('')
const form = reactive({ username: '', password: '' })

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    await auth.login(form.username, form.password)
    router.push('/')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Login gagal. Cek username dan password.'
  } finally {
    loading.value = false
  }
}
</script>
