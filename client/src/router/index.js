import { createRouter, createWebHistory } from 'vue-router';
import Login from '../views/Login.vue';
import Register from '../views/Register.vue';
import Dashboard from '../views/Dashboard.vue';
import ExperimentDetail from '../views/ExperimentDetail.vue'; // 🆕 引入新创建的详情页
import TeamMembers from '../views/TeamMembers.vue';
import Settings from '../views/Settings.vue';
import EventsTimeline from '../views/EventsTimeline.vue'; // 🆕 引入日程与大事记页面
const routes = [
  { path: '/login', name: 'Login', component: Login },
  { path: '/register', name: 'Register', component: Register },
  { path: '/', name: 'Dashboard', component: Dashboard, meta: { requiresAuth: true } },
  { 
    path: '/experiment/:id', 
    name: 'ExperimentDetail', 
    component: ExperimentDetail, 
    meta: { requiresAuth: true } 
  },
  { path: '/team-members', name: 'TeamMembers', component: TeamMembers, meta: { requiresAuth: true } },
  { path: '/events', name: 'EventsTimeline', component: EventsTimeline, meta: { requiresAuth: true } }, // 🆕 日程事件页面路由
  { path: '/settings', name: 'Settings', component: Settings, meta: { requiresAuth: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to, from) => {
  const token = localStorage.getItem('token');
  
  if (to.meta.requiresAuth && !token) {
    return { path: '/login', query: { redirect: to.fullPath } };
  }
  
  // 🆕 当从其他页面（通过 Sidebar 等）切换到 /events 时，清除缓存的查看日期使之默认展示今天。
  // 而直接刷新页面时，from.name 为空，缓存则会被保留。
  if (to.path === '/events' && from.name && from.path !== '/events') {
    sessionStorage.removeItem('view_date');
  }
});

export default router;
