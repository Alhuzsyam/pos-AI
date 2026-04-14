<template>
  <div class="p-6 max-w-5xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Reservasi Meja</h1>
      <button @click="openCreate" class="btn-primary">+ Buat Reservasi</button>
    </div>

    <!-- Filters: status + search -->
    <div class="flex gap-2 mb-4 flex-wrap items-center">
      <button v-for="s in ['', 'PENDING','CONFIRMED','SERVING','COMPLETED','CANCELLED']" :key="s"
        @click="setStatus(s)"
        :class="statusFilter === s ? 'btn-primary' : 'btn-secondary'"
        class="btn-sm capitalize">{{ s || 'Semua' }}</button>
      <div class="flex-1 min-w-[180px]">
        <input v-model="search" class="input w-full text-sm" placeholder="Cari nama / no HP..." />
      </div>
    </div>

    <!-- Result count -->
    <p class="text-xs text-gray-400 mb-3">
      Menampilkan {{ paginated.length }} dari {{ filtered.length }} reservasi
      <span v-if="search || statusFilter"> (difilter)</span>
    </p>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div v-for="res in paginated" :key="res.id" class="card p-5">
        <div class="flex items-center justify-between mb-3">
          <div>
            <p class="font-bold text-gray-900">{{ res.customer_name }}</p>
            <p class="text-xs text-gray-400">{{ res.phone || '-' }} · {{ res.pax }} pax</p>
          </div>
          <span :class="statusBadge(res.status)">{{ res.status }}</span>
        </div>
        <div class="text-sm text-gray-600 space-y-1">
          <p>📅 {{ formatDate(res.reservation_date) }}</p>
          <p>🪑 Meja: {{ res.table_number || '-' }}</p>
          <p>💰 DP: {{ formatRp(res.dp_amount) }} ({{ res.dp_method }})</p>
          <p v-if="res.total_amount">🧾 Total: {{ formatRp(res.total_amount) }}</p>
        </div>

        <!-- Items -->
        <div v-if="res.items?.length" class="mt-3 pt-3 border-t border-gray-100">
          <p class="text-xs font-semibold text-gray-500 uppercase mb-1">Item Pesanan</p>
          <div v-for="item in res.items" :key="item.id" class="flex justify-between text-sm text-gray-600">
            <span>{{ item.quantity }}x {{ item.menu_name }}</span>
            <span class="text-gray-400">{{ formatRp(item.quantity * item.price_at_moment) }}</span>
          </div>
        </div>

        <!-- Notes -->
        <p v-if="res.notes" class="text-xs text-gray-400 mt-2">{{ res.notes }}</p>

        <!-- Print buttons -->
        <div v-if="res.items?.length" class="flex gap-2 mt-3">
          <button @click="printDPReceipt(res)" class="btn-secondary btn-sm flex-1 text-xs" :disabled="printer.isPrinting.value">
            🧾 Struk DP
          </button>
          <button @click="printOrderList(res)" class="btn-secondary btn-sm flex-1 text-xs" :disabled="printer.isPrinting.value">
            📋 List Pesanan
          </button>
        </div>

        <!-- Settlement info -->
        <div v-if="res.settlement_amount != null && res.status !== 'PENDING' && res.status !== 'CONFIRMED'" class="mt-3 bg-blue-50 rounded-lg p-2 text-xs text-blue-700">
          Pelunasan: {{ formatRp(res.settlement_amount) }} via {{ res.settlement_method }}
        </div>

        <!-- Actions: PENDING -->
        <div class="flex gap-2 mt-4" v-if="res.status === 'PENDING'">
          <button @click="updateStatus(res, 'CONFIRMED')" class="btn-primary btn-sm flex-1">Konfirmasi</button>
          <button @click="updateStatus(res, 'CANCELLED')" class="btn-danger btn-sm flex-1">Batalkan</button>
        </div>

        <!-- Actions: CONFIRMED -->
        <div class="flex gap-2 mt-4" v-if="res.status === 'CONFIRMED'">
          <button @click="openServeModal(res)" class="btn-primary btn-sm flex-1">🍽️ Sajikan</button>
          <button @click="updateStatus(res, 'CANCELLED')" class="btn-danger btn-sm flex-1">Batalkan</button>
        </div>

        <!-- Actions: SERVING -->
        <div class="flex gap-2 mt-4" v-if="res.status === 'SERVING'">
          <button @click="completeReservation(res)" class="btn-primary btn-sm flex-1">Selesai</button>
        </div>
      </div>
      <div v-if="!filtered.length" class="col-span-full text-center text-gray-300 py-16">Tidak ada reservasi</div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex items-center justify-center gap-2 mt-6">
      <button @click="page--" :disabled="page === 1" class="btn-secondary btn-sm px-3" :class="{ 'opacity-40 cursor-not-allowed': page === 1 }">‹</button>
      <button v-for="p in pageNumbers" :key="p"
        @click="page = p"
        :class="['btn-sm px-3', page === p ? 'btn-primary' : 'btn-secondary']">{{ p }}</button>
      <button @click="page++" :disabled="page === totalPages" class="btn-secondary btn-sm px-3" :class="{ 'opacity-40 cursor-not-allowed': page === totalPages }">›</button>
      <span class="text-xs text-gray-400 ml-1">{{ page }} / {{ totalPages }}</span>
    </div>

    <!-- Create Modal -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div class="card p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <h2 class="font-bold text-gray-900 mb-4">Buat Reservasi</h2>
        <form @submit.prevent="createReservation" class="space-y-3">
          <div><label class="label">Nama Pelanggan</label><input v-model="form.customer_name" class="input" required /></div>
          <div><label class="label">No HP</label><input v-model="form.phone" class="input" /></div>
          <div class="grid grid-cols-2 gap-2">
            <div><label class="label">No Meja</label><input v-model="form.table_number" class="input" /></div>
            <div><label class="label">Jumlah Tamu</label><input v-model.number="form.pax" type="number" class="input" min="1" /></div>
          </div>
          <div><label class="label">Waktu Reservasi</label><input v-model="form.reservation_date" type="datetime-local" class="input" /></div>
          <div class="grid grid-cols-2 gap-2">
            <div><label class="label">DP (Rp)</label><input v-model.number="form.dp_amount" type="number" class="input" /></div>
            <div>
              <label class="label">Metode DP</label>
              <select v-model="form.dp_method" class="input">
                <option>CASH</option><option>TRANSFER</option><option>QRIS</option>
              </select>
            </div>
          </div>
          <div><label class="label">Catatan</label><input v-model="form.notes" class="input" /></div>

          <!-- Menu item picker -->
          <div class="border rounded-xl p-3">
            <div class="flex items-center justify-between mb-2">
              <label class="label mb-0">Item Pesanan (opsional)</label>
            </div>
            <input v-model="menuSearch" class="input mb-2 text-xs" placeholder="Cari menu untuk ditambahkan..." />
            <div v-if="menuSearch && filteredMenuList.length" class="border rounded-lg mb-2 max-h-32 overflow-y-auto">
              <button v-for="m in filteredMenuList" :key="m.id" type="button"
                @click="addMenuToForm(m)"
                class="w-full text-left px-3 py-1.5 text-sm hover:bg-brand-50 flex justify-between">
                <span>{{ m.name }}</span>
                <span class="text-brand-700 font-medium">{{ formatRp(m.price) }}</span>
              </button>
            </div>
            <div v-for="(item, i) in form.items" :key="i" class="flex items-center gap-2 mb-2">
              <span class="flex-1 text-sm truncate">{{ item.menu_name }}</span>
              <input v-model.number="item.quantity" type="number" min="1" class="input w-16 text-xs text-center" />
              <span class="text-xs text-gray-500 w-20 text-right">{{ formatRp(item.price_at_moment * item.quantity) }}</span>
              <button type="button" @click="form.items.splice(i, 1)" class="text-red-400 hover:text-red-600 text-sm">✕</button>
            </div>
            <p v-if="!form.items.length" class="text-xs text-gray-400 italic">Pesan item sekarang atau nanti saat sajikan</p>
            <div v-if="form.items.length" class="border-t pt-2 mt-2 flex justify-between text-sm font-semibold">
              <span>Total Item</span>
              <span class="text-brand-700">{{ formatRp(formItemsTotal) }}</span>
            </div>
          </div>

          <div class="flex gap-2 pt-2">
            <button type="submit" class="btn-primary flex-1">Buat Reservasi</button>
            <button type="button" @click="showModal = false" class="btn-secondary flex-1">Batal</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Serve Modal -->
    <div v-if="serveModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div class="card p-6 w-full max-w-sm">
        <h2 class="font-bold text-gray-900 mb-1">Sajikan Reservasi</h2>
        <p class="text-sm text-gray-500 mb-2">{{ serveTarget.customer_name }}</p>

        <div class="bg-gray-50 rounded-xl p-3 mb-4 space-y-1 text-sm">
          <div class="flex justify-between"><span class="text-gray-500">Total</span><span class="font-medium">{{ formatRp(serveTarget.total_amount || 0) }}</span></div>
          <div class="flex justify-between"><span class="text-gray-500">DP</span><span class="font-medium text-green-600">-{{ formatRp(serveTarget.dp_amount) }}</span></div>
          <div class="flex justify-between font-bold border-t pt-1"><span>Sisa Bayar</span><span class="text-brand-700">{{ formatRp((serveTarget.total_amount || 0) - serveTarget.dp_amount) }}</span></div>
        </div>

        <label class="label">Metode Pelunasan</label>
        <div class="flex gap-2 mb-4">
          <button v-for="m in ['CASH', 'QRIS', 'TRANSFER']" :key="m"
            @click="serveMethod = m"
            :class="['text-xs px-4 py-2 rounded-lg font-semibold border transition-all',
              serveMethod === m ? 'bg-brand-700 text-white border-brand-700' : 'bg-white text-gray-600 border-gray-200 hover:border-brand-400']"
          >{{ m }}</button>
        </div>

        <div class="flex gap-2">
          <button @click="confirmServe" class="btn-primary flex-1" :disabled="serving">{{ serving ? 'Memproses...' : 'Sajikan & Bayar' }}</button>
          <button @click="serveModal = false" class="btn-secondary flex-1">Batal</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, reactive } from 'vue'
import api from '@/composables/useApi'
import { useToast } from 'vue-toastification'
import dayjs from 'dayjs'
import { usePrinter } from '@/composables/usePrinter'

const toast = useToast()
const printer = usePrinter()
const reservations = ref([])
const menuItems = ref([])
const statusFilter = ref('')
const search = ref('')
const showModal = ref(false)
const menuSearch = ref('')

// Pagination
const PAGE_SIZE = 10
const page = ref(1)

const form = reactive({ customer_name: '', phone: '', table_number: '', pax: 2, reservation_date: '', dp_amount: 0, dp_method: 'CASH', notes: '', items: [] })

// Serve modal
const serveModal = ref(false)
const serveTarget = ref(null)
const serveMethod = ref('CASH')
const serving = ref(false)

const filtered = computed(() => {
  let list = reservations.value
  if (statusFilter.value) list = list.filter(r => r.status === statusFilter.value)
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(r =>
      r.customer_name.toLowerCase().includes(q) ||
      (r.phone && r.phone.includes(q))
    )
  }
  return list
})

const totalPages = computed(() => Math.ceil(filtered.value.length / PAGE_SIZE) || 1)

const paginated = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE
  return filtered.value.slice(start, start + PAGE_SIZE)
})

// Show up to 7 page numbers around current page
const pageNumbers = computed(() => {
  const total = totalPages.value
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const p = page.value
  const start = Math.max(1, p - 3)
  const end = Math.min(total, start + 6)
  return Array.from({ length: end - start + 1 }, (_, i) => start + i)
})

// Reset to page 1 when filter/search changes
watch([statusFilter, search], () => { page.value = 1 })

function setStatus(s) {
  statusFilter.value = s
  page.value = 1
}

const formItemsTotal = computed(() => form.items.reduce((s, i) => s + i.price_at_moment * i.quantity, 0))

const filteredMenuList = computed(() =>
  menuSearch.value ? menuItems.value.filter(m => m.name.toLowerCase().includes(menuSearch.value.toLowerCase())).slice(0, 8) : []
)

const formatRp = (n) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(n)
const formatDate = (d) => d ? dayjs(d).format('D MMM YYYY HH:mm') : '-'
const statusBadge = (s) => ({ PENDING: 'badge-yellow', CONFIRMED: 'badge-blue', SERVING: 'badge-purple', COMPLETED: 'badge-green', CANCELLED: 'badge-red' }[s] || 'badge-gray')

function openCreate() {
  Object.assign(form, { customer_name: '', phone: '', table_number: '', pax: 2, reservation_date: '', dp_amount: 0, dp_method: 'CASH', notes: '', items: [] })
  menuSearch.value = ''
  showModal.value = true
}

function addMenuToForm(m) {
  const existing = form.items.find(i => i.menu_item_id === m.id)
  if (existing) { existing.quantity++; return }
  form.items.push({ menu_item_id: m.id, menu_name: m.name, quantity: 1, price_at_moment: m.price })
  menuSearch.value = ''
}

function openServeModal(res) {
  serveTarget.value = res
  serveMethod.value = 'CASH'
  serveModal.value = true
}

async function loadReservations() {
  const res = await api.get('/api/v1/pos/reservations')
  reservations.value = res.data
}

async function loadMenu() {
  try {
    const res = await api.get('/api/v1/pos/menu?available_only=true')
    menuItems.value = res.data
  } catch {}
}

async function createReservation() {
  try {
    await api.post('/api/v1/pos/reservations', {
      customer_name: form.customer_name,
      phone: form.phone || null,
      table_number: form.table_number || null,
      pax: form.pax,
      reservation_date: form.reservation_date || null,
      dp_amount: form.dp_amount,
      dp_method: form.dp_method,
      notes: form.notes || null,
      items: form.items,
    })
    toast.success('Reservasi dibuat!')
    showModal.value = false
    loadReservations()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal buat reservasi')
  }
}

async function updateStatus(res, status) {
  try {
    await api.patch(`/api/v1/pos/reservations/${res.id}/status`, { status })
    toast.success(`Status: ${status}`)
    loadReservations()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal update status')
  }
}

async function confirmServe() {
  serving.value = true
  try {
    await api.post(`/api/v1/pos/reservations/${serveTarget.value.id}/serve`, { settlement_method: serveMethod.value })
    toast.success('Reservasi disajikan! Item masuk watchlist.')
    serveModal.value = false
    loadReservations()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal sajikan reservasi')
  } finally {
    serving.value = false
  }
}

async function completeReservation(res) {
  try {
    await api.patch(`/api/v1/pos/reservations/${res.id}/complete`)
    toast.success('Reservasi selesai!')
    loadReservations()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal selesaikan')
  }
}

async function printDPReceipt(res) {
  if (!printer.pairedDevice.value) {
    try { await printer.connectPrinter() } catch { toast.error('Hubungkan printer dulu di Pengaturan'); return }
  }
  try {
    const content = printer.buildReservationDPReceipt({
      customerName: res.customer_name,
      reservationDate: formatDate(res.reservation_date),
      items: res.items,
      totalAmount: res.total_amount,
      dpAmount: res.dp_amount,
      dpMethod: res.dp_method,
    })
    await printer.sendToPrinter(content)
    toast.success('Struk DP dicetak!')
  } catch (e) {
    toast.error('Gagal cetak: ' + (e.message || 'Unknown'))
  }
}

async function printOrderList(res) {
  if (!printer.pairedDevice.value) {
    try { await printer.connectPrinter() } catch { toast.error('Hubungkan printer dulu di Pengaturan'); return }
  }
  try {
    const content = printer.buildOrderList({
      customerName: res.customer_name,
      tableNumber: res.table_number,
      items: res.items,
    })
    await printer.sendToPrinter(content)
    toast.success('List pesanan dicetak!')
  } catch (e) {
    toast.error('Gagal cetak: ' + (e.message || 'Unknown'))
  }
}

onMounted(() => { loadReservations(); loadMenu() })
</script>
