<template>
  <Transition name="overlay">
    <div v-if="visible" class="loading-overlay">
      <div class="loading-content">
        <!-- Agent Status Cards -->
        <div class="agent-grid">
          <div
            v-for="(agent, index) in agents"
            :key="agent.id"
            class="agent-card"
            :class="{
              'agent-card--active': currentStep === index,
              'agent-card--done': agent.done,
            }"
            :style="{ animationDelay: `${index * 100}ms` }"
          >
            <div class="agent-icon">{{ agent.icon }}</div>
            <div class="agent-info">
              <div class="agent-name">{{ agent.name }}</div>
              <div class="agent-status">{{ agent.status }}</div>
            </div>
            <div v-if="agent.done" class="agent-check">✓</div>
          </div>
        </div>

        <!-- Progress Bar -->
        <div class="progress-container">
          <div class="progress-bar" :style="{ width: `${progress}%` }"></div>
        </div>

        <!-- Status Text -->
        <div class="status-text">
          <span class="status-dot"></span>
          {{ statusText }}
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps<{
  visible: boolean
  progress: number
  currentStep: number
}>()

const agents = ref([
  { id: 'attraction', name: '景点专家', icon: '🔍', status: '等待中...', done: false },
  { id: 'weather', name: '天气专家', icon: '🌤️', status: '等待中...', done: false },
  { id: 'hotel', name: '住宿专家', icon: '🏨', status: '等待中...', done: false },
  { id: 'planner', name: '规划专家', icon: '📋', status: '等待中...', done: false },
])

const statusText = ref('准备中...')

const statusMessages = [
  '正在分析您的偏好...',
  '景点专家正在搜索最佳去处...',
  '天气专家正在查询预报...',
  '住宿专家正在筛选酒店...',
  '规划专家正在整合信息...',
  '正在生成专属行程...',
]

watch(
  () => props.currentStep,
  (step) => {
    agents.value.forEach((agent, i) => {
      if (i < step) {
        agent.done = true
        agent.status = '已完成'
      } else if (i === step) {
        agent.status = '工作中...'
      } else {
        agent.status = '等待中...'
      }
    })
    statusText.value = statusMessages[Math.min(step, statusMessages.length - 1)]
  },
)

watch(
  () => props.progress,
  (p) => {
    if (p >= 100) {
      statusText.value = '生成完成！'
    }
  },
)
</script>

<style scoped>
.loading-overlay {
  position: fixed;
  inset: 0;
  background: rgba(255, 252, 247, 0.95);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-content {
  max-width: 420px;
  width: 100%;
  padding: 0 24px;
}

.agent-grid {
  display: grid;
  gap: 12px;
  margin-bottom: 32px;
}

.agent-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: white;
  border-radius: 12px;
  border: 1px solid #e8e4df;
  opacity: 0.5;
  transform: translateX(-8px);
  transition: all 0.4s cubic-bezier(0.22, 1, 0.36, 1);
}

.agent-card--active {
  opacity: 1;
  transform: translateX(0);
  border-color: #c67b5c;
  box-shadow: 0 4px 20px rgba(198, 123, 92, 0.15);
}

.agent-card--done {
  opacity: 0.7;
  transform: translateX(0);
}

.agent-icon {
  font-size: 24px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f0eb;
  border-radius: 10px;
  flex-shrink: 0;
}

.agent-card--active .agent-icon {
  background: #c67b5c;
  animation: pulse 2s ease-in-out infinite;
}

.agent-card--done .agent-icon {
  background: #2d4a3e;
}

.agent-info {
  flex: 1;
  min-width: 0;
}

.agent-name {
  font-family: var(--font-body);
  font-weight: 600;
  font-size: 0.95rem;
  color: #2c2520;
}

.agent-status {
  font-size: 0.8rem;
  color: #8a7e75;
  margin-top: 2px;
}

.agent-check {
  width: 24px;
  height: 24px;
  background: #2d4a3e;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
}

.progress-container {
  height: 3px;
  background: #e8e4df;
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 20px;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #c67b5c, #a65d3f);
  border-radius: 2px;
  transition: width 0.5s cubic-bezier(0.22, 1, 0.36, 1);
}

.status-text {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 0.9rem;
  color: #5a524a;
}

.status-dot {
  width: 6px;
  height: 6px;
  background: #c67b5c;
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(0.8);
  }
}

.overlay-enter-active {
  animation: fadeIn 0.3s ease;
}

.overlay-leave-active {
  animation: fadeOut 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes fadeOut {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}
</style>
