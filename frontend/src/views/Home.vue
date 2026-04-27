<template>
  <div class="home-container">
    <div class="page-header">
      <h1 class="page-title">✈️ 智能旅行助手</h1>
      <p class="page-subtitle">基于AI的个性化旅行规划</p>
    </div>

    <a-card class="form-card">
      <a-form :model="formData" @finish="handleSubmit" layout="vertical">
        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="目的地城市" name="city" :rules="[{ required: true, message: '请输入目的地城市' }, { validator: validateCity, trigger: 'blur' }]">
              <a-input v-model:value="formData.city" placeholder="请输入城市名称，如：北京、上海、成都" size="large" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="旅行天数" name="days" :rules="[{ required: true, message: '请选择天数' }]">
              <a-select v-model:value="formData.days" size="large">
                <a-select-option :value="1">1天</a-select-option>
                <a-select-option :value="2">2天</a-select-option>
                <a-select-option :value="3">3天</a-select-option>
                <a-select-option :value="4">4天</a-select-option>
                <a-select-option :value="5">5天</a-select-option>
                <a-select-option :value="6">6天</a-select-option>
                <a-select-option :value="7">7天</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="出发日期" name="start_date" :rules="[{ required: true, message: '请选择出发日期' }]">
              <a-date-picker
                v-model:value="startDate"
                style="width: 100%"
                size="large"
                format="YYYY-MM-DD"
                @change="onStartDateChange"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="返程日期" name="end_date" :rules="[{ required: true, message: '请选择返程日期' }]">
              <a-date-picker
                v-model:value="endDate"
                style="width: 100%"
                size="large"
                format="YYYY-MM-DD"
                @change="onEndDateChange"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="旅行偏好" name="preferences">
              <a-select v-model:value="formData.preferences" size="large">
                <a-select-option value="历史文化">🏛️ 历史文化</a-select-option>
                <a-select-option value="自然风光">🏔️ 自然风光</a-select-option>
                <a-select-option value="美食之旅">🍜 美食之旅</a-select-option>
                <a-select-option value="休闲度假">🏖️ 休闲度假</a-select-option>
                <a-select-option value="亲子游">👨‍👩‍👧 亲子游</a-select-option>
                <a-select-option value="购物娱乐">🛍️ 购物娱乐</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="预算范围" name="budget">
              <a-select v-model:value="formData.budget" size="large">
                <a-select-option value="经济">💰 经济 (500元/天以下)</a-select-option>
                <a-select-option value="中等">💵 中等 (500-1500元/天)</a-select-option>
                <a-select-option value="舒适">💸 舒适 (1500-3000元/天)</a-select-option>
                <a-select-option value="豪华">💎 豪华 (3000元/天以上)</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="交通方式" name="transportation">
              <a-select v-model:value="formData.transportation" size="large">
                <a-select-option value="公共交通">🚌 公共交通</a-select-option>
                <a-select-option value="出租车/网约车">🚕 出租车/网约车</a-select-option>
                <a-select-option value="租车自驾">🚗 租车自驾</a-select-option>
                <a-select-option value="步行">🚶 步行</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="住宿类型" name="accommodation">
              <a-select v-model:value="formData.accommodation" size="large">
                <a-select-option value="经济型酒店">🏨 经济型酒店</a-select-option>
                <a-select-option value="三星级酒店">🏨 三星级酒店</a-select-option>
                <a-select-option value="四星级酒店">🏨 四星级酒店</a-select-option>
                <a-select-option value="五星级酒店">🏨 五星级酒店</a-select-option>
                <a-select-option value="民宿">🏠 民宿</a-select-option>
                <a-select-option value="青年旅社">🎒 青年旅社</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item>
          <a-button type="primary" html-type="submit" size="large" :loading="loading" block>
            {{ loading ? '规划中...' : '开始规划' }}
          </a-button>
        </a-form-item>

        <a-form-item v-if="loading">
          <div class="progress-section">
            <a-progress :percent="loadingProgress" status="active" :stroke-color="'#a78bfa'" />
            <p class="loading-status">{{ loadingStatus }}</p>
            <div v-if="loadingDetails.length > 0" class="loading-details">
              <div v-for="(detail, index) in loadingDetails" :key="index" class="loading-detail-item">
                <span class="loading-detail-icon">•</span>
                <span class="loading-detail-text">{{ detail }}</span>
              </div>
            </div>
          </div>
        </a-form-item>
      </a-form>
    </a-card>

    <div class="features">
      <a-row :gutter="16">
        <a-col :span="8">
          <a-card size="small" class="feature-card">
            <template #title>🔍 智能搜索</template>
            <p>AI自动搜索景点、天气、酒店信息</p>
          </a-card>
        </a-col>
        <a-col :span="8">
          <a-card size="small" class="feature-card">
            <template #title>📅 个性化行程</template>
            <p>根据您的偏好定制每日行程安排</p>
          </a-card>
        </a-col>
        <a-col :span="8">
          <a-card size="small" class="feature-card">
            <template #title>💰 预算透明</template>
            <p>清晰的费用估算和明细分类</p>
          </a-card>
        </a-col>
      </a-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { generateTripPlan } from '@/services/api'
import type { TripPlanRequest } from '@/types'
import dayjs, { Dayjs } from 'dayjs'

const router = useRouter()

const loading = ref(false)
const loadingProgress = ref(0)
const loadingStatus = ref('')
const loadingDetails = ref<string[]>([])

const startDate = ref<Dayjs | null>(null)
const endDate = ref<Dayjs | null>(null)

const formData = ref<TripPlanRequest>({
  city: '',
  start_date: '',
  end_date: '',
  days: 3,
  preferences: '历史文化',
  budget: '中等',
  transportation: '公共交通',
  accommodation: '经济型酒店'
})

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
    formData.value.end_date = date.format('YYYY-MM-DD')
    updateDays()
  }
}

const validateCity = (_rule: any, value: string) => {
  if (!value) {
    return Promise.resolve()
  }
  if (value.trim().length < 2) {
    return Promise.reject('城市名称至少2个字符')
  }
  if (value.length > 20) {
    return Promise.reject('城市名称不能超过20个字符')
  }
  return Promise.resolve()
}

const updateDays = () => {
  if (startDate.value && endDate.value) {
    const days = endDate.value.diff(startDate.value, 'day') + 1
    formData.value.days = Math.max(1, days)
  }
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

  loading.value = true
  loadingProgress.value = 0

  loadingDetails.value = [
    '📋 准备规划参数...',
    '🔍 开始搜索景点信息...',
    '🌤️ 查询目的地天气...',
    '🏨 推荐合适的住宿...',
    '💰 计算旅行预算...',
    '📅 生成每日行程...',
    '🗺️ 规划景点路线...',
    '📝 整理最终计划...'
  ]

  let step = 0
  const progressInterval = setInterval(() => {
    if (loadingProgress.value < 95) {
      // 限制最大值并四舍五入为整数
      loadingProgress.value = Math.min(Math.round(loadingProgress.value + Math.random() * 8 + 3), 95)
      
      // 根据进度更新状态
      if (loadingProgress.value <= 15) {
        loadingStatus.value = '📋 准备规划参数...'
        step = 0
      } else if (loadingProgress.value <= 30) {
        loadingStatus.value = '🔍 正在搜索景点...'
        step = 1
      } else if (loadingProgress.value <= 45) {
        loadingStatus.value = '🌤️ 正在查询天气...'
        step = 2
      } else if (loadingProgress.value <= 60) {
        loadingStatus.value = '🏨 正在推荐酒店...'
        step = 3
      } else if (loadingProgress.value <= 70) {
        loadingStatus.value = '💰 计算旅行预算...'
        step = 4
      } else if (loadingProgress.value <= 80) {
        loadingStatus.value = '📅 生成每日行程...'
        step = 5
      } else if (loadingProgress.value <= 90) {
        loadingStatus.value = '🗺️ 规划景点路线...'
        step = 6
      } else {
        loadingStatus.value = '📝 整理最终计划...'
        step = 7
      }
    }
  }, 800)

  try {
    const response = await generateTripPlan(formData.value)
    clearInterval(progressInterval)
    loadingProgress.value = 100
    loadingStatus.value = '✅ 完成！'

    sessionStorage.setItem('tripPlan', JSON.stringify(response))

    setTimeout(() => {
      router.push({ name: 'result' })
    }, 500)
  } catch (error: any) {
    clearInterval(progressInterval)
    
    // 增强的错误处理
    if (error.enhanced) {
      message.error({
        content: `
          <div style="padding: 8px">
            <div style="font-weight: bold; margin-bottom: 4px">${error.errorMessage}</div>
            <div style="font-size: 12px; color: #666; margin-bottom: 8px">${error.errorDetails}</div>
            <div style="font-size: 12px; color: #8b5cf6">💡 ${error.solution}</div>
          </div>
        `,
        duration: 5
      })
    } else {
      message.error('生成计划失败，请稍后重试')
    }
    
    console.error('生成计划失败:', error)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.home-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 40px 20px;
  background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
  min-height: 100vh;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
  color: #5b21b6;
}

.page-title {
  font-size: 48px;
  font-weight: bold;
  margin-bottom: 12px;
  text-shadow: 2px 2px 8px rgba(139, 92, 246, 0.3);
}

.page-subtitle {
  font-size: 20px;
  opacity: 0.95;
  color: #7c3aed;
}

.form-card {
  border-radius: 16px;
  box-shadow: 0 8px 40px rgba(139, 92, 246, 0.15);
  border: 1px solid rgba(139, 92, 246, 0.08);
  background: white;
}

.progress-section {
  text-align: center;
}

.loading-status {
  margin-top: 12px;
  font-size: 16px;
  color: #8b5cf6;
  font-weight: 500;
  text-align: center;
}

.loading-details {
  margin-top: 16px;
  padding: 12px;
  background: rgba(139, 92, 246, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(139, 92, 246, 0.1);
}

.loading-detail-item {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
  font-size: 14px;
  color: #7c3aed;
}

.loading-detail-item:last-child {
  margin-bottom: 0;
}

.loading-detail-icon {
  margin-right: 8px;
  color: #a78bfa;
  font-weight: bold;
}

.loading-detail-text {
  flex: 1;
  line-height: 1.4;
}

.features {
  margin-top: 32px;
}

.feature-card {
  text-align: center;
  border-radius: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(139, 92, 246, 0.08);
  background: white;
  padding: 20px;
  min-height: 120px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(139, 92, 246, 0.15);
  border-color: rgba(139, 92, 246, 0.2);
}

.feature-card p {
  color: #7c3aed;
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .home-container {
    padding: 20px 16px;
  }
  
  .page-title {
    font-size: 36px;
  }
  
  .page-subtitle {
    font-size: 16px;
  }
  
  .form-card {
    padding: 16px;
  }
  
  .feature-card {
    padding: 16px;
    min-height: 100px;
  }
  
  .feature-card p {
    font-size: 14px;
  }
  
  .loading-details {
    padding: 10px;
  }
  
  .loading-detail-item {
    font-size: 12px;
  }
}

@media (max-width: 480px) {
  .home-container {
    padding: 16px 12px;
  }
  
  .page-title {
    font-size: 28px;
  }
  
  .page-subtitle {
    font-size: 14px;
  }
  
  .form-card {
    padding: 12px;
  }
  
  .feature-card {
    padding: 12px;
    min-height: 80px;
  }
  
  .feature-card p {
    font-size: 12px;
  }
  
  .loading-status {
    font-size: 14px;
  }
  
  .loading-details {
    padding: 8px;
  }
  
  .loading-detail-item {
    font-size: 11px;
  }
}
</style>
<style>
.home-container :deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #a78bfa 0%, #c4b5fd 100%);
  border: none;
}

.home-container :deep(.ant-btn-primary:hover) {
  background: linear-gradient(135deg, #c4b5fd 0%, #ddd6fe 100%);
}

.home-container :deep(.ant-card-head) {
  background: linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%);
  border-bottom: none;
}

.home-container :deep(.ant-card-head-title) {
  color: white;
  font-weight: 600;
}

.home-container :deep(.ant-progress-bg) {
  background: linear-gradient(90deg, #a78bfa 0%, #c4b5fd 100%);
}
</style>
