<template>
  <div class="home">
    <LoadingOverlay
      :visible="loading"
      :progress="loadingProgress"
      :currentStep="currentStep"
    />

    <!-- Hero Section -->
    <header class="hero">
      <div class="hero-bg">
        <div class="hero-grain"></div>
        <div class="hero-gradient"></div>
        <!-- Decorative floating shapes -->
        <div class="hero-shapes">
          <div class="shape shape-1"></div>
          <div class="shape shape-2"></div>
          <div class="shape shape-3"></div>
          <div class="shape shape-4"></div>
        </div>
      </div>
      <div class="hero-content">
        <div class="hero-badge">
          <span class="badge-dot"></span>
          AI 驱动
        </div>
        <h1 class="hero-title">
          <span class="hero-title-line">规划你的</span>
          <span class="hero-title-accent">下一段旅程</span>
        </h1>
        <p class="hero-subtitle">
          四个智能代理协同工作，为你搜索景点、查询天气、推荐住宿，生成专属行程
        </p>
        <div class="hero-agents">
          <div class="agent-tag">🔍 景点专家</div>
          <div class="agent-tag">🌤️ 天气专家</div>
          <div class="agent-tag">🏨 住宿专家</div>
          <div class="agent-tag">📋 规划专家</div>
        </div>
      </div>
      <div class="hero-scroll-hint">
        <span>向下滚动开始</span>
        <div class="scroll-line"></div>
      </div>
    </header>

    <!-- Planner Section -->
    <section class="planner-section">
      <div class="planner-container">
        <div class="section-label">
          <span class="label-line"></span>
          <span>行程规划</span>
          <span class="label-line"></span>
        </div>

        <form class="planner-form" @submit.prevent="handleSubmit">
          <!-- Row 1: Departure + City + Days -->
          <div class="form-row form-row--triple">
            <div class="form-group">
              <label class="form-label">
                出发城市
                <a-tooltip title="填写后系统将规划最佳交通路线并估算交通费用">
                  <span class="label-hint">?</span>
                </a-tooltip>
              </label>
              <a-auto-complete
                v-model:value="formData.departure_city"
                :options="departureOptions"
                placeholder="你从哪出发？"
                size="large"
                style="width: 100%"
                :filter-option="filterDeparture"
              />
              <span v-if="formData.departure_city && formData.departure_city === formData.city" class="field-hint">本地出发，无需城际交通</span>
            </div>
            <div class="form-group form-group--city">
              <label class="form-label">目的地</label>
              <div class="input-wrapper input-wrapper--large">
                <span class="input-icon">✦</span>
                <input
                  v-model="formData.city"
                  type="text"
                  placeholder="北京、成都、杭州..."
                  class="input-field input-field--large"
                  required
                />
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">旅行天数</label>
              <div class="days-display">
                <span class="days-number">{{ formData.days }}</span>
                <span class="days-unit">天</span>
                <span v-if="startDate && endDate" class="days-hint">自动计算</span>
              </div>
            </div>
          </div>

          <!-- Row 2: Dates -->
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">出发日期</label>
              <a-date-picker
                v-model:value="startDate"
                style="width: 100%"
                size="large"
                format="YYYY-MM-DD"
                placeholder="选择出发日"
                :disabled-date="disabledPastDate"
                @change="onStartDateChange"
              />
            </div>
            <div class="form-group">
              <label class="form-label">返程日期</label>
              <a-date-picker
                v-model:value="endDate"
                style="width: 100%"
                size="large"
                format="YYYY-MM-DD"
                placeholder="选择返程日"
                :disabled-date="disabledPastDate"
                @change="onEndDateChange"
              />
            </div>
          </div>

          <!-- Row 2.5: Travelers -->
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">出行人数</label>
              <a-input-number
                v-model:value="formData.travelers"
                :min="1"
                :max="20"
                size="large"
                style="width: 100%"
                placeholder="几人出行"
              />
            </div>
          </div>

          <!-- Row 3: Preferences -->
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">旅行偏好 <span class="label-hint">可多选</span></label>
              <div class="option-grid">
                <button
                  v-for="pref in preferenceOptions"
                  :key="pref.value"
                  type="button"
                  :class="['option-chip', { active: formData.preferences.includes(pref.value) }]"
                  @click="togglePreference(pref.value)"
                >
                  <span class="option-emoji">{{ pref.emoji }}</span>
                  <span class="option-text">{{ pref.label }}</span>
                </button>
              </div>
            </div>
          </div>

          <!-- Row 3.5: Extra Info -->
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">补充说明 <span class="label-hint">选填</span></label>
              <a-input
                v-model:value="formData.extra_info"
                size="large"
                placeholder="例如：带6岁小孩、膝盖不好少走路、对佛教文化感兴趣"
                :maxlength="200"
                allowClear
              />
            </div>
          </div>

          <!-- Row 4: Budget + Transport + Accommodation -->
          <div class="form-row form-row--triple">
            <div class="form-group">
              <label class="form-label">预算范围</label>
              <a-select v-model:value="formData.budget" size="large" placeholder="选择预算">
                <a-select-option value="经济">经济 · 500元/天以下</a-select-option>
                <a-select-option value="中等">中等 · 500-1500元/天</a-select-option>
                <a-select-option value="舒适">舒适 · 1500-3000元/天</a-select-option>
                <a-select-option value="豪华">豪华 · 3000元/天以上</a-select-option>
              </a-select>
            </div>
            <div class="form-group">
              <label class="form-label">交通方式</label>
              <a-select v-model:value="formData.transportation" size="large" placeholder="选择交通">
                <a-select-option value="公共交通">公共交通</a-select-option>
                <a-select-option value="出租车/网约车">出租车/网约车</a-select-option>
                <a-select-option value="租车自驾">租车自驾</a-select-option>
                <a-select-option value="步行">步行</a-select-option>
              </a-select>
            </div>
            <div class="form-group">
              <label class="form-label">住宿类型</label>
              <a-select v-model:value="formData.accommodation" size="large" placeholder="选择住宿">
                <a-select-option value="经济型酒店">经济型酒店</a-select-option>
                <a-select-option value="三星级酒店">三星级酒店</a-select-option>
                <a-select-option value="四星级酒店">四星级酒店</a-select-option>
                <a-select-option value="五星级酒店">五星级酒店</a-select-option>
                <a-select-option value="民宿">民宿</a-select-option>
                <a-select-option value="青年旅社">青年旅社</a-select-option>
              </a-select>
            </div>
          </div>

          <!-- Submit -->
          <div class="form-submit">
            <button
              type="submit"
              class="submit-btn"
              :class="{ 'submit-btn--loading': loading }"
              :disabled="loading"
            >
              <span v-if="!loading" class="submit-btn-text">
                <span>开始规划</span>
                <span class="submit-arrow">→</span>
              </span>
              <span v-else class="submit-btn-loading">
                <span class="loading-dots">
                  <span></span><span></span><span></span>
                </span>
                <span>{{ loadingStatus }}</span>
              </span>
            </button>
          </div>

          <!-- Progress -->
          <transition name="page">
            <div v-if="loading" class="progress-panel">
              <div class="progress-bar-track">
                <div class="progress-bar-fill" :style="{ width: loadingProgress + '%' }"></div>
              </div>
              <div class="progress-steps">
                <div
                  v-for="(step, i) in progressSteps"
                  :key="i"
                  :class="['progress-step', { active: i <= currentStep, current: i === currentStep }]"
                >
                  <span class="step-dot"></span>
                  <span class="step-text">{{ step }}</span>
                </div>
              </div>
            </div>
          </transition>
        </form>
      </div>
    </section>

    <!-- Features Section -->
    <section class="features-section">
      <div class="features-container stagger-enter">
        <div class="feature-card">
          <div class="feature-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
            </svg>
          </div>
          <h3 class="feature-title">智能搜索</h3>
          <p class="feature-desc">AI 自动搜索景点、天气、酒店信息，无需手动查找</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
          </div>
          <h3 class="feature-title">个性化行程</h3>
          <p class="feature-desc">根据偏好定制每日行程，景点游览时间精确到分钟</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
            </svg>
          </div>
          <h3 class="feature-title">预算透明</h3>
          <p class="feature-desc">清晰的费用估算，景点门票、餐饮、住宿一目了然</p>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="site-footer">
      <p>Voyager — AI 多智能体旅行规划</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { generateVariants, ApiError } from '@/services/api'
import type { TripPlanRequest } from '@/types'
import dayjs, { type Dayjs } from 'dayjs'
import LoadingOverlay from '@/components/LoadingOverlay.vue'

const router = useRouter()

const loading = ref(false)
const loadingProgress = ref(0)
const loadingStatus = ref('')
const currentStep = ref(-1)

let abortController: AbortController | null = null

const startDate = ref<Dayjs | null>(null)
const endDate = ref<Dayjs | null>(null)

onBeforeUnmount(() => {
  abortController?.abort()
})

const formData = ref<TripPlanRequest>({
  city: '',
  departure_city: '',
  start_date: '',
  end_date: '',
  days: 3,
  travelers: 1,
  preferences: ['历史文化'],
  extra_info: '',
  budget: '中等',
  transportation: '公共交通',
  accommodation: '经济型酒店',
})

const popularCities = ['北京', '上海', '广州', '深圳', '成都', '杭州', '重庆', '武汉', '西安', '南京', '长沙', '郑州', '东莞', '佛山', '合肥', '青岛', '天津', '苏州', '宁波', '厦门', '福州', '昆明', '沈阳', '大连', '济南']
const departureOptions = popularCities.map(c => ({ value: c }))
const filterDeparture = (input: string, option: any) => option.value.includes(input)

const preferenceOptions = [
  { value: '历史文化', label: '历史文化', emoji: '🏛️' },
  { value: '自然风光', label: '自然风光', emoji: '🏔️' },
  { value: '美食之旅', label: '美食之旅', emoji: '🍜' },
  { value: '休闲度假', label: '休闲度假', emoji: '🏖️' },
  { value: '亲子游', label: '亲子游', emoji: '👨‍👩‍👧' },
  { value: '购物娱乐', label: '购物娱乐', emoji: '🛍️' },
]

const togglePreference = (value: string) => {
  const idx = formData.value.preferences.indexOf(value)
  if (idx >= 0) {
    if (formData.value.preferences.length > 1) {
      formData.value.preferences.splice(idx, 1)
    }
  } else {
    formData.value.preferences.push(value)
  }
}

const progressSteps = [
  '分析交通路线',
  '景点专家搜索中',
  '天气专家查询中',
  '住宿专家推荐中',
  '规划专家设计三方案',
  '整理专家汇总中',
]

const onStartDateChange = (date: Dayjs | null) => {
  if (date) {
    formData.value.start_date = date.format('YYYY-MM-DD')
    if (endDate.value && date.isAfter(endDate.value)) {
      endDate.value = date
      formData.value.end_date = date.format('YYYY-MM-DD')
    }
    updateDays()
  }
}

const onEndDateChange = (date: Dayjs | null) => {
  if (date) {
    // 如果结束日期早于开始日期，自动修正
    if (startDate.value && date.isBefore(startDate.value)) {
      endDate.value = startDate.value
      formData.value.end_date = startDate.value.format('YYYY-MM-DD')
    } else {
      formData.value.end_date = date.format('YYYY-MM-DD')
    }
    updateDays()
  }
}

const updateDays = () => {
  if (startDate.value && endDate.value) {
    const days = endDate.value.diff(startDate.value, 'day') + 1
    formData.value.days = Math.max(1, days)
  }
}

const disabledPastDate = (current: Dayjs) => {
  return current && current.isBefore(dayjs().startOf('day'))
}

const handleSubmit = async () => {
  if (!formData.value.city.trim()) {
    message.error('请输入目的地城市')
    return
  }
  if (!formData.value.start_date || !formData.value.end_date) {
    message.error('请选择日期')
    return
  }

  abortController = new AbortController()
  loading.value = true
  loadingProgress.value = 0
  currentStep.value = 0
  loadingStatus.value = '准备中...'

  // 渐进式进度条：先快后慢，真实反映后端处理节奏
  const progressTimer = setInterval(() => {
    if (currentStep.value <= 2) {
      // 信息收集阶段：快速推进到 40%
      loadingProgress.value = Math.min(loadingProgress.value + 4, 40)
    } else if (currentStep.value === 3) {
      // LLM 生成阶段（最慢）：缓慢爬升，120秒内从 40% → 95%
      loadingProgress.value = Math.min(loadingProgress.value + 0.4, 95)
    } else {
      loadingProgress.value = Math.min(loadingProgress.value + 8, 100)
    }
  }, 500)

  try {
    // 步骤 0-2：信息收集（真实 MCP/REST 调用在后台并行进行）
    currentStep.value = 0
    loadingStatus.value = '景点专家搜索中...'
    await new Promise(r => setTimeout(r, 1500))

    currentStep.value = 1
    loadingStatus.value = '天气专家查询中...'
    await new Promise(r => setTimeout(r, 1500))

    currentStep.value = 2
    loadingStatus.value = '住宿专家推荐中...'
    await new Promise(r => setTimeout(r, 1000))

    // 步骤 3：LLM 生成三个方案（真实耗时 50-120秒）
    currentStep.value = 3
    loadingStatus.value = '规划专家设计三个方案...'

    // 实际请求
    const response = await generateVariants(formData.value, abortController.signal)
    clearInterval(progressTimer)

    const validVariants = response.variants.filter((v: any) => v.plan)
    if (validVariants.length === 0) {
      message.error('所有方案生成失败，请稍后重试')
      return
    }

    currentStep.value = 4
    loadingProgress.value = 95
    loadingStatus.value = '整理专家汇总中...'
    await new Promise(r => setTimeout(r, 500))

    loadingProgress.value = 100
    loadingStatus.value = '完成'

    sessionStorage.setItem('tripVariants', JSON.stringify(response.variants))
    sessionStorage.removeItem('tripPlan')
    setTimeout(() => router.push({ name: 'compare' }), 400)
  } catch (error: unknown) {
    clearInterval(progressTimer)
    if (error instanceof ApiError) {
      message.error(`${error.message}${error.solution ? '，' + error.solution : ''}`, 5)
    } else if (error instanceof Error && error.name === 'AbortError') {
      // user navigated away
    } else {
      message.error('生成方案失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ============================================
   Hero
   ============================================ */
.hero {
  position: relative;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  padding: var(--space-xl);
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.hero-gradient {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 80% 60% at 20% 80%, rgba(196, 101, 74, 0.12) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 80% 20%, rgba(27, 67, 50, 0.08) 0%, transparent 50%),
    linear-gradient(175deg, var(--color-cream) 0%, var(--color-sand-light) 40%, var(--color-sand) 100%);
}

.hero-grain {
  position: absolute;
  inset: 0;
  opacity: 0.03;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.7' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  background-size: 256px;
}

.hero-content {
  position: relative;
  z-index: 1;
  max-width: 700px;
  animation: fadeInUp 800ms var(--ease-out-expo) forwards;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 18px;
  background: var(--color-forest);
  color: white;
  font-family: var(--font-body);
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  border-radius: 100px;
  margin-bottom: var(--space-lg);
  animation: fadeInUp 800ms var(--ease-out-expo) 200ms forwards;
  opacity: 0;
}

.badge-dot {
  width: 6px;
  height: 6px;
  background: var(--color-terracotta);
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

.hero-agents {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
  margin-top: var(--space-xl);
  animation: fadeInUp 800ms var(--ease-out-expo) 600ms forwards;
  opacity: 0;
}

.agent-tag {
  padding: 6px 14px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(232, 226, 218, 0.6);
  border-radius: 100px;
  font-family: var(--font-body);
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-charcoal);
  transition: all var(--transition-fast);
}

.agent-tag:hover {
  background: white;
  transform: translateY(-2px);
  box-shadow: var(--shadow-card);
}

/* Decorative floating shapes */
.hero-shapes {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.shape {
  position: absolute;
  border-radius: 50%;
  opacity: 0.15;
}

.shape-1 {
  width: 300px;
  height: 300px;
  background: var(--color-terracotta);
  top: -100px;
  right: -50px;
  animation: float 8s ease-in-out infinite;
}

.shape-2 {
  width: 200px;
  height: 200px;
  background: var(--color-forest);
  bottom: 20%;
  left: -60px;
  animation: float 6s ease-in-out infinite 1s;
}

.shape-3 {
  width: 150px;
  height: 150px;
  background: var(--color-sunset);
  top: 30%;
  right: 10%;
  animation: float 7s ease-in-out infinite 2s;
}

.shape-4 {
  width: 100px;
  height: 100px;
  background: var(--color-sage);
  bottom: 10%;
  right: 20%;
  animation: float 5s ease-in-out infinite 0.5s;
}

.hero-title {
  font-family: var(--font-display);
  font-size: clamp(2.8rem, 7vw, 5rem);
  font-weight: 600;
  line-height: 1.1;
  color: var(--color-charcoal);
  margin-bottom: var(--space-lg);
}

.hero-title-line {
  display: block;
}

.hero-title-accent {
  display: block;
  color: var(--color-terracotta);
  font-style: italic;
}

.hero-subtitle {
  font-size: 1.15rem;
  color: var(--color-warm-gray);
  line-height: 1.7;
  max-width: 520px;
  margin: 0 auto;
}

.hero-scroll-hint {
  position: absolute;
  bottom: var(--space-xl);
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
  animation: fadeIn 1s ease 1s forwards;
  opacity: 0;
  z-index: 1;
}

.hero-scroll-hint span {
  font-size: 0.75rem;
  color: var(--color-warm-gray);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.scroll-line {
  width: 1px;
  height: 40px;
  background: var(--color-terracotta);
  animation: float 2s ease-in-out infinite;
}

/* ============================================
   Planner Section
   ============================================ */
.planner-section {
  padding: var(--space-3xl) var(--space-xl);
  background: var(--color-cream);
}

.planner-container {
  max-width: 900px;
  margin: 0 auto;
}

.section-label {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
  margin-bottom: var(--space-2xl);
  font-family: var(--font-display);
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-warm-gray);
  letter-spacing: 0.15em;
  text-transform: uppercase;
}

.label-line {
  width: 40px;
  height: 1px;
  background: var(--color-light-gray);
}

/* Form */
.planner-form {
  background: var(--color-paper);
  border-radius: var(--radius-xl);
  padding: var(--space-xl);
  box-shadow: var(--shadow-elevated);
  border: 1px solid rgba(232, 226, 218, 0.4);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-lg);
  margin-bottom: var(--space-lg);
}

.form-row--triple {
  grid-template-columns: 1fr 1fr 1fr;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.form-label {
  font-family: var(--font-body);
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-charcoal);
  letter-spacing: 0.03em;
}

.label-hint {
  font-weight: 400;
  color: var(--color-text-secondary);
  font-size: 0.75rem;
}

.field-hint {
  font-size: 0.7rem;
  color: var(--color-text-secondary);
  margin-top: 2px;
}

/* City input */
.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-wrapper--large .input-field--large {
  font-size: 1.25rem;
  font-family: var(--font-display);
  font-weight: 500;
  padding-left: 40px;
  height: 56px;
}

.input-icon {
  position: absolute;
  left: 14px;
  color: var(--color-terracotta);
  font-size: 1.1rem;
  pointer-events: none;
}

.input-field {
  width: 100%;
  border: 1.5px solid var(--color-light-gray);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  font-family: var(--font-body);
  font-size: 0.95rem;
  color: var(--color-charcoal);
  background: var(--color-paper);
  transition: all var(--transition-fast);
  outline: none;
}

.input-field:focus {
  border-color: var(--color-terracotta);
  box-shadow: 0 0 0 3px rgba(196, 101, 74, 0.08);
}

.input-field::placeholder {
  color: var(--color-light-gray);
}

/* Days display */
.days-display {
  display: flex;
  align-items: baseline;
  gap: 6px;
  height: 56px;
  padding: 0 16px;
  background: var(--color-paper);
  border: 1.5px solid var(--color-light-gray);
  border-radius: var(--radius-md);
}

.days-number {
  font-family: var(--font-display);
  font-size: 1.8rem;
  font-weight: 600;
  color: var(--color-terracotta);
  line-height: 1;
}

.days-unit {
  font-family: var(--font-body);
  font-size: 0.9rem;
  color: var(--color-charcoal);
  font-weight: 500;
}

.days-hint {
  font-size: 0.7rem;
  color: var(--color-warm-gray);
  margin-left: auto;
  font-style: italic;
}

/* Option chips */
.option-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.option-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border: 1.5px solid var(--color-light-gray);
  border-radius: var(--radius-md);
  background: var(--color-paper);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.option-chip:hover {
  border-color: var(--color-terracotta-light);
  background: var(--color-sand-light);
}

.option-chip.active {
  border-color: var(--color-terracotta);
  background: rgba(196, 101, 74, 0.06);
}

.option-emoji {
  font-size: 1.1rem;
}

.option-text {
  font-family: var(--font-body);
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--color-charcoal);
}

/* Submit */
.form-submit {
  margin-top: var(--space-xl);
  position: relative;
  display: flex;
  gap: 12px;
}

.submit-btn {
  flex: 1;
  height: 56px;
  border: none;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, var(--color-terracotta) 0%, var(--color-terracotta-dark) 100%);
  color: white;
  font-family: var(--font-display);
  font-size: 1.2rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
}

.submit-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, var(--color-sunset) 0%, var(--color-terracotta) 100%);
  opacity: 0;
  transition: opacity var(--transition-normal);
}

.submit-btn:hover:not(:disabled)::before {
  opacity: 1;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(196, 101, 74, 0.35);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn--loading {
  background: var(--color-charcoal);
  cursor: wait;
}

.submit-btn-text {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
}

.submit-arrow {
  transition: transform var(--transition-fast);
}

.submit-btn:hover .submit-arrow {
  transform: translateX(4px);
}

.submit-btn-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
  font-family: var(--font-body);
  font-size: 0.9rem;
}

.loading-dots {
  display: flex;
  gap: 4px;
}

.loading-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-terracotta);
  animation: float 1.2s ease-in-out infinite;
}

.loading-dots span:nth-child(2) { animation-delay: 0.15s; }
.loading-dots span:nth-child(3) { animation-delay: 0.3s; }

/* Progress panel */
.progress-panel {
  margin-top: var(--space-lg);
  padding: var(--space-lg);
  background: var(--color-sand-light);
  border-radius: var(--radius-lg);
  border: 1px solid rgba(232, 226, 218, 0.6);
}

.progress-bar-track {
  width: 100%;
  height: 4px;
  background: var(--color-light-gray);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: var(--space-md);
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-terracotta) 0%, var(--color-sunset) 100%);
  border-radius: 2px;
  transition: width 400ms var(--ease-out-expo);
}

.progress-steps {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.progress-step {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  color: var(--color-warm-gray);
  opacity: 0.4;
  transition: all var(--transition-fast);
}

.progress-step.active {
  opacity: 0.7;
  color: var(--color-charcoal);
}

.progress-step.current {
  opacity: 1;
  color: var(--color-terracotta);
  font-weight: 600;
}

.step-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-light-gray);
  flex-shrink: 0;
  transition: all var(--transition-fast);
}

.progress-step.active .step-dot {
  background: var(--color-terracotta-light);
}

.progress-step.current .step-dot {
  background: var(--color-terracotta);
  box-shadow: 0 0 0 3px rgba(196, 101, 74, 0.15);
}

/* ============================================
   Features
   ============================================ */
.features-section {
  padding: var(--space-3xl) var(--space-xl);
  background: linear-gradient(180deg, var(--color-cream) 0%, var(--color-sand-light) 100%);
  border-top: 1px solid var(--color-light-gray);
}

.features-container {
  max-width: 1000px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-xl);
}

.feature-card {
  text-align: center;
  padding: var(--space-xl);
  border-radius: var(--radius-lg);
  background: var(--color-paper);
  border: 1px solid rgba(232, 226, 218, 0.6);
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--color-terracotta), var(--color-sunset));
  transform: scaleX(0);
  transform-origin: left;
  transition: transform var(--transition-normal);
}

.feature-card:hover::before {
  transform: scaleX(1);
}

.feature-card:hover {
  transform: translateY(-8px);
  box-shadow: var(--shadow-elevated);
  border-color: var(--color-terracotta-light);
}

.feature-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, var(--color-sand) 0%, var(--color-sand-light) 100%);
  color: var(--color-terracotta);
  margin-bottom: var(--space-md);
  transition: all var(--transition-normal);
}

.feature-card:hover .feature-icon {
  background: linear-gradient(135deg, var(--color-terracotta) 0%, var(--color-terracotta-dark) 100%);
  color: white;
  transform: scale(1.1) rotate(5deg);
}

.feature-title {
  font-family: var(--font-display);
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--color-charcoal);
  margin-bottom: var(--space-sm);
}

.feature-desc {
  font-size: 0.9rem;
  color: var(--color-warm-gray);
  line-height: 1.6;
}

/* ============================================
   Footer
   ============================================ */
.site-footer {
  padding: var(--space-2xl) var(--space-xl);
  text-align: center;
  background: var(--color-charcoal);
  position: relative;
}

.site-footer::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--color-terracotta), transparent);
}

.site-footer p {
  font-family: var(--font-display);
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.7);
  font-style: italic;
  letter-spacing: 0.05em;
}

/* ============================================
   Responsive
   ============================================ */
@media (max-width: 768px) {
  .hero {
    min-height: 90vh;
    padding: var(--space-xl) var(--space-md);
  }

  .hero-title {
    font-size: clamp(2rem, 8vw, 3rem);
  }

  .planner-section {
    padding: var(--space-xl) var(--space-md);
  }

  .planner-form {
    padding: var(--space-lg);
  }

  .form-row,
  .form-row--triple {
    grid-template-columns: 1fr;
  }

  .days-display {
    height: 48px;
  }

  .option-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .features-container {
    grid-template-columns: 1fr;
    gap: var(--space-lg);
  }

  .progress-steps {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .hero-title {
    font-size: 2rem;
  }

  .option-grid {
    grid-template-columns: 1fr 1fr;
  }

  .progress-steps {
    grid-template-columns: 1fr 1fr;
    gap: 6px;
  }

  .progress-step {
    font-size: 0.65rem;
  }

  .planner-form {
    padding: var(--space-md);
    border-radius: var(--radius-lg);
  }
}
</style>
