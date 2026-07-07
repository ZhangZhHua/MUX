<template>
  <div class="toast-container">
    <TransitionGroup name="toast-slide">
      <div 
        v-for="toast in toasts" 
        :key="toast.id" 
        class="toast-card" 
        :class="[toast.type, { 'swiping': toast._swiping }]"
        :style="toast._swipeStyle"
        @touchstart="onTouchStart($event, toast)"
        @touchmove="onTouchMove($event, toast)"
        @touchend="onTouchEnd($event, toast)"
        @mousedown="onMouseDown($event, toast)"
        @mousemove="onMouseMove($event, toast)"
        @mouseup="onMouseUp($event, toast)"
        @mouseleave="onMouseLeave($event, toast)"
      >
        <span class="toast-icon">
          <span v-if="toast.type === 'success'">✅</span>
          <span v-else-if="toast.type === 'error'">❌</span>
          <span v-else>ℹ️</span>
        </span>
        <span class="toast-message">{{ toast.message }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useToast } from '../../composables/useToast';
const { toasts, dismiss } = useToast();

const SWIPE_THRESHOLD = 80; // 向右滑动阈值像素

const toastSwipeState = reactive({}); // key: toast.id -> { startX, currentX, swiping }

const getSwipeState = (toast) => {
  if (!toastSwipeState[toast.id]) {
    toastSwipeState[toast.id] = { startX: 0, currentX: 0, swiping: false };
  }
  return toastSwipeState[toast.id];
};

const updateSwipeTransform = (toast) => {
  const state = toastSwipeState[toast.id];
  if (!state) return;
  const diff = state.currentX - state.startX;
  if (diff <= 0) {
    // 左滑或无滑动不做任何处理
    toast._swiping = false;
    toast._swipeStyle = null;
    return;
  }
  toast._swiping = true;
  toast._swipeStyle = {
    transform: `translateX(${diff}px)`,
    opacity: Math.max(0, 1 - diff / (SWIPE_THRESHOLD * 2)),
    transition: 'none'
  };
};

const onTouchStart = (e, toast) => {
  const state = getSwipeState(toast);
  state.startX = e.touches[0].clientX;
  state.currentX = e.touches[0].clientX;
  state.swiping = false;
};

const onTouchMove = (e, toast) => {
  const state = getSwipeState(toast);
  state.currentX = e.touches[0].clientX;
  state.swiping = true;
  updateSwipeTransform(toast);
};

const onTouchEnd = (e, toast) => {
  const state = getSwipeState(toast);
  const diff = state.currentX - state.startX;
  if (diff > SWIPE_THRESHOLD) {
    dismiss(toast.id);
  } else {
    toast._swiping = false;
    toast._swipeStyle = null;
  }
  toastSwipeState[toast.id] = { startX: 0, currentX: 0, swiping: false };
};

// 鼠标拖动支持
let mouseState = null;

const onMouseDown = (e, toast) => {
  mouseState = { toast, startX: e.clientX, currentX: e.clientX };
  const state = getSwipeState(toast);
  state.startX = e.clientX;
  state.currentX = e.clientX;
  state.swiping = false;
};

const onMouseMove = (e, toast) => {
  if (!mouseState || mouseState.toast.id !== toast.id) return;
  const state = getSwipeState(toast);
  state.currentX = e.clientX;
  state.swiping = true;
  updateSwipeTransform(toast);
};

const onMouseUp = (e, toast) => {
  if (!mouseState || mouseState.toast.id !== toast.id) return;
  const state = getSwipeState(toast);
  const diff = state.currentX - state.startX;
  if (diff > SWIPE_THRESHOLD) {
    dismiss(toast.id);
  } else {
    toast._swiping = false;
    toast._swipeStyle = null;
  }
  toastSwipeState[toast.id] = { startX: 0, currentX: 0, swiping: false };
  mouseState = null;
};

const onMouseLeave = (e, toast) => {
  if (!mouseState || mouseState.toast.id !== toast.id) return;
  // 如果鼠标离开，回弹复位
  toast._swiping = false;
  toast._swipeStyle = null;
  toastSwipeState[toast.id] = { startX: 0, currentX: 0, swiping: false };
  mouseState = null;
};
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 2147483647; /* 最高安全层级，确保始终悬浮在所有弹窗遮罩之上 */
  display: flex;
  flex-direction: column;
  gap: 12px;
  pointer-events: none; /* 防止遮挡下方点击事件 */
}

.toast-card {
  pointer-events: auto; /* 卡片自身恢复鼠标交互 */
  min-width: 280px;
  max-width: 400px;
  padding: 14px 20px;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  font-weight: 500;
  border-left: 4px solid #cbd5e1;
  font-family: system-ui, -apple-system, sans-serif;
}

/* 根据不同状态渲染现代学术配色 */
.toast-card.success {
  border-left-color: #10b981; /* 翡翠绿 */
  background: #f0fdf4;
  color: #14532d;
}

.toast-card.error {
  border-left-color: #ef4444; /* 珊瑚红 */
  background: #fef2f2;
  color: #7f1d1d;
}

.toast-card.info {
  border-left-color: #3b82f6; /* 科技蓝 */
  background: #eff6ff;
  color: #1e3a8a;
}

.toast-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.toast-message {
  line-height: 1.4;
}

/* 优雅的 Vue 路由/动态列表入场与离场过渡动画 */
.toast-slide-enter-from {
  opacity: 0;
  transform: translateX(40px) scale(0.95);
}
.toast-slide-enter-to {
  opacity: 1;
  transform: translateX(0) scale(1);
}
.toast-slide-leave-from {
  opacity: 1;
  transform: translateY(0);
}
.toast-slide-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}
.toast-slide-enter-active,
.toast-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
</style>