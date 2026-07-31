import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'sonner'
import { AuthProvider } from '@/contexts/AuthContext'
import ProtectedRoute from '@/components/layout/ProtectedRoute'
import AppLayout from '@/components/layout/AppLayout'

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
  )
}
