import apiClient from './client'
import type { WorkingHours, ScheduleException, TimeSlot } from '../types'

export const getWorkingHours = async (): Promise<WorkingHours[]> => {
  const { data } = await apiClient.get<WorkingHours[]>('/schedule/working-hours')
  return data
}

export const updateWorkingHours = async (hoursData: Partial<WorkingHours>[]): Promise<WorkingHours[]> => {
  const { data } = await apiClient.put<WorkingHours[]>('/schedule/working-hours', hoursData)
  return data
}

export const getExceptions = async (): Promise<ScheduleException[]> => {
  const { data } = await apiClient.get<ScheduleException[]>('/schedule/exceptions')
  return data
}

export const createException = async (exceptionData: Partial<ScheduleException>): Promise<ScheduleException> => {
  const { data } = await apiClient.post<ScheduleException>('/schedule/exceptions', exceptionData)
  return data
}

export const deleteException = async (id: string): Promise<void> => {
  await apiClient.delete(`/schedule/exceptions/${id}`)
}

export const getAvailableSlots = async (date: string, serviceId: string): Promise<TimeSlot[]> => {
  const { data } = await apiClient.get<TimeSlot[]>('/schedule/available-slots', {
    params: { date, service_id: serviceId },
  })
  return data
}
