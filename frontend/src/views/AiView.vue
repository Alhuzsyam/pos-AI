<template>
  <div class="p-6 max-w-4xl mx-auto">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">AI Assistant</h1>
      <p class="text-sm text-gray-400">Tanya apapun soal bisnis kamu. Didukung agentic AI tools.</p>
    </div>

    <!-- Tools List -->
    <div class="card p-5 mb-6">
      <h2 class="font-semibold text-gray-900 mb-3 flex items-center gap-2">
        <svg class="w-4 h-4 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        Tools Tersedia
      </h2>
      <div class="flex flex-wrap gap-2">
        <span
          v-for="tool in availableTools"
          :key="tool"
          class="badge-blue cursor-pointer hover:bg-blue-200 transition"
          @click="quickTool(tool)"
        >{{ tool }}</span>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-6">
      <button
        v-for="q in quickQueries"
        :key="q.label"
        @click="executeQuick(q)"
        class="card p-4 text-left hover:ring-2 hover:ring-brand-300 transition-all"
      >
        <span class="text-2xl">{{ q.emoji }}</span>
        <p class="text-sm font-semibold text-gray-800 mt-2">{{ q.label }}</p>
        <p class="text-xs text-gray-400">{{ q.desc }}</p>
      </button>
    </div>

    <!-- Manual Tool Executor -->
    <div class="card p-5 mb-6">
      <h2 class="font-semibold text-gray-900 mb-3">Eksekusi Tool Manual</h2>
      <div class="flex gap-2">
        <select v-model="selectedTool" class="input">
          <option v-for="tool in availableTools" :key="tool" :value="tool">{{ tool }}</option>
        </select>
        <button @click="executeTool" class="btn-primary flex-shrink-0" :disabled="executing">
          <svg v-if="executing" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          Jalankan
        </button>
      </div>
    </div>

    <!-- Results -->
    <div v-if="results.length" class="space-y-4">
      <h2 class="font-semibold text-gray-900">Hasil</h2>
      <div v-for="(result, i) in results" :key="i" class="card overflow-hidden">
        <div class="flex items-center justify-between px-5 py-3 bg-gray-50 border-b border-gray-100">
          <span class="font-mono text-sm text-brand-700 font-semibold">{{ result.tool }}</span>
          <span class="text-xs text-gray-400">{{ result.latency_ms }}ms</span>
        </div>
        <div class="p-5">
          <!-- Insights -->
          <div v-if="result.data?.insights" class="mb-4 space-y-2">
            <div
              v-for="insight in result.data.insights"
              :key="insight"
              class="flex items-start gap-2 text-sm text-gray-700"
            >
              <span class="text-brand-600 mt-0.5">•</span>
              {{ insight }}
            </div>
          </div>

          <!-- Generic table display -->
          <div v-if="Array.isArray(result.data)" class="overflow-x-auto">
            <table class="table-base" v-if="result.data.length">
              <thead>
                <tr>
                  <th v-for="col in Object.keys(result.data[0])" :key="col">{{ col }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in result.data" :key="JSON.stringify(row)">
                  <td v-for="col in Object.keys(row)" :key="col">
                    {{ typeof row[col] === 'number' && col.includes('revenue') ? formatRp(row[col]) : row[col] }}
                  </td>
                </tr>
              </tbody>
            </table>
            <p v-else class="text-gray-400 text-sm">Tidak ada data</p>
          </div>

          <!-- Object display -->
          <div v-else-if="typeof result.data === 'object' && !result.data?.insights">
            <pre class="text-xs text-gray-600 bg-gray-50 rounded-xl p-4 overflow-x-auto">{{ JSON.stringify(result.data, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/composables/useApi'

const availableTools = ref([])
const selectedTool = ref('')
const executing = ref(false)
const results = ref([])

const formatRp = (n) =>
  new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(n)

const quickQueries = [
  { emoji: '📊', label: 'Revenue Hari Ini', desc: 'Summary penjualan hari ini', tool: 'get_sales_summary', args: {} },
  { emoji: '🏆', label: 'Top Menu', desc: 'Menu terlaris 30 hari terakhir', tool: 'get_top_menu', args: { days: 30, limit: 10 } },
  { emoji: '📦', label: 'Cek Stok Rendah', desc: 'Produk yang perlu restock', tool: 'check_stock', args: { low_stock_only: true } },
  { emoji: '💡', label: 'Insights Bulan Ini', desc: 'Analisis otomatis bisnis', tool: 'get_business_insights', args: { period: 'month' } },
  { emoji: '💸', label: 'Pengeluaran', desc: 'Ringkasan pengeluaran bulan ini', tool: 'get_expenses_summary', args: {} },
  { emoji: '📅', label: 'Insights Minggu Ini', desc: 'Tren 7 hari terakhir', tool: 'get_business_insights', args: { period: 'week' } },
]

async function executeTool() {
  if (!selectedTool.value) return
  executing.value = true
  try {
    const res = await api.post('/api/v1/ai/execute', {
      tool_name: selectedTool.value,
      arguments: {},
    })
    results.value.unshift({ tool: res.data.tool, data: res.data.result, latency_ms: res.data.latency_ms })
  } catch (e) {
    console.error(e)
  } finally {
    executing.value = false
  }
}

async function executeQuick(q) {
  executing.value = true
  try {
    const res = await api.post('/api/v1/ai/execute', {
      tool_name: q.tool,
      arguments: q.args,
    })
    results.value.unshift({ tool: `${q.label} (${q.tool})`, data: res.data.result, latency_ms: res.data.latency_ms })
  } catch (e) {
    console.error(e)
  } finally {
    executing.value = false
  }
}

function quickTool(tool) {
  selectedTool.value = tool
}

onMounted(async () => {
  const res = await api.get('/api/v1/ai/tools')
  availableTools.value = res.data.tools.map(t => t.function.name)
  selectedTool.value = availableTools.value[0] || ''
})
</script>
