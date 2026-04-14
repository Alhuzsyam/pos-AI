<template>
  <div class="p-6 max-w-6xl mx-auto">
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="page-title">Inventori</h1>
        <p class="page-subtitle">Kelola stok bahan baku & produk</p>
      </div>
      <button @click="showModal = true" class="btn-primary">+ Tambah Produk</button>
    </div>

    <!-- Filters -->
    <div class="flex gap-2 mb-4">
      <input v-model="search" class="input max-w-xs" placeholder="Cari produk..." />
      <button @click="lowStockOnly = !lowStockOnly" :class="['btn-sm', lowStockOnly ? 'btn-danger' : 'btn-secondary']">
        {{ lowStockOnly ? '🔴 Low Stock' : 'Semua Stok' }}
      </button>
    </div>

    <!-- Table -->
    <div class="card overflow-hidden">
      <table class="table-base">
        <thead>
          <tr>
            <th>Produk</th>
            <th>SKU</th>
            <th>Stok</th>
            <th>Unit</th>
            <th>Min</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in filtered" :key="p.id">
            <td>
              <p class="font-medium text-gray-800">{{ p.name }}</p>
              <p class="text-xs text-gray-400">{{ p.division || '-' }}</p>
            </td>
            <td class="font-mono text-xs text-gray-500">{{ p.sku || '-' }}</td>
            <td>
              <span :class="p.current_stock <= p.min_stock_level ? 'text-red-600 font-bold' : 'text-gray-800 font-semibold'">
                {{ p.current_stock }}
              </span>
            </td>
            <td class="text-gray-500">{{ p.unit }}</td>
            <td class="text-gray-400">{{ p.min_stock_level }}</td>
            <td>
              <span :class="p.current_stock === 0 ? 'badge-red' : p.current_stock <= p.min_stock_level ? 'badge-yellow' : 'badge-green'">
                {{ p.current_stock === 0 ? 'Habis' : p.current_stock <= p.min_stock_level ? 'Rendah' : 'OK' }}
              </span>
            </td>
            <td>
              <div class="flex gap-1">
                <button @click="openMovement(p, 'IN')" class="btn-secondary btn-sm">+ Stok</button>
                <button @click="openMovement(p, 'OUT')" class="btn-danger btn-sm">- Stok</button>
                <button @click="confirmDelete(p)" class="btn-sm border border-red-200 text-red-500 hover:bg-red-50 rounded-lg px-2 transition-colors" title="Hapus produk">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="!filtered.length">
            <td colspan="7" class="text-center text-gray-300 py-10">Tidak ada produk</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add Product Modal -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div class="card p-6 w-full max-w-md">
        <h2 class="font-serif text-[22px] text-claude-ink mb-5">Tambah Produk</h2>
        <form @submit.prevent="addProduct" class="space-y-3">
          <div><label class="label">Nama</label><input v-model="form.name" class="input" required /></div>
          <div><label class="label">SKU</label><input v-model="form.sku" class="input" placeholder="Opsional" /></div>
          <div class="grid grid-cols-2 gap-2">
            <div><label class="label">Stok Awal</label><input v-model.number="form.current_stock" type="number" class="input" /></div>
            <div><label class="label">Unit</label><input v-model="form.unit" class="input" placeholder="pcs, kg, liter" /></div>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div><label class="label">Min Stok</label><input v-model.number="form.min_stock_level" type="number" class="input" /></div>
            <div><label class="label">Divisi</label><input v-model="form.division" class="input" placeholder="Bar / Kitchen" /></div>
          </div>
          <div class="flex gap-2 pt-2">
            <button type="submit" class="btn-primary flex-1">Simpan</button>
            <button type="button" @click="showModal = false" class="btn-secondary flex-1">Batal</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Stock Movement Modal -->
    <div v-if="movModal.show" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div class="card p-6 w-full max-w-sm">
        <h2 class="font-serif text-[22px] text-claude-ink mb-1">{{ movModal.type === 'IN' ? 'Tambah' : 'Kurangi' }} Stok</h2>
        <p class="text-[13px] text-claude-slate mb-5">{{ movModal.product?.name }}</p>
        <div class="space-y-3">
          <div><label class="label">Jumlah</label><input v-model.number="movModal.qty" type="number" class="input" min="1" /></div>
          <div><label class="label">Catatan</label><input v-model="movModal.notes" class="input" placeholder="Opsional" /></div>
          <div class="flex gap-2">
            <button @click="submitMovement" :class="movModal.type === 'IN' ? 'btn-primary' : 'btn-danger'" class="flex-1">
              {{ movModal.type === 'IN' ? '+ Tambah Stok' : '- Kurangi Stok' }}
            </button>
            <button @click="movModal.show = false" class="btn-secondary flex-1">Batal</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirm Modal -->
    <div v-if="deleteTarget" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div class="card p-6 w-full max-w-sm">
        <h2 class="font-serif text-[20px] text-claude-ink mb-2">Hapus Produk?</h2>
        <p class="text-[13px] text-claude-slate mb-5">
          <span class="font-semibold text-red-600">{{ deleteTarget.name }}</span> akan dihapus permanen beserta riwayat stoknya.
        </p>
        <div class="flex gap-2">
          <button @click="doDelete" class="btn-danger flex-1" :disabled="deleting">
            {{ deleting ? 'Menghapus...' : 'Ya, Hapus' }}
          </button>
          <button @click="deleteTarget = null" class="btn-secondary flex-1">Batal</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import api from '@/composables/useApi'
import { useToast } from 'vue-toastification'

const toast = useToast()
const products = ref([])
const search = ref('')
const lowStockOnly = ref(false)
const showModal = ref(false)
const form = reactive({ name: '', sku: '', current_stock: 0, unit: 'pcs', min_stock_level: 5, division: '' })
const movModal = reactive({ show: false, product: null, type: 'IN', qty: 1, notes: '' })
const deleteTarget = ref(null)
const deleting = ref(false)

const filtered = computed(() =>
  products.value.filter(p =>
    (!search.value || p.name.toLowerCase().includes(search.value.toLowerCase())) &&
    (!lowStockOnly.value || p.current_stock <= p.min_stock_level)
  )
)

async function loadProducts() {
  const res = await api.get('/api/v1/inventory/products')
  products.value = res.data
}

async function addProduct() {
  try {
    await api.post('/api/v1/inventory/products', form)
    toast.success('Produk ditambahkan')
    showModal.value = false
    loadProducts()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal tambah produk')
  }
}

function openMovement(product, type) {
  movModal.product = product
  movModal.type = type
  movModal.qty = 1
  movModal.notes = ''
  movModal.show = true
}

async function submitMovement() {
  try {
    await api.post('/api/v1/inventory/movements', {
      product_id: movModal.product.id,
      qty_change: movModal.type === 'IN' ? movModal.qty : -movModal.qty,
      transaction_type: movModal.type,
      raw_input_text: movModal.notes,
    })
    toast.success('Stok diupdate')
    movModal.show = false
    loadProducts()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal update stok')
  }
}

function confirmDelete(product) {
  deleteTarget.value = product
}

async function doDelete() {
  deleting.value = true
  try {
    await api.delete(`/api/v1/inventory/products/${deleteTarget.value.id}`)
    toast.success('Produk dihapus')
    deleteTarget.value = null
    loadProducts()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal hapus produk')
  } finally {
    deleting.value = false
  }
}

onMounted(loadProducts)
</script>
