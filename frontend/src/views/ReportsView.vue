<template>
  <div class="p-6 max-w-6xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Laporan & Analitik</h1>
      <div class="flex gap-2 items-end">
        <div>
          <label class="label text-[11px]">Dari</label>
          <input v-model="exportFrom" type="date" class="input w-auto text-xs" />
        </div>
        <div>
          <label class="label text-[11px]">Sampai</label>
          <input v-model="exportTo" type="date" class="input w-auto text-xs" />
        </div>
        <button @click="downloadExcel" class="btn-primary btn-sm flex items-center gap-1" :disabled="exporting">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
          {{ exporting ? 'Downloading...' : 'Export Excel' }}
        </button>
      </div>
    </div>

    <!-- ── Laporan Closing ─────────────────────────────────────────────── -->
    <div class="card p-5 mb-6">
      <div class="flex items-center justify-between mb-4 flex-wrap gap-3">
        <div>
          <h2 class="font-semibold text-gray-900">Laporan Closing</h2>
          <p class="text-xs text-gray-400 mt-0.5">Rekap transaksi & metode pembayaran per periode</p>
        </div>
        <!-- Quick filter buttons -->
        <div class="flex gap-2 flex-wrap">
          <button v-for="f in quickFilters" :key="f.label"
            @click="applyQuickFilter(f)"
            :class="['btn-sm', closingMode === f.label ? 'btn-primary' : 'btn-secondary']">
            {{ f.label }}
          </button>
          <button @click="closingMode = 'Custom'" :class="['btn-sm', closingMode === 'Custom' ? 'btn-primary' : 'btn-secondary']">Custom</button>
        </div>
      </div>

      <!-- Custom date range (shown only when Custom selected) -->
      <div v-if="closingMode === 'Custom'" class="flex gap-2 mb-4 flex-wrap">
        <div>
          <label class="label text-[11px]">Dari</label>
          <input v-model="closingFrom" type="date" class="input w-auto text-xs" @change="loadClosing" />
        </div>
        <div>
          <label class="label text-[11px]">Sampai</label>
          <input v-model="closingTo" type="date" class="input w-auto text-xs" @change="loadClosing" />
        </div>
        <div class="flex items-end">
          <button @click="loadClosing" class="btn-primary btn-sm">Tampilkan</button>
        </div>
      </div>

      <!-- Period label -->
      <p v-if="closing" class="text-xs text-gray-400 mb-3">
        Periode: <span class="font-medium text-gray-700">{{ closing.date_from }}</span>
        <span v-if="closing.date_from !== closing.date_to"> s/d <span class="font-medium text-gray-700">{{ closing.date_to }}</span></span>
      </p>

      <!-- Summary cards -->
      <div v-if="closing" class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <div class="bg-green-50 rounded-xl p-3 text-center">
          <p class="text-xs text-gray-400">Total Omzet</p>
          <p class="text-lg font-bold text-green-700">{{ formatRp(closing.grand_total) }}</p>
          <p class="text-xs text-gray-400">{{ closing.grand_count }} transaksi</p>
        </div>
        <div class="bg-red-50 rounded-xl p-3 text-center">
          <p class="text-xs text-gray-400">Pengeluaran</p>
          <p class="text-lg font-bold text-red-600">{{ formatRp(closing.total_expenses) }}</p>
        </div>
        <div class="bg-blue-50 rounded-xl p-3 text-center col-span-2">
          <p class="text-xs text-gray-400">Estimasi Profit</p>
          <p class="text-lg font-bold" :class="closing.net_profit >= 0 ? 'text-blue-700' : 'text-red-600'">
            {{ formatRp(closing.net_profit) }}
          </p>
        </div>
      </div>

      <!-- Breakdown per metode bayar -->
      <div v-if="closing?.breakdown?.length" class="overflow-x-auto">
        <table class="table-base">
          <thead>
            <tr>
              <th>Metode Bayar</th>
              <th class="text-center">Transaksi</th>
              <th class="text-right">Total</th>
              <th class="text-right">%</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="b in closing.breakdown" :key="b.method">
              <td>
                <span :class="methodBadge(b.method)" class="text-xs font-semibold px-2 py-0.5 rounded-full">{{ b.method }}</span>
              </td>
              <td class="text-center text-gray-600">{{ b.count }}x</td>
              <td class="text-right font-semibold text-gray-800">{{ formatRp(b.total) }}</td>
              <td class="text-right text-gray-400 text-xs">
                {{ closing.grand_total > 0 ? ((b.total / closing.grand_total) * 100).toFixed(1) : '0' }}%
              </td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="border-t-2 border-gray-200">
              <td class="font-bold text-gray-900">Total</td>
              <td class="text-center font-bold text-gray-900">{{ closing.grand_count }}x</td>
              <td class="text-right font-bold text-green-700">{{ formatRp(closing.grand_total) }}</td>
              <td class="text-right text-gray-400 text-xs">100%</td>
            </tr>
          </tfoot>
        </table>
      </div>
      <div v-else-if="closing" class="text-center text-gray-300 py-8">Tidak ada transaksi pada periode ini</div>
      <div v-else class="text-center text-gray-300 py-8">Memuat data...</div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Revenue Chart -->
      <div class="card p-5">
        <div class="flex items-center justify-between mb-4">
          <h2 class="font-semibold text-gray-900">Revenue Harian</h2>
          <select v-model="revDays" @change="loadRevenue" class="input w-auto text-xs">
            <option :value="7">7 Hari</option>
            <option :value="30">30 Hari</option>
            <option :value="90">90 Hari</option>
          </select>
        </div>
        <div class="h-56">
          <Bar v-if="barData.labels.length" :data="barData" :options="barOptions" />
        </div>
      </div>

      <!-- Payment Method (overall) -->
      <div class="card p-5">
        <h2 class="font-semibold text-gray-900 mb-4">Metode Pembayaran (30 Hari)</h2>
        <div class="h-56">
          <Doughnut v-if="doughnutData.labels.length" :data="doughnutData" :options="donutOptions" />
        </div>
      </div>

      <!-- Menu Performance -->
      <div class="card p-5 lg:col-span-2">
        <div class="flex items-center justify-between mb-4">
          <h2 class="font-semibold text-gray-900">Performa Menu</h2>
          <select v-model="menuDays" @change="loadMenuPerf" class="input w-auto text-xs">
            <option :value="7">7 Hari</option>
            <option :value="30">30 Hari</option>
            <option :value="90">90 Hari</option>
          </select>
        </div>
        <div class="overflow-x-auto">
          <table class="table-base">
            <thead><tr><th>#</th><th>Menu</th><th>Qty Terjual</th><th>Revenue</th></tr></thead>
            <tbody>
              <tr v-for="(item, i) in menuPerf" :key="item.name">
                <td class="text-gray-300 font-bold">{{ i + 1 }}</td>
                <td class="font-medium text-gray-800">{{ item.name }}</td>
                <td>{{ item.qty_sold }}</td>
                <td class="font-semibold text-brand-700">{{ formatRp(item.revenue) }}</td>
              </tr>
              <tr v-if="!menuPerf.length"><td colspan="4" class="text-center text-gray-300 py-8">Belum ada data</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Inventory Summary -->
      <div class="card p-5 lg:col-span-2">
        <h2 class="font-semibold text-gray-900 mb-4">Ringkasan Inventori</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div class="text-center">
            <p class="text-3xl font-bold text-gray-900">{{ invSummary.total_products || 0 }}</p>
            <p class="text-xs text-gray-400">Total Produk</p>
          </div>
          <div class="text-center">
            <p class="text-3xl font-bold text-brand-700">{{ formatRp(invSummary.total_stock_value || 0) }}</p>
            <p class="text-xs text-gray-400">Nilai Stok</p>
          </div>
          <div class="text-center">
            <p class="text-3xl font-bold text-yellow-600">{{ invSummary.low_stock_count || 0 }}</p>
            <p class="text-xs text-gray-400">Stok Rendah</p>
          </div>
          <div class="text-center">
            <p class="text-3xl font-bold text-red-600">{{ invSummary.out_of_stock_count || 0 }}</p>
            <p class="text-xs text-gray-400">Habis</p>
          </div>
        </div>
        <div v-if="invSummary.low_stock_items?.length" class="overflow-x-auto">
          <p class="text-xs font-bold text-red-500 uppercase mb-2">Perlu Restock</p>
          <table class="table-base">
            <thead><tr><th>Produk</th><th>Stok Saat Ini</th><th>Min Stok</th></tr></thead>
            <tbody>
              <tr v-for="p in invSummary.low_stock_items" :key="p.id">
                <td class="font-medium">{{ p.name }}</td>
                <td class="text-red-600 font-bold">{{ p.current_stock }}</td>
                <td class="text-gray-400">{{ p.min_stock }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Bar, Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend } from 'chart.js'
import api from '@/composables/useApi'
import dayjs from 'dayjs'

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend)

const revenueData = ref([])
const paymentData = ref([])
const menuPerf = ref([])
const invSummary = ref({})
const revDays = ref(30)
const menuDays = ref(30)
const exportFrom = ref('')
const exportTo = ref('')
const exporting = ref(false)

// Closing report state
const closing = ref(null)
const closingMode = ref('Hari Ini')
const closingFrom = ref(dayjs().format('YYYY-MM-DD'))
const closingTo = ref(dayjs().format('YYYY-MM-DD'))

const quickFilters = [
  { label: 'Hari Ini', from: () => dayjs().format('YYYY-MM-DD'), to: () => dayjs().format('YYYY-MM-DD') },
  { label: 'Kemarin', from: () => dayjs().subtract(1, 'day').format('YYYY-MM-DD'), to: () => dayjs().subtract(1, 'day').format('YYYY-MM-DD') },
  { label: 'Bulan Ini', from: () => dayjs().startOf('month').format('YYYY-MM-DD'), to: () => dayjs().format('YYYY-MM-DD') },
  { label: 'Bulan Lalu', from: () => dayjs().subtract(1, 'month').startOf('month').format('YYYY-MM-DD'), to: () => dayjs().subtract(1, 'month').endOf('month').format('YYYY-MM-DD') },
]

function applyQuickFilter(f) {
  closingMode.value = f.label
  closingFrom.value = f.from()
  closingTo.value = f.to()
  loadClosing()
}

async function loadClosing() {
  try {
    const res = await api.get(`/api/v1/reports/closing?date_from=${closingFrom.value}&date_to=${closingTo.value}`)
    closing.value = res.data
  } catch {}
}

const formatRp = (n) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(n || 0)

const COLORS = ['#15803d','#2563eb','#d97706','#dc2626','#7c3aed','#0891b2']

function methodBadge(method) {
  return {
    CASH: 'bg-green-100 text-green-700',
    QRIS: 'bg-blue-100 text-blue-700',
    TRANSFER: 'bg-purple-100 text-purple-700',
    DEBIT: 'bg-orange-100 text-orange-700',
    CREDIT: 'bg-red-100 text-red-700',
    DEBT: 'bg-gray-100 text-gray-600',
  }[method] || 'bg-gray-100 text-gray-600'
}

const barData = computed(() => ({
  labels: revenueData.value.map(r => dayjs(r.date).format('D/M')),
  datasets: [{ label: 'Revenue', data: revenueData.value.map(r => r.revenue), backgroundColor: '#15803d33', borderColor: '#15803d', borderWidth: 2, borderRadius: 6 }]
}))

const barOptions = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: { x: { grid: { display: false } }, y: { grid: { color: '#f1f5f9' }, ticks: { callback: v => `${(v/1000).toFixed(0)}k` } } }
}

const doughnutData = computed(() => ({
  labels: paymentData.value.map(r => r.method),
  datasets: [{ data: paymentData.value.map(r => r.total), backgroundColor: COLORS }]
}))

const donutOptions = { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right' } } }

async function downloadExcel() {
  exporting.value = true
  try {
    let url = '/api/v1/reports/export-excel'
    const params = []
    if (exportFrom.value) params.push(`date_from=${exportFrom.value}`)
    if (exportTo.value) params.push(`date_to=${exportTo.value}`)
    if (params.length) url += '?' + params.join('&')

    const res = await api.get(url, { responseType: 'blob' })
    const blob = new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    const disposition = res.headers['content-disposition'] || ''
    const match = disposition.match(/filename="?(.+?)"?$/)
    link.download = match ? match[1] : 'laporan.xlsx'
    link.click()
    URL.revokeObjectURL(link.href)
  } catch (e) {
    alert('Gagal download laporan')
  } finally {
    exporting.value = false
  }
}

async function loadRevenue() {
  const res = await api.get(`/api/v1/reports/revenue/daily?days=${revDays.value}`)
  revenueData.value = res.data
}

async function loadMenuPerf() {
  const res = await api.get(`/api/v1/reports/menu/performance?days=${menuDays.value}`)
  menuPerf.value = res.data
}

onMounted(async () => {
  const today = dayjs().format('YYYY-MM-DD')
  closingFrom.value = today
  closingTo.value = today

  const [_, payRes, invRes] = await Promise.all([
    loadRevenue(),
    api.get('/api/v1/reports/revenue/by-payment-method'),
    api.get('/api/v1/reports/inventory/summary'),
  ])
  paymentData.value = payRes.data
  invSummary.value = invRes.data
  loadMenuPerf()
  loadClosing()
})
</script>
