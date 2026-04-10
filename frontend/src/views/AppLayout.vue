<template>
  <div class="flex h-screen overflow-hidden bg-surface">
    <!-- Sidebar -->
    <aside
      :class="[
        'flex flex-col bg-white border-r border-gray-100 transition-all duration-300 z-30',
        collapsed ? 'w-16' : 'w-60',
        'hidden md:flex'
      ]"
    >
      <!-- Brand -->
      <div class="flex items-center gap-3 px-4 py-5 border-b border-gray-100">
        <div class="w-8 h-8 bg-brand-700 rounded-xl flex items-center justify-center flex-shrink-0">
          <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 11h.01M12 11h.01M15 11h.01M4 19h16a2 2 0 002-2V7a2 2 0 00-2-2H4a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>
        <div v-if="!collapsed" class="min-w-0">
          <p class="font-bold text-gray-900 text-sm leading-tight">POS-AI</p>
          <p class="text-xs text-gray-400 truncate">{{ auth.user?.tenant_name || 'SaaS Platform' }}</p>
        </div>
        <button @click="collapsed = !collapsed" class="ml-auto text-gray-400 hover:text-gray-600 hidden md:block flex-shrink-0">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              :d="collapsed ? 'M9 5l7 7-7 7' : 'M15 19l-7-7 7-7'" />
          </svg>
        </button>
      </div>

      <!-- Nav -->
      <nav class="flex-1 overflow-y-auto py-4 px-2 space-y-0.5">
        <NavItem to="/" icon="chart-pie" :label="collapsed ? '' : 'Dashboard'" exact />

        <NavGroup v-if="!collapsed" label="Operasional" />
        <NavItem to="/pos" icon="cash-register" :label="collapsed ? '' : 'Kasir / POS'" />
        <NavItem to="/sales" icon="receipt" :label="collapsed ? '' : 'Riwayat Transaksi'" />
        <NavItem to="/expenses" icon="wallet" :label="collapsed ? '' : 'Pengeluaran'" v-if="auth.can('kasir')" />
        <NavItem to="/debts" icon="book" :label="collapsed ? '' : 'Buku Hutang'" />
        <NavItem to="/reservations" icon="calendar" :label="collapsed ? '' : 'Reservasi'" />

        <NavGroup v-if="!collapsed" label="Produk & Stok" />
        <NavItem to="/inventory" icon="cube" :label="collapsed ? '' : 'Inventori'" v-if="auth.can('inventory')" />
        <NavItem to="/menu" icon="menu-alt" :label="collapsed ? '' : 'Kelola Menu'" v-if="auth.can('manager')" />

        <NavGroup v-if="!collapsed" label="Analitik" />
        <NavItem to="/reports" icon="chart-bar" :label="collapsed ? '' : 'Laporan'" v-if="auth.can('manager')" />
        <NavItem to="/ai" icon="sparkles" :label="collapsed ? '' : 'AI Assistant'" />

        <NavGroup v-if="!collapsed && auth.isAdmin" label="Manajemen" />
        <NavItem to="/users" icon="users" :label="collapsed ? '' : 'Pengguna'" v-if="auth.isAdmin" />
        <NavItem to="/tenants" icon="office-building" :label="collapsed ? '' : 'Tenant'" v-if="auth.isSuperAdmin" />
        <NavItem to="/settings" icon="cog" :label="collapsed ? '' : 'Pengaturan'" />
      </nav>

      <!-- User -->
      <div class="border-t border-gray-100 p-3">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 bg-brand-100 rounded-xl flex items-center justify-center flex-shrink-0">
            <span class="text-brand-700 font-bold text-xs">{{ initials }}</span>
          </div>
          <div v-if="!collapsed" class="flex-1 min-w-0">
            <p class="text-sm font-semibold text-gray-800 truncate">{{ auth.user?.full_name || auth.user?.username }}</p>
            <p class="text-xs text-gray-400 capitalize">{{ auth.user?.role }}</p>
          </div>
          <button @click="auth.logout()" class="text-gray-400 hover:text-red-500 transition-colors" title="Logout">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>
      </div>
    </aside>

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden">
      <!-- Mobile topbar -->
      <header class="md:hidden bg-white border-b border-gray-100 px-4 py-3 flex items-center gap-3">
        <button @click="mobileOpen = !mobileOpen" class="text-gray-600">
          <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <span class="font-bold text-gray-900">POS-AI</span>
      </header>

      <!-- Page content -->
      <main class="flex-1 overflow-y-auto">
        <RouterView />
      </main>
    </div>

    <!-- Mobile drawer overlay -->
    <Teleport to="body">
      <div v-if="mobileOpen" class="fixed inset-0 z-50 md:hidden">
        <div class="absolute inset-0 bg-black/50" @click="mobileOpen = false" />
        <aside class="absolute left-0 top-0 bottom-0 w-64 bg-white flex flex-col">
          <div class="p-4 border-b flex items-center justify-between">
            <span class="font-bold text-lg">POS-AI</span>
            <button @click="mobileOpen = false"><svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg></button>
          </div>
          <nav class="flex-1 overflow-y-auto py-4 px-2 space-y-0.5" @click="mobileOpen = false">
            <NavItem to="/" icon="chart-pie" label="Dashboard" exact />
            <NavItem to="/pos" icon="cash-register" label="Kasir / POS" />
            <NavItem to="/sales" icon="receipt" label="Riwayat Transaksi" />
            <NavItem to="/expenses" icon="wallet" label="Pengeluaran" v-if="auth.can('kasir')" />
            <NavItem to="/debts" icon="book" label="Buku Hutang" />
            <NavItem to="/reservations" icon="calendar" label="Reservasi" />
            <NavItem to="/inventory" icon="cube" label="Inventori" v-if="auth.can('inventory')" />
            <NavItem to="/menu" icon="menu-alt" label="Kelola Menu" v-if="auth.can('manager')" />
            <NavItem to="/reports" icon="chart-bar" label="Laporan" v-if="auth.can('manager')" />
            <NavItem to="/ai" icon="sparkles" label="AI Assistant" />
            <NavItem to="/users" icon="users" label="Pengguna" v-if="auth.isAdmin" />
            <NavItem to="/tenants" icon="office-building" label="Tenant" v-if="auth.isSuperAdmin" />
          </nav>
        </aside>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import NavItem from '@/components/NavItem.vue'
import NavGroup from '@/components/NavGroup.vue'

const auth = useAuthStore()
const collapsed = ref(false)
const mobileOpen = ref(false)

const initials = computed(() => {
  const name = auth.user?.full_name || auth.user?.username || 'U'
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
})
</script>
