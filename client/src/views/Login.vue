<template>
  <div class="auth-wrapper">
    <div class="auth-container">
      <h2 class="auth-title">Physics Lab Log System</h2>
      <p class="auth-subtitle">Sign in to your workspace</p>
      
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>Email Address</label>
          <input type="email" v-model="email" required placeholder="name@lab.com" />
        </div>

        <div class="form-group">
          <label>Password</label>
          <input type="password" v-model="password" required placeholder="••••••••" />
        </div>

        <button type="submit" class="btn-primary">Login</button>
        
        <p class="switch-tip">
          Don't have an account? <router-link to="/register" class="link">Register here</router-link>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '../services/api';
import { useToast } from '../composables/useToast'; // 🆕 1. 引入通知组件

const email = ref('');
const password = ref('');
const router = useRouter();
const toast = useToast(); // 🆕 2. 初始化 toast

const handleLogin = async () => {
  try {
    const formData = new FormData();
    formData.append('username', email.value);
    formData.append('password', password.value);

    const response = await api.post('/auth/login', formData);
    
    localStorage.setItem('token', response.data.access_token);
    localStorage.setItem('role', response.data.role);
    localStorage.setItem('userName', response.data.full_name);
    
    toast.success("Welcome back!"); // 🆕 登录成功提示
    router.push('/');
  } catch (error) {
    // 💡 此时 toast 已经被定义，绝不会再报错
    toast.error(error.response?.data?.detail || 'Login failed. Check your credentials.');
  }
};
</script>

<style scoped>
/* 保持你的登录页样式不变 */
.auth-wrapper { display: flex; justify-content: center; align-items: center; min-height: 90vh; background-color: #fafafa; }
.auth-container { width: 100%; max-width: 420px; background: #ffffff; padding: 35px; border: 1px solid #e1e4e8; border-radius: 8px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); }
.auth-title { margin: 0; font-size: 24px; font-weight: 600; text-align: center; }
.auth-subtitle { margin: 5px 0 25px 0; font-size: 14px; color: #586069; text-align: center; }
.form-group { margin-bottom: 18px; display: flex; flex-direction: column; }
.form-group label { font-size: 13px; font-weight: 600; margin-bottom: 6px; }
.form-group input { padding: 8px 12px; font-size: 14px; border: 1px solid #d1d5da; border-radius: 6px; outline: none; }
.btn-primary { width: 100%; padding: 10px; color: #ffffff; background-color: #2563eb; border: none; border-radius: 6px; font-size: 14px; font-weight: 600; cursor: pointer; }
.btn-primary:hover { background-color: #1d4ed8; }
.switch-tip { margin-top: 20px; text-align: center; font-size: 13px; color: #586069; }
.link { color: #0366d6; text-decoration: none; }
.link:hover { text-decoration: underline; }
</style>