import { useState, useRef, useEffect } from 'react'
import { toast } from 'sonner'
import { Send, X, MessageSquare, User } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent } from '@/components/ui/card'
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
  useActiveHandoffs,
  useMessages,
  useSendReply,
  useCloseHandoff,
} from '@/hooks/useChat'

/**
 * Страница чата с клиентами — двухпанельный интерфейс
 * Слева — список хендоффов, справа — переписка с выбранным клиентом
 * Сообщения обновляются каждые 3 секунды автоматически
 */
export default function ChatPage() {
  const { data: handoffs, isLoading: handoffsLoading } = useActiveHandoffs()
  const [selectedClientId, setSelectedClientId] = useState<string | null>(null)
  const [messageInput, setMessageInput] = useState('')
  const [closeId, setCloseId] = useState<string | null>(null)

  const { data: messages, isLoading: messagesLoading } = useMessages(selectedClientId ?? '')
  const sendReply = useSendReply()
  const closeHandoff = useCloseHandoff()

  // ref для автоскролла к последнему сообщению
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // автоскролл при новых сообщениях
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // если выбранный клиент пропал из списка хендоффов — сбрасываем
  useEffect(() => {
    if (selectedClientId && handoffs && !handoffs.find((h) => h.client_id === selectedClientId)) {
      setSelectedClientId(null)
    }
  }, [handoffs, selectedClientId])

  /** Отправить ответ оператора */
  const handleSendReply = () => {
    if (!selectedClientId || !messageInput.trim()) return
    sendReply.mutate(
      { clientId: selectedClientId, content: messageInput.trim() },
      {
        onSuccess: () => setMessageInput(''),
        onError: () => toast.error('Не удалось отправить сообщение'),
      },
    )
  }

  /** Отправить по Enter */
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendReply()
    }
  }

  /** Закрыть хендофф */
  const handleConfirmClose = () => {
    if (!closeId) return
    closeHandoff.mutate(closeId, {
      onSuccess: () => {
        toast.success('Чат передан обратно боту')
        setCloseId(null)
        if (selectedClientId === closeId) {
          setSelectedClientId(null)
        }
      },
      onError: () => toast.error('Не удалось закрыть чат'),
    })
  }

  /** Форматируем время сообщения */
  const formatTime = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleTimeString('ru-RU', {
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return ''
    }
  }

  /** Форматируем дату для группировки */
  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'short',
      })
    } catch {
      return ''
    }
  }

  // текущий хендофф
  const selectedHandoff = handoffs?.find((h) => h.client_id === selectedClientId)

  return (
    <div className="space-y-4">
      {/* Заголовок */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Чат</h1>
        <p className="text-muted-foreground">Разговоры с клиентами, ожидающими оператора</p>
      </div>

      {/* Двухпанельный лейаут */}
      <div className="flex gap-4 h-[calc(100vh-220px)] min-h-[400px]">
        {/* Левая панель — список хендоффов */}
        <div className="w-full sm:w-80 shrink-0 flex flex-col">
          <Card className="flex-1 flex flex-col overflow-hidden">
            <CardContent className="p-0 flex-1 overflow-y-auto">
              {handoffsLoading ? (
                <div className="p-3 space-y-2">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : !handoffs?.length ? (
                <div className="flex flex-col items-center justify-center h-full py-8 text-center">
                  <MessageSquare className="h-8 w-8 text-muted-foreground mb-2" />
                  <p className="text-sm text-muted-foreground px-4">
                    Нет активных обращений
                  </p>
                </div>
              ) : (
                <div className="divide-y">
                  {handoffs.map((handoff) => (
                    <button
                      key={handoff.client_id}
                      className={cn(
                        'w-full text-left p-3 hover:bg-muted/50 transition-colors',
                        selectedClientId === handoff.client_id && 'bg-muted',
                      )}
                      onClick={() => setSelectedClientId(handoff.client_id)}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-sm truncate">
                              {handoff.client_name}
                            </p>
                            {handoff.unread_count > 0 && (
                              <Badge variant="default" className="text-xs px-1.5 py-0">
                                {handoff.unread_count}
                              </Badge>
                            )}
                          </div>
                          {handoff.telegram_username && (
                            <p className="text-xs text-muted-foreground">
                              @{handoff.telegram_username}
                            </p>
                          )}
                          {handoff.last_message && (
                            <p className="text-xs text-muted-foreground truncate mt-0.5">
                              {handoff.last_message}
                            </p>
                          )}
                        </div>
                        <span className="text-xs text-muted-foreground shrink-0">
                          {formatDate(handoff.created_at)}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Правая панель — чат (скрыта на мобилке когда нет выбранного) */}
        <div className={cn(
          'flex-1 flex flex-col',
          !selectedClientId && 'hidden sm:flex',
        )}>
          {!selectedClientId ? (
            <Card className="flex-1 flex items-center justify-center">
              <CardContent className="text-center">
                <MessageSquare className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
                <p className="text-muted-foreground">Выберите чат из списка слева</p>
              </CardContent>
            </Card>
          ) : (
            <Card className="flex-1 flex flex-col overflow-hidden">
              {/* Шапка чата */}
              <div className="flex items-center justify-between p-3 border-b">
                <div className="flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
                    <User className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">{selectedHandoff?.client_name}</p>
                    {selectedHandoff?.telegram_username && (
                      <p className="text-xs text-muted-foreground">
                        @{selectedHandoff.telegram_username}
                      </p>
                    )}
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCloseId(selectedClientId)}
                >
                  <X className="mr-1 h-3.5 w-3.5" />
                  Закрыть чат
                </Button>
              </div>

              {/* Сообщения */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {messagesLoading ? (
                  <div className="space-y-3">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <Skeleton
                        key={i}
                        className={cn(
                          'h-12 w-3/4',
                          i % 2 === 0 ? 'ml-auto' : '',
                        )}
                      />
                    ))}
                  </div>
                ) : !messages?.length ? (
                  <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
                    Сообщений пока нет
                  </div>
                ) : (
                  messages.map((msg) => {
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
                            'max-w-[75%] rounded-lg px-3 py-2',
                            isUser
                              ? 'bg-primary text-primary-foreground'
                              : isBot
                                ? 'bg-muted'
                                : 'bg-blue-100 dark:bg-blue-900/30',
                          )}
                        >
                          <div className="flex items-center gap-1.5 mb-0.5">
                            <span className="text-[10px] font-medium opacity-70">
                              {isUser ? 'Клиент' : isBot ? 'Бот' : 'Оператор'}
                            </span>
                          </div>
                          <p className="text-sm whitespace-pre-wrap break-words">
                            {msg.content}
                          </p>
                          <p className="text-[10px] opacity-50 mt-1 text-right">
                            {formatTime(msg.created_at)}
                          </p>
                        </div>
                      </div>
                    )
                  })
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Ввод сообщения */}
              <div className="p-3 border-t">
                <div className="flex gap-2">
                  <Input
                    value={messageInput}
                    onChange={(e) => setMessageInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Введите ответ..."
                    disabled={sendReply.isPending}
                  />
                  <Button
                    size="icon"
                    onClick={handleSendReply}
                    disabled={!messageInput.trim() || sendReply.isPending}
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* Подтверждение закрытия хендоффа */}
      <AlertDialog open={!!closeId} onOpenChange={(open) => !open && setCloseId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Закрыть чат?</AlertDialogTitle>
            <AlertDialogDescription>
              Управление разговором вернется к боту. Клиент продолжит общаться с
              AI-ассистентом.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Отмена</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmClose}>
              {closeHandoff.isPending ? 'Закрываем...' : 'Закрыть'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
