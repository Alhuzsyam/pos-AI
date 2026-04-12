<template>
  <div class="flex h-screen overflow-hidden bg-claude-paper">
    <!-- Sidebar -->
    <aside
      :class="[
        'flex flex-col bg-claude-paper border-r border-claude-line transition-all duration-300 z-30',
        collapsed ? 'w-16' : 'w-64',
        'hidden md:flex'
      ]"
    >
      <!-- Brand -->
      <div class="flex items-center gap-3 px-5 py-5">
        <div class="w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center flex-shrink-0">
          <span class="font-serif text-white text-[15px] leading-none">P</span>
        </div>
        <div v-if="!collapsed" class="min-w-0 flex-1">
          <p class="font-serif text-[15px] text-claude-ink leading-tight">POS-AI</p>
          <p class="text-[11px] text-claude-dust truncate">{{ auth.user?.tenant_name || 'SaaS Platform' }}</p>
        </div>
        <button
          @click="collapsed = !collapsed"
          class="text-claude-dust hover:text-claude-graphite transition-colors flex-shrink-0"
          :title="collapsed ? 'Buka sidebar' : 'Tutup sidebar'"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              :d="collapsed ? 'M9 5l7 7-7 7' : 'M15 19l-7-7 7-7'" />
          </svg>
        </button>
      </div>

      <!-- Nav -->
      <nav class="flex-1 overflow-y-auto py-3 px-3 space-y-0.5">
        <NavItem to="/" icon="chart-pie" :label="collapsed ? '' : 'Dashboard'" exact />

        <NavGroup v-if="!collapsed" label="Operasional" />
        <NavItem to="/pos" icon="cash-register" :label="collapsed ? '' : 'Kasir / POS'" />
        <NavItem to="/sales" icon="receipt" :label="collapsed ? '' : 'Riwayat Transaksi'" />
        <NavItem to="/expenses" icon="wallet" :label="collapsed ? '' : 'Pengeluaran'" v-if="auth.can('kasir')" />
        <NavItem to="/debts" icon="book" :label="collapsed ? '' : 'Buku Hutang'" />
        <NavItem to="/reservations" icon="calendar" :label="collapsed ? '' : 'Reservasi'" />

        <NavItem to="/watchlist" icon="clipboard-list" :label="collapsed ? '' : 'Watchlist / KDS'" />

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

      <!-- User footer -->
      <div class="border-t border-claude-line px-3 py-3">
        <div class="flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-white transition-colors">
          <div class="w-8 h-8 bg-brand-50 border border-brand-100 rounded-lg flex items-center justify-center flex-shrink-0">
            <span class="text-brand-600 font-semibold text-[11px]">{{ initials }}</span>
          </div>
          <div v-if="!collapsed" class="flex-1 min-w-0">
            <p class="text-[13px] font-medium text-claude-ink truncate">{{ auth.user?.full_name || auth.user?.username }}</p>
            <p class="text-[11px] text-claude-dust capitalize">{{ auth.user?.role }}</p>
          </div>
          <button
            v-if="!collapsed"
            @click="auth.logout()"
            class="text-claude-dust hover:text-brand-600 transition-colors"
            title="Logout"
          >
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
      <header class="md:hidden bg-claude-paper border-b border-claude-line px-4 py-3 flex items-center gap-3">
        <button @click="mobileOpen = !mobileOpen" class="text-claude-graphite">
          <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <span class="font-serif text-[16px] text-claude-ink">POS-AI</span>
      </header>

      <!-- Page content -->
      <main class="flex-1 overflow-y-auto">
        <RouterView />
      </main>
    </div>

    <!-- Mobile drawer overlay -->
    <Teleport to="body">
      <div v-if="mobileOpen" class="fixed inset-0 z-50 md:hidden">
        <div class="absolute inset-0 bg-claude-ink/40" @click="mobileOpen = false" />
        <aside class="absolute left-0 top-0 bottom-0 w-64 bg-claude-paper flex flex-col border-r border-claude-line">
          <div class="p-4 border-b border-claude-line flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center">
                <span class="font-serif text-white text-[15px] leading-none">P</span>
              </div>
              <span class="font-serif text-[16px] text-claude-ink">POS-AI</span>
            </div>
            <button @click="mobileOpen = false" class="text-claude-slate">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <nav class="flex-1 overflow-y-auto py-4 px-3 space-y-0.5" @click="mobileOpen = false">
            <NavItem to="/" icon="chart-pie" label="Dashboard" exact />
            <NavItem to="/pos" icon="cash-register" label="Kasir / POS" />
            <NavItem to="/sales" icon="receipt" label="Riwayat Transaksi" />
            <NavItem to="/expenses" icon="wallet" label="Pengeluaran" v-if="auth.can('kasir')" />
            <NavItem to="/debts" icon="book" label="Buku Hutang" />
            <NavItem to="/reservations" icon="calendar" label="Reservasi" />
            <NavItem to="/watchlist" icon="clipboard-list" label="Watchlist / KDS" />
            <NavItem to="/inventory" icon="cube" label="Inventori" v-if="auth.can('inventory')" />
            <NavItem to="/menu" icon="menu-alt" label="Kelola Menu" v-if="auth.can('manager')" />
            <NavItem to="/reports" icon="chart-bar" label="Laporan" v-if="auth.can('manager')" />
            <NavItem to="/ai" icon="sparkles" label="AI Assistant" />
            <NavItem to="/users" icon="users" label="Pengguna" v-if="auth.isAdmin" />
            <NavItem to="/tenants" icon="office-building" label="Tenant" v-if="auth.isSuperAdmin" />
            <NavItem to="/settings" icon="cog" label="Pengaturan" />
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
