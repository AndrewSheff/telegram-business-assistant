import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getFaq, createFaq, updateFaq, deleteFaq } from '@/api/faq'
import type { FaqItem } from '@/types'

export function useFaq() {
  return useQuery({
    queryKey: ['faq'],
    queryFn: getFaq,
  })
}

export function useCreateFaq() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<FaqItem>) => createFaq(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['faq'] })
    },
  })
}

export function useUpdateFaq() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<FaqItem> }) => updateFaq(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['faq'] })
    },
  })
}

export function useDeleteFaq() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteFaq(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['faq'] })
    },
  })
}
