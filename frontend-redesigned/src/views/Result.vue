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
        <button class="topbar-back" @click="goBack">
          <span class="back-arrow">←</span>
          <span>{{ backLabel }}</span>
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
          <button class="topbar-btn" @click="shareTrip" v-if="tripPlan.share_token">分享</button>
          <button class="topbar-btn" @click="exportICS">导出日历</button>
        </div>
      </nav>

      <!-- Plan Switcher (shown when coming from comparison) -->
      <div v-if="cameFromComparison && siblingVariants.length > 1" class="plan-switcher no-print">
        <button
          v-for="v in siblingVariants"
          :key="v.variant"
          :class="['switcher-btn', { active: currentVariantKey === v.variant, failed: !v.plan }]"
          :disabled="!v.plan"
          @click="switchPlan(v.variant)"
        >
          {{ styleLabels[v.variant] || v.variant }}
        </button>
      </div>

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
                <div class="overview-item" v-if="tripPlan.transport_info && tripPlan.transport_info.estimated_cost > 0">
                  <span class="overview-label">出发城市</span>
                  <span class="overview-value">{{ tripPlan.transport_info.departure_city }} → {{ tripPlan.transport_info.destination_city }}</span>
                </div>
                <div class="overview-item" v-if="tripPlan.transport_info && tripPlan.transport_info.estimated_cost > 0">
                  <span class="overview-label">交通方式</span>
                  <span class="overview-value">{{ tripPlan.transport_info.recommended_mode }}（约¥{{ tripPlan.transport_info.estimated_cost }}，{{ tripPlan.transport_info.estimated_duration }}）</span>
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
                <ul class="suggestion-list">
                  <li v-for="(item, i) in parseSuggestions(tripPlan.overall_suggestions)" :key="i" class="suggestion-item">
                    <span class="suggestion-index">{{ i + 1 }}</span>
                    <span class="suggestion-text">{{ item }}</span>
                  </li>
                </ul>
              </div>
            </div>
          </section>

          <!-- CPS Booking Links -->
          <section v-if="tripPlan.cps_links && Object.keys(tripPlan.cps_links).length" class="content-section">
            <h2 class="section-heading">
              <span class="heading-accent">💡</span>
              预订链接
            </h2>
            <div class="cps-grid">
              <a v-for="(link, key) in tripPlan.cps_links" :key="key"
                 :href="link.url" target="_blank" rel="noopener noreferrer"
                 class="cps-card">
                <span class="cps-name">{{ link.name }}</span>
                <span class="cps-arrow">→</span>
              </a>
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
              <!-- 景点导航面板 -->
              <div class="map-nav-panel" :class="{ 'map-nav-panel--collapsed': navCollapsed }" v-if="!mapLoading">
                <div class="map-nav-header" @click="navCollapsed = !navCollapsed">
                  <span class="map-nav-title">📍 导航</span>
                  <span class="map-nav-toggle">{{ navCollapsed ? '▸' : '▾' }}</span>
                </div>
                <div v-if="!navCollapsed" class="map-nav-body">
                  <div v-for="(day, dIdx) in tripPlan.days" :key="day.day_index" class="map-nav-day">
                    <div class="map-nav-day-label" :style="{ color: ['#C4654A','#2d6a4f','#457b9d','#e76f51','#6d597a'][dIdx % 5] }">Day {{ dIdx + 1 }}</div>
                    <template v-if="dayPoints[dIdx]">
                      <button
                        v-for="(pt, pIdx) in dayPoints[dIdx]"
                        :key="pIdx"
                        class="map-nav-item"
                        @click="locatePoint(dIdx, pIdx)"
                      >
                        <span class="map-nav-icon" v-if="pt.type === 'hotel'">🏨</span>
                        <span class="map-nav-icon" v-else-if="pt.type === 'meal'">🍽</span>
                        <span class="map-nav-icon" v-else-if="pt.type === 'arrival'">{{ pt.name.includes('✈') ? '✈️' : '🚄' }}</span>
                        <span class="map-nav-dot" v-else :style="{ background: ['#C4654A','#2d6a4f','#457b9d','#e76f51','#6d597a'][dIdx % 5] }">{{ pt._attrIdx || '' }}</span>
                        <span class="map-nav-info">
                          <span class="map-nav-name">{{ pt.name }}</span>
                          <span class="map-nav-meta">
                            <span class="map-nav-tag" v-if="pt.type === 'attraction' && pt.detail?.visit_duration">{{ pt.detail.visit_duration }}分钟</span>
                            <span class="map-nav-tag" v-if="pt.type === 'meal' && pt.detail?.estimated_cost">¥{{ pt.detail.estimated_cost }}</span>
                            <span class="map-nav-tag" v-if="pt.type === 'hotel' && pt.detail?.price_range">{{ pt.detail.price_range }}</span>
                          </span>
                        </span>
                      </button>
                    </template>
                  </div>
                </div>
              </div>
              <!-- 重置视图按钮 -->
              <button class="map-reset-btn" @click="resetMapView" title="重置视图">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
              </button>
              <button
                v-if="showAnimBtn"
                class="anim-play-btn"
                :class="{ 'anim-play-btn--done': animDone, 'anim-play-btn--playing': animPlaying }"
                @click="playTransportAnim"
              >
                <span v-if="animDone && !animPlaying">✅ 行程动画完成 · 点击重播</span>
                <span v-else-if="animPlaying">{{ animStatusText }}</span>
                <span v-else>▶ 播放行程动画</span>
                <div v-if="animPlaying" class="anim-progress">
                  <div class="anim-progress-bar" :style="{ width: animProgress + '%' }"></div>
                </div>
              </button>
              <!-- 动画控制栏：暂停 + 速度 -->
              <div v-if="animPlaying" class="anim-controls">
                <button class="anim-ctrl-btn" @click="togglePause" :title="animPaused ? '继续' : '暂停'">
                  {{ animPaused ? '▶' : '⏸' }}
                </button>
                <div class="anim-speed-group">
                  <button v-for="s in [1, 1.5, 2]" :key="s" class="anim-speed-btn" :class="{ active: animSpeed === s }" @click="animSpeed = s">{{ s }}x</button>
                </div>
              </div>
            </div>
            <!-- 图例 -->
            <div class="map-legend">
              <div class="map-legend-item"><span class="legend-line legend-solid"></span>驾车</div>
              <div class="map-legend-item"><span class="legend-line legend-dashed"></span>步行</div>
              <div class="map-legend-item"><span class="legend-line legend-dotted"></span>直达</div>
              <div class="map-legend-item"><span class="legend-line legend-interday"></span>跨天</div>
              <div class="map-legend-item"><span class="legend-dot" style="background:#3b82f6;"></span>酒店</div>
              <div class="map-legend-item"><span class="legend-dot" style="background:#10b981;"></span>餐厅</div>
              <div class="map-legend-item"><span class="legend-dot" style="background:#8b5cf6;"></span>景点</div>
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
                :day-index="dayIndex"
                :expanded="activeDays.includes(day.day_index)"
                :edit-mode="editMode"
                :expanded-details="expandedAttractions"
                :transport-info="tripPlan.transport_info"
                :prev-hotel="dayIndex > 0 ? tripPlan.days[dayIndex - 1]?.hotel : null"
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import type { TripPlan } from '@/types'
import { editTripPlan, addFavorite, removeFavorite, listFavorites } from '@/services/api'
import AMapLoader from '@amap/amap-jsapi-loader'
import DayCard from '@/components/DayCard.vue'
import BudgetPanel from '@/components/BudgetPanel.vue'
import WeatherGrid from '@/components/WeatherGrid.vue'
import EmptyState from '@/components/EmptyState.vue'
const loadHtml2Pdf = () => new Promise<typeof import('html2pdf.js')>((resolve, reject) => {
  if (window.html2pdf) { resolve(window.html2pdf); return }
  const s = document.createElement('script')
  s.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.2/html2pdf.bundle.min.js'
  s.onload = () => resolve((window as any).html2pdf)
  s.onerror = reject
  document.head.appendChild(s)
})

const tripPlan = ref<TripPlan>({
  city: '',
  start_date: '',
  end_date: '',
  days: [],
  weather_info: [],
  overall_suggestions: '',
})

const router = useRouter()
const loading = ref(true)
const error = ref(false)
const saving = ref(false)
const mapLoading = ref(false)
const editMode = ref(false)
const originalPlan = ref<TripPlan | null>(null)
const selectedKeys = ref<string[]>(['overview'])
const activeDays = ref<number[]>([])
const expandedAttractions = ref<Record<string, boolean>>({})
const isFavorite = ref(false)
let map: any = null
let contentMarkers: any[] = []  // 跟踪所有内容标记，便于重建
let animFrameId: number | null = null
const showAnimBtn = ref(false)
const animPlaying = ref(false)
const animDone = ref(false)
const animProgress = ref(0)
const animStatusText = ref('▶ 播放行程动画')
const animSpeed = ref(1)
const animPaused = ref(false)
const navCollapsed = ref(false)
const dayPoints = ref<{ pos: [number, number]; type: string; name: string; detail?: any; _attrIdx?: number }[][]>([])
let initMapVersion = 0

// 方案切换：从 sessionStorage 加载其他方案
const cameFromComparison = sessionStorage.getItem('fromComparison') === '1'
const siblingVariants = ref<{ variant: string; plan: TripPlan | null }[]>([])
const currentVariantKey = ref('')

if (cameFromComparison) {
  try {
    const all = JSON.parse(sessionStorage.getItem('tripVariants') || '[]')
    siblingVariants.value = all
    // 找到当前方案的 variant key
    const currentPlan = JSON.parse(sessionStorage.getItem('tripPlan') || '{}')
    const match = all.find((v: any) => v.plan && v.plan.city === currentPlan.city && JSON.stringify(v.plan.days) === JSON.stringify(currentPlan.days))
    currentVariantKey.value = match?.variant || all[0]?.variant || ''
  } catch { /* ignore */ }
}

const switchPlan = (variant: string) => {
  const found = siblingVariants.value.find(v => v.variant === variant)
  if (!found?.plan) return
  // 取消正在运行的动画
  if (animFrameId) { cancelAnimationFrame(animFrameId); animFrameId = null }
  // 清除浮动动画元素
  const prevContainer = document.getElementById('amap-container')
  if (prevContainer) prevContainer.querySelectorAll('.amap-anim-elem').forEach(el => el.remove())
  currentVariantKey.value = variant
  tripPlan.value = found.plan
  sessionStorage.setItem('tripPlan', JSON.stringify(found.plan))
  // 重置动画状态
  showAnimBtn.value = false
  animPlaying.value = false
  animDone.value = false
  animProgress.value = 0
  animStatusText.value = '▶ 播放行程动画'
  dayPoints.value = []
  if (found.plan.days.length > 0) {
    activeDays.value = [found.plan.days[0].day_index]
  }
  checkFavorite()
  nextTick(() => initMap())
}

const styleLabels: Record<string, string> = { classic: '经典高效', relaxed: '轻松休闲', deep: '深度探索' }

const backLabel = cameFromComparison ? '返回对比' : '返回'
const goBack = () => {
  sessionStorage.removeItem('fromComparison')
  if (cameFromComparison) {
    router.push({ name: 'compare' })
  } else {
    router.push({ name: 'home' })
  }
}

// 创建带 InfoWindow 和 hover 效果的标记（initMap 和 geocodeMissing 重建共用）
const createMarkerWithInfo = (pt: { pos: [number, number]; type: string; name: string; detail?: any; _attrIdx?: number }, dayColor: string, dayIndex: number, mapObj: any) => {
  let markerContent = ''
  let zIndex = 100
  if (pt.type === 'arrival') {
    const isFlight = pt.name.includes('飞机') || pt.name.includes('✈')
    const arrColor = isFlight ? '#3b82f6' : '#10b981'
    markerContent = `<div style="position:relative;cursor:pointer;">
      <div style="width:34px;height:34px;border-radius:50%;background:${arrColor};color:white;display:flex;align-items:center;justify-content:center;font-size:16px;box-shadow:0 2px 12px ${arrColor}66;transition:transform 0.2s;border:2.5px solid white;"
        onmouseenter="this.style.transform='scale(1.15)'" onmouseleave="this.style.transform='scale(1)'"
      >${isFlight ? '✈️' : '🚄'}</div>
      <div style="position:absolute;top:-22px;left:50%;transform:translateX(-50%);background:${arrColor};color:white;padding:2px 6px;border-radius:6px;font-size:9px;white-space:nowrap;font-weight:500;font-family:var(--font-body);opacity:0;transition:opacity 0.2s;pointer-events:none;" class="marker-name">${pt.name}</div>
    </div>`
    zIndex = 105
  } else if (pt.type === 'hotel') {
    markerContent = `<div style="position:relative;cursor:pointer;">
      <div style="width:30px;height:30px;border-radius:8px;background:#f59e0b;color:white;display:flex;align-items:center;justify-content:center;font-size:15px;box-shadow:0 2px 10px #f59e0b66;transition:transform 0.2s;border:2px solid white;"
        onmouseenter="this.style.transform='scale(1.15)'" onmouseleave="this.style.transform='scale(1)'"
      >🏨</div>
      <div style="position:absolute;top:-22px;left:50%;transform:translateX(-50%);background:#f59e0b;color:white;padding:2px 6px;border-radius:6px;font-size:9px;white-space:nowrap;font-weight:500;font-family:var(--font-body);opacity:0;transition:opacity 0.2s;pointer-events:none;" class="marker-name">${pt.name}</div>
    </div>`
    zIndex = 90
  } else if (pt.type === 'meal') {
    markerContent = `<div style="position:relative;cursor:pointer;">
      <div style="width:28px;height:28px;border-radius:50%;background:#2d6a4f;color:white;display:flex;align-items:center;justify-content:center;font-size:14px;box-shadow:0 2px 10px #2d6a4f66;transition:transform 0.2s;border:2px solid white;"
        onmouseenter="this.style.transform='scale(1.15)'" onmouseleave="this.style.transform='scale(1)'"
      >🍽</div>
      <div style="position:absolute;top:-22px;left:50%;transform:translateX(-50%);background:#2d6a4f;color:white;padding:2px 6px;border-radius:6px;font-size:9px;white-space:nowrap;font-weight:500;font-family:var(--font-body);opacity:0;transition:opacity 0.2s;pointer-events:none;" class="marker-name">${pt.name}</div>
    </div>`
    zIndex = 95
  } else {
    markerContent = `<div style="position:relative;cursor:pointer;">
      <div style="width:32px;height:32px;border-radius:50%;background:${dayColor};color:white;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;font-family:var(--font-body);box-shadow:0 2px 10px ${dayColor}66;transition:transform 0.2s;transform:scale(1);border:2.5px solid white;"
        onmouseenter="this.style.transform='scale(1.15)'" onmouseleave="this.style.transform='scale(1)'"
      >${dayIndex + 1}-${pt._attrIdx || 1}</div>
      <div style="position:absolute;top:-24px;left:50%;transform:translateX(-50%);background:${dayColor};color:white;padding:2px 8px;border-radius:8px;font-size:10px;white-space:nowrap;font-weight:500;font-family:var(--font-body);opacity:0;transition:opacity 0.2s;pointer-events:none;" class="marker-name">${pt.name}</div>
    </div>`
  }
  const marker = new AMap.Marker({
    position: new AMap.LngLat(pt.pos[0], pt.pos[1]),
    title: pt.name,
    content: markerContent,
    offset: new AMap.Pixel(-16, -16),
    zIndex,
  })
  // InfoWindow
  const accentColor = pt.type === 'hotel' ? '#f59e0b' : pt.type === 'meal' ? '#2d6a4f' : pt.type === 'arrival' ? '#3b82f6' : dayColor
  const typeIcons: Record<string, string> = { hotel: '🏨', meal: '🍽️', attraction: '🎯', arrival: '✈️' }
  const typeLabels: Record<string, string> = { hotel: '住宿', meal: '餐饮', attraction: '景点', arrival: '到达' }
  let infoHtml = `<div style="font-family:'DM Sans',sans-serif;min-width:200px;max-width:260px;border-radius:12px;overflow:hidden;box-shadow:0 6px 24px rgba(0,0,0,0.15);border:1px solid rgba(0,0,0,0.06);">
    <div style="height:4px;background:linear-gradient(90deg,${accentColor},${accentColor}cc);"></div>
    <div style="padding:14px 16px 12px;">
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">
        <span style="font-size:14px;">${typeIcons[pt.type] || '📍'}</span>
        <span style="font-size:9px;color:${accentColor};font-weight:700;text-transform:uppercase;letter-spacing:0.8px;">${typeLabels[pt.type] || pt.type}</span>
      </div>
      <h3 style="margin:0 0 8px;font-size:14px;font-weight:700;color:#1a1a2e;line-height:1.3;">${pt.name}</h3>`
  if (pt.type === 'hotel') {
    const h = pt.detail
    if (h?.price_range) infoHtml += `<div style="display:inline-block;background:${accentColor}15;color:${accentColor};padding:2px 8px;border-radius:6px;font-size:11px;font-weight:600;margin-bottom:6px;">${h.price_range}</div>`
    if (h?.rating) infoHtml += `<p style="margin:4px 0;font-size:11px;color:#666;">⭐ ${h.rating} 评分</p>`
    if (h?.address) infoHtml += `<p style="margin:4px 0;font-size:10px;color:#999;">📍 ${h.address}</p>`
  } else if (pt.type === 'meal') {
    const m = pt.detail
    if (m?.estimated_cost) infoHtml += `<div style="display:inline-block;background:${accentColor}15;color:${accentColor};padding:2px 8px;border-radius:6px;font-size:11px;font-weight:600;margin-bottom:6px;">约¥${m.estimated_cost}/人</div>`
    if (m?.description) infoHtml += `<p style="margin:4px 0;font-size:11px;color:#666;line-height:1.4;">${m.description}</p>`
    if (m?.address) infoHtml += `<p style="margin:4px 0;font-size:10px;color:#999;">📍 ${m.address}</p>`
  } else if (pt.type === 'arrival') {
    infoHtml += `<div style="display:inline-block;background:${accentColor}15;color:${accentColor};padding:2px 8px;border-radius:6px;font-size:11px;font-weight:600;margin-bottom:6px;">${pt.name.includes('✈') ? '✈️ 航班到达' : '🚄 列车到达'}</div>`
    infoHtml += `<p style="margin:4px 0;font-size:10px;color:#999;">📍 从此处出发开始行程</p>`
  } else {
    const a = pt.detail
    if (a?.ticket_price !== undefined && a?.ticket_price > 0) {
      infoHtml += `<div style="display:inline-block;background:${accentColor}15;color:${accentColor};padding:2px 8px;border-radius:6px;font-size:11px;font-weight:600;margin-bottom:6px;">🎫 ¥${a.ticket_price}</div>`
    } else {
      infoHtml += `<div style="display:inline-block;background:#10b98115;color:#10b981;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:600;margin-bottom:6px;">免费</div>`
    }
    if (a?.visit_duration) infoHtml += `<p style="margin:4px 0;font-size:11px;color:#666;">⏱ 建议游览 ${a.visit_duration} 分钟</p>`
    if (a?.address) infoHtml += `<p style="margin:4px 0;font-size:10px;color:#999;">📍 ${a.address}</p>`
    if (a?.description) infoHtml += `<p style="margin:6px 0 0;font-size:10px;color:#888;line-height:1.4;">${a.description.slice(0, 80)}${a.description.length > 80 ? '...' : ''}</p>`
  }
  infoHtml += `<div style="margin:8px 0 0;padding-top:6px;border-top:1px solid #f0f0f0;font-size:9px;color:#bbb;font-family:'SF Mono',monospace;">${pt.pos[0].toFixed(4)}, ${pt.pos[1].toFixed(4)}</div>`
  infoHtml += `</div></div>`
  const infoWindow = new AMap.InfoWindow({ content: infoHtml, offset: new AMap.Pixel(0, -44), isCustom: true })
  marker.on('click', () => infoWindow.open(mapObj, marker.getPosition()))
  marker.on('mouseover', () => {
    const nameEl = marker.getContent()?.querySelector?.('.marker-name')
    if (nameEl) nameEl.style.opacity = '1'
  })
  marker.on('mouseout', () => {
    const nameEl = marker.getContent()?.querySelector?.('.marker-name')
    if (nameEl) nameEl.style.opacity = '0'
  })
  return marker
}

onMounted(() => {
  const savedPlan = sessionStorage.getItem('tripPlan')
  if (savedPlan) {
    try {
      tripPlan.value = JSON.parse(savedPlan)
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

// 收集每天所有地点（酒店→早餐→景点→午餐→景点→晚餐→酒店）
// 城市中心坐标常量（模块级，供 buildDayPoints 和 initMap 共用）
const cityCenters: Record<string, [number, number]> = {
  '北京': [116.397428, 39.90923],
  '上海': [121.473701, 31.230416],
  '广州': [113.264385, 23.129112],
  '深圳': [114.057868, 22.543099],
  '成都': [104.065735, 30.659462],
  '杭州': [120.153576, 30.287459],
  '武汉': [114.298572, 30.584355],
  '西安': [108.948024, 34.263161],
  '重庆': [106.504962, 29.533155],
  '南京': [118.767413, 32.041544],
  '厦门': [118.08942, 24.479833],
  '苏州': [120.619585, 31.299015],
  '昆明': [102.832891, 25.038898],
  '丽江': [100.227106, 26.855161],
  '大理': [100.225284, 25.590093],
  '桂林': [110.299091, 25.274195],
  '三亚': [109.50823, 18.247872],
  '青岛': [120.355178, 36.082982],
  '长沙': [112.938814, 28.228207],
  '郑州': [113.665412, 34.757975],
  '哈尔滨': [126.642464, 45.757161],
  '沈阳': [123.429096, 41.796767],
  '大连': [121.614682, 38.914003],
  '济南': [117.000923, 36.675807],
  '福州': [119.306239, 26.075302],
  '合肥': [117.283042, 31.86119],
  '南昌': [115.892151, 28.676493],
  '贵阳': [106.713478, 26.578343],
  '太原': [112.549248, 37.857014],
  '石家庄': [114.514859, 38.042838],
  '兰州': [103.834303, 36.0611],
  '乌鲁木齐': [87.617733, 43.792818],
  '拉萨': [91.132212, 29.660015],
  '呼和浩特': [111.670801, 40.818311],
  '银川': [106.278179, 38.46637],
  '西宁': [101.778228, 36.623178],
  '海口': [110.349228, 20.017377],
  '珠海': [113.553986, 22.270715],
  '东莞': [113.746262, 23.046237],
  '无锡': [120.311914, 31.491169],
  '宁波': [121.544006, 29.871489],
  '天津': [117.190182, 39.125595],
  '常州': [119.974062, 31.811233],
  '温州': [120.699367, 28.000026],
  '嘉兴': [120.750865, 30.753923],
  '绍兴': [120.582112, 30.000168],
  '金华': [119.649445, 29.079059],
  '台州': [121.420757, 28.656683],
  '泉州': [118.67587, 24.874132],
  '漳州': [117.661811, 24.510897],
  '洛阳': [112.453981, 34.619682],
  '开封': [114.341447, 34.798636],
  '黄山': [118.341379, 29.954451],
}

const buildDayPoints = () => {
  const rawCity = tripPlan.value.city || ''
  const city = rawCity.replace(/[市省]$/, '')
  const center = cityCenters[city] || [116.397428, 39.90923]
  const ti = tripPlan.value.transport_info
  // 坐标有效性校验（中国范围：经度 70-140，纬度 15-55）
  const isValidCoord = (lng: number, lat: number) =>
    lng > 70 && lng < 140 && lat > 15 && lat < 55
  // 城市范围校验：坐标必须在目的地城市 100km 内（排除出发城市坐标）
  const cityCenter = cityCenters[rawCity] || cityCenters[city]
  const depCenter = ti?.departure_city ? cityCenters[ti.departure_city] : null
  const inCityBounds = (lng: number, lat: number) => {
    if (!cityCenter) return true
    const dx = (lng - cityCenter[0]) * 111 * Math.cos(lat * Math.PI / 180)
    const dy = (lat - cityCenter[1]) * 111
    return Math.sqrt(dx * dx + dy * dy) < 100
  }
  const isDepCity = (lng: number, lat: number) => {
    if (!depCenter) return false
    const dx = (lng - depCenter[0]) * 111 * Math.cos(lat * Math.PI / 180)
    const dy = (lat - depCenter[1]) * 111
    return Math.sqrt(dx * dx + dy * dy) < 30
  }
  // Day 1 起点：有到达坐标（机场/车站）用到达坐标，否则用酒店
  const arrivalCoords = (ti?.arrival_longitude && ti?.arrival_latitude && isValidCoord(ti.arrival_longitude, ti.arrival_latitude))
    ? [ti.arrival_longitude, ti.arrival_latitude] as [number, number]
    : null
  let fallbackIdx = 0
  const makeFallback = (base: [number, number], idx: number): [number, number] => {
    // 小范围固定偏移（~100-300m），确保 fallback 点不会挤在一起
    const offsets = [
      [0.001, 0.0008], [-0.0008, 0.0006], [0.0006, -0.0009],
      [-0.0007, -0.0005], [0.0009, 0.0004], [-0.0005, 0.001],
    ]
    const off = offsets[idx % offsets.length]
    return [base[0] + off[0], base[1] + off[1]]
  }
  const result: { pos: [number, number]; type: string; name: string; detail?: any; _attrIdx?: number }[][] = []
  tripPlan.value.days.forEach((day, dayIdx) => {
    const points: { pos: [number, number]; type: string; name: string; detail?: any; _attrIdx?: number }[] = []
    // 跟踪最近一个有效坐标，作为 fallback 的参考点（避免 fallback 点飞到城市中心）
    let lastGoodPos: [number, number] = center
    // 过滤无效酒店（名称为"无"或空的酒店不显示标记）
    const hasValidHotel = day.hotel && day.hotel.name && day.hotel.name !== '无' && day.hotel.name !== '无酒店'
    // Day 1 且有到达坐标：从机场/车站出发，先到酒店放行李
    if (dayIdx === 0 && arrivalCoords) {
      const modeText = ti?.recommended_mode?.includes('飞机') ? '✈️ 到达' : '🚄 到达'
      points.push({ pos: arrivalCoords, type: 'arrival', name: modeText, detail: { name: modeText } })
      lastGoodPos = arrivalCoords
      // 到达后先去酒店放行李
      if (hasValidHotel && day.hotel!.location?.longitude && day.hotel!.location?.latitude && isValidCoord(day.hotel!.location.longitude, day.hotel!.location.latitude)) {
        const hp: [number, number] = [day.hotel!.location.longitude, day.hotel!.location.latitude]
        points.push({ pos: hp, type: 'hotel', name: `${day.hotel!.name} (放行李)`, detail: day.hotel })
        lastGoodPos = hp
      } else if (hasValidHotel) {
        const pos = makeFallback(lastGoodPos, fallbackIdx++)
        points.push({ pos, type: 'hotel', name: `${day.hotel!.name} (放行李)`, detail: day.hotel })
        lastGoodPos = pos
      }
    } else if (hasValidHotel && day.hotel!.location?.longitude && day.hotel!.location?.latitude && isValidCoord(day.hotel!.location.longitude, day.hotel!.location.latitude)) {
      const hp: [number, number] = [day.hotel!.location.longitude, day.hotel!.location.latitude]
      points.push({ pos: hp, type: 'hotel', name: day.hotel!.name, detail: day.hotel })
      lastGoodPos = hp
    } else if (hasValidHotel) {
      const pos = makeFallback(lastGoodPos, fallbackIdx++)
      points.push({ pos, type: 'hotel', name: day.hotel!.name, detail: day.hotel })
      lastGoodPos = pos
    }
    const meals = day.meals || []
    const breakfast = meals.find((m: any) => m.type === '早餐' || m.type === 'breakfast')
    const lunch = meals.find((m: any) => m.type === '午餐' || m.type === 'lunch')
    const dinner = meals.find((m: any) => m.type === '晚餐' || m.type === 'dinner')
    const validMealCoord = (m: any) => m?.location?.longitude && m?.location?.latitude
      && isValidCoord(m.location.longitude, m.location.latitude)
      && inCityBounds(m.location.longitude, m.location.latitude)
      && !isDepCity(m.location.longitude, m.location.latitude)
    if (validMealCoord(breakfast)) {
      const bp: [number, number] = [breakfast.location.longitude, breakfast.location.latitude]
      points.push({ pos: bp, type: 'meal', name: breakfast.name, detail: breakfast })
      lastGoodPos = bp
    } else if (breakfast) {
      const pos = makeFallback(lastGoodPos, fallbackIdx++)
      points.push({ pos, type: 'meal', name: breakfast.name, detail: breakfast })
      lastGoodPos = pos
    }
    const attrs = day.attractions || []
    const midIdx = Math.floor(attrs.length / 2)
    let attrSeq = 0
    let lunchInserted = false
    attrs.forEach((attr: any, i: number) => {
      attrSeq++
      const validAttrCoord = attr.location?.longitude && attr.location?.latitude
        && isValidCoord(attr.location.longitude, attr.location.latitude)
        && inCityBounds(attr.location.longitude, attr.location.latitude)
      if (validAttrCoord) {
        const ap: [number, number] = [attr.location.longitude, attr.location.latitude]
        points.push({ pos: ap, type: 'attraction', name: attr.name, detail: attr, _attrIdx: attrSeq })
        lastGoodPos = ap
      } else if (attr.name) {
        const pos = makeFallback(lastGoodPos, fallbackIdx++)
        points.push({ pos, type: 'attraction', name: attr.name, detail: attr, _attrIdx: attrSeq })
        lastGoodPos = pos
      }
      if (i === midIdx && validMealCoord(lunch)) {
        const lp: [number, number] = [lunch.location.longitude, lunch.location.latitude]
        points.push({ pos: lp, type: 'meal', name: lunch.name, detail: lunch })
        lastGoodPos = lp
        lunchInserted = true
      } else if (i === midIdx && lunch) {
        const pos = makeFallback(lastGoodPos, fallbackIdx++)
        points.push({ pos, type: 'meal', name: lunch.name, detail: lunch })
        lastGoodPos = pos
        lunchInserted = true
      }
    })
    // 如果景点为空或午餐未被插入，独立添加午餐
    if (!lunchInserted && lunch) {
      if (validMealCoord(lunch)) {
        const lp: [number, number] = [lunch.location.longitude, lunch.location.latitude]
        points.push({ pos: lp, type: 'meal', name: lunch.name, detail: lunch })
        lastGoodPos = lp
      } else {
        const pos = makeFallback(lastGoodPos, fallbackIdx++)
        points.push({ pos, type: 'meal', name: lunch.name, detail: lunch })
        lastGoodPos = pos
      }
    }
    if (validMealCoord(dinner)) {
      const dp: [number, number] = [dinner.location.longitude, dinner.location.latitude]
      points.push({ pos: dp, type: 'meal', name: dinner.name, detail: dinner })
      lastGoodPos = dp
    } else if (dinner) {
      const pos = makeFallback(lastGoodPos, fallbackIdx++)
      points.push({ pos, type: 'meal', name: dinner.name, detail: dinner })
      lastGoodPos = pos
    }
    // 返回酒店（同一天酒店坐标）
    if (hasValidHotel && day.hotel!.location?.longitude && day.hotel!.location?.latitude && isValidCoord(day.hotel!.location.longitude, day.hotel!.location.latitude) && inCityBounds(day.hotel!.location.longitude, day.hotel!.location.latitude)) {
      points.push({ pos: [day.hotel!.location.longitude, day.hotel!.location.latitude], type: 'hotel', name: `${day.hotel!.name} (返回)`, detail: day.hotel })
    } else if (day.hotel) {
      const returnPos = points[0]?.pos || makeFallback(center, fallbackIdx++)
      points.push({ pos: returnPos, type: 'hotel', name: `${day.hotel.name} (返回)`, detail: day.hotel })
    }
    result.push(points)
  })
  return result
}

const initMap = async () => {
  mapLoading.value = true
  const myVersion = ++initMapVersion
  try {
    const mapContainer = document.getElementById('amap-container')
    if (!mapContainer) return

    try {
      const AMap = await AMapLoader.load({
        key: import.meta.env.VITE_AMAP_KEY || '',
        version: '2.0',
        plugins: ['AMap.Scale', 'AMap.ToolBar', 'AMap.InfoWindow', 'AMap.Driving', 'AMap.Walking', 'AMap.Geocoder'],
      })

      if (myVersion !== initMapVersion) return

      if (map) {
        contentMarkers = []
        map.destroy()
        map = null
      }

      const dayPositions: any[][] = []
      dayPoints.value = []

      if (tripPlan.value.days.length > 0) {
        // 找第一个可用坐标作为地图中心（景点→酒店→餐厅→城市中心）
        const cityCenter = cityCenters[tripPlan.value.city] || [116.397428, 39.90923]
        let mapCenter: [number, number] = cityCenter
        for (const day of tripPlan.value.days) {
          const firstAttr = day.attractions?.[0]
          if (firstAttr?.location?.longitude && firstAttr?.location?.latitude) {
            mapCenter = [firstAttr.location.longitude, firstAttr.location.latitude]
            break
          }
          if (day.hotel?.location?.longitude && day.hotel?.location?.latitude) {
            mapCenter = [day.hotel.location.longitude, day.hotel.location.latitude]
            break
          }
          const firstMeal = (day.meals || [])[0]
          if (firstMeal?.location?.longitude && firstMeal?.location?.latitude) {
            mapCenter = [firstMeal.location.longitude, firstMeal.location.latitude]
            break
          }
        }

        map = new AMap.Map(mapContainer, {
            zoom: 12,
            center: mapCenter,
            resizeEnable: true,
          })

          map.addControl(new AMap.Scale({ position: 'LB' }))
          map.addControl(new AMap.ToolBar({ position: 'RT', liteStyle: true }))

          // 收集每天所有地点（酒店→早餐→景点→午餐→景点→晚餐→酒店）
          dayPoints.value = buildDayPoints()
          dayPoints.value.forEach((points) => {
            dayPositions.push(points.map(p => p.pos))
          })

          // 创建标记
          const dayColors = ['#C4654A', '#2d6a4f', '#457b9d', '#e76f51', '#6d597a']
          dayPoints.value.forEach((points, dIdx) => {
            const dayColor = dayColors[dIdx % dayColors.length]
            points.forEach((pt) => {
              const marker = createMarkerWithInfo(pt, dayColor, dIdx, map)
              map.add(marker)
              contentMarkers.push(marker)
            })
          })

          // ===== 地理编码兜底：为没有坐标的酒店/餐厅补坐标 =====
          const geocoder = new AMap.Geocoder()
          const geocodeQuery = (query: string): Promise<{longitude: number, latitude: number} | null> => {
            return new Promise((resolve) => {
              geocoder.getLocation(query, (status: string, result: any) => {
                if (status === 'complete' && result?.geocodes?.length) {
                  const geo = result.geocodes[0].location
                  resolve({ longitude: geo.lng, latitude: geo.lat })
                } else {
                  resolve(null)
                }
              })
            })
          }
          const city = tripPlan.value.city
          const geocodeMissing = async () => {
            const tasks: Promise<void>[] = []
            tripPlan.value.days.forEach((day) => {
              // 景点无坐标 → 优先用地址查，其次用名称+城市查
              ;(day.attractions || []).forEach((attr: any) => {
                if (!attr.location?.longitude || !attr.location?.latitude) {
                  const query = attr.address || (attr.name ? `${attr.name} ${city}` : '')
                  if (query) {
                    tasks.push(geocodeQuery(query).then(loc => {
                      if (loc) attr.location = loc
                    }).catch(() => {}))
                  }
                }
              })
              // 酒店无坐标 → 优先用地址查，其次用名称+城市查
              if (day.hotel && (!day.hotel.location?.longitude || !day.hotel.location?.latitude)) {
                const query = day.hotel!.address || (day.hotel!.name ? `${day.hotel!.name} ${city}` : '')
                if (query) {
                  tasks.push(geocodeQuery(query).then(loc => {
                    if (loc) day.hotel!.location = loc
                  }).catch(() => {}))
                }
              }
              // 餐厅无坐标 → 优先用地址查，其次用名称+城市查
              ;(day.meals || []).forEach((meal: any) => {
                if (!meal.location?.longitude || !meal.location?.latitude) {
                  const query = meal.address || (meal.name ? `${meal.name} ${city}` : '')
                  if (query) {
                    tasks.push(geocodeQuery(query).then(loc => {
                      if (loc) meal.location = loc
                    }).catch(() => {}))
                  }
                }
              })
            })
            await Promise.all(tasks)
          }

          // 异步执行地理编码，完成后刷新标记和导航面板
          geocodeMissing().then(() => {
            if (myVersion !== initMapVersion || !map) return
            // 重新收集 dayPoints（含新解析的坐标）
            dayPoints.value = buildDayPoints()
            // 重建标记：移除旧标记，基于更新后的坐标重新创建
            contentMarkers.forEach(m => { if (map) map.remove(m) })
            contentMarkers = []
            const dayColors = ['#C4654A', '#2d6a4f', '#457b9d', '#e76f51', '#6d597a']
            dayPoints.value.forEach((points, dIdx) => {
              const dayColor = dayColors[dIdx % dayColors.length]
              points.forEach((pt) => {
                const marker = createMarkerWithInfo(pt, dayColor, dIdx, map)
                map.add(marker)
                contentMarkers.push(marker)
              })
            })
            // 更新 dayPositions 用于动画路线
            dayPositions.length = 0
            dayPoints.value.forEach(points => dayPositions.push(points.map(p => p.pos)))
            // 清除路线缓存，坐标已更新需重新计算
            segmentCache.clear()
            drawnSegments.clear()
            // 重置路线完成计数，重建 routesReady promise
            completedSegments = 0
            routeGen++
            recalcSegments()
            routesReady = new Promise<void>((r) => { routesReadyResolve = r })
            drawAllRoutes()
          }).catch(() => {})

          // ===== 城际交通动画 =====
          const transportInfo = tripPlan.value.transport_info
          const depCoords = cityCenters[transportInfo?.departure_city || '']
          // 优先使用到达地点坐标（机场/车站），否则用城市中心
          const destCoords = (transportInfo?.arrival_longitude && transportInfo?.arrival_latitude)
            ? [transportInfo.arrival_longitude, transportInfo.arrival_latitude] as [number, number]
            : cityCenters[tripPlan.value.city]
          if (depCoords && destCoords && transportInfo && transportInfo.estimated_cost > 0) {
            // 调整地图视野以包含两端
            map.setFitView(null, false, [60, 60, 60, 60])

            const mode = transportInfo.recommended_mode
            const isFlight = mode.includes('飞机')
            const isTrain = mode.includes('高铁')
            const transportEmoji = isFlight ? '✈️' : isTrain ? '🚄' : '🚗'
            const arcColor = isFlight ? '#3b82f6' : isTrain ? '#10b981' : '#f59e0b'

            // 城际路线：驾车/高铁尝试真实路线，飞机用弧线
            let intercityPath: [number, number][] = []
            const intercityReady = new Promise<void>((resolve) => {
              if (!isFlight) {
                // 非飞行模式：尝试 Driving API 获取真实路线
                // 三级降级：JS API Driving → 后端代理 → 弧线兜底
                const tryIntercityProxy = () => {
                  const originStr = `${depCoords[0]},${depCoords[1]}`
                  const destStr = `${destCoords[0]},${destCoords[1]}`
                  fetch(`/api/trip/route?origin=${originStr}&destination=${destStr}&mode=driving`)
                    .then(r => r.json())
                    .then((data: any) => {
                      if (data.path && data.path.length > 0) {
                        intercityPath = data.path
                        console.log(`[城际路线] 代理成功，${data.path.length} 个路径点`)
                      } else {
                        console.warn(`[城际路线] 代理返回空路径，使用弧线兜底`)
                      }
                      resolve()
                    })
                    .catch(() => {
                      console.warn(`[城际路线] 代理失败，使用弧线兜底`)
                      resolve()
                    })
                }
                try {
                  const interDriving = new AMap.Driving({ policy: AMap.DrivingPolicy.LEAST_TIME })
                  interDriving.search(
                    new AMap.LngLat(depCoords[0], depCoords[1]),
                    new AMap.LngLat(destCoords[0], destCoords[1]),
                    (status: string, result: any) => {
                      if (status === 'complete') {
                        const path = extractPath(result)
                        if (path.length > 0) {
                          intercityPath = path
                          console.log(`[城际路线] JS API 成功，${path.length} 个路径点`)
                          resolve()
                          return
                        }
                      }
                      console.warn(`[城际路线] JS API 失败 (${status})，尝试后端代理`)
                      tryIntercityProxy()
                    }
                  )
                } catch {
                  console.warn(`[城际路线] JS API 不可用，尝试后端代理`)
                  tryIntercityProxy()
                }
              } else {
                resolve()
              }
            })

            // 计算贝塞尔曲线控制点（仅飞机用弧线）
            const midLng = (depCoords[0] + destCoords[0]) / 2
            const midLat = (depCoords[1] + destCoords[1]) / 2
            const dist = Math.sqrt(
              Math.pow(depCoords[0] - destCoords[0], 2) +
              Math.pow(depCoords[1] - destCoords[1], 2)
            )

            // 飞机：画弧线 | 高铁/驾车：不画弧线，等真实路线
            let arcGlow: any = null, arcAnimated: any = null
            let bezierPoints: [number, number][] = []

            if (isFlight) {
              const arcHeight = dist * 0.15
              const controlPoint = [midLng, midLat + arcHeight]
              for (let i = 0; i <= 80; i++) {
                const t = i / 80
                bezierPoints.push([
                  (1 - t) * (1 - t) * depCoords[0] + 2 * (1 - t) * t * controlPoint[0] + t * t * destCoords[0],
                  (1 - t) * (1 - t) * depCoords[1] + 2 * (1 - t) * t * controlPoint[1] + t * t * destCoords[1],
                ])
              }
              arcGlow = new AMap.Polyline({ path: bezierPoints, strokeColor: arcColor, strokeWeight: 14, strokeOpacity: 0.12, lineJoin: 'round', lineCap: 'round' })
              map.add(arcGlow)
              arcAnimated = new AMap.Polyline({ path: bezierPoints, strokeColor: arcColor, strokeWeight: 4, strokeOpacity: 0.8, lineJoin: 'round', lineCap: 'round' })
              map.add(arcAnimated)
            }

            // 城际交通方式标签（在路线中点）
            const labelPos = isFlight && bezierPoints.length > 0
              ? bezierPoints[Math.floor(bezierPoints.length / 2)]
              : [(depCoords[0] + destCoords[0]) / 2, (depCoords[1] + destCoords[1]) / 2]
            const intercityModeLabel = isFlight ? '✈️ 飞机' : isTrain ? '🚄 高铁' : '🚗 驾车'
            const intercityModeMarker = new AMap.Marker({
              position: new AMap.LngLat(labelPos[0], labelPos[1]),
              content: `<div style="background:${arcColor};color:white;padding:3px 10px;border-radius:12px;font-size:10px;white-space:nowrap;font-weight:600;box-shadow:0 2px 8px ${arcColor}44;pointer-events:none;font-family:var(--font-body);">${intercityModeLabel} · ${transportInfo.estimated_duration}</div>`,
              offset: new AMap.Pixel(0, -20),
              zIndex: 112,
            })
            map.add(intercityModeMarker)

            // 真实路线就绪后：飞机替换弧线，高铁/驾车直接画
            intercityReady.then(() => {
              if (intercityPath.length > 0 && map) {
                if (arcGlow) map.remove(arcGlow)
                if (arcAnimated) map.remove(arcAnimated)
                // 真实路线发光底层
                map.add(new AMap.Polyline({
                  path: intercityPath,
                  strokeColor: arcColor,
                  strokeWeight: 14,
                  strokeOpacity: 0.12,
                  lineJoin: 'round',
                  lineCap: 'round',
                }))
                const realRoute = new AMap.Polyline({
                  path: intercityPath,
                  strokeColor: arcColor,
                  strokeWeight: 5,
                  strokeOpacity: 0.85,
                  lineJoin: 'round',
                  lineCap: 'round',
                  showDir: true,
                })
                map.add(realRoute)
              }
            })

            // 出发点标记
            const depMarker = new AMap.Marker({
              position: depCoords,
              content: `<div style="background:white;border:2.5px solid ${arcColor};border-radius:50%;width:36px;height:36px;display:flex;align-items:center;justify-content:center;box-shadow:0 3px 12px ${arcColor}44,0 1px 4px rgba(0,0,0,0.1);transition:transform 0.2s;" onmouseenter="this.style.transform='scale(1.1)'" onmouseleave="this.style.transform='scale(1)'">
                <svg width="20" height="20" viewBox="0 0 32 32" fill="none"><g transform="rotate(90, 16, 16)"><path d="M16 3L19 11L28 13L19 15L16 28L13 15L4 13L13 11Z" fill="${arcColor}" stroke="white" stroke-width="1.2" stroke-linejoin="round"/></g></svg>
              </div>`,
              offset: new AMap.Pixel(-18, -18),
              zIndex: 110,
            })
            map.add(depMarker)

            // 目的地标记
            const destMarker = new AMap.Marker({
              position: destCoords,
              content: `<div style="background:white;border:2.5px solid #C4654A;border-radius:50%;width:36px;height:36px;display:flex;align-items:center;justify-content:center;font-size:18px;box-shadow:0 3px 12px rgba(196,101,74,0.3),0 1px 4px rgba(0,0,0,0.1);transition:transform 0.2s;" onmouseenter="this.style.transform='scale(1.1)'" onmouseleave="this.style.transform='scale(1)'">📍</div>`,
              offset: new AMap.Pixel(-18, -18),
              zIndex: 110,
            })
            map.add(destMarker)

            // 出发地/目的地文字标签
            const depLabel = new AMap.Marker({
              position: depCoords,
              content: `<div style="background:${arcColor};color:white;padding:3px 10px;border-radius:12px;font-size:11px;white-space:nowrap;font-weight:600;box-shadow:0 2px 8px ${arcColor}44;letter-spacing:0.3px;">${transportInfo.departure_city}</div>`,
              offset: new AMap.Pixel(0, -20),
              zIndex: 111,
            })
            map.add(depLabel)

            const destLabel = new AMap.Marker({
              position: destCoords,
              content: `<div style="background:#C4654A;color:white;padding:3px 10px;border-radius:12px;font-size:11px;white-space:nowrap;font-weight:600;box-shadow:0 2px 8px rgba(196,101,74,0.4);letter-spacing:0.3px;">${tripPlan.value.city}</div>`,
              offset: new AMap.Pixel(0, -20),
              zIndex: 111,
            })
            map.add(destLabel)

            // 动画：使用 AMap.Marker 定位（避免 lngLatToContainerPixel 失效问题）
            let animPlayed = false

            // 显示播放按钮，等待用户点击
            showAnimBtn.value = true

            // 挂载到 window 供按钮调用
            ;(window as any).__playTransportAnim = () => {
              if (!animPlayed && map) {
                animPlayed = true

                // 重播：重置动画状态
                ;(window as any).__resetTransportAnim = () => {
                  animPlayed = false
                  // 清除旧的浮动动画元素
                  const mc = document.getElementById('amap-container')
                  if (mc) mc.querySelectorAll('.amap-anim-elem').forEach(el => el.remove())
                }

                const mapContainer = document.getElementById('amap-container')

                // ====== 预渲染 360° SVG 缓存（每10°一个，共36个/交通工具） ======
                // AMap setContent() 每次替换整个 DOM，无法用 CSS transition
                // 预渲染避免每帧重新生成 SVG 字符串，提升动画流畅度
                const svgTemplates: Record<string, string> = {
                  '✈️': `<path d="M16 2L20 10L29 12L20 14L18 28L16 32L14 28L12 14L3 12L12 10Z" fill="#3b82f6" stroke="white" stroke-width="1" stroke-linejoin="round"/><circle cx="16" cy="12" r="2" fill="white" opacity="0.9"/><path d="M14 18L12 24M18 18L20 24" stroke="white" stroke-width="0.8" opacity="0.5"/>`,
                  '🚄': `<rect x="10" y="5" width="12" height="22" rx="6" fill="#10b981" stroke="white" stroke-width="1.2"/><rect x="12" y="8" width="8" height="5" rx="2.5" fill="white" opacity="0.9"/><rect x="12" y="16" width="8" height="4" rx="2" fill="white" opacity="0.5"/><circle cx="13" cy="24" r="1.5" fill="white" opacity="0.8"/><circle cx="19" cy="24" r="1.5" fill="white" opacity="0.8"/><path d="M14 5L16 2L18 5" stroke="white" stroke-width="0.8" fill="none" opacity="0.6"/>`,
                  '🚗': `<rect x="8" y="4" width="16" height="24" rx="6" fill="#f59e0b" stroke="white" stroke-width="1.2"/><rect x="10" y="7" width="12" height="6" rx="3" fill="white" opacity="0.85"/><rect x="10" y="19" width="12" height="5" rx="2" fill="white" opacity="0.5"/><circle cx="10" cy="4" r="2" fill="white" opacity="0.9"/><circle cx="22" cy="4" r="2" fill="white" opacity="0.9"/><circle cx="10" cy="28" r="2" fill="white" opacity="0.9"/><circle cx="22" cy="28" r="2" fill="white" opacity="0.9"/>`,
                }
                const defaultTemplate = `<circle cx="16" cy="16" r="13" fill="#666" stroke="white" stroke-width="2"/>`

                // 预渲染：transportEmoji → angleBucket(0-179) → SVG string
                const preRenderedSvgs: Record<string, string[]> = {}
                const renderSvg = (emoji: string, deg: number) => {
                  const tmpl = svgTemplates[emoji] || defaultTemplate
                  return `<svg width="32" height="32" viewBox="0 0 32 32" fill="none" style="filter:drop-shadow(0 2px 6px rgba(0,0,0,0.4))"><g transform="rotate(${deg}, 16, 16)">${tmpl}</g></svg>`
                }
                // 预渲染当前交通工具的180个角度（每2°一个，旋转平滑）
                const angles: string[] = []
                for (let d = 0; d < 360; d += 2) {
                  angles.push(renderSvg(transportEmoji, d))
                }
                preRenderedSvgs[transportEmoji] = angles

                const getSvg = (emoji: string, angle: number) => {
                  const bucket = preRenderedSvgs[emoji]
                  if (bucket) {
                    const idx = Math.round(((angle % 360 + 360) % 360) / 2) % 180
                    return bucket[idx]
                  }
                  return renderSvg(emoji, angle)
                }

                // 创建初始图标 Marker（角度 0 = 朝北）
                // 清除旧的动画标记（重播时）
                const oldIconMarker = (window as any).__animIconMarker
                if (oldIconMarker && map) map.remove(oldIconMarker)
                const iconMarker = new AMap.Marker({
                  position: new AMap.LngLat(0, 0),
                  content: `<div>${getSvg(transportEmoji, 0)}</div>`,
                  offset: new AMap.Pixel(-16, -16),
                  zIndex: 999,
                  map,
                })
                ;(window as any).__animIconMarker = iconMarker

                // 日标签（DOM 悬浮在地图顶部）
                let dayLabel: HTMLDivElement | null = null
                if (mapContainer) {
                  dayLabel = document.createElement('div')
                  dayLabel.className = 'amap-anim-elem'
                  dayLabel.style.cssText = 'position:absolute;top:12px;left:50%;transform:translateX(-50%);background:rgba(0,0,0,0.75);color:white;padding:6px 16px;border-radius:16px;font-size:13px;font-weight:600;pointer-events:none;z-index:1000;opacity:0;transition:opacity 0.3s;font-family:var(--font-body);white-space:nowrap;'
                  mapContainer.appendChild(dayLabel)
                }

                const showDayLabel = (text: string) => {
                  if (dayLabel) { dayLabel.textContent = text; dayLabel.style.opacity = '1' }
                }
                const hideDayLabel = () => {
                  if (dayLabel) dayLabel.style.opacity = '0'
                }

                // 通用动画函数（NVIDIA优化：预计算角度 + 高效拖尾管理）
                const animateAlongPath = (
                  path: [number, number][],
                  emoji: string,
                  color: string,
                  label: string,
                  durationMs: number,
                ): Promise<void> => {
                  return new Promise((resolve) => {
                    showDayLabel(label)

                    const total = path.length
                    if (total === 0) { resolve(); return }

                    const startTime = performance.now()
                    let pausedAt = 0
                    let totalPausedMs = 0
                    const maxTrail = 18

                    // 预计算每个路径点的朝向角度（避免每帧重复 atan2 计算）
                    const angles = new Float32Array(total)
                    for (let i = 0; i < total - 1; i++) {
                      const dx = path[i + 1][0] - path[i][0]
                      const dy = path[i + 1][1] - path[i][1]
                      // 图标 SVG 鼻子朝上（y轴负方向），所以 east=90°, north=0°
                      angles[i] = (Math.atan2(dx, dy) * 180 / Math.PI + 360) % 360
                    }
                    angles[total - 1] = angles[total - 2] || 0

                    let lastAngleBucket = -999
                    let lastTrailIdx = -1

                    // Canvas 拖尾层：用单个 Canvas 渲染所有拖尾圆点，替代 CircleMarker DOM
                    let trailCanvas: HTMLCanvasElement | null = null
                    let trailCtx: CanvasRenderingContext2D | null = null
                    const trailPoints: { x: number; y: number; age: number }[] = []
                    const initTrailCanvas = () => {
                      const mc = document.getElementById('amap-container')
                      if (!mc) return
                      trailCanvas = document.createElement('canvas')
                      trailCanvas.className = 'amap-anim-elem'
                      trailCanvas.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:997;'
                      mc.appendChild(trailCanvas)
                      trailCanvas.width = mc.clientWidth
                      trailCanvas.height = mc.clientHeight
                      trailCtx = trailCanvas.getContext('2d')
                    }
                    initTrailCanvas()

                    const tick = (now: number) => {
                      if (!map) {
                        if (trailCtx && trailCanvas) { trailCtx.clearRect(0, 0, trailCanvas.width, trailCanvas.height); trailCanvas.remove() }
                        resolve(); return
                      }

                      // 暂停处理：冻结时间
                      if (animPaused.value) {
                        if (pausedAt === 0) pausedAt = now
                        animFrameId = requestAnimationFrame(tick)
                        return
                      } else if (pausedAt > 0) {
                        totalPausedMs += now - pausedAt
                        pausedAt = 0
                      }

                      const realElapsed = now - startTime - totalPausedMs
                      const elapsed = realElapsed * animSpeed.value
                      const progress = Math.min(elapsed / durationMs, 1)

                      // 缓动：easeInOutCubic
                      const eased = progress < 0.5
                        ? 4 * progress * progress * progress
                        : 1 - Math.pow(-2 * progress + 2, 3) / 2

                      const rawIdx = eased * (total - 1)
                      const idx = Math.min(Math.floor(rawIdx), total - 2)
                      const frac = rawIdx - idx
                      const p0 = path[idx]
                      const p1 = path[Math.min(idx + 1, total - 1)]

                      // 位置插值：在两个路径点之间线性插值
                      const lng = p0[0] + (p1[0] - p0[0]) * frac
                      const lat = p0[1] + (p1[1] - p0[1]) * frac
                      iconMarker.setPosition(new AMap.LngLat(lng, lat))

                      // 角度插值：平滑过渡相邻点的朝向
                      const a0 = angles[idx]
                      let a1 = angles[Math.min(idx + 1, total - 1)]
                      // 处理角度跨越 0°/360° 的情况
                      let diff = a1 - a0
                      if (diff > 180) diff -= 360
                      if (diff < -180) diff += 360
                      const angle = (a0 + diff * frac + 360) % 360

                      // 旋转：角度变化 >0.5° 才更新 DOM（视觉无感知阈值，避免每帧替换）
                      if (Math.abs(angle - lastAngleBucket) > 0.5) {
                        lastAngleBucket = angle
                        iconMarker.setContent(`<div style="position:relative;">
                          <div style="position:absolute;inset:-8px;border-radius:50%;background:radial-gradient(circle,${color}55 0%,transparent 70%);pointer-events:none;"></div>
                          ${getSvg(emoji, angle)}
                        </div>`)
                      }

                      // Canvas 拖尾渲染
                      if (trailCtx && trailCanvas && map) {
                        if (idx !== lastTrailIdx) {
                          lastTrailIdx = idx
                          const pixel = map.lngLatToContainer(new AMap.LngLat(lng, lat))
                          if (pixel) {
                            trailPoints.push({ x: pixel.getX(), y: pixel.getY(), age: 0 })
                            if (trailPoints.length > maxTrail) trailPoints.shift()
                          }
                        }
                        // 清除并重绘拖尾
                        trailCtx.clearRect(0, 0, trailCanvas.width, trailCanvas.height)
                        const len = trailPoints.length
                        for (let i = 0; i < len; i++) {
                          const tp = trailPoints[i]
                          tp.age++
                          const fade = Math.max(0, 1 - tp.age / 30)
                          // 拖尾越老越小、越透明，模拟粒子衰减
                          const size = Math.max(1, 6 * fade * fade)
                          const alpha = fade * fade * 0.6
                          trailCtx.beginPath()
                          trailCtx.arc(tp.x, tp.y, size, 0, Math.PI * 2)
                          trailCtx.fillStyle = color + Math.round(alpha * 255).toString(16).padStart(2, '0')
                          trailCtx.fill()
                        }
                        // 移除过期点
                        while (trailPoints.length > 0 && trailPoints[0].age > 30) {
                          trailPoints.shift()
                        }
                      }

                      if (progress < 1) {
                        animFrameId = requestAnimationFrame(tick)
                      } else {
                        // 清理 Canvas 拖尾
                        if (trailCtx && trailCanvas) {
                          trailCtx.clearRect(0, 0, trailCanvas.width, trailCanvas.height)
                          trailCanvas.remove()
                        }
                        trailPoints.length = 0
                        resolve()
                      }
                    }

                    animFrameId = requestAnimationFrame(tick)
                  })
                }

                // 主动画序列
                const runAnimation = async () => {
                  if (!map) { animPlaying.value = false; return }
                  // 取消上一次未完成的动画循环
                  if (animFrameId) { cancelAnimationFrame(animFrameId); animFrameId = null }

                  await intercityReady
                  await routesReady  // 等待所有路线绘制完成

                  const localRoutes = getDayRoutes()
                  const localCount = localRoutes.filter(r => r && r.length > 0).length
                  const totalPhases = 1 + localCount
                  let currentPhase = 0

                  // 阶段1：城际交通
                  const cityPath = intercityPath.length > 0 ? intercityPath : bezierPoints
                  animStatusText.value = isFlight ? '✈️ 飞行中...' : isTrain ? '🚄 列车行驶中...' : '🚗 驾车前往...'
                  await animateAlongPath(cityPath, transportEmoji, arcColor, `${transportInfo.departure_city} → ${tripPlan.value.city}`, 2000)
                  currentPhase++
                  animProgress.value = Math.round((currentPhase / totalPhases) * 100)

                  await new Promise(r => setTimeout(r, 600))

                  // 阶段2：市内逐日
                  const hasLocalRoutes = localRoutes.some(r => r && r.length > 0)
                  if (hasLocalRoutes) {
                    for (let dayIdx = 0; dayIdx < localRoutes.length; dayIdx++) {
                      const route = localRoutes[dayIdx]
                      if (!route || route.length === 0) continue

                      animStatusText.value = `🚗 Day ${dayIdx + 1} 行程中...`
                      await animateAlongPath(route, '🚗', dayColors[dayIdx % dayColors.length], `Day ${dayIdx + 1} · ${tripPlan.value.days[dayIdx]?.description || '行程'}`, 1500)
                      currentPhase++
                      animProgress.value = Math.round((currentPhase / totalPhases) * 100)

                      if (dayIdx < localRoutes.length - 1) {
                        await new Promise(r => setTimeout(r, 200))
                      }
                    }
                  }

                  animProgress.value = 100

                  // 完成标记 — SVG 内嵌动画（光环扩散 + 弹性缩放 + 勾号绘制）
                  iconMarker.setContent(`<div style="filter:drop-shadow(0 3px 10px rgba(45,106,79,0.5));">
                    <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                      <circle cx="20" cy="20" r="18" fill="none" stroke="#2d6a4f" stroke-width="2" opacity="0.3">
                        <animate attributeName="r" values="10;22" dur="0.6s" fill="freeze"/>
                        <animate attributeName="opacity" values="0.5;0" dur="0.6s" fill="freeze"/>
                        <animate attributeName="stroke-width" values="3;0.5" dur="0.6s" fill="freeze"/>
                      </circle>
                      <circle cx="20" cy="20" r="16" fill="#2d6a4f" stroke="white" stroke-width="2.5">
                        <animate attributeName="r" values="0;18;14.5;16" dur="0.55s" fill="freeze"/>
                        <animate attributeName="opacity" values="0;1;1;1" dur="0.25s" fill="freeze"/>
                      </circle>
                      <path d="M12 20L17.5 25.5L28 14.5" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                        <animate attributeName="stroke-dasharray" values="0,50;50,0" dur="0.4s" begin="0.25s" fill="freeze"/>
                      </path>
                    </svg>
                  </div>`)
                  hideDayLabel()
                  animDone.value = true
                  animPlaying.value = false
                  animStatusText.value = '✅ 行程动画完成'
                }

                runAnimation().catch((e) => {
                  console.error('[动画异常]', e)
                  animPlaying.value = false
                  animStatusText.value = '❌ 动画异常中断'
                })
              }
            }
          }

          // 按天绘制路线 + 收集路线点用于动画
          const segmentCache: Map<string, [number, number][]> = new Map()
          const drawnSegments: Set<string> = new Set()  // 防止 fallback 链重复绘制

          // 从路线结果中提取路径点
          const extractPath = (result: any): [number, number][] => {
            if (!result?.routes?.length) return []
            const route = result.routes[0]
            const path: [number, number][] = []
            for (const leg of route.legs) {
              for (const step of leg.steps) {
                for (const p of step.path) {
                  path.push([p.lng ?? p[0], p.lat ?? p[1]])
                }
              }
            }
            return path
          }

          // Douglas-Peucker 路径简化：保留主干道路，去除冗余点
          const simplifyPath = (pts: [number, number][], tolerance: number = 0.0005): [number, number][] => {
            if (pts.length <= 2) return pts
            // 找到距离起点-终点连线最远的点
            let maxDist = 0, maxIdx = 0
            const [sx, sy] = pts[0], [ex, ey] = pts[pts.length - 1]
            const dx = ex - sx, dy = ey - sy
            const lenSq = dx * dx + dy * dy
            for (let i = 1; i < pts.length - 1; i++) {
              const t = Math.max(0, Math.min(1, ((pts[i][0] - sx) * dx + (pts[i][1] - sy) * dy) / lenSq))
              const px = sx + t * dx, py = sy + t * dy
              const dist = Math.sqrt((pts[i][0] - px) ** 2 + (pts[i][1] - py) ** 2)
              if (dist > maxDist) { maxDist = dist; maxIdx = i }
            }
            if (maxDist > tolerance) {
              const left = simplifyPath(pts.slice(0, maxIdx + 1), tolerance)
              const right = simplifyPath(pts.slice(maxIdx), tolerance)
              return left.slice(0, -1).concat(right)
            }
            return [pts[0], pts[pts.length - 1]]
          }

          // 绘制路线：驾车 → 步行 → 直线兜底
          const drawRoute = (
            origin: any, destination: any, segKey: string,
            color: string, p0: [number, number], p1: [number, number],
            onDone?: () => void, isMealSeg?: boolean, isArrivalSeg?: boolean, isReturnSeg?: boolean, isInterDaySeg?: boolean,
          ) => {
            // 在路线中点添加交通方式+距离标签
            const addModeLabel = (path: [number, number][], mode: string) => {
              if (!map || path.length < 2) return
              const midIdx = Math.floor(path.length / 2)
              const mid = path[midIdx]
              let totalDist = 0
              for (let i = 1; i < path.length; i++) {
                const dx = (path[i][0] - path[i-1][0]) * 111
                const dy = (path[i][1] - path[i-1][1]) * 111
                totalDist += Math.sqrt(dx*dx + dy*dy)
              }
              const distText = totalDist < 1 ? `${Math.round(totalDist * 1000)}m` : `${totalDist.toFixed(1)}km`
              const speedMap: Record<string, number> = { driving: 40, walking: 5, direct: 30 }
              const estMin = Math.round(totalDist / (speedMap[mode] || 30) * 60)
              const timeText = estMin < 1 ? '<1分钟' : estMin > 60 ? `${Math.round(estMin/60)}小时${estMin%60}分` : `${estMin}分钟`
              let icon = '📍'
              let labelBg = 'white'
              let labelColor = '#555'
              if (isInterDaySeg) {
                icon = '🔄'
                labelBg = '#f1f5f9'
                labelColor = '#64748b'
              } else if (isArrivalSeg) {
                icon = ti?.recommended_mode?.includes('飞机') ? '✈️' : '🚄'
                labelBg = '#eff6ff'
                labelColor = '#3b82f6'
              } else if (isReturnSeg) {
                icon = '🏨'
                labelBg = '#fffbeb'
                labelColor = '#f59e0b'
              } else {
                const modeIcons: Record<string, string> = { driving: '🚗', walking: '🚶', direct: '📍' }
                icon = modeIcons[mode] || '📍'
              }
              const modeMarker = new AMap.Marker({
                position: new AMap.LngLat(mid[0], mid[1]),
                content: `<div style="background:${labelBg};padding:3px 8px;border-radius:10px;font-size:9px;color:${labelColor};white-space:nowrap;box-shadow:0 1px 6px rgba(0,0,0,0.12);border:1px solid rgba(0,0,0,0.06);font-family:var(--font-body);font-weight:500;pointer-events:none;display:flex;align-items:center;gap:4px;">
                  <span>${icon}</span>
                  <span style="color:#333;font-weight:600;">${distText}</span>
                  <span style="color:#999;">·</span>
                  <span style="color:#666;">${timeText}</span>
                </div>`,
                offset: new AMap.Pixel(-30, -8),
                zIndex: 80,
              })
              map.add(modeMarker)
            }

            const addPolyline = (path: [number, number][], opacity: number, mode?: string) => {
              if (!map || path.length === 0) return
              const displayPath = path
              segmentCache.set(segKey, displayPath)
              drawnSegments.add(segKey)
              // 确定颜色和线型
              const lineColor = isInterDaySeg ? '#94a3b8' : isArrivalSeg ? '#3b82f6' : color
              const glowWeight = isMealSeg ? 6 : isInterDaySeg ? 12 : 18
              const mainWeight = isMealSeg ? 3 : isInterDaySeg ? 4 : isArrivalSeg || isReturnSeg ? 5 : 6
              const mainOpacity = isMealSeg ? opacity * 0.7 : isInterDaySeg ? 0.6 : Math.min(opacity, 0.95)
              // 底层发光效果（让路线更醒目）
              map.add(new AMap.Polyline({
                path: displayPath, strokeColor: lineColor, strokeWeight: glowWeight,
                strokeOpacity: isMealSeg ? 0.12 : 0.25, lineJoin: 'round', lineCap: 'round',
              }))
              // 主路线 — 到达/返回/跨天用虚线，其余按交通方式
              let lineStyle: Record<string, any>
              if (isInterDaySeg) {
                lineStyle = { strokeStyle: 'dashed', strokeDasharray: [6, 8], showDir: false }
              } else if (isArrivalSeg || isReturnSeg) {
                lineStyle = { strokeStyle: 'dashed', strokeDasharray: [10, 6], showDir: false }
              } else {
                lineStyle = {
                  driving: { showDir: false },
                  walking: { strokeStyle: 'dashed', strokeDasharray: [8, 6], showDir: false },
                  direct: { strokeStyle: 'solid', showDir: false },
                }[mode || 'driving'] || { showDir: false }
              }
              map.add(new AMap.Polyline({
                path: displayPath, strokeColor: lineColor, strokeWeight: mainWeight,
                strokeOpacity: mainOpacity, lineJoin: 'round', lineCap: 'round',
                ...lineStyle,
              }))
            }

            // 后端代理优先（可靠），JS API Driving 作为备用
            const tryBackendProxy = (fallbackMode: string = 'driving') => {
              // 防止 fallback 链重复绘制同一路段
              if (drawnSegments.has(segKey)) { onDone?.(); return }
              console.log(`[路线规划] 请求 ${segKey}: mode=${fallbackMode}`)
              const originStr = `${p0[0]},${p0[1]}`
              const destStr = `${p1[0]},${p1[1]}`
              const cityParam = encodeURIComponent(tripPlan.value.city || '')
              const controller = new AbortController()
              const timer = setTimeout(() => controller.abort(), 8000)
              fetch(`/api/trip/route?origin=${originStr}&destination=${destStr}&mode=${fallbackMode}&city=${cityParam}`, { signal: controller.signal })
                .then(r => {
                  clearTimeout(timer)
                  if (!r.ok) throw new Error(`HTTP ${r.status}`)
                  return r.json()
                })
                .then((data: any) => {
                  if (!map) { onDone?.(); return }
                  if (data.path && data.path.length > 0) {
                    const routePath: [number, number][] = data.path
                    const routeMode = data.mode || fallbackMode
                    console.log(`[路线规划] ✓ ${segKey} 绘制成功: ${routeMode}, ${routePath.length}点`)
                    addPolyline(routePath, 0.85, routeMode)
                    if (!isMealSeg) addModeLabel(routePath, routeMode)
                    onDone?.()
                  } else if (fallbackMode === 'driving') {
                    console.warn(`[路线规划] driving 空路径 (${segKey}) → 尝试 transit`)
                    tryBackendProxy('transit')
                  } else if (fallbackMode === 'transit') {
                    console.warn(`[路线规划] transit 空路径 (${segKey}) → 尝试 walking`)
                    tryBackendProxy('walking')
                  } else {
                    console.warn(`[路线规划] 所有模式失败 (${segKey})，不绘制路线`)
                    onDone?.()
                  }
                })
                .catch((err) => {
                  clearTimeout(timer)
                  console.warn(`[路线规划] 代理失败 (${segKey}, ${fallbackMode}):`, err?.message)
                  if (fallbackMode === 'driving') {
                    tryBackendProxy('transit')
                  } else if (fallbackMode === 'transit') {
                    tryBackendProxy('walking')
                  } else {
                    onDone?.()
                  }
                })
            }

            // 第一优先：后端代理（可靠，已验证可用）
            tryBackendProxy('driving')
          }

          // 路线 API 并发限制（最多同时 3 个请求，避免触发限流）
          const ROUTE_CONCURRENCY = 3
          let routeActive = 0
          const routeQueue: (() => void)[] = []
          const runRoute = (fn: () => void) => {
            if (routeActive < ROUTE_CONCURRENCY) {
              routeActive++
              fn()
            } else {
              routeQueue.push(fn)
            }
          }
          const routeDone = () => {
            routeActive--
            if (routeQueue.length > 0) {
              routeActive++
              routeQueue.shift()!()
            }
          }

          // 计算总路线段数，完成后自动缩放适配
          let totalSegments = 0
          let completedSegments = 0
          let routeGen = 0  // 路线绘制代次，geocoding 重绘时递增
          let routesReadyResolve: (() => void) | null = null
          let routesReady = new Promise<void>((r) => { routesReadyResolve = r })
          const recalcSegments = () => {
            totalSegments = 0
            dayPositions.forEach((positions) => {
              if (positions.length >= 2) totalSegments += positions.length - 1
            })
          }
          recalcSegments()
          console.log(`[路线规划] 共 ${totalSegments} 个路段待绘制`)
          const originalRouteDone = routeDone
          const routeDoneWithFitView = () => {
            completedSegments++
            originalRouteDone()
            if (completedSegments >= totalSegments) {
              routesReadyResolve?.()
              if (map) setTimeout(() => { if (map) map.setFitView(null, false, [60, 60, 60, 60]) }, 300)
            }
          }

          const drawAllRoutes = () => {
            dayPositions.forEach((positions, dayIdx) => {
              if (positions.length < 2) return
              const color = dayColors[dayIdx % dayColors.length]
              const dayPts = dayPoints.value[dayIdx] || []
              for (let i = 0; i < positions.length - 1; i++) {
                // 同坐标跳过（如返回酒店与出发酒店相同）
                if (positions[i][0] === positions[i + 1][0] && positions[i][1] === positions[i + 1][1]) {
                  routeDoneWithFitView()
                  continue
                }
                const fromType = dayPts[i]?.type || ''
                const toType = dayPts[i + 1]?.type || ''
                const isMealSeg = fromType === 'meal' || toType === 'meal'
                const isArrivalSeg = fromType === 'arrival'
                const isReturnSeg = toType === 'hotel' && i === positions.length - 2
                const origin = new AMap.LngLat(positions[i][0], positions[i][1])
                const destination = new AMap.LngLat(positions[i + 1][0], positions[i + 1][1])
                runRoute(() => drawRoute(origin, destination, `${dayIdx}-${i}`, color, positions[i], positions[i + 1], routeDoneWithFitView, isMealSeg, isArrivalSeg, isReturnSeg))
              }
            })
            // 跨天连接：Day N 最后一个点 → Day N+1 第一个点
            for (let d = 0; d < dayPositions.length - 1; d++) {
              const lastPos = dayPositions[d]
              const nextPos = dayPositions[d + 1]
              if (!lastPos?.length || !nextPos?.length) continue
              const from = lastPos[lastPos.length - 1]
              const to = nextPos[0]
              // 同坐标（同一酒店）跳过
              if (from[0] === to[0] && from[1] === to[1]) continue
              const origin = new AMap.LngLat(from[0], from[1])
              const destination = new AMap.LngLat(to[0], to[1])
              runRoute(() => drawRoute(origin, destination, `interday-${d}`, '#94a3b8', from, to, routeDoneWithFitView, false, false, false, true))
            }
          }
          drawAllRoutes()

          // 合并每天的分段路线（按顺序）— 动画启动时实时读取
          // 去重：相邻分段的首尾重叠点只保留一个，避免动画卡顿
          const getDayRoutes = () => {
            const routes: [number, number][][] = []
            dayPositions.forEach((positions, dayIdx) => {
              if (positions.length < 2) return
              const route: [number, number][] = []
              for (let i = 0; i < positions.length - 1; i++) {
                const seg = segmentCache.get(`${dayIdx}-${i}`)
                if (seg && seg.length > 0) {
                  // 跳过与上一段末尾重复的点
                  if (route.length > 0) {
                    const last = route[route.length - 1]
                    const start = seg[0]
                    if (last[0] === start[0] && last[1] === start[1]) {
                      route.push(...seg.slice(1))
                    } else {
                      route.push(...seg)
                    }
                  } else {
                    route.push(...seg)
                  }
                }
              }
              routes[dayIdx] = route
            })
            return routes
          }
      }
    } catch (apiError) {
      message.error('地图加载失败，请刷新页面重试')
    }
  } catch (e: any) {
    console.error('[地图初始化]', e)
    message.error(`地图初始化失败: ${e?.message || '未知错误'}`)
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

const locatePoint = (dayIndex: number, pointIndex: number) => {
  if (!map) return
  const pts = dayPoints.value[dayIndex]
  if (!pts || !pts[pointIndex]) return
  map.setZoomAndCenter(16, pts[pointIndex].pos, false, 300)
}

const resetMapView = () => {
  if (!map) return
  map.setFitView(null, false, [60, 60, 60, 60])
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
  Modal.confirm({
    title: '删除景点',
    content: '确定要删除这个景点吗？此操作不可撤销。',
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    onOk() {
      tripPlan.value.days[dayIndex].attractions.splice(attractionIndex, 1)
      nextTick(() => initMap())
    },
  })
}

const addAttraction = (dayIndex: number) => {
  // Use the last attraction's coords as default, or center of first day's attractions
  const existing = tripPlan.value.days[dayIndex].attractions
  const lastCoords = existing.length > 0 ? existing[existing.length - 1].location : null
  tripPlan.value.days[dayIndex].attractions.push({
    name: '新景点',
    address: '请输入地址',
    location: {
      longitude: lastCoords?.longitude || 116.397,
      latitude: lastCoords?.latitude || 39.909,
    },
    visit_duration: 60,
    description: '请输入景点描述',
    ticket_price: 0,
  })
  nextTick(() => initMap())
}

const exportPDF = async () => {
  const el = document.querySelector('.result-content') as HTMLElement
  if (!el) return
  message.loading({ content: '正在生成 PDF...', key: 'pdf', duration: 0 })
  try {
    const html2pdf = await loadHtml2Pdf()
    await html2pdf()
      .set({
        margin: [10, 10],
        filename: `${tripPlan.value.city || '旅行'}行程.pdf`,
        image: { type: 'jpeg', quality: 0.95 },
        html2canvas: { scale: 2, useCORS: true },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] },
      })
      .from(el)
      .save()
    message.success({ content: 'PDF 已下载', key: 'pdf' })
  } catch {
    message.error({ content: 'PDF 生成失败，请重试', key: 'pdf' })
  }
}

const checkFavorite = async () => {
  if (!tripPlan.value.id) return
  try {
    const favorites = await listFavorites()
    isFavorite.value = favorites.some(f => f.id === tripPlan.value.id)
  } catch {
    isFavorite.value = false
  }
}

const parseSuggestions = (text: string): string[] => {
  if (!text) return []
  // Split by newlines, numbered patterns (1. / 1、/ 1）， or bullet points
  const lines = text.split(/\n/)
  const items: string[] = []
  for (const line of lines) {
    const cleaned = line.replace(/^\d+[\.\、\)）]\s*/, '').replace(/^[-•·]\s*/, '').trim()
    if (cleaned) items.push(cleaned)
  }
  return items.length > 0 ? items : [text]
}

const toggleFavorite = async () => {
  if (!tripPlan.value.id) return
  try {
    if (isFavorite.value) {
      await removeFavorite(tripPlan.value.id)
      message.success('已取消收藏')
    } else {
      await addFavorite(tripPlan.value.id)
      message.success('已收藏')
    }
    isFavorite.value = !isFavorite.value
  } catch {
    message.error('操作失败，请重试')
  }
}

const shareTrip = () => {
  if (!tripPlan.value.share_token) return
  const url = `${window.location.origin}/share/${tripPlan.value.share_token}`
  navigator.clipboard.writeText(url).then(() => {
    message.success('分享链接已复制到剪贴板')
  }).catch(() => {
    message.info(`分享链接: ${url}`)
  })
}

const exportICS = () => {
  const lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//TripPlanner//CN', 'CALSCALE:GREGORIAN']
  for (const day of tripPlan.value.days) {
    const date = day.date.replace(/-/g, '')
    // iCalendar DTEND 是排他的，全天事件需要 +1 天
    const d = new Date(day.date)
    d.setDate(d.getDate() + 1)
    const endDate = d.toISOString().slice(0, 10).replace(/-/g, '')
    const attractions = day.attractions.map(a => a.name).join(', ')
    lines.push(
      'BEGIN:VEVENT',
      `DTSTART;VALUE=DATE:${date}`,
      `DTEND;VALUE=DATE:${endDate}`,
      `SUMMARY:${tripPlan.value.city}之旅 - Day ${(day.day_index || 0) + 1}`,
      `DESCRIPTION:${day.description}\\n景点: ${attractions}`,
      'END:VEVENT'
    )
  }
  lines.push('END:VCALENDAR')
  const blob = new Blob([lines.join('\r\n')], { type: 'text/calendar;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `${tripPlan.value.city}行程.ics`
  a.click()
  message.success('日历文件已下载')
}

const playTransportAnim = () => {
  // 重播：重置状态后重新调用播放
  if (animDone.value) {
    animDone.value = false
    animProgress.value = 0
    animPaused.value = false
    animSpeed.value = 1
    // 重置动画状态（不清除地图）
    const resetFn = (window as any).__resetTransportAnim
    if (resetFn) resetFn()
    // 直接调用播放
    nextTick(() => {
      const fn = (window as any).__playTransportAnim
      if (fn) {
        animPlaying.value = true
        fn()
      }
    })
    return
  }
  const fn = (window as any).__playTransportAnim
  if (fn) {
    animPlaying.value = true
    animPaused.value = false
    fn()
  }
}

const togglePause = () => {
  animPaused.value = !animPaused.value
}

const getSectionNumber = (section: string) => {
  const base = tripPlan.value?.budget ? 3 : 2
  const sectionMap = { days: base + 1, weather: base + 2 }
  return String(sectionMap[section as keyof typeof sectionMap] || base).padStart(2, '0')
}

onBeforeUnmount(() => {
  if (animFrameId) { cancelAnimationFrame(animFrameId); animFrameId = null }
  delete (window as any).__playTransportAnim
  delete (window as any).__resetTransportAnim
  delete (window as any).__animIconMarker
  contentMarkers = []
  // 清除浮动动画元素
  const mapContainer = document.getElementById('amap-container')
  if (mapContainer) {
    mapContainer.querySelectorAll('.amap-anim-elem').forEach(el => el.remove())
  }
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
  z-index: 99;
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

/* Plan Switcher */
.plan-switcher {
  display: flex;
  justify-content: center;
  gap: 10px;
  padding: 14px var(--space-xl);
  background: var(--color-cream);
  border-bottom: 1px solid var(--color-border-light);
  position: sticky;
  top: 56px;
  z-index: 50;
}

.switcher-btn {
  padding: 8px 20px;
  border-radius: 20px;
  border: 1.5px solid var(--color-border-light);
  background: white;
  color: var(--color-text-secondary);
  font-size: 13px;
  font-family: var(--font-display);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s ease;
  white-space: nowrap;
}

.switcher-btn:hover {
  border-color: var(--color-terracotta);
  color: var(--color-terracotta);
}

.switcher-btn.active {
  background: var(--color-terracotta);
  border-color: var(--color-terracotta);
  color: white;
  box-shadow: 0 2px 8px rgba(196, 101, 74, 0.25);
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

.suggestion-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.suggestion-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-sm);
  font-size: 0.9rem;
  line-height: 1.6;
  color: var(--color-charcoal);
}

.suggestion-index {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-terracotta);
  color: white;
  font-size: 0.7rem;
  font-weight: 700;
  border-radius: 50%;
  margin-top: 2px;
}

.suggestion-text {
  flex: 1;
}

/* Map */
.map-wrapper {
  position: relative;
  background: var(--color-paper);
  border-radius: var(--radius-lg);
  border: 1px solid rgba(232, 226, 218, 0.6);
  overflow: hidden;
  box-shadow: var(--shadow-card), 0 8px 32px rgba(0,0,0,0.06);
}

.anim-play-btn {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 20;
  padding: 10px 28px;
  border: none;
  border-radius: 24px;
  background: linear-gradient(135deg, #c67b5c, #a65d3f);
  color: white;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(198, 123, 92, 0.35);
  transition: all 0.3s cubic-bezier(0.22, 1, 0.36, 1);
  white-space: nowrap;
  font-family: var(--font-body);
  overflow: hidden;
}

.anim-play-btn:hover {
  transform: translateX(-50%) translateY(-2px);
  box-shadow: 0 6px 24px rgba(198, 123, 92, 0.45);
  background: linear-gradient(135deg, #d4856a, #b4684d);
}

.anim-play-btn:active {
  transform: translateX(-50%) translateY(0);
}

.anim-play-btn:disabled {
  cursor: not-allowed;
  opacity: 0.85;
}

.anim-play-btn--playing {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.35);
  animation: pulse-glow 1.5s ease-in-out infinite;
  font-size: 0.82rem;
  min-width: 200px;
  text-align: center;
}

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 4px 16px rgba(59, 130, 246, 0.35); }
  50% { box-shadow: 0 4px 24px rgba(59, 130, 246, 0.55); }
}

.anim-play-btn--done {
  background: linear-gradient(135deg, #2d6a4f, #1b4332);
  box-shadow: 0 4px 16px rgba(45, 106, 79, 0.35);
}

.anim-play-btn--done:hover {
  background: linear-gradient(135deg, #3a7d5e, #234d3a);
}

.anim-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: rgba(255,255,255,0.2);
  border-radius: 0 0 24px 24px;
  overflow: hidden;
}

.anim-progress-bar {
  height: 100%;
  background: white;
  border-radius: 0 0 24px 24px;
  transition: width 0.3s ease;
}

/* 动画控制栏 */
.anim-controls {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
}
.anim-ctrl-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1.5px solid var(--color-primary);
  background: white;
  color: var(--color-primary);
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}
.anim-ctrl-btn:hover { background: var(--color-primary); color: white; }
.anim-speed-group {
  display: flex;
  gap: 3px;
  background: var(--color-sand-light);
  border-radius: 12px;
  padding: 2px;
}
.anim-speed-btn {
  padding: 2px 8px;
  border: none;
  border-radius: 10px;
  background: transparent;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}
.anim-speed-btn.active {
  background: var(--color-primary);
  color: white;
}

/* 图例 */
.map-legend {
  position: absolute;
  bottom: 10px;
  right: 10px;
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(6px);
  border-radius: 8px;
  padding: 6px 10px;
  display: flex;
  gap: 10px;
  font-size: 10px;
  color: var(--color-text-secondary);
  box-shadow: 0 1px 6px rgba(0,0,0,0.1);
  z-index: 90;
  font-family: var(--font-body);
}
.map-legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}
.legend-line {
  display: inline-block;
  width: 16px;
  height: 2px;
  border-radius: 1px;
}
.legend-solid { background: #3b82f6; }
.legend-dashed { background: repeating-linear-gradient(90deg, #10b981 0 4px, transparent 4px 8px); }
.legend-dotted { background: repeating-linear-gradient(90deg, #f59e0b 0 2px, transparent 2px 5px); }
.legend-interday { background: repeating-linear-gradient(90deg, #94a3b8 0 3px, transparent 3px 7px); }
.legend-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  border: 1.5px solid white;
  box-shadow: 0 0 2px rgba(0,0,0,0.2);
}

.map-container {
  height: min(600px, 70vh);
  min-height: 400px;
  position: relative;
  background: linear-gradient(135deg, var(--color-sand-light) 0%, var(--color-cream) 100%);
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
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

/* 景点导航面板 */
.map-nav-panel {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 15;
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(12px);
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  border: 1px solid rgba(232,226,218,0.5);
  max-width: 160px;
  transition: all 0.2s ease;
}

.map-nav-panel--collapsed {
  max-width: 100px;
}

.map-nav-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 10px;
  cursor: pointer;
  user-select: none;
  border-bottom: 1px solid rgba(232,226,218,0.4);
  transition: background 0.15s;
}

.map-nav-header:hover {
  background: rgba(196,101,74,0.05);
}

.map-nav-title {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-charcoal);
  font-family: var(--font-body);
  white-space: nowrap;
}

.map-nav-toggle {
  font-size: 10px;
  color: var(--color-warm-gray);
}

.map-nav-body {
  padding: 4px 6px;
  max-height: 280px;
  overflow-y: auto;
}

.map-nav-body::-webkit-scrollbar {
  width: 3px;
}

.map-nav-body::-webkit-scrollbar-thumb {
  background: rgba(0,0,0,0.15);
  border-radius: 3px;
}

.map-nav-day {
  margin-bottom: 2px;
}

.map-nav-day-label {
  font-size: 9px;
  font-weight: 700;
  padding: 2px 4px;
  font-family: var(--font-body);
  letter-spacing: 0.3px;
}

.map-nav-item {
  display: flex;
  align-items: flex-start;
  gap: 5px;
  width: 100%;
  padding: 3px 4px;
  border: none;
  background: transparent;
  border-radius: 5px;
  cursor: pointer;
  font-size: 10px;
  color: var(--color-text-secondary);
  font-family: var(--font-body);
  text-align: left;
  transition: background 0.15s;
}

.map-nav-item:hover {
  background: rgba(196,101,74,0.08);
  color: var(--color-charcoal);
}

.map-nav-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}

.map-nav-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.map-nav-coord {
  font-size: 8px;
  color: #999;
  font-family: 'SF Mono', 'Menlo', monospace;
  letter-spacing: 0.2px;
  line-height: 1.2;
}
.map-nav-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}
.map-nav-tag {
  font-size: 8px;
  color: var(--color-primary);
  background: var(--color-primary-light);
  padding: 1px 5px;
  border-radius: 4px;
  font-weight: 600;
}

.map-nav-dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  color: white;
  font-weight: 700;
}

.map-nav-icon {
  font-size: 11px;
  flex-shrink: 0;
  line-height: 1;
}

/* 重置视图按钮 */
.map-reset-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 15;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid rgba(232,226,218,0.5);
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(12px);
  color: var(--color-charcoal);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 10px rgba(0,0,0,0.08);
  transition: all 0.2s;
}

.map-reset-btn:hover {
  background: white;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  transform: scale(1.05);
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

/* CPS Links */
.cps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 10px;
}

.cps-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--color-paper);
  border: 1px solid rgba(232, 226, 218, 0.5);
  border-radius: var(--radius-md);
  text-decoration: none;
  color: var(--color-charcoal);
  transition: all var(--transition-fast);
}

.cps-card:hover {
  border-color: var(--color-terracotta);
  box-shadow: 0 2px 12px rgba(196, 101, 74, 0.1);
}

.cps-name {
  font-weight: 500;
  font-size: 0.9rem;
}

.cps-arrow {
  color: var(--color-terracotta);
  font-weight: 600;
}
</style>
