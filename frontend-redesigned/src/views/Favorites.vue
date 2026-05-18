<template>
  <div class="favorites-page">
    <div class="favorites-header">
      <h1 class="favorites-title">我的收藏</h1>
      <p class="favorites-subtitle">收藏的旅行计划</p>
    </div>

    <div v-if="loading" class="favorites-loading">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="favorites.length === 0" class="favorites-empty">
      <EmptyState
        icon="♡"
        title="暂无收藏"
        description="收藏的旅行计划会显示在这里"
        actionText="去规划行程"
        @action="$router.push('/')"
      />
    </div>

    <div v-else class="favorites-grid">
      <div
        v-for="plan in favorites"
        :key="plan.id"
        class="favorite-card"
        @click="viewTrip(plan)"
      >
        <div class="card-image">
          <img
            v-if="plan.days?.[0]?.attractions?.[0]?.image_url"
            :src="plan.days[0].attractions[0].image_url"
            :alt="plan.city"
          />
          <div v-else class="card-image-placeholder">{{ plan.city?.[0] }}</div>
        </div>
        <div class="card-body">
          <h3 class="card-city">{{ plan.city }}</h3>
          <p class="card-dates">{{ plan.start_date }} — {{ plan.end_date }}</p>
          <p class="card-meta">{{ plan.days?.length || 0 }}天行程</p>
        </div>
        <button class="card-remove" @click.stop="removeFav(plan.id!)">✕</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { TripPlan } from '@/types'
import { listFavorites, removeFavorite } from '@/services/api'
import EmptyState from '@/components/EmptyState.vue'

const router = useRouter()
const favorites = ref<TripPlan[]>([])
const loading = ref(true)

const loadFavorites = async () => {
  loading.value = true
  try {
    favorites.value = await listFavorites()
  } catch {
    message.error('加载收藏失败')
  } finally {
    loading.value = false
  }
}

const viewTrip = (plan: TripPlan) => {
  sessionStorage.setItem('tripPlan', JSON.stringify(plan))
  router.push('/result')
}

const removeFav = async (tripId: string) => {
  try {
    await removeFavorite(tripId)
    favorites.value = favorites.value.filter(f => f.id !== tripId)
    message.success('已取消收藏')
  } catch {
    message.error('操作失败')
  }
}

onMounted(loadFavorites)
</script>

<style scoped>
.favorites-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 40px 24px 80px;
}

.favorites-header {
  margin-bottom: 32px;
}

.favorites-title {
  font-family: var(--font-display);
  font-size: 1.8rem;
  font-weight: 600;
  color: var(--color-charcoal);
  margin: 0 0 4px;
}

.favorites-subtitle {
  color: var(--color-warm-gray);
  font-size: 0.9rem;
  margin: 0;
}

.favorites-loading {
  text-align: center;
  padding: 60px 0;
  color: var(--color-warm-gray);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-sand);
  border-top-color: var(--color-terracotta);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.favorites-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 20px;
}

.favorite-card {
  position: relative;
  background: white;
  border-radius: var(--radius-lg);
  overflow: hidden;
  cursor: pointer;
  transition: all var(--transition-normal);
  border: 1px solid rgba(232, 226, 218, 0.5);
}

.favorite-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-hover);
}

.card-image {
  height: 160px;
  overflow: hidden;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s ease;
}

.favorite-card:hover .card-image img {
  transform: scale(1.05);
}

.card-image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-sand), var(--color-paper));
  font-family: var(--font-display);
  font-size: 2rem;
  color: var(--color-terracotta);
}

.card-body {
  padding: 16px;
}

.card-city {
  font-family: var(--font-display);
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-charcoal);
  margin: 0 0 4px;
}

.card-dates {
  font-size: 0.8rem;
  color: var(--color-warm-gray);
  margin: 0 0 2px;
}

.card-meta {
  font-size: 0.75rem;
  color: var(--color-light-gray);
  margin: 0;
}

.card-remove {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: rgba(0,0,0,0.4);
  color: white;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.favorite-card:hover .card-remove {
  opacity: 1;
}
</style>
