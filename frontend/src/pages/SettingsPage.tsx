import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import { Save, Eye, EyeOff } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { useSettings, useUpdateSettings } from '@/hooks/useSettings'

/**
 * Страница настроек — конфиги бота, бизнеса и AI
 * Все поля в одной форме, секции разделены визуально
 */
export default function SettingsPage() {
  const { data: settings, isLoading } = useSettings()
  const updateSettings = useUpdateSettings()

  // все поля формы
  const [botToken, setBotToken] = useState('')
  const [showToken, setShowToken] = useState(false)
  const [businessName, setBusinessName] = useState('')
  const [description, setDescription] = useState('')
  const [address, setAddress] = useState('')
  const [phone, setPhone] = useState('')
  const [website, setWebsite] = useState('')
  const [welcomeMessage, setWelcomeMessage] = useState('')
  const [offlineMessage, setOfflineMessage] = useState('')
  const [aiModel, setAiModel] = useState('claude')
  const [aiSystemPrompt, setAiSystemPrompt] = useState('')
  const [timezone, setTimezone] = useState('Europe/Moscow')
  const [minCancelHours, setMinCancelHours] = useState('24')

  // заполняем форму из загруженных настроек
  useEffect(() => {
    if (settings) {
      setBusinessName(settings.business_name ?? '')
      setDescription(settings.description ?? '')
      setAddress(settings.address ?? '')
      setPhone(settings.phone ?? '')
      setWebsite(settings.website ?? '')
      setWelcomeMessage(settings.welcome_message ?? '')
      setOfflineMessage(settings.offline_message ?? '')
      setAiModel(settings.ai_model ?? 'claude')
      setAiSystemPrompt(settings.ai_system_prompt ?? '')
      setTimezone(settings.timezone ?? 'Europe/Moscow')
      setMinCancelHours(String(settings.min_cancel_hours ?? 24))
    }
  }, [settings])

  /** Сохранить все настройки */
  const handleSave = () => {
    const data: Record<string, unknown> = {
      business_name: businessName || null,
      description: description || null,
      address: address || null,
      phone: phone || null,
      website: website || null,
      welcome_message: welcomeMessage || null,
      offline_message: offlineMessage || null,
      ai_model: aiModel || null,
      ai_system_prompt: aiSystemPrompt || null,
      timezone,
      min_cancel_hours: parseInt(minCancelHours) || 24,
    }
    // токен отправляем только если заполнен (не затираем существующий)
    if (botToken) {
      data.bot_token = botToken
    }
    updateSettings.mutate(data, {
      onSuccess: () => {
        toast.success('Настройки сохранены')
        setBotToken('') // чистим поле токена после сохранения
      },
      onError: () => toast.error('Не удалось сохранить настройки'),
    })
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Заголовок */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Настройки</h1>
          <p className="text-muted-foreground">Конфигурация бота и бизнеса</p>
        </div>
        <Button onClick={handleSave} disabled={updateSettings.isPending}>
          <Save className="mr-1.5 h-4 w-4" />
          {updateSettings.isPending ? 'Сохраняем...' : 'Сохранить'}
        </Button>
      </div>

      {/* Настройки бота */}
      <Card>
        <CardHeader>
          <CardTitle>Telegram-бот</CardTitle>
          <CardDescription>Токен для подключения к Telegram Bot API</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="bot-token">
              Токен бота
              {settings?.bot_token_set && (
                <span className="text-xs text-muted-foreground ml-2">(уже задан)</span>
              )}
            </Label>
            <div className="relative">
              <Input
                id="bot-token"
                type={showToken ? 'text' : 'password'}
                value={botToken}
                onChange={(e) => setBotToken(e.target.value)}
                placeholder={settings?.bot_token_set ? 'Оставьте пустым, если не меняете' : 'Вставьте токен от @BotFather'}
                className="pr-10"
              />
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                className="absolute right-1 top-1/2 -translate-y-1/2"
                onClick={() => setShowToken(!showToken)}
              >
                {showToken ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Информация о бизнесе */}
      <Card>
        <CardHeader>
          <CardTitle>Информация о бизнесе</CardTitle>
          <CardDescription>Данные, которые бот показывает клиентам</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="biz-name">Название</Label>
            <Input
              id="biz-name"
              value={businessName}
              onChange={(e) => setBusinessName(e.target.value)}
              placeholder="Мой бизнес"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="biz-desc">Описание</Label>
            <Textarea
              id="biz-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Краткое описание вашего бизнеса"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="biz-address">Адрес</Label>
            <Input
              id="biz-address"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="г. Москва, ул. Примерная, д. 1"
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="biz-phone">Телефон</Label>
              <Input
                id="biz-phone"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+7 (999) 123-45-67"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="biz-website">Сайт</Label>
              <Input
                id="biz-website"
                value={website}
                onChange={(e) => setWebsite(e.target.value)}
                placeholder="https://example.com"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Сообщения бота */}
      <Card>
        <CardHeader>
          <CardTitle>Сообщения</CardTitle>
          <CardDescription>Тексты, которые бот отправляет клиентам</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="msg-welcome">Приветственное сообщение</Label>
            <Textarea
              id="msg-welcome"
              value={welcomeMessage}
              onChange={(e) => setWelcomeMessage(e.target.value)}
              placeholder="Здравствуйте! Я бот-помощник..."
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="msg-offline">Сообщение в нерабочее время</Label>
            <Textarea
              id="msg-offline"
              value={offlineMessage}
              onChange={(e) => setOfflineMessage(e.target.value)}
              placeholder="К сожалению, сейчас нерабочее время..."
            />
          </div>
        </CardContent>
      </Card>

      {/* Настройки AI */}
      <Card>
        <CardHeader>
          <CardTitle>AI-ассистент</CardTitle>
          <CardDescription>Настройки языковой модели</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Модель</Label>
            <Select value={aiModel} onValueChange={(val) => setAiModel(val as string)}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="claude">Claude (Anthropic)</SelectItem>
                <SelectItem value="gpt">GPT (OpenAI)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="ai-prompt">Системный промпт</Label>
            <Textarea
              id="ai-prompt"
              value={aiSystemPrompt}
              onChange={(e) => setAiSystemPrompt(e.target.value)}
              placeholder="Ты — вежливый помощник бизнеса..."
              className="min-h-[120px]"
            />
            <p className="text-xs text-muted-foreground">
              Инструкции для AI, которые определяют его поведение и стиль общения
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Общие настройки */}
      <Card>
        <CardHeader>
          <CardTitle>Общие</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="tz">Часовой пояс</Label>
              <Input
                id="tz"
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                placeholder="Europe/Moscow"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="cancel-hours">Мин. часов до отмены</Label>
              <Input
                id="cancel-hours"
                type="number"
                min="0"
                value={minCancelHours}
                onChange={(e) => setMinCancelHours(e.target.value)}
                placeholder="24"
              />
              <p className="text-xs text-muted-foreground">
                За сколько часов до записи клиент может ее отменить
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Кнопка сохранения внизу */}
      <Separator />
      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={updateSettings.isPending}>
          <Save className="mr-1.5 h-4 w-4" />
          {updateSettings.isPending ? 'Сохраняем...' : 'Сохранить настройки'}
        </Button>
      </div>
    </div>
  )
}
