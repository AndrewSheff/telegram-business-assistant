import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getBroadcasts,
  getBroadcast,
  createBroadcast,
  sendBroadcast,
  deleteBroadcast,
} from '@/api/broadcasts'
import type { BroadcastParams } from '@/api/broadcasts'
import type { Broadcast } from '@/types'

export function useBroadcasts(params?: BroadcastParams) {
  return useQuery({
    queryKey: ['broadcasts', params],
    queryFn: () => getBroadcasts(params),
  })
}

export function useBroadcast(id: string) {
  return useQuery({
    queryKey: ['broadcasts', id],
    queryFn: () => getBroadcast(id),
    enabled: !!id,
  })
}

export function useCreateBroadcast() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<Broadcast>) => createBroadcast(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['broadcasts'] })
    },
  })
}

export function useSendBroadcast() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => sendBroadcast(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['broadcasts'] })
    },
  })
}

export function useDeleteBroadcast() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteBroadcast(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['broadcasts'] })
    },
  })
}
