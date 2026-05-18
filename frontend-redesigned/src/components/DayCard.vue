<template>
  <div class="day-card" :class="{ expanded }">
    <div class="day-card-header" @click="$emit('toggle')">
      <div class="day-card-left">
        <span class="day-number">{{ dayNumber }}</span>
        <div class="day-meta">
          <span class="day-date">{{ formatDate(day.date) }} · {{ getWeekday(day.date) }}</span>
          <span class="day-desc">{{ day.description }}</span>
        </div>
      </div>
      <div class="day-card-right">
        <span class="day-stat">{{ day.attractions.length }} 景点</span>
        <span class="day-stat" v-if="day.meals?.length">{{ day.meals.length }} 餐</span>
        <span class="day-stat day-stat--hotel" v-if="day.hotel">住宿</span>
        <span class="day-card-chevron" :class="{ rotated: expanded }">›</span>
      </div>
    </div>

    <transition name="expand">
      <div v-if="expanded" class="day-card-body">
        <!-- Day 1 Arrival Info -->
        <div v-if="dayIndex === 0 && transportInfo && transportInfo.departure_city" class="arrival-banner">
          <span class="arrival-icon">{{ transportInfo.recommended_mode?.includes('飞机') ? '✈️' : '🚄' }}</span>
          <div class="arrival-info">
            <span class="arrival-route">{{ transportInfo.departure_city }} → {{ transportInfo.destination_city }}</span>
            <span class="arrival-detail">{{ transportInfo.recommended_mode }} · {{ transportInfo.estimated_duration }} · 约¥{{ transportInfo.estimated_cost }}</span>
          </div>
        </div>

        <!-- Inter-day Connection -->
        <div v-if="dayIndex > 0 && prevHotel" class="interday-banner">
          <span class="interday-icon">🔄</span>
          <div class="interday-info">
            <span class="interday-text">从 {{ prevHotel.name || '酒店' }} 出发</span>
          </div>
        </div>

        <!-- Attractions -->
        <div class="day-section" v-if="day.attractions.length">
          <h4 class="day-section-title">
            <span class="section-icon">✦</span> 景点
          </h4>
          <div class="attractions-list">
            <div
              v-for="(attraction, index) in day.attractions"
              :key="index"
              class="attraction-card"
            >
              <div class="attraction-content">
                <div class="attraction-info">
                  <div class="attraction-header">
                    <span class="attraction-number">{{ index + 1 }}</span>
                    <h5 v-if="!editMode" class="attraction-name">{{ attraction.name }}</h5>
                    <input v-else v-model="attraction.name" class="edit-input edit-input--name" placeholder="景点名称" />
                    <button
                      v-if="!editMode"
                      class="expand-toggle"
                      @click.stop="$emit('toggle-detail', index)"
                    >
                      {{ expandedDetails[`${dayIndex}-${index}`] ? '收起' : '详情' }}
                    </button>
                  </div>
                  <p class="attraction-address">📍 {{ attraction.address }}</p>
                  <div class="attraction-meta">
                    <span class="meta-tag">⏱ {{ attraction.visit_duration }}分钟</span>
                    <span v-if="attraction.ticket_price" class="meta-tag">🎫 ¥{{ attraction.ticket_price }}</span>
                    <span v-if="attraction.rating" class="meta-tag">⭐ {{ attraction.rating }}</span>
                  </div>

                  <!-- Edit fields -->
                  <div v-if="editMode" class="edit-fields">
                    <input v-model="attraction.address" class="edit-input" placeholder="地址" />
                    <input v-model.number="attraction.visit_duration" type="number" class="edit-input" placeholder="游览时间(分钟)" />
                    <input v-model.number="attraction.ticket_price" type="number" class="edit-input" placeholder="门票价格" />
                    <input v-model.number="attraction.rating" type="number" step="0.1" class="edit-input" placeholder="评分" />
                  </div>

                  <!-- Expanded details -->
                  <transition name="expand">
                    <div v-if="expandedDetails[`${dayIndex}-${index}`] && !editMode" class="attraction-details">
                      <p v-if="attraction.description">{{ attraction.description }}</p>
                      <p v-if="attraction.opening_hours">🕐 {{ attraction.opening_hours }}</p>
                      <p v-if="attraction.transportation">🚗 {{ attraction.transportation }}</p>
                      <p v-if="attraction.notes">📝 {{ attraction.notes }}</p>
                    </div>
                  </transition>
                </div>
                <div class="attraction-image-wrap" v-if="attraction.image_url">
                  <img :src="attraction.image_url" :alt="attraction.name" loading="lazy" class="attraction-image" />
                </div>
              </div>
              <div v-if="editMode" class="attraction-actions">
                <button @click.stop="$emit('move', index, 'up')" class="action-btn">↑</button>
                <button @click.stop="$emit('move', index, 'down')" class="action-btn">↓</button>
                <button @click.stop="$emit('delete', index)" class="action-btn action-btn--danger">✕</button>
              </div>
            </div>
          </div>
          <button v-if="editMode" class="add-btn" @click="$emit('add')">+ 添加景点</button>
        </div>

        <!-- Meals -->
        <div class="day-section" v-if="day.meals?.length">
          <h4 class="day-section-title">
            <span class="section-icon">✦</span> 餐饮
          </h4>
          <div class="meals-grid">
            <div v-for="meal in day.meals" :key="meal.type" class="meal-item">
              <span class="meal-emoji">{{ getMealEmoji(meal.type) }}</span>
              <div class="meal-info">
                <span class="meal-name">{{ meal.name }}</span>
                <span class="meal-cost">≈ ¥{{ meal.estimated_cost }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Hotel -->
        <div class="day-section" v-if="day.hotel">
          <h4 class="day-section-title">
            <span class="section-icon">✦</span> 住宿
          </h4>
          <div class="hotel-card">
            <div class="hotel-info">
              <h5 class="hotel-name">{{ day.hotel.name }}</h5>
              <p class="hotel-address">📍 {{ day.hotel.address }}</p>
              <div class="hotel-meta">
                <span class="meta-tag">💰 ≈¥{{ day.hotel.estimated_cost }}/晚</span>
                <span v-if="day.hotel.rating" class="meta-tag">⭐ {{ day.hotel.rating }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import type { DayPlan, TransportInfo } from '@/types'

const props = defineProps<{
  day: DayPlan
  dayNumber: number
  dayIndex: number
  expanded: boolean
  editMode: boolean
  expandedDetails: Record<string, boolean>
  transportInfo?: TransportInfo
  prevHotel?: { name?: string; address?: string } | null
}>()

defineEmits<{
  toggle: []
  'toggle-detail': [index: number]
  move: [index: number, direction: string]
  delete: [index: number]
  add: []
}>()

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}月${d.getDate()}日`
}

const getWeekday = (dateStr: string) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][d.getDay()]
}

const getMealEmoji = (type: string) => {
  return { breakfast: '🌅', lunch: '☀️', dinner: '🌙', snack: '🍿' }[type] || '🍽️'
}

</script>

<style scoped>
.day-card {
  background: var(--color-paper);
  border-radius: var(--radius-lg);
  border: 1px solid rgba(232, 226, 218, 0.6);
  overflow: hidden;
  transition: all var(--transition-normal);
  margin-bottom: var(--space-md);
}

.day-card:hover {
  box-shadow: var(--shadow-card);
}

.day-card.expanded {
  box-shadow: var(--shadow-elevated);
  border-color: rgba(196, 101, 74, 0.15);
}

.day-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-lg);
  cursor: pointer;
  transition: background var(--transition-fast);
  gap: var(--space-md);
}

.day-card-header:hover {
  background: var(--color-sand-light);
}

.day-card-left {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.day-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  background: var(--color-terracotta);
  color: white;
  font-family: var(--font-display);
  font-size: 1.3rem;
  font-weight: 700;
  flex-shrink: 0;
}

.day-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.day-date {
  font-size: 0.8rem;
  color: var(--color-warm-gray);
  font-weight: 500;
}

.day-desc {
  font-family: var(--font-display);
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--color-charcoal);
}

.day-card-right {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-shrink: 0;
}

.day-stat {
  font-size: 0.75rem;
  color: var(--color-warm-gray);
  background: var(--color-sand-light);
  padding: 3px 10px;
  border-radius: 100px;
  font-weight: 500;
}

.day-stat--hotel {
  background: rgba(196, 101, 74, 0.08);
  color: var(--color-terracotta);
}

.day-card-chevron {
  font-size: 1.2rem;
  color: var(--color-warm-gray);
  transition: transform var(--transition-fast);
  font-weight: 300;
}

.day-card-chevron.rotated {
  transform: rotate(90deg);
  color: var(--color-terracotta);
}

.day-card-body {
  padding: 0 var(--space-lg) var(--space-lg);
}

.day-section {
  margin-bottom: var(--space-lg);
}

.day-section:last-child {
  margin-bottom: 0;
}

.day-section-title {
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-charcoal);
  margin-bottom: var(--space-md);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.section-icon {
  color: var(--color-terracotta);
  font-size: 0.8rem;
}

/* Attractions */
.attractions-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.attraction-card {
  border: 1px solid rgba(232, 226, 218, 0.6);
  border-radius: var(--radius-md);
  overflow: hidden;
  transition: all var(--transition-fast);
}

.attraction-card:hover {
  border-color: rgba(196, 101, 74, 0.2);
  box-shadow: var(--shadow-subtle);
}

.attraction-content {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-md);
}

.attraction-info {
  flex: 1;
  min-width: 0;
}

.attraction-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-sm);
  margin-bottom: 4px;
}

.attraction-name {
  font-family: var(--font-display);
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--color-charcoal);
  margin: 0;
}

.expand-toggle {
  background: none;
  border: none;
  color: var(--color-terracotta);
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
  flex-shrink: 0;
}

.expand-toggle:hover {
  background: rgba(196, 101, 74, 0.06);
}

.attraction-address {
  font-size: 0.85rem;
  color: var(--color-warm-gray);
  margin-bottom: 6px;
}

.attraction-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.meta-tag {
  font-size: 0.75rem;
  color: var(--color-warm-gray);
  background: var(--color-sand-light);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-weight: 500;
}

.attraction-image-wrap {
  width: 140px;
  height: 100px;
  border-radius: var(--radius-md);
  overflow: hidden;
  flex-shrink: 0;
  background: var(--color-sand);
}

.attraction-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform var(--transition-normal);
}

.attraction-card:hover .attraction-image {
  transform: scale(1.05);
}

.attraction-details {
  margin-top: var(--space-sm);
  padding: var(--space-md);
  background: var(--color-sand-light);
  border-radius: var(--radius-md);
}

.attraction-details p {
  font-size: 0.85rem;
  color: var(--color-warm-gray);
  margin-bottom: 4px;
  line-height: 1.5;
}

.attraction-details p:last-child {
  margin-bottom: 0;
}

.attraction-actions {
  display: flex;
  gap: 6px;
  padding: 8px var(--space-md);
  border-top: 1px solid rgba(232, 226, 218, 0.6);
}

.action-btn {
  padding: 4px 12px;
  border: 1px solid var(--color-light-gray);
  border-radius: var(--radius-sm);
  background: var(--color-paper);
  cursor: pointer;
  font-size: 0.8rem;
  transition: all var(--transition-fast);
}

.action-btn:hover {
  border-color: var(--color-terracotta);
  color: var(--color-terracotta);
}

.action-btn--danger:hover {
  border-color: #e74c3c;
  color: #e74c3c;
  background: rgba(231, 76, 60, 0.04);
}

.add-btn {
  width: 100%;
  padding: 10px;
  border: 2px dashed var(--color-light-gray);
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-warm-gray);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.add-btn:hover {
  border-color: var(--color-terracotta);
  color: var(--color-terracotta);
  background: rgba(196, 101, 74, 0.03);
}

/* Meals */
.meals-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--space-sm);
}

.meal-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 10px 14px;
  background: var(--color-sand-light);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.meal-item:hover {
  background: var(--color-sand);
}

.meal-emoji {
  font-size: 1.2rem;
}

.meal-info {
  display: flex;
  flex-direction: column;
}

.meal-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--color-charcoal);
}

.meal-cost {
  font-size: 0.75rem;
  color: var(--color-warm-gray);
}

/* Hotel */
.hotel-card {
  padding: var(--space-md);
  background: var(--color-sand-light);
  border-radius: var(--radius-md);
  border: 1px solid rgba(232, 226, 218, 0.6);
}

.hotel-name {
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-charcoal);
  margin: 0 0 4px 0;
}

.hotel-address {
  font-size: 0.85rem;
  color: var(--color-warm-gray);
  margin-bottom: 6px;
}

.hotel-meta {
  display: flex;
  gap: 6px;
}

/* Edit inputs */
.edit-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--color-light-gray);
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 0.85rem;
  margin-bottom: 6px;
  transition: border-color var(--transition-fast);
  outline: none;
  background: var(--color-paper);
}

.edit-input:focus {
  border-color: var(--color-terracotta);
}

.edit-input--name {
  font-weight: 600;
  font-size: 0.95rem;
}

.edit-fields {
  margin-top: var(--space-sm);
}

/* Transitions */
.expand-enter-active {
  animation: expandDown 300ms var(--ease-out-expo);
}
.expand-leave-active {
  animation: expandDown 200ms ease reverse;
}
@keyframes expandDown {
  from {
    opacity: 0;
    max-height: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    max-height: 2000px;
    transform: translateY(0);
  }
}

@media (max-width: 768px) {
  .day-card-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .day-card-right {
    width: 100%;
    flex-wrap: wrap;
  }

  .attraction-content {
    flex-direction: column;
  }

  .attraction-image-wrap {
    width: 100%;
    height: 160px;
  }
}

/* Arrival Banner */
.arrival-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin: 0 16px 12px;
  background: linear-gradient(135deg, #eff6ff, #f0f9ff);
  border-radius: 10px;
  border: 1px solid #bfdbfe;
}

.arrival-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.arrival-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.arrival-route {
  font-size: 13px;
  font-weight: 600;
  color: #1e40af;
}

.arrival-detail {
  font-size: 11px;
  color: #64748b;
}

/* Inter-day Banner */
.interday-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  margin: 0 16px 12px;
  background: linear-gradient(135deg, #f1f5f9, #f8fafc);
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}

.interday-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.interday-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.interday-text {
  font-size: 12px;
  font-weight: 500;
  color: #475569;
}

/* Numbered attraction marker */
.attraction-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--color-accent, #C4654A);
  color: white;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
  font-family: var(--font-body);
}
</style>
