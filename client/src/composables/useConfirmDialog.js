import { ref } from 'vue';

// 全局确认弹窗状态
const show = ref(false);
const title = ref('');
const message = ref('');
let resolveCallback = null;

export function useConfirmDialog() {
  const confirm = (msg, t = 'Confirm Action') => {
    return new Promise((resolve) => {
      title.value = t;
      message.value = msg;
      show.value = true;
      resolveCallback = resolve;
    });
  };

  const onConfirm = () => {
    show.value = false;
    if (resolveCallback) resolveCallback(true);
    resolveCallback = null;
  };

  const onCancel = () => {
    show.value = false;
    if (resolveCallback) resolveCallback(false);
    resolveCallback = null;
  };

  return {
    show,
    title,
    message,
    confirm,
    onConfirm,
    onCancel
  };
}