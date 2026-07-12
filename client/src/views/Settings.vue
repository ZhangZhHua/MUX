<template>
  <div class="settings-page-layout">
    <Header :userName="userName" :userRole="userRole" @logout="handleLogout" @toggle-sidebar="isSidebarOpen = !isSidebarOpen" />
    <Sidebar :groups="groups" :currentGroupId="currentGroupId" :isOpen="isSidebarOpen" @group-change="handleGroupChange" @close="isSidebarOpen = false" />

    <main class="settings-main-content">
      <div class="settings-container">
        <h2>⚙️ {{ t('settings.title') }}</h2>

        <!-- Tabs -->
        <div class="settings-tabs">
          <button class="tab-btn" :class="{ active: activeTab === 'general' }" @click="activeTab = 'general'">🔧 {{ t('settings.general') }}</button>
          <button class="tab-btn" :class="{ active: activeTab === 'approval' }" @click="activeTab = 'approval'" v-if="isAdmin">
            👥 {{ t('settings.pendingUsers') }} <span v-if="pendingCount > 0" class="pending-badge">{{ pendingCount }}</span>
          </button>
          <button class="tab-btn" :class="{ active: activeTab === 'trash' }" @click="activeTab = 'trash'" v-if="isAdmin">
            🗑️ {{ t('settings.recycleBin') }} <span v-if="trashCount > 0" class="trash-count-badge">{{ trashCount }}</span>
          </button>
        </div>

        <!-- ===== General Settings Tab ===== -->
        <div class="tab-panel" v-if="activeTab === 'general'">
          <div class="settings-card">
            <h3>🎨 {{ t('settings.darkMode') }}</h3>
            <div class="theme-selector">
              <button class="theme-option" :class="{ active: theme === 'light' }" @click="setTheme('light')">☀️ Light</button>
              <button class="theme-option" :class="{ active: theme === 'dark' }" @click="setTheme('dark')">🌙 Dark</button>
              <button class="theme-option" :class="{ active: theme === 'system' }" @click="setTheme('system')">💻 System</button>
            </div>
          </div>

          <div class="settings-card">
            <h3>🌐 {{ t('settings.language') }}</h3>
            <select v-model="lang" @change="setLocale(lang)" class="settings-select">
              <option value="en">🇺🇸 English</option>
              <option value="zh-CN">🇨🇳 中文</option>
            </select>
          </div>

          <div class="settings-card">
            <h3>⏱️ {{ t('settings.sessionTimeout') }}</h3>
            <div class="timeout-row">
              <select v-model="sessionTimeoutMode" @change="onTimeoutModeChange" class="settings-select" style="min-width: 180px;">
                <option value="never">🔓 Never (no timeout)</option>
                <option value="30">30 minutes</option>
                <option value="60">1 hour</option>
                <option value="120">2 hours</option>
                <option value="240">4 hours</option>
                <option value="480">8 hours</option>
                <option value="custom">Custom...</option>
              </select>
              <input v-if="sessionTimeoutMode === 'custom'" type="number" v-model.number="sessionTimeout" min="5" max="10080" class="settings-input" placeholder="min" />
              <button class="btn-save-sm" @click="saveSessionTimeout">Save</button>
            </div>
          </div>

          <div class="settings-card" v-if="userRole === 'sys_admin'">
            <h3>👥 {{ t('settings.requireApproval') }}</h3>
            <label class="toggle-switch">
              <input type="checkbox" v-model="requireApproval" @change="saveApprovalSetting" />
              <span class="toggle-slider"></span>
              <span class="toggle-label">{{ requireApproval ? 'ON — new users need approval' : 'OFF — instant registration' }}</span>
            </label>
          </div>
        </div>

        <!-- ===== Pending Approvals Tab ===== -->
        <div class="tab-panel" v-if="activeTab === 'approval' && isAdmin">
          <div v-if="loadingPending" class="loading-state">⏳ Loading...</div>
          <div v-else-if="pendingUsers.length === 0" class="empty-state">{{ t('settings.noPending') }}</div>
          <div v-else class="pending-list">
            <div v-for="user in pendingUsers" :key="user.id" class="pending-item">
              <div class="pending-info">
                <strong>{{ user.first_name }} {{ user.last_name }}</strong>
                <span class="pending-email">{{ user.email }}</span>
                <span class="pending-institution" v-if="user.institution">{{ user.institution }}</span>
              </div>
              <div class="pending-actions">
                <button class="btn-approve" @click="approveUser(user.id)">✅ {{ t('settings.approve') }}</button>
                <button class="btn-reject-sm" @click="rejectUser(user.id)">❌ {{ t('settings.reject') }}</button>
              </div>
            </div>
          </div>
        </div>

        <!-- ===== Recycle Bin Tab ===== -->
        <div class="tab-panel" v-if="activeTab === 'trash' && isAdmin">
          <div v-if="loadingTrash" class="loading-state">⏳ Loading recycle bin...</div>
          <div v-else-if="trashExperiments.length === 0" class="empty-state">
            <span class="empty-icon">🗑️</span>
            <h3>{{ t('settings.emptyTrash') }}</h3>
          </div>
          <div v-else class="trash-list">
            <div class="trash-header-row">{{ trashExperiments.length }} deleted experiment(s)</div>
            <div v-for="exp in trashExperiments" :key="exp.id" class="trash-item">
              <div class="trash-item-info">
                <h4>{{ exp.title }}</h4>
                <div class="trash-meta">
                  <span>🆔 #{{ exp.id }}</span><span v-if="exp.group">🏷️ {{ exp.group.name }}</span><span>🗑️ {{ formatDate(exp.deleted_at) }}</span>
                </div>
              </div>
              <div class="trash-item-actions">
                <button class="btn-restore" @click="restoreExperiment(exp.id)" :disabled="restoringId === exp.id">♻️ {{ t('settings.restore') }}</button>
                <button v-if="userRole === 'sys_admin'" class="btn-permanent-delete" @click="confirmPermanentDelete(exp)" :disabled="deletingId === exp.id">💀 {{ t('settings.permanentDelete') }}</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Permanent Delete Confirmation -->
        <Teleport to="body">
          <div class="modal-backdrop" v-if="showPermanentDeleteModal" @mousedown.self="mouseDownTarget = $event.target" @mouseup.self="mouseDownTarget === $event.currentTarget && closePermanentDeleteModal()">
            <div class="modal-box confirmation-modal">
              <div class="modal-header"><h3>⚠️ Permanent Deletion</h3><button class="btn-close-x" @click="closePermanentDeleteModal">&times;</button></div>
              <div class="confirmation-body"><p>Permanently destroy <strong style="color: #dc2626;">"{{ deletingExperiment?.title }}"</strong>? This is IRREVERSIBLE.</p></div>
              <div class="modal-actions"><button class="btn-cancel" @click="closePermanentDeleteModal">Cancel</button><button class="btn-submit" style="background: #dc2626 !important;" @click="executePermanentDelete">Destroy</button></div>
            </div>
          </div>
        </Teleport>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Header from '../components/layout/Header.vue'
import Sidebar from '../components/layout/Sidebar.vue'
import api from '../services/api'
import { useToast } from '../composables/useToast'
import { useTheme } from '../composables/useTheme'
import { useI18n } from '../composables/useI18n'

const router = useRouter()
const toast = useToast()
const { theme, setTheme } = useTheme()
const { t, currentLocale, setLocale } = useI18n()

const lang = ref(currentLocale.value)

const userName = ref('Researcher')
const userRole = ref('member')
const isAdmin = ref(false)
const groups = ref([])
const currentGroupId = ref(Number(localStorage.getItem('activeGroupId') || 0))
const isSidebarOpen = ref(false)
const activeTab = ref('general')

// General settings
const sessionTimeout = ref(120)
const sessionTimeoutMode = ref('120')
const requireApproval = ref(false)

// Pending users
const pendingUsers = ref([])
const pendingCount = ref(0)
const loadingPending = ref(false)

// Recycle bin
const loadingTrash = ref(false)
const trashExperiments = ref([])
const trashCount = ref(0)
const restoringId = ref(null)
const deletingId = ref(null)
const showPermanentDeleteModal = ref(false)
const deletingExperiment = ref(null)
let mouseDownTarget = null

onMounted(async () => {
  userName.value = localStorage.getItem('userName') || 'Researcher'
  userRole.value = localStorage.getItem('role') || 'member'
  isAdmin.value = userRole.value === 'sys_admin' || userRole.value === 'team_admin'

  try { const res = await api.get('/auth/me'); userRole.value = res.data.role; isAdmin.value = userRole.value === 'sys_admin' || userRole.value === 'team_admin' } catch {}
  try { groups.value = (await api.get('/auth/groups')).data } catch {}

  // Load settings
  try { const t = parseInt((await api.get('/auth/system-settings/session_timeout')).data.value) || 120; sessionTimeout.value = t; sessionTimeoutMode.value = t >= 10000 ? 'never' : String(t) } catch {}
  try { requireApproval.value = (await api.get('/auth/system-settings/require_approval')).data.value === 'true' } catch {}

  if (isAdmin.value) {
    await fetchPendingUsers()
    await fetchTrash()
  }
})

const onTimeoutModeChange = () => {
  const map = { never: 99999, 30: 30, 60: 60, 120: 120, 240: 240, 480: 480 }
  if (sessionTimeoutMode.value !== 'custom') {
    sessionTimeout.value = map[sessionTimeoutMode.value] || 120
    saveSessionTimeout()
  }
}

const saveSessionTimeout = async () => {
  try { await api.put('/auth/system-settings/session_timeout', { value: String(sessionTimeout.value) }); toast.success('Session timeout saved.') } catch { toast.error('Failed to save.') }
}

const saveApprovalSetting = async () => {
  try { await api.put('/auth/system-settings/require_approval', { value: requireApproval.value ? 'true' : 'false' }); toast.success('Approval setting saved.') } catch { toast.error('Failed to save.') }
}

const fetchPendingUsers = async () => {
  loadingPending.value = true
  try { const res = await api.get('/auth/users/pending'); pendingUsers.value = res.data; pendingCount.value = res.data.length } catch { /* 403 if not admin */ }
  loadingPending.value = false
}

const approveUser = async (id) => {
  try { await api.put(`/auth/users/${id}/approve`); toast.success('User approved!'); await fetchPendingUsers() } catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
}

const rejectUser = async (id) => {
  try { await api.put(`/auth/users/${id}/reject`); toast.success('User rejected.'); await fetchPendingUsers() } catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
}

const fetchTrash = async () => { loadingTrash.value = true; try { const r = await api.get('/experiments/trash'); trashExperiments.value = r.data; trashCount.value = r.data.length } catch {} loadingTrash.value = false }
const restoreExperiment = async (id) => { restoringId.value = id; try { await api.put(`/experiments/${id}/restore`); toast.success('Restored!'); await fetchTrash() } catch (e) { toast.error(e.response?.data?.detail || 'Failed') } restoringId.value = null }
const confirmPermanentDelete = (exp) => { deletingExperiment.value = exp; showPermanentDeleteModal.value = true }
const closePermanentDeleteModal = () => { showPermanentDeleteModal.value = false; deletingExperiment.value = null }
const executePermanentDelete = async () => { if (!deletingExperiment.value) return; deletingId.value = deletingExperiment.value.id; try { await api.delete(`/experiments/${deletingExperiment.value.id}/permanent`); toast.success('Destroyed.'); showPermanentDeleteModal.value = false; deletingExperiment.value = null; await fetchTrash() } catch (e) { toast.error('Failed') } deletingId.value = null }

const formatDate = (d) => d ? new Date(d).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : 'Unknown'
const handleGroupChange = (gid) => { currentGroupId.value = gid; localStorage.setItem('activeGroupId', gid) }
const handleLogout = () => { localStorage.clear(); router.push('/login') }
</script>

<style scoped>
.settings-page-layout { height: 100%; overflow: hidden; background-color: var(--bg-primary); }
.settings-main-content { margin-top: 64px; margin-left: 240px; padding: 24px 32px; box-sizing: border-box; height: calc(100vh - 64px); overflow-y: auto; }
.settings-container { max-width: 900px; }
.settings-container h2 { margin: 0 0 20px; font-size: 22px; color: var(--text-main); }

.settings-tabs { display: flex; gap: 8px; margin-bottom: 20px; border-bottom: 1px solid var(--border-color); padding-bottom: 12px; }
.tab-btn { padding: 8px 20px; border: 1px solid var(--border-color); border-radius: 8px; background: var(--bg-surface); font-size: 14px; font-weight: 600; color: var(--text-muted); cursor: pointer; transition: all 0.15s; }
.tab-btn:hover { background: #f1f5f9; color: var(--text-main); }
.tab-btn.active { background: var(--primary-color); color: #fff; border-color: var(--primary-color); }
.trash-count-badge, .pending-badge { background: #ef4444; color: #fff; font-size: 11px; padding: 1px 7px; border-radius: 99px; margin-left: 6px; }

.tab-panel { min-height: 300px; }
.loading-state, .empty-state { text-align: center; padding: 60px 20px; color: var(--text-muted); font-size: 15px; }
.empty-icon { font-size: 48px; display: block; margin-bottom: 12px; }

/* Settings Card */
.settings-card { background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 10px; padding: 20px; margin-bottom: 16px; }
.settings-card h3 { margin: 0 0 16px; font-size: 15px; color: var(--text-main); }

.theme-selector { display: flex; gap: 8px; }
.theme-option { padding: 8px 20px; border: 1px solid var(--border-color); border-radius: 8px; background: var(--bg-surface); font-size: 14px; cursor: pointer; color: var(--text-muted); font-weight: 600; transition: all 0.15s; }
.theme-option:hover { border-color: var(--primary-color); }
.theme-option.active { background: var(--primary-color); color: #fff; border-color: var(--primary-color); }

.settings-select { padding: 10px 14px; border: 1px solid var(--border-color); border-radius: 8px; font-size: 14px; background: var(--bg-surface); color: var(--text-main); min-width: 200px; outline: none; }

.timeout-row { display: flex; align-items: center; gap: 12px; }
.settings-input { width: 80px; padding: 8px 12px; border: 1px solid var(--border-color); border-radius: 8px; font-size: 14px; text-align: center; outline: none; background: var(--bg-surface); color: var(--text-main); }
.timeout-label { font-size: 13px; color: var(--text-muted); }
.btn-save-sm { padding: 6px 14px; background: var(--primary-color); color: #fff; border: none; border-radius: 6px; font-size: 13px; cursor: pointer; }

/* Toggle Switch */
.toggle-switch { display: flex; align-items: center; gap: 12px; cursor: pointer; font-size: 14px; color: var(--text-muted); }
.toggle-switch input { display: none; }
.toggle-slider { width: 44px; height: 24px; background: #cbd5e1; border-radius: 12px; position: relative; transition: background 0.2s; flex-shrink: 0; }
.toggle-slider::after { content: ''; position: absolute; top: 2px; left: 2px; width: 20px; height: 20px; background: #fff; border-radius: 50%; transition: transform 0.2s; }
.toggle-switch input:checked + .toggle-slider { background: var(--success-color); }
.toggle-switch input:checked + .toggle-slider::after { transform: translateX(20px); }
.toggle-label { font-size: 13px; }

/* Pending Users */
.pending-list { display: flex; flex-direction: column; gap: 10px; }
.pending-item { display: flex; justify-content: space-between; align-items: center; background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 10px; padding: 16px 20px; }
.pending-info { display: flex; flex-direction: column; gap: 4px; }
.pending-email { font-size: 13px; color: var(--text-muted); }
.pending-institution { font-size: 12px; color: var(--primary-color); }
.pending-actions { display: flex; gap: 8px; flex-shrink: 0; }
.btn-approve { padding: 6px 14px; background: #dcfce7; border: 1px solid #bbf7d0; border-radius: 6px; color: #15803d; font-weight: 600; font-size: 13px; cursor: pointer; }
.btn-reject-sm { padding: 6px 14px; background: #fef2f2; border: 1px solid #fee2e2; border-radius: 6px; color: #dc2626; font-weight: 600; font-size: 13px; cursor: pointer; }

/* Trash */
.trash-list { display: flex; flex-direction: column; gap: 10px; }
.trash-header-row { font-size: 13px; color: var(--text-muted); margin-bottom: 4px; }
.trash-item { display: flex; justify-content: space-between; align-items: center; background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 10px; padding: 16px 20px; }
.trash-item-info h4 { margin: 0 0 6px; font-size: 15px; color: var(--text-main); }
.trash-meta { display: flex; gap: 16px; font-size: 12px; color: var(--text-muted); flex-wrap: wrap; }
.trash-item-actions { display: flex; gap: 8px; flex-shrink: 0; }
.btn-restore { padding: 7px 16px; background: #dcfce7; border: 1px solid #bbf7d0; border-radius: 6px; color: #15803d; font-weight: 600; font-size: 13px; cursor: pointer; }
.btn-permanent-delete { padding: 7px 16px; background: #fef2f2; border: 1px solid #fee2e2; border-radius: 6px; color: #dc2626; font-weight: 600; font-size: 13px; cursor: pointer; }

/* Modal */
.modal-backdrop { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(15,23,42,0.45); backdrop-filter: blur(8px); display: flex; justify-content: center; align-items: center; z-index: var(--z-overlay); }
.modal-box { background: var(--bg-surface); border-radius: 14px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.08); padding: 28px; box-sizing: border-box; }
.confirmation-modal { max-width: 460px; text-align: left; }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.modal-header h3 { margin: 0; font-size: 17px; font-weight: 700; color: var(--text-main); }
.btn-close-x { background: transparent; border: none; font-size: 22px; color: #94a3b8; cursor: pointer; }
.confirmation-body { font-size: 13.5px; line-height: 1.5; color: var(--text-muted); padding: 10px 0 20px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; }
.btn-cancel { padding: 8px 16px; background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 6px; color: var(--text-muted); font-weight: 600; font-size: 13px; cursor: pointer; }
.btn-submit { padding: 8px 18px; background: var(--primary-color); color: white; border: none; border-radius: 6px; font-weight: 600; font-size: 13px; cursor: pointer; }

@media (max-width: 767px) { .settings-main-content { margin-left: 0; padding: 16px; } .trash-item, .pending-item { flex-direction: column; align-items: flex-start; gap: 12px; } }
</style>
