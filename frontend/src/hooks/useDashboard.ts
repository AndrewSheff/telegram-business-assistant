import { useQuery } from '@tanstack/react-query'
import { fetchDashboardStats, fetchActivityChart, fetchTopServices, fetchTopQuestions } from '@/api/dashboard'

export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: fetchDashboardStats,
  })
}

export function useDashboardActivity(days?: number) {
  return useQuery({
    queryKey: ['dashboard', 'activity', days],
    queryFn: () => fetchActivityChart(days),
  })
}

export function useTopServices(limit?: number) {
  return useQuery({
    queryKey: ['dashboard', 'top-services', limit],
    queryFn: () => fetchTopServices(limit),
  })
}

export function useTopQuestions(limit?: number) {
  return useQuery({
    queryKey: ['dashboard', 'top-questions', limit],
    queryFn: () => fetchTopQuestions(limit),
  })
}
