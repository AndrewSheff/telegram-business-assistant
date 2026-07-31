import { useState } from 'react'
import { toast } from 'sonner'
import { Plus, Pencil, Trash2, HelpCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent } from '@/components/ui/card'
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
import { useFaq, useCreateFaq, useUpdateFaq, useDeleteFaq } from '@/hooks/useFaq'
import type { FaqItem } from '@/types'

// --- форма ---

interface FaqFormData {
  question: string
  answer: string
  category: string
  sort_order: string
}

const emptyFaqForm: FaqFormData = {
  question: '',
  answer: '',
  category: '',
  sort_order: '0',
}

/**
 * Страница FAQ — вопросы-ответы для бота
 * Карточки со сворачиваемыми ответами, CRUD, toggle активности
 */
export default function FaqPage() {
  const { data: faqItems, isLoading } = useFaq()
  const createFaq = useCreateFaq()
  const updateFaq = useUpdateFaq()
  const deleteFaq = useDeleteFaq()

  // состояние диалогов
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<FaqItem | null>(null)
  const [form, setForm] = useState<FaqFormData>(emptyFaqForm)
  const [deleteId, setDeleteId] = useState<string | null>(null)

  // какие карточки развернуты
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  /** Развернуть/свернуть ответ */
  const toggleExpand = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  /** Добавить новый FAQ */
  const handleAdd = () => {
    setEditingItem(null)
    setForm(emptyFaqForm)
    setDialogOpen(true)
  }

  /** Редактировать FAQ */
  const handleEdit = (item: FaqItem) => {
    setEditingItem(item)
    setForm({
      question: item.question,
      answer: item.answer,
      category: item.category ?? '',
      sort_order: String(item.sort_order),
    })
    setDialogOpen(true)
  }

  /** Сохранить FAQ */
  const handleSave = () => {
    const data = {
      question: form.question,
      answer: form.answer,
      category: form.category || null,
      sort_order: parseInt(form.sort_order) || 0,
    }

    if (editingItem) {
      updateFaq.mutate(
        { id: editingItem.id, data },
        {
          onSuccess: () => {
            toast.success('Вопрос обновлен')
            setDialogOpen(false)
          },
          onError: () => toast.error('Не удалось обновить вопрос'),
        },
      )
    } else {
      createFaq.mutate(data, {
        onSuccess: () => {
          toast.success('Вопрос добавлен')
          setDialogOpen(false)
        },
        onError: () => toast.error('Не удалось добавить вопрос'),
      })
    }
  }

  /** Удалить FAQ */
  const handleConfirmDelete = () => {
    if (!deleteId) return
    deleteFaq.mutate(deleteId, {
      onSuccess: () => {
        toast.success('Вопрос удален')
        setDeleteId(null)
      },
      onError: () => toast.error('Не удалось удалить вопрос'),
    })
  }

  /** Переключить активность FAQ */
  const handleToggleActive = (item: FaqItem) => {
    updateFaq.mutate(
      { id: item.id, data: { is_active: !item.is_active } },
      {
        onSuccess: () =>
          toast.success(item.is_active ? 'Вопрос деактивирован' : 'Вопрос активирован'),
        onError: () => toast.error('Не удалось изменить статус'),
      },
    )
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">FAQ</h1>
          <p className="text-muted-foreground">
            Часто задаваемые вопросы для бота
          </p>
        </div>
        <Button onClick={handleAdd}>
          <Plus className="mr-1.5 h-4 w-4" />
          Добавить вопрос
        </Button>
      </div>

      {/* Список FAQ */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      ) : !faqItems?.length ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <HelpCircle className="h-8 w-8 text-muted-foreground mb-2" />
            <p className="text-muted-foreground mb-4">Вопросов пока нет</p>
            <Button onClick={handleAdd}>
              <Plus className="mr-1.5 h-4 w-4" />
              Добавить первый вопрос
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {faqItems.map((item) => {
            const isExpanded = expanded.has(item.id)
            return (
              <Card key={item.id} className={cn(!item.is_active && 'opacity-60')}>
                <CardContent className="p-4">
                  {/* Заголовок вопроса */}
                  <div className="flex items-start gap-3">
                    <button
                      onClick={() => toggleExpand(item.id)}
                      className="flex-1 text-left"
                    >
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-sm">{item.question}</p>
                        {isExpanded ? (
                          <ChevronUp className="h-4 w-4 shrink-0 text-muted-foreground" />
                        ) : (
                          <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
                        )}
                      </div>
                      {item.category && (
                        <Badge variant="outline" className="mt-1.5 text-xs">
                          {item.category}
                        </Badge>
                      )}
                    </button>

                    {/* Кнопки управления */}
                    <div className="flex items-center gap-2 shrink-0">
                      <Switch
                        checked={item.is_active}
                        onCheckedChange={() => handleToggleActive(item)}
                        size="sm"
                      />
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => handleEdit(item)}
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => setDeleteId(item.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5 text-destructive" />
                      </Button>
                    </div>
                  </div>

                  {/* Ответ — сворачиваемый */}
                  {isExpanded && (
                    <div className="mt-3 pt-3 border-t text-sm text-muted-foreground whitespace-pre-wrap">
                      {item.answer}
                    </div>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {/* Диалог создания/редактирования */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{editingItem ? 'Редактировать вопрос' : 'Новый вопрос'}</DialogTitle>
            <DialogDescription>
              Бот будет использовать эти вопросы для ответов клиентам
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="faq-q">Вопрос</Label>
              <Input
                id="faq-q"
                value={form.question}
                onChange={(e) => setForm({ ...form, question: e.target.value })}
                placeholder="Как записаться на прием?"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="faq-a">Ответ</Label>
              <Textarea
                id="faq-a"
                value={form.answer}
                onChange={(e) => setForm({ ...form, answer: e.target.value })}
                placeholder="Подробный ответ на вопрос..."
                className="min-h-[120px]"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="faq-cat">Категория</Label>
                <Input
                  id="faq-cat"
                  value={form.category}
                  onChange={(e) => setForm({ ...form, category: e.target.value })}
                  placeholder="Общие"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="faq-order">Порядок</Label>
                <Input
                  id="faq-order"
                  type="number"
                  value={form.sort_order}
                  onChange={(e) => setForm({ ...form, sort_order: e.target.value })}
                  placeholder="0"
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Отмена
            </Button>
            <Button
              onClick={handleSave}
              disabled={
                !form.question || !form.answer || createFaq.isPending || updateFaq.isPending
              }
            >
              {createFaq.isPending || updateFaq.isPending ? 'Сохраняем...' : 'Сохранить'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Подтверждение удаления */}
      <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить вопрос?</AlertDialogTitle>
            <AlertDialogDescription>
              Вопрос будет удален из базы знаний бота.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              className="bg-destructive/10 text-destructive hover:bg-destructive/20"
            >
              {deleteFaq.isPending ? 'Удаляем...' : 'Удалить'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
