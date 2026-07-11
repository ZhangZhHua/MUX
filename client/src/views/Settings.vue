<template>
  <div class="settings-page-layout">
    <Header :userName="userName" :userRole="userRole" @logout="handleLogout" @toggle-sidebar="isSidebarOpen = !isSidebarOpen" />
    <Sidebar :groups="groups" :currentGroupId="currentGroupId" :isOpen="isSidebarOpen" @group-change="handleGroupChange" @close="isSidebarOpen = false" />

    <main class="settings-main-content">
      <div class="settings-container">
        <h2>⚙️ System Settings</h2>
        
        <!-- Tabs -->
        <div class="settings-tabs">
          <button class="tab-btn" :class="{ active: activeTab === 'trash' }" @click="activeTab = 'trash'">
            🗑️ Recycle Bin <span v-if="trashCount > 0" class="trash-count-badge">{{ trashCount }}</span>
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'general' }" @click="activeTab = 'general'">
            🔧 General
          </button>
        </div>

        <!-- Recycle Bin Tab -->
        <div class="tab-panel" v-if="activeTab === 'trash'">
          <div v-if="!isAdmin" class="permission-denied">
            <p>🔒 Only admins can access the recycle bin.</p>
          </div>

          <div v-else-if="loadingTrash" class="loading-state">
            <p>⏳ Loading recycle bin...</p>
          </div>

          <div v-else-if="trashExperiments.length === 0" class="empty-trash">
            <span class="empty-icon">🗑️</span>
            <h3>Recycle Bin is Empty</h3>
            <p>Deleted experiments will appear here for recovery.</p>
          </div>

          <div v-else class="trash-list">
            <div class="trash-header-row">
              <span>{{ trashExperiments.length }} deleted experiment(s) in recycle bin</span>
            </div>
            <div v-for="exp in trashExperiments" :key="exp.id" class="trash-item">
              <div class="trash-item-info">
                <h4>{{ exp.title }}</h4>
                <div class="trash-meta">
                  <span>🆔 #{{ exp.id }}</span>
                  <span v-if="exp.group">🏷️ {{ exp.group.name }}</span>
                  <span>🗑️ Deleted: {{ formatDate(exp.deleted_at) }}</span>
                  <span class="status-badge-sm" :class="exp.status">{{ exp.status }}</span>
                </div>
              </div>
              <div class="trash-item-actions">
                <button class="btn-restore" @click="restoreExperiment(exp.id)" :disabled="restoringId === exp.id">
                  {{ restoringId === exp.id ? '⏳' : '♻️' }} Restore
                </button>
                <button v-if="userRole === 'sys_admin'" class="btn-permanent-delete" @click="confirmPermanentDelete(exp)" :disabled="deletingId === exp.id">
                  {{ deletingId === exp.id ? '⏳' : '💀' }} Destroy Forever
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- General Tab (placeholder) -->
        <div class="tab-panel" v-if="activeTab === 'general'">
          <div class="settings-placeholder">
            <p>🔧 General configuration tools are under development.</p>
          </div>
        </div>

        <!-- Permanent Delete Confirmation Modal -->
        <Teleport to="body">
          <div class="modal-backdrop" v-if="showPermanentDeleteModal" @mousedown.self="mouseDownTarget = $event.target" @mouseup.self="mouseDownTarget === $event.currentTarget && closePermanentDeleteModal()">
            <div class="modal-box confirmation-modal">
              <div class="modal-header">
                <h3>⚠️ Permanent Deletion Confirmation</h3>
                <button class="btn-close-x" @click="closePermanentDeleteModal">&times;</button>
              </div>
              <div class="confirmation-body">
                <p>You are about to <strong style="color: #dc2626;">permanently destroy</strong> the experiment:</p>
                <p style="font-weight: 700; font-size: 16px; margin: 8px 0;">"{{ deletingExperiment?.title }}"</p>
                <p style="color: #dc2626; font-weight: 600;">This action is IRREVERSIBLE. All associated logs, bulletins, steps, and attachments will be permanently lost.</p>
              </div>
              <div class="modal-actions">
                <button class="btn-cancel" @click="closePermanentDeleteModal">Cancel</button>
                <button class="btn-submit" style="background: #dc2626 !important;" @click="executePermanentDelete">Yes, Destroy Forever</button>
              </div>
            </div>
          </div>
        </Teleport>
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
import { useToast } from '../composables/useToast';

const router = useRouter();
const toast = useToast();

const userName = ref('Researcher');
const userRole = ref('member');
const groups = ref([]);
const currentGroupId = ref(Number(localStorage.getItem('activeGroupId') || 0));
const isSidebarOpen = ref(false);

const activeTab = ref('trash');
const isAdmin = ref(false);
const loadingTrash = ref(false);
const trashExperiments = ref([]);
const trashCount = ref(0);
const restoringId = ref(null);
const deletingId = ref(null);

// Permanent delete modal
const showPermanentDeleteModal = ref(false);
const deletingExperiment = ref(null);
let mouseDownTarget = null;

onMounted(async () => {
  userName.value = localStorage.getItem('userName') || 'Researcher';
  userRole.value = localStorage.getItem('role') || 'member';
  isAdmin.value = userRole.value === 'sys_admin' || userRole.value === 'team_admin';
  
  try {
    const res = await api.get('/auth/me');
    userRole.value = res.data.role;
    isAdmin.value = userRole.value === 'sys_admin' || userRole.value === 'team_admin';
  } catch {}

  try {
    const response = await api.get('/auth/groups');
    groups.value = response.data;
  } catch {}
  
  if (isAdmin.value) {
    await fetchTrash();
  }
});

const fetchTrash = async () => {
  loadingTrash.value = true;
  try {
    const res = await api.get('/experiments/trash');
    trashExperiments.value = res.data;
    trashCount.value = res.data.length;
  } catch (err) {
    toast.error('Failed to load recycle bin.');
  }
  loadingTrash.value = false;
};

const restoreExperiment = async (id) => {
  restoringId.value = id;
  try {
    await api.put(`/experiments/${id}/restore`);
    toast.success('Experiment restored!');
    await fetchTrash();
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Failed to restore experiment.');
  }
  restoringId.value = null;
};

const confirmPermanentDelete = (exp) => {
  deletingExperiment.value = exp;
  showPermanentDeleteModal.value = true;
};

const closePermanentDeleteModal = () => {
  showPermanentDeleteModal.value = false;
  deletingExperiment.value = null;
  mouseDownTarget = null;
};

const executePermanentDelete = async () => {
  if (!deletingExperiment.value) return;
  deletingId.value = deletingExperiment.value.id;
  try {
    await api.delete(`/experiments/${deletingExperiment.value.id}/permanent`);
    toast.success('Experiment permanently destroyed.');
    showPermanentDeleteModal.value = false;
    deletingExperiment.value = null;
    await fetchTrash();
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Failed to permanently delete.');
  }
  deletingId.value = null;
};

const formatDate = (dateStr) => {
  if (!dateStr) return 'Unknown';
  const d = new Date(dateStr);
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
};

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
.settings-page-layout { height: 100%; overflow: hidden; background-color: var(--bg-primary); }
.settings-main-content { margin-top: 64px; margin-left: 240px; padding: 24px 32px; box-sizing: border-box; height: calc(100vh - 64px); overflow-y: auto; }

.settings-container { max-width: 900px; }
.settings-container h2 { margin: 0 0 20px; font-size: 22px; color: var(--text-main); }

.settings-tabs { display: flex; gap: 8px; margin-bottom: 20px; border-bottom: 1px solid var(--border-color); padding-bottom: 12px; }
.tab-btn { padding: 8px 20px; border: 1px solid var(--border-color); border-radius: 8px; background: #fff; font-size: 14px; font-weight: 600; color: #475569; cursor: pointer; transition: all 0.15s; }
.tab-btn:hover { background: #f1f5f9; color: #0f172a; }
.tab-btn.active { background: var(--primary-color); color: #fff; border-color: var(--primary-color); }
.trash-count-badge { background: #ef4444; color: #fff; font-size: 11px; padding: 1px 7px; border-radius: 99px; margin-left: 6px; }

.tab-panel { min-height: 300px; }
.permission-denied, .loading-state { text-align: center; padding: 60px 20px; color: var(--text-muted); font-size: 15px; }

.empty-trash { text-align: center; padding: 60px 20px; background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 12px; }
.empty-icon { font-size: 48px; display: block; margin-bottom: 12px; }
.empty-trash h3 { margin: 0 0 8px; font-size: 18px; color: var(--text-main); }
.empty-trash p { margin: 0; color: var(--text-muted); font-size: 14px; }

.trash-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-size: 13px; color: var(--text-muted); }

.trash-list { display: flex; flex-direction: column; gap: 10px; }
.trash-item { display: flex; justify-content: space-between; align-items: center; background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 10px; padding: 16px 20px; transition: box-shadow 0.15s; }
.trash-item:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
.trash-item-info h4 { margin: 0 0 6px; font-size: 15px; color: var(--text-main); }
.trash-meta { display: flex; gap: 16px; font-size: 12px; color: var(--text-muted); flex-wrap: wrap; align-items: center; }
.status-badge-sm { font-size: 11px; font-weight: 700; padding: 1px 8px; border-radius: 99px; }
.status-badge-sm.running { background: #dcfce7; color: #15803d; }
.status-badge-sm.paused { background: #fef9c3; color: #854d0e; }
.status-badge-sm.stopped { background: #fee2e2; color: #dc2626; }
.status-badge-sm.archived { background: #f1f5f9; color: #64748b; }

.trash-item-actions { display: flex; gap: 8px; flex-shrink: 0; }
.btn-restore { padding: 7px 16px; background: #dcfce7; border: 1px solid #bbf7d0; border-radius: 6px; color: #15803d; font-weight: 600; font-size: 13px; cursor: pointer; transition: all 0.15s; }
.btn-restore:hover { background: #bbf7d0; }
.btn-permanent-delete { padding: 7px 16px; background: #fef2f2; border: 1px solid #fee2e2; border-radius: 6px; color: #dc2626; font-weight: 600; font-size: 13px; cursor: pointer; transition: all 0.15s; }
.btn-permanent-delete:hover { background: #fee2e2; border-color: #fca5a5; }

/* Modal styles (reuse existing patterns) */
.modal-backdrop { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(15,23,42,0.45); backdrop-filter: blur(8px); display: flex; justify-content: center; align-items: center; z-index: var(--z-overlay, 1000); }
.modal-box { background: #fff; border-radius: 14px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.08); padding: 28px; box-sizing: border-box; animation: modal-slide-up 0.22s cubic-bezier(0.16,1,0.3,1); }
@keyframes modal-slide-up { from { opacity: 0; transform: translateY(10px) scale(0.98); } to { opacity: 1; transform: translateY(0) scale(1); } }
.confirmation-modal { max-width: 460px; text-align: left; }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.modal-header h3 { margin: 0; font-size: 17px; font-weight: 700; color: #0f172a; }
.btn-close-x { background: transparent; border: none; font-size: 22px; color: #94a3b8; cursor: pointer; }
.confirmation-body { font-size: 13.5px; line-height: 1.5; color: #334155; padding: 10px 0 20px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; }
.btn-cancel { padding: 8px 16px; background: #fff; border: 1px solid #cbd5e1; border-radius: 6px; color: #475569; font-weight: 600; font-size: 13px; cursor: pointer; }
.btn-submit { padding: 8px 18px; background: #2563eb; color: white; border: none; border-radius: 6px; font-weight: 600; font-size: 13px; cursor: pointer; }

.settings-placeholder { text-align: center; padding: 60px 20px; color: var(--text-muted); }

@media (max-width: 767px) {
  .settings-main-content { margin-left: 0; padding: 16px; }
  .trash-item { flex-direction: column; align-items: flex-start; gap: 12px; }
  .trash-item-actions { width: 100%; justify-content: flex-end; }
}
</style>
