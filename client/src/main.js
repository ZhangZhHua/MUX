import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // 引入我们配置的路由
import './assets/main.css' // 🆕 引入全局样式


const app = createApp(App)

app.use(router) // 挂载路由

app.mount('#app')