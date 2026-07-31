import apiClient from './client'
import type { LoginResponse } from '@/types'

/** Логин — отправляем email и пароль, получаем токен */
export async function loginRequest(email: string, password: string): Promise<LoginResponse> {
  // Бэкенд ожидает form-data для OAuth2
  const formData = new URLSearchParams()
  formData.append('username', email)
  formData.append('password', password)

  const { data } = await apiClient.post<LoginResponse>('/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return data
}

/** Смена пароля — для первого входа или по желанию */
export async function changePasswordRequest(
  currentPassword: string,
  newPassword: string
): Promise<void> {
  await apiClient.post('/auth/change-password', {
    current_password: currentPassword,
    new_password: newPassword,
  })
}
