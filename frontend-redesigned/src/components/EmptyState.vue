<template>
  <div class="empty-state">
    <div class="empty-illustration">
      <div class="empty-icon">{{ icon }}</div>
      <div class="empty-circles">
        <div class="circle circle-1"></div>
        <div class="circle circle-2"></div>
        <div class="circle circle-3"></div>
      </div>
    </div>

    <h3 class="empty-title">{{ title }}</h3>
    <p class="empty-description">{{ description }}</p>

    <div v-if="actionText" class="empty-action">
      <button class="empty-btn" @click="$emit('action')">
        {{ actionText }}
      </button>
    </div>

    <div v-if="tips && tips.length" class="empty-tips">
      <div v-for="(tip, index) in tips" :key="index" class="tip-item">
        <span class="tip-icon">💡</span>
        <span class="tip-text">{{ tip }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  icon?: string
  title: string
  description: string
  actionText?: string
  tips?: string[]
}>()

defineEmits<{
  action: []
}>()
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
  text-align: center;
  max-width: 400px;
  margin: 0 auto;
}

.empty-illustration {
  position: relative;
  width: 120px;
  height: 120px;
  margin-bottom: 32px;
}

.empty-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 48px;
  z-index: 2;
  animation: float 3s ease-in-out infinite;
}

.empty-circles {
  position: absolute;
  inset: 0;
}

.circle {
  position: absolute;
  border-radius: 50%;
  border: 2px dashed #d4cfc9;
  animation: pulse 3s ease-in-out infinite;
}

.circle-1 {
  inset: 0;
  animation-delay: 0s;
}

.circle-2 {
  inset: 10px;
  animation-delay: 0.5s;
}

.circle-3 {
  inset: 20px;
  animation-delay: 1s;
}

@keyframes float {
  0%, 100% {
    transform: translate(-50%, -50%) translateY(0);
  }
  50% {
    transform: translate(-50%, -50%) translateY(-8px);
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.5;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.05);
  }
}

.empty-title {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 600;
  color: #2c2520;
  margin-bottom: 12px;
}

.empty-description {
  font-size: 0.95rem;
  color: #8a7e75;
  line-height: 1.6;
  margin-bottom: 24px;
}

.empty-action {
  margin-bottom: 32px;
}

.empty-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 28px;
  background: #c67b5c;
  color: white;
  border: none;
  border-radius: 8px;
  font-family: var(--font-body);
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.22, 1, 0.36, 1);
}

.empty-btn:hover {
  background: #a65d3f;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(198, 123, 92, 0.3);
}

.empty-tips {
  width: 100%;
  max-width: 300px;
  background: #f9f6f2;
  border-radius: 12px;
  padding: 16px;
}

.tip-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 0;
}

.tip-item:not(:last-child) {
  border-bottom: 1px solid #e8e4df;
}

.tip-icon {
  flex-shrink: 0;
}

.tip-text {
  font-size: 0.85rem;
  color: #5a524a;
  text-align: left;
  line-height: 1.4;
}
</style>
