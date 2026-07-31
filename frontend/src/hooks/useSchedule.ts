import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getWorkingHours,
  updateWorkingHours,
  getExceptions,
  createException,
  deleteException,
  getAvailableSlots,
} from '@/api/schedule'
import type { WorkingHours, ScheduleException } from '@/types'

export function useWorkingHours() {
  return useQuery({
    queryKey: ['working-hours'],
    queryFn: getWorkingHours,
  })
}

export function useUpdateWorkingHours() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<WorkingHours>[]) => updateWorkingHours(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['working-hours'] })
    },
  })
}

export function useScheduleExceptions() {
  return useQuery({
    queryKey: ['schedule-exceptions'],
    queryFn: getExceptions,
  })
}

export function useCreateException() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<ScheduleException>) => createException(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedule-exceptions'] })
    },
  })
}

export function useDeleteException() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteException(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedule-exceptions'] })
    },
  })
}

export function useAvailableSlots(date: string | undefined, serviceId: string | undefined) {
  return useQuery({
    queryKey: ['available-slots', date, serviceId],
    queryFn: () => getAvailableSlots(date!, serviceId!),
    enabled: !!date && !!serviceId,
  })
}
