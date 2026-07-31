import apiClient from './client'
import type { Booking, BookingListResponse, BookingStatus } from '../types'

export interface BookingParams {
  date_from?: string
  date_to?: string
  status?: BookingStatus
  client_id?: string
  service_id?: string
  page?: number
  size?: number
}

export const getBookings = async (params?: BookingParams): Promise<BookingListResponse> => {
  const { data } = await apiClient.get<BookingListResponse>('/bookings', { params })
  return data
}

export const getTodayBookings = async (): Promise<Booking[]> => {
  const { data } = await apiClient.get<Booking[]>('/bookings/today')
  return data
}

export const getBooking = async (id: string): Promise<Booking> => {
  const { data } = await apiClient.get<Booking>(`/bookings/${id}`)
  return data
}

export const updateBookingStatus = async (id: string, status: BookingStatus): Promise<void> => {
  await apiClient.patch(`/bookings/${id}/status`, { status })
}
