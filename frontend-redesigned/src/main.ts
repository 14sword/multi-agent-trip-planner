import { createApp } from 'vue'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import './assets/design-system.css'
import './assets/micro-interactions.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(Antd)
app.use(router)
app.mount('#app')
