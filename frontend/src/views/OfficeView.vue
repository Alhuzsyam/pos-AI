<template>
  <div class="p-5 max-w-5xl mx-auto">
    <!-- Header -->
    <div class="flex items-center gap-3 mb-4">
      <h1 class="text-xl font-bold text-gray-900">🎮 Live Office</h1>
      <span class="flex items-center gap-1.5 text-xs text-green-600 font-medium">
        <span class="w-2 h-2 bg-green-500 rounded-full animate-pulse inline-block"></span>
        Live
      </span>
      <div class="ml-auto flex gap-2">
        <button @click="showScore = true" class="btn-primary btn-sm text-xs">🏆 Lihat Skor</button>
        <button @click="showNames = !showNames" class="btn-secondary btn-sm text-xs">✏️ Edit Nama</button>
      </div>
    </div>

    <!-- Name + settings editor -->
    <div v-if="showNames" class="card p-4 mb-4 flex gap-4 flex-wrap items-end">
      <div v-for="role in ['bar', 'kitchen', 'waiter']" :key="role">
        <label class="label capitalize">{{ role }}</label>
        <input v-model="names[role]" class="input text-sm w-32" @input="saveNames" />
      </div>
      <div>
        <label class="label">Maks Order (capek 😵)</label>
        <input v-model.number="maxOrders" type="number" min="1" max="100" class="input text-sm w-24" @change="saveSettings" />
      </div>
      <p class="text-xs text-gray-400 self-end pb-1">Tersimpan otomatis</p>
    </div>

    <!-- Stats -->
    <div class="flex gap-3 mb-4">
      <div class="card px-4 py-2.5 flex items-center gap-2">
        <span class="text-lg">🍹</span>
        <div>
          <p class="text-xs text-gray-400">Bar</p>
          <p class="font-bold text-blue-600 text-lg leading-none">{{ barOrders.length }}</p>
        </div>
      </div>
      <div class="card px-4 py-2.5 flex items-center gap-2">
        <span class="text-lg">🍳</span>
        <div>
          <p class="text-xs text-gray-400">Kitchen</p>
          <p class="font-bold text-orange-500 text-lg leading-none">{{ kitchenOrders.length }}</p>
        </div>
      </div>
      <div class="card px-4 py-2.5 flex items-center gap-2">
        <span class="text-lg">🚶</span>
        <div>
          <p class="text-xs text-gray-400">Delivery</p>
          <p class="font-bold text-green-600 text-lg leading-none">{{ deliveryOrders.length }}</p>
        </div>
      </div>
      <div class="ml-auto card px-4 py-2.5 text-xs text-gray-400 flex items-center gap-1">
        <span>Refresh tiap 3 detik</span>
      </div>
    </div>

    <!-- Office -->
    <div class="office-wrapper" ref="officeRef">
      <!-- Room: BAR -->
      <div class="room" :style="roomStyle('#7C3D0F', '#B5651D')">
        <div class="room-label">🍹 Bar</div>
        <!-- Furniture: counter -->
        <div class="furniture counter-bar"></div>
        <!-- Bottles decoration -->
        <div class="bottles">
          <div class="bottle" style="background:#3B82F6;height:14px;width:6px"></div>
          <div class="bottle" style="background:#EF4444;height:12px;width:6px"></div>
          <div class="bottle" style="background:#10B981;height:16px;width:6px"></div>
          <div class="bottle" style="background:#F59E0B;height:10px;width:6px"></div>
        </div>
        <!-- Floor -->
        <div class="floor" style="background:#92400E"></div>
        <!-- Character -->
        <div class="char-wrapper">
          <div v-if="barOrders.length > maxOrders" class="overload-badge">😵 {{ barOrders.length }} order!</div>
          <SpeechBubble :tasks="barOrders" :busy="barOrders.length > 0" />
          <PixelChar type="bartender" :busy="barOrders.length > 0" />
          <div class="char-name">{{ names.bar }}</div>
        </div>
      </div>

      <!-- Room: KITCHEN -->
      <div class="room" :style="roomStyle('#374151', '#4B5563')">
        <div class="room-label">🍳 Kitchen</div>
        <!-- Stove -->
        <div class="furniture stove"></div>
        <div class="stove-burners">
          <div class="burner" :class="{ hot: kitchenOrders.length > 0 }"></div>
          <div class="burner" :class="{ hot: kitchenOrders.length > 1 }"></div>
        </div>
        <!-- Counter -->
        <div class="furniture counter-kitchen"></div>
        <!-- Floor -->
        <div class="floor" style="background:#1F2937"></div>
        <!-- Character -->
        <div class="char-wrapper">
          <div v-if="kitchenOrders.length > maxOrders" class="overload-badge">😵 {{ kitchenOrders.length }} order!</div>
          <SpeechBubble :tasks="kitchenOrders" :busy="kitchenOrders.length > 0" />
          <PixelChar type="chef" :busy="kitchenOrders.length > 0" />
          <div class="char-name">{{ names.kitchen }}</div>
        </div>
      </div>

      <!-- Room: MEJA PELANGGAN -->
      <div class="room" :style="roomStyle('#14532D', '#166534')">
        <div class="room-label">🪑 Meja Pelanggan</div>
        <!-- Tables -->
        <div class="customer-tables">
          <div class="cust-table">
            <div class="table-top"></div>
            <div class="table-chairs">
              <div class="chair"></div><div class="chair"></div>
            </div>
          </div>
          <div class="cust-table">
            <div class="table-top"></div>
            <div class="table-chairs">
              <div class="chair"></div><div class="chair"></div>
            </div>
          </div>
        </div>
        <!-- Floor -->
        <div class="floor" style="background:#052e16"></div>
        <!-- Static customer ghost chars -->
        <div class="customers">
          <div class="ghost-customer">👤</div>
          <div class="ghost-customer">👤</div>
        </div>
      </div>

      <!-- Floating score popups -->
      <div v-for="fp in floatingPoints" :key="fp.id"
           class="float-point" :class="`float-${fp.station}`">
        {{ fp.text }}
      </div>

      <!-- Cat — random wanderer -->
      <div class="cat-layer" :class="catAnimClass">
        <div class="cat-char" :style="{ transform: catFacing === 'left' ? 'scaleX(-1)' : 'scaleX(1)' }">
          {{ catMood }}
        </div>
      </div>

      <!-- Waiter — absolute, animates across all rooms -->
      <div class="waiter-layer" :class="waiterAnimClass">
        <div class="char-wrapper waiter-char-wrap">
          <div v-if="deliveryOrders.length > maxOrders" class="overload-badge">😵 {{ deliveryOrders.length }} antar!</div>
          <WaiterBubble :carrying="waiterCarrying" :pos="waiterPos" />
          <PixelChar type="waiter" :busy="deliveryOrders.length > 0" :facing="waiterFacing" />
          <div class="char-name waiter-name-tag">{{ names.waiter }}</div>
        </div>
      </div>
    </div>

    <!-- Legend -->
    <div class="mt-3 flex gap-4 text-xs text-gray-500">
      <span>💬 Bubble = item sedang dikerjakan</span>
      <span>💤 Tidur = tidak ada order</span>
      <span>🚶 Waiter jalan = ada pesanan siap antar</span>
      <span class="ml-auto">Maks capek: <b>{{ maxOrders }}</b> order</span>
    </div>

    <!-- Score Modal -->
    <div v-if="showScore" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-sm p-6">
        <div class="flex items-center justify-between mb-5">
          <h2 class="font-bold text-lg text-gray-900">🏆 Papan Skor</h2>
          <div class="flex gap-2">
            <button @click="resetScores" class="btn-secondary btn-sm text-xs">Reset</button>
            <button @click="showScore = false" class="text-gray-400 hover:text-gray-600 text-xl leading-none">✕</button>
          </div>
        </div>

        <!-- Podium -->
        <div class="space-y-3 mb-5">
          <div v-for="(entry, i) in scoreboard" :key="entry.station"
               class="flex items-center gap-3 p-3 rounded-xl"
               :class="i === 0 ? 'bg-yellow-50 border-2 border-yellow-200' : i === 1 ? 'bg-gray-50 border border-gray-200' : 'bg-orange-50 border border-orange-200'">
            <span class="text-2xl">{{ ['🥇','🥈','🥉'][i] }}</span>
            <div class="flex-1">
              <p class="font-bold text-gray-900 text-sm">{{ names[entry.station] }}</p>
              <div class="w-full bg-gray-200 rounded-full h-2 mt-1">
                <div class="h-2 rounded-full transition-all duration-500"
                     :class="i === 0 ? 'bg-yellow-400' : i === 1 ? 'bg-gray-400' : 'bg-orange-400'"
                     :style="{ width: maxScore > 0 ? (entry.score / maxScore * 100) + '%' : '0%' }"></div>
              </div>
            </div>
            <div class="text-right">
              <p class="font-bold text-lg" :class="i === 0 ? 'text-yellow-600' : 'text-gray-600'">{{ entry.score }}</p>
              <p class="text-xs text-gray-400">poin</p>
            </div>
          </div>
        </div>

        <!-- Stats -->
        <div class="bg-gray-50 rounded-xl p-3 text-xs text-gray-600 space-y-1">
          <p class="font-semibold text-gray-700 mb-2">📊 Statistik Sesi</p>
          <div v-for="entry in scoreboard" :key="entry.station" class="flex justify-between">
            <span>{{ names[entry.station] }}</span>
            <span>
              {{ entry.count }} item · rata2 <b>{{ entry.avgTime }}s</b>
            </span>
          </div>
          <p v-if="scoreboard.every(e => e.score === 0)" class="text-gray-400 italic text-center pt-2">
            Belum ada skor. Tunggu order diproses...
          </p>
        </div>

        <p class="text-xs text-gray-400 text-center mt-3">Skor = 1000 ÷ waktu proses (detik). Makin cepat makin tinggi!</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, defineComponent, h } from 'vue'
import api from '@/composables/useApi'

// =============================================
// Pixel Character Component
// =============================================
const PIXEL_SIZE = 4

const PALETTES = {
  bartender: { H:'#4A2C0A', S:'#FDBCB4', B:'#1D4ED8', W:'#FFFFFF', K:'#111827', '.':null },
  chef:      { H:'#3D2B1F', S:'#FDBCB4', W:'#F9FAFB', K:'#111827', R:'#EF4444', '.':null },
  waiter:    { H:'#1C1917', S:'#FDBCB4', W:'#FFFFFF', K:'#0F172A', G:'#9CA3AF', T:'#D97706', '.':null },
}

const GRIDS = {
  bartender: [
    '..HHHH..',
    '.HHHHH..',
    '.SSSSSS.',
    '.S.SS.S.',
    '..SSSS..',
    '..BBBB..',
    'WWBBBBWW',
    'BBBBBBBB',
    '.BB..BB.',
    '.KK..KK.',
    '.KK..KK.',
    'KK....KK',
  ],
  chef: [
    '..WWWW..',
    '.WWWWWW.',
    '.SSSSSS.',
    '.S.SS.S.',
    '..SSSS..',
    '.WWWWWW.',
    'WWWWWWWW',
    'WWWWWWWW',
    '.WW..WW.',
    '.KK..KK.',
    '.KK..KK.',
    'KK....KK',
  ],
  waiter: [
    '..HHHH..',
    '.HHHHHH.',
    '.SSSSSS.',
    '.S.SS.S.',
    '..SSSS..',
    '..WTWW..',
    'KKKWWKKK',
    'KKKWWKKK',
    '.KK..KK.',
    '.KK..KK.',
    '.KK..KK.',
    'KK....KK',
  ],
}

const PixelChar = defineComponent({
  props: { type: String, busy: Boolean, facing: { type: String, default: 'right' } },
  setup(props) {
    return () => {
      const palette = PALETTES[props.type]
      const grid = GRIDS[props.type]
      const s = PIXEL_SIZE
      const anim = props.busy ? 'bob-fast' : 'bob-slow'
      const flip = props.facing === 'left' ? 'scaleX(-1)' : 'scaleX(1)'
      return h('div', {
        style: { display:'inline-block', imageRendering:'pixelated', animation:`${anim} 0.6s steps(1) infinite`, transform: flip }
      }, grid.map((row, y) =>
        h('div', { key: y, style: { display:'flex' } },
          row.split('').map((px, x) =>
            h('div', { key: x, style: { width:`${s}px`, height:`${s}px`, background: palette[px] || 'transparent' } })
          )
        )
      ))
    }
  }
})

// =============================================
// Speech Bubble Component
// =============================================
const SpeechBubble = defineComponent({
  props: { tasks: Array, busy: Boolean, bubbleSide: { type: String, default: 'right' } },
  setup(props) {
    return () => {
      if (!props.tasks || props.tasks.length === 0) {
        return h('div', { class: 'speech-bubble sleep-bubble' }, '💤 Santai')
      }
      const first = props.tasks[0]
      const label = first.items?.[0]?.menu_name || first.customer_name || '...'
      const short = label.length > 18 ? label.slice(0, 16) + '…' : label
      const extra = props.tasks.length > 1 ? ` +${props.tasks.length - 1}` : ''
      return h('div', { class: 'speech-bubble work-bubble' }, [
        h('span', { class: 'bubble-icon' }, '⚡'),
        ` ${short}${extra}`
      ])
    }
  }
})

// =============================================
// Waiter Bubble Component
// =============================================
const WaiterBubble = defineComponent({
  props: { carrying: Object, pos: String },
  setup(props) {
    return () => {
      if (!props.carrying) {
        return h('div', { class: 'speech-bubble sleep-bubble' }, '💤 Standby')
      }
      const isPickingUp = props.pos !== 'customer'
      const label = props.carrying.label || '...'
      const short = label.length > 14 ? label.slice(0, 12) + '…' : label
      const table = props.carrying.table ? ` →${props.carrying.table}` : ''
      const icon = isPickingUp ? '🤲' : '🏃'
      const text = isPickingUp ? `Ambil: ${short}` : `Antar: ${short}${table}`
      return h('div', { class: `speech-bubble ${isPickingUp ? 'pickup-bubble' : 'deliver-bubble'}` }, [
        h('span', {}, icon), ` ${text}`
      ])
    }
  }
})

// =============================================
// State
// =============================================
const showNames = ref(false)
const showScore = ref(false)
const names = ref({ bar: 'Bartender', kitchen: 'Chef Dapur', waiter: 'Waiter' })
const maxOrders = ref(10)
const queue = ref([])
let pollTimer = null

// =============================================
// Scoring Engine
// =============================================
// Tracks when items first seen as PENDING / PREPARED
const itemTimestamps = {} // { itemId: { time, station } }
const scoreData = ref({
  bar:     { score: 0, count: 0, totalTime: 0 },
  kitchen: { score: 0, count: 0, totalTime: 0 },
  waiter:  { score: 0, count: 0, totalTime: 0 },
})
const floatingPoints = ref([])

const scoreboard = computed(() => {
  return ['bar', 'kitchen', 'waiter']
    .map(s => ({
      station: s,
      score: scoreData.value[s].score,
      count: scoreData.value[s].count,
      avgTime: scoreData.value[s].count > 0
        ? Math.round(scoreData.value[s].totalTime / scoreData.value[s].count)
        : 0,
    }))
    .sort((a, b) => b.score - a.score)
})

const maxScore = computed(() => Math.max(...scoreboard.value.map(e => e.score), 1))

function spawnFloat(station, points) {
  const id = Date.now() + Math.random()
  floatingPoints.value.push({ id, station, text: `+${points}` })
  setTimeout(() => {
    floatingPoints.value = floatingPoints.value.filter(f => f.id !== id)
  }, 1400)
}

function trackScores(newQueue) {
  const now = Date.now()
  for (const order of newQueue) {
    for (const item of order.items || []) {
      const key = `item_${item.id}`
      const wkey = `wait_${item.id}`

      if (item.status === 'PENDING') {
        if (!itemTimestamps[key]) {
          const station = item.division?.toLowerCase() === 'bar' ? 'bar' : 'kitchen'
          itemTimestamps[key] = { time: now, station }
        }
      } else if (item.status === 'PREPARED') {
        // Bar/Kitchen completed
        if (itemTimestamps[key]) {
          const elapsed = Math.max((now - itemTimestamps[key].time) / 1000, 1)
          const station = itemTimestamps[key].station
          const pts = Math.max(5, Math.round(1000 / elapsed))
          scoreData.value[station].score += pts
          scoreData.value[station].count++
          scoreData.value[station].totalTime += elapsed
          spawnFloat(station, pts)
          delete itemTimestamps[key]
        }
        // Start waiter timer
        if (!itemTimestamps[wkey]) {
          itemTimestamps[wkey] = { time: now, station: 'waiter' }
        }
      } else if (item.status === 'DELIVERED' || item.status === 'SERVED') {
        // Waiter completed delivery
        if (itemTimestamps[wkey]) {
          const elapsed = Math.max((now - itemTimestamps[wkey].time) / 1000, 1)
          const pts = Math.max(5, Math.round(1000 / elapsed))
          scoreData.value.waiter.score += pts
          scoreData.value.waiter.count++
          scoreData.value.waiter.totalTime += elapsed
          spawnFloat('waiter', pts)
          delete itemTimestamps[wkey]
        }
      }
    }
  }
}

function resetScores() {
  scoreData.value = {
    bar:     { score: 0, count: 0, totalTime: 0 },
    kitchen: { score: 0, count: 0, totalTime: 0 },
    waiter:  { score: 0, count: 0, totalTime: 0 },
  }
  Object.keys(itemTimestamps).forEach(k => delete itemTimestamps[k])
}

// Waiter animation state
const waiterPos = ref('customer') // 'bar' | 'kitchen' | 'customer'
const waiterFacing = ref('left')
const waiterStep = ref(0)
const waiterCarrying = ref(null) // { menu_name, customer_name, table_number }
let waiterTimer = null

function saveNames() {
  localStorage.setItem('office_names', JSON.stringify(names.value))
}

function saveSettings() {
  localStorage.setItem('office_max_orders', String(maxOrders.value))
}

function loadNames() {
  try {
    const saved = localStorage.getItem('office_names')
    if (saved) names.value = { ...names.value, ...JSON.parse(saved) }
    const savedMax = localStorage.getItem('office_max_orders')
    if (savedMax) maxOrders.value = parseInt(savedMax, 10) || 10
  } catch {}
}

// =============================================
// Queue data
// =============================================
const barOrders = computed(() => queue.value.filter(o =>
  o.items?.some(i => i.status === 'PENDING' && i.division?.toLowerCase() === 'bar')
))

const kitchenOrders = computed(() => queue.value.filter(o =>
  o.items?.some(i => i.status === 'PENDING' && i.division?.toLowerCase() === 'kitchen')
))

const deliveryOrders = computed(() => queue.value.filter(o =>
  o.items?.some(i => i.status === 'PREPARED')
))

async function loadQueue() {
  try {
    const res = await api.get('/api/v1/queue/')
    trackScores(res.data)
    queue.value = res.data
  } catch {}
}

// =============================================
// Waiter animation logic
// =============================================
const waiterAnimClass = computed(() => `waiter-pos-${waiterPos.value}`)

// Posisi numerik buat hitung arah hadap
const ROOM_ORDER = { bar: 0, kitchen: 1, customer: 2 }

/**
 * Build route dari delivery orders secara berurutan:
 * Tiap order → cek item PREPARED di divisi apa → waiter ke sana dulu → lalu ke customer
 * Contoh: [bar, customer, kitchen, customer, bar, customer]
 */
function buildWaiterRoute() {
  const route = []
  for (const order of deliveryOrders.value) {
    const prepared = order.items?.filter(i => i.status === 'PREPARED') || []
    // Kelompokkan per divisi (preserving order)
    const seen = new Set()
    for (const item of prepared) {
      const div = item.division?.toLowerCase() === 'bar' ? 'bar' : 'kitchen'
      if (!seen.has(div)) {
        seen.add(div)
        route.push({
          room: div,
          label: item.menu_name,
          table: order.table_number,
          customer: order.customer_name,
        })
        route.push({
          room: 'customer',
          label: item.menu_name,
          table: order.table_number,
          customer: order.customer_name,
        })
      }
    }
  }
  return route
}

function tickWaiter() {
  const route = buildWaiterRoute()

  if (route.length === 0) {
    waiterPos.value = 'customer'
    waiterFacing.value = 'left'
    waiterCarrying.value = null
    return
  }

  // Maju satu langkah di route, wrap-around
  waiterStep.value = (waiterStep.value + 1) % route.length
  const next = route[waiterStep.value]

  // Tentukan arah hadap berdasarkan posisi sekarang vs berikutnya
  const currentOrder = ROOM_ORDER[waiterPos.value] ?? 2
  const nextOrder = ROOM_ORDER[next.room] ?? 2
  waiterFacing.value = nextOrder > currentOrder ? 'right' : 'left'

  waiterPos.value = next.room
  waiterCarrying.value = next
}

// =============================================
// Cat — random wanderer
// =============================================
const ROOMS = ['bar', 'kitchen', 'customer']
const catPos = ref('kitchen')
const catFacing = ref('right')
const catMood = ref('😺') // changes randomly
const CAT_MOODS = ['😺', '😸', '🐱', '😻', '😼']
let catTimer = null

function moveCat() {
  const current = ROOM_ORDER[catPos.value] ?? 1
  const options = ROOMS.filter(r => r !== catPos.value)
  const next = options[Math.floor(Math.random() * options.length)]
  catFacing.value = ROOM_ORDER[next] > current ? 'right' : 'left'
  catPos.value = next
  if (Math.random() < 0.3) {
    catMood.value = CAT_MOODS[Math.floor(Math.random() * CAT_MOODS.length)]
  }
}

const catAnimClass = computed(() => `cat-pos-${catPos.value}`)

// =============================================
// Room style helper
// =============================================
function roomStyle(wall, accent) {
  return { '--wall': wall, '--accent': accent }
}

// =============================================
// Lifecycle
// =============================================
onMounted(() => {
  loadNames()
  loadQueue()
  pollTimer = setInterval(loadQueue, 3000)
  waiterTimer = setInterval(tickWaiter, 2500)
  catTimer = setInterval(moveCat, 4500 + Math.random() * 2000)
})

onUnmounted(() => {
  clearInterval(pollTimer)
  clearInterval(waiterTimer)
  clearInterval(catTimer)
})
</script>

<style scoped>
/* ==============================
   Office container
   ============================== */
.office-wrapper {
  position: relative;
  display: flex;
  border: 3px solid #1f2937;
  border-radius: 8px;
  overflow: hidden;
  height: 360px;
  image-rendering: pixelated;
}

/* ==============================
   Rooms
   ============================== */
.room {
  flex: 1;
  position: relative;
  background: var(--wall);
  border-right: 2px solid rgba(0,0,0,0.3);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  padding-bottom: 48px;
}
.room:last-child { border-right: none; }

.room-label {
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 11px;
  font-weight: 700;
  color: rgba(255,255,255,0.85);
  background: rgba(0,0,0,0.3);
  padding: 2px 8px;
  border-radius: 4px;
  white-space: nowrap;
  letter-spacing: 0.5px;
}

.floor {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 44px;
  border-top: 2px solid rgba(0,0,0,0.2);
}

/* ==============================
   Furniture: Bar
   ============================== */
.counter-bar {
  position: absolute;
  bottom: 44px;
  left: 10%;
  right: 10%;
  height: 28px;
  background: #92400E;
  border: 2px solid #78350F;
  border-radius: 4px 4px 0 0;
  z-index: 1;
}

.bottles {
  position: absolute;
  bottom: 72px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 4px;
  align-items: flex-end;
}
.bottle {
  border-radius: 2px 2px 0 0;
  border: 1px solid rgba(0,0,0,0.3);
}

/* ==============================
   Furniture: Kitchen
   ============================== */
.stove {
  position: absolute;
  bottom: 72px;
  left: 20%;
  width: 60%;
  height: 32px;
  background: #374151;
  border: 2px solid #111827;
  border-radius: 4px;
}

.stove-burners {
  position: absolute;
  bottom: 96px;
  left: 28%;
  display: flex;
  gap: 16px;
}
.burner {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #374151;
  border: 2px solid #6B7280;
  transition: all 0.5s;
}
.burner.hot {
  background: #EF4444;
  border-color: #F97316;
  box-shadow: 0 0 6px #F97316;
  animation: flame 0.4s ease-in-out infinite alternate;
}
@keyframes flame {
  from { box-shadow: 0 0 4px #F97316; }
  to   { box-shadow: 0 0 10px #EF4444; }
}

.counter-kitchen {
  position: absolute;
  bottom: 44px;
  left: 8%;
  right: 8%;
  height: 28px;
  background: #6B7280;
  border: 2px solid #374151;
  border-radius: 4px 4px 0 0;
}

/* ==============================
   Furniture: Customer Area
   ============================== */
.customer-tables {
  position: absolute;
  bottom: 60px;
  display: flex;
  gap: 20px;
  left: 50%;
  transform: translateX(-50%);
}
.cust-table { display: flex; flex-direction: column; align-items: center; gap: 3px; }
.table-top {
  width: 52px;
  height: 12px;
  background: #A16207;
  border: 2px solid #713F12;
  border-radius: 3px;
}
.table-chairs { display: flex; gap: 8px; }
.chair {
  width: 14px;
  height: 12px;
  background: #92400E;
  border: 1px solid #451A03;
  border-radius: 2px;
}

.customers {
  position: absolute;
  bottom: 50px;
  display: flex;
  gap: 30px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 18px;
  opacity: 0.5;
}
.ghost-customer { animation: bob-slow 1.2s ease-in-out infinite; }

/* ==============================
   Character wrapper
   ============================== */
.char-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 5;
}

.char-name {
  font-size: 10px;
  font-weight: 700;
  color: white;
  background: rgba(0,0,0,0.5);
  padding: 1px 6px;
  border-radius: 3px;
  margin-top: 3px;
  white-space: nowrap;
}

/* ==============================
   Speech Bubbles
   ============================== */
:deep(.speech-bubble) {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 6px;
  white-space: nowrap;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  pointer-events: none;
  z-index: 10;
  &::after {
    content: '';
    position: absolute;
    bottom: -5px;
    left: 50%;
    transform: translateX(-50%);
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
  }
}

:deep(.sleep-bubble) {
  background: rgba(30,30,30,0.75);
  color: #9CA3AF;
  &::after { border-top: 5px solid rgba(30,30,30,0.75); }
}

:deep(.work-bubble) {
  background: #FEF9C3;
  color: #713F12;
  border: 1px solid #FDE68A;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  &::after { border-top: 5px solid #FEF9C3; }
}

:deep(.pickup-bubble) {
  background: #DBEAFE;
  color: #1E40AF;
  border: 1px solid #BFDBFE;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  &::after { border-top: 5px solid #DBEAFE; }
}

:deep(.deliver-bubble) {
  background: #D1FAE5;
  color: #065F46;
  border: 1px solid #A7F3D0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  animation: deliver-pop 0.3s ease;
  &::after { border-top: 5px solid #D1FAE5; }
}

@keyframes deliver-pop {
  from { transform: translateX(-50%) scale(0.8); opacity: 0; }
  to   { transform: translateX(-50%) scale(1);   opacity: 1; }
}

/* Overload badge */
.overload-badge {
  position: absolute;
  bottom: calc(100% + 52px);
  left: 50%;
  transform: translateX(-50%);
  font-size: 11px;
  font-weight: 800;
  color: #fff;
  background: #DC2626;
  border: 2px solid #7F1D1D;
  padding: 3px 8px;
  border-radius: 6px;
  white-space: nowrap;
  z-index: 15;
  animation: overload-shake 0.4s ease-in-out infinite;
  box-shadow: 0 0 8px rgba(220,38,38,0.6);
}
@keyframes overload-shake {
  0%,100% { transform: translateX(-50%) rotate(-2deg); }
  50%      { transform: translateX(-50%) rotate(2deg); }
}

:deep(.bubble-icon) {
  animation: pulse-icon 0.5s ease-in-out infinite alternate;
}
@keyframes pulse-icon {
  from { opacity: 0.7; }
  to   { opacity: 1; }
}

/* ==============================
   Waiter Layer
   ============================== */
.waiter-layer {
  position: absolute;
  bottom: 48px;
  z-index: 8;
  transition: left 1.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.waiter-char-wrap { align-items: center; }
.waiter-name-tag { background: rgba(0,0,0,0.6) !important; }

/* Position: bar (left room center) */
.waiter-pos-bar {
  left: calc(16.66% - 16px);
}
/* Position: kitchen (middle room center) */
.waiter-pos-kitchen {
  left: calc(50% - 16px);
}
/* Position: customer (right room center) */
.waiter-pos-customer {
  left: calc(83.33% - 16px);
}

/* ==============================
   Pixel animations
   ============================== */
@keyframes bob-slow {
  0%, 100% { transform: translateY(0px); }
  50%       { transform: translateY(-3px); }
}
@keyframes bob-fast {
  0%, 100% { transform: translateY(0px); }
  25%       { transform: translateY(-2px); }
  75%       { transform: translateY(-4px); }
}

/* ==============================
   Floating score popups
   ============================== */
.float-point {
  position: absolute;
  bottom: 120px;
  font-size: 13px;
  font-weight: 800;
  color: #FACC15;
  text-shadow: 0 1px 3px rgba(0,0,0,0.7);
  pointer-events: none;
  z-index: 20;
  animation: float-up 1.4s ease-out forwards;
  white-space: nowrap;
}
.float-bar     { left: calc(16.66% - 16px); }
.float-kitchen { left: calc(50% - 16px); }
.float-waiter  { left: calc(83.33% - 16px); }

@keyframes float-up {
  0%   { transform: translateY(0px);   opacity: 1; }
  80%  { transform: translateY(-40px); opacity: 0.8; }
  100% { transform: translateY(-60px); opacity: 0; }
}

/* ==============================
   Cat wanderer
   ============================== */
.cat-layer {
  position: absolute;
  bottom: 46px;
  z-index: 7;
  transition: left 1.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.cat-char {
  font-size: 20px;
  display: inline-block;
  animation: cat-walk 0.5s steps(2) infinite;
  filter: drop-shadow(0 2px 2px rgba(0,0,0,0.5));
  cursor: default;
  user-select: none;
}

/* slightly offset from waiter so they don't overlap perfectly */
.cat-pos-bar     { left: calc(16.66% - 36px); }
.cat-pos-kitchen { left: calc(50% + 12px); }
.cat-pos-customer{ left: calc(83.33% + 8px); }

@keyframes cat-walk {
  0%   { transform: translateY(0px); }
  50%  { transform: translateY(-3px); }
  100% { transform: translateY(0px); }
}
</style>
