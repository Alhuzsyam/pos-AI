import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'

import App from './App.vue'
import router from './router'
import './style.css'

// Apply saved theme before first render to avoid flash
if (localStorage.getItem('theme') === 'dark') {
  document.documentElement.classList.add('dark')
}

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(Toast, { timeout: 3000, position: 'top-right' })
app.mount('#app')
