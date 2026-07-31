import apiClient from './client'
import type { DashboardStats, ActivityPoint, TopService, TopQuestion } from '@/types'

/** Получить общую статистику для дашборда */
export async function fetchDashboardStats(): Promise<DashboardStats> {
  const { data } = await apiClient.get<DashboardStats>('/dashboard/stats')
  return data
}

/** Получить данные активности за последние N дней */
export async function fetchActivityChart(days: number = 30): Promise<ActivityPoint[]> {
  const { data } = await apiClient.get<ActivityPoint[]>('/dashboard/activity', {
    params: { days },
  })
  return data
}

/** Получить топ услуг по количеству бронирований */
export async function fetchTopServices(limit: number = 5): Promise<TopService[]> {
  const { data } = await apiClient.get<TopService[]>('/dashboard/top-services', {
    params: { limit },
  })
  return data
}

/** Получить самые частые вопросы */
export async function fetchTopQuestions(limit: number = 5): Promise<TopQuestion[]> {
  const { data } = await apiClient.get<TopQuestion[]>('/dashboard/top-questions', {
    params: { limit },
  })
  return data
}
