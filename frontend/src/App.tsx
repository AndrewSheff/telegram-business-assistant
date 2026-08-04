import { Component, type ReactNode } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'sonner'
import { AuthProvider } from '@/contexts/AuthContext'
import ProtectedRoute from '@/components/layout/ProtectedRoute'
import AppLayout from '@/components/layout/AppLayout'

/** Ловит ошибки рендера — чтобы все приложение не падало */
class ErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-center">
            <h1 className="mb-2 text-2xl font-bold">Что-то пошло не так</h1>
            <p className="mb-4 text-gray-600">
              Произошла непредвиденная ошибка
            </p>
            <button
              onClick={() => {
                this.setState({ hasError: false })
                window.location.href = '/'
              }}
              className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
            >
              Вернуться на главную
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

// Страницы
import LoginPage from '@/pages/LoginPage'
import ChangePasswordPage from '@/pages/ChangePasswordPage'
import DashboardPage from '@/pages/DashboardPage'
import BookingsPage from '@/pages/BookingsPage'
import ServicesPage from '@/pages/ServicesPage'
import SchedulePage from '@/pages/SchedulePage'
import ClientsPage from '@/pages/ClientsPage'
import ClientDetailPage from '@/pages/ClientDetailPage'
import FaqPage from '@/pages/FaqPage'
import KnowledgePage from '@/pages/KnowledgePage'
import BroadcastsPage from '@/pages/BroadcastsPage'
import BroadcastCreatePage from '@/pages/BroadcastCreatePage'
import ChatPage from '@/pages/ChatPage'
import SettingsPage from '@/pages/SettingsPage'
import UsersPage from '@/pages/UsersPage'
import NotFoundPage from '@/pages/NotFoundPage'

/**
 * Корневой компонент приложения — роутинг и провайдеры
 * Все маршруты тут, защищенные обернуты в ProtectedRoute
 */
export default function App() {
  return (
    <ErrorBoundary>
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Публичные маршруты */}
          <Route path="/login" element={<LoginPage />} />

          {/* Смена пароля — защищенная, но без лейаута (отдельная страница) */}
          <Route
            path="/change-password"
            element={
              <ProtectedRoute>
                <ChangePasswordPage />
              </ProtectedRoute>
            }
          />

          {/* Корень — перенаправляем на дашборд */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />

          {/* Защищенные маршруты с лейаутом админки */}
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/bookings" element={<BookingsPage />} />
            <Route path="/services" element={<ServicesPage />} />
            <Route path="/schedule" element={<SchedulePage />} />
            <Route path="/clients" element={<ClientsPage />} />
            <Route path="/clients/:id" element={<ClientDetailPage />} />
            <Route path="/faq" element={<FaqPage />} />
            <Route path="/knowledge" element={<KnowledgePage />} />
            <Route path="/broadcasts" element={<BroadcastsPage />} />
            <Route path="/broadcasts/new" element={<BroadcastCreatePage />} />
            <Route path="/chat" element={<ChatPage />} />

            {/* Маршруты только для владельца */}
            <Route
              path="/settings"
              element={
                <ProtectedRoute requiredRole="owner">
                  <SettingsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/users"
              element={
                <ProtectedRoute requiredRole="owner">
                  <UsersPage />
                </ProtectedRoute>
              }
            />
          </Route>

          {/* 404 — все остальное */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>

        {/* Тосты — уведомления поверх всего */}
        <Toaster position="top-right" richColors closeButton />
      </AuthProvider>
    </BrowserRouter>
    </ErrorBoundary>
  )
}
