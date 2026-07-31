import apiClient from './client'
import type { KnowledgeBlock } from '../types'

export const getKnowledge = async (): Promise<KnowledgeBlock[]> => {
  const { data } = await apiClient.get<KnowledgeBlock[]>('/knowledge')
  return data
}

export const createKnowledge = async (blockData: Partial<KnowledgeBlock>): Promise<KnowledgeBlock> => {
  const { data } = await apiClient.post<KnowledgeBlock>('/knowledge', blockData)
  return data
}

export const updateKnowledge = async (
  id: string,
  blockData: Partial<KnowledgeBlock>,
): Promise<KnowledgeBlock> => {
  const { data } = await apiClient.put<KnowledgeBlock>(`/knowledge/${id}`, blockData)
  return data
}

export const deleteKnowledge = async (id: string): Promise<void> => {
  await apiClient.delete(`/knowledge/${id}`)
}
