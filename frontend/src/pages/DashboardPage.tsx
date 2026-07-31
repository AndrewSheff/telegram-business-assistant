import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Users, UserPlus, Calendar, MessageSquare } from 'lucide-react'
import {
  useDashboardStats,
  useDashboardActivity,
  useTopServices,
  useTopQuestions,
} from '@/hooks/useDashboard'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { format, parseISO } from 'date-fns'
import { ru } from 'date-fns/locale'

// --- Карточка статистики ---

interface StatCardProps {
  title: string
  value: number | undefined
  icon: React.ElementType
  isLoading: boolean
}

/** Карточка с одной метрикой — число + иконка + подпись */
function StatCard({ title, value, icon: Icon, isLoading }: StatCardProps) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 p-6">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-primary/10">
          <Icon className="h-6 w-6 text-primary" />
        </div>
        <div>
          {isLoading ? (
            <Skeleton className="h-8 w-20 mb-1" />
          ) : (
            <p className="text-2xl font-bold">{value ?? 0}</p>
          )}
          <p className="text-sm text-muted-foreground">{title}</p>
        </div>
      </CardContent>
    </Card>
  )
}

// --- Бар-лист для топов ---

interface BarListItem {
  name: string
  value: number
}

interface BarListProps {
  data: BarListItem[]
  isLoading: boolean
}

/** Горизонтальный список с полосками — для топ-услуг и вопросов */
function BarList({ data, isLoading }: BarListProps) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="space-y-1">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-2 w-full" />
          </div>
        ))}
      </div>
    )
  }

  if (!data.length) {
    return <p className="text-sm text-muted-foreground py-4">Пока данных нет</p>
  }

  const maxValue = Math.max(...data.map((d) => d.value), 1)

  return (
    <div className="space-y-3">
      {data.map((item, idx) => (
        <div key={idx}>
          <div className="flex justify-between text-sm mb-1">
            <span className="truncate mr-2">{item.name}</span>
            <span className="shrink-0 font-medium text-muted-foreground">{item.value}</span>
          </div>
          <div className="h-2 rounded-full bg-muted overflow-hidden">
            <div
              className="h-full rounded-full bg-primary transition-all"
              style={{ width: `${(item.value / maxValue) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

// --- Основная страница дашборда ---

/**
 * Дашборд — главная страница админки
 * Показываем ключевые метрики, график активности и топы
 */
export default function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useDashboardStats()
  const { data: activity, isLoading: activityLoading } = useDashboardActivity(30)
  const { data: topServices, isLoading: servicesLoading } = useTopServices(5)
  const { data: topQuestions, isLoading: questionsLoading } = useTopQuestions(5)

  // Форматируем данные для графика
  const chartData = (activity ?? []).map((point) => ({
    ...point,
    // Красивая дата для тултипа
    formattedDate: (() => {
      try {
        return format(parseISO(point.date), 'd MMM', { locale: ru })
      } catch {
        return point.date
      }
    })(),
  }))

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Дашборд</h1>
        <p className="text-muted-foreground">Обзор вашего бизнеса</p>
      </div>

      {/* Карточки статистики — 4 штуки в ряд */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Всего клиентов"
          value={stats?.total_clients}
          icon={Users}
          isLoading={statsLoading}
        />
        <StatCard
          title="Новых за неделю"
          value={stats?.new_clients_week}
          icon={UserPlus}
          isLoading={statsLoading}
        />
        <StatCard
          title="Записей сегодня"
          value={stats?.bookings_today}
          icon={Calendar}
          isLoading={statsLoading}
        />
        <StatCard
          title="Ожидают оператора"
          value={stats?.pending_handoffs}
          icon={MessageSquare}
          isLoading={statsLoading}
        />
      </div>

      {/* График активности */}
      <Card>
        <CardHeader>
          <CardTitle>Активность за 30 дней</CardTitle>
        </CardHeader>
        <CardContent>
          {activityLoading ? (
            <Skeleton className="h-[300px] w-full" />
          ) : chartData.length === 0 ? (
            <div className="flex h-[300px] items-center justify-center text-muted-foreground">
              Пока данных для графика нет
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="bookingsGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="hsl(var(--chart-1))" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="hsl(var(--chart-1))" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis
                  dataKey="formattedDate"
                  tick={{ fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                  allowDecimals={false}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: '8px',
                    border: '1px solid hsl(var(--border))',
                    backgroundColor: 'hsl(var(--card))',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="bookings"
                  name="Записи"
                  stroke="hsl(var(--chart-1))"
                  fill="url(#bookingsGradient)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      {/* Два столбца — топ услуг и топ вопросов */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Популярные услуги</CardTitle>
          </CardHeader>
          <CardContent>
            <BarList
              data={(topServices ?? []).map((s) => ({
                name: s.service_name,
                value: s.count,
              }))}
              isLoading={servicesLoading}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Частые вопросы</CardTitle>
          </CardHeader>
          <CardContent>
            <BarList
              data={(topQuestions ?? []).map((q) => ({
                name: q.question,
                value: q.count,
              }))}
              isLoading={questionsLoading}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
