<template>
  <div class="p-6 max-w-5xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Reservasi Meja</h1>
      <button @click="showModal = true" class="btn-primary">+ Buat Reservasi</button>
    </div>

    <div class="flex gap-2 mb-4">
      <button v-for="s in ['', 'PENDING','CONFIRMED','COMPLETED','CANCELLED']" :key="s"
        @click="statusFilter = s"
        :class="statusFilter === s ? 'btn-primary' : 'btn-secondary'"
        class="btn-sm capitalize">{{ s || 'Semua' }}</button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div v-for="res in filtered" :key="res.id" class="card p-5">
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
        </div>
        <div class="flex gap-2 mt-4" v-if="res.status === 'PENDING'">
          <button @click="updateStatus(res, 'CONFIRMED')" class="btn-primary btn-sm flex-1">Konfirmasi</button>
          <button @click="updateStatus(res, 'CANCELLED')" class="btn-danger btn-sm flex-1">Batalkan</button>
        </div>
        <div class="flex gap-2 mt-4" v-if="res.status === 'CONFIRMED'">
          <button @click="updateStatus(res, 'COMPLETED')" class="btn-primary btn-sm flex-1">Selesai</button>
        </div>
      </div>
      <div v-if="!filtered.length" class="col-span-full text-center text-gray-300 py-16">Tidak ada reservasi</div>
    </div>

    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div class="card p-6 w-full max-w-md overflow-y-auto max-h-screen">
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
          <div class="flex gap-2 pt-2">
            <button type="submit" class="btn-primary flex-1">Buat Reservasi</button>
            <button type="button" @click="showModal = false" class="btn-secondary flex-1">Batal</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import api from '@/composables/useApi'
import { useToast } from 'vue-toastification'
import dayjs from 'dayjs'

const toast = useToast()
const reservations = ref([])
const statusFilter = ref('')
const showModal = ref(false)
const form = reactive({ customer_name: '', phone: '', table_number: '', pax: 2, reservation_date: '', dp_amount: 0, dp_method: 'CASH', notes: '' })

const filtered = computed(() =>
  statusFilter.value ? reservations.value.filter(r => r.status === statusFilter.value) : reservations.value
)

const formatRp = (n) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(n)
const formatDate = (d) => d ? dayjs(d).format('D MMM YYYY HH:mm') : '-'
const statusBadge = (s) => ({ PENDING: 'badge-yellow', CONFIRMED: 'badge-blue', COMPLETED: 'badge-green', CANCELLED: 'badge-red' }[s] || 'badge-gray')

async function loadReservations() {
  const res = await api.get('/api/v1/pos/reservations')
  reservations.value = res.data
}

async function createReservation() {
  try {
    await api.post('/api/v1/pos/reservations', form)
    toast.success('Reservasi dibuat')
    showModal.value = false
    loadReservations()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal buat reservasi')
  }
}

async function updateStatus(res, status) {
  await api.patch(`/api/v1/pos/reservations/${res.id}/status`, { status })
  loadReservations()
}

onMounted(loadReservations)
</script>
