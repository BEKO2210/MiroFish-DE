import { createApp } from 'vue'
import App from './App.vue'
import './assets/tokens.css'
import router from './router'
import i18n from './i18n'
import { applyTheme, loadTheme } from './theme'

applyTheme(loadTheme())

const app = createApp(App)

app.use(router)
app.use(i18n)

app.mount('#app')
