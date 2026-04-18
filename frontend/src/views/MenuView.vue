<template>
  <div class="p-6 max-w-5xl mx-auto">
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="page-title">Kelola Menu</h1>
        <p class="page-subtitle">Daftar menu yang dijual di POS</p>
      </div>
      <button @click="openAdd" class="btn-primary">+ Tambah Menu</button>
    </div>

    <!-- Filter bar -->
    <div class="flex flex-col gap-2 mb-5">
      <input v-model="search" class="input max-w-xs" placeholder="Cari menu..." />
      <div class="flex items-center gap-1.5">
        <div class="flex gap-1.5 overflow-x-auto pb-0.5 flex-1" style="scrollbar-width:none">
          <button
            @click="filterDiv = ''"
            :class="['flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all',
              filterDiv === '' ? 'bg-brand-700 text-white border-brand-700' : 'bg-white text-gray-600 border-gray-200 hover:border-brand-400']"
          >Semua</button>
          <button
            v-for="d in activeDivisions" :key="d"
            @click="filterDiv = d"
            :class="['flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all',
              filterDiv === d ? 'bg-brand-700 text-white border-brand-700' : 'bg-white text-gray-600 border-gray-200 hover:border-brand-400']"
          ><span class="mr-1">{{ divIcon(d) }}</span>{{ d }}</button>
        </div>
        <button @click="openDivSettings"
          :class="['flex-shrink-0 p-1.5 rounded-lg border transition-colors', showDivSettings ? 'bg-brand-50 border-brand-300 text-brand-700' : 'border-gray-200 text-gray-400 hover:bg-gray-50']"
          title="Atur divisi filter">
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
          </svg>
        </button>
      </div>

      <!-- Inline settings panel -->
      <div v-if="showDivSettings" class="bg-gray-50 border border-gray-200 rounded-xl p-3 space-y-2">
        <p class="text-xs font-semibold text-gray-600">Pilih divisi yang tampil di filter:</p>
        <div class="flex flex-wrap gap-1.5">
          <label v-for="d in divisions" :key="d"
            class="flex items-center gap-1.5 px-2.5 py-1 rounded-full border cursor-pointer transition-all select-none text-xs font-semibold"
            :class="menuSelected.includes(d) ? 'bg-brand-700 border-brand-700 text-white' : 'bg-white border-gray-200 text-gray-600 hover:border-brand-400'">
            <input type="checkbox" :value="d" v-model="menuSelected" class="hidden" />
            <span>{{ divIcon(d) }}</span>{{ d }}
          </label>
        </div>
        <div class="flex gap-2">
          <button @click="saveMenuDivSettings" class="btn-primary btn-sm text-xs">Simpan</button>
          <button @click="showDivSettings = false" class="btn-secondary btn-sm text-xs">Batal</button>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="item in filteredMenu" :key="item.id" class="card p-5">
        <div class="flex items-center justify-between mb-3">
          <div class="w-10 h-10 bg-brand-50 border border-brand-100 rounded-lg flex items-center justify-center text-[18px]">
            {{ divIcon(item.division) }}
          </div>
          <span :class="item.is_available ? 'badge-green' : 'badge-red'">{{ item.is_available ? 'Aktif' : 'Nonaktif' }}</span>
        </div>
        <h3 class="font-serif text-[17px] text-claude-ink leading-tight">{{ item.name }}</h3>
        <p class="text-[11px] text-claude-dust mt-0.5 mb-2 uppercase tracking-wide">{{ item.category || item.division }}</p>
        <p class="text-brand-600 font-semibold text-[15px]">{{ formatRp(item.price) }}</p>

        <!-- Recipes/Ingredients preview (collapsible) -->
        <div class="mt-2 pt-2 border-t border-claude-line">
          <button
            v-if="item.recipes && item.recipes.length"
            @click="toggleRecipes(item.id)"
            class="flex items-center gap-1 text-[11px] text-claude-dust uppercase tracking-wide hover:text-claude-ink transition-colors"
          >
            <svg
              :class="['w-3 h-3 transition-transform duration-200', expandedRecipes.has(item.id) ? 'rotate-90' : '']"
              fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"/>
            </svg>
            Bahan Baku ({{ item.recipes.length }})
          </button>
          <p v-else class="text-[11px] text-claude-dust italic">Belum ada resep</p>
          <div v-if="expandedRecipes.has(item.id)" class="mt-1.5 space-y-0.5">
            <div v-for="r in item.recipes" :key="r.id" class="text-[12px] text-claude-slate">
              {{ r.product_name }} ({{ r.amount_needed }} {{ r.product_unit }})
            </div>
          </div>
        </div>

        <div class="flex gap-2 mt-3">
          <button @click="openEdit(item)" class="btn-secondary btn-sm flex-1">Edit</button>
          <button @click="toggleAvail(item)" :class="item.is_available ? 'btn-danger' : 'btn-primary'" class="btn-sm flex-1">
            {{ item.is_available ? 'Nonaktif' : 'Aktifkan' }}
          </button>
          <button @click="confirmDelete(item)" class="btn-sm border border-red-200 text-red-500 hover:bg-red-50 rounded-lg px-2 transition-colors" title="Hapus menu">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
          </button>
        </div>
      </div>
      <div v-if="!filteredMenu.length" class="col-span-full text-center text-claude-dust py-16 font-serif text-[16px]">
        {{ search || filterDiv ? 'Tidak ada menu yang cocok' : 'Belum ada menu' }}
      </div>
    </div>

    <!-- Delete Confirm Modal -->
    <div v-if="deleteTarget" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div class="card p-6 w-full max-w-sm">
        <h2 class="font-serif text-[20px] text-claude-ink mb-2">Hapus Menu?</h2>
        <p class="text-[13px] text-claude-slate mb-5">
          Menu <span class="font-semibold text-red-600">{{ deleteTarget.name }}</span> akan dihapus permanen dari daftar POS.
        </p>
        <div class="flex gap-2">
          <button @click="doDelete" class="btn-danger flex-1" :disabled="deleting">
            {{ deleting ? 'Menghapus...' : 'Ya, Hapus' }}
          </button>
          <button @click="deleteTarget = null" class="btn-secondary flex-1">Batal</button>
        </div>
      </div>
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
import { ref, computed, onMounted, reactive } from 'vue'
import api from '@/composables/useApi'
import { useToast } from 'vue-toastification'

const toast = useToast()
const menu = ref([])
const products = ref([])
const divisions = ref(['Bar', 'Kitchen', 'Titipan'])
const search = ref('')
const filterDiv = ref('')
const activeDivisions = ref([])
const menuSelected = ref([])
const showDivSettings = ref(false)
const LS_MENU = 'menu_divisions_v1'

const filteredMenu = computed(() =>
  menu.value.filter(m =>
    (!search.value || m.name.toLowerCase().includes(search.value.toLowerCase())) &&
    (!filterDiv.value || m.division === filterDiv.value)
  )
)

function openDivSettings() {
  menuSelected.value = [...activeDivisions.value]
  showDivSettings.value = !showDivSettings.value
}

function saveMenuDivSettings() {
  localStorage.setItem(LS_MENU, JSON.stringify(menuSelected.value))
  activeDivisions.value = [...menuSelected.value]
  if (filterDiv.value && !activeDivisions.value.includes(filterDiv.value)) filterDiv.value = ''
  showDivSettings.value = false
}

const showModal = ref(false)
const editItem = ref(null)
const form = reactive({ name: '', price: 0, division: 'Bar', category: '', description: '', recipes: [] })
const deleteTarget = ref(null)
const deleting = ref(false)
const expandedRecipes = ref(new Set())

const formatRp = (n) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(n)

function toggleRecipes(id) {
  if (expandedRecipes.value.has(id)) {
    expandedRecipes.value.delete(id)
  } else {
    expandedRecipes.value.add(id)
  }
  expandedRecipes.value = new Set(expandedRecipes.value)
}

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
  Object.assign(form, { name: '', price: 0, division: divisions.value[0] || '', category: '', description: '', recipes: [] })
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

function confirmDelete(item) {
  deleteTarget.value = item
}

async function doDelete() {
  deleting.value = true
  try {
    await api.delete(`/api/v1/pos/menu/${deleteTarget.value.id}`)
    toast.success('Menu dihapus')
    deleteTarget.value = null
    loadMenu()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal hapus menu')
  } finally {
    deleting.value = false
  }
}

async function loadDivisions() {
  try {
    const res = await api.get('/api/v1/settings/')
    const divs = res.data.divisions || ['Bar', 'Kitchen', 'Titipan']
    divisions.value = divs
    const raw = localStorage.getItem(LS_MENU)
    const local = raw ? JSON.parse(raw).filter(d => divs.includes(d)) : null
    activeDivisions.value = local?.length ? local : [...divs]
  } catch {}
}

onMounted(() => { loadMenu(); loadProducts(); loadDivisions() })
</script>
