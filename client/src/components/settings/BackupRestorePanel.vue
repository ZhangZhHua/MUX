<script setup>
import { onMounted, ref, shallowRef } from 'vue'
import api from '../../services/api'
import { useToast } from '../../composables/useToast'

const toast = useToast()

const autoBackup = shallowRef(true)
const retentionDays = shallowRef(7)
const backups = ref([])
const backupDir = shallowRef('/backups')
const loading = shallowRef(true)
const saving = shallowRef(false)
const creating = shallowRef(false)
const restoringFilename = shallowRef('')
const errorMessage = shallowRef('')
const statusMessage = shallowRef('')

async function loadBackupData() {
  loading.value = true
  errorMessage.value = ''

  try {
    const [settingsResponse, listResponse] = await Promise.all([
      api.get('/backup/settings'),
      api.get('/backup/list'),
    ])

    autoBackup.value = settingsResponse.data.auto_backup === 'true'
    retentionDays.value = settingsResponse.data.retention_days || 7
    backups.value = listResponse.data.backups || []
    backupDir.value = listResponse.data.backup_dir || '/backups'
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || 'Unable to load backup information.'
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    await api.put('/backup/settings', null, {
      params: {
        auto_backup: autoBackup.value ? 'true' : 'false',
        retention_days: retentionDays.value,
      },
    })
    statusMessage.value = 'Backup settings saved.'
    toast.success(statusMessage.value)
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || 'Failed to save backup settings.'
  } finally {
    saving.value = false
  }
}

async function createBackup() {
  creating.value = true
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    const response = await api.post('/backup/trigger')
    statusMessage.value = response.data.message || 'Backup created.'
    toast.success(statusMessage.value)
    await loadBackupData()
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || 'Backup failed.'
  } finally {
    creating.value = false
  }
}

async function restoreBackup(filename) {
  const confirmed = window.confirm(
    `Restore ${filename}? The current database will be overwritten. Create a fresh backup before continuing.`,
  )
  if (!confirmed) return

  restoringFilename.value = filename
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    const response = await api.post(`/backup/restore/${encodeURIComponent(filename)}`)
    statusMessage.value = response.data.message || `Restored ${filename}.`
    toast.success(statusMessage.value)
  } catch (error) {
    errorMessage.value = error.response?.data?.detail || 'Restore failed.'
  } finally {
    restoringFilename.value = ''
  }
}

function formatBackupDate(value) {
  if (!value) return 'Unknown date'
  return new Date(value).toLocaleString()
}

onMounted(loadBackupData)
</script>

<template>
  <section class="backup-panel" aria-labelledby="backup-heading">
    <div class="settings-card">
      <div class="card-heading-row">
        <div>
          <h3 id="backup-heading">💾 Automatic backups</h3>
          <p class="card-description">Create a daily PostgreSQL backup and keep it on the host-mounted backup directory.</p>
        </div>
        <button class="btn-secondary" type="button" :disabled="loading" @click="loadBackupData">
          {{ loading ? 'Refreshing…' : 'Refresh' }}
        </button>
      </div>

      <div v-if="loading" class="state-message" role="status">Loading backup settings…</div>
      <div v-else class="backup-settings-grid">
        <label class="toggle-switch">
          <input v-model="autoBackup" type="checkbox" />
          <span class="toggle-slider" aria-hidden="true"></span>
          <span>Daily automatic backup</span>
        </label>

        <label class="retention-field">
          <span>Retention period</span>
          <span class="retention-control">
            <input v-model.number="retentionDays" type="number" min="1" max="365" />
            days
          </span>
        </label>

        <button class="btn-primary" type="button" :disabled="saving" @click="saveSettings">
          {{ saving ? 'Saving…' : 'Save settings' }}
        </button>
      </div>
    </div>

    <div class="settings-card">
      <div class="card-heading-row">
        <div>
          <h3>Manual backup</h3>
          <p class="card-description">Backups are written to <code>{{ backupDir }}</code> and mounted on the Docker host.</p>
        </div>
        <button class="btn-primary" type="button" :disabled="creating" @click="createBackup">
          {{ creating ? 'Creating…' : 'Create backup now' }}
        </button>
      </div>
    </div>

    <p v-if="statusMessage" class="feedback feedback-success" role="status">{{ statusMessage }}</p>
    <p v-if="errorMessage" class="feedback feedback-error" role="alert">{{ errorMessage }}</p>

    <div class="settings-card">
      <h3>Available backups</h3>

      <div v-if="loading" class="state-message" role="status">Loading backups…</div>
      <div v-else-if="backups.length === 0" class="state-message">No backups are available yet.</div>
      <div v-else class="backup-list">
        <article v-for="backup in backups" :key="backup.filename" class="backup-item">
          <div class="backup-item-info">
            <strong>{{ backup.filename }}</strong>
            <span>{{ backup.size_display }} · {{ formatBackupDate(backup.created_at) }}</span>
          </div>
          <button
            class="btn-danger-outline"
            type="button"
            :disabled="Boolean(restoringFilename)"
            @click="restoreBackup(backup.filename)"
          >
            {{ restoringFilename === backup.filename ? 'Restoring…' : 'Restore' }}
          </button>
        </article>
      </div>
    </div>
  </section>
</template>

<style scoped>
.backup-panel { min-height: 300px; }
.settings-card { background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 10px; padding: 20px; margin-bottom: 16px; }
.settings-card h3 { margin: 0 0 8px; font-size: 15px; color: var(--text-main); }
.card-heading-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; }
.card-description { margin: 0; color: var(--text-muted); font-size: 13px; line-height: 1.5; }
.card-description code { color: var(--primary-color); }
.backup-settings-grid { display: grid; grid-template-columns: minmax(220px, 1fr) minmax(180px, 1fr) auto; align-items: center; gap: 20px; margin-top: 20px; }
.toggle-switch { display: flex; align-items: center; gap: 10px; color: var(--text-main); font-size: 14px; cursor: pointer; }
.toggle-switch input { position: absolute; opacity: 0; pointer-events: none; }
.toggle-slider { width: 44px; height: 24px; background: #cbd5e1; border-radius: 999px; position: relative; transition: background 0.2s; flex-shrink: 0; }
.toggle-slider::after { content: ''; position: absolute; top: 2px; left: 2px; width: 20px; height: 20px; background: #fff; border-radius: 50%; transition: transform 0.2s; }
.toggle-switch input:checked + .toggle-slider { background: var(--success-color); }
.toggle-switch input:checked + .toggle-slider::after { transform: translateX(20px); }
.toggle-switch input:focus-visible + .toggle-slider { outline: 3px solid color-mix(in srgb, var(--primary-color) 30%, transparent); outline-offset: 2px; }
.retention-field { display: flex; align-items: center; justify-content: space-between; gap: 12px; color: var(--text-main); font-size: 14px; }
.retention-control { display: flex; align-items: center; gap: 7px; color: var(--text-muted); }
.retention-control input { width: 70px; padding: 8px 10px; border: 1px solid var(--border-color); border-radius: 7px; background: var(--bg-surface); color: var(--text-main); }
.btn-primary, .btn-secondary, .btn-danger-outline { border-radius: 7px; padding: 8px 14px; font-weight: 600; font-size: 13px; cursor: pointer; }
.btn-primary { border: 1px solid var(--primary-color); background: var(--primary-color); color: #fff; }
.btn-secondary { border: 1px solid var(--border-color); background: var(--bg-surface); color: var(--text-main); }
.btn-danger-outline { border: 1px solid #fecaca; background: #fff; color: #b91c1c; }
button:disabled { cursor: not-allowed; opacity: 0.6; }
.feedback { margin: 0 0 16px; border-radius: 8px; padding: 11px 14px; font-size: 13px; }
.feedback-success { background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; }
.feedback-error { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
.state-message { padding: 30px 12px; text-align: center; color: var(--text-muted); font-size: 14px; }
.backup-list { display: flex; flex-direction: column; gap: 8px; margin-top: 14px; }
.backup-item { display: flex; justify-content: space-between; align-items: center; gap: 16px; border: 1px solid var(--border-color); border-radius: 8px; padding: 13px 15px; }
.backup-item-info { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.backup-item-info strong { overflow-wrap: anywhere; color: var(--text-main); font-size: 13px; }
.backup-item-info span { color: var(--text-muted); font-size: 12px; }

@media (max-width: 760px) {
  .card-heading-row, .backup-item { flex-direction: column; align-items: stretch; }
  .backup-settings-grid { grid-template-columns: 1fr; }
  .retention-field { justify-content: flex-start; }
}
</style>
