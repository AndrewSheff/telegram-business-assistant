import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import type { UserRole } from '@/types'

interface ProtectedRouteProps {
  children: React.ReactNode
  /** Какая роль нужна для доступа (необязательно) */
  requiredRole?: UserRole
}

/**
 * Защищенный маршрут — не пускает без авторизации
 * Если юзер должен сменить пароль — редиректит на смену
 * Если нужна определенная роль — проверяет
 */
export default function ProtectedRoute({ children, requiredRole }: ProtectedRouteProps) {
  const { user, isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  // Пока грузимся — показываем лоадер, чтоб не мелькало
  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    )
  }

  // Не залогинен — на страницу логина
  if (!isAuthenticated || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Надо сменить пароль — отправляем на смену (но не зацикливаем)
  if (user.must_change_password && location.pathname !== '/change-password') {
    return <Navigate to="/change-password" replace />
  }

  // Проверка роли — если нужна определенная и у юзера не та
  if (requiredRole && user.role !== requiredRole) {
    return <Navigate to="/dashboard" replace />
  }

  return <>{children}</>
}
