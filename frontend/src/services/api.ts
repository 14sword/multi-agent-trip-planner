import axios from 'axios'
import type { TripPlanRequest, TripPlan } from '../types'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.request.use(
  config => {
    console.log('发送请求：', config)
    return config
  },
  error => Promise.reject(error)
)

api.interceptors.response.use(
  response => {
    console.log('收到响应：', response)
    return response
  },
  error => {
    console.error('请求失败：', error)
    
    // 增强错误处理
    let errorMessage = '网络请求失败，请检查网络连接'
    let errorDetails = ''
    let solution = ''
    
    if (error.response) {
      // 服务器返回错误
      const status = error.response.status
      const data = error.response.data
      
      switch (status) {
        case 400:
          errorMessage = '请求参数错误'
          errorDetails = data.detail || '请检查输入参数'
          solution = '请检查您输入的城市名称和日期是否正确'
          break
        case 401:
          errorMessage = '未授权访问'
          errorDetails = '需要登录'
          solution = '请重新登录后再试'
          break
        case 403:
          errorMessage = '访问被拒绝'
          errorDetails = '没有权限执行此操作'
          solution = '请联系管理员'
          break
        case 404:
          errorMessage = '接口不存在'
          errorDetails = '请求的接口不存在'
          solution = '请刷新页面后重试'
          break
        case 500:
          errorMessage = '服务器内部错误'
          errorDetails = data.detail || '服务器处理请求时发生错误'
          solution = '请稍后重试，或联系技术支持'
          break
        case 502:
          errorMessage = '网关错误'
          errorDetails = '服务器暂时不可用'
          solution = '请稍后重试'
          break
        case 503:
          errorMessage = '服务不可用'
          errorDetails = '服务器暂时过载'
          solution = '请稍后重试'
          break
        case 504:
          errorMessage = '网关超时'
          errorDetails = '服务器响应超时'
          solution = '请检查网络连接后重试'
          break
        default:
          errorMessage = `服务器错误 (${status})`
          errorDetails = data.detail || '未知错误'
          solution = '请稍后重试'
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      errorMessage = '服务器无响应'
      errorDetails = '请求已发送但未收到服务器响应'
      solution = '请检查网络连接和服务器状态'
    } else {
      // 请求配置错误
      errorMessage = '请求配置错误'
      errorDetails = error.message || '未知错误'
      solution = '请刷新页面后重试'
    }
    
    // 增强错误对象
    const enhancedError = {
      ...error,
      enhanced: true,
      errorMessage,
      errorDetails,
      solution
    }
    
    return Promise.reject(enhancedError)
  }
)

export const generateTripPlan = async (request: TripPlanRequest): Promise<TripPlan> => {
  const response = await api.post<TripPlan>('/trip/plan', request)
  return response.data
}

export const editTripPlan = async (tripPlan: TripPlan): Promise<TripPlan> => {
  const response = await api.post<TripPlan>('/trip/edit', { trip_plan: tripPlan })
  return response.data
}

export default api
