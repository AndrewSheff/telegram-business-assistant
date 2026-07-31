import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Home } from 'lucide-react'

/**
 * Страница 404 — когда юзер забрел не туда
 * Простая, понятная, с кнопкой домой
 */
export default function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4 text-center">
      <h1 className="text-7xl font-bold text-primary">404</h1>
      <p className="mt-4 text-xl font-semibold text-foreground">Страница не найдена</p>
      <p className="mt-2 text-muted-foreground">
        Такой страницы не существует или она была удалена
      </p>
      <Button className="mt-6" render={<Link to="/dashboard" />}>
        <Home className="mr-2 h-4 w-4" />
        На главную
      </Button>
    </div>
  )
}
