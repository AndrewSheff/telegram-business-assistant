import apiClient from './client'
import type { Settings } from '../types'

export const getSettings = async (): Promise<Settings> => {
  const { data } = await apiClient.get<Settings>('/settings')
  return data
}

export const updateSettings = async (settingsData: Partial<Settings>): Promise<Settings> => {
  const { data } = await apiClient.put<Settings>('/settings', settingsData)
  return data
}
