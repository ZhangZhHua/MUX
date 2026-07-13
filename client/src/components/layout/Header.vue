<template>
  <header class="global-header">
    <div class="header-left">
      <button class="hamburger-menu" @click="$emit('toggle-sidebar')" aria-label="Toggle Navigation Sidebar">
        <span class="hamburger-bar"></span>
        <span class="hamburger-bar"></span>
        <span class="hamburger-bar"></span>
      </button>
      <MuxLogo @click="goHomeAndRefresh" style="cursor: pointer;" />
    </div>

    <div class="header-center">
      <div class="search-wrapper" :class="{ 'search-active': searchQuery.length > 0 }">
        <span class="search-icon">🔍</span>
        <input
          type="text"
          v-model="searchQuery"
          placeholder="Search experiments, events, or people..."
          @input="onSearchInput"
          @focus="openSearchResults"
          @keydown.escape="closeSearch"
        />
        <span v-if="searchLoading" class="search-spinner">⏳</span>
        <span v-if="searchQuery && !searchLoading" class="search-clear" @click="clearSearch">✕</span>
      </div>
      <!-- Search Results Dropdown -->
      <div class="search-dropdown" v-if="showSearchResults && searchQuery.length > 0" @mousedown.prevent>
        <div v-if="searchLoading" class="search-status">Searching...</div>
        <template v-else>
          <div v-if="searchError" class="search-status search-error">{{ searchError }}</div>
          <!-- Experiments Section -->
          <div v-if="!searchError && searchResults.experiments && searchResults.experiments.length > 0" class="search-section">
            <div class="search-section-header">🔬 Experiments</div>
            <div
              v-for="exp in searchResults.experiments"
              :key="'exp-'+exp.id"
              class="search-result-item"
              @click="navigateToExperiment(exp.id)"
            >
              <span class="search-item-icon">🔬</span>
              <div class="search-item-info">
                <span class="search-item-title">{{ exp.title }}</span>
                <span class="search-item-meta">{{ exp.group_name }} · {{ exp.status }}</span>
              </div>
            </div>
          </div>
          <!-- Events Section -->
          <div v-if="!searchError && searchResults.events && searchResults.events.length > 0" class="search-section">
            <div class="search-section-header">📅 Lab Events</div>
            <div
              v-for="evt in searchResults.events"
              :key="'evt-'+evt.id"
              class="search-result-item"
              @click="navigateToEvent(evt.id)"
            >
              <span class="search-item-icon">📅</span>
              <div class="search-item-info">
                <span class="search-item-title">{{ evt.title }}</span>
                <span class="search-item-meta">{{ evt.group_name }} · {{ formatSearchDate(evt.start_date) }}</span>
              </div>
            </div>
          </div>
          <!-- Users Section -->
          <div v-if="!searchError && searchResults.users && searchResults.users.length > 0" class="search-section">
            <div class="search-section-header">👥 People</div>
            <div
              v-for="user in searchResults.users"
              :key="'user-'+user.id"
              class="search-result-item"
              @click="navigateToUser(user.id)"
            >
              <span class="search-item-icon">👤</span>
              <div class="search-item-info">
                <span class="search-item-title">{{ user.first_name }} {{ user.last_name }}</span>
                <span class="search-item-meta">{{ user.institution || user.email }}</span>
              </div>
            </div>
          </div>
          <!-- No Results -->
          <div v-if="!searchError && !hasSearchResults" class="search-status">No results found for "{{ searchQuery }}"</div>
        </template>
      </div>
    </div>

    <div class="header-right">
      <span class="role-badge">{{ userRole }}</span>

      <div class="user-profile-trigger" @click="openProfileModal" title="Click to view & edit your account profile">
        <img v-if="currentUserAvatar" :src="getAvatarUrl(currentUserAvatar)" class="header-avatar-fit" />
        <span v-else class="user-avatar-avatar">👤</span>
        <span class="user-name-text">{{ currentFullName }}</span>
      </div>

      <button class="btn-logout" @click="$emit('logout')">Logout</button>
    </div>

    <Teleport to="body">
      <div class="modal-backdrop" v-if="showProfileModal" @mousedown.self="mouseDownTarget = $event.target" @mouseup.self="mouseDownTarget === $event.currentTarget && closeProfileModal()">
        <div class="modal-box profile-center-modal">

          <div class="profile-modal-layout">
            <div class="profile-mini-sidebar">
              <div class="card-avatar-area">
                <div class="avatar-upload-container">
                  <div class="profile-huge-avatar" @click="triggerAvatarPicker">
                    <img v-if="currentUserAvatar" :src="getAvatarUrl(currentUserAvatar)" class="avatar-img-fit" />
                    <span v-else class="avatar-placeholder">👤</span>
                    <div class="avatar-hover-overlay">
                      <span class="camera-icon">📷</span>
                      <span class="hover-text">Upload</span>
                    </div>
                  </div>

                  <input
                    type="file"
                    ref="avatarFileSelector"
                    style="display: none"
                    accept="image/png, image/jpeg, image/jpg"
                    @change="handleAvatarFileChange"
                  />
                </div>
                <h4>{{ profileForm.first_name }} {{ profileForm.last_name }}</h4>
                <p class="institution-sub">{{ profileForm.institution || 'No Institution Linked' }}</p>
                <span class="sidebar-role-tag">{{ userRole.toUpperCase() }}</span>
              </div>

              <div class="profile-tab-menu">
                <button class="tab-menu-item" :class="{ active: activeTab === 'profile' }" @click="activeTab = 'profile'">
                  👤 Personal Profile
                </button>
                <button class="tab-menu-item" :class="{ active: activeTab === 'security' }" @click="activeTab = 'security'">
                  🔐 Account Security
                </button>
                <button type="button" class="tab-menu-item btn-mobile-logout" @click="handleMobileLogout">
                  🚪 Logout Account
                </button>
              </div>
            </div>

            <div class="profile-main-form-stage">
              <div class="profile-stage-header">
                <h3>{{ activeTab === 'profile' ? 'Account Profile Settings' : 'Security Credentials' }}</h3>
                <button class="btn-close-profile-x" @click="closeProfileModal">&times;</button>
              </div>

              <form v-if="activeTab === 'profile'" @submit.prevent="handleSaveProfile" class="profile-render-form">
                <div class="form-grid-row">
                  <div class="profile-form-group flex-1">
                    <label>First Name *</label>
                    <input type="text" v-model="profileForm.first_name" required />
                  </div>
                  <div class="profile-form-group flex-1">
                    <label>Last Name *</label>
                    <input type="text" v-model="profileForm.last_name" required />
                  </div>
                </div>

                <div class="profile-form-group">
                  <label>Email Address (Primary Identity - Read Only)</label>
                  <input type="email" :value="userEmail" disabled class="input-disabled" title="To change identity email, contact sys_admin." />
                </div>

                <div class="profile-form-group">
                  <label>Contact Phone Number</label>
                  <input type="text" v-model="profileForm.phone" placeholder="e.g., +86 188-XXXX-XXXX" />
                </div>

                <div class="profile-form-group">
                  <label>Research Institution / Affiliation (单位)</label>
                  <input type="text" v-model="profileForm.institution" placeholder="e.g., University of Science and Technology of China (USTC)" />
                </div>

                <div class="profile-form-group">
                  <label>Country / Region (国家地区)</label>
                  <select v-model="profileForm.country_region" class="profile-select-native">
                    <option value="">Select your location...</option>
                    <option value="China">China (中国)</option>
                    <option value="Singapore">Singapore (新加坡)</option>
                    <option value="Switzerland">Switzerland (CERN / 瑞士)</option>
                    <option value="United States">United States (美国)</option>
                    <option value="Germany">Germany (德国)</option>
                  </select>
                </div>

                <div class="profile-form-group">
                  <label>Academic Bio / Research Group Directives</label>
                  <textarea v-model="profileForm.academic_bio" rows="3" placeholder="Describe your current detector calibration fields or experimental focus..."></textarea>
                </div>

                <div class="profile-form-actions">
                  <button type="button" class="btn-profile-cancel" @click="closeProfileModal">Cancel</button>
                  <button type="submit" class="btn-profile-submit">Save Node profile</button>
                </div>
              </form>

              <div v-else class="security-placeholder-flow">
                <div class="security-alert-box">
                  <p>🔐 Your login token is encrypted with **HMAC-SHA256** and managed securely via session local cookies.</p>
                </div>
                <div class="profile-form-group" style="margin-top: 16px;">
                  <label>Current Credentials State</label>
                  <input type="text" value="•••••••••••••••••••••••••" disabled class="input-disabled" />
                </div>
                <button type="button" class="btn-profile-submit" style="margin-top: 12px; width: auto;" @click="toast.info('Password resetting vault coming next milestone!')">
                  Request Credentials Reset Loop
                </button>
              </div>

            </div>
          </div>

        </div>
      </div>
    </Teleport>

  </header>
</template>

<script setup>
import { ref, shallowRef, computed, onMounted, onBeforeUnmount } from 'vue';
import { useRouter } from 'vue-router';
import api from '../../services/api';
import MuxLogo from '../common/MuxLogo.vue';
import { useToast } from '../../composables/useToast';

const props = defineProps({
  userName: { type: String, default: 'Researcher' },
  userRole: { type: String, default: 'member' }
});

const emit = defineEmits(['logout', 'toggle-sidebar']);
const router = useRouter();
const toast = useToast();

// --- Search State ---
const searchQuery = shallowRef('');
const searchResults = shallowRef({ experiments: [], events: [], users: [] });
const showSearchResults = shallowRef(false);
const searchLoading = shallowRef(false);
const searchError = shallowRef('');
let searchDebounceTimer = null;
let latestSearchId = 0;

const hasSearchResults = computed(() => {
  return (searchResults.value.experiments?.length || 0) +
         (searchResults.value.events?.length || 0) +
         (searchResults.value.users?.length || 0) > 0;
});

const onSearchInput = () => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
  const q = searchQuery.value.trim();
  const searchId = ++latestSearchId;
  searchError.value = '';
  if (q.length < 2) {
    searchResults.value = { experiments: [], events: [], users: [] };
    showSearchResults.value = false;
    searchLoading.value = false;
    return;
  }
  showSearchResults.value = true;
  searchLoading.value = true;
  searchDebounceTimer = setTimeout(() => performSearch(q, searchId), 300);
};

const performSearch = async (q, searchId) => {
  searchError.value = '';
  try {
    const res = await api.get('/experiments/search', { params: { q } });
    if (searchId !== latestSearchId) return;
    searchResults.value = res.data;
    showSearchResults.value = true;
  } catch (e) {
    if (searchId !== latestSearchId) return;
    searchResults.value = { experiments: [], events: [], users: [] };
    searchError.value = 'Search failed. Please try again.';
    showSearchResults.value = true;
  } finally {
    if (searchId === latestSearchId) searchLoading.value = false;
  }
};

const openSearchResults = () => {
  if (searchQuery.value.trim().length >= 2) {
    showSearchResults.value = true;
  }
};

const clearSearch = () => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
  latestSearchId += 1;
  searchQuery.value = '';
  searchResults.value = { experiments: [], events: [], users: [] };
  searchError.value = '';
  searchLoading.value = false;
  showSearchResults.value = false;
};

const closeSearch = () => {
  showSearchResults.value = false;
};

const navigateToExperiment = (id) => {
  closeSearch();
  router.push(`/experiment/${id}`);
};

const navigateToEvent = (id) => {
  closeSearch();
  router.push('/events');
  // We can't directly jump to a specific event on the events page easily,
  // but at least take the user to the events page
};

const navigateToUser = (id) => {
  closeSearch();
  router.push('/team-members');
};

const formatSearchDate = (dateStr) => {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

const showProfileModal = ref(false);
const activeTab = ref('profile'); // profile | security

const goHomeAndRefresh = () => {
  if (window.location.pathname === '/') {
    window.location.reload();
  } else {
    window.location.href = '/';
  }
};

let mouseDownTarget = null;

const userEmail = ref('');
const currentFullName = ref('');
const avatarFileSelector = ref(null);
const currentUserAvatar = ref(null);

// Reactive user form state
const profileForm = ref({
  first_name: '',
  last_name: '',
  phone: '',
  institution: '',
  country_region: '',
  academic_bio: ''
});

// Close search dropdown when clicking outside
const handleClickOutside = (e) => {
  const searchEl = document.querySelector('.header-center');
  if (searchEl && !searchEl.contains(e.target)) {
    showSearchResults.value = false;
  }
};

onMounted(async () => {
  document.addEventListener('click', handleClickOutside);
  // Active fetch: try to load full profile from server to get avatar + name
  try {
    const response = await api.get('/auth/me');
    const u = response.data;
    currentFullName.value = `${u.first_name} ${u.last_name}`;
    localStorage.setItem('userName', currentFullName.value);
    currentUserAvatar.value = u.avatar_node || null;
    if (u.avatar_node) {
      localStorage.setItem('userAvatar', u.avatar_node);
    } else {
      localStorage.removeItem('userAvatar');
    }
  } catch (e) {
    // Fallback: restore cached avatar from localStorage
    currentUserAvatar.value = localStorage.getItem('userAvatar') || null;
  }
});

onBeforeUnmount(() => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer);
  document.removeEventListener('click', handleClickOutside);
});

// Open profile modal and fetch latest data from server
const openProfileModal = async () => {
  try {
    const response = await api.get('/auth/me');
    const u = response.data;

    userEmail.value = u.email;
    profileForm.value.first_name = u.first_name;
    profileForm.value.last_name = u.last_name;
    profileForm.value.phone = u.phone || '';
    profileForm.value.institution = u.institution || '';
    profileForm.value.country_region = u.country_region || '';
    profileForm.value.academic_bio = u.academic_bio || '';

    // Sync display name
    currentFullName.value = `${u.first_name} ${u.last_name}`;

    // Sync avatar state and cache from server source of truth
    currentUserAvatar.value = u.avatar_node || null;
    if (u.avatar_node) {
      localStorage.setItem('userAvatar', u.avatar_node);
    } else {
      localStorage.removeItem('userAvatar');
    }

    activeTab.value = 'profile';
    showProfileModal.value = true;
  } catch (error) {
    toast.error("Failed to fetch account credentials from node server.");
  }
};

const closeProfileModal = () => {
  showProfileModal.value = false;
};

const handleMobileLogout = () => {
  emit('logout');
  showProfileModal.value = false;
};

// Submit profile form to server
const handleSaveProfile = async () => {
  try {
    const response = await api.put('/auth/profile', {
      first_name: profileForm.value.first_name,
      last_name: profileForm.value.last_name,
      phone: profileForm.value.phone || null,
      institution: profileForm.value.institution || null,
      country_region: profileForm.value.country_region || null,
      academic_bio: profileForm.value.academic_bio || null
    });

    const updatedUser = response.data;
    currentFullName.value = `${updatedUser.first_name} ${updatedUser.last_name}`;

    // Sync local name cache
    localStorage.setItem('userName', currentFullName.value);

    toast.success("Account profile node database synchronized!");
    showProfileModal.value = false;

    window.location.reload();
  } catch (error) {
    toast.error("Failed to commit profile updates.");
  }
};

// Fallback name init from localStorage
currentFullName.value = localStorage.getItem('userName') || props.userName;

// Trigger hidden file input
const triggerAvatarPicker = () => {
  avatarFileSelector.value.click();
};

// Handle avatar file selection and two-phase upload + bind
const handleAvatarFileChange = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  // Enforce 2MB size limit
  if (file.size > 10 * 1024 * 1024) {
    toast.error("Avatar size standard violation. Keep image under 10MB.");
    return;
  }

  // Phase 1: upload binary to /experiments/upload
  const formData = new FormData();
  formData.append('file', file);

  toast.info("Uploading your new academic avatar...");

  try {
    const uploadRes = await api.post('/experiments/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    const serverFileName = uploadRes.data.filename;

    // Phase 2: bind filename to current user account (correct /auth/ prefix)
    await api.put('/auth/profile/academic-identity', {
      avatar_node: serverFileName
    });

    // Phase 3: update local reactive state and cache
    currentUserAvatar.value = serverFileName;
    localStorage.setItem('userAvatar', serverFileName);
    toast.success("Academic avatar reconfigured smoothly!");

    window.location.reload();
  } catch (error) {
    toast.error("Failed to commit avatar to server node.");
  } finally {
    event.target.value = ''; // Reset file input
  }
};

// Build URL for avatar image display
const getAvatarUrl = (node) => `${api.defaults.baseURL}/experiments/attachments/${node}`;
</script>

<style scoped>
.global-header {
  position: fixed; top: 0; left: 0; right: 0; height: 64px;
  background: #ffffff; border-bottom: 1px solid #e2e8f0;
  display: flex; justify-content: space-between; align-items: center;
  padding: 0 24px; z-index: var(--z-sticky); box-sizing: border-box;
}
.header-left { display: flex; align-items: center; gap: 10px; }
.logo-icon { font-size: 22px; }
.logo-text { margin: 0; font-size: 16px; font-weight: 700; color: #0f172a; cursor: pointer; }

.header-center { width: 400px; }
.search-wrapper {
  display: flex; align-items: center; gap: 8px; background: var(--bg-primary);
  border: 1px solid var(--border-color); border-radius: 6px; padding: 6px 12px; width: 100%; box-sizing: border-box;
}
.search-icon { font-size: 13px; color: var(--text-muted); }
.search-wrapper input {
  background: transparent; border: none; outline: none; width: 100%; font-size: 13px; color: var(--text-main); cursor: not-allowed;
}
.search-wrapper input::placeholder { color: var(--text-muted); opacity: 1; }

.header-right { display: flex; align-items: center; gap: 16px; }
.role-badge { font-size: 11px; font-weight: 600; background: #eff6ff; color: #2563eb; padding: 2px 8px; border-radius: 4px; border: 1px solid #bfdbfe; text-transform: lowercase; }

/* User profile trigger area */
.user-profile-trigger {
  display: flex; align-items: center; gap: 8px; cursor: pointer;
  padding: 6px 10px; border-radius: 6px; transition: all 0.2s; user-select: none;
}
.user-profile-trigger:hover { background: #f1f5f9; }
.user-avatar-avatar { font-size: 15px; }
.user-name-text { font-size: 14px; font-weight: 600; color: #334155; }

.btn-logout {
  background: transparent; border: 1px solid #fca5a5; color: #ef4444;
  padding: 4px 12px; font-size: 13px; font-weight: 600; border-radius: 6px; cursor: pointer; transition: all 0.15s;
}
.btn-logout:hover { background: #fef2f2; }

/* Profile modal two-column layout */
.profile-center-modal {
  width: 95% !important;
  max-width: 780px !important;
  height: 600px !important;
  padding: 0 !important;
  overflow: hidden;
  border-radius: 14px !important;
}
.profile-modal-layout {
  display: flex;
  height: 100%;
}

/* Left sidebar */
.profile-mini-sidebar {
  width: 240px;
  background: #f8fafc;
  border-right: 1px solid #e2e8f0;
  padding: 32px 20px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 28px;
  height: 100%;
}
.card-avatar-area { text-align: center; display: flex; flex-direction: column; align-items: center; }
.huge-avatar { width: 64px; height: 64px; background: #e2e8f0; border-radius: 50%; font-size: 32px; display: flex; align-items: center; justify-content: center; margin-bottom: 12px; }
.card-avatar-area h4 { margin: 0 0 4px 0; font-size: 16px; font-weight: 700; color: #0f172a; }
.institution-sub { margin: 0 0 12px 0; font-size: 12px; color: #64748b; font-weight: 500; }
.sidebar-role-tag { font-size: 10px; font-weight: 700; background: #0f172a; color: white; padding: 2px 6px; border-radius: 4px; }

.profile-tab-menu { display: flex; flex-direction: column; gap: 6px; width: 100%; }
.tab-menu-item {
  width: 100%; padding: 10px 14px; text-align: left; background: transparent;
  border: none; border-radius: 8px; font-size: 13.5px; font-weight: 600; color: #475569;
  cursor: pointer; transition: all 0.15s;
}
.tab-menu-item:hover { background: #e2e8f0; color: #0f172a; }
.tab-menu-item.active { background: #ffffff; color: #2563eb; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }

/* Right main form stage */
.profile-shadow-form-stage {
  flex: 1; padding: 32px; box-sizing: border-box; display: flex; flex-direction: column; background: #ffffff;
}
.profile-stage-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.profile-stage-header h3 { margin: 0; font-size: 18px; font-weight: 700; color: #0f172a; letter-spacing: -0.3px; }
.btn-close-profile-x { background: transparent; border: none; font-size: 26px; color: #94a3b8; cursor: pointer; padding: 0; line-height: 1; }
.btn-close-profile-x:hover { color: #1e293b; }

.profile-main-form-stage {
  flex: 1;
  padding: 32px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  height: 100%;
  overflow-y: auto;
}

.profile-render-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  text-align: left;
  flex: 1;
}
.form-grid-row { display: flex; gap: 16px; }
.flex-1 { flex: 1; }

.profile-form-group { display: flex; flex-direction: column; text-align: left; }
.profile-form-group label { font-size: 12.5px; font-weight: 600; color: #475569; margin-bottom: 6px; }
.profile-form-group input, .profile-form-group textarea, .profile-select-native {
  padding: 8px 12px; font-size: 14px; border: 1px solid #cbd5e1; border-radius: 6px;
  outline: none; background: #ffffff; width: 100%; box-sizing: border-box; color: #1e293b; transition: border 0.15s;
}
.profile-form-group input:focus, .profile-form-group textarea:focus, .profile-select-native:focus {
  border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}
.input-disabled { background: #f1f5f9 !important; border-color: #e2e8f0 !important; color: #64748b !important; cursor: not-allowed; }
.profile-select-native { background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23475569'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 12px center; background-size: 16px; -webkit-appearance: none; -moz-appearance: none; appearance: none; padding-right: 36px; }

.profile-form-actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 12px; border-top: 1px solid #f1f5f9; padding-top: 16px; }
.btn-profile-cancel { padding: 8px 16px; background: transparent; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13.5px; font-weight: 600; color: #64748b; cursor: pointer; }
.btn-profile-cancel:hover { background: #f8fafc; color: #1e293b; }
.btn-profile-submit { padding: 8px 16px; background: #2563eb; color: white; border: none; border-radius: 6px; font-size: 13.5px; font-weight: 600; cursor: pointer; }
.btn-profile-submit:hover { background: #1d4ed8; }

/* Security tab styles */
.security-placeholder-flow { text-align: left; display: flex; flex-direction: column; gap: 14px; }
.security-alert-box { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px; padding: 12px; }
.security-alert-box p { margin: 0; font-size: 13px; color: #1e40af; line-height: 1.5; }

/* Avatar upload container */
.avatar-upload-container {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

/* Large circular avatar slot */
.profile-huge-avatar {
  width: 84px;
  height: 84px;
  background: #f1f5f9;
  border: 2px solid #e2e8f0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  cursor: pointer;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.avatar-img-fit {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  font-size: 42px;
  color: #94a3b8;
}

/* Hover overlay for upload prompt */
.avatar-hover-overlay {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(15, 23, 42, 0.65);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.18s ease;
}

.profile-huge-avatar:hover .avatar-hover-overlay {
  opacity: 1;
}

.camera-icon { font-size: 16px; }
.hover-text {
  font-size: 10px;
  color: #ffffff;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.header-avatar-fit {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid #cbd5e1;
  display: inline-block;
  vertical-align: middle;
}

/* Hamburger menu button styles */
.hamburger-menu {
  display: none;
  flex-direction: column;
  justify-content: space-around;
  width: 22px;
  height: 18px;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
  margin-right: 8px;
  outline: none;
}
.hamburger-bar {
  width: 22px;
  height: 2.5px;
  background-color: #475569;
  border-radius: 5px;
  transition: all 0.2s ease;
}

.btn-mobile-logout {
  display: none;
  color: #ef4444 !important;
  border-top: 1px dashed rgba(239, 68, 68, 0.2);
  margin-top: 12px;
}

@media (max-width: 767px) {
  .hamburger-menu {
    display: flex;
  }
  .header-center {
    display: none; /* Hide search bar on mobile */
  }
  .role-badge, .user-name-text, .btn-logout {
    display: none; /* Hide redundant elements to avoid overflowing */
  }
  .global-header {
    padding: 0 16px;
  }

  /* Make the profile trigger modal more responsive */
  .profile-center-modal {
    width: 92% !important;
    height: auto !important;
    max-height: 90vh !important;
    overflow-y: auto !important;
  }
  .profile-modal-layout {
    flex-direction: column;
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
  .btn-mobile-logout {
    display: flex !important;
  }
}

/* Search dropdown styles */
.header-center { position: relative; }
.search-wrapper { position: relative; }
.search-wrapper.search-active { border-color: var(--primary-color); box-shadow: 0 0 0 2px rgba(37,99,235,0.1); }
.search-wrapper input { cursor: text !important; }
.search-spinner { font-size: 13px; animation: spin 1s linear infinite; }
.search-clear { font-size: 14px; color: var(--text-muted); cursor: pointer; padding: 2px 4px; border-radius: 3px; }
.search-clear:hover { background: var(--border-color); color: var(--text-main); }

.search-dropdown {
  position: absolute;
  top: 42px;
  left: 0;
  right: 0;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(15,23,42,0.12);
  max-height: 420px;
  overflow-y: auto;
  z-index: var(--z-overlay);
}
.search-section { padding: 6px 0; }
.search-section + .search-section { border-top: 1px solid var(--border-color); }
.search-section-header {
  padding: 8px 16px;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.search-result-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.12s;
}
.search-result-item:hover { background: var(--bg-primary); }
.search-item-icon { font-size: 15px; flex-shrink: 0; }
.search-item-info { display: flex; flex-direction: column; min-width: 0; }
.search-item-title { font-size: 13.5px; font-weight: 600; color: var(--text-main); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.search-item-meta { font-size: 11.5px; color: var(--text-muted); margin-top: 1px; }
.search-status { padding: 20px; text-align: center; font-size: 13px; color: var(--text-muted); }
.search-error { color: #dc2626; }

@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
