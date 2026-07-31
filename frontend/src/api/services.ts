import apiClient from './client'
import type { Service, ServiceCategory } from '../types'

export const getServices = async (): Promise<Service[]> => {
  const { data } = await apiClient.get<Service[]>('/services')
  return data
}

export const createService = async (serviceData: Partial<Service>): Promise<Service> => {
  const { data } = await apiClient.post<Service>('/services', serviceData)
  return data
}

export const updateService = async (id: string, serviceData: Partial<Service>): Promise<Service> => {
  const { data } = await apiClient.put<Service>(`/services/${id}`, serviceData)
  return data
}

export const deleteService = async (id: string): Promise<void> => {
  await apiClient.delete(`/services/${id}`)
}

export const getCategories = async (): Promise<ServiceCategory[]> => {
  const { data } = await apiClient.get<ServiceCategory[]>('/services/categories')
  return data
}

export const createCategory = async (categoryData: Partial<ServiceCategory>): Promise<ServiceCategory> => {
  const { data } = await apiClient.post<ServiceCategory>('/services/categories', categoryData)
  return data
}

export const updateCategory = async (id: string, categoryData: Partial<ServiceCategory>): Promise<ServiceCategory> => {
  const { data } = await apiClient.put<ServiceCategory>(`/services/categories/${id}`, categoryData)
  return data
}

export const deleteCategory = async (id: string): Promise<void> => {
  await apiClient.delete(`/services/categories/${id}`)
}
