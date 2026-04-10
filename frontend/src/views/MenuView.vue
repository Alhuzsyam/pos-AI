<template>
  <div class="p-6 max-w-5xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Kelola Menu</h1>
      <button @click="openAdd" class="btn-primary">+ Tambah Menu</button>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="item in menu" :key="item.id" class="card p-4">
        <div class="flex items-center justify-between mb-2">
          <div class="w-10 h-10 bg-brand-50 rounded-xl flex items-center justify-center text-xl">
            {{ item.division === 'Kitchen' ? '🍳' : '☕' }}
          </div>
          <span :class="item.is_available ? 'badge-green' : 'badge-red'">{{ item.is_available ? 'Aktif' : 'Nonaktif' }}</span>
        </div>
        <h3 class="font-semibold text-gray-900">{{ item.name }}</h3>
        <p class="text-xs text-gray-400 mb-1">{{ item.category || item.division }}</p>
        <p class="text-brand-700 font-bold">{{ formatRp(item.price) }}</p>
        <div class="flex gap-2 mt-3">
          <button @click="openEdit(item)" class="btn-secondary btn-sm flex-1">Edit</button>
          <button @click="toggleAvail(item)" :class="item.is_available ? 'btn-danger' : 'btn-primary'" class="btn-sm flex-1">
            {{ item.is_available ? 'Nonaktifkan' : 'Aktifkan' }}
          </button>
        </div>
      </div>
      <div v-if="!menu.length" class="col-span-full text-center text-gray-300 py-16">Belum ada menu</div>
    </div>

    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div class="card p-6 w-full max-w-md">
        <h2 class="font-bold text-gray-900 mb-4">{{ editItem ? 'Edit Menu' : 'Tambah Menu' }}</h2>
        <form @submit.prevent="saveMenu" class="space-y-3">
          <div><label class="label">Nama Menu</label><input v-model="form.name" class="input" required /></div>
          <div><label class="label">Harga (Rp)</label><input v-model.number="form.price" type="number" class="input" required /></div>
          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="label">Divisi</label>
              <select v-model="form.division" class="input">
                <option>Bar</option><option>Kitchen</option>
              </select>
            </div>
            <div><label class="label">Kategori</label><input v-model="form.category" class="input" placeholder="Minuman, Makanan" /></div>
          </div>
          <div><label class="label">Deskripsi</label><input v-model="form.description" class="input" /></div>
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

const toast = useToast()
const menu = ref([])
const showModal = ref(false)
const editItem = ref(null)
const form = reactive({ name: '', price: 0, division: 'Bar', category: '', description: '' })

const formatRp = (n) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(n)

async function loadMenu() {
  const res = await api.get('/api/v1/pos/menu?available_only=false')
  menu.value = res.data
}

function openAdd() {
  editItem.value = null
  Object.assign(form, { name: '', price: 0, division: 'Bar', category: '', description: '' })
  showModal.value = true
}

function openEdit(item) {
  editItem.value = item
  Object.assign(form, { name: item.name, price: item.price, division: item.division, category: item.category || '', description: item.description || '' })
  showModal.value = true
}

async function saveMenu() {
  try {
    if (editItem.value) {
      await api.patch(`/api/v1/pos/menu/${editItem.value.id}`, form)
    } else {
      await api.post('/api/v1/pos/menu', form)
    }
    toast.success('Menu disimpan')
    showModal.value = false
    loadMenu()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal simpan')
  }
}

async function toggleAvail(item) {
  await api.patch(`/api/v1/pos/menu/${item.id}`, { is_available: !item.is_available })
  loadMenu()
}

onMounted(loadMenu)
</script>
