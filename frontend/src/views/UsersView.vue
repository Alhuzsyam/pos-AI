<template>
  <div class="p-6 max-w-4xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Manajemen Pengguna</h1>
        <p class="text-sm text-gray-400">Kelola akses dan role pengguna dalam tenant ini</p>
      </div>
      <button @click="showModal = true" class="btn-primary">+ Tambah User</button>
    </div>

    <!-- Role Info -->
    <div class="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
      <div v-for="role in roles" :key="role.name" class="card p-3 text-center">
        <span class="text-xl">{{ role.emoji }}</span>
        <p class="text-xs font-bold text-gray-800 mt-1">{{ role.name }}</p>
        <p class="text-xs text-gray-400">{{ role.desc }}</p>
      </div>
    </div>

    <!-- Users Table -->
    <div class="card overflow-hidden">
      <table class="table-base">
        <thead>
          <tr>
            <th>Pengguna</th>
            <th>Role</th>
            <th>Status</th>
            <th>Terakhir Login</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>
              <div>
                <p class="font-medium text-gray-800">{{ user.full_name || user.username }}</p>
                <p class="text-xs text-gray-400">@{{ user.username }}</p>
              </div>
            </td>
            <td>
              <span :class="`badge-${roleColor(user.role)}`">{{ user.role }}</span>
            </td>
            <td>
              <span :class="user.is_active ? 'badge-green' : 'badge-red'">
                {{ user.is_active ? 'Aktif' : 'Nonaktif' }}
              </span>
            </td>
            <td class="text-xs text-gray-400">{{ formatDate(user.last_login) }}</td>
            <td>
              <div class="flex gap-2">
                <button @click="toggleActive(user)" class="btn-secondary btn-sm">
                  {{ user.is_active ? 'Nonaktifkan' : 'Aktifkan' }}
                </button>
                <button @click="deleteUser(user)" class="btn-danger btn-sm">Hapus</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div class="card p-6 w-full max-w-md">
        <h2 class="font-bold text-gray-900 mb-4">Tambah Pengguna</h2>
        <form @submit.prevent="createUser" class="space-y-3">
          <div><label class="label">Username</label><input v-model="form.username" class="input" required /></div>
          <div><label class="label">Nama Lengkap</label><input v-model="form.full_name" class="input" /></div>
          <div><label class="label">Email</label><input v-model="form.email" type="email" class="input" /></div>
          <div><label class="label">Password</label><input v-model="form.password" type="password" class="input" required /></div>
          <div>
            <label class="label">Role</label>
            <select v-model="form.role" class="input">
              <option v-for="r in ['admin','manager','kasir','inventory']" :key="r" :value="r">{{ r }}</option>
            </select>
          </div>
          <div class="flex gap-2 pt-2">
            <button type="submit" class="btn-primary flex-1">Simpan</button>
            <button type="button" @click="showModal = false" class="btn-secondary flex-1">Batal</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import api from '@/composables/useApi'
import { useToast } from 'vue-toastification'
import dayjs from 'dayjs'

const toast = useToast()
const users = ref([])
const showModal = ref(false)
const form = reactive({ username: '', full_name: '', email: '', password: '', role: 'kasir' })

const roles = [
  { name: 'superadmin', emoji: '👑', desc: 'Semua akses' },
  { name: 'admin', emoji: '🛡️', desc: 'Full 1 tenant' },
  { name: 'manager', emoji: '📋', desc: 'Report + staff' },
  { name: 'kasir', emoji: '💳', desc: 'POS + transaksi' },
  { name: 'inventory', emoji: '📦', desc: 'Kelola stok' },
]

const roleColor = (r) => ({ superadmin: 'blue', admin: 'green', manager: 'yellow', kasir: 'gray', inventory: 'blue' }[r] || 'gray')
const formatDate = (d) => d ? dayjs(d).format('D MMM YYYY HH:mm') : '-'

async function loadUsers() {
  const res = await api.get('/api/v1/users/')
  users.value = res.data
}

async function createUser() {
  try {
    await api.post('/api/v1/users/', form)
    toast.success('User berhasil dibuat')
    showModal.value = false
    Object.assign(form, { username: '', full_name: '', email: '', password: '', role: 'kasir' })
    loadUsers()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal membuat user')
  }
}

async function toggleActive(user) {
  await api.patch(`/api/v1/users/${user.id}`, { is_active: !user.is_active })
  loadUsers()
}

async function deleteUser(user) {
  if (!confirm(`Hapus user ${user.username}?`)) return
  try {
    await api.delete(`/api/v1/users/${user.id}`)
    toast.success('User dihapus')
    loadUsers()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal hapus')
  }
}

onMounted(loadUsers)
</script>
