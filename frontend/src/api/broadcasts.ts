import apiClient from './client'
import type { Broadcast, BroadcastListResponse } from '../types'

export interface BroadcastParams {
  page?: number
  size?: number
}

export const getBroadcasts = async (params?: BroadcastParams): Promise<BroadcastListResponse> => {
  const { data } = await apiClient.get<BroadcastListResponse>('/broadcasts', { params })
  return data
}

export const createBroadcast = async (broadcastData: Partial<Broadcast>): Promise<Broadcast> => {
  const { data } = await apiClient.post<Broadcast>('/broadcasts', broadcastData)
  return data
}

export const getBroadcast = async (id: string): Promise<Broadcast> => {
  const { data } = await apiClient.get<Broadcast>(`/broadcasts/${id}`)
  return data
}

export const sendBroadcast = async (id: string): Promise<void> => {
  await apiClient.post(`/broadcasts/${id}/send`)
}

export const deleteBroadcast = async (id: string): Promise<void> => {
  await apiClient.delete(`/broadcasts/${id}`)
}
