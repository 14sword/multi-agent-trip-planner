<template>
  <div class="result-container">
    <a-spin v-if="loading" :spinning="loading" tip="加载中...">
      <template #indicator>
        <a-spin tip="加载行程数据..." size="large" />
      </template>
      <div style="height: 80vh; display: flex; align-items: center; justify-content: center;"></div>
    </a-spin>

    <div v-else-if="error" class="error-container">
      <EmptyState
        icon="📋"
        title="无法加载行程"
        description="行程数据为空或已过期，请返回首页重新规划"
        actionText="返回首页"
        :tips="['确保从首页提交规划请求', '刷新页面后重试']"
        @action="$router.push('/')"
      />
    </div>

    <div v-else>
      <a-row :gutter="24">
        <a-col :span="6">
          <a-affix :offset-top="20">
            <a-card class="sidebar" size="small">
              <template #title>📑 目录</template>
              <a-menu
                v-model:selectedKeys="selectedKeys"
                mode="inline"
                @click="scrollToSection"
              >
                <a-menu-item key="overview">📋 行程概览</a-menu-item>
                <a-menu-item key="budget" v-if="tripPlan.budget">💰 预算明细</a-menu-item>
                <a-menu-item key="map">🗺️ 地图</a-menu-item>
                <a-menu-item key="days">📅 每日行程</a-menu-item>
                <a-menu-item key="weather">🌤️ 天气</a-menu-item>
              </a-menu>

              <a-divider />

              <a-space direction="vertical" style="width: 100%">
                <a-button type="primary" block @click="toggleEditMode">
                  {{ editMode ? '📤 取消编辑' : '✏️ 编辑行程' }}
                </a-button>
                <a-button block @click="exportPDF">
                  📄 导出PDF
                </a-button>
                <a-button block @click="exportImage">
                  🖼️ 导出图片
                </a-button>
                <a-button block @click="showShareOptions">
                  📤 分享行程
                </a-button>
                <a-button block @click="toggleFavorite" :type="isFavorite ? 'primary' : 'default'">
                  {{ isFavorite ? '❤️ 已收藏' : '🤍 收藏行程' }}
                </a-button>
                <a-button block @click="$router.push('/')">
                  🏠 返回首页
                </a-button>
              </a-space>
            </a-card>
          </a-affix>
        </a-col>

        <a-col :span="18">
          <div id="trip-plan-content">
            <a-row :gutter="16" class="header-actions" style="margin-bottom: 16px;">
              <a-col :span="24">
                <a-space>
                  <a-button v-if="editMode" type="primary" @click="saveChanges" :loading="saving">💾 保存修改</a-button>
                  <a-button v-if="editMode" @click="cancelEdit">❌ 取消</a-button>
                </a-space>
              </a-col>
            </a-row>

            <div id="overview">
              <a-card class="section-card">
                <template #title>
                  <span class="section-title">📋 行程概览</span>
                </template>
                <a-descriptions bordered>
                  <a-descriptions-item label="目的地">{{ tripPlan.city }}</a-descriptions-item>
                  <a-descriptions-item label="行程天数">{{ tripPlan.days.length }}天</a-descriptions-item>
                  <a-descriptions-item label="日期范围">
                    {{ tripPlan.start_date }} ~ {{ tripPlan.end_date }}
                  </a-descriptions-item>
                </a-descriptions>
                <a-divider />
                <a-typography-paragraph>
                  <blockquote>{{ tripPlan.overall_suggestions }}</blockquote>
                </a-typography-paragraph>
              </a-card>
            </div>

            <div id="budget" v-if="tripPlan.budget">
              <a-card class="section-card">
                <template #title>
                  <span class="section-title">💰 预算明细</span>
                </template>
                <a-row :gutter="16">
                  <a-col :span="6">
                    <div class="budget-item">
                      <div class="budget-item-header">
                        <span class="budget-icon">🎫</span>
                        <span class="budget-label">景点门票</span>
                      </div>
                      <div class="budget-value">¥{{ tripPlan.budget.total_attractions }}</div>
                      <a-progress 
                        :percent="Math.round((tripPlan.budget.total_attractions / tripPlan.budget.total) * 100)" 
                        :stroke-color="'#722ed1'" 
                        :show-info="false"
                        size="small"
                      />
                    </div>
                  </a-col>
                  <a-col :span="6">
                    <div class="budget-item">
                      <div class="budget-item-header">
                        <span class="budget-icon">🏨</span>
                        <span class="budget-label">酒店住宿</span>
                      </div>
                      <div class="budget-value">¥{{ tripPlan.budget.total_hotels }}</div>
                      <a-progress 
                        :percent="Math.round((tripPlan.budget.total_hotels / tripPlan.budget.total) * 100)" 
                        :stroke-color="'#eb2f96'" 
                        :show-info="false"
                        size="small"
                      />
                    </div>
                  </a-col>
                  <a-col :span="6">
                    <div class="budget-item">
                      <div class="budget-item-header">
                        <span class="budget-icon">🍜</span>
                        <span class="budget-label">餐饮费用</span>
                      </div>
                      <div class="budget-value">¥{{ tripPlan.budget.total_meals }}</div>
                      <a-progress 
                        :percent="Math.round((tripPlan.budget.total_meals / tripPlan.budget.total) * 100)" 
                        :stroke-color="'#fa8c16'" 
                        :show-info="false"
                        size="small"
                      />
                    </div>
                  </a-col>
                  <a-col :span="6">
                    <div class="budget-item">
                      <div class="budget-item-header">
                        <span class="budget-icon">🚗</span>
                        <span class="budget-label">交通费用</span>
                      </div>
                      <div class="budget-value">¥{{ tripPlan.budget.total_transportation }}</div>
                      <a-progress 
                        :percent="Math.round((tripPlan.budget.total_transportation / tripPlan.budget.total) * 100)" 
                        :stroke-color="'#1890ff'" 
                        :show-info="false"
                        size="small"
                      />
                    </div>
                  </a-col>
                </a-row>
                <a-divider />
                <a-row>
                  <a-col :span="24" style="text-align: center;">
                    <div class="budget-total">
                      <span class="budget-total-label">💎 预估总费用</span>
                      <span class="budget-total-value">¥{{ tripPlan.budget.total }}</span>
                    </div>
                  </a-col>
                </a-row>
              </a-card>
            </div>

            <div id="map">
              <a-card class="section-card">
                <template #title>
                  <span class="section-title">🗺️ 景点地图</span>
                </template>
                <div id="amap-container" style="height: 400px; border-radius: 8px; position: relative;">
                  <a-spin v-if="mapLoading" :spinning="mapLoading" tip="加载地图中..." style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 10;" />
                </div>
              </a-card>
            </div>

            <div id="days">
              <a-card class="section-card">
              <template #title>
                <span class="section-title">📅 每日行程</span>
              </template>

              <a-collapse v-model:activeKey="activeDays">
                <a-collapse-panel
                  v-for="(day, dayIndex) in tripPlan.days"
                  :key="day.day_index"
                >
                  <template #header>
                    <div class="day-header">
                      <div class="day-header-left">
                        <span class="day-icon">{{ getDayIcon(dayIndex) }}</span>
                        <div class="day-info">
                          <span class="day-title">第{{ dayIndex + 1 }}天</span>
                          <span class="day-date">{{ formatDate(day.date) }} {{ getWeekday(day.date) }}</span>
                        </div>
                      </div>
                      <div class="day-header-right">
                        <a-tag :color="getTagColor(dayIndex)" class="day-description">
                          {{ day.description }}
                        </a-tag>
                        <div class="day-stats">
                          <a-tag v-if="day.attractions.length > 0" color="blue">
                            🏛️ {{ day.attractions.length }}个景点
                          </a-tag>
                          <a-tag v-if="day.meals && day.meals.length > 0" color="green">
                            🍜 {{ day.meals.length }}餐
                          </a-tag>
                          <a-tag v-if="day.hotel" color="orange">
                            🏨 住宿
                          </a-tag>
                        </div>
                      </div>
                    </div>
                  </template>

                  <a-divider orientation="left">🏛️ 景点</a-divider>
                  
                  <!-- 添加景点按钮 -->
                  <div v-if="editMode" style="margin-bottom: 16px;">
                    <a-button type="dashed" block @click="addAttraction(day.day_index)">
                      ➕ 添加景点
                    </a-button>
                  </div>
                  
                  <div v-for="(attraction, index) in day.attractions" :key="index" class="attraction-item">
                    <a-card size="small" class="attraction-card">
                      <a-row :gutter="16" align="middle">
                        <a-col :span="14">
                          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <h4 v-if="!editMode">{{ attraction.name }}</h4>
                            <a-input v-else v-model:value="attraction.name" placeholder="景点名称" style="font-weight: 600;" />
                            <a-button 
                              v-if="!editMode"
                              size="small" 
                              type="text" 
                              @click="toggleAttractionDetails(day.day_index, index)"
                            >
                              {{ expandedAttractions[`${day.day_index}-${index}`] ? '收起' : '展开' }}
                            </a-button>
                          </div>
                          <div v-if="editMode" style="margin-bottom: 8px;">
                            <a-input v-model:value="attraction.address" placeholder="📍 地址" style="margin-bottom: 4px;" />
                            <a-input-number v-model:value="attraction.visit_duration" min="1" max="480" placeholder="⏱️ 游览时间(分钟)" style="width: 100%; margin-bottom: 4px;" />
                            <a-input v-model:value="attraction.ticket_price" placeholder="🎫 门票价格(元)" style="margin-bottom: 4px;" />
                            <a-input v-model:value="attraction.rating" placeholder="⭐ 评分" />
                          </div>
                          <template v-else>
                            <p>📍 {{ attraction.address }}</p>
                            <p>⏱️ 建议游览 {{ attraction.visit_duration }} 分钟</p>
                            <p v-if="attraction.ticket_price">🎫 门票: {{ attraction.ticket_price }}元</p>
                            <p v-if="attraction.rating">⭐ 评分: {{ attraction.rating }}</p>
                          </template>
                          
                          <!-- 景点详情展开区域 -->
                          <div 
                            v-if="expandedAttractions[`${day.day_index}-${index}`] && !editMode" 
                            class="attraction-details"
                          >
                            <a-divider orientation="left" style="margin: 12px 0;">详情</a-divider>
                            <p v-if="attraction.description" style="line-height: 1.5;">{{ attraction.description }}</p>
                            <p v-if="attraction.opening_hours" style="line-height: 1.5;">🕐 开放时间: {{ attraction.opening_hours }}</p>
                            <p v-if="attraction.transportation" style="line-height: 1.5;">🚗 交通: {{ attraction.transportation }}</p>
                            <p v-if="attraction.notes" style="line-height: 1.5;">📝 备注: {{ attraction.notes }}</p>
                          </div>
                        </a-col>
                        <a-col :span="10">
                          <div class="attraction-image-container">
                            <img
                              v-if="attraction.image_url"
                              :src="attraction.image_url"
                              :alt="attraction.name"
                              loading="lazy"
                              class="attraction-image"
                            />
                          </div>
                        </a-col>
                      </a-row>
                      <div v-if="editMode" class="edit-actions">
                        <a-space>
                          <a-button size="small" @click="moveAttraction(day.day_index, index, 'up')">⬆️ 上移</a-button>
                          <a-button size="small" @click="moveAttraction(day.day_index, index, 'down')">⬇️ 下移</a-button>
                          <a-button size="small" danger @click="deleteAttraction(day.day_index, index)">🗑️ 删除</a-button>
                        </a-space>
                      </div>
                    </a-card>
                  </div>

                  <a-divider orientation="left">🍜 餐饮</a-divider>
                  <a-list size="small" bordered>
                    <a-list-item v-for="meal in day.meals" :key="meal.type">
                      <a-list-item-meta>
                        <template #title>
                          {{ getMealEmoji(meal.type) }} {{ meal.name }}
                        </template>
                        <template #description>
                          💰 约{{ meal.estimated_cost }}元
                        </template>
                      </a-list-item-meta>
                    </a-list-item>
                  </a-list>

                  <a-divider orientation="left">🏨 住宿</a-divider>
                  <a-card size="small" v-if="day.hotel">
                    <h4>{{ day.hotel.name }}</h4>
                    <p>📍 {{ day.hotel.address }}</p>
                    <p>💰 约{{ day.hotel.estimated_cost }}元/晚</p>
                  </a-card>
                </a-collapse-panel>
              </a-collapse>
            </a-card>
            </div>

            <div id="weather">
              <a-card class="section-card">
                <template #title>
                  <span class="section-title">🌤️ 天气预报</span>
                </template>
                <a-row :gutter="16">
                  <a-col :span="24">
                    <a-list :grid="{ gutter: 16, xs: 1, sm: 2, md: 3, lg: 4 }" :data-source="tripPlan.weather_info">
                      <template #renderItem="{ item }">
                        <a-list-item>
                          <a-card size="small" :class="getWeatherCardClass(item.day_weather)">
                            <h4>{{ item.date }}</h4>
                            <p>{{ getWeatherEmoji(item.day_weather) }} {{ item.day_weather }}</p>
                            <p>{{ getWeatherEmoji(item.night_weather) }} {{ item.night_weather }}</p>
                            <p>🌡️ {{ item.day_temp }}°C / {{ item.night_temp }}°C</p>
                            <p>💨 {{ item.wind_direction }} {{ item.wind_power }}</p>
                          </a-card>
                        </a-list-item>
                      </template>
                    </a-list>
                  </a-col>
                </a-row>
              </a-card>
            </div>
          </div>
        </a-col>
      </a-row>
    </div>

    <!-- 分享模态框 -->
    <a-modal
      v-model:visible="shareVisible"
      title="📤 分享行程"
      width="500px"
      :footer="null"
    >
      <div class="share-content" style="text-align: center; padding: 20px 0;">
        <div style="font-size: 48px; margin-bottom: 16px;">🔧</div>
        <h3 style="color: #333; margin-bottom: 12px;">分享功能需要云服务器支持</h3>
        <p style="color: #666; line-height: 1.6; margin-bottom: 16px;">
          当前版本暂不支持在线分享功能。<br/>
          您可以：
        </p>
        <a-list size="small" style="text-align: left; max-width: 300px; margin: 0 auto;">
          <a-list-item>❤️ 使用收藏功能保存行程</a-list-item>
          <a-list-item>📄 使用PDF导出功能导出行程</a-list-item>
          <a-list-item>✏️ 编辑行程后重新生成</a-list-item>
        </a-list>
        <div style="margin-top: 20px; padding: 12px; background: #f5f5f5; border-radius: 8px;">
          <p style="font-size: 12px; color: #666; margin: 0;">
            💡 部署云服务器后可实现在线分享功能
          </p>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import type { TripPlan, DayPlan } from '@/types'
import { editTripPlan, ApiError } from '@/services/api'
import AMapLoader from '@amap/amap-jsapi-loader'
import EmptyState from '@/components/EmptyState.vue'

const tripPlan = ref<TripPlan>({
  city: '',
  start_date: '',
  end_date: '',
  days: [],
  weather_info: [],
  overall_suggestions: ''
})

const loading = ref(true)
const error = ref(false)
const saving = ref(false)
const mapLoading = ref(false)
const editMode = ref(false)
const originalPlan = ref<TripPlan | null>(null)
const activeSection = ref('overview')
const selectedKeys = ref<string[]>(['overview'])
const activeDays = ref<number[]>([0])
const expandedAttractions = ref<Record<string, boolean>>({})
const shareVisible = ref(false)
const isFavorite = ref(false)
let map: any = null
let abortController: AbortController | null = null

onBeforeUnmount(() => {
  abortController?.abort()
  if (map) {
    map.destroy()
    map = null
  }
})

onMounted(() => {
  const savedPlan = sessionStorage.getItem('tripPlan')
  if (savedPlan) {
    try {
      tripPlan.value = JSON.parse(savedPlan)
      checkFavorite()
      nextTick(() => {
        initMap()
      })
    } catch {
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
    if (!mapContainer) {
      message.error('找不到地图容器')
      return
    }

    mapContainer.style.height = '400px'
    mapContainer.style.width = '100%'
    mapContainer.style.border = '1px solid #d9d9d9'
    mapContainer.style.background = '#f5f5f5'

    try {
      const AMap = await AMapLoader.load({
        key: import.meta.env.VITE_AMAP_KEY || '',
        version: '2.0',
        plugins: ['AMap.Scale', 'AMap.ToolBar', 'AMap.InfoWindow']
      })

      if (map) {
        map.destroy()
        map = null
      }

      const firstAttraction = tripPlan.value.days[0]?.attractions[0]
      const hasLocation = firstAttraction?.location?.longitude && firstAttraction?.location?.latitude

      map = new AMap.Map(mapContainer, {
        zoom: 12,
        center: hasLocation
          ? [firstAttraction.location.longitude, firstAttraction.location.latitude]
          : [116.397428, 39.90923],
        resizeEnable: true,
        zoomEnable: true,
        dragEnable: true,
      })

      map.addControl(new AMap.Scale())
      map.addControl(new AMap.ToolBar())

      const allPositions: [number, number][] = []

      tripPlan.value.days.forEach((day) => {
        day.attractions.forEach((attraction, index) => {
          const loc = attraction.location
          if (!loc?.longitude || !loc?.latitude) return

          const position: [number, number] = [loc.longitude, loc.latitude]
          allPositions.push(position)

          const marker = new AMap.Marker({
            position,
            title: attraction.name,
            label: {
              content: `${day.day_index + 1}-${index + 1}`,
              direction: 'top',
              offset: new AMap.Pixel(0, -30),
              style: {
                backgroundColor: '#1890ff',
                color: '#fff',
                border: 'none',
                padding: '2px 6px',
                borderRadius: '4px',
                fontSize: '12px',
              },
            },
          })

          const infoWindow = new AMap.InfoWindow({
            content: `
              <div style="padding: 10px; min-width: 200px;">
                <h3 style="margin: 0 0 10px 0; font-size: 14px;">${attraction.name}</h3>
                <p style="margin: 5px 0; font-size: 12px;">📍 ${attraction.address}</p>
                <p style="margin: 5px 0; font-size: 12px;">⏱️ 建议游览 ${attraction.visit_duration} 分钟</p>
                ${attraction.ticket_price ? `<p style="margin: 5px 0; font-size: 12px;">🎫 门票: ${attraction.ticket_price}元</p>` : ''}
                ${attraction.rating ? `<p style="margin: 5px 0; font-size: 12px;">⭐ 评分: ${attraction.rating}</p>` : ''}
              </div>
            `,
            offset: new AMap.Pixel(0, -40),
          })

          marker.on('click', () => infoWindow.open(map, marker.getPosition()))
          map.add(marker)
        })
      })

      if (allPositions.length > 1) {
        for (let i = 0; i < allPositions.length - 1; i++) {
          const [lng1, lat1] = allPositions[i]
          const [lng2, lat2] = allPositions[i + 1]
          const midLng = (lng1 + lng2) / 2
          const midLat = (lat1 + lat2) / 2
          const dist = Math.sqrt((lng2 - lng1) ** 2 + (lat2 - lat1) ** 2)
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
            strokeColor: '#1890ff',
            strokeWeight: 4,
            strokeOpacity: 0.8,
            lineJoin: 'round',
            lineCap: 'round',
            showDir: true,
          })
          map.add(curve)
        }
      }
    } catch {
      message.error('高德地图API加载失败，请检查网络连接')
      mapContainer.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: center; height: 100%;">
          <div style="text-align: center;">
            <p style="color: #ff4d4f; margin-bottom: 8px;">地图加载失败</p>
            <p style="color: #666; font-size: 12px;">请检查网络连接或刷新页面重试</p>
          </div>
        </div>
      `
    }
  } catch {
    message.error('地图初始化失败')
  } finally {
    mapLoading.value = false
  }
}

const scrollToSection = ({ key }: { key: string }) => {
  activeSection.value = key
  selectedKeys.value = [key]
  const element = document.getElementById(key)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

const toggleEditMode = () => {
  if (!editMode.value) {
    originalPlan.value = JSON.parse(JSON.stringify(tripPlan.value))
  }
  editMode.value = !editMode.value
}

const saveChanges = async () => {
  abortController = new AbortController()
  saving.value = true
  try {
    const updatedPlan = await editTripPlan(tripPlan.value, abortController.signal)
    tripPlan.value = updatedPlan
    sessionStorage.setItem('tripPlan', JSON.stringify(updatedPlan))
    editMode.value = false
    message.success('修改已保存')
    nextTick(() => initMap())
  } catch (error: unknown) {
    if (error instanceof ApiError) {
      message.error(`${error.message}${error.solution ? '，' + error.solution : ''}`)
    } else if (!(error instanceof Error && error.name === 'AbortError')) {
      message.error('保存失败，请稍后重试')
    }
  } finally {
    saving.value = false
  }
}

const cancelEdit = () => {
  if (originalPlan.value) {
    tripPlan.value = originalPlan.value
  }
  editMode.value = false
  message.info('已取消修改')
}

const moveAttraction = (dayIndex: number, attractionIndex: number, direction: string) => {
  const attractions = tripPlan.value.days[dayIndex].attractions
  const newIndex = direction === 'up' ? attractionIndex - 1 : attractionIndex + 1

  if (newIndex >= 0 && newIndex < attractions.length) {
    [attractions[attractionIndex], attractions[newIndex]] = [attractions[newIndex], attractions[attractionIndex]]
    // 实时更新地图
    nextTick(() => {
      initMap()
    })
  }
}

const deleteAttraction = (dayIndex: number, attractionIndex: number) => {
  // 添加确认提示
  const confirmed = confirm('确定要删除这个景点吗？')
  if (!confirmed) {
    return
  }
  
  // 确保索引有效
  if (dayIndex >= tripPlan.value.days.length || attractionIndex >= tripPlan.value.days[dayIndex].attractions.length) {
    message.error('删除失败：索引无效')
    return
  }
  
  tripPlan.value.days[dayIndex].attractions.splice(attractionIndex, 1)
  message.success('已删除景点')
  
  // 实时更新地图
  nextTick(() => {
    initMap()
  })
}

const addAttraction = (dayIndex: number) => {
  const newAttraction = {
    name: '新景点',
    address: '请输入地址',
    location: {
      longitude: tripPlan.value.days[dayIndex].attractions[0]?.location.longitude || 104.0668,
      latitude: tripPlan.value.days[dayIndex].attractions[0]?.location.latitude || 30.5728
    },
    visit_duration: 60,
    description: '请输入景点描述',
    ticket_price: 0
  }
  tripPlan.value.days[dayIndex].attractions.push(newAttraction)
  message.success('已添加新景点')
  // 实时更新地图
  nextTick(() => {
    initMap()
  })
}

const getMealEmoji = (type: string) => {
  const emojis: Record<string, string> = {
    breakfast: '🌅',
    lunch: '🌞',
    dinner: '🌙',
    snack: '🍿'
  }
  return emojis[type] || '🍽️'
}

const getDayIcon = (dayIndex: number) => {
  const icons = ['🌟', '✨', '🌈', '🎯', '🎪', '🎨', '🏆', '💫']
  return icons[dayIndex % icons.length]
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    const month = date.getMonth() + 1
    const day = date.getDate()
    return `${month}月${day}日`
  } catch {
    return dateStr
  }
}

const getWeekday = (dateStr: string) => {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    return weekdays[date.getDay()]
  } catch {
    return ''
  }
}

const getTagColor = (dayIndex: number) => {
  const colors = ['blue', 'green', 'orange', 'red', 'purple', 'cyan', 'magenta', 'gold']
  return colors[dayIndex % colors.length]
}

const getWeatherEmoji = (weather: string) => {
  if (weather.includes('晴')) return '☀️'
  if (weather.includes('阴')) return '☁️'
  if (weather.includes('雨')) return '🌧️'
  if (weather.includes('雪')) return '❄️'
  if (weather.includes('雾')) return '🌫️'
  if (weather.includes('风')) return '💨'
  return '🌤️'
}

const getWeatherCardClass = (weather: string) => {
  if (weather.includes('晴')) return 'weather-sunny'
  if (weather.includes('雨')) return 'weather-rainy'
  if (weather.includes('雪')) return 'weather-snowy'
  return 'weather-cloudy'
}

const toggleAttractionDetails = (dayIndex: number, attractionIndex: number) => {
  const key = `${dayIndex}-${attractionIndex}`
  expandedAttractions.value[key] = !expandedAttractions.value[key]
}

const exportPDF = () => {
  message.info('正在生成PDF...')
  // 使用浏览器打印功能实现PDF导出
  window.print()
}

const exportImage = () => {
  message.info('图片导出功能开发中，建议使用PDF导出功能')
}

const showShareOptions = () => {
  shareVisible.value = true
}

const getFavoriteKey = () => {
  return `favorite_${tripPlan.value.city}_${tripPlan.value.start_date}`
}

const checkFavorite = () => {
  const key = getFavoriteKey()
  isFavorite.value = localStorage.getItem(key) !== null
}

const toggleFavorite = () => {
  const key = getFavoriteKey()
  if (isFavorite.value) {
    localStorage.removeItem(key)
    message.success('已取消收藏')
  } else {
    const favoriteData = {
      city: tripPlan.value.city,
      start_date: tripPlan.value.start_date,
      end_date: tripPlan.value.end_date,
      total_days: tripPlan.value.days.length,
      total_budget: tripPlan.value.budget?.total || 0,
      saved_at: new Date().toISOString(),
      plan_data: JSON.stringify(tripPlan.value)
    }
    localStorage.setItem(key, JSON.stringify(favoriteData))
    message.success('行程已保存到本地浏览器！')
  }
  checkFavorite()
}
</script>

<style scoped>
.result-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
  background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.sidebar {
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(139, 92, 246, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: white;
  border: 1px solid rgba(139, 92, 246, 0.08);
}

.sidebar:hover {
  box-shadow: 0 8px 30px rgba(139, 92, 246, 0.15);
  transform: translateY(-2px);
}

.section-card {
  margin-bottom: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(139, 92, 246, 0.06);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  background: white;
  border: 1px solid rgba(139, 92, 246, 0.06);
}

.section-card:hover {
  box-shadow: 0 8px 28px rgba(139, 92, 246, 0.12);
  transform: translateY(-2px);
  border-color: rgba(139, 92, 246, 0.15);
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 0;
}

/* 预算卡片样式 */
.budget-item {
  background: #fafafa;
  border-radius: 10px;
  padding: 14px;
  transition: all 0.3s ease;
  border: 1px solid #f0f0f0;
}

.budget-item:hover {
  background: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.budget-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.budget-icon {
  font-size: 16px;
}

.budget-label {
  font-size: 13px;
  color: #666;
}

.budget-value {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 8px;
}

.budget-total {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%);
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(139, 92, 246, 0.25);
}

.budget-total-label {
  font-size: 14px;
  color: #fff;
  opacity: 0.9;
}

.budget-total-value {
  font-size: 32px;
  font-weight: bold;
  color: #fff;
}

/* 按钮样式优化 */
:deep(.ant-btn) {
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.1);
}

:deep(.ant-btn:hover) {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(139, 92, 246, 0.15);
}

:deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #a78bfa 0%, #c4b5fd 100%);
  border: none;
}

:deep(.ant-btn-primary:hover) {
  background: linear-gradient(135deg, #c4b5fd 0%, #ddd6fe 100%);
}

/* 卡片标题样式 */
:deep(.ant-card-head) {
  border-bottom: none;
  background: linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%);
  padding: 12px 20px;
}

:deep(.ant-card-head-title) {
  font-size: 16px;
  font-weight: 600;
  color: white;
}

/* 菜单样式 */
:deep(.ant-menu) {
  background: transparent;
  border-right: none;
}

:deep(.ant-menu-item) {
  border-radius: 8px;
  margin: 4px 8px;
  transition: all 0.3s ease;
}

:deep(.ant-menu-item:hover) {
  background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
}

:deep(.ant-menu-item-selected) {
  background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
  color: #7c3aed;
  font-weight: 600;
}

/* 列表样式 */
:deep(.ant-list-item) {
  transition: all 0.3s ease;
  border-radius: 8px;
  margin-bottom: 4px;
}

:deep(.ant-list-item:hover) {
  background-color: #faf5ff;
  padding-left: 16px;
}

/* 折叠面板样式 */
:deep(.ant-collapse-item) {
  border-radius: 12px !important;
  margin-bottom: 12px;
  overflow: hidden;
  border: 1px solid rgba(139, 92, 246, 0.1);
}

:deep(.ant-collapse-header) {
  font-weight: 600;
  color: #5b21b6;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, #faf5ff 0%, #f5f3ff 100%);
  border-radius: 12px !important;
}

:deep(.ant-collapse-header:hover) {
  background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
  color: #7c3aed;
}

:deep(.ant-collapse-content-box) {
  background: white;
}

/* 标签样式 */
:deep(.ant-tag) {
  border-radius: 6px;
  font-size: 12px;
  padding: 4px 10px;
  font-weight: 500;
}

/* 统计数字样式 */
:deep(.ant-statistic-content-value) {
  font-weight: 700;
  color: #8b5cf6;
}

:deep(.ant-statistic-title) {
  color: #7c3aed;
  font-weight: 500;
}

/* 预算卡片特殊样式 */
:deep(.budget-total-card) {
  background: linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%);
  color: white;
  border-radius: 12px;
}

:deep(.budget-total-card .ant-statistic-title),
:deep(.budget-total-card .ant-statistic-content-value) {
  color: white;
}

/* 加载动画 */
:deep(.ant-spin-dot) {
  font-size: 28px;
}

/* 进度条样式 */
:deep(.ant-progress-bg) {
  background: linear-gradient(90deg, #a78bfa 0%, #c4b5fd 100%);
}

/* 输入框样式 */
:deep(.ant-input),
:deep(.ant-select-selector),
:deep(.ant-picker) {
  border-radius: 8px !important;
  transition: all 0.3s ease;
}

:deep(.ant-input:hover),
:deep(.ant-select-selector:hover),
:deep(.ant-picker:hover) {
  border-color: #40a9ff !important;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.1);
}

:deep(.ant-input:focus),
:deep(.ant-select-focused .ant-select-selector),
:deep(.ant-picker-focused) {
  border-color: #1890ff !important;
  box-shadow: 0 0 0 3px rgba(24, 144, 255, 0.2) !important;
}

/* 响应式布局优化 */
@media (max-width: 992px) {
  .result-container {
    padding: 16px;
  }
  
  .sidebar {
    position: relative !important;
    margin-bottom: 24px;
  }
}

@media (max-width: 768px) {
  .result-container {
    padding: 12px;
  }
  
  .section-card {
    margin-bottom: 16px;
  }
}

.section-title {
  font-size: 16px;
}

/* 每日行程header样式 */
.day-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  width: 100%;
  padding: 4px 0;
  gap: 16px;
}

.day-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.day-icon {
  font-size: 24px;
  line-height: 1;
}

.day-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.day-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.3;
}

.day-date {
  font-size: 13px;
  color: #666;
  line-height: 1.3;
}

.day-header-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 8px;
    flex-wrap: wrap;
    flex: 1;
    justify-content: flex-start;
  }

  .day-stats {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

.day-description {
  max-width: 400px;
  white-space: normal;
  word-break: break-word;
  line-height: 1.4;
  padding: 4px 10px;
}

.attraction-card {
  margin-bottom: 12px;
  border-radius: 8px;
}

.attraction-item {
  margin-bottom: 12px;
}

.edit-actions {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #ddd;
}

.weather-sunny {
  background: linear-gradient(135deg, #fff9e6 0%, #ffffff 100%);
  border: 1px solid #ffe58f;
  box-shadow: 0 4px 12px rgba(255, 229, 143, 0.2);
  transition: all 0.3s ease;
}

.weather-cloudy {
  background: linear-gradient(135deg, #f0f5ff 0%, #ffffff 100%);
  border: 1px solid #adc6ff;
  box-shadow: 0 4px 12px rgba(173, 198, 255, 0.2);
  transition: all 0.3s ease;
}

.weather-rainy {
  background: linear-gradient(135deg, #f6ffed 0%, #ffffff 100%);
  border: 1px solid #b7eb8f;
  box-shadow: 0 4px 12px rgba(183, 235, 143, 0.2);
  transition: all 0.3s ease;
}

.weather-snowy {
  background: linear-gradient(135deg, #f9f0ff 0%, #ffffff 100%);
  border: 1px solid #d3adf7;
  box-shadow: 0 4px 12px rgba(211, 173, 247, 0.2);
  transition: all 0.3s ease;
}

.weather-sunny:hover,
.weather-cloudy:hover,
.weather-rainy:hover,
.weather-snowy:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
}

.weather-sunny h4,
.weather-cloudy h4,
.weather-rainy h4,
.weather-snowy h4 {
  color: #1a1a1a;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
  text-align: center;
}

.weather-sunny p,
.weather-cloudy p,
.weather-rainy p,
.weather-snowy p {
  color: #4b5563;
  margin: 6px 0;
  font-size: 13px;
  text-align: center;
  line-height: 1.4;
}

.weather-sunny p:first-of-type,
.weather-cloudy p:first-of-type,
.weather-rainy p:first-of-type,
.weather-snowy p:first-of-type {
  font-weight: 500;
  color: #374151;
}

.weather-sunny p:nth-child(3),
.weather-cloudy p:nth-child(3),
.weather-rainy p:nth-child(3),
.weather-snowy p:nth-child(3) {
  font-weight: 500;
  color: #374151;
}

.header-actions {
  display: flex;
  justify-content: flex-end;
}

.attraction-image-container {
  width: 100%;
  height: 120px;
  overflow: hidden;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f3e8ff 0%, #ede9fe 100%);
  border: 1px solid rgba(139, 92, 246, 0.1);
  position: relative;
}

.attraction-image-container::before {
  content: '📸';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 24px;
  color: #a78bfa;
  opacity: 0.6;
  z-index: 1;
}

.attraction-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: all 0.3s ease;
  opacity: 0;
  position: relative;
  z-index: 2;
}

.attraction-image[loading="lazy"]:loaded {
  opacity: 1;
}

/* 兼容不同浏览器的图片加载状态 */
.attraction-image {
  animation: fadeIn 0.5s ease-in-out forwards;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.attraction-image:hover {
  transform: scale(1.05);
}

.attraction-details {
  margin-top: 12px;
  padding: 12px;
  background: rgba(139, 92, 246, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(139, 92, 246, 0.1);
  animation: slideDown 0.3s ease-in-out;
}

.share-content {
  padding: 10px 0;
}

.share-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.share-options .ant-btn {
  padding: 12px 0;
  font-size: 14px;
  font-weight: 500;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 文字溢出处理 */
h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

p {
  margin: 4px 0;
  font-size: 14px;
  color: #666;
  line-height: 1.4;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

/* 统一色块样式 */
.weather-sunny,
.weather-cloudy,
.weather-rainy,
.weather-snowy {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.weather-sunny:hover,
.weather-cloudy:hover,
.weather-rainy:hover,
.weather-snowy:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* 卡片样式统一 */
.attraction-card {
  margin-bottom: 12px;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
  transition: all 0.3s ease;
}

.attraction-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #1890ff;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .attraction-image-container {
    height: 100px;
    background: linear-gradient(135deg, #f3e8ff 0%, #ede9fe 100%);
    border: 1px solid rgba(139, 92, 246, 0.1);
  }

  h4 {
    font-size: 14px;
  }

  p {
    font-size: 12px;
  }
}

/* 打印样式优化 - 确保PDF导出格式正确 */
@media print {
  /* 全局打印基础设置 */
  * {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }

  @page {
    size: A4;
    margin: 15mm;
  }

  /* 隐藏不需要打印的元素 */
  .sidebar,
  .header-actions,
  .edit-actions,
  .ant-affix,
  .ant-spin,
  .ant-spin-nested-loading {
    display: none !important;
  }

  /* 主容器优化 */
  .result-container {
    max-width: 100% !important;
    width: 100% !important;
    padding: 0 !important;
    background: white !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  }

  /* 内容区域优化 */
  #trip-plan-content {
    width: 100% !important;
    max-width: 100% !important;
  }

  /* 卡片样式优化 */
  .section-card {
    box-shadow: none !important;
    border: 1px solid #e8e8e8 !important;
    border-radius: 8px !important;
    page-break-inside: avoid;
    margin-bottom: 20px !important;
    background: white !important;
  }

  /* 标题优化 */
  :deep(.ant-card-head) {
    background: #f8f9fa !important;
    border-bottom: 1px solid #e8e8e8 !important;
  }

  :deep(.ant-card-head-title) {
    font-weight: 600 !important;
    font-size: 16px !important;
    color: #1a1a1a !important;
  }

  /* 每日行程折叠面板打印优化 */
  :deep(.ant-collapse) {
    border: none !important;
    background: transparent !important;
  }

  :deep(.ant-collapse-item) {
    border: 1px solid #e8e8e8 !important;
    border-radius: 8px !important;
    margin-bottom: 16px !important;
    overflow: hidden !important;
  }

  /* 折叠面板Header打印优化 */
  :deep(.ant-collapse-header) {
    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%) !important;
    padding: 16px !important;
    border-bottom: 1px solid #e8e8e8 !important;
  }

  :deep(.ant-collapse-header:hover) {
    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%) !important;
  }

  /* 确保折叠面板在打印时展开 */
  :deep(.ant-collapse-content-box) {
    display: block !important;
    max-height: none !important;
    padding: 16px !important;
  }

  :deep(.ant-collapse-content) {
    overflow: visible !important;
  }

  /* Day header打印优化 */
  .day-header {
    display: flex !important;
    justify-content: space-between !important;
    align-items: flex-start !important;
    width: 100% !important;
    gap: 12px !important;
    flex-wrap: wrap !important;
  }

  .day-header-left {
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    flex-shrink: 0 !important;
  }

  .day-header-right {
    display: flex !important;
    align-items: flex-start !important;
    flex-wrap: wrap !important;
    gap: 8px !important;
    justify-content: flex-start !important;
    flex: 1 !important;
    flex-direction: column !important;
  }

  .day-stats {
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    flex-wrap: wrap !important;
  }

  .day-description {
    max-width: 100% !important;
    width: 100% !important;
    white-space: normal !important;
    word-break: break-word !important;
    display: inline-block !important;
    margin-top: 4px !important;
  }

  .day-title {
    font-size: 16px !important;
    font-weight: 600 !important;
    color: #1a1a1a !important;
  }

  .day-date {
    font-size: 14px !important;
    color: #666 !important;
  }

  /* 标签打印优化 */
  :deep(.ant-tag) {
    display: inline-flex !important;
    align-items: center !important;
    white-space: nowrap !important;
    margin: 2px 4px 2px 0 !important;
    border-radius: 6px !important;
    font-size: 12px !important;
    padding: 4px 10px !important;
  }

  /* 景点卡片打印优化 */
  .attraction-card {
    border: 1px solid #e8e8e8 !important;
    border-radius: 8px !important;
    margin-bottom: 12px !important;
    page-break-inside: avoid;
  }

  .attraction-image-container {
    height: 100px !important;
    background: linear-gradient(135deg, #f3e8ff 0%, #ede9fe 100%) !important;
    border: 1px solid rgba(139, 92, 246, 0.1) !important;
  }

  /* 图片打印优化 */
  img {
    max-width: 100% !important;
    height: auto !important;
    page-break-inside: avoid;
  }

  /* 天气卡片打印优化 */
  .weather-sunny,
  .weather-cloudy,
  .weather-rainy,
  .weather-snowy {
    border: 1px solid #e8e8e8 !important;
    border-radius: 8px !important;
    page-break-inside: avoid;
  }

  /* 预算卡片打印优化 */
  .ant-statistic {
    text-align: center !important;
  }

  /* 分页控制 */
  .section-card,
  .attraction-card {
    page-break-inside: avoid !important;
  }

  /* 确保文字可见 */
  p, h4 {
    color: #333 !important;
  }
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .result-container {
    padding: 16px;
  }
  
  .sidebar {
    margin-bottom: 20px;
  }
  
  .section-card {
    margin-bottom: 16px;
  }
  
  .attraction-card {
    flex-direction: column;
  }
  
  .attraction-image-container {
    width: 100%;
    height: 200px;
    background: linear-gradient(135deg, #f3e8ff 0%, #ede9fe 100%);
    border: 1px solid rgba(139, 92, 246, 0.1);
  }
  
  .attraction-info {
    flex: 1;
    margin-top: 12px;
  }
}

@media (max-width: 768px) {
  .result-container {
    padding: 12px;
  }
  
  .result-content {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    margin-bottom: 16px;
  }
  
  .main-content {
    width: 100%;
  }
  
  .header-actions {
    flex-direction: column;
    gap: 8px;
  }
  
  .header-actions .ant-btn {
    width: 100%;
  }
  
  .attraction-card {
    padding: 12px;
  }
  
  .attraction-image-container {
    height: 180px;
    background: linear-gradient(135deg, #f3e8ff 0%, #ede9fe 100%);
    border: 1px solid rgba(139, 92, 246, 0.1);
  }
  
  .day-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .day-header-right {
    align-items: flex-start;
    width: 100%;
  }
  
  .day-stats {
    flex-wrap: wrap;
  }
  
  .day-description {
    max-width: 100% !important;
  }
}

@media (max-width: 480px) {
  .result-container {
    padding: 8px;
  }
  
  .section-card {
    margin-bottom: 12px;
  }
  
  .attraction-card {
    padding: 8px;
  }
  
  .attraction-image-container {
    height: 150px;
    background: linear-gradient(135deg, #f3e8ff 0%, #ede9fe 100%);
    border: 1px solid rgba(139, 92, 246, 0.1);
  }
  
  .attraction-info h4 {
    font-size: 14px;
  }
  
  .attraction-info p {
    font-size: 12px;
  }
  
  .day-title {
    font-size: 14px;
  }
  
  .day-date {
    font-size: 12px;
  }
  
  .day-description {
    font-size: 12px;
    padding: 4px 8px;
  }
  
  .loading-details {
    padding: 8px;
  }
  
  .loading-detail-item {
    font-size: 11px;
  }
}

/* 优化字体颜色，提高可读性 */
h4 {
  color: #1a1a1a !important;
  font-weight: 600;
}

p {
  color: #333 !important;
  line-height: 1.5;
}

.attraction-info p {
  color: #4b5563 !important;
}

/* 确保表单标签和其他文本元素的颜色清晰 */
.ant-form-item-label > label {
  color: #1a1a1a !important;
  font-weight: 500;
}

.ant-select-selection-item,
.ant-input {
  color: #1a1a1a !important;
}
</style>
