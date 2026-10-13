import { createApp } from 'vue'
import App from './App.vue'
import './assets/tokens.css'
import router from './router'
import { applyTheme, loadTheme } from './theme'

applyTheme(loadTheme())

const app = createApp(App)

app.use(router)

app.mount('#app')
