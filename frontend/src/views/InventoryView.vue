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
      <input v-model="search" @input="currentPage = 1" class="input max-w-xs" placeholder="Cari produk..." />
      <button @click="toggleLowStock" :class="['btn-sm', lowStockOnly ? 'btn-danger' : 'btn-secondary']">
        {{ lowStockOnly ? '🔴 Low Stock' : 'Semua Stok' }}
      </button>
      <div class="ml-auto flex items-center gap-2 text-sm text-gray-500">
        <span>Tampilkan</span>
        <select v-model="pageSize" @change="currentPage = 1" class="input py-1 w-16">
          <option :value="10">10</option>
          <option :value="25">25</option>
          <option :value="50">50</option>
        </select>
        <span>per halaman</span>
      </div>
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
          <tr v-for="p in paginated" :key="p.id">
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
                <button @click="openEdit(p)" class="btn-sm border border-blue-200 text-blue-500 hover:bg-blue-50 rounded-lg px-2 transition-colors" title="Edit produk">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
                </button>
                <button @click="confirmDelete(p)" class="btn-sm border border-red-200 text-red-500 hover:bg-red-50 rounded-lg px-2 transition-colors" title="Hapus produk">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="!paginated.length">
            <td colspan="7" class="text-center text-gray-300 py-10">Tidak ada produk</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex items-center justify-between mt-4 text-sm text-gray-500">
      <span>Menampilkan {{ (currentPage - 1) * pageSize + 1 }}–{{ Math.min(currentPage * pageSize, filtered.length) }} dari {{ filtered.length }} produk</span>
      <div class="flex items-center gap-1">
        <button @click="currentPage = 1" :disabled="currentPage === 1" class="btn-sm btn-secondary px-2 disabled:opacity-40">«</button>
        <button @click="currentPage--" :disabled="currentPage === 1" class="btn-sm btn-secondary px-2 disabled:opacity-40">‹</button>
        <template v-for="p in pageNumbers" :key="p">
          <span v-if="p === '...'" class="px-2 text-gray-400">...</span>
          <button v-else @click="currentPage = p" :class="['btn-sm px-3 rounded-lg', p === currentPage ? 'btn-primary' : 'btn-secondary']">{{ p }}</button>
        </template>
        <button @click="currentPage++" :disabled="currentPage === totalPages" class="btn-sm btn-secondary px-2 disabled:opacity-40">›</button>
        <button @click="currentPage = totalPages" :disabled="currentPage === totalPages" class="btn-sm btn-secondary px-2 disabled:opacity-40">»</button>
      </div>
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

    <!-- Edit Product Modal -->
    <div v-if="editTarget" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div class="card p-6 w-full max-w-md">
        <h2 class="font-serif text-[22px] text-claude-ink mb-5">Edit Produk</h2>
        <form @submit.prevent="updateProduct" class="space-y-3">
          <div><label class="label">Nama</label><input v-model="editForm.name" class="input" required /></div>
          <div><label class="label">SKU</label><input v-model="editForm.sku" class="input" placeholder="Opsional" /></div>
          <div class="grid grid-cols-2 gap-2">
            <div><label class="label">Stok Saat Ini</label><input v-model.number="editForm.current_stock" type="number" class="input" /></div>
            <div><label class="label">Unit</label><input v-model="editForm.unit" class="input" placeholder="pcs, kg, liter" /></div>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div><label class="label">Min Stok</label><input v-model.number="editForm.min_stock_level" type="number" class="input" /></div>
            <div><label class="label">Divisi</label><input v-model="editForm.division" class="input" placeholder="Bar / Kitchen" /></div>
          </div>
          <div class="flex gap-2 pt-2">
            <button type="submit" class="btn-primary flex-1" :disabled="saving">{{ saving ? 'Menyimpan...' : 'Simpan' }}</button>
            <button type="button" @click="editTarget = null" class="btn-secondary flex-1">Batal</button>
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
const editTarget = ref(null)
const editForm = reactive({ name: '', sku: '', current_stock: 0, unit: '', min_stock_level: 0, division: '' })
const saving = ref(false)

// Pagination
const currentPage = ref(1)
const pageSize = ref(10)

const filtered = computed(() =>
  products.value.filter(p =>
    (!search.value || p.name.toLowerCase().includes(search.value.toLowerCase())) &&
    (!lowStockOnly.value || p.current_stock <= p.min_stock_level)
  )
)

const totalPages = computed(() => Math.ceil(filtered.value.length / pageSize.value))

const paginated = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filtered.value.slice(start, start + pageSize.value)
})

const pageNumbers = computed(() => {
  const total = totalPages.value
  const cur = currentPage.value
  const pages = []
  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i)
  } else {
    pages.push(1)
    if (cur > 3) pages.push('...')
    for (let i = Math.max(2, cur - 1); i <= Math.min(total - 1, cur + 1); i++) pages.push(i)
    if (cur < total - 2) pages.push('...')
    pages.push(total)
  }
  return pages
})

function toggleLowStock() {
  lowStockOnly.value = !lowStockOnly.value
  currentPage.value = 1
}

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

function openEdit(product) {
  editTarget.value = product
  Object.assign(editForm, {
    name: product.name,
    sku: product.sku || '',
    current_stock: product.current_stock,
    unit: product.unit,
    min_stock_level: product.min_stock_level,
    division: product.division || '',
  })
}

async function updateProduct() {
  saving.value = true
  try {
    await api.put(`/api/v1/inventory/products/${editTarget.value.id}`, editForm)
    toast.success('Produk diperbarui')
    editTarget.value = null
    loadProducts()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal update produk')
  } finally {
    saving.value = false
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
