<template>
  <div class="auth-wrapper">
    <!-- Ambient Glows (Light Mode) -->
    <div class="ambient-glow cyan-glow"></div>
    <div class="ambient-glow indigo-glow"></div>
    
    <div class="auth-container">
      <div class="logo-row">
        <MuxLogo />
      </div>
      <!-- <h2 class="auth-title">Welcome back</h2> -->
      <p class="auth-subtitle">Sign in to MUX Lab Data OS</p>
      
      <form @submit.prevent="handleLogin" class="auth-form">
        <div class="form-group">
          <label>Email Address</label>
          <input type="email" v-model="email" required placeholder="name@lab.com" class="auth-input" />
        </div>

        <div class="form-group">
          <label>Password</label>
          <input type="password" v-model="password" required placeholder="••••••••" class="auth-input" />
        </div>

        <button type="submit" class="btn-primary">
          <span>Sign In</span>
          <span class="btn-arrow">→</span>
        </button>
        
        <p class="switch-tip">
          Don't have an account? <router-link to="/register" class="link">Register here</router-link>
          <!-- 换行 --> 
          <br> If forget password, please contact the administrator.
        </p>
       
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from '../services/api';
import { useToast } from '../composables/useToast';
import MuxLogo from '../components/common/MuxLogo.vue';

const email = ref('');
const password = ref('');
const router = useRouter();
const route = useRoute();
const toast = useToast();

const getSafeRedirectPath = () => {
  const redirect = route.query.redirect;
  return typeof redirect === 'string' && redirect.startsWith('/') && !redirect.startsWith('//')
    ? redirect
    : '/';
};

const handleLogin = async () => {
  try {
    const formData = new FormData();
    formData.append('username', email.value);
    formData.append('password', password.value);

    const response = await api.post('/auth/login', formData);
    
    localStorage.setItem('token', response.data.access_token);
    localStorage.setItem('role', response.data.role);
    localStorage.setItem('userName', response.data.full_name);
    localStorage.setItem('userId', response.data.user_id);
    
    toast.success("Welcome back!");
    router.replace(getSafeRedirectPath());
  } catch (error) {
    toast.error(error.response?.data?.detail || 'Login failed. Check your credentials.');
  }
};
</script>

<style scoped>
.auth-wrapper {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: radial-gradient(circle at center, #f8fafc 0%, #e2e8f0 100%);
  overflow: hidden;
  font-family: Inter, system-ui, -apple-system, sans-serif;
  color: #1e293b;
}

/* Background Ambient Glows - very soft for light mode */
.ambient-glow {
  position: absolute;
  width: 450px;
  height: 450px;
  border-radius: 50%;
  filter: blur(140px);
  opacity: 0.45;
  pointer-events: none;
  z-index: 0;
}
.cyan-glow {
  background: #ecfeff;
  top: 10%;
  left: 15%;
}
.indigo-glow {
  background: #e0e7ff;
  bottom: 10%;
  right: 15%;
}

/* Premium White Glassmorphic Container */
.auth-container {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 420px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 16px;
  padding: 40px;
  box-shadow: 
    0 10px 25px -5px rgba(15, 23, 42, 0.05), 
    0 20px 40px -15px rgba(15, 23, 42, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  animation: slide-up 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes slide-up {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.logo-row {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.auth-title {
  margin: 0;
  font-size: 24px;
  font-weight: 800;
  text-align: center;
  letter-spacing: -0.5px;
  color: #0f172a;
}

.auth-subtitle {
  margin: 6px 0 32px 0;
  font-size: 14px;
  color: #64748b;
  text-align: center;
  font-weight: 500;
}

.auth-form {
  display: flex;
  flex-direction: column;
}

.form-group {
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  text-align: left;
}

.form-group label {
  font-size: 12.5px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #475569;
}

.auth-input {
  padding: 10px 14px;
  font-size: 14px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  outline: none;
  background: #ffffff;
  color: #0f172a;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.auth-input::placeholder {
  color: #94a3b8;
}

.auth-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
  background: #ffffff;
}

.btn-primary {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 11px;
  margin-top: 10px;
  color: #ffffff;
  background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
  border: none;
  border-radius: 8px;
  font-size: 14.5px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.18);
  transition: all 0.2s ease;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.28);
  filter: brightness(1.05);
}

.btn-primary:active {
  transform: translateY(0);
}

.btn-arrow {
  transition: transform 0.2s ease;
}

.btn-primary:hover .btn-arrow {
  transform: translateX(3px);
}

.switch-tip {
  margin-top: 24px;
  text-align: center;
  font-size: 13.5px;
  color: #64748b;
}

.link {
  color: #2563eb;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.15s ease;
}

.link:hover {
  color: #1d4ed8;
  text-decoration: underline;
}
</style>
