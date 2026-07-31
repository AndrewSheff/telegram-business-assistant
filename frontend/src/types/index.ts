// ==========================================
// Типы для фронтенда Telegram Business Assistant
// Зеркалят бэкенд-схемы, чтобы все было четко
// ==========================================

// --- Общий тип пагинации ---

/** Обертка для любых пагинированных ответов от API */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
}

// --- Пользователи и авторизация ---

/** Роли в системе */
export type UserRole = 'owner' | 'operator'

/** Пользователь системы — владелец или оператор */
export interface User {
  id: string
  email: string
  name: string
  role: UserRole
  is_active: boolean
  must_change_password: boolean
  created_at: string
}

/** Ответ на успешный логин — токен + юзер */
export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

// --- Клиенты ---

/** Клиент из Telegram — инфа из телеги + наши заметки */
export interface Client {
  id: string
  telegram_id: number
  first_name: string
  last_name?: string | null
  username?: string | null
  phone?: string | null
  notes?: string | null
  is_blocked: boolean
  last_interaction_at?: string | null
  created_at: string
  bookings_count?: number | null
}

/** Список клиентов с пагинацией */
export type ClientListResponse = PaginatedResponse<Client>

// --- Услуги и категории ---

/** Услуга, которую предлагает бизнес */
export interface Service {
  id: string
  name: string
  description?: string | null
  price: number
  duration_minutes: number
  category_id?: string | null
  category_name?: string | null
  sort_order: number
  is_active: boolean
  created_at: string
}

/** Категория услуг — группировка для удобства */
export interface ServiceCategory {
  id: string
  name: string
  sort_order: number
}

// --- Расписание ---

/** Рабочие часы на конкретный день недели */
export interface WorkingHours {
  id: string
  day_of_week: number
  start_time: string
  end_time: string
  break_start?: string | null
  break_end?: string | null
  is_working_day: boolean
}

/** Исключение в расписании — выходной или сокращенный день */
export interface ScheduleException {
  id: string
  exception_date: string
  is_working_day: boolean
  start_time?: string | null
  end_time?: string | null
  reason?: string | null
}

/** Временной слот для записи */
export interface TimeSlot {
  start_time: string
  end_time: string
}

// --- Бронирования ---

/** Статусы бронирования — весь жизненный цикл записи */
export type BookingStatus = 'pending' | 'confirmed' | 'completed' | 'cancelled' | 'no_show'

/** Бронирование — запись клиента на услугу */
export interface Booking {
  id: string
  client_id: string
  client_name?: string | null
  service_id: string
  service_name?: string | null
  booking_date: string
  start_time: string
  end_time: string
  status: BookingStatus
  notes?: string | null
  created_at: string
}

/** Список бронирований с пагинацией */
export type BookingListResponse = PaginatedResponse<Booking>

// --- FAQ ---

/** Вопрос-ответ из базы знаний FAQ */
export interface FaqItem {
  id: string
  question: string
  answer: string
  category?: string | null
  sort_order: number
  is_active: boolean
  created_at: string
}

// --- База знаний ---

/** Блок знаний — контекст для AI-ассистента */
export interface KnowledgeBlock {
  id: string
  title: string
  content: string
  is_active: boolean
  sort_order: number
  created_at: string
}

// --- Рассылки ---

/** Сегменты для рассылки — кому шлем */
export type BroadcastSegment = 'all' | 'recent' | 'inactive'

/** Статус рассылки — от черновика до завершения */
export type BroadcastStatus = 'draft' | 'scheduled' | 'sending' | 'completed' | 'failed'

/** Рассылка — массовое сообщение клиентам через бота */
export interface Broadcast {
  id: string
  title: string
  content: string
  image_url?: string | null
  segment: BroadcastSegment
  segment_days?: number | null
  status: BroadcastStatus
  total_count: number
  sent_count: number
  failed_count: number
  scheduled_at?: string | null
  completed_at?: string | null
  created_at: string
}

/** Список рассылок с пагинацией */
export type BroadcastListResponse = PaginatedResponse<Broadcast>

// --- Чат ---

/** Сообщение в чате — от клиента, бота или оператора */
export interface ChatMessage {
  id: string
  client_id: string
  role: string
  content: string
  is_handoff: boolean
  created_at: string
}

/** Клиент в очереди на ответ оператора */
export interface HandoffClient {
  client_id: string
  client_name: string
  telegram_username?: string | null
  last_message?: string | null
  unread_count: number
  created_at: string
}

// --- Дашборд ---

/** Основная статистика для главной — все важное одним взглядом */
export interface DashboardStats {
  total_clients: number
  new_clients_week: number
  bookings_today: number
  bookings_week: number
  bookings_month: number
  pending_handoffs: number
}

/** Точка на графике активности — бронирования и взаимодействия за день */
export interface ActivityPoint {
  date: string
  bookings: number
  interactions: number
}

/** Популярная услуга — для рейтинга */
export interface TopService {
  service_name: string
  count: number
}

/** Частый вопрос — что клиентов интересует больше всего */
export interface TopQuestion {
  question: string
  count: number
}

// --- Настройки ---

/** Настройки бизнеса — все конфиги бота и AI */
export interface Settings {
  id: string
  bot_token_set: boolean
  business_name?: string | null
  description?: string | null
  address?: string | null
  phone?: string | null
  website?: string | null
  welcome_message?: string | null
  offline_message?: string | null
  timezone: string
  min_cancel_hours: number
  ai_model?: string | null
  ai_system_prompt?: string | null
  updated_at: string
}
