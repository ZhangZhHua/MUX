<template>
  <router-view />
  <ToastContainer />
  <ConfirmDialog />
  <div v-if="showTimeoutWarning" class="timeout-overlay">
    <div class="timeout-modal">
      <h3>⏰ Session Timeout</h3>
      <p>You've been idle for too long. You'll be logged out in <strong>{{ countdown }}</strong> seconds.</p>
      <div class="timeout-actions">
        <button class="btn-stay" @click="resetIdleTimer">I'm still here</button>
        <button class="btn-logout-now" @click="forceLogout">Logout now</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import api from './services/api'
import ToastContainer from './components/common/ToastContainer.vue'
import ConfirmDialog from './components/common/ConfirmDialog.vue'

const router = useRouter()

const IDLE_CHECK_INTERVAL = 30000 // Check every 30 seconds
const WARNING_SECONDS = 60
const showTimeoutWarning = ref(false)
const countdown = ref(WARNING_SECONDS)

let idleTimer = null
let countdownTimer = null
let sessionTimeoutMinutes = 120
let lastActivity = Date.now()

const resetIdleTimer = () => {
  lastActivity = Date.now()
  showTimeoutWarning.value = false
  countdown.value = WARNING_SECONDS
  if (countdownTimer) clearInterval(countdownTimer)
  // Update last_active on server
  if (sessionStorage.getItem('authenticated')) {
    api.get('/auth/me').catch(() => {})
  }
}

const checkIdle = async () => {
  if (!sessionStorage.getItem('authenticated')) return
  
  const elapsed = (Date.now() - lastActivity) / 60000 // minutes
  
  // Load timeout setting
  try {
    const r = await api.get('/auth/users/session-status')
    sessionTimeoutMinutes = r.data.session_timeout_minutes
    if (r.data.is_timed_out) {
      forceLogout()
      return
    }
  } catch {}

  const warningThreshold = sessionTimeoutMinutes - 1 // Warn 1 minute before
  if (elapsed >= sessionTimeoutMinutes) {
    forceLogout()
  } else if (elapsed >= warningThreshold) {
    if (!showTimeoutWarning.value) {
      showTimeoutWarning.value = true
      countdown.value = Math.ceil(sessionTimeoutMinutes - elapsed) * 60
      countdownTimer = setInterval(() => {
        countdown.value--
        if (countdown.value <= 0) {
          forceLogout()
        }
      }, 1000)
    }
  }
}

const forceLogout = () => {
  api.post('/auth/logout').catch(() => {})
  sessionStorage.removeItem('authenticated')
  localStorage.clear()
  if (countdownTimer) clearInterval(countdownTimer)
  if (idleTimer) clearInterval(idleTimer)
  router.push('/login')
}

// Track activity
const activityEvents = ['mousedown', 'mousemove', 'keydown', 'scroll', 'touchstart', 'click']
const onActivity = () => { lastActivity = Date.now() }

onMounted(() => {
  activityEvents.forEach(e => document.addEventListener(e, onActivity, { passive: true }))
  idleTimer = setInterval(checkIdle, IDLE_CHECK_INTERVAL)
})

onUnmounted(() => {
  activityEvents.forEach(e => document.removeEventListener(e, onActivity))
  if (idleTimer) clearInterval(idleTimer)
  if (countdownTimer) clearInterval(countdownTimer)
})
</script>

<style>
.timeout-overlay {
  position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
  background: rgba(15,23,42,0.6); backdrop-filter: blur(8px);
  display: flex; justify-content: center; align-items: center; z-index: 9999;
}
.timeout-modal {
  background: var(--bg-surface); border-radius: 14px; padding: 32px;
  max-width: 420px; text-align: center; box-shadow: 0 25px 50px rgba(0,0,0,0.15);
}
.timeout-modal h3 { margin: 0 0 12px; font-size: 20px; color: var(--text-main); }
.timeout-modal p { font-size: 14px; color: var(--text-muted); margin: 0 0 20px; line-height: 1.5; }
.timeout-actions { display: flex; gap: 10px; justify-content: center; }
.btn-stay { padding: 10px 20px; background: var(--primary-color); color: #fff; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; }
.btn-logout-now { padding: 10px 20px; background: #fef2f2; border: 1px solid #fee2e2; border-radius: 8px; color: #dc2626; font-weight: 600; cursor: pointer; }
</style>
