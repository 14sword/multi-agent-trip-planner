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

// 自动附加 JWT token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
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

// ====== 核心 ======
export const generateTripPlan = async (request: TripPlanRequest, signal?: AbortSignal): Promise<TripPlan> => {
  const response = await api.post<TripPlan>('/trip/plan', request, { signal })
  return response.data
}

// ====== 流式输出 ======
export type StreamEvent =
  | { type: 'progress'; message: string }
  | { type: 'result'; data: TripPlan }
  | { type: 'error'; message: string }

export const generateTripPlanStream = async (
  request: TripPlanRequest,
  onProgress: (message: string) => void,
  signal?: AbortSignal,
): Promise<TripPlan> => {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const token = localStorage.getItem('auth_token')
  if (token) headers['Authorization'] = `Bearer ${token}`

  const response = await fetch('/api/trip/plan/stream', {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
    signal,
  })

  if (!response.ok) {
    throw new ApiError('生成计划失败', response.status, '', '请稍后重试')
  }

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    let eventType = ''
    for (const line of lines) {
      if (line.startsWith('event: ')) {
        eventType = line.slice(7).trim()
      } else if (line.startsWith('data: ')) {
        const rawData = line.slice(6)
        if (eventType === 'progress') {
          onProgress(rawData)
        } else if (eventType === 'result') {
          return JSON.parse(rawData) as TripPlan
        } else if (eventType === 'error') {
          throw new ApiError(rawData, 500, '', '请稍后重试')
        }
        eventType = ''
      }
    }
  }
  throw new ApiError('连接中断', 0, '', '请稍后重试')
}

export const editTripPlan = async (tripPlan: TripPlan, signal?: AbortSignal): Promise<TripPlan> => {
  const response = await api.post<TripPlan>('/trip/edit', { trip_plan: tripPlan }, { signal })
  return response.data
}

// ====== 多方案 ======
export const generateVariants = async (request: TripPlanRequest, signal?: AbortSignal) => {
  const response = await api.post('/trip/plan/variants', request, { signal })
  return response.data as { variants: { variant: string; plan: TripPlan | null; error?: string }[] }
}

// ====== CRUD ======
export const getTrip = async (tripId: string): Promise<TripPlan> => {
  const response = await api.get<TripPlan>(`/trip/${tripId}`)
  return response.data
}

export const listTrips = async () => {
  const response = await api.get('/trip/list')
  return response.data as { trips: { id: string; city: string; start_date: string; end_date: string; days_count: number; share_token?: string; created_at: string }[] }
}

export const deleteTrip = async (tripId: string) => {
  const response = await api.delete(`/trip/${tripId}`)
  return response.data as { ok: boolean }
}

// ====== 分享 ======
export const getSharedTrip = async (shareToken: string): Promise<TripPlan> => {
  const response = await api.get<TripPlan>(`/trip/share/${shareToken}`)
  return response.data
}

// ====== 收藏 ======
export const addFavorite = async (tripId: string) => {
  const response = await api.post(`/trip/favorite/${tripId}`)
  return response.data as { ok: boolean; added: boolean }
}

export const removeFavorite = async (tripId: string) => {
  const response = await api.delete(`/trip/favorite/${tripId}`)
  return response.data as { ok: boolean }
}

export const listFavorites = async (): Promise<TripPlan[]> => {
  const response = await api.get('/trip/favorites/list')
  return (response.data as { favorites: TripPlan[] }).favorites
}

export default api
