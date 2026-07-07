<template>
  <div class="settings-page-layout">
    <Header :userName="userName" :userRole="userRole" @logout="handleLogout" />
    <Sidebar :groups="groups" :currentGroupId="currentGroupId" @group-change="handleGroupChange" />

    <main class="settings-main-content">
      <div class="settings-placeholder">
        <span class="settings-icon">⚙️</span>
        <h2>System Settings</h2>
        <p>Coming soon — configuration and administration tools are under development.</p>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import Header from '../components/layout/Header.vue';
import Sidebar from '../components/layout/Sidebar.vue';
import api from '../services/api';

const router = useRouter();

const userName = ref('Researcher');
const userRole = ref('member');
const groups = ref([]);
const currentGroupId = ref(Number(localStorage.getItem('activeGroupId') || 0));

onMounted(async () => {
  userName.value = localStorage.getItem('userName') || 'Researcher';
  userRole.value = localStorage.getItem('role') || 'member';
  try {
    const response = await api.get('/auth/groups');
    groups.value = response.data;
  } catch {
    // groups optional for placeholder page
  }
});

const handleGroupChange = (groupId) => {
  currentGroupId.value = groupId;
  localStorage.setItem('activeGroupId', groupId);
};

const handleLogout = () => {
  localStorage.clear();
  router.push('/login');
};
</script>

<style scoped>
.settings-page-layout {
  height: 100%;
  overflow: hidden;
  background-color: var(--bg-primary);
}

.settings-main-content {
  margin-top: 64px;
  margin-left: 240px;
  padding: 24px 32px;
  box-sizing: border-box;
  height: calc(100vh - 64px);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.settings-placeholder {
  text-align: center;
  max-width: 480px;
  padding: 48px 40px;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
}

.settings-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
}

.settings-placeholder h2 {
  margin: 0 0 12px;
  font-size: 24px;
  color: var(--text-main);
}

.settings-placeholder p {
  margin: 0;
  color: var(--text-muted);
  font-size: 15px;
  line-height: 1.6;
}
</style>
