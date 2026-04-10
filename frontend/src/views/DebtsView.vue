<template>
  <div class="p-6 max-w-5xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Buku Hutang</h1>
      <button @click="showModal = true" class="btn-primary">+ Catat Hutang</button>
    </div>

    <div class="flex gap-2 mb-4">
      <button @click="filterPaid = null" :class="filterPaid === null ? 'btn-primary' : 'btn-secondary'" class="btn-sm">Semua</button>
      <button @click="filterPaid = false" :class="filterPaid === false ? 'btn-primary' : 'btn-secondary'" class="btn-sm">Belum Lunas</button>
      <button @click="filterPaid = true" :class="filterPaid === true ? 'btn-primary' : 'btn-secondary'" class="btn-sm">Lunas</button>
    </div>

    <div class="card overflow-hidden">
      <table class="table-base">
        <thead><tr><th>Pelanggan</th><th>Total</th><th>Status</th><th>Jatuh Tempo</th><th></th></tr></thead>
        <tbody>
          <tr v-for="debt in filteredDebts" :key="debt.id">
            <td>
              <p class="font-medium text-gray-800">{{ debt.customer_name }}</p>
              <p class="text-xs text-gray-400">{{ debt.phone || '-' }}</p>
            </td>
            <td class="font-semibold text-red-600">{{ formatRp(debt.total_amount) }}</td>
            <td><span :class="debt.is_paid ? 'badge-green' : 'badge-red'">{{ debt.is_paid ? 'Lunas' : 'Belum' }}</span></td>
            <td class="text-xs text-gray-400">{{ debt.due_date || '-' }}</td>
            <td>
              <button v-if="!debt.is_paid" @click="payDebt(debt)" class="btn-primary btn-sm">Lunaskan</button>
            </td>
          </tr>
          <tr v-if="!filteredDebts.length"><td colspan="5" class="text-center text-gray-300 py-8">Tidak ada hutang</td></tr>
        </tbody>
      </table>
    </div>

    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div class="card p-6 w-full max-w-md">
        <h2 class="font-bold text-gray-900 mb-4">Catat Hutang</h2>
        <form @submit.prevent="addDebt" class="space-y-3">
          <div><label class="label">Nama Pelanggan</label><input v-model="form.customer_name" class="input" required /></div>
          <div><label class="label">No HP</label><input v-model="form.phone" class="input" /></div>
          <div><label class="label">Jatuh Tempo</label><input v-model="form.due_date" type="date" class="input" /></div>
          <div><label class="label">Catatan</label><input v-model="form.notes" class="input" /></div>
          <div class="border rounded-xl p-3">
            <div class="flex items-center justify-between mb-2">
              <label class="label mb-0">Item Hutang</label>
              <button type="button" @click="addItem" class="text-xs text-brand-700 font-semibold">+ Tambah</button>
            </div>
            <div v-for="(item, i) in form.items" :key="i" class="grid grid-cols-3 gap-2 mb-2">
              <input v-model="item.menu_name" class="input col-span-2" placeholder="Nama menu" />
              <input v-model.number="item.quantity" type="number" class="input" placeholder="Qty" min="1" />
              <input v-model.number="item.price_at_moment" type="number" class="input col-span-2" placeholder="Harga" />
              <button type="button" @click="form.items.splice(i, 1)" class="btn-danger btn-sm">✕</button>
            </div>
          </div>
          <div class="flex gap-2 pt-2">
            <button type="submit" class="btn-primary flex-1">Simpan</button>
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

const toast = useToast()
const debts = ref([])
const filterPaid = ref(null)
const showModal = ref(false)
const form = reactive({ customer_name: '', phone: '', due_date: '', notes: '', items: [] })

const filteredDebts = computed(() =>
  filterPaid.value === null ? debts.value : debts.value.filter(d => d.is_paid === filterPaid.value)
)
const formatRp = (n) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(n)

function addItem() { form.items.push({ menu_name: '', quantity: 1, price_at_moment: 0 }) }

async function loadDebts() {
  const res = await api.get('/api/v1/pos/debts')
  debts.value = res.data
}

async function addDebt() {
  if (!form.items.length) { toast.error('Tambah minimal 1 item'); return }
  try {
    await api.post('/api/v1/pos/debts', form)
    toast.success('Hutang dicatat')
    showModal.value = false
    Object.assign(form, { customer_name: '', phone: '', due_date: '', notes: '', items: [] })
    loadDebts()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal catat hutang')
  }
}

async function payDebt(debt) {
  if (!confirm(`Lunaskan hutang ${debt.customer_name} sebesar ${formatRp(debt.total_amount)}?`)) return
  await api.patch(`/api/v1/pos/debts/${debt.id}/pay`)
  toast.success('Hutang dilunasi!')
  loadDebts()
}

onMounted(loadDebts)
</script>
