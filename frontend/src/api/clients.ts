import apiClient from './client'
import type { Client, ClientListResponse, Booking, ChatMessage } from '../types'

export interface ClientParams {
  search?: string
  page?: number
  size?: number
}

export const getClients = async (params?: ClientParams): Promise<ClientListResponse> => {
  const { data } = await apiClient.get<ClientListResponse>('/clients', { params })
  return data
}

export const getClient = async (id: string): Promise<Client> => {
  const { data } = await apiClient.get<Client>(`/clients/${id}`)
  return data
}

export const updateClient = async (id: string, clientData: Partial<Client>): Promise<void> => {
  await apiClient.put(`/clients/${id}`, clientData)
}

export const getClientHistory = async (
  id: string,
): Promise<{ bookings: Booking[]; messages: ChatMessage[] }> => {
  const { data } = await apiClient.get<{ bookings: Booking[]; messages: ChatMessage[] }>(
    `/clients/${id}/history`,
  )
  return data
}
