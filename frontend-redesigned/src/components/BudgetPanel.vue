<template>
  <div class="budget-panel">
    <div class="budget-grid">
      <div
        v-for="item in budgetItems"
        :key="item.key"
        class="budget-item"
      >
        <div class="budget-item-header">
          <span class="budget-icon">{{ item.icon }}</span>
          <span class="budget-label">{{ item.label }}</span>
        </div>
        <div class="budget-value">¥{{ item.value }}</div>
        <div class="budget-bar-track">
          <div
            class="budget-bar-fill"
            :style="{
              width: budget.total ? Math.round((item.value / budget.total) * 100) + '%' : '0%',
              background: item.color
            }"
          ></div>
        </div>
        <span class="budget-percent">
          {{ budget.total ? Math.round((item.value / budget.total) * 100) : 0 }}%
        </span>
      </div>
    </div>

    <div class="budget-total">
      <span class="total-label">预估总费用</span>
      <span class="total-value">¥{{ budget.total }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Budget } from '@/types'

const props = defineProps<{ budget: Budget }>()

const budgetItems = computed(() => [
  { key: 'attractions', icon: '🎫', label: '景点门票', value: props.budget.total_attractions, color: 'var(--color-terracotta)' },
  { key: 'hotels', icon: '🏨', label: '酒店住宿', value: props.budget.total_hotels, color: 'var(--color-forest)' },
  { key: 'meals', icon: '🍜', label: '餐饮费用', value: props.budget.total_meals, color: 'var(--color-sunset)' },
  { key: 'transport', icon: '🚗', label: '交通费用', value: props.budget.total_transportation, color: 'var(--color-sage)' },
])
</script>

<style scoped>
.budget-panel {
  padding: var(--space-lg);
}

.budget-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-md);
  margin-bottom: var(--space-lg);
}

.budget-item {
  padding: var(--space-md);
  background: var(--color-sand-light);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.budget-item:hover {
  background: var(--color-sand);
  transform: translateY(-2px);
}

.budget-item-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.budget-icon {
  font-size: 1rem;
}

.budget-label {
  font-size: 0.8rem;
  color: var(--color-warm-gray);
  font-weight: 500;
}

.budget-value {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-charcoal);
  margin-bottom: 8px;
}

.budget-bar-track {
  width: 100%;
  height: 4px;
  background: rgba(232, 226, 218, 0.6);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 6px;
}

.budget-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 600ms var(--ease-out-expo);
}

.budget-percent {
  font-size: 0.75rem;
  color: var(--color-warm-gray);
  font-weight: 500;
}

.budget-total {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-lg);
  background: var(--color-forest);
  border-radius: var(--radius-lg);
}

.total-label {
  font-family: var(--font-body);
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
}

.total-value {
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 700;
  color: white;
}

@media (max-width: 768px) {
  .budget-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .budget-grid {
    grid-template-columns: 1fr;
  }
}
</style>
