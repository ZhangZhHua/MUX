<template>
  <div>
    <!-- Mobile Sidebar Backdrop Overlay -->
    <div class="sidebar-mobile-backdrop" v-if="isOpen" @click="$emit('close')"></div>

    <aside class="global-sidebar" :class="{ 'is-open': isOpen }">
      <!-- Mobile Sidebar Close Button -->
      <button class="btn-close-sidebar" @click="$emit('close')" aria-label="Close Sidebar">&times;</button>
    <div class="team-selector-zone">
      <div class="team-header-row">
        <label class="sidebar-label">RESEARCH TEAM</label>
        <button 
          v-if="userRole === 'sys_admin'" 
          class="btn-spawn-group-trigger" 
          title="Spawn New Research Group Partition"
          @click="showCreateGroupModal = true"
        >
          ➕
        </button>
      </div>

      <div class="team-select-wrapper">
        <select 
          :value="currentGroupId" 
          @change="$emit('group-change', Number($event.target.value))"
          class="modern-team-selector"
        >
          <option :value="0">✨ All My Teams</option>
          <option v-for="g in groups" :key="g.id" :value="g.id">
            {{ g.name }}
          </option>
        </select>
      </div>
    </div>

    <!-- Part 2: Experiments & Team Pages Navigation -->
    <nav class="sidebar-nav-menu">
      <div class="nav-item" :class="{ active: route.path === '/' }" @click="router.push('/')">
        <span class="nav-icon">📊</span>
        <span class="nav-text">Experiments Overview</span>
      </div>

      <div class="nav-item" :class="{ active: route.path === '/team-members' }" @click="router.push('/team-members')">
        <span class="nav-icon">👥</span>
        <span class="nav-text">Team Members</span>
      </div>

      <div class="nav-item" :class="{ active: route.path === '/events' }" @click="router.push('/events')">
        <span class="nav-icon">📅</span>
        <span class="nav-text">Lab Events</span>
      </div>
    </nav>

    <!-- Telemetry Clocks (Now above Settings at the bottom) -->
    <div class="telemetry-clocks-panel">
      <div class="clock-node">
        <span class="clock-label">Beijing (UTC+8)</span>
        <span class="clock-time">{{ beijingTime }}</span>
      </div>
      <div class="clock-node">
        <span class="clock-label">Geneva (CERN)</span>
        <span class="clock-time">{{ genevaTime }}</span>
      </div>
    </div>

    <!-- Part 3: Settings Navigation (At the bottom) -->
    <nav class="sidebar-footer-menu">
      <div class="nav-item" :class="{ active: route.path === '/settings' }" @click="router.push('/settings')">
        <span class="nav-icon">⚙️</span>
        <span class="nav-text">System Settings</span>
      </div>
    </nav>

    <Teleport to="body">
      <div class="modal-backdrop" v-if="showCreateGroupModal" @mousedown.self="mouseDownTarget = $event.target" @mouseup.self="mouseDownTarget === $event.currentTarget && closeGroupModal()">
        <div class="modal-box spawn-group-modal">
          <div class="modal-header">
            <h3>Spawn New Research Group</h3>
            <button class="btn-close-x" @click="closeGroupModal">&times;</button>
          </div>
          <form @submit.prevent="handleCommitNewGroup" class="modal-form-flow">
            <div class="modal-form-group">
              <label>Group Cluster Name *</label>
              <input type="text" v-model="newGroupName" required placeholder="e.g., HGTD, DarkMatter..." />
            </div>
            <div class="modal-form-group">
              <label>Scientific Directive / Description</label>
              <textarea v-model="newGroupDesc" rows="3" placeholder="Describe research goals..."></textarea>
            </div>
            <div class="modal-actions">
              <button type="button" class="btn-cancel" @click="closeGroupModal">Cancel</button>
              <button type="submit" class="btn-submit" :disabled="!newGroupName.trim()">Deploy Node</button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>
  </aside>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import api from '../../services/api';
import { useToast } from '../../composables/useToast';

defineProps({
  groups: { type: Array, default: () => [] },
  currentGroupId: { type: Number, default: 0 },
  isOpen: { type: Boolean, default: false }
});

const emit = defineEmits(['group-change', 'close']);

const router = useRouter();
const route = useRoute();
const toast = useToast();
const userRole = ref('member');

const showCreateGroupModal = ref(false);
const newGroupName = ref('');
const newGroupDesc = ref('');

let mouseDownTarget = null;

const beijingTime = ref('');
const genevaTime = ref('');
let clockInterval = null;

const updateClocks = () => {
  const now = new Date();
  beijingTime.value = now.toLocaleTimeString('en-US', {
    timeZone: 'Asia/Shanghai',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  });
  genevaTime.value = now.toLocaleTimeString('en-US', {
    timeZone: 'Europe/Zurich',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  });
};

onMounted(() => {
  userRole.value = localStorage.getItem('role') || 'member';
  updateClocks();
  clockInterval = setInterval(updateClocks, 10000);
});

onUnmounted(() => {
  if (clockInterval) clearInterval(clockInterval);
});

const closeGroupModal = () => {
  showCreateGroupModal.value = false;
  newGroupName.value = '';
  newGroupDesc.value = '';
};

const handleCommitNewGroup = async () => {
  if (!newGroupName.value.trim()) return;
  try {
    await api.post('/auth/groups', {
      name: newGroupName.value.trim(),
      description: newGroupDesc.value.trim() || null
    });
    toast.success(`Research group [${newGroupName.value}] deployed!`);
    closeGroupModal();
    window.location.reload();
  } catch (error) {
    toast.error(error.response?.data?.detail || "Failed to deploy group.");
  }
};
</script>

<style scoped>
.global-sidebar { position: fixed; top: 64px; left: 0; bottom: 0; width: 240px; background: #ffffff; border-right: 1px solid #e2e8f0; padding: 24px 16px; box-sizing: border-box; display: flex; flex-direction: column; gap: 32px; z-index: var(--z-sticky); }
.team-selector-zone { display: flex; flex-direction: column; gap: 8px; text-align: left; }
.team-header-row { display: flex; justify-content: space-between; align-items: center; width: 100%; }
.sidebar-label { font-size: 11px; font-weight: 700; color: #94a3b8; letter-spacing: 0.5px; }
.btn-spawn-group-trigger { background: #f1f5f9; border: 1px solid #e2e8f0; color: #475569; font-size: 10px; width: 22px; height: 22px; border-radius: 4px; display: flex; align-items: center; justify-content: center; cursor: pointer; padding: 0; }
.btn-spawn-group-trigger:hover { background: #2563eb; color: #ffffff; border-color: #2563eb; }
.team-select-native { padding: 8px 12px; font-size: 14px; border: 1px solid #cbd5e1; border-radius: 6px; outline: none; background: #ffffff; width: 100%; color: #1e293b; font-weight: 600; cursor: pointer; }
.sidebar-nav-menu { display: flex; flex-direction: column; gap: 8px; }
.nav-item { display: flex; align-items: center; gap: 12px; padding: 10px 14px; border-radius: 8px; cursor: pointer; transition: all 0.2s; user-select: none; color: #475569; font-weight: 600; font-size: 14px; }
.nav-item:hover { background: #f1f5f9; color: #0f172a; }
.nav-item.active { background: #eff6ff; color: #2563eb; }
.nav-icon { font-size: 16px; }
.nav-text { flex: 1; text-align: left; }
.spawn-group-modal { background: #ffffff !important; width: 95% !important; max-width: 480px !important; border-radius: 12px !important; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25) !important; padding: 26px !important; box-sizing: border-box !important; }
/* 1. 团队选择器外层安全容器 */
.team-select-wrapper {
  position: relative;
  width: 100%;
}

/* 2. 彻底脱胎换骨的现代下拉框 (带颜色、文字居中) */
.modern-team-selector {
  width: 100%;
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  
  padding: 10px 16px;
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
  background: linear-gradient(135deg, var(--primary-color), #1d4ed8);
  
  border: none;
  border-radius: 8px;
  cursor: pointer;
  
  text-align: center;
  text-align-last: center;
  
  transition: all 0.2s ease;
  box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.15), 0 2px 4px -2px rgba(37, 99, 235, 0.15);
}
.modern-team-selector option {
  color: var(--text-main);
  background: #ffffff;
}

.modern-team-selector:hover {
  background: linear-gradient(135deg, #1d4ed8, #1e40af);
  box-shadow: 0 6px 8px -1px rgba(37, 99, 235, 0.25), 0 4px 6px -2px rgba(37, 99, 235, 0.25);
}

.modern-team-selector:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.4);
}

.sidebar-footer-menu {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.telemetry-clocks-panel {
  margin-top: auto;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-align: left;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.02);
}
.clock-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.clock-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
  letter-spacing: 0.5px;
}
.clock-time {
  font-family: var(--mono, monospace);
  font-size: 13.5px;
  font-weight: 700;
  color: var(--text-main);
}

/* Responsive sidebar and backdrop styles */
.sidebar-mobile-backdrop {
  display: none;
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  z-index: var(--z-overlay);
}

.btn-close-sidebar {
  display: none;
  position: absolute;
  top: 16px;
  right: 16px;
  background: transparent;
  border: none;
  font-size: 26px;
  color: var(--text-muted);
  cursor: pointer;
  line-height: 1;
}

@media (max-width: 767px) {
  .sidebar-mobile-backdrop {
    display: block;
  }
  .btn-close-sidebar {
    display: block;
  }
  .global-sidebar {
    position: fixed !important;
    top: 0;
    left: 0;
    height: 100vh;
    width: 240px;
    z-index: calc(var(--z-overlay) + 10);
    transform: translateX(-100%);
    transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    box-shadow: 10px 0 25px rgba(15, 23, 42, 0.15) !important;
  }
  .global-sidebar.is-open {
    transform: translateX(0);
  }
  .telemetry-clocks-panel {
    display: none !important; /* Hide clocks panel in mobile sidebar, already hidden in header */
  }
}
</style>