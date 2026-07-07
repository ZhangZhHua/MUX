import { createRouter, createWebHistory } from 'vue-router';
import Login from '../views/Login.vue';
import Register from '../views/Register.vue';
import Dashboard from '../views/Dashboard.vue';
import ExperimentDetail from '../views/ExperimentDetail.vue'; // 🆕 引入新创建的详情页
import TeamMembers from '../views/TeamMembers.vue';
import Settings from '../views/Settings.vue';
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
  { path: '/settings', name: 'Settings', component: Settings, meta: { requiresAuth: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to, from) => {
  const token = localStorage.getItem('token');
  
  if (to.meta.requiresAuth && !token) {
    return '/login'; // 直接返回目标路径，Vue Router 会自动拦截并重定向
  }
  // 如果允许通行，不需要显式写任何 return，或者 return true 即可
});

export default router;