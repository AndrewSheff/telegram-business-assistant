import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  Calendar,
  Scissors,
  Clock,
  Users,
  HelpCircle,
  BookOpen,
  Send,
  MessageSquare,
  Settings,
  UserCog,
  LogOut,
  Menu,
  X,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { useAuth } from '@/contexts/AuthContext'
import { cn } from '@/lib/utils'

/** Элемент навигации в сайдбаре */
interface NavItem {
  label: string
  path: string
  icon: React.ElementType
  /** Показывать только для определенной роли */
  ownerOnly?: boolean
}

// Все пункты меню — порядок как в ТЗ
const navItems: NavItem[] = [
  { label: 'Дашборд', path: '/dashboard', icon: LayoutDashboard },
  { label: 'Записи', path: '/bookings', icon: Calendar },
  { label: 'Услуги', path: '/services', icon: Scissors },
  { label: 'Расписание', path: '/schedule', icon: Clock },
  { label: 'Клиенты', path: '/clients', icon: Users },
  { label: 'FAQ', path: '/faq', icon: HelpCircle },
  { label: 'База знаний', path: '/knowledge', icon: BookOpen },
  { label: 'Рассылки', path: '/broadcasts', icon: Send },
  { label: 'Чат', path: '/chat', icon: MessageSquare },
  { label: 'Настройки', path: '/settings', icon: Settings, ownerOnly: true },
  { label: 'Пользователи', path: '/users', icon: UserCog, ownerOnly: true },
]

/**
 * Основной лейаут админки — сайдбар + контент
 * На мобиле сайдбар сворачивается в гамбургер-меню
 */
export default function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // Фильтруем пункты меню по роли
  const visibleItems = navItems.filter(
    (item) => !item.ownerOnly || user?.role === 'owner'
  )

  // Обработчик логаута
  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // Закрываем сайдбар при клике на ссылку (мобилка)
  const handleNavClick = () => {
    setSidebarOpen(false)
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* Оверлей на мобилке — затемнение за сайдбаром */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Боковая панель */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex w-64 flex-col bg-slate-900 text-white transition-transform duration-200 lg:static lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Шапка сайдбара */}
        <div className="flex h-16 items-center justify-between px-4">
          <h1 className="text-lg font-bold tracking-tight">Business Assistant</h1>
          <button
            onClick={() => setSidebarOpen(false)}
            className="rounded-md p-1 hover:bg-slate-800 lg:hidden"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <Separator className="bg-slate-700" />

        {/* Навигация */}
        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
          {visibleItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={handleNavClick}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-slate-700/80 text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                )
              }
            >
              <item.icon className="h-5 w-5 shrink-0" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <Separator className="bg-slate-700" />

        {/* Инфо о юзере + кнопка выхода */}
        <div className="p-4">
          <div className="mb-3">
            <p className="text-sm font-medium text-white truncate">{user?.name}</p>
            <p className="text-xs text-slate-400 truncate">{user?.email}</p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            className="w-full justify-start gap-2 text-slate-300 hover:bg-slate-800 hover:text-white"
          >
            <LogOut className="h-4 w-4" />
            Выйти
          </Button>
        </div>
      </aside>

      {/* Основной контент */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Мобильный хедер с гамбургером */}
        <header className="flex h-16 items-center gap-4 border-b bg-white px-4 lg:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            className="rounded-md p-2 hover:bg-gray-100"
          >
            <Menu className="h-5 w-5" />
          </button>
          <h1 className="text-lg font-semibold">Business Assistant</h1>
        </header>

        {/* Контентная область — тут рендерятся вложенные маршруты */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
