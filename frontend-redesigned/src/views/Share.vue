<template>
  <div class="share-page">
    <div v-if="loading" class="share-loading">
      <div class="loading-spinner"></div>
      <p>加载行程中...</p>
    </div>

    <div v-else-if="error" class="share-error">
      <EmptyState
        icon="🔗"
        title="链接无效"
        description="该分享链接已过期或不存在"
        actionText="返回首页"
        @action="$router.push('/')"
      />
    </div>

    <template v-else>
      <!-- Header -->
      <header class="share-header">
        <div class="header-brand">
          <span class="brand-icon">✦</span>
          <span class="brand-text">Voyager</span>
        </div>
        <div class="header-info">
          <h1 class="share-title">{{ plan.city }}之旅</h1>
          <p class="share-meta">{{ plan.start_date }} — {{ plan.end_date }} · {{ plan.days?.length || 0 }}天</p>
        </div>
      </header>

      <!-- Content -->
      <main class="share-content">
        <!-- Days -->
        <section v-for="day in plan.days" :key="day.day_index" class="share-day">
          <h2 class="day-title">Day {{ (day.day_index || 0) + 1 }} · {{ day.date }}</h2>
          <p class="day-desc">{{ day.description }}</p>

          <div class="day-attractions">
            <div v-for="attr in day.attractions" :key="attr.name" class="attraction-card">
              <img v-if="attr.image_url" :src="attr.image_url" :alt="attr.name" class="attraction-img" />
              <div class="attraction-info">
                <h3 class="attraction-name">{{ attr.name }}</h3>
                <p class="attraction-desc">{{ attr.description }}</p>
                <div class="attraction-meta">
                  <span v-if="attr.ticket_price">¥{{ attr.ticket_price }}</span>
                  <span v-if="attr.visit_duration">{{ attr.visit_duration }}分钟</span>
                </div>
              </div>
            </div>
          </div>

          <div v-if="day.meals?.length" class="day-meals">
            <span v-for="meal in day.meals" :key="meal.name" class="meal-tag">
              {{ meal.name }}
            </span>
          </div>
        </section>

        <!-- CPS Links -->
        <section v-if="plan.cps_links" class="share-cps">
          <h2 class="section-title">预订链接</h2>
          <div class="cps-links">
            <a v-for="(link, key) in plan.cps_links" :key="key"
               :href="link.url" target="_blank" class="cps-link">
              {{ link.name }} →
            </a>
          </div>
        </section>
      </main>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import type { TripPlan } from '@/types'
import { getSharedTrip } from '@/services/api'
import EmptyState from '@/components/EmptyState.vue'

const route = useRoute()
const plan = ref<TripPlan>({ city: '', start_date: '', end_date: '', days: [], weather_info: [], overall_suggestions: '' })
const loading = ref(true)
const error = ref(false)

onMounted(async () => {
  const token = route.params.token as string
  try {
    plan.value = await getSharedTrip(token)
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.share-page {
  max-width: 700px;
  margin: 0 auto;
  padding: 0 20px 60px;
  min-height: 100vh;
  background: var(--color-cream, #fffcf7);
}

.share-loading, .share-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  color: var(--color-warm-gray, #8a7e75);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e8e4df;
  border-top-color: #c67b5c;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin { to { transform: rotate(360deg); } }

.share-header {
  padding: 32px 0 24px;
  border-bottom: 1px solid rgba(232,226,218,0.5);
  margin-bottom: 32px;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 16px;
  font-size: 0.85rem;
  color: #8a7e75;
}

.brand-icon { color: #c67b5c; }

.brand-text {
  font-family: var(--font-display, 'Cormorant Garamond', serif);
  font-weight: 600;
}

.share-title {
  font-family: var(--font-display, 'Cormorant Garamond', serif);
  font-size: 1.8rem;
  font-weight: 600;
  color: #2c2520;
  margin: 0 0 4px;
}

.share-meta {
  color: #8a7e75;
  font-size: 0.85rem;
  margin: 0;
}

.share-day {
  margin-bottom: 32px;
}

.day-title {
  font-family: var(--font-display, 'Cormorant Garamond', serif);
  font-size: 1.2rem;
  font-weight: 600;
  color: #2c2520;
  margin: 0 0 8px;
}

.day-desc {
  color: #5a524a;
  font-size: 0.9rem;
  line-height: 1.6;
  margin: 0 0 16px;
}

.day-attractions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.attraction-card {
  display: flex;
  gap: 12px;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(232,226,218,0.5);
}

.attraction-img {
  width: 100px;
  height: 80px;
  object-fit: cover;
  flex-shrink: 0;
}

.attraction-info {
  padding: 8px 12px 8px 0;
  min-width: 0;
}

.attraction-name {
  font-weight: 600;
  font-size: 0.9rem;
  color: #2c2520;
  margin: 0 0 4px;
}

.attraction-desc {
  font-size: 0.78rem;
  color: #8a7e75;
  margin: 0 0 4px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.attraction-meta {
  display: flex;
  gap: 12px;
  font-size: 0.75rem;
  color: #c67b5c;
  font-weight: 500;
}

.day-meals {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
}

.meal-tag {
  padding: 4px 10px;
  background: #f5f0eb;
  border-radius: 20px;
  font-size: 0.75rem;
  color: #5a524a;
}

.share-cps {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid rgba(232,226,218,0.5);
}

.section-title {
  font-family: var(--font-display, 'Cormorant Garamond', serif);
  font-size: 1.1rem;
  font-weight: 600;
  color: #2c2520;
  margin: 0 0 12px;
}

.cps-links {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.cps-link {
  padding: 8px 16px;
  background: white;
  border: 1px solid rgba(232,226,218,0.5);
  border-radius: 8px;
  text-decoration: none;
  color: #2c2520;
  font-size: 0.85rem;
  transition: border-color 0.2s;
}

.cps-link:hover {
  border-color: #c67b5c;
}
</style>
