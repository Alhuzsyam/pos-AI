<template>
  <div class="min-h-screen flex flex-col bg-[#faf9f5]">
    <!-- Top brand bar -->
    <header class="px-8 py-6">
      <span class="font-serif text-xl text-[#1f1e1d]">POS-AI</span>
    </header>

    <!-- Centered login -->
    <main class="flex-1 flex items-center justify-center px-6 pb-24">
      <div class="w-full max-w-[400px]">
        <!-- Heading -->
        <div class="text-center mb-10">
          <h1 class="font-serif text-[44px] leading-[1.05] tracking-tight text-[#1f1e1d]">
            Masuk ke POS-AI
          </h1>
          <p class="mt-4 text-[15px] text-[#6b6558]">
            Multi-Tenant Point of Sale dengan AI
          </p>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleLogin" class="space-y-4">
          <div>
            <label for="username" class="block text-[13px] font-medium text-[#3d3929] mb-2">
              Username
            </label>
            <input
              id="username"
              v-model="form.username"
              type="text"
              placeholder="username"
              autocomplete="username"
              required
              class="w-full px-4 py-3 bg-white border border-[#e5e1d8] rounded-lg text-[15px] text-[#1f1e1d] placeholder-[#b8b0a3] focus:outline-none focus:border-[#c96442] focus:ring-2 focus:ring-[#c96442]/15 transition"
            />
          </div>

          <div>
            <label for="password" class="block text-[13px] font-medium text-[#3d3929] mb-2">
              Password
            </label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              placeholder="••••••••"
              autocomplete="current-password"
              required
              class="w-full px-4 py-3 bg-white border border-[#e5e1d8] rounded-lg text-[15px] text-[#1f1e1d] placeholder-[#b8b0a3] focus:outline-none focus:border-[#c96442] focus:ring-2 focus:ring-[#c96442]/15 transition"
            />
          </div>

          <!-- Error -->
          <div
            v-if="error"
            class="text-[13px] text-[#b54a2a] bg-[#fbf0ec] border border-[#f1d9cf] rounded-lg px-3.5 py-2.5"
          >
            {{ error }}
          </div>

          <!-- Submit -->
          <button
            type="submit"
            :disabled="loading"
            class="w-full flex items-center justify-center gap-2 bg-[#c96442] hover:bg-[#b5573a] disabled:opacity-60 disabled:cursor-not-allowed text-white font-medium py-3 rounded-lg transition-colors text-[15px] mt-2"
          >
            <svg
              v-if="loading"
              class="w-4 h-4 animate-spin"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              />
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            <span>{{ loading ? 'Memproses...' : 'Lanjut' }}</span>
          </button>
        </form>

        <!-- Fine print -->
        <p class="text-center text-[12px] text-[#a8a195] mt-10 leading-relaxed">
          Dengan masuk, kamu menyetujui penggunaan sistem POS-AI
          <br />
          sesuai kebijakan tenant kamu.
        </p>
      </div>
    </main>

    <!-- Footer -->
    <footer class="px-8 py-6 text-center text-[12px] text-[#a8a195]">
      POS-AI SaaS &copy; {{ new Date().getFullYear() }}
    </footer>
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
    error.value =
      err.response?.data?.detail || 'Login gagal. Cek username dan password.'
  } finally {
    loading.value = false
  }
}
</script>
