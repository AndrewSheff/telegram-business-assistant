import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getKnowledge, createKnowledge, updateKnowledge, deleteKnowledge } from '@/api/knowledge'
import type { KnowledgeBlock } from '@/types'

export function useKnowledge() {
  return useQuery({
    queryKey: ['knowledge'],
    queryFn: getKnowledge,
  })
}

export function useCreateKnowledge() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<KnowledgeBlock>) => createKnowledge(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge'] })
    },
  })
}

export function useUpdateKnowledge() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<KnowledgeBlock> }) =>
      updateKnowledge(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge'] })
    },
  })
}

export function useDeleteKnowledge() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteKnowledge(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge'] })
    },
  })
}
