import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import { Save, Plus, Trash2, CalendarOff } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
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
import {
  useWorkingHours,
  useUpdateWorkingHours,
  useScheduleExceptions,
  useCreateException,
  useDeleteException,
} from '@/hooks/useSchedule'
import type { WorkingHours } from '@/types'

/** Названия дней недели на русском — как в нормальной стране */
const DAY_NAMES = [
  'Понедельник',
  'Вторник',
  'Среда',
  'Четверг',
  'Пятница',
  'Суббота',
  'Воскресенье',
]

/** Короткие названия для мобилки */
const DAY_SHORT = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

// --- Типы для формы исключения ---

interface ExceptionFormData {
  exception_date: string
  reason: string
  is_working_day: boolean
  start_time: string
  end_time: string
}

const emptyExceptionForm: ExceptionFormData = {
  exception_date: '',
  reason: '',
  is_working_day: false,
  start_time: '',
  end_time: '',
}

/**
 * Страница расписания — рабочие часы по дням недели + исключения
 * Все дни редактируются прямо на странице, сохраняются разом
 */
export default function SchedulePage() {
  const { data: workingHours, isLoading: hoursLoading } = useWorkingHours()
  const updateHours = useUpdateWorkingHours()
  const { data: exceptions, isLoading: exceptionsLoading } = useScheduleExceptions()
  const createException = useCreateException()
  const deleteException = useDeleteException()

  // локальная копия рабочих часов для редактирования
  const [localHours, setLocalHours] = useState<Partial<WorkingHours>[]>([])
  const [hasChanges, setHasChanges] = useState(false)

  // диалог исключения
  const [exceptionDialogOpen, setExceptionDialogOpen] = useState(false)
  const [exceptionForm, setExceptionForm] = useState<ExceptionFormData>(emptyExceptionForm)
  const [deleteExceptionId, setDeleteExceptionId] = useState<string | null>(null)

  // заполняем локальное состояние при загрузке данных
  useEffect(() => {
    if (workingHours) {
      setLocalHours(
        workingHours.map((wh) => ({
          id: wh.id,
          day_of_week: wh.day_of_week,
          start_time: wh.start_time,
          end_time: wh.end_time,
          break_start: wh.break_start,
          break_end: wh.break_end,
          is_working_day: wh.is_working_day,
        })),
      )
      setHasChanges(false)
    }
  }, [workingHours])

  /** Обновить поле конкретного дня */
  const updateDay = (dayIndex: number, field: string, value: string | boolean) => {
    setLocalHours((prev) => {
      const next = [...prev]
      const idx = next.findIndex((h) => h.day_of_week === dayIndex)
      if (idx >= 0) {
        next[idx] = { ...next[idx], [field]: value }
      } else {
        // если дня нет в массиве — создаем
        next.push({
          day_of_week: dayIndex,
          is_working_day: field === 'is_working_day' ? (value as boolean) : false,
          start_time: '09:00',
          end_time: '18:00',
          [field]: value,
        })
      }
      return next
    })
    setHasChanges(true)
  }

  /** Сохранить все расписание разом */
  const handleSaveSchedule = () => {
    updateHours.mutate(localHours, {
      onSuccess: () => {
        toast.success('Расписание сохранено')
        setHasChanges(false)
      },
      onError: () => toast.error('Не удалось сохранить расписание'),
    })
  }

  /** Создать исключение из расписания */
  const handleAddException = () => {
    const data: Record<string, unknown> = {
      exception_date: exceptionForm.exception_date,
      reason: exceptionForm.reason || null,
      is_working_day: exceptionForm.is_working_day,
    }
    if (exceptionForm.is_working_day && exceptionForm.start_time) {
      data.start_time = exceptionForm.start_time
      data.end_time = exceptionForm.end_time
    }
    createException.mutate(data, {
      onSuccess: () => {
        toast.success('Исключение добавлено')
        setExceptionDialogOpen(false)
        setExceptionForm(emptyExceptionForm)
      },
      onError: () => toast.error('Не удалось добавить исключение'),
    })
  }

  /** Подтвердить удаление исключения */
  const handleConfirmDeleteException = () => {
    if (!deleteExceptionId) return
    deleteException.mutate(deleteExceptionId, {
      onSuccess: () => {
        toast.success('Исключение удалено')
        setDeleteExceptionId(null)
      },
      onError: () => toast.error('Не удалось удалить исключение'),
    })
  }

  /** Получить данные дня по номеру */
  const getDayData = (dayIndex: number) => {
    return (
      localHours.find((h) => h.day_of_week === dayIndex) ?? {
        day_of_week: dayIndex,
        is_working_day: false,
        start_time: '09:00',
        end_time: '18:00',
        break_start: null,
        break_end: null,
      }
    )
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Расписание</h1>
          <p className="text-muted-foreground">Рабочие часы и исключения</p>
        </div>
        <Button onClick={handleSaveSchedule} disabled={!hasChanges || updateHours.isPending}>
          <Save className="mr-1.5 h-4 w-4" />
          {updateHours.isPending ? 'Сохраняем...' : 'Сохранить расписание'}
        </Button>
      </div>

      {/* Рабочие часы по дням */}
      <Card>
        <CardHeader>
          <CardTitle>Рабочие часы</CardTitle>
        </CardHeader>
        <CardContent>
          {hoursLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 7 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {Array.from({ length: 7 }).map((_, dayIndex) => {
                const day = getDayData(dayIndex)
                return (
                  <div
                    key={dayIndex}
                    className="flex flex-col gap-3 rounded-lg border p-3 sm:flex-row sm:items-center"
                  >
                    {/* Переключатель и название дня */}
                    <div className="flex items-center gap-3 sm:w-40">
                      <Switch
                        checked={day.is_working_day}
                        onCheckedChange={(checked) =>
                          updateDay(dayIndex, 'is_working_day', checked)
                        }
                        size="sm"
                      />
                      <span className="font-medium text-sm">
                        <span className="hidden sm:inline">{DAY_NAMES[dayIndex]}</span>
                        <span className="sm:hidden">{DAY_SHORT[dayIndex]}</span>
                      </span>
                    </div>

                    {/* Поля времени — только для рабочих дней */}
                    {day.is_working_day ? (
                      <div className="flex flex-wrap items-center gap-2 text-sm">
                        <div className="flex items-center gap-1.5">
                          <Label className="text-xs text-muted-foreground whitespace-nowrap">
                            с
                          </Label>
                          <Input
                            type="time"
                            className="w-28 h-8"
                            value={day.start_time ?? '09:00'}
                            onChange={(e) => updateDay(dayIndex, 'start_time', e.target.value)}
                          />
                        </div>
                        <div className="flex items-center gap-1.5">
                          <Label className="text-xs text-muted-foreground whitespace-nowrap">
                            до
                          </Label>
                          <Input
                            type="time"
                            className="w-28 h-8"
                            value={day.end_time ?? '18:00'}
                            onChange={(e) => updateDay(dayIndex, 'end_time', e.target.value)}
                          />
                        </div>
                        <div className="flex items-center gap-1.5">
                          <Label className="text-xs text-muted-foreground whitespace-nowrap">
                            перерыв
                          </Label>
                          <Input
                            type="time"
                            className="w-28 h-8"
                            value={day.break_start ?? ''}
                            onChange={(e) => updateDay(dayIndex, 'break_start', e.target.value)}
                            placeholder="—"
                          />
                          <span className="text-muted-foreground">—</span>
                          <Input
                            type="time"
                            className="w-28 h-8"
                            value={day.break_end ?? ''}
                            onChange={(e) => updateDay(dayIndex, 'break_end', e.target.value)}
                            placeholder="—"
                          />
                        </div>
                      </div>
                    ) : (
                      <span className="text-sm text-muted-foreground">Выходной</span>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Исключения из расписания */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Исключения из расписания</CardTitle>
          <Button
            size="sm"
            onClick={() => {
              setExceptionForm(emptyExceptionForm)
              setExceptionDialogOpen(true)
            }}
          >
            <Plus className="mr-1 h-3.5 w-3.5" />
            Добавить
          </Button>
        </CardHeader>
        <CardContent>
          {exceptionsLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : !exceptions?.length ? (
            <div className="flex items-center gap-2 py-4 text-sm text-muted-foreground">
              <CalendarOff className="h-4 w-4" />
              Исключений пока нет
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Дата</TableHead>
                  <TableHead className="hidden sm:table-cell">Причина</TableHead>
                  <TableHead>Тип</TableHead>
                  <TableHead className="hidden md:table-cell">Время</TableHead>
                  <TableHead className="w-16 text-right">Действия</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {exceptions.map((exc) => (
                  <TableRow key={exc.id}>
                    <TableCell className="font-medium">{exc.exception_date}</TableCell>
                    <TableCell className="hidden sm:table-cell">
                      {exc.reason || <span className="text-muted-foreground">—</span>}
                    </TableCell>
                    <TableCell>
                      {exc.is_working_day ? (
                        <span className="text-sm text-green-600">Рабочий</span>
                      ) : (
                        <span className="text-sm text-red-500">Выходной</span>
                      )}
                    </TableCell>
                    <TableCell className="hidden md:table-cell">
                      {exc.is_working_day && exc.start_time && exc.end_time
                        ? `${exc.start_time} — ${exc.end_time}`
                        : '—'}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => setDeleteExceptionId(exc.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5 text-destructive" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Диалог добавления исключения */}
      <Dialog open={exceptionDialogOpen} onOpenChange={setExceptionDialogOpen}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Новое исключение</DialogTitle>
            <DialogDescription>
              Добавьте выходной или измененный рабочий день
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="exc-date">Дата</Label>
              <Input
                id="exc-date"
                type="date"
                value={exceptionForm.exception_date}
                onChange={(e) =>
                  setExceptionForm({ ...exceptionForm, exception_date: e.target.value })
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="exc-reason">Причина</Label>
              <Input
                id="exc-reason"
                value={exceptionForm.reason}
                onChange={(e) => setExceptionForm({ ...exceptionForm, reason: e.target.value })}
                placeholder="Праздничный день, ремонт и т.п."
              />
            </div>
            <div className="flex items-center gap-3">
              <Switch
                checked={exceptionForm.is_working_day}
                onCheckedChange={(checked) =>
                  setExceptionForm({ ...exceptionForm, is_working_day: checked as boolean })
                }
                size="sm"
              />
              <Label>Рабочий день (с особым графиком)</Label>
            </div>
            {exceptionForm.is_working_day && (
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="exc-start">Начало</Label>
                  <Input
                    id="exc-start"
                    type="time"
                    value={exceptionForm.start_time}
                    onChange={(e) =>
                      setExceptionForm({ ...exceptionForm, start_time: e.target.value })
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="exc-end">Конец</Label>
                  <Input
                    id="exc-end"
                    type="time"
                    value={exceptionForm.end_time}
                    onChange={(e) =>
                      setExceptionForm({ ...exceptionForm, end_time: e.target.value })
                    }
                  />
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setExceptionDialogOpen(false)}>
              Отмена
            </Button>
            <Button
              onClick={handleAddException}
              disabled={!exceptionForm.exception_date || createException.isPending}
            >
              {createException.isPending ? 'Добавляем...' : 'Добавить'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Подтверждение удаления исключения */}
      <AlertDialog
        open={!!deleteExceptionId}
        onOpenChange={(open) => !open && setDeleteExceptionId(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить исключение?</AlertDialogTitle>
            <AlertDialogDescription>
              Дата вернется к обычному расписанию.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDeleteException}
              className="bg-destructive/10 text-destructive hover:bg-destructive/20"
            >
              {deleteException.isPending ? 'Удаляем...' : 'Удалить'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
