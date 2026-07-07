import { ref } from 'vue';

// 全局唯一的通知队列状态（跨页面共享）
const toasts = ref([]);

export function useToast() {
  const show = (message, type = 'info', duration = 3000) => {
    const id = Date.now() + Math.random();
    
    // 将新通知推入队列
    toasts.value.push({ id, message, type });

    // 到期后自动移除，实现无感淡出
    setTimeout(() => {
      toasts.value = toasts.value.filter(t => t.id !== id);
    }, duration);
  };

  const dismiss = (id) => {
    toasts.value = toasts.value.filter(t => t.id !== id);
  };

  return {
    toasts,
    success: (msg) => show(msg, 'success'),
    error: (msg) => show(msg, 'error'),
    info: (msg) => show(msg, 'info'),
    dismiss
  };
}