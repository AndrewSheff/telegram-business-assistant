import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getBookings, getTodayBookings, getBooking, updateBookingStatus } from '@/api/bookings'
import type { BookingParams } from '@/api/bookings'
import type { BookingStatus } from '@/types'

export function useBookings(params?: BookingParams) {
  return useQuery({
    queryKey: ['bookings', params],
    queryFn: () => getBookings(params),
  })
}

export function useTodayBookings() {
  return useQuery({
    queryKey: ['bookings', 'today'],
    queryFn: getTodayBookings,
  })
}

export function useBooking(id: string) {
  return useQuery({
    queryKey: ['bookings', id],
    queryFn: () => getBooking(id),
    enabled: !!id,
  })
}

export function useUpdateBookingStatus() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: BookingStatus }) =>
      updateBookingStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookings'] })
    },
  })
}
