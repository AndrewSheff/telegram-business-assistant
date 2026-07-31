import apiClient from './client'
import type { User } from '../types'

export const getUsers = async (): Promise<User[]> => {
  const { data } = await apiClient.get<User[]>('/users')
  return data
}

export const createUser = async (
  userData: Partial<User>,
): Promise<{ user: User; temp_password: string }> => {
  const { data } = await apiClient.post<{ user: User; temp_password: string }>('/users', userData)
  return data
}

export const updateUser = async (id: string, userData: Partial<User>): Promise<User> => {
  const { data } = await apiClient.put<User>(`/users/${id}`, userData)
  return data
}

export const deleteUser = async (id: string): Promise<void> => {
  await apiClient.delete(`/users/${id}`)
}

export const getProfile = async (): Promise<User> => {
  const { data } = await apiClient.get<User>('/users/me')
  return data
}

export const updateProfile = async (name: string): Promise<User> => {
  const { data } = await apiClient.put<User>('/users/me', { name })
  return data
}
