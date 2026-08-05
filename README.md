<!--
  BANNER: см. github_resume/DESIGN_SYSTEM.md — Telegram Business Assistant
  Сохранить как assets/banner.png и раскомментировать:
-->
<!-- <img src="assets/banner.png" alt="Telegram Business Assistant" width="100%"> -->

<div align="center">

> **[English version](README_EN.md)**

# Telegram Business Assistant

### Бот-платформа для сервисного бизнеса

[![CI/CD](https://github.com/AndrewSheff/telegram-business-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/AndrewSheff/telegram-business-assistant/actions)
[![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178C6?logo=typescript&logoColor=white)](https://typescriptlang.org)
[![aiogram 3](https://img.shields.io/badge/aiogram-3.19-26A5E4?logo=telegram&logoColor=white)](https://aiogram.dev)
[![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Клиенты записываются через Telegram. AI отвечает на вопросы 24/7. Владельцы управляют всем из веб-панели.**

[Быстрый старт](#быстрый-старт) · [Возможности](#возможности) · [Скриншоты](#скриншоты) · [Архитектура](#архитектура) · [API](#api-документация)

</div>

---

> **Проблема:** Сервисный бизнес тратит 3-5 часов в день на ручное управление записями. 40% бронирований приходится на нерабочее время, когда никто не берет трубку. 20-35% записей заканчиваются неявкой без напоминаний.

**Telegram Business Assistant** превращает Telegram в полноценную платформу для управления бизнесом — клиенты записываются на услуги, задают вопросы и получают напоминания прямо в мессенджере, а владельцы ведут операционку через современную админ-панель с CRM, аналитикой и рассылками.

<div align="center">

| Строк кода | Эндпоинтов API | Моделей БД | Страниц админки | Тестов | Сервисов Docker |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **16 800+** | **55** | **14** | **16** | **48** | **5** |

</div>

---

## Скриншоты

| Дашборд | Чат с клиентом |
|:-------:|:--------------:|
| ![Dashboard](screenshots/dashboard.png) | ![Chat](screenshots/chat.png) |

---

## Возможности

**Онлайн-запись через Telegram** — клиент выбирает услугу, дату и время и подтверждает запись, не покидая мессенджер. Процесс построен на FSM с блокировкой `SELECT FOR UPDATE` для защиты от двойных бронирований.

**AI-ассистент с передачей оператору** — Claude или GPT отвечает на вопросы на основе базы знаний бизнеса. Если AI не справляется, разговор плавно передается живому оператору с сохранением всего контекста.

**Живой чат и панель оператора** — интерфейс чата в реальном времени в админ-панели. Операторы видят активные диалоги, счетчики непрочитанных и могут в любой момент подключиться вместо AI.

**Рассылки** — отправка целевых объявлений всем подписчикам с ограничением скорости доставки (с учетом лимитов Telegram API). Статистика доставки по каждому сообщению.

**Встроенная CRM** — автоматические профили клиентов из Telegram-взаимодействий. История записей, журнал переписки, поиск и фильтрация по имени, телефону или username.

**Управление расписанием** — недельные рабочие часы с перерывами на обед. Переопределения для конкретных дат и праздников. Бот автоматически показывает только доступные слоты.

**Каталог услуг** — услуги, организованные по категориям, с длительностью, ценой и описанием. Напрямую используется в боте при записи и в аналитике.

**FAQ и база знаний** — структурированные вопросы-ответы по категориям (проверяются до обращения к AI). Отдельные блоки базы знаний для расширенного контекста AI.

**Дашборд и аналитика** — метрики в реальном времени: записи, новые клиенты, выручка. Графики активности (7д/30д), популярные услуги, распределение статусов записей.

**Автоматические напоминания** — APScheduler отправляет подтверждения записи, напоминания за 24 часа и за 2 часа. Автоматическое выявление неявок.

**Мультипользовательский доступ** — роли Владелец (полный доступ) и Оператор (чат и записи). Обязательная смена пароля при первом входе.

**Корпоративная безопасность** — JWT + bcrypt, rate limiting на эндпоинтах авторизации, трассировка по request ID, структурированное JSON-логирование.

---

## Архитектура

```
                      +------------------+
                      |     Nginx :80    |
                      |  Обратный прокси |
                      +--------+---------+
                               |
                +--------------+--------------+
                |                             |
        +-------+-------+           +--------+--------+
        | Frontend :3000|           |  Backend :8000  |
        |  React 19 SPA |           |  FastAPI + Bot  |
        +---------------+           +---+----+----+---+
                                        |    |    |
                          +-------------+    |    +-----------+
                          |                  |                |
                 +--------+---+    +---------+----+    +------+------+
                 | PostgreSQL |    |    Redis     |    |  Telegram   |
                 |   :5432    |    |    :6379     |    |  Bot API    |
                 |  14 моделей|    | Rate Limit   |    +------+------+
                 +------------+    +--------------+           |
                                                       +------+------+
                                                       | APScheduler |
                                                       | Напоминания |
                                                       | Рассылки    |
                                                       +-------------+
```

### Поток обработки сообщений бота

```
Сообщение клиента в Telegram
        |
        v
  [обработчик aiogram]
        |
        +---> /book       --> FSM: услуга -> дата -> время -> подтверждение
        +---> /faq        --> категории и ответы FAQ
        +---> /services   --> каталог услуг с ценами
        +---> /my_bookings --> список и отмена предстоящих записей
        +---> свободный текст --> AI-конвейер:
                                1. Проверка совпадения в FAQ
                                2. Сборка контекста (расписание, услуги, база знаний)
                                3. Вызов Claude/GPT
                                4. При неуверенности --> предложение передать оператору
                                5. Оператор подключается через админ-панель
```

---

## Быстрый старт

### Требования
- Docker & Docker Compose v2+
- Токен Telegram-бота от [@BotFather](https://t.me/BotFather)
- (Опционально) API-ключ Anthropic или OpenAI для AI-чата

### 1. Клонирование и настройка

```bash
git clone https://github.com/AndrewSheff/telegram-business-assistant.git
cd telegram-business-assistant
cp .env.example .env
```

Отредактируй `.env`:

```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...     # обязательно
SECRET_KEY=your-random-32-char-string    # обязательно
ADMIN_EMAIL=admin@yourcompany.com
ADMIN_DEFAULT_PASSWORD=SecurePass123
ANTHROPIC_API_KEY=sk-ant-...             # опционально, для AI-чата
```

### 2. Запуск

```bash
docker compose up -d
```

### 3. Доступ

| Сервис | URL |
|:-------|:----|
| Админ-панель | http://localhost |
| Документация API (Swagger) | http://localhost/docs |
| Проверка работоспособности | http://localhost/api/v1/health |

Войди с учетными данными администратора из `.env`. При первом входе смени пароль, затем настрой свой бизнес в разделе **Настройки**.

---

## Технологии

| Слой | Технология | Версия |
|:-----|:-----------|:-------|
| **Backend** | Python, FastAPI, SQLAlchemy (async), Alembic | 3.13, 0.115, 2.0 |
| **Telegram** | aiogram, APScheduler | 3.19, 3.11 |
| **Frontend** | React, TypeScript, Vite, TailwindCSS, shadcn/ui | 19, 5+, 6, v4 |
| **База данных** | PostgreSQL | 16 |
| **Кеш** | Redis | 7 |
| **AI** | Anthropic Claude, OpenAI GPT | Latest |
| **Авторизация** | JWT (python-jose) + bcrypt | HS256 |
| **Инфраструктура** | Docker Compose, Nginx, GitHub Actions CI/CD | Multi-stage |
| **Логирование** | structlog (JSON) | Трассировка запросов |
| **Тестирование** | Pytest (async) | 48 тестов, 10 файлов |

---

## API документация

Интерактивный Swagger по адресу `/docs`. **55 эндпоинтов** в 13 группах:

| Группа | Префикс | Эндпоинты |
|:-------|:--------|:----------|
| Авторизация | `/api/v1/auth` | Вход, смена пароля, обновление токена |
| Дашборд | `/api/v1/dashboard` | Агрегированные метрики и графики |
| Услуги | `/api/v1/services` | CRUD каталога услуг с категориями |
| Расписание | `/api/v1/schedule` | Рабочие часы и исключения по датам |
| Записи | `/api/v1/bookings` | Управление, смена статусов |
| Клиенты | `/api/v1/clients` | Профили и история записей |
| FAQ | `/api/v1/faq` | CRUD FAQ с категориями |
| База знаний | `/api/v1/knowledge` | Блоки базы знаний для AI |
| Рассылки | `/api/v1/broadcasts` | Кампании массовых сообщений |
| Чат | `/api/v1/chat` | Живой чат, диалоги, передача оператору |
| Настройки | `/api/v1/settings` | Настройка профиля бизнеса |
| Пользователи | `/api/v1/users` | Управление пользователями и ролями |
| Здоровье | `/api/v1/health` | Liveness и readiness-пробы |

---

## Структура проекта

```
telegram-business-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app with lifespan
│   │   ├── config.py            # Pydantic settings
│   │   ├── database.py          # Async SQLAlchemy engine
│   │   ├── api/v1/              # 13 REST API routers
│   │   ├── bot/                 # Telegram bot
│   │   │   ├── bot.py           # Bot initialization
│   │   │   ├── handlers/        # Message & callback handlers
│   │   │   ├── keyboards/       # Inline & reply keyboards
│   │   │   └── states/          # FSM states for booking
│   │   ├── models/              # 14 SQLAlchemy models
│   │   ├── schemas/             # Pydantic v2 schemas
│   │   ├── services/            # Business logic layer
│   │   ├── tasks/               # APScheduler tasks
│   │   └── core/                # Security, logging, exceptions
│   ├── tests/                   # 48 pytest tests (10 files)
│   ├── Dockerfile
│   └── entrypoint.sh
├── frontend/
│   ├── src/
│   │   ├── api/                 # Axios API clients
│   │   ├── components/          # UI components + layout
│   │   ├── contexts/            # Auth context provider
│   │   ├── pages/               # 16 page components
│   │   └── lib/                 # Utilities
│   └── Dockerfile
├── docker/nginx/
├── .github/workflows/           # CI/CD (lint + test + build)
├── docker-compose.yml           # 5 services with health checks
└── .env.example
```

---

## Переменные окружения

| Переменная | Обязательна | По умолчанию | Описание |
|:-----------|:------------|:-------------|:---------|
| `TELEGRAM_BOT_TOKEN` | Да | -- | Токен бота от @BotFather |
| `SECRET_KEY` | Да | -- | Ключ подписи JWT (мин. 32 символа) |
| `ADMIN_EMAIL` | Нет | `admin@company.com` | Email первоначального владельца |
| `ADMIN_DEFAULT_PASSWORD` | Нет | -- | Пароль первоначального владельца |
| `DATABASE_URL` | Нет | Авто | Подключение к PostgreSQL |
| `REDIS_URL` | Нет | Авто | Подключение к Redis |
| `ANTHROPIC_API_KEY` | Нет | -- | Для Claude AI-чата |
| `OPENAI_API_KEY` | Нет | -- | Для GPT AI-чата |
| `TIMEZONE` | Нет | `UTC` | Часовой пояс бизнеса |
| `LOG_LEVEL` | Нет | `INFO` | Уровень логирования |

---

## Разработка

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
docker compose up -d postgres redis
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev

# Тесты
cd backend && pytest tests/ -v

# Линтер
ruff check backend/
cd frontend && npm run lint && npx tsc --noEmit
```

---

## Лицензия

[MIT](LICENSE) — разрешено для коммерческого использования.
