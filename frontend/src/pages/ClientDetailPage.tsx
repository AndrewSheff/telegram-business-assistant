import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { ArrowLeft, Save, Ban, UserCheck, MessageSquare } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useClient, useUpdateClient, useClientHistory } from '@/hooks/useClients'
import type { BookingStatus } from '@/types'

/** Цвета статусов бронирований — чтобы глазу было приятно */
const STATUS_COLORS: Record<BookingStatus, string> = {
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  confirmed: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  completed: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  cancelled: 'bg-gray-100 text-gray-600 dark:bg-gray-800/30 dark:text-gray-400',
  no_show: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
}

const STATUS_LABELS: Record<BookingStatus, string> = {
  pending: 'Ожидает',
  confirmed: 'Подтверждена',
  completed: 'Завершена',
  cancelled: 'Отменена',
  no_show: 'Не пришел',
}

/**
 * Карточка клиента — вся инфа, заметки, история записей и сообщений
 * Можно заблокировать, добавить заметки
 */
export default function ClientDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: client, isLoading } = useClient(id!)
  const updateClient = useUpdateClient()
  const { data: history, isLoading: historyLoading } = useClientHistory(id!)

  const [notes, setNotes] = useState<string | null>(null)

  // синхронизируем заметки при загрузке
  const currentNotes = notes ?? client?.notes ?? ''

  /** Сохранить заметки */
  const handleSaveNotes = () => {
    updateClient.mutate(
      { id: id!, data: { notes: currentNotes || null } },
      {
        onSuccess: () => toast.success('Заметки сохранены'),
        onError: () => toast.error('Не удалось сохранить заметки'),
      },
    )
  }

  /** Заблокировать / разблокировать клиента */
  const handleToggleBlock = () => {
    if (!client) return
    updateClient.mutate(
      { id: id!, data: { is_blocked: !client.is_blocked } },
      {
        onSuccess: () =>
          toast.success(client.is_blocked ? 'Клиент разблокирован' : 'Клиент заблокирован'),
        onError: () => toast.error('Не удалось изменить статус клиента'),
      },
    )
  }

  /** Форматируем дату покрасивее */
  const formatDateTime = (dateStr?: string | null) => {
    if (!dateStr) return '—'
    try {
      return new Date(dateStr).toLocaleString('ru-RU', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return dateStr
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (!client) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" onClick={() => navigate('/clients')}>
          <ArrowLeft className="mr-1.5 h-4 w-4" />
          Назад к списку
        </Button>
        <p className="text-muted-foreground">Клиент не найден</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Назад и заголовок */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/clients')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {client.first_name}
            {client.last_name ? ` ${client.last_name}` : ''}
          </h1>
          <p className="text-muted-foreground">
            Карточка клиента
          </p>
        </div>
      </div>

      {/* Инфо-карточка */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Информация</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Telegram ID</span>
              <span className="text-sm font-medium">{client.telegram_id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Юзернейм</span>
              <span className="text-sm font-medium">
                {client.username ? `@${client.username}` : '—'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Телефон</span>
              <span className="text-sm font-medium">{client.phone || '—'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Записей</span>
              <span className="text-sm font-medium">{client.bookings_count ?? 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Последнее взаимодействие</span>
              <span className="text-sm">{formatDateTime(client.last_interaction_at)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Статус</span>
              {client.is_blocked ? (
                <Badge variant="destructive">Заблокирован</Badge>
              ) : (
                <Badge variant="secondary">Активный</Badge>
              )}
            </div>
            <div className="pt-2">
              <Button
                variant={client.is_blocked ? 'outline' : 'destructive'}
                size="sm"
                className="w-full"
                onClick={handleToggleBlock}
                disabled={updateClient.isPending}
              >
                {client.is_blocked ? (
                  <>
                    <UserCheck className="mr-1.5 h-3.5 w-3.5" />
                    Разблокировать
                  </>
                ) : (
                  <>
                    <Ban className="mr-1.5 h-3.5 w-3.5" />
                    Заблокировать
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Заметки */}
        <Card>
          <CardHeader>
            <CardTitle>Заметки</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Textarea
              value={currentNotes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Заметки про клиента — что угодно для себя"
              className="min-h-[120px]"
            />
            <Button
              size="sm"
              onClick={handleSaveNotes}
              disabled={updateClient.isPending || currentNotes === (client.notes ?? '')}
            >
              <Save className="mr-1.5 h-3.5 w-3.5" />
              {updateClient.isPending ? 'Сохраняем...' : 'Сохранить заметки'}
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Вкладки: записи и сообщения */}
      <Tabs defaultValue="bookings">
        <TabsList>
          <TabsTrigger value="bookings">Записи</TabsTrigger>
          <TabsTrigger value="messages">Сообщения</TabsTrigger>
        </TabsList>

        {/* Записи клиента */}
        <TabsContent value="bookings">
          <Card>
            <CardContent className="p-0">
              {historyLoading ? (
                <div className="p-6 space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <Skeleton key={i} className="h-10 w-full" />
                  ))}
                </div>
              ) : !history?.bookings?.length ? (
                <div className="py-8 text-center text-muted-foreground text-sm">
                  У этого клиента пока нет записей
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Услуга</TableHead>
                      <TableHead>Дата</TableHead>
                      <TableHead className="hidden sm:table-cell">Время</TableHead>
                      <TableHead>Статус</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {history.bookings.map((booking) => (
                      <TableRow key={booking.id}>
                        <TableCell className="font-medium">
                          {booking.service_name || '—'}
                        </TableCell>
                        <TableCell>{booking.booking_date}</TableCell>
                        <TableCell className="hidden sm:table-cell">
                          {booking.start_time?.slice(0, 5)} — {booking.end_time?.slice(0, 5)}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant="secondary"
                            className={cn(
                              'border-0',
                              STATUS_COLORS[booking.status],
                            )}
                          >
                            {STATUS_LABELS[booking.status]}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Сообщения — чат-подобный вид */}
        <TabsContent value="messages">
          <Card>
            <CardContent className="p-4">
              {historyLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <Skeleton key={i} className="h-16 w-3/4" />
                  ))}
                </div>
              ) : !history?.messages?.length ? (
                <div className="py-8 text-center text-sm text-muted-foreground">
                  <MessageSquare className="h-6 w-6 mx-auto mb-2 opacity-50" />
                  Сообщений пока нет
                </div>
              ) : (
                <div className="space-y-3 max-h-[500px] overflow-y-auto">
                  {history.messages.map((msg) => {
                    const isUser = msg.role === 'user'
                    const isBot = msg.role === 'assistant' || msg.role === 'bot'
                    return (
                      <div
                        key={msg.id}
                        className={cn(
                          'flex',
                          isUser ? 'justify-end' : 'justify-start',
                        )}
                      >
                        <div
                          className={cn(
                            'max-w-[75%] rounded-lg px-3 py-2 text-sm',
                            isUser
                              ? 'bg-primary text-primary-foreground'
                              : isBot
                                ? 'bg-muted'
                                : 'bg-blue-100 dark:bg-blue-900/30',
                          )}
                        >
                          <div className="mb-1">
                            <span className="text-xs opacity-70">
                              {isUser ? 'Клиент' : isBot ? 'Бот' : 'Оператор'}
                            </span>
                          </div>
                          <p className="whitespace-pre-wrap break-words">{msg.content}</p>
                          <p className="text-xs opacity-50 mt-1">
                            {formatDateTime(msg.created_at)}
                          </p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
