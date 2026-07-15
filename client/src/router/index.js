import { createRouter, createWebHistory } from 'vue-router';
import api from '../services/api';
const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  { path: '/register', name: 'Register', component: () => import('../views/Register.vue') },
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue'), meta: { requiresAuth: true } },
  { 
    path: '/experiment/:id', 
    name: 'ExperimentDetail', 
    component: () => import('../views/ExperimentDetail.vue'),
    meta: { requiresAuth: true } 
  },
  { path: '/team-members', name: 'TeamMembers', component: () => import('../views/TeamMembers.vue'), meta: { requiresAuth: true } },
  { path: '/events', name: 'EventsTimeline', component: () => import('../views/EventsTimeline.vue'), meta: { requiresAuth: true } },
  { path: '/settings', name: 'Settings', component: () => import('../views/Settings.vue'), meta: { requiresAuth: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach(async (to, from) => {
  if (to.meta.requiresAuth) {
    try {
      await api.get('/auth/me');
      sessionStorage.setItem('authenticated', 'true');
    } catch {
      sessionStorage.removeItem('authenticated');
      return { path: '/login', query: { redirect: to.fullPath } };
    }
  }
  
  // 🆕 当从其他页面（通过 Sidebar 等）切换到 /events 时，清除缓存的查看日期使之默认展示今天。
  // 而直接刷新页面时，from.name 为空，缓存则会被保留。
  if (to.path === '/events' && from.name && from.path !== '/events') {
    sessionStorage.removeItem('view_date');
  }
});

export default router;
