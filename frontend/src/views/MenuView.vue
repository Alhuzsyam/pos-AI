<template>
  <div class="p-6 max-w-5xl mx-auto">
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="page-title">Kelola Menu</h1>
        <p class="page-subtitle">Daftar menu yang dijual di POS</p>
      </div>
      <button @click="openAdd" class="btn-primary">+ Tambah Menu</button>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="item in menu" :key="item.id" class="card p-5">
        <div class="flex items-center justify-between mb-3">
          <div class="w-10 h-10 bg-brand-50 border border-brand-100 rounded-lg flex items-center justify-center text-[18px]">
            {{ divIcon(item.division) }}
          </div>
          <span :class="item.is_available ? 'badge-green' : 'badge-red'">{{ item.is_available ? 'Aktif' : 'Nonaktif' }}</span>
        </div>
        <h3 class="font-serif text-[17px] text-claude-ink leading-tight">{{ item.name }}</h3>
        <p class="text-[11px] text-claude-dust mt-0.5 mb-2 uppercase tracking-wide">{{ item.category || item.division }}</p>
        <p class="text-brand-600 font-semibold text-[15px]">{{ formatRp(item.price) }}</p>

        <!-- Recipes/Ingredients preview -->
        <div v-if="item.recipes && item.recipes.length" class="mt-2 pt-2 border-t border-claude-line">
          <p class="text-[11px] text-claude-dust uppercase tracking-wide mb-1">Bahan Baku:</p>
          <div v-for="r in item.recipes" :key="r.id" class="text-[12px] text-claude-slate">
            {{ r.product_name }} ({{ r.amount_needed }} {{ r.product_unit }})
          </div>
        </div>
        <div v-else class="mt-2 pt-2 border-t border-claude-line">
          <p class="text-[11px] text-claude-dust italic">Belum ada resep</p>
        </div>

        <div class="flex gap-2 mt-3">
          <button @click="openEdit(item)" class="btn-secondary btn-sm flex-1">Edit</button>
          <button @click="toggleAvail(item)" :class="item.is_available ? 'btn-danger' : 'btn-primary'" class="btn-sm flex-1">
            {{ item.is_available ? 'Nonaktifkan' : 'Aktifkan' }}
          </button>
        </div>
      </div>
      <div v-if="!menu.length" class="col-span-full text-center text-claude-dust py-16 font-serif text-[16px]">Belum ada menu</div>
    </div>

    <!-- Modal Add/Edit Menu -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div class="card p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <h2 class="font-serif text-[22px] text-claude-ink mb-5">{{ editItem ? 'Edit Menu' : 'Tambah Menu' }}</h2>
        <form @submit.prevent="saveMenu" class="space-y-3">
          <div><label class="label">Nama Menu</label><input v-model="form.name" class="input" required /></div>
          <div><label class="label">Harga (Rp)</label><input v-model.number="form.price" type="number" class="input" required /></div>
          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="label">Divisi</label>
              <select v-model="form.division" class="input">
                <option v-for="d in divisions" :key="d" :value="d">{{ d }}</option>
              </select>
            </div>
            <div><label class="label">Kategori</label><input v-model="form.category" class="input" placeholder="Minuman, Makanan" /></div>
          </div>
          <div><label class="label">Deskripsi</label><input v-model="form.description" class="input" /></div>

          <!-- Recipe / Ingredient Section -->
          <div class="border-t border-claude-line pt-3 mt-3">
            <div class="flex items-center justify-between mb-2">
              <label class="label mb-0">Resep / Bahan Baku</label>
              <button type="button" @click="addRecipeRow" class="text-brand-600 text-[12px] font-medium hover:underline">+ Tambah Bahan</button>
            </div>
            <div v-for="(r, idx) in form.recipes" :key="idx" class="flex gap-2 mb-2 items-end">
              <div class="flex-1">
                <select v-model="r.product_id" class="input text-[13px]" required>
                  <option value="" disabled>Pilih produk...</option>
                  <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }} ({{ p.unit }})</option>
                </select>
              </div>
              <div class="w-24">
                <input v-model.number="r.amount_needed" type="number" step="0.1" min="0.1" class="input text-[13px]" placeholder="Qty" required />
              </div>
              <button type="button" @click="form.recipes.splice(idx, 1)" class="text-red-500 hover:text-red-700 pb-2">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
              </button>
            </div>
            <p v-if="!form.recipes.length" class="text-[12px] text-claude-dust italic">Belum ada bahan. Klik "+ Tambah Bahan" untuk menambahkan.</p>
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

const toast = useToast()
const menu = ref([])
const products = ref([])
const divisions = ref(['Bar', 'Kitchen', 'Titipan'])
const showModal = ref(false)
const editItem = ref(null)
const form = reactive({ name: '', price: 0, division: 'Bar', category: '', description: '', recipes: [] })

const formatRp = (n) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(n)

function divIcon(div) {
  const icons = { Kitchen: '🍳', Bar: '☕', Titipan: '📦' }
  return icons[div] || '🍽️'
}

async function loadMenu() {
  const res = await api.get('/api/v1/pos/menu?available_only=false')
  menu.value = res.data
}

async function loadProducts() {
  try {
    const res = await api.get('/api/v1/inventory/products')
    products.value = res.data
  } catch { products.value = [] }
}

function openAdd() {
  editItem.value = null
  Object.assign(form, { name: '', price: 0, division: 'Bar', category: '', description: '', recipes: [] })
  showModal.value = true
}

function openEdit(item) {
  editItem.value = item
  Object.assign(form, {
    name: item.name,
    price: item.price,
    division: item.division,
    category: item.category || '',
    description: item.description || '',
    recipes: (item.recipes || []).map(r => ({ product_id: r.product_id, amount_needed: r.amount_needed })),
  })
  showModal.value = true
}

function addRecipeRow() {
  form.recipes.push({ product_id: '', amount_needed: 1 })
}

async function saveMenu() {
  try {
    const payload = {
      name: form.name,
      price: form.price,
      division: form.division,
      category: form.category,
      description: form.description,
      recipes: form.recipes.filter(r => r.product_id),
    }
    if (editItem.value) {
      await api.patch(`/api/v1/pos/menu/${editItem.value.id}`, payload)
    } else {
      await api.post('/api/v1/pos/menu', payload)
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

async function loadDivisions() {
  try {
    const res = await api.get('/api/v1/settings/')
    divisions.value = res.data.divisions || ['Bar', 'Kitchen', 'Titipan']
  } catch {}
}

onMounted(() => { loadMenu(); loadProducts(); loadDivisions() })
</script>
