<template>
  <div class="p-6 max-w-5xl mx-auto space-y-5">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900">Gaji Karyawan</h1>
      <div class="flex gap-2">
        <button @click="activeTab = 'payroll'" :class="['btn-sm border transition-all', activeTab === 'payroll' ? 'btn-primary' : 'btn-secondary']">Slip Gaji</button>
        <button @click="activeTab = 'employees'" :class="['btn-sm border transition-all', activeTab === 'employees' ? 'btn-primary' : 'btn-secondary']">Karyawan</button>
        <button @click="activeTab = 'financial'; loadFinancial()" :class="['btn-sm border transition-all', activeTab === 'financial' ? 'btn-primary' : 'btn-secondary']">Ringkasan Keuangan</button>
      </div>
    </div>

    <!-- ==================== TAB SLIP GAJI ==================== -->
    <div v-if="activeTab === 'payroll'" class="space-y-4">
      <!-- Filter periode + Generate All -->
      <div class="card p-4 flex flex-wrap items-end gap-3">
        <div>
          <label class="label">Bulan</label>
          <select v-model.number="filterMonth" class="input w-32" @change="loadRecords">
            <option v-for="m in months" :key="m.value" :value="m.value">{{ m.label }}</option>
          </select>
        </div>
        <div>
          <label class="label">Tahun</label>
          <select v-model.number="filterYear" class="input w-28" @change="loadRecords">
            <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
          </select>
        </div>
        <button @click="generateAll" class="btn-secondary btn-sm" :disabled="generatingAll">
          {{ generatingAll ? 'Generating...' : '⚡ Generate Semua' }}
        </button>
        <button @click="openAddRecord" class="btn-primary btn-sm">+ Tambah Manual</button>
        <div class="flex-1" />
        <!-- Summary -->
        <div v-if="summary" class="flex gap-4 text-sm">
          <div class="text-center">
            <p class="text-xs text-gray-400">Total Gaji</p>
            <p class="font-bold text-gray-900">{{ formatRp(summary.total_gaji) }}</p>
          </div>
          <div class="text-center">
            <p class="text-xs text-gray-400">Sudah Dibayar</p>
            <p class="font-bold text-green-600">{{ formatRp(summary.sudah_dibayar) }}</p>
          </div>
          <div class="text-center">
            <p class="text-xs text-gray-400">Belum Dibayar</p>
            <p class="font-bold text-red-500">{{ formatRp(summary.belum_dibayar) }}</p>
          </div>
        </div>
      </div>

      <!-- List slip gaji -->
      <div class="card overflow-hidden">
        <div v-if="records.length === 0" class="text-center py-12 text-gray-400">
          <p class="text-4xl mb-2">💸</p>
          <p class="text-sm">Belum ada slip gaji untuk periode ini.</p>
          <p class="text-xs mt-1">Klik "Generate Semua" untuk buat otomatis dari data karyawan.</p>
        </div>
        <table v-else class="w-full text-sm">
          <thead class="bg-gray-50 border-b">
            <tr>
              <th class="text-left px-4 py-3 font-medium text-gray-600">Karyawan</th>
              <th class="text-right px-4 py-3 font-medium text-gray-600">Gaji Pokok</th>
              <th class="text-right px-4 py-3 font-medium text-gray-600">Bonus</th>
              <th class="text-right px-4 py-3 font-medium text-gray-600">Potongan</th>
              <th class="text-right px-4 py-3 font-medium text-gray-600">Total</th>
              <th class="text-center px-4 py-3 font-medium text-gray-600">Status</th>
              <th class="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody class="divide-y">
            <tr v-for="r in records" :key="r.id" class="hover:bg-gray-50 transition-colors">
              <td class="px-4 py-3 font-medium text-gray-900">{{ r.employee_name }}</td>
              <td class="px-4 py-3 text-right text-gray-700">{{ formatRp(r.base_salary) }}</td>
              <td class="px-4 py-3 text-right text-green-600">{{ r.bonus > 0 ? '+' + formatRp(r.bonus) : '-' }}</td>
              <td class="px-4 py-3 text-right text-red-500">{{ r.deduction > 0 ? '-' + formatRp(r.deduction) : '-' }}</td>
              <td class="px-4 py-3 text-right font-bold text-gray-900">{{ formatRp(r.total) }}</td>
              <td class="px-4 py-3 text-center">
                <span :class="r.status === 'paid' ? 'badge-green' : 'badge-yellow'">
                  {{ r.status === 'paid' ? 'Dibayar' : 'Draft' }}
                </span>
              </td>
              <td class="px-4 py-3">
                <div class="flex gap-1 justify-end">
                  <button @click="openEditRecord(r)" class="btn-sm btn-secondary text-xs">Edit</button>
                  <button v-if="r.status === 'draft'" @click="markPaid(r)" class="btn-sm btn-primary text-xs">Bayar</button>
                  <button @click="deleteRecord(r)" class="btn-sm text-xs text-red-500 hover:bg-red-50 border border-red-200 rounded px-2">Hapus</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ==================== TAB KARYAWAN ==================== -->
    <div v-if="activeTab === 'employees'" class="space-y-4">
      <div class="flex justify-end">
        <button @click="openAddEmployee" class="btn-primary btn-sm">+ Tambah Karyawan</button>
      </div>
      <div class="card overflow-hidden">
        <div v-if="employees.length === 0" class="text-center py-12 text-gray-400">
          <p class="text-4xl mb-2">👥</p>
          <p class="text-sm">Belum ada karyawan. Tambah dulu ya.</p>
        </div>
        <table v-else class="w-full text-sm">
          <thead class="bg-gray-50 border-b">
            <tr>
              <th class="text-left px-4 py-3 font-medium text-gray-600">Nama</th>
              <th class="text-left px-4 py-3 font-medium text-gray-600">Jabatan</th>
              <th class="text-left px-4 py-3 font-medium text-gray-600">No. HP</th>
              <th class="text-right px-4 py-3 font-medium text-gray-600">Gaji Pokok</th>
              <th class="text-left px-4 py-3 font-medium text-gray-600">Mulai Kerja</th>
              <th class="text-center px-4 py-3 font-medium text-gray-600">Status</th>
              <th class="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody class="divide-y">
            <tr v-for="e in employees" :key="e.id" class="hover:bg-gray-50 transition-colors">
              <td class="px-4 py-3 font-medium text-gray-900">{{ e.name }}</td>
              <td class="px-4 py-3 text-gray-600">{{ e.position || '-' }}</td>
              <td class="px-4 py-3 text-gray-600">{{ e.phone || '-' }}</td>
              <td class="px-4 py-3 text-right font-medium">{{ formatRp(e.base_salary) }}</td>
              <td class="px-4 py-3 text-gray-500 text-xs">{{ e.join_date || '-' }}</td>
              <td class="px-4 py-3 text-center">
                <span :class="e.is_active ? 'badge-green' : 'badge-red'">{{ e.is_active ? 'Aktif' : 'Nonaktif' }}</span>
              </td>
              <td class="px-4 py-3">
                <div class="flex gap-1 justify-end">
                  <button @click="openEditEmployee(e)" class="btn-sm btn-secondary text-xs">Edit</button>
                  <button @click="deleteEmployee(e)" class="btn-sm text-xs text-red-500 hover:bg-red-50 border border-red-200 rounded px-2">Hapus</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ==================== TAB RINGKASAN KEUANGAN ==================== -->
    <div v-if="activeTab === 'financial'" class="space-y-4">
      <!-- Filter periode -->
      <div class="card p-4 flex flex-wrap items-end gap-3">
        <div>
          <label class="label">Bulan</label>
          <select v-model.number="filterMonth" class="input w-32" @change="loadFinancial">
            <option v-for="m in months" :key="m.value" :value="m.value">{{ m.label }}</option>
          </select>
        </div>
        <div>
          <label class="label">Tahun</label>
          <select v-model.number="filterYear" class="input w-28" @change="loadFinancial">
            <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
          </select>
        </div>
      </div>

      <div v-if="financial" class="space-y-4">
        <!-- Kartu ringkasan -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div class="card p-4 text-center">
            <p class="text-xs text-gray-400 mb-1">Revenue</p>
            <p class="text-lg font-bold text-green-600">{{ formatRp(financial.revenue) }}</p>
          </div>
          <div class="card p-4 text-center">
            <p class="text-xs text-gray-400 mb-1">Total Pengeluaran</p>
            <p class="text-lg font-bold text-red-500">{{ formatRp(financial.total_deductions) }}</p>
          </div>
          <div class="card p-4 text-center border-2" :class="financial.net_profit >= 0 ? 'border-green-200' : 'border-red-200'">
            <p class="text-xs text-gray-400 mb-1">Laba Bersih</p>
            <p class="text-lg font-bold" :class="financial.net_profit >= 0 ? 'text-green-600' : 'text-red-500'">
              {{ formatRp(financial.net_profit) }}
            </p>
          </div>
          <div class="card p-4 text-center">
            <p class="text-xs text-gray-400 mb-1">Gaji Karyawan</p>
            <p class="text-lg font-bold text-orange-500">{{ formatRp(financial.total_salary) }}</p>
            <p class="text-xs text-gray-400 mt-0.5">
              <span class="text-green-600">{{ formatRp(financial.salary_paid) }} dibayar</span> ·
              <span class="text-red-400">{{ formatRp(financial.salary_draft) }} pending</span>
            </p>
          </div>
        </div>

        <!-- Detail breakdown -->
        <div class="card p-5">
          <h3 class="font-semibold text-gray-900 mb-4">Rincian Keuangan</h3>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between py-2 border-b">
              <span class="text-gray-700">💰 Revenue Penjualan</span>
              <span class="font-medium text-green-600">+ {{ formatRp(financial.revenue) }}</span>
            </div>
            <div class="flex justify-between py-2 border-b text-gray-500">
              <span>🧾 Pengeluaran Operasional</span>
              <span class="text-red-500">- {{ formatRp(financial.expenses) }}</span>
            </div>
            <div class="flex justify-between py-2 border-b text-gray-500">
              <span>👥 Total Gaji Karyawan</span>
              <span class="text-red-500">- {{ formatRp(financial.total_salary) }}</span>
            </div>
            <!-- Biaya custom -->
            <div v-if="financial.monthly_costs_detail.length > 0">
              <div v-for="c in financial.monthly_costs_detail" :key="c.id" class="flex justify-between py-1.5 pl-4 text-gray-500">
                <span>📌 {{ c.name }}</span>
                <span class="text-red-500">- {{ formatRp(c.amount) }}</span>
              </div>
            </div>
            <div class="flex justify-between py-3 font-bold text-base">
              <span class="text-gray-900">Laba Bersih</span>
              <span :class="financial.net_profit >= 0 ? 'text-green-600' : 'text-red-500'">
                {{ financial.net_profit >= 0 ? '+' : '' }}{{ formatRp(financial.net_profit) }}
              </span>
            </div>
          </div>
        </div>

        <!-- Biaya Operasional Custom -->
        <div class="card p-5">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="font-semibold text-gray-900">Biaya Operasional</h3>
              <p class="text-xs text-gray-400 mt-0.5">Listrik, air, pajak, sewa, dan lainnya</p>
            </div>
            <button @click="openAddCost" class="btn-primary btn-sm">+ Tambah</button>
          </div>
          <div v-if="financial.monthly_costs_detail.length === 0" class="text-center py-6 text-gray-300 text-sm">
            Belum ada biaya. Tambah listrik, air, pajak, dll.
          </div>
          <div v-else class="space-y-2">
            <div v-for="c in financial.monthly_costs_detail" :key="c.id"
              class="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-xl">
              <span class="text-sm font-medium text-gray-800">{{ c.name }}</span>
              <div class="flex items-center gap-3">
                <span class="text-sm text-red-500 font-medium">{{ formatRp(c.amount) }}</span>
                <button @click="deleteCost(c)" class="text-xs text-red-400 hover:text-red-600">Hapus</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== MODAL BIAYA CUSTOM ==================== -->
    <div v-if="costModal.open" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6 space-y-4">
        <h2 class="font-bold text-lg text-gray-900">Tambah Biaya Operasional</h2>
        <div class="space-y-3">
          <div>
            <label class="label">Nama Biaya <span class="text-red-500">*</span></label>
            <input v-model="costModal.name" class="input" placeholder="Listrik, Air, Pajak, Sewa, dll" />
          </div>
          <div>
            <label class="label">Jumlah (Rp) <span class="text-red-500">*</span></label>
            <input v-model.number="costModal.amount" type="number" class="input" placeholder="500000" />
          </div>
        </div>
        <div class="flex gap-2 pt-2">
          <button @click="saveCost" class="btn-primary flex-1" :disabled="!costModal.name || !costModal.amount">Tambah</button>
          <button @click="costModal.open = false" class="btn-secondary flex-1">Batal</button>
        </div>
      </div>
    </div>

    <!-- ==================== MODAL KARYAWAN ==================== -->
    <div v-if="empModal.open" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4">
        <h2 class="font-bold text-lg text-gray-900">{{ empModal.id ? 'Edit Karyawan' : 'Tambah Karyawan' }}</h2>
        <div class="space-y-3">
          <div>
            <label class="label">Nama <span class="text-red-500">*</span></label>
            <input v-model="empModal.name" class="input" placeholder="Nama lengkap" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="label">Jabatan</label>
              <input v-model="empModal.position" class="input" placeholder="Kasir, Chef, dll" />
            </div>
            <div>
              <label class="label">No. HP</label>
              <input v-model="empModal.phone" class="input" placeholder="08xxx" />
            </div>
          </div>
          <div>
            <label class="label">Gaji Pokok (Rp)</label>
            <input v-model.number="empModal.base_salary" type="number" class="input" placeholder="3000000" />
          </div>
          <div>
            <label class="label">Tanggal Mulai Kerja</label>
            <input v-model="empModal.join_date" type="date" class="input" />
          </div>
          <div v-if="empModal.id" class="flex items-center gap-2">
            <input type="checkbox" v-model="empModal.is_active" id="emp-active" class="w-4 h-4" />
            <label for="emp-active" class="text-sm">Karyawan aktif</label>
          </div>
        </div>
        <div class="flex gap-2 pt-2">
          <button @click="saveEmployee" class="btn-primary flex-1" :disabled="!empModal.name">
            {{ empModal.id ? 'Simpan' : 'Tambah' }}
          </button>
          <button @click="empModal.open = false" class="btn-secondary flex-1">Batal</button>
        </div>
      </div>
    </div>

    <!-- ==================== MODAL SLIP GAJI ==================== -->
    <div v-if="recModal.open" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4">
        <h2 class="font-bold text-lg text-gray-900">{{ recModal.id ? 'Edit Slip Gaji' : 'Tambah Slip Gaji' }}</h2>
        <div class="space-y-3">
          <div v-if="!recModal.id">
            <label class="label">Karyawan <span class="text-red-500">*</span></label>
            <select v-model.number="recModal.employee_id" class="input">
              <option value="" disabled>Pilih karyawan</option>
              <option v-for="e in employees.filter(e => e.is_active)" :key="e.id" :value="e.id">
                {{ e.name }} — {{ formatRp(e.base_salary) }}
              </option>
            </select>
          </div>
          <div v-else>
            <label class="label">Karyawan</label>
            <p class="font-medium text-gray-900">{{ recModal.employee_name }}</p>
          </div>
          <div v-if="!recModal.id" class="grid grid-cols-2 gap-3">
            <div>
              <label class="label">Bulan</label>
              <select v-model.number="recModal.period_month" class="input">
                <option v-for="m in months" :key="m.value" :value="m.value">{{ m.label }}</option>
              </select>
            </div>
            <div>
              <label class="label">Tahun</label>
              <select v-model.number="recModal.period_year" class="input">
                <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
              </select>
            </div>
          </div>
          <div v-if="!recModal.id">
            <label class="label">Gaji Pokok (Rp) — kosongkan untuk pakai default</label>
            <input v-model.number="recModal.base_salary" type="number" class="input" placeholder="Gunakan default karyawan" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="label">Bonus (Rp)</label>
              <input v-model.number="recModal.bonus" type="number" class="input" placeholder="0" />
            </div>
            <div>
              <label class="label">Potongan (Rp)</label>
              <input v-model.number="recModal.deduction" type="number" class="input" placeholder="0" />
            </div>
          </div>
          <div>
            <label class="label">Catatan</label>
            <textarea v-model="recModal.notes" class="input h-20 resize-none" placeholder="Opsional..." />
          </div>
          <!-- Preview total -->
          <div v-if="recModal.id" class="bg-gray-50 rounded-xl p-3 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-500">Gaji Pokok</span>
              <span>{{ formatRp(recModal.base_salary_display) }}</span>
            </div>
            <div class="flex justify-between text-green-600">
              <span>+ Bonus</span>
              <span>{{ formatRp(recModal.bonus || 0) }}</span>
            </div>
            <div class="flex justify-between text-red-500">
              <span>- Potongan</span>
              <span>{{ formatRp(recModal.deduction || 0) }}</span>
            </div>
            <div class="flex justify-between font-bold text-gray-900 border-t pt-2 mt-2">
              <span>Total</span>
              <span>{{ formatRp((recModal.base_salary_display || 0) + (recModal.bonus || 0) - (recModal.deduction || 0)) }}</span>
            </div>
          </div>
        </div>
        <div class="flex gap-2 pt-2">
          <button @click="saveRecord" class="btn-primary flex-1">
            {{ recModal.id ? 'Simpan' : 'Tambah' }}
          </button>
          <button @click="recModal.open = false" class="btn-secondary flex-1">Batal</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/composables/useApi'
import { useToast } from 'vue-toastification'

const toast = useToast()

const activeTab = ref('payroll')
const employees = ref([])
const records = ref([])
const summary = ref(null)
const generatingAll = ref(false)

const now = new Date()
const filterMonth = ref(now.getMonth() + 1)
const filterYear = ref(now.getFullYear())

const years = Array.from({ length: 5 }, (_, i) => now.getFullYear() - 2 + i)
const months = [
  { value: 1, label: 'Januari' }, { value: 2, label: 'Februari' }, { value: 3, label: 'Maret' },
  { value: 4, label: 'April' }, { value: 5, label: 'Mei' }, { value: 6, label: 'Juni' },
  { value: 7, label: 'Juli' }, { value: 8, label: 'Agustus' }, { value: 9, label: 'September' },
  { value: 10, label: 'Oktober' }, { value: 11, label: 'November' }, { value: 12, label: 'Desember' },
]

const empModal = reactive({ open: false, id: null, name: '', position: '', phone: '', base_salary: 0, join_date: '', is_active: true })
const recModal = reactive({ open: false, id: null, employee_id: '', employee_name: '', period_month: now.getMonth() + 1, period_year: now.getFullYear(), base_salary: null, base_salary_display: 0, bonus: 0, deduction: 0, notes: '' })
const costModal = reactive({ open: false, name: '', amount: 0 })
const financial = ref(null)

const formatRp = (n) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(n || 0)

async function loadEmployees() {
  const res = await api.get('/api/v1/payroll/employees')
  employees.value = res.data
}

async function loadRecords() {
  const [recRes, sumRes] = await Promise.all([
    api.get('/api/v1/payroll/records', { params: { month: filterMonth.value, year: filterYear.value } }),
    api.get('/api/v1/payroll/summary', { params: { month: filterMonth.value, year: filterYear.value } }),
  ])
  records.value = recRes.data
  summary.value = sumRes.data
}

async function generateAll() {
  generatingAll.value = true
  try {
    const res = await api.post('/api/v1/payroll/records/generate-all', null, {
      params: { month: filterMonth.value, year: filterYear.value }
    })
    const { created, skipped } = res.data
    toast.success(`${created.length} slip dibuat${skipped.length ? `, ${skipped.length} sudah ada (skip)` : ''}`)
    await loadRecords()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal generate')
  } finally {
    generatingAll.value = false
  }
}

async function markPaid(r) {
  try {
    await api.patch(`/api/v1/payroll/records/${r.id}`, { status: 'paid' })
    toast.success(`Gaji ${r.employee_name} ditandai dibayar`)
    await loadRecords()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal update')
  }
}

async function deleteRecord(r) {
  if (!confirm(`Hapus slip gaji ${r.employee_name}?`)) return
  try {
    await api.delete(`/api/v1/payroll/records/${r.id}`)
    toast.success('Slip gaji dihapus')
    await loadRecords()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal hapus')
  }
}

// ---- Employee modal ----
function openAddEmployee() {
  Object.assign(empModal, { open: true, id: null, name: '', position: '', phone: '', base_salary: 0, join_date: '', is_active: true })
}
function openEditEmployee(e) {
  Object.assign(empModal, { open: true, id: e.id, name: e.name, position: e.position || '', phone: e.phone || '', base_salary: e.base_salary, join_date: e.join_date || '', is_active: e.is_active })
}
async function saveEmployee() {
  const payload = { name: empModal.name, position: empModal.position, phone: empModal.phone, base_salary: empModal.base_salary, join_date: empModal.join_date || null }
  try {
    if (empModal.id) {
      await api.patch(`/api/v1/payroll/employees/${empModal.id}`, { ...payload, is_active: empModal.is_active })
      toast.success('Karyawan diperbarui')
    } else {
      await api.post('/api/v1/payroll/employees', payload)
      toast.success('Karyawan ditambahkan')
    }
    empModal.open = false
    await loadEmployees()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal simpan')
  }
}
async function deleteEmployee(e) {
  if (!confirm(`Hapus karyawan ${e.name}?`)) return
  try {
    await api.delete(`/api/v1/payroll/employees/${e.id}`)
    toast.success('Karyawan dihapus')
    await loadEmployees()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal hapus')
  }
}

// ---- Record modal ----
function openAddRecord() {
  Object.assign(recModal, { open: true, id: null, employee_id: '', employee_name: '', period_month: filterMonth.value, period_year: filterYear.value, base_salary: null, base_salary_display: 0, bonus: 0, deduction: 0, notes: '' })
}
function openEditRecord(r) {
  Object.assign(recModal, { open: true, id: r.id, employee_id: r.employee_id, employee_name: r.employee_name, period_month: r.period_month, period_year: r.period_year, base_salary: null, base_salary_display: r.base_salary, bonus: r.bonus, deduction: r.deduction, notes: r.notes || '' })
}
async function saveRecord() {
  try {
    if (recModal.id) {
      await api.patch(`/api/v1/payroll/records/${recModal.id}`, { bonus: recModal.bonus, deduction: recModal.deduction, notes: recModal.notes })
      toast.success('Slip gaji diperbarui')
    } else {
      const payload = { employee_id: recModal.employee_id, period_month: recModal.period_month, period_year: recModal.period_year, bonus: recModal.bonus || 0, deduction: recModal.deduction || 0, notes: recModal.notes }
      if (recModal.base_salary) payload.base_salary = recModal.base_salary
      await api.post('/api/v1/payroll/records', payload)
      toast.success('Slip gaji ditambahkan')
    }
    recModal.open = false
    await loadRecords()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal simpan')
  }
}

// ---- Financial ----
async function loadFinancial() {
  const res = await api.get('/api/v1/payroll/financial-summary', { params: { month: filterMonth.value, year: filterYear.value } })
  financial.value = res.data
}

function openAddCost() {
  Object.assign(costModal, { open: true, name: '', amount: 0 })
}

async function saveCost() {
  try {
    await api.post('/api/v1/payroll/monthly-costs', {
      period_month: filterMonth.value,
      period_year: filterYear.value,
      name: costModal.name,
      amount: costModal.amount,
    })
    toast.success('Biaya ditambahkan')
    costModal.open = false
    await loadFinancial()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal simpan')
  }
}

async function deleteCost(c) {
  if (!confirm(`Hapus biaya "${c.name}"?`)) return
  try {
    await api.delete(`/api/v1/payroll/monthly-costs/${c.id}`)
    toast.success('Biaya dihapus')
    await loadFinancial()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal hapus')
  }
}

onMounted(async () => {
  await Promise.all([loadEmployees(), loadRecords()])
})
</script>
