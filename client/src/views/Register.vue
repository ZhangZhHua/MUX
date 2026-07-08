<template>
  <div class="auth-wrapper">
    <div class="auth-container">
      <h2 class="auth-title">MUX | Lab Data OS</h2>
      <p class="auth-subtitle">Create your research account</p>
      
      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label>Email Address</label>
          <input type="email" v-model="email" required placeholder="name@lab.com" />
        </div>
        
        <div class="name-row">
          <div class="form-group flex-1">
            <label>First Name</label>
            <input type="text" v-model="firstName" required placeholder="e.g. John" />
          </div>
          <div class="form-group flex-1">
            <label>Last Name</label>
            <input type="text" v-model="lastName" required placeholder="e.g. Doe" />
          </div>
        </div>

        <div class="form-group">
          <label>Password</label>
          <input type="password" v-model="password" required placeholder="••••••••" />
        </div>
        
        <div class="form-group">
          <label>Select Research Groups (Multi-selectable)</label>
          <div v-if="availableGroups.length > 0" class="group-checkboxes">
            <div v-for="group in availableGroups" :key="group.id" class="checkbox-item">
              <input type="checkbox" :id="'group-' + group.id" :value="group.id" v-model="selectedGroupIds" />
              <label :for="'group-' + group.id">{{ group.name }}</label>
            </div>
          </div>

          <div v-else class="empty-group-box">
            <p class="empty-tip">⚠️ No groups found in database.</p>
            <div class="quick-add-input">
              <input type="text" v-model="newGroupName" placeholder="Enter new group name" />
              <button type="button" @click="handleQuickCreateGroup" class="btn-secondary">Add Group</button>
            </div>
          </div>
        </div>

        <button type="submit" class="btn-primary">Register</button>
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
import { useToast } from '../composables/useToast'; // 🆕 1. 引入通知组件

const email = ref('');
const password = ref('');
const firstName = ref('');
const lastName = ref('');
const selectedGroupIds = ref([]);
const availableGroups = ref([]);
const newGroupName = ref('');
const router = useRouter();
const toast = useToast(); // 🆕 2. 初始化 toast

const fetchGroups = async () => {
  try {
    const response = await api.get('/auth/groups');
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
    toast.success("Group registered into node database."); // 🆕 优雅提示
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
    toast.success('Registration successful! Redirecting to login.'); // 🆕 优雅提示
    router.push('/login');
  } catch (error) {
    toast.error(error.response?.data?.detail || 'Registration failed');
  }
};
</script>

<style scoped>
/* 保持原有的精致注册页 CSS 样式不变 */
.auth-wrapper { display: flex; justify-content: center; align-items: center; min-height: 90vh; background-color: #fafafa; box-sizing: border-box; }
.auth-container { width: 100%; max-width: 460px; background: #ffffff; padding: 35px; border: 1px solid #e1e4e8; border-radius: 8px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); }
.auth-title { margin: 0; font-size: 24px; font-weight: 600; text-align: center; }
.auth-subtitle { margin: 5px 0 25px 0; font-size: 14px; color: #586069; text-align: center; }
.form-group { margin-bottom: 18px; display: flex; flex-direction: column; }
.form-group label { font-size: 13px; font-weight: 600; margin-bottom: 6px; }
.form-group input { padding: 8px 12px; font-size: 14px; border: 1px solid #d1d5da; border-radius: 6px; outline: none; background-color: #fafbfc; }
.name-row { display: flex; gap: 12px; }
.flex-1 { flex: 1; }
.group-checkboxes { border: 1px solid #d1d5da; border-radius: 6px; padding: 10px 12px; max-height: 130px; overflow-y: auto; background: #fafbfc; }
.checkbox-item { display: flex; align-items: center; margin-bottom: 8px; }
.checkbox-item input { margin-right: 8px; cursor: pointer; }
.empty-group-box { border: 1px dashed #d1d5da; border-radius: 6px; padding: 12px; background: #fffdf5; }
.empty-tip { margin: 0 0 8px 0; font-size: 13px; color: #9a6e1a; }
.quick-add-input { display: flex; gap: 8px; }
.quick-add-input input { flex: 1; padding: 6px 10px; }
.btn-secondary { padding: 6px 12px; background: #eff3f6; border: 1px solid #d1d5da; border-radius: 4px; font-size: 13px; font-weight: 600; cursor: pointer; }
.btn-primary { width: 100%; padding: 10px; color: #ffffff; background-color: #2ea44f; border: none; border-radius: 6px; font-size: 14px; font-weight: 600; cursor: pointer; }
.switch-tip { margin-top: 20px; text-align: center; font-size: 13px; color: #586069; }
.link { color: #0366d6; text-decoration: none; }
</style>