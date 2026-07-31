import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { ArrowLeft, Send, Save, Image } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useCreateBroadcast, useSendBroadcast } from '@/hooks/useBroadcasts'
import type { BroadcastSegment } from '@/types'

/**
 * Создание новой рассылки — форма + превью
 * Можно сохранить как черновик или сразу отправить
 */
export default function BroadcastCreatePage() {
  const navigate = useNavigate()
  const createBroadcast = useCreateBroadcast()
  const sendBroadcast = useSendBroadcast()

  // поля формы
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [segment, setSegment] = useState<BroadcastSegment>('all')
  const [segmentDays, setSegmentDays] = useState('30')

  // нужны ли дни для сегмента
  const needsDays = segment === 'recent' || segment === 'inactive'

  /** Сохранить как черновик */
  const handleSaveDraft = () => {
    createBroadcast.mutate(
      {
        title,
        content,
        image_url: imageUrl || null,
        segment,
        segment_days: needsDays ? parseInt(segmentDays) || 30 : null,
      },
      {
        onSuccess: () => {
          toast.success('Черновик сохранен')
          navigate('/broadcasts')
        },
        onError: () => toast.error('Не удалось создать рассылку'),
      },
    )
  }

  /** Создать и сразу отправить */
  const handleCreateAndSend = () => {
    createBroadcast.mutate(
      {
        title,
        content,
        image_url: imageUrl || null,
        segment,
        segment_days: needsDays ? parseInt(segmentDays) || 30 : null,
      },
      {
        onSuccess: (broadcast) => {
          // после создания сразу запускаем отправку
          sendBroadcast.mutate(broadcast.id, {
            onSuccess: () => {
              toast.success('Рассылка создана и отправляется')
              navigate('/broadcasts')
            },
            onError: () => {
              toast.error('Рассылка создана, но не удалось запустить отправку')
              navigate('/broadcasts')
            },
          })
        },
        onError: () => toast.error('Не удалось создать рассылку'),
      },
    )
  }

  const isValid = title.trim() && content.trim()
  const isBusy = createBroadcast.isPending || sendBroadcast.isPending

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/broadcasts')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Новая рассылка</h1>
          <p className="text-muted-foreground">Создайте массовое сообщение для клиентов</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Форма */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Содержание</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="bc-title">Название рассылки</Label>
                <Input
                  id="bc-title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Акция на стрижку"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="bc-content">Текст сообщения</Label>
                <Textarea
                  id="bc-content"
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Текст, который получат ваши клиенты..."
                  className="min-h-[160px]"
                  maxLength={4096}
                />
                <p className={cn(
                  "text-xs text-right",
                  content.length > 3800 ? "text-destructive" : "text-muted-foreground"
                )}>
                  {content.length} / 4096
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="bc-image">URL изображения (необязательно)</Label>
                <div className="flex gap-2">
                  <Image className="h-4 w-4 mt-2 shrink-0 text-muted-foreground" />
                  <Input
                    id="bc-image"
                    value={imageUrl}
                    onChange={(e) => setImageUrl(e.target.value)}
                    placeholder="https://example.com/image.jpg"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Аудитория</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Сегмент</Label>
                <Select
                  value={segment}
                  onValueChange={(val) => setSegment(val as BroadcastSegment)}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Все клиенты</SelectItem>
                    <SelectItem value="recent">Недавние (были за N дней)</SelectItem>
                    <SelectItem value="inactive">Неактивные (не были N дней)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {needsDays && (
                <div className="space-y-2">
                  <Label htmlFor="bc-days">Количество дней</Label>
                  <Input
                    id="bc-days"
                    type="number"
                    min="1"
                    value={segmentDays}
                    onChange={(e) => setSegmentDays(e.target.value)}
                    placeholder="30"
                  />
                  <p className="text-xs text-muted-foreground">
                    {segment === 'recent'
                      ? 'Клиенты, которые взаимодействовали с ботом за последние N дней'
                      : 'Клиенты, которые не взаимодействовали с ботом N дней'}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Кнопки */}
          <div className="flex flex-col gap-2 sm:flex-row">
            <Button
              variant="outline"
              onClick={handleSaveDraft}
              disabled={!isValid || isBusy}
              className="flex-1"
            >
              <Save className="mr-1.5 h-4 w-4" />
              {createBroadcast.isPending ? 'Сохраняем...' : 'Сохранить черновик'}
            </Button>
            <Button
              onClick={handleCreateAndSend}
              disabled={!isValid || isBusy}
              className="flex-1"
            >
              <Send className="mr-1.5 h-4 w-4" />
              {isBusy ? 'Отправляем...' : 'Создать и отправить'}
            </Button>
          </div>
        </div>

        {/* Превью */}
        <div className="lg:sticky lg:top-6">
          <Card>
            <CardHeader>
              <CardTitle>Превью сообщения</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="rounded-lg bg-muted p-4 space-y-3">
                {imageUrl && (
                  <div className="rounded-md overflow-hidden bg-gray-200 dark:bg-gray-700">
                    <img
                      src={imageUrl}
                      alt="Preview"
                      className="w-full h-auto max-h-[200px] object-cover"
                      onError={(e) => {
                        ;(e.target as HTMLImageElement).style.display = 'none'
                      }}
                    />
                  </div>
                )}
                {content ? (
                  <p className="text-sm whitespace-pre-wrap break-words">{content}</p>
                ) : (
                  <p className="text-sm text-muted-foreground italic">
                    Тут будет текст вашего сообщения...
                  </p>
                )}
              </div>
              <div className="mt-3 text-xs text-muted-foreground">
                Так примерно будет выглядеть сообщение в Telegram
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
