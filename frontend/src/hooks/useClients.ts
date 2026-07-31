import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getClients, getClient, updateClient, getClientHistory } from '@/api/clients'
import type { ClientParams } from '@/api/clients'
import type { Client } from '@/types'

export function useClients(params?: ClientParams) {
  return useQuery({
    queryKey: ['clients', params],
    queryFn: () => getClients(params),
  })
}

export function useClient(id: string) {
  return useQuery({
    queryKey: ['clients', id],
    queryFn: () => getClient(id),
    enabled: !!id,
  })
}

export function useUpdateClient() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Client> }) => updateClient(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] })
    },
  })
}

export function useClientHistory(id: string) {
  return useQuery({
    queryKey: ['clients', id, 'history'],
    queryFn: () => getClientHistory(id),
    enabled: !!id,
  })
}
