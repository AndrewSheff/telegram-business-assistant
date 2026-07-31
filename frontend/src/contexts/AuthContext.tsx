import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { loginRequest } from '@/api/auth'
import type { User, UserRole } from '@/types'

// --- Вспомогательные штуки для JWT ---

/** Декодирует payload из JWT-токена без библиотек — просто base64 */
function decodeJwtPayload(token: string): JwtPayload | null {
  try {
    const base64Url = token.split('.')[1]
    if (!base64Url) return null
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    )
    return JSON.parse(jsonPayload)
  } catch {
    return null
  }
}

/** Структура payload в нашем JWT */
interface JwtPayload {
  sub: string
  email: string
  name: string
  role: UserRole
  must_change_password?: boolean
  exp: number
}

/** Проверяет не протух ли токен */
function isTokenExpired(token: string): boolean {
  const payload = decodeJwtPayload(token)
  if (!payload?.exp) return true
  return Date.now() >= payload.exp * 1000
}

/** Вытаскивает юзера из JWT — чтоб не дергать лишний раз бэкенд */
function userFromToken(token: string): User | null {
  const payload = decodeJwtPayload(token)
  if (!payload) return null
  return {
    id: payload.sub,
    email: payload.email,
    name: payload.name,
    role: payload.role,
    is_active: true,
    must_change_password: payload.must_change_password ?? false,
    created_at: '',
  }
}

// --- Контекст авторизации ---

interface AuthContextType {
  /** Текущий пользователь или null если не залогинен */
  user: User | null
  /** Залогинен ли пользователь */
  isAuthenticated: boolean
  /** Загружаемся ли мы при старте (проверяем токен) */
  isLoading: boolean
  /** Войти в систему */
  login: (email: string, password: string) => Promise<void>
  /** Выйти из системы */
  logout: () => void
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined)

// React Query клиент — один на все приложение
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60_000, // 5 минут данные считаются свежими
    },
  },
})

const TOKEN_KEY = 'access_token'

/** Провайдер авторизации — оборачивает все приложение */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // При загрузке проверяем есть ли живой токен в localStorage
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token && !isTokenExpired(token)) {
      const decoded = userFromToken(token)
      setUser(decoded)
    } else if (token) {
      // Токен протух — чистим
      localStorage.removeItem(TOKEN_KEY)
    }
    setIsLoading(false)
  }, [])

  // Логин — отправляем запрос и сохраняем токен
  const login = useCallback(async (email: string, password: string) => {
    const response = await loginRequest(email, password)
    localStorage.setItem(TOKEN_KEY, response.access_token)
    setUser(response.user)
  }, [])

  // Логаут — чистим все и отправляем на логин
  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setUser(null)
    queryClient.clear()
  }, [])

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
  }

  return (
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
    </QueryClientProvider>
  )
}

/** Хук для доступа к контексту авторизации — кидает ошибку если вне провайдера */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth надо использовать внутри AuthProvider, братан')
  }
  return context
}
