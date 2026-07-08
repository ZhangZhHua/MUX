<template>
  <div class="mux-logo-container" @click="goHome">
    <!-- 1. MUX 核心多路复用图标 (内联高精细度 SVG) -->
    <div class="icon-wrapper">
      <!-- 碰撞中心的外部呼吸光晕效果 -->
      <div class="glow-dot"></div>
      
      <svg 
        class="logo-svg" 
        viewBox="0 0 32 32" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
      >
        <!-- 轨迹线 1 (上方束流弯曲汇聚) -->
        <path 
          d="M4 8C12 8 16 16 24 16" 
          stroke="url(#mux-gradient-cyan)" 
          stroke-width="2.5" 
          stroke-linecap="round"
          class="track-line"
        />
        <!-- 轨迹线 2 (中央束流直线穿透) -->
        <path 
          d="M4 16H24" 
          stroke="url(#mux-gradient-cyan)" 
          stroke-width="2.5" 
          stroke-linecap="round"
        />
        <!-- 轨迹线 3 (下方束流弯曲汇聚) -->
        <path 
          d="M4 24C12 24 16 16 24 16" 
          stroke="url(#mux-gradient-cyan)" 
          stroke-width="2.5" 
          stroke-linecap="round"
          class="track-line"
        />
        
        <!-- 聚焦碰撞中心 (信号聚合核心点) -->
        <circle 
          cx="24" 
          cy="16" 
          r="3.5" 
          fill="#22d3ee" 
          class="pulse-circle"
        />
        <circle 
          cx="24" 
          cy="16" 
          r="1.5" 
          fill="#ffffff" 
        />

        <!-- SVG 渐变色定义 -->
        <defs>
          <linearGradient id="mux-gradient-cyan" x1="4" y1="16" x2="24" y2="16" gradientUnits="userSpaceOnUse">
            <stop stop-color="#312e81" stop-opacity="0.4" /> <!-- 始于深邃暗蓝 -->
            <stop offset="0.5" stop-color="#6366f1" />     <!-- 经过靛蓝加速 -->
            <stop offset="1" stop-color="#22d3ee" />       <!-- 汇聚于耀眼青色 -->
          </linearGradient>
        </defs>
      </svg>
    </div>

    <!-- 2. 品牌文本排版 (Typography) -->
    <div class="brand-text-wrapper">
      <span class="brand-title">MUX</span>
      <span class="brand-subtitle">LAB DATA OS</span>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';

const router = useRouter();

const goHome = () => {
  router.push('/');
};
</script>

<style scoped>
.mux-logo-container {
  display: flex;
  align-items: center;
  gap: 12px;
  user-select: none;
  cursor: pointer;
}

/* 核心 SVG 容器与光晕 */
.icon-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.glow-dot {
  position: absolute;
  right: 4px;
  width: 12px;
  height: 12px;
  background: rgba(6, 182, 212, 0.3);
  border-radius: 50%;
  filter: blur(6px);
  transition: background-color 0.3s ease;
  animation: pulse-glow 2s infinite ease-in-out;
}

.mux-logo-container:hover .glow-dot {
  background: rgba(34, 211, 238, 0.5);
}

@keyframes pulse-glow {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

/* SVG 图形与动效 */
.logo-svg {
  width: 32px;
  height: 32px;
  color: #94a3b8; /* slate-400 */
  transition: color 0.3s ease;
}

.mux-logo-container:hover .logo-svg {
  color: #ffffff;
}

.track-line {
  opacity: 0.7;
  transition: opacity 0.3s ease;
}

.mux-logo-container:hover .track-line {
  opacity: 1;
}

.pulse-circle {
  animation: pulse-circle-anim 1.5s infinite ease-in-out;
}

@keyframes pulse-circle-anim {
  0%, 100% { transform: scale(1); transform-origin: 24px 16px; }
  50% { transform: scale(1.15); transform-origin: 24px 16px; }
}

/* 品牌文字布局 */
.brand-text-wrapper {
  display: flex;
  flex-direction: column;
  justify-content: center;
  border-left: 1px solid rgba(226, 232, 240, 0.15); /* 适配网站的暗淡灰白分割线 */
  padding-left: 12px;
}

.brand-title {
  font-size: 20px;
  font-weight: 900;
  letter-spacing: 0.05em;
  line-height: 1;
  background: linear-gradient(to right, #22d3ee, #5eead4, #818cf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  transition: all 0.3s ease;
  font-family: system-ui, -apple-system, sans-serif;
}

.mux-logo-container:hover .brand-title {
  background: linear-gradient(to right, #67e8f9, #a5f3fc, #c7d2fe);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.brand-subtitle {
  font-size: 9px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-weight: 500;
  letter-spacing: 0.15em;
  color: #64748b; /* slate-500 */
  text-transform: uppercase;
  margin-top: 2px;
  transition: color 0.3s ease;
}

.mux-logo-container:hover .brand-subtitle {
  color: rgba(34, 211, 238, 0.8);
}
</style>
