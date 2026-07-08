<template>
  <div class="dashboard-layout">
    <Header :userName="userName" :userRole="userRole" @logout="handleLogout" />
    
    <Sidebar :groups="groups" :currentGroupId="currentGroupId" @group-change="handleGroupChange" />

    <main class="main-content">
      <div class="workspace-container">
        
        <div class="workspace-left">
          <div class="welcome-banner">
            <h2>Welcome back, {{ userName }}!</h2>
            <p>Unified data telemetry hub for collaborative physics logs.</p>
          </div>

          <div class="filter-matrix-bar">
            <div class="filter-controls-group">
              <!-- Tags Filter Row -->
              <div class="filter-row">
                <span class="filter-row-label">Tags</span>
                <div class="tags-cloud">
                  <span class="tag-pill" :class="{ active: selectedTag === null }" @click="handleTagFilter(null)">All Tags</span>
                  <span class="tag-pill" v-for="t in allAvailableTags" :key="t.id" :class="{ active: selectedTag === t.name }" @click="handleTagFilter(t.name)">
                    {{ t.name }}
                  </span>
                </div>
              </div>

              <!-- Status Filter Row -->
              <div class="filter-row">
                <span class="filter-row-label">Status</span>
                <div class="status-cloud">
                  <span class="status-pill" :class="{ active: selectedStatus === null }" @click="handleStatusFilter(null)">All Statuses</span>
                  <span class="status-pill" :class="{ active: selectedStatus === 'running' }" @click="handleStatusFilter('running')">🟢 Running</span>
                  <span class="status-pill" :class="{ active: selectedStatus === 'paused' }" @click="handleStatusFilter('paused')">🟡 Paused</span>
                  <span class="status-pill" :class="{ active: selectedStatus === 'stopped' }" @click="handleStatusFilter('stopped')">🔴 Stopped</span>
                  <span class="status-pill" :class="{ active: selectedStatus === 'archived' }" @click="handleStatusFilter('archived')">⚪ Archived</span>
                </div>
              </div>
            </div>
            
            <div class="action-buttons-wrapper" v-if="userRole !== 'member'">
              <button class="btn-tag-round" title="Add New Tag Globally" @click="showCreateTagModal = true">🏷️</button>
              <button class="btn-create-exp" :disabled="currentGroupId === 0" :title="currentGroupId === 0 ? 'Select a specific team to unlock creation' : ''" @click="openCreateExperimentModal">
                + New Experiment
              </button>
            </div>
          </div>

          <div class="experiment-grid" v-if="filteredExperiments.length > 0">
            <div v-for="exp in filteredExperiments" :key="exp.id" class="experiment-card" @click="router.push(`/experiment/${exp.id}`)">
              <div class="card-header">
                <div class="title-cluster-pack">
                  <span v-if="currentGroupId === 0" class="team-owner-badge" :class="getGroupBadgeClass(exp.group?.name)">{{ exp.group?.name ? 'Group ' + exp.group.name : 'Group PRC' }}</span>
                  <h3 class="exp-title">{{ exp.title }}</h3>
                </div>
                <span class="status-badge" :class="exp.status">{{ formatStatusText(exp.status) }}</span>
              </div>
              <p class="exp-summary">
                {{ formatSummary(exp.description) }}
              </p>
              <div class="card-tags">
                <span v-for="t in exp.tags" :key="t.id" class="hash-tag">{{ t.name }}</span>
              </div>
              <div class="card-footer">
                <span class="time-node-row">
                  <span>⏱️ Initialized: {{ formatTime(exp.created_at) }}</span>
                  <span class="divider-dot">•</span>
                  <span> Updated: {{ formatDateTime(exp.updated_at) }}</span>
                </span>
                <span>ID: <strong>#{{ exp.id }}</strong></span>
              </div>
            </div>
          </div>

          <div class="empty-state" v-else>
            <p>🔬 No operational logs synchronized under current cluster metrics.</p>
          </div>
        </div>

        <div class="workspace-right">
          <div class="intelligence-card alert-board-panel">
            <div class="intel-header">
              <h3>🔔 Live Bulletins & Notices</h3>
              <span class="pulse-red-dot"></span>
            </div>
            
            <div class="notices-scroller-box" v-if="noticeList.length > 0">
              <div 
                v-for="notice in noticeList" 
                :key="notice.id" 
                class="notice-node"
                :class="notice.type === 'system' ? 'system-broadcast-red' : 'team-broadcast-orange'"
              >
                <button 
                  v-if="isAdminUser && !(notice.type === 'system' && userRole !== 'sys_admin')"
                  class="btn-burn-notice"
                  title="Archive this notice from database"
                  @click.stop="executeKillNotice(notice.id)"
                >
                  &times;
                </button>

                <div class="notice-meta-line">
                  <span class="badge-tag" :class="notice.type">
                    {{ notice.type === 'team' && notice.group_name ? `TEAM: ${notice.group_name}` : notice.type.toUpperCase() }}
                  </span>
                  <span class="notice-author-ts">{{ notice.author_name }} · {{ formatTimeOnly(notice.created_at) }}</span>
                </div>
                <p class="notice-body-text">{{ notice.content }}</p>
              </div>
            </div>
            
            <div class="empty-notices-fallback" v-else>
              🕊️ All silent. No active warnings registered.
            </div>

            <div class="notice-quick-post-anchor" v-if="isAdminUser">
              <textarea 
                v-model="postNoticeInput" 
                rows="2" 
                :placeholder="userRole === 'sys_admin' ? 'Broadcast new system directive or team message...' : 'Post a message for today\'s shift operators...'"
                @keydown.enter.prevent="executeBroadcastNotice"
              ></textarea>
              
              <div class="post-action-subrow">
                <label class="sys-checkbox-lbl" v-if="userRole === 'sys_admin'">
                  <input type="checkbox" v-model="postNoticeIsSystem" /> 🚀 Global System-Wide
                </label>
                <span v-else class="team-lock-lbl">🔒 Posting into Team #{{ currentGroupId }}</span>
                
                <button class="btn-post-intel" :disabled="!postNoticeInput.trim() || (currentGroupId === 0 && !postNoticeIsSystem)" @click="executeBroadcastNotice">
                  Broadcast
                </button>
              </div>
            </div>
          </div>

          <div class="intelligence-card activity-timeline-panel">
            <div class="intel-header">
              <h3>📋 Recent Activities</h3>
              <button 
                class="btn-clear-ghost" 
                :class="{ 'is-loading': isSyncing }" 
                :disabled="isSyncing"
                @click="triggerManualSync"
              >
                🔄 Sync
              </button>
            </div>
            
            <div class="activity-timeline" v-if="activityList.length > 0">
              <div class="timeline-item" v-for="act in activityList" :key="act.id">
                <div class="time">⏱️ {{ formatDateTime(act.created_at) }}</div>
                <div class="desc">
                  <strong class="operator-name">{{ act.user_name }}</strong> 
                  <span class="action-highlight-verb">{{ act.action }}</span> 
                  <span class="text-blue-link">{{ act.target }}</span>
                </div>
              </div>
            </div>
            
            <div class="empty-notices-fallback" v-else>
              📡 Standing by. No active telemetry events cached.
            </div>
          </div>

          <!-- ℹ️ Help & Support Panel -->
          <div class="intelligence-card help-support-panel" style="margin-top: 16px;">
            <div class="intel-header">
              <h3>ℹ️ Help & Support</h3>
              <button 
                v-if="userRole === 'sys_admin'" 
                class="btn-clear-ghost"
                @click="toggleHelpEdit"
              >
                {{ isEditingHelp ? 'Cancel' : '✍️ Edit' }}
              </button>
            </div>
            
            <div class="help-info-content" v-if="!isEditingHelp" style="text-align: left; font-size: 13px; color: #475569; line-height: 1.5; white-space: pre-wrap;">
              {{ helpInfoText }}
            </div>
            
            <div class="help-info-edit-box" v-else style="display: flex; flex-direction: column; gap: 8px;">
              <textarea 
                v-model="editHelpInput" 
                rows="4" 
                style="width: 100%; font-size: 13px; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; outline: none; resize: vertical;"
                placeholder="Enter help and support contact info..."
              ></textarea>
              <div style="display: flex; justify-content: flex-end;">
                <button 
                  class="btn-post-intel" 
                  style="padding: 6px 12px; font-size: 12px;" 
                  @click="saveHelpInfo"
                >
                  Save settings
                </button>
              </div>
            </div>
          </div>
        </div>

      </div>
    </main>

    <Teleport to="body">
      <div class="modal-backdrop" v-if="showCreateTagModal" @click.self="closeTagModal">
        <div class="modal-box max-w-sm">
          <div class="modal-header">
            <h3>Add Global System Tag</h3>
            <button class="btn-close-x" @click="closeTagModal">&times;</button>
          </div>
          <form @submit.prevent="submitGlobalTag">
            <div class="modal-form-group">
              <label>New Tag Name</label>
              <input type="text" v-model="globalNewTagName" required placeholder="e.g., #Calibration" />
            </div>
            <div class="modal-actions">
              <button type="button" class="btn-cancel" @click="closeTagModal">Cancel</button>
              <button type="submit" class="btn-submit">Register Tag</button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <Teleport to="body">
      <div class="modal-backdrop" v-if="showCreateExperimentModal" @click.self="closeCreateExperimentModal">
        <div class="modal-box max-w-md" style="background: #ffffff; padding: 26px; border-radius: 12px;">
          <div class="modal-header">
            <h3>Create New Experiment Project</h3>
            <button class="btn-close-x" @click="closeCreateExperimentModal">&times;</button>
          </div>
          <form @submit.prevent="submitNewExperiment" class="modal-form-flow" style="text-align:left; display:flex; flex-direction:column; gap:14px; margin-top:10px;">
            <div class="modal-form-group">
              <label style="font-size: 13px; font-weight: 600; margin-bottom: 6px; display: block; color: #475569;">Experiment Title *</label>
              <input type="text" v-model="newExpTitle" required placeholder="e.g., Superconducting Qubit Calibration" style="padding: 8px 12px; font-size: 14px; border: 1px solid var(--border-color); border-radius: 6px; width: 100%; box-sizing: border-box;" />
            </div>
            <div class="modal-form-group">
              <label style="font-size: 13px; font-weight: 600; margin-bottom: 6px; display: block; color: #475569;">Document Format Type</label>
              <select v-model="newExpFormatType" style="padding: 8px 12px; font-size: 14px; border: 1px solid var(--border-color); border-radius: 6px; width: 100%; box-sizing: border-box; background: #fafbfc; cursor:pointer;">
                <option value="markdown">Markdown Mode</option>
                <option value="text">Plain Text Mode</option>
              </select>
            </div>
            <div class="modal-form-group">
              <label style="font-size: 13px; font-weight: 600; margin-bottom: 6px; display: block; color: #475569;">Initial Overview Description</label>
              <textarea v-model="newExpDesc" rows="4" placeholder="Describe initial beamline configurations or cryogenic targets..." style="padding: 8px 12px; font-size: 14px; border: 1px solid var(--border-color); border-radius: 6px; width: 100%; box-sizing: border-box; resize: vertical; outline:none;"></textarea>
            </div>
            <div class="modal-actions" style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 10px;">
              <button type="button" class="btn-cancel" @click="closeCreateExperimentModal">Cancel</button>
              <button type="submit" class="btn-submit" :disabled="!newExpTitle.trim()">Deploy Experiment</button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useConfirmDialog } from '../composables/useConfirmDialog';
import api from '../services/api';
import { useToast } from '../composables/useToast';
import Header from '../components/layout/Header.vue';
import Sidebar from '../components/layout/Sidebar.vue';

const router = useRouter();
const toast = useToast();
const { confirm } = useConfirmDialog();

const userName = ref('');
const userRole = ref('');
const groups = ref([]);
const experiments = ref([]);
const allAvailableTags = ref([]);
const currentGroupId = ref(Number(localStorage.getItem('activeGroupId') || 0));
const selectedTag = ref(null);
const selectedStatus = ref(null);

const filteredExperiments = computed(() => {
  if (!selectedStatus.value) return experiments.value;
  return experiments.value.filter(exp => exp.status === selectedStatus.value);
});
const getGroupBadgeClass = (groupName) => {
  if (!groupName) return 'badge-rpc';
  const name = groupName.toUpperCase();
  if (name.includes('RPC')) return 'badge-rpc';
  if (name.includes('HGTD')) return 'badge-hgtd';
  return 'badge-other';
};

const formatSummary = (desc) => {
  if (!desc) return 'No telemetry summary defined.';
  const lines = desc.split('\n').map(l => l.trim()).filter(l => l.length > 0);
  if (lines.length === 0) return 'No telemetry summary defined.';
  const firstLine = lines[0];
  const plainText = firstLine
    .replace(/#+\s+/g, '') // Headers
    .replace(/\*\*([^*]+)\*\*/g, '$1') // Bold
    .replace(/\*([^*]+)\*/g, '$1') // Italic
    .replace(/__([^_]+)__/g, '$1') // Bold under
    .replace(/_([^_]+)_/g, '$1') // Italic under
    .replace(/`([^`]+)`/g, '$1') // Inline code
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Links
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, '') // Images
    .replace(/^\s*[-*+]\s+/gm, '') // Bullet lists
    .replace(/^\s*\d+\.\s+/gm, '') // Numbered lists
    .trim();
  
  if (plainText.length <= 130) return plainText;
  return plainText.slice(0, 130) + '...';
};

const showCreateTagModal = ref(false);
const globalNewTagName = ref('');

// 真通知与真动态数据源状态机
const noticeList = ref([]);
const activityList = ref([]);
const postNoticeInput = ref('');
const postNoticeIsSystem = ref(false);

// Help & Support panel refs
const helpInfoText = ref('');
const isEditingHelp = ref(false);
const editHelpInput = ref('');

// 🆕 新增：创建实验专属响应式状态机
const showCreateExperimentModal = ref(false);
const newExpTitle = ref('');
const newExpDesc = ref('');
const newExpFormatType = ref('markdown');

const isAdminUser = computed(() => userRole.value === 'sys_admin' || userRole.value === 'team_admin');

onMounted(async () => {
  userName.value = localStorage.getItem('userName') || 'Researcher';
  userRole.value = localStorage.getItem('role') || 'member';
  await fetchUserGroups();
  await fetchSystemTags();
  await fetchHelpInfo();
});

const fetchUserGroups = async () => {
  try {
    const response = await api.get('/auth/groups');
    groups.value = response.data;
    if (currentGroupId.value !== 0 && !groups.value.some(g => g.id === currentGroupId.value)) {
      currentGroupId.value = 0;
      localStorage.setItem('activeGroupId', 0);
    }
    await refreshIntelligenceDeck();
  } catch (error) {
    toast.error("Failed to sync group communication arrays.");
  }
};

const handleGroupChange = async (groupId) => {
  currentGroupId.value = groupId;
  localStorage.setItem('activeGroupId', groupId);
  await refreshIntelligenceDeck();
};

const refreshIntelligenceDeck = async () => {
  try {
    let url = '/experiments';
    if (currentGroupId.value && currentGroupId.value !== 0) {
      url += `?group_id=${currentGroupId.value}`;
    }
    if (selectedTag.value) {
      url += url.includes('?') ? `&tag=${encodeURIComponent(selectedTag.value)}` : `?tag=${encodeURIComponent(selectedTag.value)}`;
    }
    const expRes = await api.get(url);
    experiments.value = expRes.data;

    await fetchLiveNotices();
    await fetchRecentActivities();
  } catch (error) {
    console.error("Telemetry frame sync aborted.");
  }
};

const fetchLiveNotices = async () => {
  try {
    const res = await api.get(`/experiments/intelligence/notices?group_id=${currentGroupId.value}`);
    noticeList.value = res.data;
  } catch (error) {}
};

const fetchRecentActivities = async () => {
  try {
    const res = await api.get(`/experiments/intelligence/activities?group_id=${currentGroupId.value}`);
    activityList.value = res.data;
  } catch (error) {}
};

const executeBroadcastNotice = async () => {
  if (!postNoticeInput.value.trim()) return;
  const noticeType = postNoticeIsSystem.value && userRole.value === 'sys_admin' ? 'system' : 'team';
  
  try {
    await api.post('/experiments/intelligence/notices', {
      type: noticeType,
      group_id: currentGroupId.value === 0 ? null : currentGroupId.value,
      content: postNoticeInput.value.trim()
    });
    toast.success("Broadcast directive integrated into PostgreSQL database cluster.");
    postNoticeInput.value = '';
    await fetchLiveNotices();
  } catch (error) {
    toast.error(error.response?.data?.detail || "Broadcast blocked.");
  }
};

const executeKillNotice = async (noticeId) => {
  if (!(await confirm("Are you sure you want to permanently erase this notice?"))) return;
  try {
    await api.delete(`/experiments/intelligence/notices/${noticeId}`);
    toast.success("Notice safely unlinked from central cluster.");
    await fetchLiveNotices();
  } catch (error) {
    toast.error(error.response?.data?.detail || "Deletion failed.");
  }
};

// 🆕 新增：实验创建弹窗的控制器函数与提交管道
const openCreateExperimentModal = () => {
  newExpTitle.value = '';
  newExpDesc.value = '';
  newExpFormatType.value = 'markdown';
  showCreateExperimentModal.value = true;
};

const closeCreateExperimentModal = () => {
  showCreateExperimentModal.value = false;
};

const submitNewExperiment = async () => {
  if (!newExpTitle.value.trim() || currentGroupId.value === 0) return;
  try {
    await api.post('/experiments', {
      title: newExpTitle.value.trim(),
      description: newExpDesc.value.trim(),
      format_type: newExpFormatType.value,
      group_id: currentGroupId.value,
      status: 'running'
    });
    toast.success("New experiment project deployed successfully!");
    closeCreateExperimentModal();
    await refreshIntelligenceDeck(); // 重新刷重大盘列表
  } catch (error) {
    toast.error(error.response?.data?.detail || "Failed to create experiment.");
  }
};

const fetchSystemTags = async () => {
  try {
    const response = await api.get('/experiments/tags');
    // Only display tags starting with '#' on the experiment dashboard
    allAvailableTags.value = response.data.filter(t => t.name && t.name.startsWith('#'));
  } catch (error) {}
};

const handleTagFilter = async (tag) => {
  selectedTag.value = tag;
  await refreshIntelligenceDeck();
};

const handleStatusFilter = (status) => {
  selectedStatus.value = status;
};

const closeTagModal = () => { showCreateTagModal.value = false; globalNewTagName.value = ''; };

const submitGlobalTag = async () => {
  let name = globalNewTagName.value.trim();
  if (!name) return;
  if (!name.startsWith('#')) name = `#${name}`;
  try {
    await api.post('/experiments/tags', { name: name });
    showCreateTagModal.value = false;
    globalNewTagName.value = '';
    await fetchSystemTags();
    await refreshIntelligenceDeck();
    toast.success(`Tag ${name} registered!`);
  } catch (error) {
    toast.error("Tag mapping error.");
  }
};

const fetchHelpInfo = async () => {
  try {
    const response = await api.get('/auth/system-settings/help_info');
    helpInfoText.value = response.data.value;
  } catch (error) {
    console.error("Failed to load help settings:", error);
  }
};

const toggleHelpEdit = () => {
  isEditingHelp.value = !isEditingHelp.value;
  if (isEditingHelp.value) {
    editHelpInput.value = helpInfoText.value;
  }
};

const saveHelpInfo = async () => {
  try {
    const response = await api.put('/auth/system-settings/help_info', {
      value: editHelpInput.value
    });
    helpInfoText.value = response.data.value;
    isEditingHelp.value = false;
    toast.success("Help support details reconfigured!");
  } catch (error) {
    toast.error("Failed to configure system settings.");
  }
};

const formatStatusText = (status) => {
  const map = { running: '🟢 Running', paused: '🟡 Paused', stopped: '🔴 Stopped', archived: '⚪ Archived' };
  return map[status] || '🟢 Running';
};

const parseUTC = (isoStr) => {
  if (!isoStr) return null;
  let formatted = isoStr;
  if (!isoStr.endsWith('Z') && !isoStr.includes('+') && !/-\d{2}:\d{2}$/.test(isoStr)) {
    formatted = isoStr + 'Z';
  }
  return new Date(formatted);
};

const formatTime = (iso) => {
  const d = parseUTC(iso);
  return d ? d.toLocaleDateString() : '';
};
const formatTimeOnly = (iso) => {
  const d = parseUTC(iso);
  if (!d) return '';
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  const hh = String(d.getHours()).padStart(2, '0');
  const min = String(d.getMinutes()).padStart(2, '0');
  return `${mm}-${dd} ${hh}:${min}`;
};
const handleLogout = () => { localStorage.clear(); router.push('/login'); };
const formatDateTime = (iso) => {
  const d = parseUTC(iso);
  if (!d) return '';
  const datePart = d.toLocaleDateString();
  const hh = String(d.getHours()).padStart(2, '0');
  const min = String(d.getMinutes()).padStart(2, '0');
  return `${datePart} ${hh}:${min}`;
};


const isSyncing = ref(false);

const triggerManualSync = async () => {
  if (isSyncing.value) return;
  isSyncing.value = true;
  
  try {
    // 物理拉取最新的后端持久化审计数据
    await fetchRecentActivities();
    toast.success("Activity re-synchronized!");
  } catch (error) {
    toast.error("Failed to sync.");
  } finally {
    // 持续 600 毫秒的优雅旋转动画后，释放状态
    setTimeout(() => {
      isSyncing.value = false;
    }, 600);
  }
};
</script>

<style scoped>
.dashboard-layout { height: 100%; overflow: hidden; background-color: var(--bg-primary); }
.main-content {
  margin-top: 64px;
  margin-left: 240px;
  padding: 24px 32px;
  box-sizing: border-box;
  height: calc(100vh - 64px);
  overflow: hidden;
}
.workspace-container {
  display: flex;
  gap: 28px;
  max-width: 1400px;
  margin: 0 auto;
  align-items: stretch;
  height: 100%;
}
.workspace-left {
  flex: 1;
  min-width: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.workspace-right {
  width: 340px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
  height: 100%;
  overflow-y: auto;
  padding-right: 4px;
}
.workspace-right::-webkit-scrollbar {
  width: 6px;
}
.workspace-right::-webkit-scrollbar-track {
  background: transparent;
}
.workspace-right::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}
.workspace-right::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.welcome-banner { text-align: left; flex-shrink: 0; }
.welcome-banner h2 { margin: 0 0 4px 0; font-size: 24px; font-weight: 700; color: var(--text-main); letter-spacing: -0.5px; }
.welcome-banner p { margin: 0; color: var(--text-muted); font-size: 14px; }

.filter-matrix-bar { display: flex; justify-content: space-between; align-items: flex-start; margin: 24px 0 16px 0; flex-shrink: 0; gap: 16px; }
.filter-controls-group { display: flex; flex-direction: column; gap: 10px; flex: 1; min-width: 0; }
.filter-row { display: flex; align-items: center; gap: 12px; }
.filter-row-label { font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; width: 54px; flex-shrink: 0; text-align: left; }
.tags-cloud { display: flex; gap: 6px; flex-wrap: wrap; }
.tag-pill { padding: 4px 10px; font-size: 12px; font-weight: 500; background: #ffffff; border: 1px solid var(--border-color); border-radius: 20px; cursor: pointer; color: var(--text-muted); transition: all 0.2s; }
.tag-pill.active, .tag-pill:hover { background: #0f172a; color: white; border-color: #0f172a; }

.status-cloud { display: flex; gap: 6px; flex-wrap: wrap; }
.status-pill { padding: 4px 10px; font-size: 12px; font-weight: 500; background: #ffffff; border: 1px solid var(--border-color); border-radius: 20px; cursor: pointer; color: var(--text-muted); transition: all 0.2s; }
.status-pill.active, .status-pill:hover { background: #0f172a; color: white; border-color: #0f172a; }

.action-buttons-wrapper { display: flex; align-items: center; gap: 8px; margin-top: 4px; }
.btn-tag-round { width: 34px; height: 34px; border-radius: 50%; background: #ffffff; border: 1px solid var(--border-color); font-size: 14px; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: var(--shadow-sm); }
.btn-create-exp { background: #2563eb; color: #fff; border: none; padding: 0 14px; font-size: 13px; font-weight: 600; border-radius: 6px; cursor: pointer; height: 34px; box-shadow: 0 2px 4px rgba(37,99,235,0.1); }
.btn-create-exp:disabled { background: #cbd5e1; color: #94a3b8; cursor: not-allowed; box-shadow: none; }

.experiment-grid {
  display: flex;
  flex-direction: column;
  gap: 14px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding-right: 8px;
}
.experiment-grid::-webkit-scrollbar {
  width: 6px;
}
.experiment-grid::-webkit-scrollbar-track {
  background: transparent;
}
.experiment-grid::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}
.experiment-grid::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.experiment-card { background: #ffffff; border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 18px; box-shadow: var(--shadow-sm); cursor: pointer; transition: all 0.2s; }
.experiment-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); border-color: #cbd5e1; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.title-cluster-pack { display: flex; align-items: center; gap: 8px; }

.team-owner-badge { font-size: 10px; font-weight: 700; color: #2563eb; background: #eff6ff; border: 1px solid #bfdbfe; padding: 1px 5px; border-radius: 4px; text-transform: uppercase; font-family: monospace; }
.team-owner-badge.badge-rpc { color: #2563eb; background: #eff6ff; border-color: #bfdbfe; }
.team-owner-badge.badge-hgtd { color: #059669; background: #ecfdf5; border-color: #a7f3d0; }
.team-owner-badge.badge-other { color: #7c3aed; background: #f5f3ff; border-color: #ddd6fe; }
.exp-title { margin: 0; font-size: 20px; font-weight: 800; color: #0f172a; text-align: left; }
.status-badge { font-size: 10px; font-weight: 600; padding: 2px 6px; border-radius: 4px; }
.status-badge.running { background: #ecfdf5; color: var(--success-color); }
.status-badge.paused { background: #fffbeb; color: #d97706; }
.status-badge.stopped { background: #fef2f2; color: #ef4444; }
.status-badge.archived { background: #f1f5f9; color: #64748b; }
.exp-summary { color: var(--text-muted); font-size: 13.5px; line-height: 1.5; margin: 0 0 12px 0; text-align: left; }
.card-tags { display: flex; gap: 6px; margin-bottom: 12px; }
.hash-tag { font-size: 11.5px; background: #f1f5f9; color: #475569; padding: 2px 6px; border-radius: 4px; font-weight: 500; }
.card-footer { display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: var(--text-muted); border-top: 1px solid #f1f5f9; padding-top: 10px; }
.time-node-row { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; text-align: left; }
.divider-dot { color: var(--text-muted); opacity: 0.5; }

.empty-state {
  text-align: center;
  padding: 50px;
  background: #ffffff;
  border: 1px dashed var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-muted);
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.intelligence-card { background: #ffffff; border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 18px; box-shadow: var(--shadow-sm); text-align: left; position: relative; }
.intel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; border-bottom: 1px solid #f1f5f9; padding-bottom: 8px; }
.intel-header h3 { margin: 0; font-size: 13.5px; font-weight: 700; color: #0f172a; text-transform: uppercase; letter-spacing: 0.5px; }
.pulse-red-dot { width: 8px; height: 8px; background: #ef4444; border-radius: 50%; box-shadow: 0 0 0 0 rgba(239, 64, 64, 0.4); animation: pulse 1.6s infinite; }
@keyframes pulse { 0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 64, 64, 0.5); } 70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(239, 64, 64, 0); } 100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 64, 64, 0); } }

.notices-scroller-box { display: flex; flex-direction: column; gap: 10px; max-height: 250px; overflow-y: auto; padding-right: 2px; }
.notice-node { border-radius: 6px; padding: 10px 12px; font-size: 13px; line-height: 1.4; border-left: 4px solid #94a3b8; position: relative; }
.notice-node:hover .btn-burn-notice { opacity: 1; }
.btn-burn-notice { position: absolute; top: 6px; right: 8px; background: transparent; border: none; color: #94a3b8; font-size: 16px; cursor: pointer; opacity: 0; transition: opacity 0.15s; font-weight: bold; }
.btn-burn-notice:hover { color: #dc2626; }

.system-broadcast-red { background: #fef2f2; border-color: #ef4444; }
.team-broadcast-orange { background: #fffbeb; border-color: #f59e0b; }
.notice-meta-line { display: flex; justify-content: space-between; align-items: center; font-size: 10.5px; font-weight: 700; margin-bottom: 4px; }
.badge-tag { padding: 1px 4px; border-radius: 3px; font-size: 9px; color: white; }
.badge-tag.system { background: #ef4444; }
.badge-tag.team { background: #f59e0b; }
.notice-author-ts { color: #64748b; font-family: sans-serif; }
.notice-body-text { margin: 0; color: #1e293b; font-weight: 500; word-break: break-all; }
.empty-notices-fallback { font-size: 12.5px; color: #94a3b8; padding: 24px 0; text-align: center; font-weight: 500; }

.notice-quick-post-anchor { margin-top: 14px; border-top: 1px dashed #e2e8f0; padding-top: 12px; display: flex; flex-direction: column; gap: 8px; }
.notice-quick-post-anchor textarea { width: 100%; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 10px; font-size: 12.5px; background: #fafbfc; outline: none; box-sizing: border-box; resize: none; }
.notice-quick-post-anchor textarea:focus { border-color: #2563eb; background: #ffffff; }
.post-action-subrow { display: flex; justify-content: space-between; align-items: center; }
.sys-checkbox-lbl { font-size: 11.5px; color: #dc2626; font-weight: 700; display: flex; align-items: center; gap: 4px; cursor: pointer; user-select: none; }
.sys-checkbox-lbl input { width: 14px; height: 14px; cursor: pointer; }
.team-lock-lbl { font-size: 11px; color: #64748b; font-weight: 600; }
.btn-post-intel { background: #0f172a; color: white; border: none; padding: 5px 12px; font-size: 12px; font-weight: 600; border-radius: 4px; cursor: pointer; }
.btn-post-intel:disabled { background: #e2e8f0; color: #94a3b8; cursor: not-allowed; }

.activity-timeline-panel { background: #ffffff; }
.btn-clear-ghost { background: transparent; border: none; color: #2563eb; font-size: 12px; font-weight: 600; cursor: pointer; padding: 0; }
.activity-timeline { display: flex; flex-direction: column; gap: 12px; max-height: 380px; overflow-y: auto; }
.timeline-item { font-size: 12.5px; line-height: 1.4; border-left: 2px solid #e2e8f0; padding-left: 10px; position: relative; margin-left: 4px; text-align: left; }
.timeline-item .time { font-size: 10.5px; color: #94a3b8; font-weight: 600; margin-bottom: 2px; }
.action-highlight-verb { color: #0284c7; font-weight: 600; font-style: italic; }
.text-blue-link { color: #1e293b; font-weight: 700; font-family: monospace; background: #f1f5f9; padding: 1px 4px; border-radius: 3px; }

/* ==========================================================================
   🆕 完美化整容：双子星弹窗高级 SaaS 视觉规范样式
   ========================================================================== */

/* 1. 遮罩层：全屏高级感高斯模糊 */
.modal-backdrop {
  position: fixed !important;
  top: 0 !important; left: 0 !important;
  width: 100vw !important; height: 100vh !important;
  background: rgba(15, 23, 42, 0.45) !important; /* 电影级微暗遮罩 */
  backdrop-filter: blur(8px) !important;
  -webkit-backdrop-filter: blur(8px) !important;
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  z-index: var(--z-overlay) !important;
}

/* 2. 弹窗本体卡片：白净、圆润、重度悬浮阴影，附带优雅的淡入微动画 */
.modal-box {
  background: #ffffff !important;
  border-radius: 14px !important;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.08), 0 10px 10px -5px rgba(0, 0, 0, 0.03) !important;
  padding: 28px !important;
  box-sizing: border-box !important;
  animation: modal-slide-up 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}
.max-w-sm { width: 92% !important; max-width: 400px !important; }
.max-w-md { width: 92% !important; max-width: 500px !important; }

@keyframes modal-slide-up {
  from { opacity: 0; transform: translateY(10px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

/* 3. 弹窗头部精细排版 */
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.modal-header h3 {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.3px;
}
.btn-close-x {
  background: transparent; border: none; font-size: 22px;
  color: #94a3b8; cursor: pointer; padding: 0; line-height: 1;
}
.btn-close-x:hover { color: #475569; }

/* 4. 表单流式布局与无国界高级输入框/下拉菜单 */
.modal-form-flow {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.modal-form-group {
  display: flex;
  flex-direction: column;
  text-align: left;
}
.modal-form-group label {
  font-size: 12.5px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 6px;
}
.modal-form-group input, 
.modal-form-group textarea,
.modal-form-group select {
  padding: 10px 14px !important;
  font-size: 13.5px !important;
  border: 1px solid #cbd5e1 !important;
  border-radius: 8px !important;
  outline: none !important;
  background: #ffffff !important;
  color: #1e293b !important;
  box-sizing: border-box !important;
  transition: all 0.15s ease;
}

/* 呼吸聚焦蓝光圈（Linear风格） */
.modal-form-group input:focus,
.modal-form-group textarea:focus,
.modal-form-group select:focus {
  border-color: #2563eb !important;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
}

/* 5. 按钮精细化控制（消灭生硬的原始色块） */
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 10px;
}
.btn-cancel {
  padding: 8px 16px !important;
  background: #ffffff !important;
  border: 1px solid #cbd5e1 !important;
  border-radius: 6px !important;
  color: #475569 !important;
  font-weight: 600 !important;
  font-size: 13px !important;
  cursor: pointer !important;
  transition: all 0.1s;
}
.btn-cancel:hover {
  background: #f1f5f9 !important;
  color: #0f172a !important;
}
.btn-submit {
  padding: 8px 18px !important;
  background: #2563eb !important;
  color: white !important;
  border: none !important;
  border-radius: 6px !important;
  font-weight: 600 !important;
  font-size: 13px !important;
  cursor: pointer !important;
  box-shadow: 0 2px 4px rgba(37, 99, 235, 0.15) !important;
  transition: all 0.1s;
}
.btn-submit:hover:not(:disabled) {
  background: #1d4ed8 !important;
}
/* 极具工业美感的置灰禁用态（防止未填标题误触） */
.btn-submit:disabled {
  background: #f1f5f9 !important;
  color: #cbd5e1 !important;
  cursor: not-allowed !important;
  box-shadow: none !important;
  border: 1px solid #e2e8f0 !important;
}
/* ==========================================================================
   🎨 实验室动态（Recent Activities）现代化重构样式
   ========================================================================== */
.activity-timeline-panel {
  background: #ffffff;
}

.activity-timeline {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 380px;
  overflow-y: auto;
  padding-top: 4px;
}

/* 现代化精细时间轴单项 */
.timeline-item {
  font-size: 13px;
  line-height: 1.5;
  border-left: 2px solid #e2e8f0; /* 清爽的时间轴垂线 */
  padding-left: 18px; /* 腾出黄金间距 */
  position: relative;
  margin-left: 6px;
  text-align: left;
  padding-bottom: 16px;
}

/* 🆕 核心设计：利用伪元素，在时间轴左侧绘制一个精致的互动的空心科研锚点 */
.timeline-item::before {
  content: "";
  position: absolute;
  left: -5px; /* 精准卡在垂线上 */
  top: 5px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #cbd5e1;
  border: 2px solid #ffffff; /* 白色外圈切边隔开垂线 */
  transition: all 0.2s ease;
}

/* 灵动的悬浮呼吸高亮微交互 */
.timeline-item:hover::before {
  background: #2563eb; /* 悬浮时小圆点亮起物理蓝 */
  transform: scale(1.1);
}

.timeline-item .time {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 600;
  margin-bottom: 3px;
  letter-spacing: 0.2px;
}

/* 操作员姓名卡片 */
.operator-name {
  color: #0f172a;
  font-weight: 700;
}

/* ⚡ 核心修复：彻底解决名字与动词、动词与目标挤在一起的排版硬伤 */
.action-highlight-verb {
  color: #0284c7; /* 极具科技感的浅蓝色 */
  font-weight: 500;
  font-style: normal; /* 扔掉倾斜，采用扁平化现代 SaaS 字体体感 */
  margin: 0 5px; /* ⚡ 左右强行撑开 5 像素黄金呼吸安全距，绝不拥挤 */
}

/* 目标实验标签小胶囊（完美剔除生硬的 monospace，对接全局视觉层级） */
.text-blue-link {
  color: #1e293b;
  font-weight: 600;
  font-family: inherit; /* 继承系统优雅的无衬线字体 */
  background: #f1f5f9; /* 极其柔和的背景衬底 */
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  display: inline-block;
  box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
.btn-clear-ghost {
  background: transparent;
  border: none;
  color: #2563eb;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: color 0.15s ease;
}

.btn-clear-ghost:hover:not(:disabled) {
  color: #1d4ed8;
}

/* 🆕 核心新增：当激活同步时，按钮变灰且里面的 🔄 图标疯狂但优雅地转圈 */
.btn-clear-ghost.is-loading {
  color: #94a3b8 !important;
  cursor: not-allowed;
}

.btn-clear-ghost.is-loading::before {
  /* 如果你想让文字前的图标旋转，可以在这里对特定的 emoji 挂载动画 */
}

/* 针对整个按钮或内部文字应用旋转（最简单直接的方式是让整个 Sync 文字/图标震颤旋转） */
.btn-clear-ghost.is-loading {
  animation: btn-spin-subtle 0.6s linear infinite;
}

@keyframes btn-spin-subtle {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>