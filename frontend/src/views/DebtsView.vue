<template>
  <div class="p-6 max-w-5xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Buku Hutang</h1>
      <button @click="openCreateModal" class="btn-primary">+ Catat Hutang</button>
    </div>

    <div class="flex gap-2 mb-3 flex-wrap items-center">
      <button @click="filterPaid = null" :class="filterPaid === null ? 'btn-primary' : 'btn-secondary'" class="btn-sm">Semua</button>
      <button @click="filterPaid = false" :class="filterPaid === false ? 'btn-primary' : 'btn-secondary'" class="btn-sm">Belum Lunas</button>
      <button @click="filterPaid = true" :class="filterPaid === true ? 'btn-primary' : 'btn-secondary'" class="btn-sm">Lunas</button>
    </div>
    <div class="flex gap-2 mb-4 flex-wrap items-center">
      <input v-model="dateFrom" type="date" class="input text-sm w-36" placeholder="Dari" />
      <span class="text-gray-400 text-sm">—</span>
      <input v-model="dateTo" type="date" class="input text-sm w-36" placeholder="Sampai" />
      <button v-if="dateFrom || dateTo" @click="dateFrom = ''; dateTo = ''" class="btn-secondary btn-sm text-xs">Reset</button>
      <p class="text-xs text-gray-400 ml-auto">{{ filteredDebts.length }} data</p>
    </div>

    <!-- Debts List -->
    <div class="space-y-3">
      <div v-for="debt in filteredDebts" :key="debt.id" class="card overflow-hidden">
        <!-- Header row (clickable to expand) -->
        <div class="flex items-center gap-4 p-4 cursor-pointer hover:bg-gray-50 transition-colors" @click="toggleExpand(debt.id)">
          <div class="flex-1 min-w-0">
            <p class="font-semibold text-gray-800">{{ debt.customer_name }}</p>
            <p class="text-xs text-gray-400">{{ debt.phone || '-' }} · {{ debt.items?.length || 0 }} item</p>
          </div>
          <div class="text-right">
            <p class="font-bold text-red-600">{{ formatRp(debt.total_amount) }}</p>
            <p class="text-xs text-gray-400">{{ debt.due_date || '-' }}</p>
          </div>
          <span :class="debt.is_paid ? 'badge-green' : 'badge-red'">{{ debt.is_paid ? 'Lunas' : 'Belum' }}</span>
          <svg :class="['w-5 h-5 text-gray-400 transition-transform', expanded === debt.id ? 'rotate-180' : '']" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </div>

        <!-- Expanded detail -->
        <div v-if="expanded === debt.id" class="border-t border-gray-100">
          <!-- Items table -->
          <div class="p-4">
            <p class="text-xs font-semibold text-gray-500 uppercase mb-2">Detail Item</p>
            <table class="w-full text-sm">
              <thead><tr class="text-left text-xs text-gray-400 border-b"><th class="pb-1">Menu</th><th class="pb-1 text-center">Qty</th><th class="pb-1 text-right">Harga</th><th class="pb-1 text-right">Subtotal</th></tr></thead>
              <tbody>
                <tr v-for="item in debt.items" :key="item.id" class="border-b border-gray-50">
                  <td class="py-1.5">{{ item.menu_name }}</td>
                  <td class="py-1.5 text-center">{{ item.quantity }}</td>
                  <td class="py-1.5 text-right text-gray-500">{{ formatRp(item.price_at_moment) }}</td>
                  <td class="py-1.5 text-right font-medium">{{ formatRp(item.quantity * item.price_at_moment) }}</td>
                </tr>
                <tr v-if="!debt.items?.length"><td colspan="4" class="py-3 text-center text-gray-300">Tidak ada item</td></tr>
              </tbody>
            </table>
          </div>

          <!-- Notes -->
          <div v-if="debt.notes" class="px-4 pb-3">
            <p class="text-xs text-gray-400">Catatan: <span class="text-gray-600">{{ debt.notes }}</span></p>
          </div>

          <!-- Paid info -->
          <div v-if="debt.is_paid" class="px-4 pb-4">
            <div class="bg-green-50 rounded-lg p-3 text-sm text-green-700">
              Lunas pada {{ formatDate(debt.paid_at) }} via <span class="font-semibold">{{ debt.payment_method }}</span>
            </div>
          </div>

          <!-- Actions for unpaid -->
          <div v-if="!debt.is_paid" class="px-4 pb-4 flex gap-2">
            <button @click.stop="openPayModal(debt)" class="btn-primary btn-sm flex-1">Lunaskan</button>
            <button @click.stop="openAddItemsModal(debt)" class="btn-secondary btn-sm flex-1">+ Tambah Item</button>
          </div>
        </div>
      </div>

      <div v-if="!filteredDebts.length" class="text-center text-gray-300 py-16">Tidak ada hutang</div>
    </div>

    <!-- Pay Modal -->
    <div v-if="payModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div class="card p-6 w-full max-w-sm">
        <h2 class="font-bold text-gray-900 mb-1">Lunaskan Hutang</h2>
        <p class="text-sm text-gray-500 mb-4">{{ payTarget.customer_name }} — {{ formatRp(payTarget.total_amount) }}</p>

        <label class="label">Metode Pembayaran</label>
        <div class="flex gap-2 mb-4">
          <button v-for="m in ['CASH', 'QRIS', 'TRANSFER']" :key="m"
            @click="payMethod = m"
            :class="['text-xs px-4 py-2 rounded-lg font-semibold border transition-all',
              payMethod === m ? 'bg-brand-700 text-white border-brand-700' : 'bg-white text-gray-600 border-gray-200 hover:border-brand-400']"
          >{{ m }}</button>
        </div>

        <div class="flex gap-2">
          <button @click="confirmPay" class="btn-primary flex-1" :disabled="paying">{{ paying ? 'Memproses...' : 'Konfirmasi Bayar' }}</button>
          <button @click="payModal = false" class="btn-secondary flex-1">Batal</button>
        </div>
      </div>
    </div>

    <!-- Create Debt Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div class="card p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
        <h2 class="font-bold text-gray-900 mb-4">Catat Hutang Baru</h2>
        <form @submit.prevent="createDebt" class="space-y-3">
          <div><label class="label">Nama Pelanggan</label><input v-model="form.customer_name" class="input" required /></div>
          <div class="grid grid-cols-2 gap-2">
            <div><label class="label">No HP</label><input v-model="form.phone" class="input" /></div>
            <div><label class="label">No Meja</label><input v-model="form.table_number" class="input" placeholder="A1" /></div>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div><label class="label">Jatuh Tempo</label><input v-model="form.due_date" type="date" class="input" /></div>
            <div><label class="label">Diskon (Rp)</label><input v-model.number="form.discount_amount" type="number" class="input" /></div>
          </div>
          <div><label class="label">Catatan</label><input v-model="form.notes" class="input" /></div>

          <!-- Menu item picker -->
          <div class="border rounded-xl p-3">
            <div class="flex items-center justify-between mb-2">
              <label class="label mb-0">Item Hutang</label>
            </div>
            <!-- Search menu -->
            <input v-model="menuSearch" class="input mb-2 text-xs" placeholder="Cari menu untuk ditambahkan..." />
            <div v-if="menuSearch && filteredMenuItems.length" class="border rounded-lg mb-2 max-h-32 overflow-y-auto">
              <button v-for="m in filteredMenuItems" :key="m.id" type="button"
                @click="addMenuToForm(m)"
                class="w-full text-left px-3 py-1.5 text-sm hover:bg-brand-50 flex justify-between">
                <span>{{ m.name }}</span>
                <span class="text-brand-700 font-medium">{{ formatRp(m.price) }}</span>
              </button>
            </div>
            <!-- Selected items -->
            <div v-for="(item, i) in form.items" :key="i" class="flex items-center gap-2 mb-2">
              <span class="flex-1 text-sm truncate">{{ item.menu_name }}</span>
              <input v-model.number="item.quantity" type="number" min="1" class="input w-16 text-xs text-center" />
              <span class="text-xs text-gray-500 w-20 text-right">{{ formatRp(item.price_at_moment * item.quantity) }}</span>
              <button type="button" @click="form.items.splice(i, 1)" class="text-red-400 hover:text-red-600 text-sm">✕</button>
            </div>
            <p v-if="!form.items.length" class="text-xs text-gray-400 italic">Cari dan pilih menu di atas</p>
            <div v-if="form.items.length" class="border-t pt-2 mt-2 flex justify-between text-sm font-semibold">
              <span>Total</span>
              <span class="text-brand-700">{{ formatRp(formTotal) }}</span>
            </div>
          </div>

          <div class="flex gap-2 pt-2">
            <button type="submit" class="btn-primary flex-1" :disabled="!form.items.length">Simpan</button>
            <button type="button" @click="showCreateModal = false" class="btn-secondary flex-1">Batal</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Add Items Modal -->
    <div v-if="addItemsModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div class="card p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
        <h2 class="font-bold text-gray-900 mb-1">Tambah Item</h2>
        <p class="text-sm text-gray-500 mb-4">{{ addItemsTarget.customer_name }} — sisa {{ formatRp(addItemsTarget.total_amount) }}</p>

        <input v-model="menuSearch2" class="input mb-2 text-xs" placeholder="Cari menu..." />
        <div v-if="menuSearch2 && filteredMenuItems2.length" class="border rounded-lg mb-2 max-h-32 overflow-y-auto">
          <button v-for="m in filteredMenuItems2" :key="m.id" type="button"
            @click="addMenuToNewItems(m)"
            class="w-full text-left px-3 py-1.5 text-sm hover:bg-brand-50 flex justify-between">
            <span>{{ m.name }}</span>
            <span class="text-brand-700 font-medium">{{ formatRp(m.price) }}</span>
          </button>
        </div>

        <div v-for="(item, i) in newItems" :key="i" class="flex items-center gap-2 mb-2">
          <span class="flex-1 text-sm truncate">{{ item.menu_name }}</span>
          <input v-model.number="item.quantity" type="number" min="1" class="input w-16 text-xs text-center" />
          <span class="text-xs text-gray-500 w-20 text-right">{{ formatRp(item.price_at_moment * item.quantity) }}</span>
          <button type="button" @click="newItems.splice(i, 1)" class="text-red-400 hover:text-red-600 text-sm">✕</button>
        </div>
        <p v-if="!newItems.length" class="text-xs text-gray-400 italic mb-3">Cari dan pilih menu di atas</p>

        <div v-if="newItems.length" class="border-t pt-2 mb-3 flex justify-between text-sm font-semibold">
          <span>Tambahan</span>
          <span class="text-red-600">+{{ formatRp(newItemsTotal) }}</span>
        </div>

        <div class="flex gap-2">
          <button @click="submitAddItems" class="btn-primary flex-1" :disabled="!newItems.length || addingItems">{{ addingItems ? 'Menyimpan...' : 'Tambahkan' }}</button>
          <button @click="addItemsModal = false" class="btn-secondary flex-1">Batal</button>
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
const debts = ref([])
const menuItems = ref([])
const filterPaid = ref(null)
const dateFrom = ref('')
const dateTo = ref('')
const expanded = ref(null)

// Create modal
const showCreateModal = ref(false)
const menuSearch = ref('')
const form = reactive({ customer_name: '', phone: '', table_number: '', due_date: '', notes: '', items: [], discount_amount: 0 })

// Pay modal
const payModal = ref(false)
const payTarget = ref(null)
const payMethod = ref('CASH')
const paying = ref(false)

// Add items modal
const addItemsModal = ref(false)
const addItemsTarget = ref(null)
const newItems = ref([])
const menuSearch2 = ref('')
const addingItems = ref(false)

const filteredDebts = computed(() => {
  let list = filterPaid.value === null ? debts.value : debts.value.filter(d => d.is_paid === filterPaid.value)
  if (dateFrom.value) list = list.filter(d => d.created_at && d.created_at >= dateFrom.value)
  if (dateTo.value) list = list.filter(d => d.created_at && d.created_at.slice(0, 10) <= dateTo.value)
  return list
})

const formTotal = computed(() => form.items.reduce((s, i) => s + i.price_at_moment * i.quantity, 0))
const newItemsTotal = computed(() => newItems.value.reduce((s, i) => s + i.price_at_moment * i.quantity, 0))

const filteredMenuItems = computed(() =>
  menuSearch.value ? menuItems.value.filter(m => m.name.toLowerCase().includes(menuSearch.value.toLowerCase())).slice(0, 8) : []
)
const filteredMenuItems2 = computed(() =>
  menuSearch2.value ? menuItems.value.filter(m => m.name.toLowerCase().includes(menuSearch2.value.toLowerCase())).slice(0, 8) : []
)

const formatRp = (n) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(n)
const formatDate = (d) => d ? new Date(d).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' }) : '-'

function toggleExpand(id) { expanded.value = expanded.value === id ? null : id }

function openCreateModal() {
  Object.assign(form, { customer_name: '', phone: '', table_number: '', due_date: '', notes: '', items: [], discount_amount: 0 })
  menuSearch.value = ''
  showCreateModal.value = true
}

function addMenuToForm(m) {
  const existing = form.items.find(i => i.menu_item_id === m.id)
  if (existing) { existing.quantity++; return }
  form.items.push({ menu_item_id: m.id, menu_name: m.name, quantity: 1, price_at_moment: m.price })
  menuSearch.value = ''
}

function addMenuToNewItems(m) {
  const existing = newItems.value.find(i => i.menu_item_id === m.id)
  if (existing) { existing.quantity++; return }
  newItems.value.push({ menu_item_id: m.id, menu_name: m.name, quantity: 1, price_at_moment: m.price })
  menuSearch2.value = ''
}

function openPayModal(debt) {
  payTarget.value = debt
  payMethod.value = 'CASH'
  payModal.value = true
}

function openAddItemsModal(debt) {
  addItemsTarget.value = debt
  newItems.value = []
  menuSearch2.value = ''
  addItemsModal.value = true
}

async function loadDebts() {
  try {
    const res = await api.get('/api/v1/pos/debts')
    debts.value = res.data
  } catch (e) {
    toast.error('Gagal memuat data hutang')
  }
}

async function loadMenu() {
  try {
    const res = await api.get('/api/v1/pos/menu?available_only=true')
    menuItems.value = res.data
  } catch {}
}

async function createDebt() {
  if (!form.items.length) { toast.error('Tambah minimal 1 item'); return }
  try {
    await api.post('/api/v1/pos/debts', {
      customer_name: form.customer_name,
      phone: form.phone || null,
      table_number: form.table_number || null,
      due_date: form.due_date || null,
      notes: form.notes || null,
      discount_amount: form.discount_amount,
      items: form.items,
    })
    toast.success('Hutang dicatat! Item masuk watchlist.')
    showCreateModal.value = false
    loadDebts()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal catat hutang')
  }
}

async function confirmPay() {
  paying.value = true
  try {
    await api.patch(`/api/v1/pos/debts/${payTarget.value.id}/pay`, { payment_method: payMethod.value })
    toast.success(`Hutang dilunasi via ${payMethod.value}!`)
    payModal.value = false
    loadDebts()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal lunasi hutang')
  } finally {
    paying.value = false
  }
}

async function submitAddItems() {
  addingItems.value = true
  try {
    await api.post(`/api/v1/pos/debts/${addItemsTarget.value.id}/add-items`, { items: newItems.value })
    toast.success('Item ditambahkan! Masuk watchlist.')
    addItemsModal.value = false
    loadDebts()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal tambah item')
  } finally {
    addingItems.value = false
  }
}

onMounted(() => { loadDebts(); loadMenu() })
</script>
