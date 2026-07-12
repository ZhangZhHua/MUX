<template>
  <div class="auth-wrapper">
    <!-- Ambient Glows (Light Mode) -->
    <div class="ambient-glow cyan-glow"></div>
    <div class="ambient-glow indigo-glow"></div>
    
    <div class="auth-container">
      <div class="logo-row">
        <MuxLogo />
      </div>
      <h2 class="auth-title">Create account</h2>
      <p class="auth-subtitle">Get started with MUX Lab Data OS</p>
      
      <form @submit.prevent="handleRegister" class="auth-form">
        <div class="form-group">
          <label>Email Address</label>
          <input type="email" v-model="email" required placeholder="name@lab.com" class="auth-input" />
        </div>
        
        <div class="name-row">
          <div class="form-group flex-1">
            <label>First Name</label>
            <input type="text" v-model="firstName" required placeholder="e.g. John" class="auth-input" />
          </div>
          <div class="form-group flex-1">
            <label>Last Name</label>
            <input type="text" v-model="lastName" required placeholder="e.g. Doe" class="auth-input" />
          </div>
        </div>

        <div class="form-group">
          <label>Password</label>
          <input type="password" v-model="password" required placeholder="••••••••" class="auth-input" />
        </div>
        
        <div class="form-group">
          <label>Select Research Groups (Multi-selectable)</label>
          <div v-if="availableGroups.length > 0" class="group-checkboxes">
            <div v-for="group in availableGroups" :key="group.id" class="checkbox-item">
              <input type="checkbox" :id="'group-' + group.id" :value="group.id" v-model="selectedGroupIds" class="auth-checkbox" />
              <label :for="'group-' + group.id" class="checkbox-label">{{ group.name }}</label>
            </div>
          </div>

          <div v-else class="empty-group-box">
            <p class="empty-tip">⚠️ No groups found in database.</p>
            <div class="quick-add-input">
              <input type="text" v-model="newGroupName" placeholder="New group name" class="auth-input compact-input" />
              <button type="button" @click="handleQuickCreateGroup" class="btn-secondary">Add</button>
            </div>
          </div>
        </div>

        <button type="submit" class="btn-primary">
          <span>Register Account</span>
          <span class="btn-arrow">→</span>
        </button>
        <p class="switch-tip">
          Already have an account? <router-link to="/login" class="link">Login here</router-link>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../services/api';
import { useToast } from '../composables/useToast';
import MuxLogo from '../components/common/MuxLogo.vue';

const email = ref('');
const password = ref('');
const firstName = ref('');
const lastName = ref('');
const selectedGroupIds = ref([]);
const availableGroups = ref([]);
const newGroupName = ref('');
const router = useRouter();
const toast = useToast();

const fetchGroups = async () => {
  try {
    const response = await api.get('/auth/public-groups');
    availableGroups.value = response.data;
  } catch (error) {
    console.error('Failed to fetch groups:', error);
  }
};

onMounted(() => { fetchGroups(); });

const handleQuickCreateGroup = async () => {
  if (!newGroupName.value.trim()) return;
  try {
    await api.post('/auth/groups', { name: newGroupName.value.trim(), description: 'Auto created' });
    newGroupName.value = '';
    toast.success("Group registered into node database.");
    await fetchGroups();
  } catch (error) {
    toast.error(error.response?.data?.detail || 'Failed to create group');
  }
};

const handleRegister = async () => {
  if (selectedGroupIds.value.length === 0) {
    toast.error('Please select at least one research group.');
    return;
  }
  try {
    await api.post('/auth/register', {
      email: email.value,
      password: password.value,
      first_name: firstName.value,
      last_name: lastName.value,
      group_ids: selectedGroupIds.value
    });
    toast.success('Registration successful! Redirecting to login.');
    router.push('/login');
  } catch (error) {
    toast.error(error.response?.data?.detail || 'Registration failed');
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
  overflow-y: auto;
  padding: 40px 20px;
  box-sizing: border-box;
  font-family: Inter, system-ui, -apple-system, sans-serif;
  color: #1e293b;
}

/* Background Ambient Glows - very soft for light mode */
.ambient-glow {
  position: absolute;
  width: 480px;
  height: 480px;
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
  max-width: 480px;
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

.name-row {
  display: flex;
  gap: 16px;
}

.flex-1 {
  flex: 1;
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

.group-checkboxes {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 12px;
  max-height: 130px;
  overflow-y: auto;
  background: #ffffff;
  box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.04);
}

/* Custom Scrollbar for Checkboxes */
.group-checkboxes::-webkit-scrollbar {
  width: 6px;
}
.group-checkboxes::-webkit-scrollbar-track {
  background: transparent;
}
.group-checkboxes::-webkit-scrollbar-thumb {
  background: rgba(15, 23, 42, 0.15);
  border-radius: 3px;
}
.group-checkboxes::-webkit-scrollbar-thumb:hover {
  background: rgba(15, 23, 42, 0.25);
}

.checkbox-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.checkbox-item:last-child {
  margin-bottom: 0;
}

.auth-checkbox {
  margin-right: 10px;
  accent-color: #2563eb;
  cursor: pointer;
  width: 15px;
  height: 15px;
}

.checkbox-label {
  font-size: 13.5px !important;
  font-weight: 500 !important;
  color: #0f172a !important;
  margin-bottom: 0 !important;
  cursor: pointer;
  user-select: none;
}

.empty-group-box {
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  padding: 14px;
  background: rgba(245, 158, 11, 0.05);
}

.empty-tip {
  margin: 0 0 10px 0;
  font-size: 13px;
  color: #d97706;
  font-weight: 600;
}

.quick-add-input {
  display: flex;
  gap: 8px;
}

.compact-input {
  flex: 1;
  padding: 6px 12px;
  font-size: 13px;
}

.btn-secondary {
  padding: 6px 14px;
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  color: #334155;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-secondary:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
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