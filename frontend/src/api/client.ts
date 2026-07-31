import axios from 'axios'
import { API_BASE_URL } from '@/lib/constants'

/**
 * Axios-клиент для работы с API
 * Автоматом цепляет токен к каждому запросу и обрабатывает 401
 */
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Перехватчик запросов — добавляем токен если есть
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Перехватчик ответов — если 401, выкидываем из сессии
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      // Перенаправляем на логин, но только если мы не на странице логина
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient
