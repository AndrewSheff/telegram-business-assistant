import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { Plus, Send, Trash2, ChevronLeft, ChevronRight, Radio } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
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
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { useBroadcasts, useSendBroadcast, useDeleteBroadcast } from '@/hooks/useBroadcasts'
import { DEFAULT_PAGE_SIZE } from '@/lib/constants'
import type { BroadcastStatus, BroadcastSegment } from '@/types'

/** Конфиг бейджей статусов рассылки */
const STATUS_CONFIG: Record<BroadcastStatus, { label: string; className: string }> = {
  draft: {
    label: 'Черновик',
    className: 'bg-gray-100 text-gray-600 dark:bg-gray-800/30 dark:text-gray-400',
  },
  scheduled: {
    label: 'Запланирована',
    className: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
  },
  sending: {
    label: 'Отправляется',
    className: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  },
  completed: {
    label: 'Завершена',
    className: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  },
  failed: {
    label: 'Ошибка',
    className: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  },
}

/** Названия сегментов по-русски */
const SEGMENT_LABELS: Record<BroadcastSegment, string> = {
  all: 'Все',
  recent: 'Недавние',
  inactive: 'Неактивные',
}

/**
 * Страница рассылок — список рассылок с управлением
 * Можно отправлять черновики и удалять
 */
export default function BroadcastsPage() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [sendId, setSendId] = useState<string | null>(null)
  const [deleteId, setDeleteId] = useState<string | null>(null)

  const { data, isLoading } = useBroadcasts({ page, size: DEFAULT_PAGE_SIZE })
  const sendBroadcast = useSendBroadcast()
  const deleteBroadcast = useDeleteBroadcast()

  const broadcasts = data?.items ?? []
  const totalPages = data ? Math.ceil(data.total / DEFAULT_PAGE_SIZE) : 0

  /** Отправить рассылку */
  const handleConfirmSend = () => {
    if (!sendId) return
    sendBroadcast.mutate(sendId, {
      onSuccess: () => {
        toast.success('Рассылка запущена')
        setSendId(null)
      },
      onError: () => toast.error('Не удалось запустить рассылку'),
    })
  }

  /** Удалить рассылку */
  const handleConfirmDelete = () => {
    if (!deleteId) return
    deleteBroadcast.mutate(deleteId, {
      onSuccess: () => {
        toast.success('Рассылка удалена')
        setDeleteId(null)
      },
      onError: () => toast.error('Не удалось удалить рассылку'),
    })
  }

  /** Форматируем дату */
  const formatDate = (dateStr?: string | null) => {
    if (!dateStr) return '—'
    try {
      return new Date(dateStr).toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return dateStr
    }
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Рассылки</h1>
          <p className="text-muted-foreground">Массовые сообщения клиентам через бота</p>
        </div>
        <Button onClick={() => navigate('/broadcasts/new')}>
          <Plus className="mr-1.5 h-4 w-4" />
          Новая рассылка
        </Button>
      </div>

      {/* Таблица рассылок */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : broadcasts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Radio className="h-8 w-8 text-muted-foreground mb-2" />
              <p className="text-muted-foreground mb-4">Рассылок пока нет</p>
              <Button onClick={() => navigate('/broadcasts/new')}>
                <Plus className="mr-1.5 h-4 w-4" />
                Создать первую рассылку
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Название</TableHead>
                  <TableHead className="hidden sm:table-cell">Сегмент</TableHead>
                  <TableHead>Статус</TableHead>
                  <TableHead className="hidden md:table-cell">Отправлено</TableHead>
                  <TableHead className="hidden sm:table-cell">Создана</TableHead>
                  <TableHead className="text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {broadcasts.map((broadcast) => {
                  const statusCfg = STATUS_CONFIG[broadcast.status]
                  return (
                    <TableRow key={broadcast.id}>
                      <TableCell className="font-medium max-w-[200px] truncate">
                        {broadcast.title}
                      </TableCell>
                      <TableCell className="hidden sm:table-cell">
                        <Badge variant="outline">
                          {SEGMENT_LABELS[broadcast.segment] ?? broadcast.segment}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="secondary"
                          className={cn('border-0', statusCfg.className)}
                        >
                          {statusCfg.label}
                        </Badge>
                      </TableCell>
                      <TableCell className="hidden md:table-cell">
                        {broadcast.status === 'draft'
                          ? '—'
                          : `${broadcast.sent_count} / ${broadcast.total_count}`}
                        {broadcast.failed_count > 0 && (
                          <span className="text-destructive ml-1">
                            ({broadcast.failed_count} ошибок)
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="hidden sm:table-cell text-sm text-muted-foreground">
                        {formatDate(broadcast.created_at)}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          {broadcast.status === 'draft' && (
                            <>
                              <Button
                                variant="outline"
                                size="xs"
                                onClick={() => setSendId(broadcast.id)}
                              >
                                <Send className="mr-1 h-3 w-3" />
                                Отправить
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                onClick={() => setDeleteId(broadcast.id)}
                              >
                                <Trash2 className="h-3.5 w-3.5 text-destructive" />
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

      {/* Подтверждение отправки */}
      <AlertDialog open={!!sendId} onOpenChange={(open) => !open && setSendId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Отправить рассылку?</AlertDialogTitle>
            <AlertDialogDescription>
              Сообщение будет отправлено всем клиентам в выбранном сегменте. Это действие
              нельзя отменить.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmSend}>
              {sendBroadcast.isPending ? 'Отправляем...' : 'Отправить'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Подтверждение удаления */}
      <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить рассылку?</AlertDialogTitle>
            <AlertDialogDescription>
              Черновик рассылки будет удален безвозвратно.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              className="bg-destructive/10 text-destructive hover:bg-destructive/20"
            >
              {deleteBroadcast.isPending ? 'Удаляем...' : 'Удалить'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
