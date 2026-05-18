<template>
  <div class="comparison">
    <!-- Loading -->
    <div v-if="loading" class="comparison-loading">
      <div class="loading-content">
        <div class="loading-spinner"></div>
        <p>加载方案数据...</p>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="comparison-error">
      <EmptyState
        icon="📋"
        title="无法加载方案"
        description="方案数据为空或已过期，请返回首页重新规划"
        actionText="返回首页"
        @action="$router.push('/')"
      />
    </div>

    <!-- Content -->
    <div v-else class="comparison-content">
      <!-- Top Bar -->
      <nav class="topbar">
        <button class="topbar-back" @click="$router.push('/')">
          <span class="back-arrow">←</span>
          <span>返回</span>
        </button>
        <div class="topbar-title">选择你心仪的方案</div>
        <div class="topbar-spacer"></div>
      </nav>

      <!-- Header -->
      <header class="comparison-header">
        <h1 class="header-title">{{ city }}之旅</h1>
        <p class="header-subtitle">三种旅行风格，同一份预算</p>
      </header>

      <!-- Mobile Tabs -->
      <div class="mobile-tabs">
        <button
          v-for="(v, i) in variants"
          :key="v.variant"
          :class="['mobile-tab', { active: activeMobileIndex === i }]"
          @click="activeMobileIndex = i"
        >
          {{ getStyleIcon(v.variant) }} {{ getStyleLabel(v.variant) }}
        </button>
      </div>

      <!-- Desktop Grid -->
      <div ref="gridRef" class="comparison-grid">
        <div
          v-for="(v, i) in variants"
          :key="v.variant"
          :class="['comparison-card', { 'card-failed': !v.plan }]"
          :style="{ animationDelay: `${i * 120}ms` }"
        >
          <!-- Card Header -->
          <div class="card-header">
            <div class="card-icon">{{ getStyleIcon(v.variant) }}</div>
            <h2 class="card-name">{{ v.plan?.overall_suggestions ? getPlanName(v) : getStyleLabel(v.variant) }}</h2>
            <span class="card-style">{{ getStyleLabel(v.variant) }}</span>
            <span v-if="v.plan && getRecommendTag(v, i)" class="card-recommend">{{ getRecommendTag(v, i) }}</span>
          </div>

          <!-- Card Stats -->
          <div v-if="v.plan" class="card-stats">
            <div class="stat">
              <span class="stat-value">{{ v.plan.days.length }}</span>
              <span class="stat-label">天</span>
            </div>
            <div class="stat">
              <span class="stat-value">{{ totalAttractions(v.plan) }}</span>
              <span class="stat-label">景点</span>
            </div>
            <div class="stat">
              <span class="stat-value">{{ totalMeals(v.plan) }}</span>
              <span class="stat-label">美食</span>
            </div>
            <div class="stat" v-if="v.plan.budget">
              <span class="stat-value">¥{{ v.plan.budget.total }}</span>
              <span class="stat-label">预估费用</span>
            </div>
          </div>
          <div v-if="v.plan?.budget && v.plan.days.length" class="per-person-cost">
            约 ¥{{ Math.round(v.plan.budget.total / (v.plan.travelers || 1) / v.plan.days.length) }}/人/天
          </div>

          <!-- Transport Info -->
          <div v-if="v.plan?.transport_info && v.plan.transport_info.estimated_cost > 0" class="transport-info">
            <span class="transport-mode">{{ v.plan.transport_info.recommended_mode }}</span>
            <span class="transport-detail">{{ v.plan.transport_info.departure_city }} → {{ v.plan.transport_info.destination_city }}</span>
            <span class="transport-cost">约¥{{ v.plan.transport_info.estimated_cost }}</span>
            <span class="transport-duration">{{ v.plan.transport_info.estimated_duration }}</span>
          </div>

          <!-- Budget Breakdown -->
          <div v-if="v.plan?.budget" class="budget-breakdown">
            <div class="breakdown-bar">
              <div class="bar-segment bar-hotel" :style="{ width: budgetPercent(v.plan.budget, 'hotel') }"></div>
              <div class="bar-segment bar-food" :style="{ width: budgetPercent(v.plan.budget, 'food') }"></div>
              <div class="bar-segment bar-ticket" :style="{ width: budgetPercent(v.plan.budget, 'ticket') }"></div>
              <div class="bar-segment bar-transport" :style="{ width: budgetPercent(v.plan.budget, 'transport') }"></div>
            </div>
            <div class="breakdown-legend">
              <span class="legend-item"><i class="legend-dot dot-hotel"></i>住宿 ¥{{ v.plan.budget.total_hotels }}</span>
              <span class="legend-item"><i class="legend-dot dot-food"></i>餐饮 ¥{{ v.plan.budget.total_meals }}</span>
              <span class="legend-item"><i class="legend-dot dot-ticket"></i>门票 ¥{{ v.plan.budget.total_attractions }}</span>
              <span class="legend-item"><i class="legend-dot dot-transport"></i>交通 ¥{{ v.plan.budget.total_transportation }}</span>
            </div>
          </div>

          <!-- Daily Preview -->
          <div v-if="v.plan" class="card-days">
            <div v-for="day in v.plan.days" :key="day.day_index" class="day-preview">
              <div class="day-label">Day {{ day.day_index + 1 }}</div>
              <!-- Route visual: attractions connected by lines -->
              <div class="route-visual">
                <template v-for="(attr, j) in day.attractions.slice(0, 4)" :key="j">
                  <span class="route-node" :title="attr.name">{{ j + 1 }}</span>
                  <span v-if="j < Math.min(day.attractions.length, 4) - 1" class="route-line"></span>
                </template>
                <span v-if="day.attractions.length > 4" class="route-more">+{{ day.attractions.length - 4 }}</span>
              </div>
              <div class="day-attractions">
                <span
                  v-for="(attr, j) in day.attractions.slice(0, 3)"
                  :key="j"
                  class="day-attr-tag"
                >{{ attr.name }}</span>
                <span v-if="day.attractions.length > 3" class="day-attr-more">
                  +{{ day.attractions.length - 3 }}
                </span>
              </div>
            </div>
          </div>

          <!-- Failed State -->
          <div v-if="!v.plan" class="card-failed-content">
            <span class="failed-icon">⚠️</span>
            <span>方案生成失败</span>
          </div>

          <!-- CTA -->
          <button
            v-if="v.plan"
            class="card-cta"
            @click="selectVariant(v.plan!)"
          >
            选择此方案 →
          </button>
        </div>
      </div>

      <!-- Mobile Dots -->
      <div class="mobile-dots">
        <span
          v-for="(_, i) in variants"
          :key="i"
          :class="['dot', { active: activeMobileIndex === i }]"
          @click="activeMobileIndex = i"
        ></span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import type { TripPlan } from '@/types'
import EmptyState from '@/components/EmptyState.vue'

const router = useRouter()
const loading = ref(true)
const error = ref(false)
const city = ref('')
const variants = ref<{ variant: string; plan: TripPlan | null; style_name?: string }[]>([])
const activeMobileIndex = ref(0)
const gridRef = ref<HTMLElement | null>(null)
let scrollObserver: IntersectionObserver | null = null
let isScrollSyncing = false

watch(activeMobileIndex, (idx) => {
  if (!gridRef.value || isScrollSyncing) return
  const cards = gridRef.value.querySelectorAll('.comparison-card')
  if (cards[idx]) {
    cards[idx].scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' })
  }
})

const styleConfig: Record<string, { icon: string; label: string }> = {
  classic: { icon: '🏛️', label: '经典高效' },
  relaxed: { icon: '🌿', label: '轻松休闲' },
  deep: { icon: '🎭', label: '深度探索' },
}

const getStyleIcon = (key: string) => styleConfig[key]?.icon || '📋'
const getStyleLabel = (key: string) => styleConfig[key]?.label || key

const getPlanName = (v: { variant: string; plan: TripPlan | null }) => {
  if (!v.plan) return getStyleLabel(v.variant)
  const suggestions = v.plan.overall_suggestions || ''
  const firstLine = suggestions.split('\n')[0]?.replace(/^#+\s*/, '').trim()
  return firstLine && firstLine.length < 20 ? firstLine : getStyleLabel(v.variant)
}

const totalAttractions = (plan: TripPlan) =>
  plan.days.reduce((sum, d) => sum + d.attractions.length, 0)

const totalMeals = (plan: TripPlan) =>
  plan.days.reduce((sum, d) => sum + (d.meals?.length || 0), 0)

const getRecommendTag = (v: { variant: string; plan: TripPlan | null }, idx: number): string => {
  if (!v.plan || variants.value.length < 2) return ''
  const validPlans = variants.value.filter(x => x.plan).map(x => x.plan!)
  if (validPlans.length < 2) return ''

  const myAttractions = totalAttractions(v.plan)
  const myMeals = totalMeals(v.plan)
  const maxAttractions = Math.max(...validPlans.map(p => totalAttractions(p)))
  const maxMeals = Math.max(...validPlans.map(p => totalMeals(p)))
  const minAttractions = Math.min(...validPlans.map(p => totalAttractions(p)))

  if (myAttractions === maxAttractions && myAttractions > minAttractions) return '景点最多'
  if (myMeals === maxMeals && myMeals > 3) return '美食首选'
  if (myAttractions === minAttractions && v.variant === 'relaxed') return '最舒适'
  if (v.variant === 'classic') return '经典之选'
  if (v.variant === 'deep') return '深度推荐'
  return ''
}

const budgetPercent = (budget: { total: number; total_hotels: number; total_meals: number; total_attractions: number; total_transportation: number }, type: string) => {
  if (!budget.total) return '0%'
  const map: Record<string, number> = {
    hotel: budget.total_hotels,
    food: budget.total_meals,
    ticket: budget.total_attractions,
    transport: budget.total_transportation,
  }
  return Math.round(((map[type] || 0) / budget.total) * 100) + '%'
}

const selectVariant = (plan: TripPlan) => {
  sessionStorage.setItem('tripPlan', JSON.stringify(plan))
  sessionStorage.setItem('fromComparison', '1')
  // 保留 tripVariants 以便用户从详情页返回对比页时能重新加载
  router.push({ name: 'result' })
}

onMounted(() => {
  const savedVariants = sessionStorage.getItem('tripVariants')
  if (savedVariants) {
    try {
      const parsed = JSON.parse(savedVariants)
      if (!Array.isArray(parsed) || parsed.length === 0) {
        error.value = true
      } else {
        variants.value = parsed
        if (parsed[0].plan) {
          city.value = parsed[0].plan.city
        }
      }
    } catch (e) {
      error.value = true
    }
  } else {
    error.value = true
  }
  loading.value = false

  // 移动端滑动同步标签栏
  if (gridRef.value) {
    scrollObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && entry.intersectionRatio > 0.5) {
            const card = entry.target as HTMLElement
            const cards = Array.from(gridRef.value?.querySelectorAll('.comparison-card') || [])
            const idx = cards.indexOf(card)
            if (idx !== -1 && idx !== activeMobileIndex.value) {
              isScrollSyncing = true
              activeMobileIndex.value = idx
              setTimeout(() => { isScrollSyncing = false }, 300)
            }
          }
        })
      },
      { root: gridRef.value, threshold: 0.5 }
    )
    gridRef.value.querySelectorAll('.comparison-card').forEach((card) => {
      scrollObserver!.observe(card)
    })
  }
})

onBeforeUnmount(() => {
  if (scrollObserver) {
    scrollObserver.disconnect()
    scrollObserver = null
  }
})
</script>

<style scoped>
.comparison {
  min-height: 100vh;
  background: var(--color-cream);
}

.comparison-loading,
.comparison-error {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-terracotta);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Topbar */
.topbar {
  display: flex;
  align-items: center;
  padding: 16px 24px;
  background: rgba(255, 252, 247, 0.9);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 10;
}

.topbar-back {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  font-size: 0.9rem;
  padding: 8px 12px;
  border-radius: var(--radius-md);
  transition: all 0.2s;
}

.topbar-back:hover {
  background: var(--color-border);
  color: var(--color-charcoal);
}

.back-arrow { font-size: 1.1rem; }

.topbar-title {
  flex: 1;
  text-align: center;
  font-family: var(--font-display);
  font-weight: 600;
  color: var(--color-charcoal);
}

.topbar-spacer { width: 80px; }

/* Header */
.comparison-header {
  text-align: center;
  padding: 48px 24px 32px;
  animation: fadeUp 0.6s ease both;
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(16px); }
}

.header-title {
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-charcoal);
  margin: 0 0 8px;
}

.header-subtitle {
  color: var(--color-text-secondary);
  font-size: 1rem;
  margin: 0;
}

/* Grid */
.comparison-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px 48px;
}

/* Card */
.comparison-card {
  background: white;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.22, 1, 0.36, 1);
  animation: cardIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
  display: flex;
  flex-direction: column;
}

@keyframes cardIn {
  from {
    opacity: 0;
    transform: translateY(24px);
  }
}

.comparison-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.08);
  border-color: var(--color-terracotta);
}

.card-failed {
  opacity: 0.6;
  border-color: #e74c3c;
}

/* Card Header */
.card-header {
  padding: 28px 24px 20px;
  text-align: center;
  border-bottom: 1px solid var(--color-border);
}

.card-icon {
  font-size: 2.5rem;
  margin-bottom: 12px;
}

.card-name {
  font-family: var(--font-display);
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--color-charcoal);
  margin: 0 0 8px;
}

.card-style {
  display: inline-block;
  padding: 4px 12px;
  background: var(--color-cream);
  border-radius: 20px;
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.card-recommend {
  display: inline-block;
  padding: 3px 10px;
  background: linear-gradient(135deg, #c67b5c, #e6a23c);
  border-radius: 20px;
  font-size: 0.7rem;
  color: white;
  font-weight: 600;
  margin-left: 6px;
}

/* Stats */
.card-stats {
  display: flex;
  justify-content: center;
  gap: 20px;
  padding: 20px 16px;
  border-bottom: 1px solid var(--color-border);
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-family: var(--font-display);
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--color-terracotta);
}

.stat-label {
  font-size: 0.7rem;
  color: var(--color-text-secondary);
  margin-top: 2px;
}

/* Transport Info */
.per-person-cost {
  text-align: center;
  padding: 6px 20px;
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  background: rgba(0, 0, 0, 0.02);
}

.transport-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.06), rgba(16, 185, 129, 0.06));
  border-top: 1px solid rgba(59, 130, 246, 0.1);
  font-size: 0.75rem;
  flex-wrap: wrap;
}

.transport-mode {
  background: #3b82f6;
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.7rem;
}

.transport-detail {
  color: var(--color-text);
  font-weight: 500;
}

.transport-cost {
  color: #3b82f6;
  font-weight: 600;
}

.transport-duration {
  color: var(--color-text-secondary);
  margin-left: auto;
}

/* Days Preview */
.card-days {
  padding: 16px 20px;
  flex: 1;
}

.day-preview {
  padding: 10px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}

.day-preview:last-child { border-bottom: none; }

.day-label {
  font-family: var(--font-display);
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-terracotta);
  margin-bottom: 6px;
}

.route-visual {
  display: flex;
  align-items: center;
  gap: 0;
  margin-bottom: 6px;
}

.route-node {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--color-terracotta);
  color: white;
  font-size: 0.55rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.route-line {
  width: 16px;
  height: 2px;
  background: var(--color-terracotta);
  opacity: 0.4;
  flex-shrink: 0;
}

.route-more {
  font-size: 0.6rem;
  color: var(--color-text-secondary);
  margin-left: 4px;
}

.day-attractions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.day-attr-tag {
  display: inline-block;
  padding: 2px 8px;
  background: var(--color-cream);
  border-radius: 4px;
  font-size: 0.7rem;
  color: var(--color-charcoal);
}

.day-attr-more {
  font-size: 0.7rem;
  color: var(--color-text-secondary);
  padding: 2px 4px;
}

.day-meals {
  display: flex;
  gap: 4px;
  margin-top: 6px;
}

.meal-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-terracotta);
  opacity: 0.5;
}

/* Failed */
.card-failed-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #e74c3c;
  font-size: 0.9rem;
  padding: 40px 0;
}

.failed-icon { font-size: 2rem; }

/* Budget Breakdown */
.budget-breakdown {
  padding: 0 20px 16px;
}

.breakdown-bar {
  display: flex;
  height: 6px;
  border-radius: 3px;
  overflow: hidden;
  background: #f0ebe6;
  margin-bottom: 8px;
}

.bar-segment {
  height: 100%;
  transition: width 0.5s ease;
}

.bar-hotel { background: #c67b5c; }
.bar-food { background: #e6a23c; }
.bar-ticket { background: #2d4a3e; }
.bar-transport { background: #7c9eb2; }

.breakdown-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.65rem;
  color: var(--color-text-secondary);
}

.legend-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
}

.dot-hotel { background: #c67b5c; }
.dot-food { background: #e6a23c; }
.dot-ticket { background: #2d4a3e; }
.dot-transport { background: #7c9eb2; }

/* CTA */
.card-cta {
  display: block;
  margin: 16px 20px 20px;
  padding: 14px;
  background: var(--color-charcoal);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-family: var(--font-display);
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.card-cta:hover {
  background: var(--color-terracotta);
  transform: translateY(-1px);
}

/* Mobile Tabs */
.mobile-tabs {
  display: none;
  gap: 8px;
  padding: 0 24px 16px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.mobile-tab {
  flex-shrink: 0;
  padding: 8px 16px;
  border: 1px solid var(--color-border);
  border-radius: 20px;
  background: white;
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.mobile-tab.active {
  background: var(--color-charcoal);
  color: white;
  border-color: var(--color-charcoal);
}

/* Mobile Dots */
.mobile-dots {
  display: none;
  justify-content: center;
  gap: 8px;
  padding: 16px 0 32px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-border);
  cursor: pointer;
  transition: all 0.2s;
}

.dot.active {
  background: var(--color-terracotta);
  transform: scale(1.3);
}

/* Mobile */
@media (max-width: 900px) {
  .comparison-grid {
    display: flex;
    overflow-x: auto;
    scroll-snap-type: x mandatory;
    -webkit-overflow-scrolling: touch;
    padding: 0 16px 16px;
    gap: 16px;
    scrollbar-width: none;
  }

  .comparison-grid::-webkit-scrollbar { display: none; }

  .comparison-card {
    min-width: calc(100vw - 48px);
    scroll-snap-align: center;
    flex-shrink: 0;
  }

  .mobile-tabs { display: flex; }
  .mobile-dots { display: flex; }

  .header-title { font-size: 1.5rem; }
  .comparison-header { padding: 32px 24px 16px; }
}
</style>
