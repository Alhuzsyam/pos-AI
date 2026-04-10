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
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="sale in sales" :key="sale.id" @click="selectedSale = sale" class="cursor-pointer">
            <td class="font-mono text-xs text-brand-700">{{ sale.transaction_code }}</td>
            <td class="text-xs text-gray-500">{{ formatDate(sale.transaction_date) }}</td>
            <td>{{ sale.customer_name || '-' }}</td>
            <td>{{ sale.table_number || '-' }}</td>
            <td><span class="badge-gray">{{ sale.payment_method }}</span></td>
            <td class="font-semibold text-gray-900">{{ formatRp(sale.final_amount) }}</td>
            <td><span class="badge-green">{{ sale.status }}</span></td>
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
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import api from '@/composables/useApi'
import dayjs from 'dayjs'

const sales = ref([])
const selectedSale = ref(null)
const filters = reactive({ dateFrom: '', dateTo: '' })

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

onMounted(loadSales)
</script>
