<template>
  <div class="team-page-layout">
    <Header :userName="userName" :userRole="userRole" @logout="handleLogout" @toggle-sidebar="isSidebarOpen = !isSidebarOpen" />
    <Sidebar :groups="userGroups" :currentGroupId="activeGroupId" :isOpen="isSidebarOpen" @group-change="handleGroupChange" @close="isSidebarOpen = false" />

    <main class="team-main-content">
      <div class="team-container-box">
        
        <div class="team-view-banner">
          <div class="banner-left">
            <div class="group-scope-pack">
              <span class="group-scope-badge">🔬 Team: {{ activeGroupName }}</span>
            </div>
            <h2>Research Team Roster Workspace</h2>
            <p>Unified roster management and academic credential registry across collaborative nodes.</p>
          </div>
          <div class="banner-right">
            <span class="total-count-tag">👥 Current Scope: <strong>{{ memberList.length }}</strong> Researchers</span>
            <button v-if="isAdminUser && activeGroupId !== 0" class="btn-add-global-member" @click="openAddMemberModal">
              ➕ Add Team Member
            </button>
          </div>
        </div>

        <div class="members-card-grid" v-if="memberList.length > 0">
          <div 
            v-for="member in memberList" 
            :key="member.id" 
            class="member-profile-card"
            @click="inspectMemberDetails(member)"
          >
            <button 
              v-if="isAdminUser && activeGroupId !== 0 && member.email !== currentUserEmail" 
              class="btn-kick-member" 
              title="De-enroll this researcher from current group"
              @click.stop="executeFireMember(member.id)"
            >
              &times;
            </button>

            <div class="card-top-decorator" :class="member.role"></div>
            <div class="card-main-body">
              <div class="member-avatar-circle">
                <img v-if="member.avatar_node" :src="getAvatarStreamUrl(member.avatar_node)" class="avatar-img-fit" />
                <span v-else>👤</span>
              </div>
              <h3 class="member-fullname">{{ member.first_name }} {{ member.last_name }}</h3>
              <span class="role-indicator-badge" :class="member.role">{{ member.role }}</span>
              
              <div class="member-meta-lines">
                <p class="meta-line">🏢 <span>{{ member.institution || 'External Node' }}</span></p>
                <p class="meta-line">📧 <span class="email-text">{{ member.email }}</span></p>
              </div>
            </div>
            <div class="card-footer-bio">
              {{ member.academic_bio ? member.academic_bio : 'No research focus statement recorded yet.' }}
            </div>
          </div>
        </div>

        <div class="empty-team-state" v-else>
          <p>📡 Select a specific physical cluster group to display personnel nodes.</p>
        </div>
      </div>
    </main>

    <Teleport to="body">
      <div class="modal-backdrop" v-if="showDetailModal" @mousedown.self="mouseDownTarget = $event.target" @mouseup.self="mouseDownTarget === $event.currentTarget && closeDetailModal()" style="z-index: var(--z-overlay)">
        <div class="modal-box profile-center-modal">
          <div class="profile-modal-layout" v-if="selectedMember">
            <div class="profile-mini-sidebar">
              <div class="huge-avatar">
                <img v-if="selectedMember.avatar_node" :src="getAvatarStreamUrl(selectedMember.avatar_node)" class="avatar-img-fit-circle" />
                <span v-else>👤</span>
              </div>
              <h4>{{ selectedMember.first_name }} {{ selectedMember.last_name }}</h4>
              <p class="institution-sub">{{ selectedMember.institution || 'No Affiliation' }}</p>
              <span class="sidebar-role-tag" :class="selectedMember.role">{{ selectedMember.role.toUpperCase() }}</span>
              
              <button 
                class="btn-visit-homepage" 
                :disabled="!selectedMember.homepage_url"
                @click="openExternalHomepage(selectedMember.homepage_url)"
                :title="selectedMember.homepage_url ? 'Visit Portfolio' : 'No link registered'"
              >
                🌐 Visit Portfolio
              </button>
            </div>

            <div class="profile-main-form-stage">
              <div class="profile-stage-header">
                <h3>Researcher Credentials Summary</h3>
                <button class="btn-close-profile-x" @click="closeDetailModal">&times;</button>
              </div>

              <div class="profile-render-form">
                <div class="profile-form-group active-groups-pillbox">
                  <label>🧬 Affiliated Research Clusters (当前隶属团队)</label>
                  <div class="pill-rack" v-if="selectedMember.groups && selectedMember.groups.length > 0">
                    <span v-for="g in selectedMember.groups" :key="g.id" class="cluster-pill-node">
                      🔬 {{ g.name }}
                    </span>
                  </div>
                  <span v-else class="text-unassigned">Unassigned Roster</span>
                </div>

                <div class="form-grid-row">
                  <div class="profile-form-group flex-1">
                    <label>First Name</label>
                    <input type="text" :value="selectedMember.first_name" disabled class="input-disabled" />
                  </div>
                  <div class="profile-form-group flex-1">
                    <label>Last Name</label>
                    <input type="text" :value="selectedMember.last_name" disabled class="input-disabled" />
                  </div>
                </div>
                <div class="profile-form-group">
                  <label>Email Address</label>
                  <input type="email" :value="selectedMember.email" disabled class="input-disabled" />
                </div>
                <div class="profile-form-group">
                  <label>Portfolio Homepage Link</label>
                  <input type="text" :value="selectedMember.homepage_url || 'Not Registered'" disabled class="input-disabled" />
                </div>
                <div class="profile-form-group">
                  <label>Research Institution</label>
                  <input type="text" :value="selectedMember.institution || 'Not Configured'" disabled class="input-disabled" />
                </div>
                <div class="profile-form-group">
                  <label>Academic Bio</label>
                  <textarea rows="2" :value="selectedMember.academic_bio || 'No description summary added.'" disabled class="input-disabled"></textarea>
                </div>

                <div class="profile-form-group admin-control-segment" v-if="isAdminUser">
                  <div class="admin-control-header">
                    <label class="font-blue-highlight">🛡️ System Privilege Role Assignment</label>
                    <p class="admin-control-hint">Only role privilege is adjusted here. Membership scope and backend permissions remain unchanged.</p>
                  </div>
                  <div class="admin-control-row">
                    <select v-model="targetAssignRole" @change="executeRoleMutation(selectedMember.id, $event.target.value)" class="profile-select-active-admin">
                      <option v-if="userRole === 'sys_admin'" value="sys_admin">sys_admin (超级管理员)</option>
                      <option value="team_admin">team_admin (课题组主管/PI)</option>
                      <option value="member">member (值班研究员)</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <Teleport to="body">
      <div class="modal-backdrop" v-if="showAddMemberModal" @mousedown.self="mouseDownTarget = $event.target" @mouseup.self="mouseDownTarget === $event.currentTarget && closeAddMemberModal()" style="z-index: var(--z-overlay)">
        <div class="modal-box global-pool-picker-modal">
          <div class="modal-header">
            <div class="header-composite-title">
              <h3>Enlist Staff From Central Registry</h3>
              <p class="modal-subtitle-desc">Search and allocate qualified researchers into current cluster.</p>
            </div>
            <button class="btn-close-x" @click="closeAddMemberModal">&times;</button>
          </div>
          <div class="pool-search-container">
            <span class="search-lens">🔍</span>
            <input type="text" v-model="searchPoolQuery" placeholder="Filter candidates by name, school, email..." />
          </div>
          <div class="candidates-scroll-y" v-if="filteredAvailablePool.length > 0">
            <div v-for="cand in filteredAvailablePool" :key="cand.id" class="candidate-row-card">
              <div class="cand-left">
                <div class="cand-avatar">
                  <img v-if="cand.avatar_node" :src="getAvatarStreamUrl(cand.avatar_node)" class="avatar-img-fit-circle" />
                  <span v-else>👤</span>
                </div>
                <div class="cand-info">
                  <h4>{{ cand.first_name }} {{ cand.last_name }}</h4>
                  <p>📧 {{ cand.email }} | 🏢 {{ cand.institution || 'External Node' }}</p>
                </div>
              </div>
              <div class="cand-right">
                <button class="btn-action-recruit" @click="executeRecruitMember(cand.id)">➕ Enroll</button>
              </div>
            </div>
          </div>
          <div class="empty-pool-state" v-else>
            <p>🕊️ No unassigned candidates match your filter criteria.</p>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import api from '../services/api';
import { useToast } from '../composables/useToast';
import { useConfirmDialog } from '../composables/useConfirmDialog';
import Header from '../components/layout/Header.vue';
import Sidebar from '../components/layout/Sidebar.vue';

const toast = useToast();
const { confirm } = useConfirmDialog();
const userName = ref('');
const userRole = ref('');
const currentUserEmail = ref('');
const userGroups = ref([]);
const activeGroupId = ref(Number(localStorage.getItem('activeGroupId') || 0));
const memberList = ref([]);

let mouseDownTarget = null;
const isSidebarOpen = ref(false);

const activeGroupName = computed(() => {
  if (activeGroupId.value === 0) return 'All My Teams';
  const match = userGroups.value.find(g => g.id === activeGroupId.value);
  return match ? match.name : `Research Group #${activeGroupId.value}`;
});

const showDetailModal = ref(false);
const selectedMember = ref(null);
const targetAssignRole = ref('member');

const showAddMemberModal = ref(false);
const globalUserPool = ref([]);
const searchPoolQuery = ref('');

const isAdminUser = computed(() => userRole.value === 'sys_admin' || userRole.value === 'team_admin');

const filteredAvailablePool = computed(() => {
  const currentMemberIds = memberList.value.map(m => m.id);
  let available = globalUserPool.value.filter(u => !currentMemberIds.includes(u.id));
  const q = searchPoolQuery.value.trim().toLowerCase();
  if (q) {
    available = available.filter(u => `${u.first_name} ${u.last_name}`.toLowerCase().includes(q) || u.email.toLowerCase().includes(q));
  }
  return available;
});

onMounted(async () => {
  userName.value = localStorage.getItem('userName') || 'Researcher';
  userRole.value = localStorage.getItem('role') || 'member';
  currentUserEmail.value = localStorage.getItem('userEmail') || '';
  await fetchUserGroups();
});

const fetchUserGroups = async () => {
  try {
    const response = await api.get('/auth/groups');
    userGroups.value = response.data;
    if (activeGroupId.value !== 0 && !userGroups.value.some(g => g.id === activeGroupId.value)) {
      activeGroupId.value = userGroups.value.length > 0 ? userGroups.value[0].id : 0;
    }
    await fetchTeamRoster();
  } catch (error) {
    toast.error("Roster infrastructure alignment sync failed.");
  }
};

const handleGroupChange = async (groupId) => {
  activeGroupId.value = groupId;
  localStorage.setItem('activeGroupId', groupId);
  await fetchTeamRoster();
};

const fetchTeamRoster = async () => {
  try {
    if (activeGroupId.value === 0) {
      // 💡 聚合查看模式：全量拉取系统内全员（对齐上帝视角和多组展示）
      const response = await api.get('/auth/users');
      memberList.value = response.data;
    } else {
      const response = await api.get(`/experiments/groups/${activeGroupId.value}/members`);
      memberList.value = response.data;
    }
  } catch (error) {
    toast.error("Database roster streaming failed.");
  }
};

const openAddMemberModal = async () => {
  try {
    const response = await api.get('/auth/users');
    globalUserPool.value = response.data;
    searchPoolQuery.value = '';
    showAddMemberModal.value = true;
  } catch (error) {
    toast.error("Global directory stream error.");
  }
};

const closeAddMemberModal = () => { showAddMemberModal.value = false; };

const executeRecruitMember = async (userId) => {
  try {
    await api.post(`/auth/groups/${activeGroupId.value}/members`, { user_id: userId });
    toast.success("Scientist safely enrolled!");
    await fetchTeamRoster();
  } catch (error) {
    toast.error(error.response?.data?.detail || "Enrollment failed.");
  }
};

// ❌ 核心功能：在线剔除编制
const executeFireMember = async (userId) => {
  if (!(await confirm("Are you absolute sure you want to de-enroll this user from current group?"))) return;
  try {
    await api.delete(`/auth/groups/${activeGroupId.value}/members/${userId}`);
    toast.success("Scientist successfully removed from group roster.");
    await fetchTeamRoster();
  } catch (error) {
    toast.error(error.response?.data?.detail || "Eviction aborted.");
  }
};

const inspectMemberDetails = (member) => {
  selectedMember.value = member;
  targetAssignRole.value = member.role;
  showDetailModal.value = true;
};

const closeDetailModal = () => { showDetailModal.value = false; selectedMember.value = null; };

const executeRoleMutation = async (targetUserId, newRoleName) => {
  const roleLabels = {
    sys_admin: '超级管理员（sys_admin）',
    team_admin: '课题组主管（team_admin）',
    member: '值班研究员（member）'
  };
  if (!(await confirm(
    `确认将 ${selectedMember.value.first_name} ${selectedMember.value.last_name} ` +
    `的角色变更为「${roleLabels[newRoleName] || newRoleName}」？\n\n` +
    `权限将在确认后立即生效。`
  ))) return;
  try {
    await api.put(`/auth/users/${targetUserId}/role`, { role: newRoleName });
    toast.success("权限重配成功！");
    selectedMember.value.role = newRoleName;
    await fetchTeamRoster();
  } catch (error) {
    toast.error(error.response?.data?.detail || "权限变更请求被拒绝，请检查权限是否足够。");
  }
};

const getAvatarStreamUrl = (node) => `${api.defaults.baseURL}/experiments/attachments/${node}`;
const openExternalHomepage = (url) => { if (url) window.open(url.startsWith('http') ? url : `https://${url}`, '_blank'); };
const handleLogout = () => { localStorage.clear(); window.location.href = '/login'; };
</script>

<style scoped>
.team-page-layout { height: 100%; overflow: hidden; background-color: var(--bg-primary); }
.team-main-content {
  margin-top: 64px;
  margin-left: 240px;
  padding: 24px 32px;
  box-sizing: border-box;
  height: calc(100vh - 64px);
  overflow: hidden;
}

@media (max-width: 1023px) {
  .team-main-content {
    height: calc(100vh - 64px) !important;
    overflow-y: auto !important;
  }
  .team-container-box {
    height: auto !important;
    overflow-y: visible !important;
  }
  .members-card-grid {
    height: auto !important;
    overflow-y: visible !important;
    padding-right: 0 !important;
  }
}

@media (max-width: 767px) {
  .team-main-content {
    margin-left: 0 !important;
    padding: 16px !important;
  }
  .team-view-banner {
    flex-direction: column !important;
    align-items: stretch !important;
    gap: 16px !important;
  }
  .banner-right {
    flex-direction: column !important;
    align-items: stretch !important;
    gap: 10px !important;
  }
  .total-count-tag {
    text-align: center !important;
  }
  .members-card-grid {
    grid-template-columns: 1fr !important;
  }
  
  .profile-center-modal {
    width: 92% !important;
    height: auto !important;
    max-height: 90vh !important;
    overflow-y: auto !important;
  }
  .profile-modal-layout {
    flex-direction: column !important;
  }
  .profile-mini-sidebar {
    width: 100% !important;
    height: auto !important;
    border-right: none !important;
    border-bottom: 1px solid #e2e8f0;
    padding: 20px !important;
  }
  .profile-main-form-stage {
    padding: 20px !important;
    overflow-y: visible !important;
  }
}

.team-container-box {
  max-width: 1300px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
  height: 100%;
  min-height: 0;
}
.team-view-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 18px;
  text-align: left;
  flex-shrink: 0;
}
.team-view-banner h2 { margin: 0 0 4px 0; font-size: 24px; font-weight: 700; color: var(--text-main); letter-spacing: -0.5px; }
.team-view-banner p { margin: 0; font-size: 14px; color: var(--text-muted); }
.banner-right { display: flex; align-items: center; gap: 12px; }
.total-count-tag { background: #ffffff; border: 1px solid var(--border-color); font-size: 13px; font-weight: 600; color: #475569; padding: 7px 14px; border-radius: 20px; box-shadow: var(--shadow-sm); }
.btn-add-global-member { background: #2563eb; color: white; border: none; padding: 8px 16px; font-size: 13.5px; font-weight: 600; border-radius: 6px; cursor: pointer; box-shadow: 0 4px 6px -1px rgba(37,99,235,0.2); }
.btn-add-global-member:hover { background: #1d4ed8; }

.members-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding-right: 8px;
  align-content: start;
}
.members-card-grid::-webkit-scrollbar {
  width: 6px;
}
.members-card-grid::-webkit-scrollbar-track {
  background: transparent;
}
.members-card-grid::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}
.members-card-grid::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
.member-profile-card { background: #ffffff; border: 1px solid var(--border-color); border-radius: var(--radius-md); overflow: hidden; display: flex; flex-direction: column; box-shadow: var(--shadow-sm); position: relative; cursor: pointer; }
.member-profile-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }

/* 开除编制按钮悬浮显现效果 */
.btn-kick-member { position: absolute; top: 12px; right: 12px; width: 22px; height: 22px; background: rgba(239, 68, 68, 0.1); border: 1px solid #fca5a5; color: #ef4444; border-radius: 50%; font-size: 16px; display: flex; align-items: center; justify-content: center; cursor: pointer; z-index: 10; font-weight: bold; transition: all 0.15s; }
.btn-kick-member:hover { background: #ef4444; color: white; transform: scale(1.1); }

.card-top-decorator { height: 5px; width: 100%; background: #94a3b8; }
.card-top-decorator.sys_admin { background: #ef4444; }
.card-top-decorator.team_admin { background: #2563eb; }
.card-top-decorator.member { background: #10b981; }

.card-main-body { padding: 20px; flex: 1; display: flex; flex-direction: column; align-items: center; border-bottom: 1px solid #f1f5f9; }
.member-avatar-circle { width: 56px; height: 56px; background: #f1f5f9; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 12px; border: 1px solid #e2e8f0; overflow: hidden; font-size: 24px; }
.avatar-img-fit { width: 100%; height: 100%; object-fit: cover; }
.avatar-img-fit-circle { width: 100%; height: 100%; object-fit: cover; border-radius: 50%; }

.member-fullname { margin: 0 0 4px 0; font-size: 16px; font-weight: 700; color: #0f172a; }
.role-indicator-badge { font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; margin-bottom: 14px; }
.role-indicator-badge.sys_admin { background: #fee2e2; color: #ef4444; }
.role-indicator-badge.team_admin { background: #eff6ff; color: #2563eb; }
.role-indicator-badge.member { background: #ecfdf5; color: #10b981; }

.member-meta-lines { width: 100%; display: flex; flex-direction: column; gap: 4px; text-align: left; }
.meta-line { margin: 0; font-size: 12px; color: #475569; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.meta-line span { color: #1e293b; font-weight: 500; }
.email-text { font-family: monospace; color: #64748b !important; text-decoration: underline; }
.card-footer-bio { background: #f8fafc; padding: 10px 18px; font-size: 12px; color: #64748b; text-align: left; min-height: 32px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

/* 780px * 600px 独立卡片 */
.profile-center-modal { width: 95% !important; max-width: 780px !important; height: 600px !important; padding: 0 !important; overflow: hidden; border-radius: 14px !important; }
.profile-modal-layout { display: flex; height: 100%; }
.profile-mini-sidebar { width: 240px; background: #f8fafc; border-right: 1px solid #e2e8f0; padding: 32px 18px; box-sizing: border-box; display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-start; gap: 12px; }
.huge-avatar { width: 72px; height: 72px; background: #e2e8f0; border-radius: 50%; font-size: 32px; display: flex; align-items: center; justify-content: center; overflow: hidden; border: 1px solid #cbd5e1; }
.profile-mini-sidebar h4 { margin: 4px 0 0 0; font-size: 16px; font-weight: 700; color: #0f172a; }
.institution-sub { margin: 0; font-size: 12px; color: #64748b; text-align: center; }
.btn-visit-homepage { margin-top: auto; width: 100%; padding: 8px; border-radius: 6px; font-size: 12.5px; font-weight: 600; background: #ffffff; border: 1px solid #cbd5e1; color: #334155; cursor: pointer; }
.btn-visit-homepage:not(:disabled):hover { background: #f1f5f9; color: #2563eb; border-color: #2563eb; }
.btn-visit-homepage:disabled { background: #f1f5f9; color: #cbd5e1; cursor: not-allowed; }

.profile-main-form-stage { flex: 1; padding: 32px; box-sizing: border-box; display: flex; flex-direction: column; background: #ffffff; height: 100%; overflow-y: auto; }
.profile-stage-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.profile-stage-header h3 { margin: 0; font-size: 18px; font-weight: 700; color: #0f172a; }

.profile-render-form { display: flex; flex-direction: column; gap: 12px; text-align: left; }
.active-groups-pillbox { background: #fafbfc; border: 1px solid #e2e8f0; padding: 10px 14px; border-radius: 8px; }
.pill-rack { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; }
.cluster-pill-node { font-size: 11.5px; font-weight: 600; color: #0369a1; background: #e0f2fe; border: 1px solid #bae6fd; padding: 2px 8px; border-radius: 4px; }

.form-grid-row { display: flex; gap: 16px; }
.profile-form-group label { font-size: 12px; font-weight: 600; color: #475569; margin-bottom: 4px; display: block; }
.profile-form-group input, .profile-form-group textarea { padding: 8px 12px; font-size: 13.5px; border: 1px solid #cbd5e1; border-radius: 6px; outline: none; background: #ffffff; width: 100%; box-sizing: border-box; }
.admin-control-segment {
  margin-top: 4px;
  border: 1px solid var(--border-color);
  background: linear-gradient(180deg, #f8fbff 0%, #f3f8ff 100%);
  padding: 14px;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}
.admin-control-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 10px;
}
.font-blue-highlight {
  color: #1d4ed8;
  font-size: 12.5px;
  font-weight: 700;
}
.admin-control-hint {
  margin: 0;
  font-size: 12px;
  line-height: 1.45;
  color: var(--text-muted);
}
.admin-control-row {
  display: flex;
  align-items: center;
}
.profile-select-active-admin {
  width: 100%;
  min-height: 40px;
  border: 1px solid #bfdbfe;
  border-radius: 10px;
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
  background: #ffffff;
  box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.04);
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease;
  outline: none;
}
.profile-select-active-admin:hover {
  border-color: #93c5fd;
  background: #f8fbff;
}
.profile-select-active-admin:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.18);
}

/* 选拔大弹窗 */
.global-pool-picker-modal { width: 95% !important; max-width: 580px !important; border-radius: 14px !important; padding: 24px !important; box-sizing: border-box !important; background: #ffffff !important; }
.pool-search-container { display: flex; align-items: center; gap: 10px; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 14px; margin: 16px 0; }
.candidates-scroll-y { max-height: 260px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; border: 1px solid #e2e8f0; padding: 6px; border-radius: 8px; background: #fafbfc; }
.candidate-row-card { display: flex; justify-content: space-between; align-items: center; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px 12px; }
.cand-left { display: flex; align-items: center; gap: 12px; }
.cand-avatar { width: 40px; height: 40px; background: #f1f5f9; border-radius: 50%; display: flex; align-items: center; justify-content: center; overflow: hidden; border: 1px solid #e2e8f0; font-size: 18px; flex-shrink: 0; }
.cand-info { text-align: left; }
.cand-info h4 { margin: 0 0 2px 0; font-size: 14px; font-weight: 700; color: #0f172a; }
.cand-info p { margin: 0; font-size: 11px; color: #64748b; }

.group-scope-pack {
  margin-bottom: 8px;
}
.group-scope-badge {
  font-size: 11px;
  font-weight: 700;
  color: #2563eb;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  padding: 3px 10px;
  border-radius: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: inline-block;
}

@media (max-width: 768px) {
  .admin-control-segment {
    padding: 12px;
  }
  .admin-control-hint {
    font-size: 11.5px;
  }
  .profile-select-active-admin {
    min-height: 38px;
    font-size: 12.5px;
  }
}
</style>