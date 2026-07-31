import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getActiveHandoffs, getMessages, sendReply, closeHandoff } from '@/api/chat'

export function useActiveHandoffs() {
  return useQuery({
    queryKey: ['chat', 'handoffs'],
    queryFn: getActiveHandoffs,
    refetchInterval: 5000,
  })
}

export function useMessages(clientId: string) {
  return useQuery({
    queryKey: ['chat', 'messages', clientId],
    queryFn: () => getMessages(clientId),
    enabled: !!clientId,
    refetchInterval: 3000,
  })
}

export function useSendReply() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ clientId, content }: { clientId: string; content: string }) =>
      sendReply(clientId, content),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['chat', 'messages', variables.clientId] })
    },
  })
}

export function useCloseHandoff() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (clientId: string) => closeHandoff(clientId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat'] })
    },
  })
}
