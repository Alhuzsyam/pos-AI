<template>
  <div class="p-6 max-w-3xl mx-auto space-y-5">
    <h1 class="text-2xl font-bold text-gray-900">Pengaturan</h1>

    <!-- Profile -->
    <div class="card p-5">
      <h2 class="font-semibold text-gray-900 mb-4">Profil Saya</h2>
      <div class="grid grid-cols-2 gap-4 text-sm">
        <div><label class="label">Username</label><p class="font-medium text-gray-800">{{ auth.user?.username }}</p></div>
        <div><label class="label">Role</label><span :class="`badge-${roleColor}`">{{ auth.user?.role }}</span></div>
        <div><label class="label">Tenant</label><p class="text-gray-700">{{ auth.user?.tenant_name || 'Superadmin (global)' }}</p></div>
      </div>
    </div>

    <!-- AI Settings -->
    <div class="card p-5">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="font-semibold text-gray-900">AI Provider Settings</h2>
          <p class="text-xs text-gray-400 mt-0.5">Tiap tenant punya API key sendiri. Gw support OpenAI, Gemini, Groq, dan Ollama.</p>
        </div>
        <span :class="hasKey ? 'badge-green' : 'badge-red'">{{ hasKey ? 'Key Aktif' : 'Belum Setup' }}</span>
      </div>

      <div class="space-y-4">
        <div>
          <label class="label">Provider</label>
          <div class="flex gap-2 flex-wrap">
            <button v-for="p in providers" :key="p.value"
              @click="aiForm.ai_provider = p.value"
              :class="['btn-sm border transition-all', aiForm.ai_provider === p.value ? 'btn-primary' : 'btn-secondary']">
              {{ p.label }}
            </button>
          </div>
        </div>

        <div v-if="aiForm.ai_provider === 'openai'">
          <label class="label">OpenAI API Key</label>
          <input v-model="aiForm.openai_api_key" class="input font-mono text-xs" :placeholder="currentSettings?.has_openai_key ? 'sk-••••••••••••••••••••••' : 'sk-...'" />
          <div class="mt-2">
            <label class="label">Model</label>
            <select v-model="aiForm.ai_model" class="input">
              <option value="gpt-4o-mini">gpt-4o-mini (Cepat & Murah)</option>
              <option value="gpt-4o">gpt-4o (Terbaik)</option>
              <option value="gpt-3.5-turbo">gpt-3.5-turbo (Legacy)</option>
            </select>
          </div>
        </div>

        <div v-if="aiForm.ai_provider === 'gemini'">
          <label class="label">Google Gemini API Key</label>
          <input v-model="aiForm.gemini_api_key" class="input font-mono text-xs" :placeholder="currentSettings?.has_gemini_key ? 'AIza••••••••••••••' : 'AIza...'" />
          <p class="text-xs text-gray-400 mt-1">Gratis tier tersedia. Daftar di <span class="text-brand-700">aistudio.google.com</span></p>
        </div>

        <div v-if="aiForm.ai_provider === 'groq'">
          <label class="label">Groq API Key</label>
          <input v-model="aiForm.groq_api_key" class="input font-mono text-xs" :placeholder="currentSettings?.has_groq_key ? 'gsk_••••••••••••••••' : 'gsk_...'" />
          <div class="mt-2">
            <label class="label">Model</label>
            <select v-model="aiForm.ai_model" class="input">
              <option value="llama-3.3-70b-versatile">Llama 3.3 70B (Gratis!)</option>
              <option value="mixtral-8x7b-32768">Mixtral 8x7B</option>
            </select>
          </div>
          <p class="text-xs text-gray-400 mt-1">Groq gratis dan sangat cepat! Daftar di <span class="text-brand-700">console.groq.com</span></p>
        </div>

        <div v-if="aiForm.ai_provider === 'ollama'">
          <label class="label">Ollama Host</label>
          <input v-model="aiForm.ollama_host" class="input" placeholder="http://localhost:11434" />
          <div class="mt-2">
            <label class="label">Model</label>
            <input v-model="aiForm.ai_model" class="input" placeholder="llama3, mistral, dll" />
          </div>
          <p class="text-xs text-gray-400 mt-1">Jalankan AI lokal dengan Ollama. Gratis, privat.</p>
        </div>

        <button @click="saveAiSettings" class="btn-primary" :disabled="savingAi">
          {{ savingAi ? 'Menyimpan...' : 'Simpan AI Settings' }}
        </button>
      </div>
    </div>

    <!-- Business Profile -->
    <div class="card p-5">
      <h2 class="font-semibold text-gray-900 mb-4">Profil Bisnis</h2>
      <p class="text-xs text-gray-400 mb-4">Digunakan AI untuk memberikan insight yang lebih relevan dengan bisnis kamu.</p>
      <div class="space-y-3">
        <div>
          <label class="label">Tipe Bisnis</label>
          <select v-model="bizForm.business_type" class="input">
            <option value="cafe">Cafe / Coffee Shop</option>
            <option value="restaurant">Restoran</option>
            <option value="warung">Warung Makan</option>
            <option value="retail">Toko Retail</option>
            <option value="bakery">Bakery / Kue</option>
            <option value="other">Lainnya</option>
          </select>
        </div>
        <div>
          <label class="label">Deskripsi Bisnis</label>
          <textarea v-model="bizForm.business_description" class="input h-24 resize-none" placeholder="Ceritakan bisnis kamu: lokasi, target pelanggan, keunggulan, dll. Semakin detail, insight AI semakin akurat." />
        </div>
        <div>
          <label class="label">Target Omzet Harian (Rp)</label>
          <input v-model.number="bizForm.target_daily_revenue" type="number" class="input" placeholder="Contoh: 2000000" />
        </div>
        <button @click="saveBizSettings" class="btn-primary">Simpan Profil Bisnis</button>
      </div>
    </div>

    <!-- Weekly Insights -->
    <div class="card p-5">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="font-semibold text-gray-900">Weekly AI Insights</h2>
          <p class="text-xs text-gray-400 mt-0.5">Analisis bisnis mingguan + 5 langkah aksi untuk growth</p>
        </div>
        <button @click="generateInsight" class="btn-primary btn-sm" :disabled="generating">
          <svg v-if="generating" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          {{ generating ? 'Generating...' : '✨ Generate Sekarang' }}
        </button>
      </div>

      <!-- Latest Insight -->
      <div v-if="latestInsight?.insight_text" class="space-y-3">
        <div class="flex items-center gap-2 text-xs text-gray-400">
          <span>📅 {{ latestInsight.week_start }} s/d {{ latestInsight.week_end }}</span>
          <span>·</span>
          <span>🤖 {{ latestInsight.ai_provider_used }}</span>
        </div>

        <!-- Metrics snapshot -->
        <div class="grid grid-cols-3 gap-2" v-if="latestInsight.metrics">
          <div class="bg-gray-50 rounded-xl p-3 text-center">
            <p class="text-xs text-gray-400">Revenue</p>
            <p class="text-sm font-bold text-gray-900">{{ formatRp(latestInsight.metrics.this_week_revenue) }}</p>
            <p class="text-xs" :class="latestInsight.metrics.revenue_growth_pct >= 0 ? 'text-green-600' : 'text-red-600'">
              {{ latestInsight.metrics.revenue_growth_pct >= 0 ? '↑' : '↓' }}{{ Math.abs(latestInsight.metrics.revenue_growth_pct) }}%
            </p>
          </div>
          <div class="bg-gray-50 rounded-xl p-3 text-center">
            <p class="text-xs text-gray-400">Transaksi</p>
            <p class="text-sm font-bold text-gray-900">{{ latestInsight.metrics.this_week_transactions }}x</p>
          </div>
          <div class="bg-gray-50 rounded-xl p-3 text-center">
            <p class="text-xs text-gray-400">Profit Est.</p>
            <p class="text-sm font-bold" :class="latestInsight.metrics.net_profit_estimate >= 0 ? 'text-green-600' : 'text-red-600'">
              {{ formatRp(latestInsight.metrics.net_profit_estimate) }}
            </p>
          </div>
        </div>

        <!-- Insight text -->
        <div class="bg-gradient-to-br from-brand-50 to-blue-50 rounded-xl p-4 border border-brand-100">
          <p class="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">{{ latestInsight.insight_text }}</p>
        </div>

        <!-- Action items -->
        <div v-if="latestInsight.action_items?.length" class="bg-yellow-50 rounded-xl p-4 border border-yellow-100">
          <p class="text-xs font-bold text-yellow-700 uppercase mb-2">Langkah Aksi</p>
          <ul class="space-y-1">
            <li v-for="(item, i) in latestInsight.action_items" :key="i" class="flex items-start gap-2 text-sm text-yellow-800">
              <span class="text-yellow-500 font-bold flex-shrink-0">{{ i + 1 }}.</span>
              {{ item }}
            </li>
          </ul>
        </div>
      </div>
      <div v-else class="text-center py-8 text-gray-300">
        <p class="text-4xl mb-2">✨</p>
        <p class="text-sm">Belum ada insight. Klik "Generate Sekarang" untuk analisis bisnis kamu.</p>
        <p class="text-xs mt-1 text-gray-300">Butuh API key dulu ya (setup di AI Settings di atas)</p>
      </div>
    </div>

    <!-- WhatsApp Notification Settings -->
    <div class="card p-5">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="font-semibold text-gray-900">Notifikasi WhatsApp</h2>
          <p class="text-xs text-gray-400 mt-0.5">Kirim laporan harian & alert stok rendah via WhatsApp (WAHA API)</p>
        </div>
        <label class="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" v-model="waForm.whatsapp_notify" class="w-4 h-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500" />
          <span class="text-sm font-medium" :class="waForm.whatsapp_notify ? 'text-green-600' : 'text-gray-400'">{{ waForm.whatsapp_notify ? 'Aktif' : 'Nonaktif' }}</span>
        </label>
      </div>

      <!-- Form fields — disabled saat notify off -->
      <div class="space-y-3" :class="{ 'opacity-50 pointer-events-none': !waForm.whatsapp_notify }">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="label">WAHA URL</label>
            <input v-model="waForm.waha_url" class="input text-xs" placeholder="http://localhost:3000" />
          </div>
          <div>
            <label class="label">WAHA Session</label>
            <input v-model="waForm.waha_session" class="input text-xs" placeholder="default" />
          </div>
        </div>
        <div>
          <label class="label">WAHA API Key</label>
          <input v-model="waForm.waha_api_key" class="input font-mono text-xs" :placeholder="currentSettings?.has_waha_key ? '••••••••••••' : 'API key WAHA'" />
        </div>
        <div>
          <label class="label">WhatsApp Group ID</label>
          <input v-model="waForm.whatsapp_group_id" class="input font-mono text-xs" placeholder="120363xxxxx@g.us" />
          <p class="text-[10px] text-gray-400 mt-1">ID group WA tujuan notifikasi. Bisa didapat dari WAHA API.</p>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="label">Jam Kirim</label>
            <select v-model.number="waForm.whatsapp_schedule_hour" class="input">
              <option v-for="h in 24" :key="h-1" :value="h-1">{{ String(h-1).padStart(2,'0') }}:00</option>
            </select>
          </div>
          <div>
            <label class="label">Menit</label>
            <select v-model.number="waForm.whatsapp_schedule_minute" class="input">
              <option v-for="m in [0,15,30,45]" :key="m" :value="m">:{{ String(m).padStart(2,'0') }}</option>
            </select>
          </div>
        </div>
      </div>
      <!-- Tombol selalu bisa diklik, tidak ikut disabled -->
      <div class="flex gap-2 mt-3">
        <button @click="saveWaSettings" class="btn-primary">Simpan WA Settings</button>
        <button @click="testWhatsapp" class="btn-secondary" :disabled="testingWa">
          {{ testingWa ? 'Mengirim...' : 'Test Kirim' }}
        </button>
      </div>
    </div>

    <!-- API Integration -->
    <div class="card p-5">
      <h2 class="font-semibold text-gray-900 mb-3">Integrasi Agentic AI</h2>
      <p class="text-sm text-gray-500 mb-3">Gunakan endpoint ini untuk koneksi dengan LangChain, AutoGen, CrewAI, dll.</p>
      <div class="space-y-2">
        <div v-for="ep in endpoints" :key="ep.label">
          <label class="label">{{ ep.label }}</label>
          <div class="flex gap-2">
            <input :value="ep.url" class="input font-mono text-xs" readonly />
            <button @click="copy(ep.url)" class="btn-secondary btn-sm flex-shrink-0">Copy</button>
          </div>
        </div>
      </div>
      <div class="mt-3 p-3 bg-blue-50 rounded-xl text-xs text-blue-700 space-y-1">
        <p class="font-bold">Auth Header:</p>
        <p class="font-mono">Authorization: Bearer &lt;access_token&gt;</p>
        <p class="font-bold mt-2">Example Tool Call (POST /api/v1/ai/execute):</p>
        <pre class="font-mono text-xs">{{"{\n  \"tool_name\": \"get_business_insights\",\n  \"arguments\": {\"period\": \"week\"}\n}"}}</pre>
      </div>
    </div>

    <!-- Divisions & Watchlist -->
    <div class="card p-5">
      <h2 class="font-semibold text-gray-900 mb-4">Divisi & Watchlist</h2>
      <div class="space-y-4">
        <div>
          <label class="label">Divisi Menu</label>
          <p class="text-xs text-gray-400 mb-2">Divisi yang muncul di POS, Menu, dan Watchlist/KDS</p>
          <div class="flex flex-wrap gap-2 mb-2">
            <span v-for="(d, i) in divForm.divisions" :key="i"
              class="inline-flex items-center gap-1 bg-brand-50 text-brand-700 px-3 py-1 rounded-full text-sm font-medium">
              {{ d }}
              <button type="button" @click="divForm.divisions.splice(i, 1)" class="text-brand-400 hover:text-red-600 ml-1">✕</button>
            </span>
          </div>
          <div class="flex gap-2">
            <input v-model="newDivision" class="input flex-1" placeholder="Nama divisi baru" @keydown.enter.prevent="addDivision" />
            <button type="button" @click="addDivision" class="btn-secondary btn-sm">Tambah</button>
          </div>
        </div>
        <div class="flex items-center justify-between pt-2 border-t">
          <div>
            <p class="text-sm font-medium text-gray-800">Watchlist / KDS</p>
            <p class="text-xs text-gray-400">Aktifkan Kitchen Display System untuk monitor pesanan</p>
          </div>
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" v-model="divForm.watchlist_enabled" class="w-4 h-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500" />
            <span class="text-sm font-medium" :class="divForm.watchlist_enabled ? 'text-green-600' : 'text-gray-400'">{{ divForm.watchlist_enabled ? 'Aktif' : 'Nonaktif' }}</span>
          </label>
        </div>
        <button @click="saveDivSettings" class="btn-primary">Simpan Divisi & Watchlist</button>
      </div>
    </div>

    <!-- Bluetooth Printer -->
    <div class="card p-5">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="font-semibold text-gray-900">Printer Bluetooth</h2>
          <p class="text-xs text-gray-400 mt-0.5">Hubungkan thermal printer via Bluetooth untuk cetak struk</p>
        </div>
        <span :class="printer.pairedDevice.value ? 'badge-green' : 'badge-red'">{{ printer.pairedDevice.value ? 'Connected' : 'Disconnected' }}</span>
      </div>

      <div class="space-y-4">
        <!-- Status -->
        <div class="bg-gray-50 rounded-xl p-4 flex items-center gap-4">
          <div :class="['w-12 h-12 rounded-full flex items-center justify-center text-white text-lg', printer.pairedDevice.value ? 'bg-green-500' : 'bg-gray-400']">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" /></svg>
          </div>
          <div>
            <p class="text-sm font-semibold text-gray-800">{{ printer.pairedDevice.value ? printer.pairedDevice.value.name : 'Belum Ada Printer' }}</p>
            <p class="text-xs text-gray-400">{{ printer.printerStatus.value }}</p>
            <p v-if="!printer.pairedDevice.value && lastPrinterName" class="text-xs text-gray-400">Terakhir: {{ lastPrinterName }}</p>
          </div>
        </div>

        <!-- Guide -->
        <div class="bg-blue-50 rounded-xl p-3 text-xs text-blue-700 space-y-1">
          <p class="font-bold">Panduan Koneksi:</p>
          <ul class="list-disc pl-4 space-y-0.5">
            <li>Pastikan Bluetooth perangkat sudah aktif</li>
            <li>Nyalakan printer thermal Bluetooth (RPP02N, MTP-2, dll)</li>
            <li>Klik "Cari Printer" dan pilih nama printer</li>
            <li>Gunakan "Test Print" untuk memastikan koneksi</li>
          </ul>
        </div>

        <!-- Buttons -->
        <div class="flex gap-2">
          <button @click="handleConnectPrinter" class="btn-primary flex-1" :disabled="printer.isConnecting.value">
            {{ printer.isConnecting.value ? 'Mencari...' : 'Cari Printer' }}
          </button>
          <button v-if="printer.pairedDevice.value" @click="handleTestPrint" class="btn-secondary flex-1" :disabled="printer.isPrinting.value">
            {{ printer.isPrinting.value ? 'Mencetak...' : 'Test Print' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Change Password -->
    <div class="card p-5">
      <h2 class="font-semibold text-gray-900 mb-4">Ganti Password</h2>
      <form @submit.prevent="changePassword" class="space-y-3 max-w-sm">
        <div><label class="label">Password Lama</label><input v-model="pwForm.old_password" type="password" class="input" required /></div>
        <div><label class="label">Password Baru</label><input v-model="pwForm.new_password" type="password" class="input" required minlength="6" /></div>
        <button type="submit" class="btn-primary">Ganti Password</button>
      </form>
    </div>

    <!-- Logout -->
    <div class="card p-5">
      <button @click="auth.logout()" class="btn-danger">Keluar dari Akun</button>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAppSettingsStore } from '@/stores/appSettings'
import api from '@/composables/useApi'
import { useToast } from 'vue-toastification'
import { usePrinter } from '@/composables/usePrinter'

const auth = useAuthStore()
const appSettings = useAppSettingsStore()
const toast = useToast()
const printer = usePrinter()
const lastPrinterName = ref(printer.getLastPrinterName())

const currentSettings = ref(null)
const latestInsight = ref(null)
const savingAi = ref(false)
const generating = ref(false)

const aiForm = reactive({ ai_provider: 'openai', openai_api_key: '', gemini_api_key: '', groq_api_key: '', ollama_host: '', ai_model: 'gpt-4o-mini' })
const bizForm = reactive({ business_type: 'cafe', business_description: '', target_daily_revenue: 0 })
const waForm = reactive({ whatsapp_notify: false, waha_url: 'http://localhost:3000', waha_api_key: '', waha_session: 'default', whatsapp_group_id: '', whatsapp_schedule_hour: 21, whatsapp_schedule_minute: 30 })
const testingWa = ref(false)
const pwForm = reactive({ old_password: '', new_password: '' })
const divForm = reactive({ divisions: ['Bar', 'Kitchen', 'Titipan'], watchlist_enabled: true })
const newDivision = ref('')

const providers = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'gemini', label: 'Gemini (Google)' },
  { value: 'groq', label: 'Groq (Gratis!)' },
  { value: 'ollama', label: 'Ollama (Lokal)' },
]

const roleColor = computed(() => ({ superadmin: 'blue', admin: 'green', manager: 'yellow', kasir: 'gray', inventory: 'blue' }[auth.user?.role] || 'gray'))
const hasKey = computed(() => currentSettings.value?.has_openai_key || currentSettings.value?.has_gemini_key || currentSettings.value?.has_groq_key || currentSettings.value?.ollama_host)

const baseUrl = window.location.origin
const endpoints = [
  { label: 'Tool Definitions (OpenAI format)', url: `${baseUrl}/api/v1/ai/tools` },
  { label: 'Execute Tool', url: `${baseUrl}/api/v1/ai/execute` },
  { label: 'Business Context for Agent', url: `${baseUrl}/api/v1/ai/context` },
  { label: 'Weekly Insights', url: `${baseUrl}/api/v1/settings/insights/latest` },
  { label: 'API Docs (Swagger)', url: `${baseUrl}/docs` },
]

const formatRp = (n) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(n || 0)

async function loadSettings() {
  const [sRes, iRes] = await Promise.all([
    api.get('/api/v1/settings/'),
    api.get('/api/v1/settings/insights/latest').catch(() => ({ data: null })),
  ])
  currentSettings.value = sRes.data
  latestInsight.value = iRes.data?.insight_text ? iRes.data : null

  // Pre-fill forms (jangan tampilkan key asli)
  aiForm.ai_provider = sRes.data.ai_provider || 'openai'
  aiForm.ai_model = sRes.data.ai_model || 'gpt-4o-mini'
  aiForm.ollama_host = sRes.data.ollama_host || ''
  bizForm.business_type = sRes.data.business_type || 'cafe'
  bizForm.business_description = sRes.data.business_description || ''
  bizForm.target_daily_revenue = sRes.data.target_daily_revenue || 0

  // Divisions & Watchlist
  divForm.divisions = sRes.data.divisions || ['Bar', 'Kitchen', 'Titipan']
  divForm.watchlist_enabled = sRes.data.watchlist_enabled ?? true

  // WA settings
  waForm.whatsapp_notify = sRes.data.whatsapp_notify || false
  waForm.waha_url = sRes.data.waha_url || 'http://localhost:3000'
  waForm.waha_session = sRes.data.waha_session || 'default'
  waForm.whatsapp_group_id = sRes.data.whatsapp_group_id || ''
  waForm.whatsapp_schedule_hour = sRes.data.whatsapp_schedule_hour ?? 21
  waForm.whatsapp_schedule_minute = sRes.data.whatsapp_schedule_minute ?? 30
}

async function saveAiSettings() {
  savingAi.value = true
  try {
    const payload = { ai_provider: aiForm.ai_provider, ai_model: aiForm.ai_model }
    if (aiForm.openai_api_key) payload.openai_api_key = aiForm.openai_api_key
    if (aiForm.gemini_api_key) payload.gemini_api_key = aiForm.gemini_api_key
    if (aiForm.groq_api_key) payload.groq_api_key = aiForm.groq_api_key
    if (aiForm.ollama_host) payload.ollama_host = aiForm.ollama_host

    await api.patch('/api/v1/settings/', payload)
    toast.success('AI settings disimpan!')
    aiForm.openai_api_key = ''
    aiForm.gemini_api_key = ''
    aiForm.groq_api_key = ''
    loadSettings()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal simpan')
  } finally {
    savingAi.value = false
  }
}

async function saveWaSettings() {
  try {
    const payload = {
      whatsapp_notify: waForm.whatsapp_notify,
      waha_url: waForm.waha_url,
      waha_session: waForm.waha_session,
      whatsapp_group_id: waForm.whatsapp_group_id,
      whatsapp_schedule_hour: waForm.whatsapp_schedule_hour,
      whatsapp_schedule_minute: waForm.whatsapp_schedule_minute,
    }
    if (waForm.waha_api_key) payload.waha_api_key = waForm.waha_api_key
    await api.patch('/api/v1/settings/', payload)
    toast.success('WhatsApp settings disimpan!')
    waForm.waha_api_key = ''
    loadSettings()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal simpan')
  }
}

async function testWhatsapp() {
  testingWa.value = true
  try {
    await api.post('/api/v1/settings/whatsapp/test')
    toast.success('Pesan test terkirim! Cek group WA.')
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal kirim test')
  } finally {
    testingWa.value = false
  }
}

async function saveBizSettings() {
  await api.patch('/api/v1/settings/', bizForm)
  toast.success('Profil bisnis disimpan!')
}

async function generateInsight() {
  generating.value = true
  try {
    const res = await api.post('/api/v1/settings/insights/generate')
    toast.success('Generating... Refresh dalam 10-30 detik!')
    // Poll hasil setelah 15 detik
    setTimeout(async () => {
      await loadSettings()
      generating.value = false
    }, 15000)
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal generate insight')
    generating.value = false
  }
}

function addDivision() {
  const d = newDivision.value.trim()
  if (!d) return
  if (divForm.divisions.includes(d)) { toast.error('Divisi sudah ada'); return }
  divForm.divisions.push(d)
  newDivision.value = ''
}

async function saveDivSettings() {
  try {
    await api.patch('/api/v1/settings/', { divisions: divForm.divisions, watchlist_enabled: divForm.watchlist_enabled })
    toast.success('Divisi & Watchlist disimpan!')
    // Reset appSettings so sidebar re-fetches watchlist_enabled state
    appSettings.reset()
    appSettings.load()
    loadSettings()
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal simpan')
  }
}

async function handleConnectPrinter() {
  try {
    await printer.connectPrinter()
    lastPrinterName.value = printer.getLastPrinterName()
    toast.success('Printer terhubung!')
  } catch (e) {
    toast.error('Gagal menghubungkan printer: ' + (e.message || 'Unknown'))
  }
}

async function handleTestPrint() {
  try {
    await printer.testPrint()
    toast.success('Test print terkirim!')
  } catch (e) {
    toast.error('Gagal test print: ' + (e.message || 'Unknown'))
  }
}

async function changePassword() {
  try {
    await api.post('/api/v1/auth/change-password', pwForm)
    toast.success('Password berhasil diubah')
    pwForm.old_password = ''
    pwForm.new_password = ''
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Gagal ganti password')
  }
}

function copy(text) {
  navigator.clipboard.writeText(text)
  toast.success('Disalin!')
}

onMounted(loadSettings)
</script>
