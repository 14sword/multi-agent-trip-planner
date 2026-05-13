<template>
  <div class="result">
    <!-- Loading -->
    <div v-if="loading" class="result-loading">
      <div class="loading-content">
        <div class="loading-spinner"></div>
        <p>加载行程数据...</p>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="result-error">
      <EmptyState
        icon="📋"
        title="无法加载行程"
        description="行程数据为空或已过期，请返回首页重新规划"
        actionText="返回首页"
        :tips="['确保从首页提交规划请求', '刷新页面后重试']"
        @action="$router.push('/')"
      />
    </div>

    <!-- Content -->
    <div v-else class="result-content">
      <!-- Top Bar -->
      <nav class="topbar no-print">
        <button class="topbar-back" @click="$router.push('/')">
          <span class="back-arrow">←</span>
          <span>返回</span>
        </button>
        <div class="topbar-actions">
          <button v-if="editMode" class="topbar-btn topbar-btn--primary" @click="saveChanges" :disabled="saving">
            {{ saving ? '保存中...' : '保存修改' }}
          </button>
          <button v-if="editMode" class="topbar-btn" @click="cancelEdit">取消</button>
          <button v-if="!editMode" class="topbar-btn" @click="toggleEditMode">编辑</button>
          <button class="topbar-btn" @click="exportPDF">导出 PDF</button>
          <button :class="['topbar-btn', { 'topbar-btn--active': isFavorite }]" @click="toggleFavorite">
            {{ isFavorite ? '已收藏' : '收藏' }}
          </button>
        </div>
      </nav>

      <!-- Page Header -->
      <header class="result-header">
        <div class="header-content">
          <span class="header-label">{{ tripPlan.city }}</span>
          <h1 class="header-title">{{ tripPlan.city }}之旅</h1>
          <p class="header-meta">
            {{ tripPlan.start_date }} — {{ tripPlan.end_date }} · {{ tripPlan.days.length }}天
          </p>
        </div>
      </header>

      <!-- Main Layout -->
      <div class="result-layout">
        <!-- Sidebar -->
        <aside class="sidebar no-print">
          <a-affix :offset-top="24">
            <nav class="sidebar-nav">
              <a-menu
                v-model:selectedKeys="selectedKeys"
                mode="inline"
                @click="scrollToSection"
              >
                <a-menu-item key="overview">行程概览</a-menu-item>
                <a-menu-item key="budget" v-if="tripPlan.budget">预算明细</a-menu-item>
                <a-menu-item key="map">景点地图</a-menu-item>
                <a-menu-item key="days">每日行程</a-menu-item>
                <a-menu-item key="weather">天气预报</a-menu-item>
              </a-menu>
            </nav>
          </a-affix>
        </aside>

        <!-- Main Content -->
        <main id="trip-plan-content" class="main-content">
          <!-- Overview -->
          <section id="overview" class="content-section">
            <h2 class="section-heading">
              <span class="heading-accent">01</span>
              行程概览
            </h2>
            <div class="overview-card">
              <div class="overview-grid">
                <div class="overview-item">
                  <span class="overview-label">目的地</span>
                  <span class="overview-value">{{ tripPlan.city }}</span>
                </div>
                <div class="overview-item">
                  <span class="overview-label">行程天数</span>
                  <span class="overview-value">{{ tripPlan.days.length }}天</span>
                </div>
                <div class="overview-item">
                  <span class="overview-label">日期范围</span>
                  <span class="overview-value">{{ tripPlan.start_date }} ~ {{ tripPlan.end_date }}</span>
                </div>
              </div>
              <div class="overview-suggestion">
                <p>{{ tripPlan.overall_suggestions }}</p>
              </div>
            </div>
          </section>

          <!-- Budget -->
          <section id="budget" v-if="tripPlan.budget" class="content-section">
            <h2 class="section-heading">
              <span class="heading-accent">02</span>
              预算明细
            </h2>
            <BudgetPanel :budget="tripPlan.budget" />
          </section>

          <!-- Map -->
          <section id="map" class="content-section">
            <h2 class="section-heading">
              <span class="heading-accent">{{ tripPlan.budget ? '03' : '02' }}</span>
              景点地图
            </h2>
            <div class="map-wrapper">
              <div id="amap-container" class="map-container">
                <div v-if="mapLoading" class="map-loading">
                  <div class="loading-spinner loading-spinner--small"></div>
                  <span>加载地图中...</span>
                </div>
              </div>
            </div>
          </section>

          <!-- Days -->
          <section id="days" class="content-section">
            <h2 class="section-heading">
              <span class="heading-accent">{{ getSectionNumber('days') }}</span>
              每日行程
            </h2>
            <div class="days-list">
              <DayCard
                v-for="(day, dayIndex) in tripPlan.days"
                :key="day.day_index"
                :day="day"
                :day-number="dayIndex + 1"
                :expanded="activeDays.includes(day.day_index)"
                :edit-mode="editMode"
                :expanded-details="expandedAttractions"
                @toggle="toggleDay(day.day_index)"
                @toggle-detail="(i) => toggleAttractionDetail(day.day_index, i)"
                @move="(i, dir) => moveAttraction(day.day_index, i, dir)"
                @delete="(i) => deleteAttraction(day.day_index, i)"
                @add="addAttraction(day.day_index)"
              />
            </div>
          </section>

          <!-- Weather -->
          <section id="weather" class="content-section">
            <h2 class="section-heading">
              <span class="heading-accent">{{ getSectionNumber('weather') }}</span>
              天气预报
            </h2>
            <WeatherGrid :weather="tripPlan.weather_info" />
          </section>
        </main>
      </div>

      <!-- Share Modal -->
      <a-modal
        v-model:visible="shareVisible"
        title="分享行程"
        width="440px"
        :footer="null"
      >
        <div style="text-align: center; padding: 24px 0;">
          <p style="margin-bottom: 16px; color: var(--color-warm-gray);">当前版本暂不支持在线分享。</p>
          <p style="color: var(--color-warm-gray);">您可以使用收藏功能保存行程，或导出为 PDF。</p>
        </div>
      </a-modal>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import type { TripPlan } from '@/types'
import { editTripPlan } from '@/services/api'
import AMapLoader from '@amap/amap-jsapi-loader'
import DayCard from '@/components/DayCard.vue'
import BudgetPanel from '@/components/BudgetPanel.vue'
import WeatherGrid from '@/components/WeatherGrid.vue'
import EmptyState from '@/components/EmptyState.vue'

const tripPlan = ref<TripPlan>({
  city: '',
  start_date: '',
  end_date: '',
  days: [],
  weather_info: [],
  overall_suggestions: '',
})

const loading = ref(true)
const error = ref(false)
const saving = ref(false)
const mapLoading = ref(false)
const editMode = ref(false)
const originalPlan = ref<TripPlan | null>(null)
const selectedKeys = ref<string[]>(['overview'])
const activeDays = ref<number[]>([])
const expandedAttractions = ref<Record<string, boolean>>({})
const shareVisible = ref(false)
const isFavorite = ref(false)
let map: any = null

onMounted(() => {
  const savedPlan = sessionStorage.getItem('tripPlan')
  if (savedPlan) {
    try {
      tripPlan.value = JSON.parse(savedPlan)
      // Expand first day by default
      if (tripPlan.value.days.length > 0) {
        activeDays.value = [tripPlan.value.days[0].day_index]
      }
      checkFavorite()
      nextTick(() => initMap())
    } catch (e) {
      error.value = true
    } finally {
      loading.value = false
    }
  } else {
    error.value = true
    loading.value = false
  }
})

const initMap = async () => {
  mapLoading.value = true
  try {
    const mapContainer = document.getElementById('amap-container')
    if (!mapContainer) return

    try {
      const AMap = await AMapLoader.load({
        key: import.meta.env.VITE_AMAP_KEY || '',
        version: '2.0',
        plugins: ['AMap.Scale', 'AMap.ToolBar', 'AMap.InfoWindow'],
      })

      if (map) {
        map.destroy()
        map = null
      }

      const allPositions: any[] = []

      if (tripPlan.value.days.length > 0 && tripPlan.value.days[0].attractions.length > 0) {
        const first = tripPlan.value.days[0].attractions[0]
        if (first.location?.longitude && first.location?.latitude) {
          map = new AMap.Map(mapContainer, {
            zoom: 12,
            center: [first.location.longitude, first.location.latitude],
            resizeEnable: true,
          })

          map.addControl(new AMap.Scale())
          map.addControl(new AMap.ToolBar())

          tripPlan.value.days.forEach((day) => {
            day.attractions.forEach((attraction, index) => {
              if (attraction.location?.longitude && attraction.location?.latitude) {
                const position = [attraction.location.longitude, attraction.location.latitude]
                allPositions.push(position)

                const marker = new AMap.Marker({
                  position,
                  title: attraction.name,
                  label: {
                    content: `${day.day_index + 1}-${index + 1}`,
                    direction: 'top',
                    offset: new AMap.Pixel(0, -30),
                  },
                })

                const infoWindow = new AMap.InfoWindow({
                  content: `
                    <div style="padding: 12px; min-width: 200px; font-family: 'DM Sans', sans-serif;">
                      <h3 style="margin: 0 0 8px 0; font-size: 14px; font-weight: 600;">${attraction.name}</h3>
                      <p style="margin: 3px 0; font-size: 12px; color: #666;">📍 ${attraction.address}</p>
                      <p style="margin: 3px 0; font-size: 12px; color: #666;">⏱ ${attraction.visit_duration}分钟</p>
                      ${attraction.ticket_price ? `<p style="margin: 3px 0; font-size: 12px; color: #666;">🎫 ¥${attraction.ticket_price}</p>` : ''}
                    </div>
                  `,
                  offset: new AMap.Pixel(0, -40),
                })

                marker.on('click', () => infoWindow.open(map, marker.getPosition()))
                map.add(marker)
              }
            })
          })

          if (allPositions.length > 1) {
            // Build bezier curves between consecutive points for natural arcs
            for (let i = 0; i < allPositions.length - 1; i++) {
              const [lng1, lat1] = allPositions[i]
              const [lng2, lat2] = allPositions[i + 1]
              const midLng = (lng1 + lng2) / 2
              const midLat = (lat1 + lat2) / 2
              const dist = Math.sqrt((lng2 - lng1) ** 2 + (lat2 - lat1) ** 2)
              // Perpendicular offset scaled by distance — creates natural arc
              const offset = dist * 0.15
              const dx = lng2 - lng1
              const dy = lat2 - lat1
              const ctrlLng = midLng - (dy / dist) * offset
              const ctrlLat = midLat + (dx / dist) * offset

              const curve = new AMap.BezierCurve({
                path: [
                  [lng1, lat1],
                  [ctrlLng, ctrlLat],
                  [lng2, lat2],
                ],
                strokeColor: '#C4654A',
                strokeWeight: 3,
                strokeOpacity: 0.7,
                lineJoin: 'round',
                lineCap: 'round',
                showDir: true,
              })
              map.add(curve)
            }
          }
        } else {
          map = new AMap.Map(mapContainer, { zoom: 12, center: [116.397428, 39.90923], resizeEnable: true })
        }
      } else {
        map = new AMap.Map(mapContainer, { zoom: 12, center: [116.397428, 39.90923], resizeEnable: true })
      }
    } catch (apiError) {
      message.error('地图加载失败，请检查网络连接')
    }
  } catch (e) {
    message.error('地图初始化失败')
  } finally {
    mapLoading.value = false
  }
}

const scrollToSection = ({ key }: { key: string }) => {
  selectedKeys.value = [key]
  document.getElementById(key)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const toggleDay = (dayIndex: number) => {
  const i = activeDays.value.indexOf(dayIndex)
  if (i > -1) activeDays.value.splice(i, 1)
  else activeDays.value.push(dayIndex)
}

const toggleAttractionDetail = (dayIndex: number, attractionIndex: number) => {
  const key = `${dayIndex}-${attractionIndex}`
  expandedAttractions.value[key] = !expandedAttractions.value[key]
}

const toggleEditMode = () => {
  if (!editMode.value) {
    originalPlan.value = JSON.parse(JSON.stringify(tripPlan.value))
  }
  editMode.value = !editMode.value
}

const saveChanges = async () => {
  saving.value = true
  try {
    const updated = await editTripPlan(tripPlan.value)
    tripPlan.value = updated
    editMode.value = false
    message.success('修改已保存')
    nextTick(() => initMap())
  } catch {
    message.error('保存失败，请稍后重试')
  } finally {
    saving.value = false
  }
}

const cancelEdit = () => {
  if (originalPlan.value) tripPlan.value = originalPlan.value
  editMode.value = false
}

const moveAttraction = (dayIndex: number, attractionIndex: number, direction: string) => {
  const attractions = tripPlan.value.days[dayIndex].attractions
  const newIndex = direction === 'up' ? attractionIndex - 1 : attractionIndex + 1
  if (newIndex >= 0 && newIndex < attractions.length) {
    [attractions[attractionIndex], attractions[newIndex]] = [attractions[newIndex], attractions[attractionIndex]]
    nextTick(() => initMap())
  }
}

const deleteAttraction = (dayIndex: number, attractionIndex: number) => {
  if (!confirm('确定要删除这个景点吗？')) return
  tripPlan.value.days[dayIndex].attractions.splice(attractionIndex, 1)
  nextTick(() => initMap())
}

const addAttraction = (dayIndex: number) => {
  tripPlan.value.days[dayIndex].attractions.push({
    name: '新景点',
    address: '请输入地址',
    location: {
      longitude: tripPlan.value.days[dayIndex].attractions[0]?.location.longitude || 104.0668,
      latitude: tripPlan.value.days[dayIndex].attractions[0]?.location.latitude || 30.5728,
    },
    visit_duration: 60,
    description: '请输入景点描述',
    ticket_price: 0,
  })
  nextTick(() => initMap())
}

const exportPDF = () => window.print()

const getFavoriteKey = () => `favorite_${tripPlan.value.city}_${tripPlan.value.start_date}`

const checkFavorite = () => {
  isFavorite.value = localStorage.getItem(getFavoriteKey()) !== null
}

const toggleFavorite = () => {
  const key = getFavoriteKey()
  if (isFavorite.value) {
    localStorage.removeItem(key)
    message.success('已取消收藏')
  } else {
    localStorage.setItem(key, JSON.stringify({
      city: tripPlan.value.city,
      start_date: tripPlan.value.start_date,
      end_date: tripPlan.value.end_date,
      total_days: tripPlan.value.days.length,
      total_budget: tripPlan.value.budget?.total || 0,
      saved_at: new Date().toISOString(),
      plan_data: JSON.stringify(tripPlan.value),
    }))
    message.success('已收藏')
  }
  checkFavorite()
}

const getSectionNumber = (section: string) => {
  const base = tripPlan.budget ? 3 : 2
  const sectionMap = { days: base + 1, weather: base + 2 }
  return String(sectionMap[section as keyof typeof sectionMap] || base).padStart(2, '0')
}

onBeforeUnmount(() => {
  if (map) {
    map.destroy()
    map = null
  }
})
</script>

<style scoped>
/* ============================================
   Layout
   ============================================ */
.result {
  min-height: 100vh;
  background: var(--color-cream);
}

.result-loading,
.result-error {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-content {
  text-align: center;
}

.loading-content p {
  margin-top: var(--space-md);
  color: var(--color-warm-gray);
  font-size: 0.9rem;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-light-gray);
  border-top-color: var(--color-terracotta);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto;
}

.loading-spinner--small {
  width: 20px;
  height: 20px;
  border-width: 2px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-card {
  text-align: center;
  padding: var(--space-2xl);
}

.error-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(196, 101, 74, 0.08);
  color: var(--color-terracotta);
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: var(--space-md);
}

.error-card h2 {
  margin-bottom: var(--space-sm);
}

.error-card p {
  margin-bottom: var(--space-lg);
}

.back-btn {
  padding: 10px 24px;
  background: var(--color-terracotta);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-family: var(--font-body);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.back-btn:hover {
  background: var(--color-terracotta-dark);
}

/* ============================================
   Top Bar
   ============================================ */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) var(--space-xl);
  background: rgba(253, 248, 240, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(232, 226, 218, 0.4);
  position: sticky;
  top: 0;
  z-index: 100;
}

.topbar-back {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  font-family: var(--font-body);
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--color-charcoal);
  cursor: pointer;
  padding: 6px 12px;
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.topbar-back:hover {
  background: var(--color-sand);
}

.back-arrow {
  font-size: 1.1rem;
  transition: transform var(--transition-fast);
}

.topbar-back:hover .back-arrow {
  transform: translateX(-3px);
}

.topbar-actions {
  display: flex;
  gap: 6px;
}

.topbar-btn {
  padding: 6px 16px;
  border: 1px solid var(--color-light-gray);
  border-radius: var(--radius-md);
  background: var(--color-paper);
  font-family: var(--font-body);
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-charcoal);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.topbar-btn:hover {
  border-color: var(--color-terracotta);
  color: var(--color-terracotta);
}

.topbar-btn--primary {
  background: var(--color-terracotta);
  border-color: var(--color-terracotta);
  color: white;
}

.topbar-btn--primary:hover {
  background: var(--color-terracotta-dark);
  color: white;
}

.topbar-btn--active {
  background: var(--color-terracotta);
  border-color: var(--color-terracotta);
  color: white;
}

/* ============================================
   Header
   ============================================ */
.result-header {
  padding: var(--space-3xl) var(--space-xl) var(--space-2xl);
  text-align: center;
  background:
    radial-gradient(ellipse 60% 40% at 50% 100%, rgba(196, 101, 74, 0.06) 0%, transparent 60%),
    var(--color-cream);
}

.header-label {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--color-terracotta);
  margin-bottom: var(--space-md);
}

.header-title {
  font-family: var(--font-display);
  font-size: clamp(2rem, 5vw, 3.2rem);
  font-weight: 600;
  color: var(--color-charcoal);
  margin-bottom: var(--space-sm);
}

.header-meta {
  font-size: 1rem;
  color: var(--color-warm-gray);
}

/* ============================================
   Layout Grid
   ============================================ */
.result-layout {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: var(--space-xl);
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--space-xl) var(--space-3xl);
}

.sidebar {
  position: relative;
}

.sidebar-nav {
  background: var(--color-paper);
  border-radius: var(--radius-lg);
  border: 1px solid rgba(232, 226, 218, 0.6);
  padding: var(--space-sm);
  box-shadow: var(--shadow-subtle);
}

.main-content {
  min-width: 0;
}

/* ============================================
   Content Sections
   ============================================ */
.content-section {
  margin-bottom: var(--space-2xl);
  animation: fadeInUp 600ms var(--ease-out-expo) forwards;
  opacity: 0;
}

.content-section:nth-child(1) { animation-delay: 100ms; }
.content-section:nth-child(2) { animation-delay: 200ms; }
.content-section:nth-child(3) { animation-delay: 300ms; }
.content-section:nth-child(4) { animation-delay: 400ms; }
.content-section:nth-child(5) { animation-delay: 500ms; }

.section-heading {
  font-family: var(--font-display);
  font-size: 1.6rem;
  font-weight: 600;
  color: var(--color-charcoal);
  margin-bottom: var(--space-lg);
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding-bottom: var(--space-md);
  border-bottom: 1px solid var(--color-light-gray);
  position: relative;
}

.section-heading::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 60px;
  height: 2px;
  background: var(--color-terracotta);
}

.heading-accent {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--color-sand);
  color: var(--color-terracotta);
  font-size: 0.75rem;
  font-weight: 700;
  font-family: var(--font-body);
  border-radius: var(--radius-sm);
}

/* Overview */
.overview-card {
  background: var(--color-paper);
  border-radius: var(--radius-lg);
  border: 1px solid rgba(232, 226, 218, 0.6);
  padding: var(--space-xl);
  box-shadow: var(--shadow-card);
  position: relative;
  overflow: hidden;
}

.overview-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--color-terracotta), var(--color-sunset), var(--color-forest));
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-lg);
  margin-bottom: var(--space-lg);
  padding-bottom: var(--space-lg);
  border-bottom: 1px solid var(--color-light-gray);
}

.overview-item {
  text-align: center;
  padding: var(--space-md);
  background: var(--color-sand-light);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.overview-item:hover {
  background: var(--color-sand);
  transform: translateY(-2px);
}

.overview-label {
  display: block;
  font-size: 0.7rem;
  color: var(--color-warm-gray);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 6px;
}

.overview-value {
  font-family: var(--font-display);
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--color-charcoal);
}

.overview-suggestion {
  padding: var(--space-md);
  background: var(--color-sand-light);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--color-terracotta);
}

.overview-suggestion p {
  font-size: 0.95rem;
  line-height: 1.7;
  color: var(--color-warm-gray);
  font-style: italic;
  margin: 0;
}

/* Map */
.map-wrapper {
  background: var(--color-paper);
  border-radius: var(--radius-lg);
  border: 1px solid rgba(232, 226, 218, 0.6);
  overflow: hidden;
  box-shadow: var(--shadow-card);
}

.map-container {
  height: 420px;
  position: relative;
  background: linear-gradient(135deg, var(--color-sand-light) 0%, var(--color-cream) 100%);
}

.map-loading {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  background: rgba(253, 248, 240, 0.95);
  backdrop-filter: blur(4px);
  z-index: 10;
}

.map-loading span {
  font-size: 0.85rem;
  color: var(--color-warm-gray);
  font-weight: 500;
}

/* Days list */
.days-list {
  display: flex;
  flex-direction: column;
}

/* ============================================
   Responsive
   ============================================ */
@media (max-width: 992px) {
  .result-layout {
    grid-template-columns: 1fr;
    padding: 0 var(--space-md) var(--space-2xl);
  }

  .sidebar {
    display: none;
  }

  .topbar {
    padding: var(--space-md);
  }

  .result-header {
    padding: var(--space-2xl) var(--space-md) var(--space-xl);
  }
}

@media (max-width: 768px) {
  .topbar-actions {
    flex-wrap: wrap;
  }

  .overview-grid {
    grid-template-columns: 1fr;
  }

  .map-container {
    height: 300px;
  }
}
</style>
