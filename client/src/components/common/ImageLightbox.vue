<template>
  <Teleport to="body">
    <Transition name="fade">
      <div 
        v-if="isOpen" 
        class="lightbox-backdrop" 
        @click.self="handleClose" 
        @keydown.esc="handleClose" 
        tabindex="0" 
        ref="backdropRef"
      >
        <div class="lightbox-container" @click.self="handleClose">
          <!-- Close Button -->
          <button class="btn-close-lightbox" @click="handleClose" title="Close Preview">&times;</button>
          
          <!-- Image Stage -->
          <div 
            class="lightbox-stage" 
            @click.self="handleClose"
            @wheel.prevent="handleWheel"
            @mousedown="handleMouseDown"
            @mousemove="handleMouseMove"
            @mouseup="handleMouseUp"
            @mouseleave="handleMouseUp"
            :style="{ cursor: isDragging ? 'grabbing' : 'grab' }"
          >
            <img 
              :src="imageUrl" 
              :style="imgStyle" 
              alt="Preview" 
              class="lightbox-image" 
              draggable="false"
            />
          </div>

          <!-- Controls Toolbar -->
          <div class="lightbox-toolbar">
            <!-- Info / Traceability -->
            <div class="lightbox-info">
              <span class="info-title">📄 {{ truncateFileName(filename, 32) }}</span>
              <span class="info-meta">Uploaded by {{ uploader }} {{ logContext ? '· ' + logContext : '' }}</span>
            </div>

            <!-- Action Controls -->
            <div class="info-actions">
              <button class="tool-btn" @click="zoomIn" title="Zoom In (Scroll Wheel)">➕ Zoom In</button>
              <button class="tool-btn" @click="zoomOut" title="Zoom Out (Scroll Wheel)">➖ Zoom Out</button>
              <button class="tool-btn" @click="rotateClockwise" title="Rotate Clockwise 90°">🔄 Rotate</button>
              <button class="tool-btn" @click="resetTransforms" title="Reset Transforms">↩️ Reset</button>
              <button v-if="allowDownload" class="tool-btn btn-download-raw" @click="$emit('download', filename)" title="Download Raw File">⬇️ Download</button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue';

const props = defineProps({
  isOpen: { type: Boolean, required: true },
  imageUrl: { type: String, required: true },
  filename: { type: String, default: '' },
  uploader: { type: String, default: 'Unknown' },
  logContext: { type: String, default: '' },
  allowDownload: { type: Boolean, default: true }
});

const emit = defineEmits(['close', 'download']);

const scale = ref(1);
const translateX = ref(0);
const translateY = ref(0);
const rotate = ref(0);
const backdropRef = ref(null);
const isDragging = ref(false);

const imgStyle = computed(() => {
  return {
    transform: `translate(${translateX.value}px, ${translateY.value}px) scale(${scale.value}) rotate(${rotate.value}deg)`,
    transition: isDragging.value ? 'none' : 'transform 0.15s ease-out'
  };
});

// Drag tracking coordinates
const startX = ref(0);
const startY = ref(0);

const handleClose = () => {
  emit('close');
};

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    resetTransforms();
    nextTick(() => {
      if (backdropRef.value) {
        backdropRef.value.focus();
      }
    });
  }
});

const resetTransforms = () => {
  scale.value = 1;
  translateX.value = 0;
  translateY.value = 0;
  rotate.value = 0;
};

const handleWheel = (e) => {
  const zoomFactor = 0.12;
  if (e.deltaY < 0) {
    scale.value = Math.min(scale.value + zoomFactor, 6);
  } else {
    scale.value = Math.max(scale.value - zoomFactor, 0.4);
  }
};

const handleMouseDown = (e) => {
  isDragging.value = true;
  startX.value = e.clientX - translateX.value;
  startY.value = e.clientY - translateY.value;
};

const handleMouseMove = (e) => {
  if (!isDragging.value) return;
  translateX.value = e.clientX - startX.value;
  translateY.value = e.clientY - startY.value;
};

const handleMouseUp = () => {
  isDragging.value = false;
};

const zoomIn = () => {
  scale.value = Math.min(scale.value + 0.3, 6);
};

const zoomOut = () => {
  scale.value = Math.max(scale.value - 0.3, 0.4);
};

const rotateClockwise = () => {
  rotate.value = (rotate.value + 90) % 360;
};

const truncateFileName = (name, length = 20) => {
  if (!name) return '';
  if (name.length <= length) return name;
  const extIndex = name.lastIndexOf('.');
  if (extIndex === -1) return name.slice(0, length) + '...';
  const ext = name.slice(extIndex);
  const base = name.slice(0, extIndex);
  const baseLen = length - ext.length - 3;
  if (baseLen <= 0) return name.slice(0, length) + '...';
  return base.slice(0, baseLen) + '...' + ext;
};
</script>

<style scoped>
.lightbox-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(15, 23, 42, 0.86);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  z-index: 99999;
  display: flex;
  justify-content: center;
  align-items: center;
  outline: none;
}

.lightbox-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.btn-close-lightbox {
  position: absolute;
  top: 24px;
  right: 24px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #f8fafc;
  font-size: 28px;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  z-index: 100010;
  line-height: 1;
}

.btn-close-lightbox:hover {
  background: rgba(239, 68, 68, 0.25);
  border-color: rgba(239, 68, 68, 0.4);
  color: #fca5a5;
  transform: scale(1.08);
}

.lightbox-stage {
  flex: 1;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  user-select: none;
  touch-action: none;
}

.lightbox-image {
  max-width: 85vw;
  max-height: 80vh;
  object-fit: contain;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.lightbox-toolbar {
  width: auto;
  max-width: 90%;
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 14px 28px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 36px;
  margin-bottom: 32px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4);
  z-index: 100005;
}

.lightbox-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  color: #f8fafc;
  min-width: 180px;
}

.info-title {
  font-size: 13.5px;
  font-weight: 600;
  letter-spacing: -0.15px;
  color: #f1f5f9;
}

.info-meta {
  font-size: 11px;
  color: #94a3b8;
  margin-top: 3px;
}

.info-actions {
  display: flex;
  gap: 10px;
}

.tool-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #f1f5f9;
  padding: 7px 14px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.tool-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.25);
  transform: translateY(-1px);
}

.btn-download-raw {
  background: #2563eb;
  border-color: #2563eb;
  color: #ffffff;
}

.btn-download-raw:hover {
  background: #1d4ed8;
  border-color: #1d4ed8;
}

/* Transition animations */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
