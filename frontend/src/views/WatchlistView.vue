<template>
  <div class="p-6 max-w-7xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="page-title">Watchlist / KDS</h1>
        <p class="page-subtitle">Kitchen Display System - Monitor pesanan</p>
      </div>
      <div class="flex gap-2 flex-wrap">
        <button v-for="d in divisions" :key="d"
          @click="activeTab = d.toLowerCase()" :class="tabClass(d.toLowerCase())" class="relative">
          {{ d }}
          <span v-if="counts[d.toLowerCase()]" class="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white rounded-full text-[10px] flex items-center justify-center">{{ counts[d.toLowerCase()] }}</span>
        </button>
        <button @click="activeTab = 'waiter'" :class="tabClass('waiter')" class="relative">
          Waiter
          <span v-if="counts.waiter" class="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white rounded-full text-[10px] flex items-center justify-center">{{ counts.waiter }}</span>
        </button>
      </div>
    </div>

    <!-- Orders Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="order in filteredOrders" :key="order.sale_id" class="card p-4">
        <!-- Order Header -->
        <div class="flex items-center justify-between mb-3 pb-2 border-b border-claude-line">
          <div>
            <span class="font-serif text-[15px] text-claude-ink font-semibold">{{ order.transaction_code }}</span>
            <span v-if="order.table_number" class="ml-2 text-[12px] bg-brand-50 text-brand-600 px-2 py-0.5 rounded">Meja {{ order.table_number }}</span>
          </div>
          <span class="text-[11px] text-claude-dust">{{ formatTime(order.created_at) }}</span>
        </div>
        <p v-if="order.customer_name" class="text-[12px] text-claude-slate mb-2">{{ order.customer_name }}</p>

        <!-- Items -->
        <div class="space-y-2">
          <div v-for="item in order.items" :key="item.id"
            :class="['flex items-center justify-between p-2 rounded-lg text-[13px]',
              item.status === 'PENDING' ? 'bg-amber-50 border border-amber-200' :
              item.status === 'PREPARED' ? 'bg-blue-50 border border-blue-200' :
              item.status === 'DELIVERED' ? 'bg-green-50 border border-green-200' :
              'bg-gray-50 border border-gray-200']">
            <div>
              <span class="font-medium">{{ item.quantity }}x</span> {{ item.menu_name }}
              <span v-if="item.note" class="block text-[11px] text-claude-dust italic">{{ item.note }}</span>
            </div>
            <div class="flex items-center gap-2">
              <span :class="statusBadge(item.status)" class="text-[10px] px-2 py-0.5 rounded-full font-medium">{{ item.status }}</span>
              <!-- Action buttons based on station -->
              <button v-if="activeTab !== 'waiter' && item.status === 'PENDING'"
                @click="markPrepared(item.id)" class="btn-primary btn-xs">Selesai</button>
              <button v-if="activeTab === 'waiter' && item.status === 'PREPARED'"
                @click="markDelivered(item.id)" class="btn-primary btn-xs">Antar</button>
            </div>
          </div>
        </div>

        <!-- Batch action -->
        <div class="mt-3 pt-2 border-t border-claude-line">
          <button v-if="activeTab !== 'waiter' && order.items.some(i => i.status === 'PENDING')"
            @click="prepareAll(order.sale_id)" class="btn-secondary btn-sm w-full">Selesai Semua</button>
          <button v-if="activeTab === 'waiter' && order.items.some(i => i.status === 'PREPARED')"
            @click="deliverAll(order.sale_id)" class="btn-secondary btn-sm w-full">Antar Semua</button>
        </div>
      </div>
    </div>

    <div v-if="!filteredOrders.length" class="text-center text-claude-dust py-20 font-serif text-[16px]">
      Tidak ada pesanan {{ activeTab === 'waiter' ? 'siap antar' : 'menunggu' }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import api from '@/composables/useApi'
import { useToast } from 'vue-toastification'

const toast = useToast()
const divisions = ref(['Bar', 'Kitchen'])
const activeTab = ref('bar')
const orders = ref([])
const counts = ref({})
let pollInterval = null
let prevCounts = {}

// Notification sound
let audioCtx = null
function playTing() {
  try {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)()
    const osc = audioCtx.createOscillator()
    const gain = audioCtx.createGain()
    osc.connect(gain)
    gain.connect(audioCtx.destination)
    osc.frequency.value = 880
    osc.type = 'sine'
    gain.gain.setValueAtTime(0.3, audioCtx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.5)
    osc.start(audioCtx.currentTime)
    osc.stop(audioCtx.currentTime + 0.5)
  } catch {}
}

const filteredOrders = computed(() => {
  if (activeTab.value === 'waiter') {
    return orders.value.filter(o => o.items.some(i => i.status === 'PREPARED'))
      .map(o => ({ ...o, items: o.items.filter(i => i.status === 'PREPARED') }))
  }
  // Division tab — match by name (case-insensitive)
  const div = divisions.value.find(d => d.toLowerCase() === activeTab.value) || activeTab.value
  return orders.value.filter(o => o.items.some(i => i.division === div && i.status === 'PENDING'))
    .map(o => ({ ...o, items: o.items.filter(i => i.division === div && i.status === 'PENDING') }))
})

async function loadQueue() {
  try {
    const [qRes, cRes] = await Promise.all([
      api.get('/api/v1/queue/'),
      api.get('/api/v1/queue/counts'),
    ])
    orders.value = qRes.data
    const newCounts = cRes.data

    // Play ting if new items appeared in current station
    const stationKey = activeTab.value
    if ((newCounts[stationKey] || 0) > (prevCounts[stationKey] || 0)) {
      playTing()
    }
    prevCounts = { ...newCounts }
    counts.value = newCounts
  } catch {}
}

async function markPrepared(itemId) {
  try {
    await api.put(`/api/v1/queue/${itemId}/prepare`)
    toast.success('Item siap diantar!')
    loadQueue()
  } catch (e) { toast.error(e.response?.data?.detail || 'Gagal update') }
}

async function markDelivered(itemId) {
  try {
    await api.put(`/api/v1/queue/${itemId}/deliver`)
    toast.success('Item sudah diantar!')
    loadQueue()
  } catch (e) { toast.error(e.response?.data?.detail || 'Gagal update') }
}

async function prepareAll(saleId) {
  const div = divisions.value.find(d => d.toLowerCase() === activeTab.value) || activeTab.value
  try {
    await api.put(`/api/v1/queue/order/${saleId}/prepare-all?division=${div}`)
    toast.success('Semua item selesai!')
    loadQueue()
  } catch (e) { toast.error(e.response?.data?.detail || 'Gagal update') }
}

async function deliverAll(saleId) {
  try {
    await api.put(`/api/v1/queue/order/${saleId}/deliver-all`)
    toast.success('Semua item diantar!')
    loadQueue()
  } catch (e) { toast.error(e.response?.data?.detail || 'Gagal update') }
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
}

function tabClass(tab) {
  return [
    'px-4 py-2 rounded-lg text-[13px] font-medium transition-colors',
    activeTab.value === tab
      ? 'bg-brand-500 text-white shadow-sm'
      : 'bg-white text-claude-slate border border-claude-line hover:bg-brand-50'
  ].join(' ')
}

function statusBadge(status) {
  return {
    'PENDING': 'bg-amber-100 text-amber-700',
    'PREPARED': 'bg-blue-100 text-blue-700',
    'DELIVERED': 'bg-green-100 text-green-700',
    'SERVED': 'bg-gray-100 text-gray-500',
  }[status] || 'bg-gray-100 text-gray-500'
}

async function loadDivisions() {
  try {
    const res = await api.get('/api/v1/settings/')
    const divs = res.data.divisions || ['Bar', 'Kitchen', 'Titipan']
    // Filter out non-watchlist divisions if needed, keep all for now
    divisions.value = divs
    activeTab.value = divs[0]?.toLowerCase() || 'bar'
  } catch {}
}

onMounted(async () => {
  await loadDivisions()
  await loadQueue()
  pollInterval = setInterval(loadQueue, 5000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>
