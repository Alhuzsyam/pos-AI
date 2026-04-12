<template>
  <div class="p-6 max-w-6xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Riwayat Transaksi</h1>
    </div>

    <!-- Filters -->
    <div class="flex gap-2 mb-4 flex-wrap">
      <input v-model="filters.dateFrom" type="date" class="input w-auto" />
      <input v-model="filters.dateTo" type="date" class="input w-auto" />
      <button @click="loadSales" class="btn-primary btn-sm">Filter</button>
      <button @click="resetFilter" class="btn-secondary btn-sm">Reset</button>
    </div>

    <!-- Summary -->
    <div class="grid grid-cols-3 gap-4 mb-4">
      <div class="stat-card">
        <span class="stat-label">Total Transaksi</span>
        <p class="stat-value">{{ sales.length }}</p>
      </div>
      <div class="stat-card">
        <span class="stat-label">Total Revenue</span>
        <p class="stat-value">{{ formatRp(totalRevenue) }}</p>
      </div>
      <div class="stat-card">
        <span class="stat-label">Rata-rata</span>
        <p class="stat-value">{{ formatRp(avgTransaction) }}</p>
      </div>
    </div>

    <!-- Table -->
    <div class="card overflow-hidden">
      <table class="table-base">
        <thead>
          <tr>
            <th>Kode</th>
            <th>Waktu</th>
            <th>Pelanggan</th>
            <th>Meja</th>
            <th>Pembayaran</th>
            <th>Total</th>
            <th>Aksi</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="sale in sales" :key="sale.id">
            <td class="font-mono text-xs text-brand-700">{{ sale.transaction_code }}</td>
            <td class="text-xs text-gray-500">{{ formatDate(sale.transaction_date) }}</td>
            <td>{{ sale.customer_name || '-' }}</td>
            <td>{{ sale.table_number || '-' }}</td>
            <td>
              <button @click="openEditPayment(sale)" class="badge-gray cursor-pointer hover:bg-brand-50 transition-colors" title="Klik untuk edit metode bayar">
                {{ sale.payment_method }}
              </button>
            </td>
            <td class="font-semibold text-gray-900">{{ formatRp(sale.final_amount) }}</td>
            <td>
              <div class="flex gap-1">
                <button @click="selectedSale = sale" class="btn-secondary btn-xs">Detail</button>
                <button @click="printReceipt(sale.id)" class="btn-primary btn-xs">Struk</button>
              </div>
            </td>
          </tr>
          <tr v-if="!sales.length">
            <td colspan="7" class="text-center text-gray-300 py-8">Belum ada transaksi</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Detail Modal -->
    <div v-if="selectedSale" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div class="card p-6 w-full max-w-md">
        <div class="flex items-center justify-between mb-4">
          <h2 class="font-bold text-gray-900">Detail Transaksi</h2>
          <button @click="selectedSale = null" class="text-gray-400 hover:text-gray-600">✕</button>
        </div>
        <div class="space-y-2 text-sm mb-4">
          <div class="flex justify-between"><span class="text-gray-400">Kode</span><span class="font-mono text-brand-700">{{ selectedSale.transaction_code }}</span></div>
          <div class="flex justify-between"><span class="text-gray-400">Waktu</span><span>{{ formatDate(selectedSale.transaction_date) }}</span></div>
          <div class="flex justify-between"><span class="text-gray-400">Pelanggan</span><span>{{ selectedSale.customer_name || '-' }}</span></div>
          <div class="flex justify-between"><span class="text-gray-400">Meja</span><span>{{ selectedSale.table_number || '-' }}</span></div>
          <div class="flex justify-between"><span class="text-gray-400">Pembayaran</span><span>{{ selectedSale.payment_method }}</span></div>
        </div>
        <table class="table-base mb-4">
          <thead><tr><th>Menu</th><th>Qty</th><th>Subtotal</th></tr></thead>
          <tbody>
            <tr v-for="item in selectedSale.items" :key="item.id">
              <td>{{ item.menu_name }}</td>
              <td>{{ item.quantity }}</td>
              <td>{{ formatRp(item.subtotal) }}</td>
            </tr>
          </tbody>
        </table>
        <div class="border-t pt-3 space-y-1 text-sm">
          <div class="flex justify-between text-gray-400"><span>Subtotal</span><span>{{ formatRp(selectedSale.total_amount) }}</span></div>
          <div class="flex justify-between text-gray-400"><span>Diskon</span><span>-{{ formatRp(selectedSale.discount_amount) }}</span></div>
          <div class="flex justify-between font-bold text-gray-900"><span>Total</span><span class="text-brand-700">{{ formatRp(selectedSale.final_amount) }}</span></div>
        </div>
        <div class="flex gap-2 mt-4">
          <button @click="printReceipt(selectedSale.id)" class="btn-primary flex-1">Cetak Struk</button>
          <button @click="selectedSale = null" class="btn-secondary flex-1">Tutup</button>
        </div>
      </div>
    </div>

    <!-- Edit Payment Modal -->
    <div v-if="editPaymentSale" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div class="card p-6 w-full max-w-sm">
        <h2 class="font-bold text-gray-900 mb-4">Edit Metode Pembayaran</h2>
        <p class="text-sm text-gray-500 mb-3">{{ editPaymentSale.transaction_code }}</p>
        <div class="grid grid-cols-2 gap-2 mb-4">
          <button v-for="method in paymentMethods" :key="method"
            @click="newPaymentMethod = method"
            :class="['py-3 rounded-lg text-[13px] font-medium border transition-colors',
              newPaymentMethod === method ? 'bg-brand-500 text-white border-brand-500' : 'bg-white text-claude-slate border-claude-line hover:bg-brand-50']">
            {{ method }}
          </button>
        </div>
        <div class="flex gap-2">
          <button @click="savePaymentMethod" class="btn-primary flex-1" :disabled="newPaymentMethod === editPaymentSale.payment_method">Simpan</button>
          <button @click="editPaymentSale = null" class="btn-secondary flex-1">Batal</button>
        </div>
      </div>
    </div>

    <!-- Hidden Receipt for Printing -->
    <div id="receipt-print" class="hidden"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import api from '@/composables/useApi'
import { useToast } from 'vue-toastification'
import dayjs from 'dayjs'

const toast = useToast()
const sales = ref([])
const selectedSale = ref(null)
const editPaymentSale = ref(null)
const newPaymentMethod = ref('CASH')
const filters = reactive({ dateFrom: '', dateTo: '' })
const paymentMethods = ['CASH', 'QRIS', 'TRANSFER', 'DEBIT', 'CREDIT']

const totalRevenue = computed(() => sales.value.reduce((s, t) => s + (t.final_amount || 0), 0))
const avgTransaction = computed(() => sales.value.length ? totalRevenue.value / sales.value.length : 0)

const formatRp = (n) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(n)
const formatDate = (d) => dayjs(d).format('D MMM YYYY HH:mm')

async function loadSales() {
  let url = '/api/v1/pos/sales?limit=100'
  if (filters.dateFrom) url += `&date_from=${filters.dateFrom}`
  if (filters.dateTo) url += `&date_to=${filters.dateTo}`
  const res = await api.get(url)
  sales.value = res.data
}

function resetFilter() {
  filters.dateFrom = ''
  filters.dateTo = ''
  loadSales()
}

function openEditPayment(sale) {
  editPaymentSale.value = sale
  newPaymentMethod.value = sale.payment_method
}

async function savePaymentMethod() {
  try {
    await api.patch(`/api/v1/pos/sales/${editPaymentSale.value.id}/payment`, {
      payment_method: newPaymentMethod.value,
    })
    toast.success(`Metode bayar diubah ke ${newPaymentMethod.value}`)
    editPaymentSale.value.payment_method = newPaymentMethod.value
    editPaymentSale.value = null
    loadSales()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal update')
  }
}

async function printReceipt(saleId) {
  try {
    const res = await api.get(`/api/v1/pos/sales/${saleId}/receipt`)
    const r = res.data
    const itemsHtml = r.items.map(i =>
      `<tr>
        <td style="text-align:left">${i.qty}x ${i.name}${i.note ? '<br><small style="color:#888">' + i.note + '</small>' : ''}</td>
        <td style="text-align:right">${formatRp(i.subtotal)}</td>
      </tr>`
    ).join('')

    const html = `
      <div style="font-family:'Courier New',monospace;width:280px;padding:10px;font-size:12px;color:#000">
        <div style="text-align:center;margin-bottom:8px">
          <div style="font-size:16px;font-weight:bold">${r.store_name}</div>
          ${r.store_address ? '<div style="font-size:10px">' + r.store_address + '</div>' : ''}
          ${r.store_phone ? '<div style="font-size:10px">' + r.store_phone + '</div>' : ''}
        </div>
        <div style="border-top:1px dashed #000;margin:6px 0"></div>
        <div style="font-size:11px">
          <div>${r.transaction_code}</div>
          <div>${r.date}</div>
          <div>Kasir: ${r.cashier}</div>
          ${r.customer_name ? '<div>Customer: ' + r.customer_name + '</div>' : ''}
          ${r.table_number ? '<div>Meja: ' + r.table_number + '</div>' : ''}
        </div>
        <div style="border-top:1px dashed #000;margin:6px 0"></div>
        <table style="width:100%;font-size:11px;border-collapse:collapse">
          ${itemsHtml}
        </table>
        <div style="border-top:1px dashed #000;margin:6px 0"></div>
        <table style="width:100%;font-size:11px">
          <tr><td>Subtotal</td><td style="text-align:right">${formatRp(r.total_amount)}</td></tr>
          ${r.discount_amount ? '<tr><td>Diskon</td><td style="text-align:right">-' + formatRp(r.discount_amount) + '</td></tr>' : ''}
          ${r.tax_amount ? '<tr><td>Pajak</td><td style="text-align:right">' + formatRp(r.tax_amount) + '</td></tr>' : ''}
          <tr style="font-weight:bold;font-size:13px"><td>TOTAL</td><td style="text-align:right">${formatRp(r.final_amount)}</td></tr>
        </table>
        <div style="border-top:1px dashed #000;margin:6px 0"></div>
        <div style="text-align:center;font-size:10px">
          <div>Bayar: ${r.payment_method}</div>
          <div style="margin-top:6px">Terima kasih!</div>
          <div>Powered by POS-AI</div>
        </div>
      </div>
    `

    const printWindow = window.open('', '_blank', 'width=320,height=600')
    printWindow.document.write(`
      <html><head><title>Struk ${r.transaction_code}</title>
      <style>@media print{body{margin:0}@page{size:80mm auto;margin:0}}</style>
      </head><body>${html}</body></html>
    `)
    printWindow.document.close()
    printWindow.focus()
    setTimeout(() => { printWindow.print() }, 300)
  } catch (e) {
    toast.error('Gagal load struk')
  }
}

onMounted(loadSales)
</script>
