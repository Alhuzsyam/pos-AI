<template>
  <div class="h-full flex flex-col md:flex-row">
    <!-- Menu Grid -->
    <div class="flex-1 flex flex-col overflow-hidden border-r border-gray-100">
      <div class="p-4 border-b border-gray-100 flex gap-2">
        <input v-model="search" class="input flex-1" placeholder="Cari menu..." />
        <select v-model="filterDiv" class="input w-auto">
          <option value="">Semua</option>
          <option v-for="d in divisions" :key="d" :value="d">{{ d }}</option>
        </select>
      </div>
      <div class="flex-1 overflow-y-auto p-4 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 content-start">
        <button
          v-for="item in filteredMenu"
          :key="item.id"
          @click="addToCart(item)"
          class="card p-4 text-left hover:ring-2 hover:ring-brand-400 transition-all active:scale-95"
        >
          <div class="w-10 h-10 bg-brand-50 rounded-xl flex items-center justify-center mb-3">
            <span class="text-xl">{{ divIcon(item.division) }}</span>
          </div>
          <p class="text-sm font-semibold text-gray-800 leading-tight">{{ item.name }}</p>
          <p class="text-xs text-brand-700 font-bold mt-1">{{ formatRp(item.price) }}</p>
          <span class="badge-gray text-xs mt-1">{{ item.division }}</span>
        </button>
        <div v-if="!filteredMenu.length" class="col-span-full text-center text-gray-300 py-16">
          Menu tidak ditemukan
        </div>
      </div>
    </div>

    <!-- Cart -->
    <div class="w-full md:w-80 flex flex-col bg-white">
      <div class="p-4 border-b border-gray-100">
        <h2 class="font-bold text-gray-900">Keranjang</h2>
        <p class="text-xs text-gray-400">{{ cart.length }} item</p>
      </div>

      <div class="flex-1 overflow-y-auto p-4 space-y-3">
        <div v-if="!cart.length" class="text-center text-gray-300 py-10 text-sm">Keranjang kosong</div>
        <div v-for="item in cart" :key="item.id" class="flex items-center gap-3">
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
              @click="order.paymentMethod = method"
              :class="['text-xs px-3 py-1.5 rounded-lg font-semibold border transition-all',
                order.paymentMethod === method
                  ? 'bg-brand-700 text-white border-brand-700'
                  : 'bg-white text-gray-600 border-gray-200 hover:border-brand-400']"
            >{{ method }}</button>
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

const order = reactive({ customerName: '', tableNumber: '', paymentMethod: 'CASH', discount: 0, isDebt: false, phone: '' })

const filteredMenu = computed(() =>
  menu.value.filter(m =>
    (!search.value || m.name.toLowerCase().includes(search.value.toLowerCase())) &&
    (!filterDiv.value || m.division === filterDiv.value)
  )
)

const subtotal = computed(() => cart.value.reduce((s, i) => s + i.price * i.qty, 0))

const formatRp = (n) =>
  new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(n)

function divIcon(div) {
  const icons = { Kitchen: '🍳', Bar: '☕', Titipan: '📦' }
  return icons[div] || '🍽️'
}

function addToCart(item) {
  const existing = cart.value.find(c => c.id === item.id)
  if (existing) { existing.qty++; return }
  cart.value.push({ id: item.id, name: item.name, price: item.price, qty: 1 })
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
    // Auto-print receipt (only for non-debt)
    if (!order.isDebt && res.data?.id) {
      try { await printReceipt(res.data.id) } catch {}
    }
    cart.value = []
    order.customerName = ''
    order.tableNumber = ''
    order.discount = 0
    order.isDebt = false
    order.phone = ''
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal proses transaksi')
  } finally {
    loading.value = false
  }
}

async function printReceipt(saleId) {
  const res = await api.get(`/api/v1/pos/sales/${saleId}/receipt`)
  const r = res.data

  // Try Bluetooth first
  if (printer.pairedDevice.value) {
    try {
      const content = printer.buildSaleReceipt({
        storeName: r.store_name,
        storeAddress: r.store_address,
        storePhone: r.store_phone,
        transactionCode: r.transaction_code,
        date: r.date,
        cashier: r.cashier,
        customerName: r.customer_name,
        tableNumber: r.table_number,
        items: r.items.map(i => ({ menu_name: i.name, quantity: i.qty, price_at_moment: i.subtotal / i.qty })),
        totalAmount: r.total_amount,
        discountAmount: r.discount_amount,
        finalAmount: r.final_amount,
        paymentMethod: r.payment_method,
      })
      await printer.sendToPrinter(content)
      toast.success('Struk dicetak via Bluetooth!')
      return
    } catch (e) {
      console.warn('Bluetooth print failed, fallback to browser:', e)
    }
  }

  // Fallback: browser print
  const itemsHtml = r.items.map(i =>
    `<tr><td style="text-align:left">${i.qty}x ${i.name}</td><td style="text-align:right">${formatRp(i.subtotal)}</td></tr>`
  ).join('')
  const html = `
    <div style="font-family:'Courier New',monospace;width:280px;padding:10px;font-size:12px;color:#000">
      <div style="text-align:center;margin-bottom:8px">
        <div style="font-size:16px;font-weight:bold">${r.store_name}</div>
        ${r.store_address ? '<div style="font-size:10px">' + r.store_address + '</div>' : ''}
        ${r.store_phone ? '<div style="font-size:10px">' + r.store_phone + '</div>' : ''}
      </div>
      <div style="border-top:1px dashed #000;margin:6px 0"></div>
      <div style="font-size:11px"><div>${r.transaction_code}</div><div>${r.date}</div><div>Kasir: ${r.cashier}</div>
        ${r.customer_name ? '<div>Customer: ' + r.customer_name + '</div>' : ''}
        ${r.table_number ? '<div>Meja: ' + r.table_number + '</div>' : ''}
      </div>
      <div style="border-top:1px dashed #000;margin:6px 0"></div>
      <table style="width:100%;font-size:11px;border-collapse:collapse">${itemsHtml}</table>
      <div style="border-top:1px dashed #000;margin:6px 0"></div>
      <table style="width:100%;font-size:11px">
        <tr><td>Subtotal</td><td style="text-align:right">${formatRp(r.total_amount)}</td></tr>
        ${r.discount_amount ? '<tr><td>Diskon</td><td style="text-align:right">-' + formatRp(r.discount_amount) + '</td></tr>' : ''}
        <tr style="font-weight:bold;font-size:13px"><td>TOTAL</td><td style="text-align:right">${formatRp(r.final_amount)}</td></tr>
      </table>
      <div style="border-top:1px dashed #000;margin:6px 0"></div>
      <div style="text-align:center;font-size:10px"><div>Bayar: ${r.payment_method}</div><div style="margin-top:6px">Terima kasih!</div></div>
    </div>`
  const pw = window.open('', '_blank', 'width=320,height=600')
  pw.document.write(`<html><head><title>Struk</title><style>@media print{body{margin:0}@page{size:80mm auto;margin:0}}</style></head><body>${html}</body></html>`)
  pw.document.close()
  pw.focus()
  setTimeout(() => pw.print(), 300)
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
