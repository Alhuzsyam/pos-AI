<template>
  <div class="h-full flex flex-col md:flex-row">
    <!-- Menu Grid -->
    <div class="flex-1 flex flex-col overflow-hidden border-r border-gray-100">
      <div class="p-4 border-b border-gray-100 flex gap-2">
        <input v-model="search" class="input flex-1" placeholder="Cari menu..." />
        <select v-model="filterDiv" class="input w-auto">
          <option value="">Semua</option>
          <option value="Bar">Bar</option>
          <option value="Kitchen">Kitchen</option>
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
            <span class="text-xl">{{ item.division === 'Kitchen' ? '🍳' : '☕' }}</span>
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
            <p class="text-xs text-gray-400">{{ formatRp(item.price) }} × {{ item.qty }}</p>
          </div>
          <div class="flex items-center gap-1">
            <button @click="decQty(item)" class="w-6 h-6 rounded-lg bg-gray-100 text-gray-600 flex items-center justify-center text-sm hover:bg-red-50 hover:text-red-600">−</button>
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
            <input v-model="order.customerName" class="input" placeholder="Opsional" />
          </div>
          <div>
            <label class="label">No Meja</label>
            <input v-model="order.tableNumber" class="input" placeholder="A1" />
          </div>
        </div>

        <div>
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

        <button
          @click="checkout"
          :disabled="!cart.length || loading"
          class="btn-primary w-full justify-center py-3 text-base"
        >
          <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          Bayar {{ cart.length ? formatRp(subtotal - order.discount) : '' }}
        </button>
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
const cart = ref([])
const search = ref('')
const filterDiv = ref('')
const loading = ref(false)

const order = reactive({ customerName: '', tableNumber: '', paymentMethod: 'CASH', discount: 0 })

const filteredMenu = computed(() =>
  menu.value.filter(m =>
    (!search.value || m.name.toLowerCase().includes(search.value.toLowerCase())) &&
    (!filterDiv.value || m.division === filterDiv.value)
  )
)

const subtotal = computed(() => cart.value.reduce((s, i) => s + i.price * i.qty, 0))

const formatRp = (n) =>
  new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(n)

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
    })
    toast.success('Transaksi berhasil!')
    // Auto-print receipt
    if (res.data?.id) {
      try { await printReceipt(res.data.id) } catch {}
    }
    cart.value = []
    order.customerName = ''
    order.tableNumber = ''
    order.discount = 0
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal proses transaksi')
  } finally {
    loading.value = false
  }
}

async function printReceipt(saleId) {
  const res = await api.get(`/api/v1/pos/sales/${saleId}/receipt`)
  const r = res.data
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

onMounted(async () => {
  const res = await api.get('/api/v1/pos/menu?available_only=true')
  menu.value = res.data
})
</script>
