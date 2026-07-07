<template>
  <Teleport to="body">
    <div class="confirm-backdrop" v-if="show" @click.self="onCancel">
      <div class="confirm-box">
        <div class="confirm-header">
          <span class="confirm-icon">⚠️</span>
          <h3>{{ title }}</h3>
        </div>
        <div class="confirm-body">
          <p>{{ message }}</p>
        </div>
        <div class="confirm-actions">
          <button class="btn-cancel" @click="onCancel">Cancel</button>
          <button class="btn-confirm" @click="onConfirm">Confirm</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { useConfirmDialog } from '../../composables/useConfirmDialog';

const { show, title, message, onConfirm, onCancel } = useConfirmDialog();
</script>

<style scoped>
.confirm-backdrop {
  position: fixed !important;
  top: 0 !important; left: 0 !important; right: 0 !important; bottom: 0 !important;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(4px);
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  z-index: var(--z-modal) !important;
}
.confirm-box {
  background: #ffffff;
  border-radius: 14px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  width: 400px;
  max-width: 90vw;
  padding: 28px;
  text-align: left;
}
.confirm-icon { font-size: 20px; margin-right: 8px; }
.confirm-header { display: flex; align-items: center; margin-bottom: 12px; }
.confirm-header h3 { margin: 0; font-size: 16px; font-weight: 700; color: #0f172a; }
.confirm-body p { margin: 0 0 24px 0; font-size: 14px; color: #475569; line-height: 1.6; }
.confirm-actions { display: flex; justify-content: flex-end; gap: 12px; }
.btn-cancel {
  padding: 8px 20px; border: 1px solid #e2e8f0; border-radius: 8px;
  font-size: 14px; font-weight: 600; color: #64748b; background: #fff;
  cursor: pointer; transition: all 0.15s;
}
.btn-cancel:hover { background: #f1f5f9; }
.btn-confirm {
  padding: 8px 20px; border: none; border-radius: 8px;
  font-size: 14px; font-weight: 600; color: #fff; background: #ef4444;
  cursor: pointer; transition: all 0.15s;
}
.btn-confirm:hover { background: #dc2626; }
</style>