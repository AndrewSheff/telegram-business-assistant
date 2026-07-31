import apiClient from './client'
import type { HandoffClient, ChatMessage } from '../types'

export const getActiveHandoffs = async (): Promise<HandoffClient[]> => {
  const { data } = await apiClient.get<HandoffClient[]>('/chat/handoffs')
  return data
}

export const getMessages = async (clientId: string): Promise<ChatMessage[]> => {
  const { data } = await apiClient.get<ChatMessage[]>(`/chat/${clientId}/messages`)
  return data
}

export const sendReply = async (clientId: string, content: string): Promise<void> => {
  await apiClient.post(`/chat/${clientId}/reply`, { content })
}

export const closeHandoff = async (clientId: string): Promise<void> => {
  await apiClient.post(`/chat/${clientId}/close`)
}
