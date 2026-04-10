<template>
  <div class="p-6 max-w-5xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Pengeluaran</h1>
      <button @click="showModal = true" class="btn-primary">+ Catat Pengeluaran</button>
    </div>

    <div class="card overflow-hidden">
      <table class="table-base">
        <thead>
          <tr><th>Item</th><th>Kategori</th><th>Tanggal</th><th>Jumlah</th><th>Catatan</th></tr>
        </thead>
        <tbody>
          <tr v-for="e in expenses" :key="e.id">
            <td class="font-medium text-gray-800">{{ e.item_name }}</td>
            <td><span class="badge-gray">{{ e.category || '-' }}</span></td>
            <td class="text-xs text-gray-500">{{ e.purchase_date || '-' }}</td>
            <td class="font-semibold text-red-600">{{ formatRp(e.price) }}</td>
            <td class="text-xs text-gray-400">{{ e.note || '-' }}</td>
          </tr>
          <tr v-if="!expenses.length"><td colspan="5" class="text-center text-gray-300 py-8">Belum ada pengeluaran</td></tr>
        </tbody>
      </table>
    </div>

    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div class="card p-6 w-full max-w-sm">
        <h2 class="font-bold text-gray-900 mb-4">Catat Pengeluaran</h2>
        <form @submit.prevent="addExpense" class="space-y-3">
          <div><label class="label">Nama Item</label><input v-model="form.item_name" class="input" required /></div>
          <div><label class="label">Jumlah (Rp)</label><input v-model.number="form.price" type="number" class="input" required /></div>
          <div><label class="label">Kategori</label><input v-model="form.category" class="input" placeholder="Bahan baku, Operasional, dll" /></div>
          <div><label class="label">Tanggal</label><input v-model="form.purchase_date" type="date" class="input" /></div>
          <div><label class="label">Catatan</label><input v-model="form.note" class="input" /></div>
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
import { ref, onMounted, reactive } from 'vue'
import api from '@/composables/useApi'
import { useToast } from 'vue-toastification'

const toast = useToast()
const expenses = ref([])
const showModal = ref(false)
const form = reactive({ item_name: '', price: 0, category: '', purchase_date: '', note: '' })

const formatRp = (n) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(n)

async function addExpense() {
  try {
    await api.post('/api/v1/pos/expenses', form)
    toast.success('Pengeluaran dicatat')
    showModal.value = false
    Object.assign(form, { item_name: '', price: 0, category: '', purchase_date: '', note: '' })
    loadExpenses()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal catat')
  }
}

async function loadExpenses() {
  const res = await api.get('/api/v1/pos/expenses')
  expenses.value = res.data
}

onMounted(loadExpenses)
</script>
