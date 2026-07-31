import { useState } from 'react'
import { toast } from 'sonner'
import { Plus, Pencil, Trash2, BookOpen } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
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
import {
  useKnowledge,
  useCreateKnowledge,
  useUpdateKnowledge,
  useDeleteKnowledge,
} from '@/hooks/useKnowledge'
import type { KnowledgeBlock } from '@/types'

// --- форма ---

interface KnowledgeFormData {
  title: string
  content: string
  sort_order: string
}

const emptyForm: KnowledgeFormData = {
  title: '',
  content: '',
  sort_order: '0',
}

/**
 * Страница базы знаний — блоки контекста для AI-ассистента
 * Карточки с превью, CRUD, переключение активности
 */
export default function KnowledgePage() {
  const { data: blocks, isLoading } = useKnowledge()
  const createKnowledge = useCreateKnowledge()
  const updateKnowledge = useUpdateKnowledge()
  const deleteKnowledge = useDeleteKnowledge()

  // состояние диалогов
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingBlock, setEditingBlock] = useState<KnowledgeBlock | null>(null)
  const [form, setForm] = useState<KnowledgeFormData>(emptyForm)
  const [deleteId, setDeleteId] = useState<string | null>(null)

  /** Добавить новый блок */
  const handleAdd = () => {
    setEditingBlock(null)
    setForm(emptyForm)
    setDialogOpen(true)
  }

  /** Редактировать блок */
  const handleEdit = (block: KnowledgeBlock) => {
    setEditingBlock(block)
    setForm({
      title: block.title,
      content: block.content,
      sort_order: String(block.sort_order),
    })
    setDialogOpen(true)
  }

  /** Сохранить блок */
  const handleSave = () => {
    const data = {
      title: form.title,
      content: form.content,
      sort_order: parseInt(form.sort_order) || 0,
    }

    if (editingBlock) {
      updateKnowledge.mutate(
        { id: editingBlock.id, data },
        {
          onSuccess: () => {
            toast.success('Блок обновлен')
            setDialogOpen(false)
          },
          onError: () => toast.error('Не удалось обновить блок'),
        },
      )
    } else {
      createKnowledge.mutate(data, {
        onSuccess: () => {
          toast.success('Блок создан')
          setDialogOpen(false)
        },
        onError: () => toast.error('Не удалось создать блок'),
      })
    }
  }

  /** Удалить блок */
  const handleConfirmDelete = () => {
    if (!deleteId) return
    deleteKnowledge.mutate(deleteId, {
      onSuccess: () => {
        toast.success('Блок удален')
        setDeleteId(null)
      },
      onError: () => toast.error('Не удалось удалить блок'),
    })
  }

  /** Переключить активность блока */
  const handleToggleActive = (block: KnowledgeBlock) => {
    updateKnowledge.mutate(
      { id: block.id, data: { is_active: !block.is_active } },
      {
        onSuccess: () =>
          toast.success(block.is_active ? 'Блок деактивирован' : 'Блок активирован'),
        onError: () => toast.error('Не удалось изменить статус'),
      },
    )
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">База знаний</h1>
          <p className="text-muted-foreground">
            Контекстные блоки для AI-ассистента
          </p>
        </div>
        <Button onClick={handleAdd}>
          <Plus className="mr-1.5 h-4 w-4" />
          Добавить блок
        </Button>
      </div>

      {/* Карточки блоков знаний */}
      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-40 w-full" />
          ))}
        </div>
      ) : !blocks?.length ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <BookOpen className="h-8 w-8 text-muted-foreground mb-2" />
            <p className="text-muted-foreground mb-4">Блоков знаний пока нет</p>
            <Button onClick={handleAdd}>
              <Plus className="mr-1.5 h-4 w-4" />
              Создать первый блок
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {blocks.map((block) => (
            <Card
              key={block.id}
              className={cn(
                'flex flex-col',
                !block.is_active && 'opacity-60',
              )}
            >
              <CardContent className="flex flex-col flex-1 p-4">
                {/* Заголовок и бейдж */}
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h3 className="font-medium text-sm line-clamp-2">{block.title}</h3>
                  <Badge
                    variant={block.is_active ? 'default' : 'secondary'}
                    className="shrink-0"
                  >
                    {block.is_active ? 'Активен' : 'Выкл'}
                  </Badge>
                </div>

                {/* Превью контента */}
                <p className="text-xs text-muted-foreground line-clamp-4 flex-1 mb-3">
                  {block.content}
                </p>

                {/* Кнопки */}
                <div className="flex items-center justify-between pt-2 border-t">
                  <Button
                    variant="ghost"
                    size="xs"
                    onClick={() => handleToggleActive(block)}
                  >
                    {block.is_active ? 'Выключить' : 'Включить'}
                  </Button>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => handleEdit(block)}
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => setDeleteId(block.id)}
                    >
                      <Trash2 className="h-3.5 w-3.5 text-destructive" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Диалог создания/редактирования */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>
              {editingBlock ? 'Редактировать блок' : 'Новый блок знаний'}
            </DialogTitle>
            <DialogDescription>
              AI-ассистент использует эти блоки как контекст для ответов
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="kb-title">Заголовок</Label>
              <Input
                id="kb-title"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="Например: О нашей компании"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="kb-content">Содержание</Label>
              <Textarea
                id="kb-content"
                value={form.content}
                onChange={(e) => setForm({ ...form, content: e.target.value })}
                placeholder="Подробная информация..."
                className="min-h-[160px]"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="kb-order">Порядок сортировки</Label>
              <Input
                id="kb-order"
                type="number"
                value={form.sort_order}
                onChange={(e) => setForm({ ...form, sort_order: e.target.value })}
                placeholder="0"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Отмена
            </Button>
            <Button
              onClick={handleSave}
              disabled={
                !form.title ||
                !form.content ||
                createKnowledge.isPending ||
                updateKnowledge.isPending
              }
            >
              {createKnowledge.isPending || updateKnowledge.isPending
                ? 'Сохраняем...'
                : 'Сохранить'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Подтверждение удаления */}
      <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить блок знаний?</AlertDialogTitle>
            <AlertDialogDescription>
              Блок будет удален безвозвратно. AI-ассистент перестанет его использовать.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmDelete}
              className="bg-destructive/10 text-destructive hover:bg-destructive/20"
            >
              {deleteKnowledge.isPending ? 'Удаляем...' : 'Удалить'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
