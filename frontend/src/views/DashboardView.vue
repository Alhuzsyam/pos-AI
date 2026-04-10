<template>
  <div class="p-6 max-w-7xl mx-auto">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p class="text-sm text-gray-400">{{ today }}</p>
      </div>
      <button @click="loadData" class="btn-secondary btn-sm">
        <svg class="w-4 h-4" :class="loading && 'animate-spin'" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        Refresh
      </button>
    </div>

    <!-- KPI Cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div class="stat-card">
        <div class="flex items-center justify-between">
          <span class="stat-label">Revenue Hari Ini</span>
          <div class="stat-icon bg-green-50">
            <svg class="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>
        <p class="stat-value">{{ formatRp(data?.today?.revenue || 0) }}</p>
        <p class="text-xs text-gray-400 mt-1">{{ data?.today?.transaction_count || 0 }} transaksi</p>
      </div>

      <div class="stat-card">
        <div class="flex items-center justify-between">
          <span class="stat-label">Revenue Bulan Ini</span>
          <div class="stat-icon bg-blue-50">
            <svg class="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
        </div>
        <p class="stat-value">{{ formatRp(data?.month?.revenue || 0) }}</p>
        <p class="text-xs text-gray-400 mt-1">Estimasi profit: {{ formatRp(data?.month?.profit_estimate || 0) }}</p>
      </div>

      <div class="stat-card">
        <div class="flex items-center justify-between">
          <span class="stat-label">Avg Transaksi</span>
          <div class="stat-icon bg-purple-50">
            <svg class="w-5 h-5 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
        </div>
        <p class="stat-value">{{ formatRp(data?.today?.avg_transaction || 0) }}</p>
        <p class="text-xs text-gray-400 mt-1">Per transaksi hari ini</p>
      </div>

      <div class="stat-card" :class="data?.alerts?.low_stock_count > 0 && 'ring-2 ring-red-200'">
        <div class="flex items-center justify-between">
          <span class="stat-label">Stok Rendah</span>
          <div class="stat-icon" :class="data?.alerts?.low_stock_count > 0 ? 'bg-red-50' : 'bg-gray-50'">
            <svg class="w-5 h-5" :class="data?.alerts?.low_stock_count > 0 ? 'text-red-600' : 'text-gray-400'" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
        </div>
        <p class="stat-value" :class="data?.alerts?.low_stock_count > 0 ? 'text-red-600' : ''">
          {{ data?.alerts?.low_stock_count || 0 }}
        </p>
        <p class="text-xs text-gray-400 mt-1">Produk perlu restock</p>
      </div>
    </div>

    <!-- Charts + Top Menu -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <!-- Revenue Chart -->
      <div class="card p-5 lg:col-span-2">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-semibold text-gray-900">Revenue 30 Hari</h3>
        </div>
        <div class="h-48">
          <LineChart v-if="chartData.labels.length" :data="chartData" :options="chartOptions" />
          <div v-else class="h-full flex items-center justify-center text-gray-300 text-sm">Belum ada data</div>
        </div>
      </div>

      <!-- Top Menu -->
      <div class="card p-5">
        <h3 class="font-semibold text-gray-900 mb-4">Top Menu Hari Ini</h3>
        <div v-if="data?.top_menu_today?.length" class="space-y-3">
          <div v-for="(item, i) in data.top_menu_today" :key="item.name" class="flex items-center gap-3">
            <span class="text-xs font-bold text-gray-300 w-5">{{ i + 1 }}</span>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-gray-800 truncate">{{ item.name }}</p>
              <p class="text-xs text-gray-400">{{ item.qty }}x · {{ formatRp(item.revenue) }}</p>
            </div>
          </div>
        </div>
        <div v-else class="text-center text-gray-300 text-sm py-8">Belum ada transaksi hari ini</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { Line as LineChart } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler } from 'chart.js'
import api from '@/composables/useApi'
import dayjs from 'dayjs'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler)

const loading = ref(false)
const data = ref(null)
const revenueHistory = ref([])

const today = computed(() => dayjs().format('dddd, D MMMM YYYY'))

const formatRp = (n) =>
  new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(n)

const chartData = computed(() => ({
  labels: revenueHistory.value.map(r => dayjs(r.date).format('D/M')),
  datasets: [{
    label: 'Revenue',
    data: revenueHistory.value.map(r => r.revenue),
    borderColor: '#15803d',
    backgroundColor: 'rgba(21,128,61,0.08)',
    tension: 0.4,
    fill: true,
    pointRadius: 3,
  }]
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    x: { grid: { display: false }, ticks: { font: { size: 11 } } },
    y: { grid: { color: '#f1f5f9' }, ticks: { font: { size: 11 }, callback: v => `${(v/1000).toFixed(0)}k` } },
  }
}

async function loadData() {
  loading.value = true
  try {
    const [dashRes, histRes] = await Promise.all([
      api.get('/api/v1/reports/dashboard'),
      api.get('/api/v1/reports/revenue/daily?days=30'),
    ])
    data.value = dashRes.data
    revenueHistory.value = histRes.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>
