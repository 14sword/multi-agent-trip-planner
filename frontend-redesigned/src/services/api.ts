import axios, { type AxiosError } from 'axios'
import type { TripPlanRequest, TripPlan } from '../types'

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public details: string,
    public solution: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

const api = axios.create({
  baseURL: '/api',
  timeout: 300000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  response => response,
  (error: AxiosError<{ detail?: string }>) => {
    let message = '网络请求失败，请检查网络连接'
    let details = ''
    let solution = ''

    if (error.response) {
      const status = error.response.status
      const data = error.response.data
      details = data?.detail || ''

      if (status === 429) {
        message = '请求过于频繁'
        details = details || '请稍后再试'
        solution = '等待1分钟后重试'
      } else if (status === 500) {
        message = '服务器内部错误'
        solution = '请稍后重试'
      } else if (status === 422) {
        message = '输入参数有误'
        solution = '请检查城市名称和日期格式'
      } else {
        message = `请求失败 (${status})`
        solution = '请稍后重试'
      }
    } else if (error.code === 'ECONNABORTED') {
      message = '请求超时'
      solution = '服务器响应时间过长，请稍后重试'
    }

    return Promise.reject(new ApiError(message, error.response?.status || 0, details, solution))
  },
)

export const generateTripPlan = async (request: TripPlanRequest, signal?: AbortSignal): Promise<TripPlan> => {
  const response = await api.post<TripPlan>('/trip/plan', request, { signal })
  return response.data
}

export const editTripPlan = async (tripPlan: TripPlan, signal?: AbortSignal): Promise<TripPlan> => {
  const response = await api.post<TripPlan>('/trip/edit', { trip_plan: tripPlan }, { signal })
  return response.data
}

export default api
