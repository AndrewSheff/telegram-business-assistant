import { useState } from 'react'
import { toast } from 'sonner'
import { Search, ChevronLeft, ChevronRight, Filter } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { useBookings, useUpdateBookingStatus } from '@/hooks/useBookings'
import { DEFAULT_PAGE_SIZE } from '@/lib/constants'
import type { BookingStatus } from '@/types'

/** Конфиг бейджей статусов — цвет и текст */
const STATUS_CONFIG: Record<BookingStatus, { label: string; className: string }> = {
  pending: {
    label: 'Ожидает',
    className: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  },
  confirmed: {
    label: 'Подтверждена',
    className: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  },
  completed: {
    label: 'Завершена',
    className: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  },
  cancelled: {
    label: 'Отменена',
    className: 'bg-gray-100 text-gray-600 dark:bg-gray-800/30 dark:text-gray-400',
  },
  no_show: {
    label: 'Не пришел',
    className: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  },
}

/**
 * Страница записей — все бронирования с фильтрами и статусами
 * Можно подтвердить, завершить, отменить или отметить неявку
 */
export default function BookingsPage() {
  // фильтры
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [page, setPage] = useState(1)

  // диалог подтверждения смены статуса
  const [statusAction, setStatusAction] = useState<{
    id: string
    status: BookingStatus
    label: string
  } | null>(null)

  const { data, isLoading } = useBookings({
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    status: (statusFilter as BookingStatus) || undefined,
    page,
    size: DEFAULT_PAGE_SIZE,
  })
  const updateStatus = useUpdateBookingStatus()

  const bookings = data?.items ?? []
  const totalPages = data ? Math.ceil(data.total / DEFAULT_PAGE_SIZE) : 0

  /** Смена статуса бронирования */
  const handleConfirmStatusChange = () => {
    if (!statusAction) return
    updateStatus.mutate(
      { id: statusAction.id, status: statusAction.status },
      {
        onSuccess: () => {
          toast.success(`Запись ${statusAction.label.toLowerCase()}`)
          setStatusAction(null)
        },
        onError: () => toast.error('Не удалось изменить статус записи'),
      },
    )
  }

  /** Открыть диалог смены статуса */
  const requestStatusChange = (id: string, status: BookingStatus, label: string) => {
    setStatusAction({ id, status, label })
  }

  /** Сбросить фильтры */
  const handleClearFilters = () => {
    setDateFrom('')
    setDateTo('')
    setStatusFilter('')
    setPage(1)
  }

  const hasFilters = dateFrom || dateTo || statusFilter

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Записи</h1>
        <p className="text-muted-foreground">Управление бронированиями клиентов</p>
      </div>

      {/* Фильтры */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground">Дата от</Label>
              <Input
                type="date"
                className="w-full sm:w-40"
                value={dateFrom}
                onChange={(e) => {
                  setDateFrom(e.target.value)
                  setPage(1)
                }}
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground">Дата до</Label>
              <Input
                type="date"
                className="w-full sm:w-40"
                value={dateTo}
                onChange={(e) => {
                  setDateTo(e.target.value)
                  setPage(1)
                }}
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs text-muted-foreground">Статус</Label>
              <Select
                value={statusFilter}
                onValueChange={(val) => {
                  setStatusFilter(val as string)
                  setPage(1)
                }}
              >
                <SelectTrigger className="w-full sm:w-44">
                  <SelectValue placeholder="Все статусы" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Все статусы</SelectItem>
                  <SelectItem value="pending">Ожидает</SelectItem>
                  <SelectItem value="confirmed">Подтверждена</SelectItem>
                  <SelectItem value="completed">Завершена</SelectItem>
                  <SelectItem value="cancelled">Отменена</SelectItem>
                  <SelectItem value="no_show">Не пришел</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {hasFilters && (
              <Button variant="ghost" size="sm" onClick={handleClearFilters}>
                <Filter className="mr-1 h-3.5 w-3.5" />
                Сбросить
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Таблица бронирований */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : bookings.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Search className="h-8 w-8 text-muted-foreground mb-2" />
              <p className="text-muted-foreground">
                {hasFilters ? 'По вашим фильтрам ничего не найдено' : 'Записей пока нет'}
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Клиент</TableHead>
                  <TableHead>Услуга</TableHead>
                  <TableHead>Дата</TableHead>
                  <TableHead className="hidden sm:table-cell">Время</TableHead>
                  <TableHead>Статус</TableHead>
                  <TableHead className="text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {bookings.map((booking) => {
                  const statusCfg = STATUS_CONFIG[booking.status]
                  return (
                    <TableRow key={booking.id}>
                      <TableCell className="font-medium">
                        {booking.client_name || 'Неизвестный'}
                      </TableCell>
                      <TableCell>{booking.service_name || '—'}</TableCell>
                      <TableCell>{booking.booking_date}</TableCell>
                      <TableCell className="hidden sm:table-cell">
                        {booking.start_time?.slice(0, 5)}
                        {booking.end_time ? ` — ${booking.end_time.slice(0, 5)}` : ''}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="secondary"
                          className={cn('border-0', statusCfg.className)}
                        >
                          {statusCfg.label}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1 flex-wrap">
                          {booking.status === 'pending' && (
                            <Button
                              variant="outline"
                              size="xs"
                              onClick={() =>
                                requestStatusChange(booking.id, 'confirmed', 'Подтверждена')
                              }
                            >
                              Подтвердить
                            </Button>
                          )}
                          {booking.status === 'confirmed' && (
                            <Button
                              variant="outline"
                              size="xs"
                              onClick={() =>
                                requestStatusChange(booking.id, 'completed', 'Завершена')
                              }
                            >
                              Завершить
                            </Button>
                          )}
                          {(booking.status === 'pending' || booking.status === 'confirmed') && (
                            <>
                              <Button
                                variant="ghost"
                                size="xs"
                                onClick={() =>
                                  requestStatusChange(booking.id, 'cancelled', 'Отменена')
                                }
                              >
                                Отменить
                              </Button>
                              <Button
                                variant="ghost"
                                size="xs"
                                className="text-destructive"
                                onClick={() =>
                                  requestStatusChange(booking.id, 'no_show', 'Отмечена как неявка')
                                }
                              >
                                Не пришел
                              </Button>
                            </>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Пагинация */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Страница {page} из {totalPages} (всего {data?.total ?? 0})
          </p>
          <div className="flex gap-1">
            <Button
              variant="outline"
              size="icon-sm"
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon-sm"
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Диалог подтверждения смены статуса */}
      <AlertDialog
        open={!!statusAction}
        onOpenChange={(open) => !open && setStatusAction(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Изменить статус записи?</AlertDialogTitle>
            <AlertDialogDescription>
              Запись будет переведена в статус «{statusAction?.label}».
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmStatusChange}>
              {updateStatus.isPending ? 'Применяем...' : 'Подтвердить'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
