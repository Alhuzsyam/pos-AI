import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/composables/useApi'

export const useAppSettingsStore = defineStore('appSettings', () => {
  const watchlistEnabled = ref(true)
  const loaded = ref(false)

  async function load() {
    if (loaded.value) return
    try {
      const res = await api.get('/api/v1/settings/')
      watchlistEnabled.value = res.data.watchlist_enabled ?? true
      loaded.value = true
    } catch {}
  }

  function reset() {
    loaded.value = false
    watchlistEnabled.value = true
  }

  return { watchlistEnabled, loaded, load, reset }
})
