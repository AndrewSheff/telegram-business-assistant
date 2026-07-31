import apiClient from './client'
import type { FaqItem } from '../types'

export const getFaq = async (): Promise<FaqItem[]> => {
  const { data } = await apiClient.get<FaqItem[]>('/faq')
  return data
}

export const createFaq = async (faqData: Partial<FaqItem>): Promise<FaqItem> => {
  const { data } = await apiClient.post<FaqItem>('/faq', faqData)
  return data
}

export const updateFaq = async (id: string, faqData: Partial<FaqItem>): Promise<FaqItem> => {
  const { data } = await apiClient.put<FaqItem>(`/faq/${id}`, faqData)
  return data
}

export const deleteFaq = async (id: string): Promise<void> => {
  await apiClient.delete(`/faq/${id}`)
}
