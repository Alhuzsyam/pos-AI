/**
 * Bluetooth Thermal Printer (ESC/POS) via Web Bluetooth API.
 * Service UUID: 000018f0-0000-1000-8000-00805f9b34fb
 * Characteristic UUID: 00002af1-0000-1000-8000-00805f9b34fb
 */
import { ref } from 'vue'

const SERVICE_UUID = '000018f0-0000-1000-8000-00805f9b34fb'
const CHAR_UUID = '00002af1-0000-1000-8000-00805f9b34fb'
const CHUNK_SIZE = 20

// Shared state across components
const pairedDevice = ref(null)
const printerStatus = ref('Disconnected')
const isConnecting = ref(false)
const isPrinting = ref(false)

// ESC/POS commands
const ESC = {
  INIT: '\x1B\x40',
  CENTER: '\x1B\x61\x01',
  LEFT: '\x1B\x61\x00',
  BOLD_ON: '\x1B\x45\x01',
  BOLD_OFF: '\x1B\x45\x00',
  FEED: '\x0A\x0A\x0A',
  LINE: '--------------------------------\n',
}

// Persist last printer name
function saveLastPrinter(name) {
  localStorage.setItem('posai_printer_name', name)
}
function getLastPrinterName() {
  return localStorage.getItem('posai_printer_name')
}

async function connectPrinter() {
  isConnecting.value = true
  try {
    const device = await navigator.bluetooth.requestDevice({
      filters: [{ services: [SERVICE_UUID] }],
      optionalServices: [SERVICE_UUID],
    })
    const server = await device.gatt.connect()
    pairedDevice.value = device
    printerStatus.value = 'Connected: ' + device.name
    saveLastPrinter(device.name)
    return device
  } catch (e) {
    console.error('Bluetooth connect error:', e)
    printerStatus.value = 'Failed'
    throw e
  } finally {
    isConnecting.value = false
  }
}

async function sendToPrinter(content) {
  if (!pairedDevice.value) throw new Error('Printer belum terhubung')
  isPrinting.value = true
  try {
    const server = await pairedDevice.value.gatt.connect()
    const service = await server.getPrimaryService(SERVICE_UUID)
    const characteristic = await service.getCharacteristic(CHAR_UUID)

    const encoder = new TextEncoder()
    const data = encoder.encode(content)

    // Send in chunks (BLE limit)
    for (let i = 0; i < data.length; i += CHUNK_SIZE) {
      await characteristic.writeValue(data.slice(i, i + CHUNK_SIZE))
    }
  } finally {
    isPrinting.value = false
  }
}

async function testPrint() {
  const content =
    ESC.INIT + ESC.CENTER +
    ESC.BOLD_ON + 'TEST PRINT BERHASIL\n' + ESC.BOLD_OFF +
    'POS-AI System\n' +
    ESC.LINE +
    'Printer siap digunakan\n' +
    ESC.FEED
  await sendToPrinter(content)
}

// ============ Receipt builders ============

function formatRpRaw(n) {
  return 'Rp' + (n || 0).toLocaleString('id-ID')
}

/**
 * Build POS sale receipt ESC/POS content.
 */
function buildSaleReceipt({ storeName, storeAddress, storePhone, transactionCode, date, cashier, customerName, tableNumber, items, totalAmount, discountAmount, finalAmount, paymentMethod }) {
  let c = ESC.INIT + ESC.CENTER
  c += ESC.BOLD_ON + (storeName || 'POS-AI') + '\n' + ESC.BOLD_OFF
  if (storeAddress) c += storeAddress + '\n'
  if (storePhone) c += storePhone + '\n'
  c += ESC.LINE + ESC.LEFT
  c += 'No  : ' + (transactionCode || '') + '\n'
  c += 'Tgl : ' + (date || new Date().toLocaleString('id-ID')) + '\n'
  if (cashier) c += 'Kasir: ' + cashier + '\n'
  if (customerName) c += 'Plg : ' + customerName + '\n'
  if (tableNumber) c += 'Meja: ' + tableNumber + '\n'
  c += ESC.LINE

  if (items) {
    items.forEach(i => {
      const name = i.menu_name || i.name
      const qty = i.quantity || i.qty
      const price = i.price_at_moment || i.price
      const sub = qty * price
      c += name + '\n'
      c += qty + ' x ' + formatRpRaw(price) + ' = ' + formatRpRaw(sub) + '\n'
    })
    c += ESC.LINE
  }

  c += 'Subtotal: ' + formatRpRaw(totalAmount) + '\n'
  if (discountAmount) c += 'Diskon  : -' + formatRpRaw(discountAmount) + '\n'
  c += ESC.BOLD_ON + 'TOTAL   : ' + formatRpRaw(finalAmount) + '\n' + ESC.BOLD_OFF
  c += 'Bayar   : ' + (paymentMethod || 'CASH') + '\n'
  c += ESC.LINE
  c += ESC.CENTER + 'Terima kasih!\n'
  c += ESC.FEED
  return c
}

/**
 * Build reservation DP receipt ESC/POS content.
 */
function buildReservationDPReceipt({ storeName, customerName, reservationDate, items, totalAmount, dpAmount, dpMethod }) {
  let c = ESC.INIT + ESC.CENTER
  c += ESC.BOLD_ON + (storeName || 'POS-AI') + '\n' + ESC.BOLD_OFF
  c += 'BUKTI RESERVASI (DP)\n'
  c += ESC.LINE + ESC.LEFT
  c += 'Plg : ' + customerName + '\n'
  c += 'Tgl : ' + (reservationDate || '-') + '\n'
  c += ESC.LINE

  if (items && items.length) {
    items.forEach(i => {
      const qty = i.quantity || i.qty
      const price = i.price_at_moment || i.price
      c += i.menu_name + '\n'
      c += qty + ' x ' + formatRpRaw(price) + ' = ' + formatRpRaw(qty * price) + '\n'
    })
    c += ESC.LINE
  }

  c += 'Total    : ' + formatRpRaw(totalAmount) + '\n'
  c += ESC.BOLD_ON + 'DP (' + dpMethod + '): ' + formatRpRaw(dpAmount) + '\n' + ESC.BOLD_OFF
  c += 'SISA     : ' + formatRpRaw((totalAmount || 0) - (dpAmount || 0)) + '\n'
  c += ESC.FEED
  return c
}

/**
 * Build shopping list (daftar belanja bahan baku) ESC/POS content.
 */
function buildShoppingList(items) {
  const date = new Date().toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' })
  const time = new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })

  let c = ESC.INIT + ESC.CENTER
  c += ESC.BOLD_ON + 'DAFTAR BELANJA\n' + ESC.BOLD_OFF
  c += 'Bahan Baku\n'
  c += ESC.LINE + ESC.LEFT
  c += 'Tgl  : ' + date + '\n'
  c += 'Waktu: ' + time + '\n'
  c += 'Item : ' + items.length + ' bahan\n'
  c += ESC.LINE

  items.forEach((item, i) => {
    const no   = String(i + 1).padStart(2) + '.'
    const nama = item.name.length > 15 ? item.name.slice(0, 14) + '~' : item.name
    const beli = String(item.toBuy) + ' ' + item.unit
    // Col: "02. " (4) + nama padEnd(15) + beli padStart(7) = 26 chars
    c += no + ' ' + nama.padEnd(15) + beli.padStart(7) + '\n'
    c += '    [ ] Catat    [ ] Beli\n'
  })

  c += ESC.LINE
  c += '[ ] Catat = cek ada sblm blnja\n'
  c += '[ ] Beli  = centang sdh dibeli\n'
  c += ESC.FEED
  return c
}

/**
 * Build order list for kitchen/waiter.
 */
function buildOrderList({ storeName, customerName, tableNumber, items }) {
  let c = ESC.INIT + ESC.CENTER
  c += ESC.BOLD_ON + 'LIST PESANAN\n' + ESC.BOLD_OFF
  c += (storeName || 'POS-AI') + '\n'
  c += ESC.LINE + ESC.LEFT
  if (customerName) c += 'Plg : ' + customerName + '\n'
  if (tableNumber) c += 'Meja: ' + tableNumber + '\n'
  c += ESC.LINE

  if (items && items.length) {
    items.forEach(i => {
      const qty = i.quantity || i.qty
      c += qty + 'x ' + (i.menu_name || i.name) + '\n'
      if (i.note) c += '   *' + i.note + '\n'
    })
  }
  c += ESC.LINE + ESC.FEED
  return c
}

export function usePrinter() {
  return {
    // State
    pairedDevice,
    printerStatus,
    isConnecting,
    isPrinting,
    // Actions
    connectPrinter,
    sendToPrinter,
    testPrint,
    getLastPrinterName,
    // Builders
    buildSaleReceipt,
    buildReservationDPReceipt,
    buildOrderList,
    buildShoppingList,
    ESC,
  }
}
