<template>
  <div class="h-full flex flex-col md:flex-row">
    <!-- Menu Panel -->
    <div
      class="flex-1 flex-col overflow-hidden border-r border-gray-100"
      :class="mobileView === 'cart' ? 'hidden md:flex' : 'flex'"
    >
      <!-- Search + Tab Filter -->
      <div class="p-3 md:p-4 border-b border-gray-100 space-y-2">
        <input v-model="search" class="input w-full" placeholder="Cari menu..." />
        <div class="flex gap-1.5 overflow-x-auto pb-0.5" style="scrollbar-width:none;-webkit-overflow-scrolling:touch">
          <button
            @click="filterDiv = ''"
            :class="['flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all',
              filterDiv === '' ? 'bg-brand-700 text-white border-brand-700' : 'bg-white text-gray-600 border-gray-200 hover:border-brand-400']"
          >Semua</button>
          <button
            v-for="d in divisions" :key="d"
            @click="filterDiv = d"
            :class="['flex-shrink-0 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all',
              filterDiv === d ? 'bg-brand-700 text-white border-brand-700' : 'bg-white text-gray-600 border-gray-200 hover:border-brand-400']"
          ><span class="mr-1">{{ divIcon(d) }}</span>{{ d }}</button>
        </div>
      </div>

      <!-- Menu Grid -->
      <div class="flex-1 overflow-y-auto p-3 md:p-4 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2 md:gap-3 content-start pb-24 md:pb-4">
        <button
          v-for="item in filteredMenu"
          :key="item.id"
          @click="addToCart(item)"
          class="card p-3 md:p-4 text-left hover:ring-2 hover:ring-brand-400 transition-all active:scale-95"
        >
          <div class="w-8 h-8 md:w-10 md:h-10 bg-brand-50 rounded-xl flex items-center justify-center mb-2 md:mb-3">
            <span class="text-lg md:text-xl">{{ divIcon(item.division) }}</span>
          </div>
          <p class="text-sm font-semibold text-gray-800 leading-tight">{{ item.name }}</p>
          <p class="text-xs text-brand-700 font-bold mt-1">{{ formatRp(item.price) }}</p>
          <span class="badge-gray text-xs mt-1">{{ item.division }}</span>
        </button>
        <div v-if="!filteredMenu.length" class="col-span-full text-center text-gray-300 py-16">
          Menu tidak ditemukan
        </div>
      </div>

      <!-- Mobile: floating cart button -->
      <div class="md:hidden fixed bottom-4 right-4 z-20">
        <button
          @click="mobileView = 'cart'"
          class="relative flex items-center gap-2 bg-brand-700 text-white px-4 py-3 rounded-2xl shadow-lg font-semibold text-sm active:scale-95 transition-all"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/>
          </svg>
          Keranjang
          <span v-if="cart.length" class="absolute -top-1.5 -right-1.5 bg-red-500 text-white text-[10px] font-bold rounded-full w-5 h-5 flex items-center justify-center">
            {{ cart.length }}
          </span>
        </button>
      </div>
    </div>

    <!-- Cart -->
    <div
      class="w-full md:w-80 flex-col bg-white"
      :class="mobileView === 'menu' ? 'hidden md:flex' : 'flex'"
    >
      <div class="p-4 border-b border-gray-100 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <!-- Mobile back to menu -->
          <button @click="mobileView = 'menu'" class="md:hidden p-1.5 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7"/>
            </svg>
          </button>
          <div>
            <h2 class="font-bold text-gray-900">Keranjang</h2>
            <p class="text-xs text-gray-400">{{ cart.length }} item</p>
          </div>
        </div>
        <!-- Printer status + connect button -->
        <button
          @click="connectPrinter"
          :disabled="printer.isConnecting.value"
          :class="[
            'flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] font-medium border transition-all',
            printer.pairedDevice.value
              ? 'border-green-200 text-green-700 bg-green-50 hover:bg-green-100'
              : 'border-gray-200 text-gray-500 bg-gray-50 hover:bg-gray-100'
          ]"
        >
          <span :class="printer.pairedDevice.value ? 'text-green-500' : 'text-gray-400'">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"/>
            </svg>
          </span>
          {{ printer.isConnecting.value ? 'Connecting...' : printer.pairedDevice.value ? 'Printer OK' : 'Hubungkan' }}
        </button>
      </div>

      <div class="flex-1 overflow-y-auto p-4 space-y-3">
        <div v-if="!cart.length" class="text-center text-gray-300 py-10 text-sm">Keranjang kosong</div>
        <div v-for="item in cart" :key="item.id" class="space-y-1">
          <div class="flex items-center gap-3">
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-gray-800 truncate">{{ item.name }}</p>
              <p class="text-xs text-gray-400">{{ formatRp(item.price) }} x {{ item.qty }}</p>
            </div>
            <div class="flex items-center gap-1">
              <button @click="decQty(item)" class="w-6 h-6 rounded-lg bg-gray-100 text-gray-600 flex items-center justify-center text-sm hover:bg-red-50 hover:text-red-600">-</button>
              <span class="w-6 text-center text-sm font-bold">{{ item.qty }}</span>
              <button @click="incQty(item)" class="w-6 h-6 rounded-lg bg-gray-100 text-gray-600 flex items-center justify-center text-sm hover:bg-brand-50 hover:text-brand-700">+</button>
            </div>
            <p class="text-sm font-semibold text-brand-700 w-20 text-right">{{ formatRp(item.price * item.qty) }}</p>
          </div>
          <input
            v-model="item.note"
            class="w-full text-xs border border-gray-100 rounded-lg px-2 py-1 text-gray-600 placeholder-gray-300 focus:outline-none focus:border-brand-300 bg-gray-50"
            placeholder="Catatan (misal: tanpa bawang, extra pedas...)"
          />
        </div>
      </div>

      <!-- Order Info -->
      <div class="p-4 border-t border-gray-100 space-y-3">
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="label">Nama Pelanggan</label>
            <input v-model="order.customerName" class="input" :placeholder="order.isDebt ? 'Wajib untuk hutang' : 'Opsional'" :required="order.isDebt" />
          </div>
          <div>
            <label class="label">No Meja</label>
            <input v-model="order.tableNumber" class="input" placeholder="A1" />
          </div>
        </div>

        <!-- Phone (shown when debt mode) -->
        <div v-if="order.isDebt">
          <label class="label">No HP (opsional)</label>
          <input v-model="order.phone" class="input" placeholder="08xx" />
        </div>

        <div v-if="!order.isDebt">
          <label class="label">Pembayaran</label>
          <div class="flex gap-2 flex-wrap">
            <button
              v-for="method in ['CASH', 'QRIS', 'TRANSFER', 'DEBIT']"
              :key="method"
              @click="order.paymentMethod = method; cashReceived = 0"
              :class="['text-xs px-3 py-1.5 rounded-lg font-semibold border transition-all',
                order.paymentMethod === method
                  ? 'bg-brand-700 text-white border-brand-700'
                  : 'bg-white text-gray-600 border-gray-200 hover:border-brand-400']"
            >{{ method }}</button>
          </div>
        </div>

        <!-- Cash received + kembalian -->
        <div v-if="!order.isDebt && order.paymentMethod === 'CASH'" class="space-y-2">
          <label class="label">Uang Diterima</label>
          <input
            v-model.number="cashReceived"
            type="number"
            class="input"
            placeholder="Masukkan nominal..."
            @focus="cashReceived === 0 ? cashReceived = '' : null"
          />
          <!-- Quick denomination buttons -->
          <div class="flex gap-1.5 flex-wrap">
            <button
              v-for="nom in quickNominals"
              :key="nom"
              @click="cashReceived = nom"
              class="text-[11px] px-2 py-1 rounded-md border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors font-medium"
            >{{ formatNom(nom) }}</button>
          </div>
          <!-- Kembalian -->
          <div
            v-if="cashReceived > 0"
            :class="[
              'rounded-xl p-3 flex justify-between items-center text-sm font-semibold',
              change >= 0 ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'
            ]"
          >
            <span>{{ change >= 0 ? 'Kembalian' : 'Kurang' }}</span>
            <span>{{ formatRp(Math.abs(change)) }}</span>
          </div>
        </div>

        <!-- Total -->
        <div class="bg-gray-50 rounded-xl p-3 space-y-1">
          <div class="flex justify-between text-sm text-gray-500">
            <span>Subtotal</span>
            <span>{{ formatRp(subtotal) }}</span>
          </div>
          <div class="flex justify-between text-sm text-gray-500">
            <span>Diskon</span>
            <input v-model.number="order.discount" type="number" class="w-24 text-right bg-transparent border-b border-dashed border-gray-300 text-sm focus:outline-none" />
          </div>
          <div class="flex justify-between font-bold text-gray-900 pt-1 border-t border-gray-200">
            <span>Total</span>
            <span class="text-brand-700">{{ formatRp(subtotal - order.discount) }}</span>
          </div>
        </div>

        <!-- Two buttons: Bayar + Utang -->
        <div class="flex gap-2">
          <button
            @click="order.isDebt = false; checkout()"
            :disabled="!cart.length || loading"
            class="btn-primary flex-1 justify-center py-3"
          >
            <svg v-if="loading && !order.isDebt" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            Bayar
          </button>
          <button
            @click="order.isDebt = true; checkout()"
            :disabled="!cart.length || loading"
            class="flex-1 justify-center py-3 rounded-lg font-semibold text-sm border-2 border-red-400 text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50"
          >
            Hutang
          </button>
        </div>

        <!-- Cetak Struk — muncul setelah transaksi berhasil -->
        <div v-if="lastSaleId" class="flex gap-2">
          <button
            @click="printReceipt(lastSaleId)"
            :disabled="printer.isPrinting.value"
            class="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg border-2 border-brand-400 text-brand-700 text-sm font-semibold hover:bg-brand-50 transition-colors"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"/>
            </svg>
            {{ printer.isPrinting.value ? 'Mencetak...' : 'Cetak Struk' }}
          </button>
          <button @click="lastSaleId = null" class="px-3 py-2.5 rounded-lg border border-gray-200 text-gray-400 hover:text-gray-600 text-sm transition-colors">
            Lewati
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import api from '@/composables/useApi'
import { useToast } from 'vue-toastification'
import { usePrinter } from '@/composables/usePrinter'

const toast = useToast()
const printer = usePrinter()
const menu = ref([])
const cart = ref([])
const search = ref('')
const filterDiv = ref('')
const loading = ref(false)
const divisions = ref(['Bar', 'Kitchen', 'Titipan'])
const mobileView = ref('menu')
const lastSaleId = ref(null)

async function connectPrinter() {
  try {
    await printer.connectPrinter()
    toast.success('Printer terhubung: ' + printer.pairedDevice.value?.name)
  } catch (e) {
    if (e.name !== 'NotFoundError') toast.error('Gagal hubungkan printer')
  }
}

const order = reactive({ customerName: '', tableNumber: '', paymentMethod: 'CASH', discount: 0, isDebt: false, phone: '' })
const cashReceived = ref(0)

const filteredMenu = computed(() =>
  menu.value.filter(m =>
    (!search.value || m.name.toLowerCase().includes(search.value.toLowerCase())) &&
    (!filterDiv.value || m.division === filterDiv.value)
  )
)

const subtotal = computed(() => cart.value.reduce((s, i) => s + i.price * i.qty, 0))
const totalAfterDiscount = computed(() => subtotal.value - order.discount)
const change = computed(() => cashReceived.value - totalAfterDiscount.value)

// Quick nominal buttons: round up total to nearest denominations
const quickNominals = computed(() => {
  const t = totalAfterDiscount.value
  const denoms = [1000, 2000, 5000, 10000, 20000, 50000, 100000]
  const result = []
  for (const d of denoms) {
    const rounded = Math.ceil(t / d) * d
    if (rounded >= t && !result.includes(rounded) && result.length < 5) result.push(rounded)
  }
  return result
})

const formatRp = (n) =>
  new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(n)

const formatNom = (n) =>
  n >= 1000 ? (n / 1000) + 'rb' : n.toString()

function divIcon(div) {
  const icons = { Kitchen: '🍳', Bar: '☕', Titipan: '📦' }
  return icons[div] || '🍽️'
}

function addToCart(item) {
  const existing = cart.value.find(c => c.id === item.id)
  if (existing) { existing.qty++; return }
  cart.value.push({ id: item.id, name: item.name, price: item.price, qty: 1, note: '' })
}

function incQty(item) { item.qty++ }
function decQty(item) {
  if (item.qty <= 1) { cart.value = cart.value.filter(c => c.id !== item.id); return }
  item.qty--
}

async function checkout() {
  if (!cart.value.length) return
  if (order.isDebt && !order.customerName) {
    toast.error('Nama pelanggan wajib untuk hutang')
    return
  }
  loading.value = true
  try {
    const items = cart.value.map(i => ({
      menu_item_id: i.id,
      menu_name: i.name,
      quantity: i.qty,
      price_at_moment: i.price,
      note: i.note || null,
    }))
    const res = await api.post('/api/v1/pos/sales', {
      items,
      customer_name: order.customerName || null,
      table_number: order.tableNumber || null,
      payment_method: order.paymentMethod,
      discount_amount: order.discount,
      is_debt: order.isDebt,
      phone: order.phone || null,
    })
    toast.success(order.isDebt ? 'Hutang tercatat! Item masuk watchlist.' : 'Transaksi berhasil!')
    // Simpan sale ID untuk tombol "Cetak Struk" (hanya non-debt)
    lastSaleId.value = (!order.isDebt && res.data?.id) ? res.data.id : null
    cart.value = []
    order.customerName = ''
    order.tableNumber = ''
    order.discount = 0
    order.isDebt = false
    order.phone = ''
    cashReceived.value = 0
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal proses transaksi')
  } finally {
    loading.value = false
  }
}

async function printReceipt(saleId) {
  if (!printer.pairedDevice.value) {
    try { await printer.connectPrinter() } catch {
      toast.error('Printer belum terhubung. Klik "Hubungkan" dulu.')
      return
    }
  }
  try {
    const res = await api.get(`/api/v1/pos/sales/${saleId}/receipt`)
    const r = res.data
    const content = printer.buildSaleReceipt({
      storeName: r.store_name,
      storeAddress: r.store_address,
      storePhone: r.store_phone,
      transactionCode: r.transaction_code,
      date: r.date,
      cashier: r.cashier,
      customerName: r.customer_name,
      tableNumber: r.table_number,
      items: r.items.map(i => ({ menu_name: i.name, quantity: i.qty, price_at_moment: i.price })),
      totalAmount: r.total_amount,
      discountAmount: r.discount_amount,
      finalAmount: r.final_amount,
      paymentMethod: r.payment_method,
    })
    await printer.sendToPrinter(content)
    toast.success('Struk dicetak!')
    lastSaleId.value = null
  } catch (e) {
    toast.error('Gagal cetak: ' + (e.message || 'Unknown error'))
  }
}

async function loadDivisions() {
  try {
    const res = await api.get('/api/v1/settings/')
    divisions.value = res.data.divisions || ['Bar', 'Kitchen', 'Titipan']
  } catch {}
}

onMounted(async () => {
  const [menuRes] = await Promise.all([
    api.get('/api/v1/pos/menu?available_only=true'),
    loadDivisions(),
  ])
  menu.value = menuRes.data
})
</script>
