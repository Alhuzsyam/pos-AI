<template>
  <div class="p-6 max-w-5xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Manajemen Tenant</h1>
        <p class="text-sm text-gray-400">Kelola semua cafe & toko yang terdaftar</p>
      </div>
      <button @click="showModal = true" class="btn-primary">+ Tambah Tenant</button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="tenant in tenants" :key="tenant.id" class="card p-5">
        <div class="flex items-center justify-between mb-3">
          <div class="w-10 h-10 bg-brand-50 rounded-xl flex items-center justify-center">
            <span class="text-xl">🏪</span>
          </div>
          <span :class="tenant.is_active ? 'badge-green' : 'badge-red'">
            {{ tenant.is_active ? 'Aktif' : 'Nonaktif' }}
          </span>
        </div>
        <h3 class="font-bold text-gray-900">{{ tenant.name }}</h3>
        <p class="text-xs text-gray-400 mb-1">@{{ tenant.slug }}</p>
        <div class="flex items-center justify-between mt-3">
          <span :class="`badge-${tenant.plan === 'enterprise' ? 'blue' : tenant.plan === 'pro' ? 'yellow' : 'gray'}`">
            {{ tenant.plan }}
          </span>
          <span class="text-xs text-gray-400">{{ tenant.user_count }} users</span>
        </div>
        <div class="flex gap-2 mt-4">
          <button @click="toggleTenant(tenant)" class="btn-secondary btn-sm flex-1">
            {{ tenant.is_active ? 'Nonaktifkan' : 'Aktifkan' }}
          </button>
          <button @click="deleteTenant(tenant)" class="btn-danger btn-sm">Hapus</button>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div class="card p-6 w-full max-w-md max-h-screen overflow-y-auto">
        <h2 class="font-bold text-gray-900 mb-4">Buat Tenant Baru</h2>
        <form @submit.prevent="createTenant" class="space-y-3">
          <div><label class="label">Nama Toko</label><input v-model="form.name" class="input" required /></div>
          <div><label class="label">Slug (URL)</label><input v-model="form.slug" class="input" required placeholder="nama-toko" /></div>
          <div>
            <label class="label">Plan</label>
            <select v-model="form.plan" class="input">
              <option value="basic">Basic</option>
              <option value="pro">Pro</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>
          <div><label class="label">Alamat</label><input v-model="form.address" class="input" /></div>
          <div><label class="label">Telepon</label><input v-model="form.phone" class="input" /></div>
          <hr class="my-2" />
          <p class="text-xs font-bold text-gray-500 uppercase">Admin Pertama</p>
          <div><label class="label">Username Admin</label><input v-model="form.admin_username" class="input" required /></div>
          <div><label class="label">Password Admin</label><input v-model="form.admin_password" type="password" class="input" required /></div>
          <div><label class="label">Email Admin</label><input v-model="form.admin_email" type="email" class="input" /></div>
          <div class="flex gap-2 pt-2">
            <button type="submit" class="btn-primary flex-1">Buat Tenant</button>
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

const toast = useToast()
const tenants = ref([])
const showModal = ref(false)
const form = reactive({
  name: '', slug: '', plan: 'basic', address: '', phone: '',
  admin_username: '', admin_password: '', admin_email: '', admin_full_name: ''
})

async function loadTenants() {
  const res = await api.get('/api/v1/tenants/')
  tenants.value = res.data
}

async function createTenant() {
  try {
    await api.post('/api/v1/tenants/', form)
    toast.success('Tenant berhasil dibuat')
    showModal.value = false
    loadTenants()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal membuat tenant')
  }
}

async function toggleTenant(tenant) {
  await api.patch(`/api/v1/tenants/${tenant.id}`, { is_active: !tenant.is_active })
  loadTenants()
}

async function deleteTenant(tenant) {
  if (!confirm(`Hapus tenant ${tenant.name}? Semua data akan hilang!`)) return
  try {
    await api.delete(`/api/v1/tenants/${tenant.id}`)
    toast.success('Tenant dihapus')
    loadTenants()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal hapus')
  }
}

onMounted(loadTenants)
</script>
