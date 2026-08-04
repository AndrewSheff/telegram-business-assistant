<div align="center">

# Telegram Business Assistant

### All-in-One Telegram Bot Platform for Service Businesses

[![CI/CD](https://github.com/AndrewSheff/telegram-business-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/AndrewSheff/telegram-business-assistant/actions)
[![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![TypeScript 6](https://img.shields.io/badge/TypeScript-6-3178C6?logo=typescript&logoColor=white)](https://typescriptlang.org)
[![aiogram 3](https://img.shields.io/badge/aiogram-3.19-26A5E4?logo=telegram&logoColor=white)](https://aiogram.dev)
[![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Turn Telegram into a complete business management platform.**
Customers book appointments, ask questions, and get reminders directly in Telegram. Business owners manage everything through a modern admin panel with AI-powered chat, CRM, broadcasts, and analytics.

[Quick Start](#-quick-start) &bull; [Features](#-features) &bull; [Architecture](#-architecture) &bull; [API](#-api-documentation) &bull; [Bot Commands](#-telegram-bot-commands)

</div>

---

## The Problem

> Service businesses (salons, clinics, studios) spend **3-5 hours daily** answering the same questions, managing appointments manually, and chasing no-shows. Clients call, wait on hold, and leave. **40% of bookings** happen outside business hours when nobody picks up the phone.

**Telegram Business Assistant** solves this with a single platform that works 24/7: an AI-powered Telegram bot handles bookings and questions, while operators manage everything from a web admin panel. When the bot can't answer, it seamlessly hands the conversation to a human.

**Key metrics:**
- 16,800+ lines of production-ready code
- 55 API endpoints with Swagger documentation
- 14 database models with Alembic migrations
- 16 admin panel pages
- 48 automated tests
- CI/CD pipeline with GitHub Actions
- Docker Compose: one command to deploy

---

## Screenshots

| Login | Dashboard | Bookings |
|:-----:|:---------:|:--------:|
| ![Login](screenshots/login.png) | ![Dashboard](screenshots/dashboard.png) | ![Bookings](screenshots/bookings.png) |

| Services | Chat | Settings |
|:--------:|:----:|:--------:|
| ![Services](screenshots/services.png) | ![Chat](screenshots/chat.png) | ![Settings](screenshots/settings.png) |

---

## Features

### Online Booking via Telegram
Customers browse services, pick a date and available time slot, and confirm appointments without leaving Telegram. FSM-based booking flow with conflict detection and `SELECT FOR UPDATE` locking to prevent double-bookings.

### AI Assistant with Handoff
Powered by **Claude** or **GPT**, the bot answers customer questions using the business knowledge base and FAQ. It detects when it can't help and offers to connect the customer with a live operator. All context is preserved during handoff.

### Live Chat & Operator Panel
Real-time chat interface in the admin panel. Operators see all active conversations, unread counts, and can take over from the AI at any point. Supports multiple operators with role-based access.

### Broadcast Messaging
Send targeted announcements to all subscribers with rate-limited delivery (respects Telegram API limits). Track delivery stats, view per-message logs, and schedule campaigns.

### Built-in CRM
Automatic client profiles from Telegram interactions. View booking history, conversation logs, and client details. Search and filter by name, phone, or Telegram username.

### Schedule Management
Define weekly working hours with lunch breaks. Override specific dates for holidays, sick days, or special hours. The booking bot automatically shows only available time slots.

### Service Catalog
Organize services into categories with duration, price, and descriptions. Services feed directly into the Telegram booking flow and admin analytics.

### FAQ & Knowledge Base
Structured FAQ with categories that the bot checks before calling the AI. Separate knowledge base blocks for detailed context the AI uses when generating answers.

### Dashboard & Analytics
Real-time metrics: bookings today, new clients this week, total revenue. Activity charts (7d/30d), popular services, and booking status distribution.

### Automated Reminders
APScheduler sends booking confirmations, 24-hour reminders, and 2-hour reminders. Automatic no-show detection for past bookings without confirmation.

### Multi-User Access
Role-based access control: **Owner** (full access), **Operator** (chat and bookings). Owner manages users, settings, and broadcasts; operators focus on client interactions.

### Enterprise Security
JWT authentication with bcrypt password hashing. Forced password change on first login. Rate limiting on auth endpoints. Request ID tracing and structured JSON logging.

---

## Architecture

```
                          +------------------+
                          |     Nginx:80     |
                          |  Reverse Proxy   |
                          +--------+---------+
                                   |
                    +--------------+--------------+
                    |                             |
            +-------+-------+           +--------+--------+
            | Frontend:3000 |           |  Backend:8000   |
            |  React 19 SPA |           |  FastAPI + Bot  |
            +---------------+           +---+----+----+---+
                                            |    |    |
                              +-------------+    |    +-----------+
                              |                  |                |
                     +--------+---+    +---------+----+    +------+------+
                     | PostgreSQL |    |    Redis     |    |  Telegram   |
                     |   :5432    |    |    :6379     |    |  Bot API    |
                     |  14 models |    |  Rate Limit  |    +------+------+
                     +------------+    +--------------+           |
                                                           +------+------+
                                                           | APScheduler |
                                                           | Reminders   |
                                                           | Broadcasts  |
                                                           +-------------+
```

### How the Bot Works

```
Customer sends message in Telegram
        |
        v
  [aiogram handler]
        |
        +---> /book    --> FSM: select service -> date -> time -> confirm
        +---> /faq     --> Show FAQ categories and answers
        +---> /services --> Display service catalog
        +---> /my_bookings --> List & cancel bookings
        +---> free text --> AI pipeline:
                              1. Check FAQ for exact match
                              2. Build context (schedule, services, knowledge base)
                              3. Call Claude/GPT with full context
                              4. If AI uncertain --> offer handoff to operator
                              5. Operator takes over in admin panel
```

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **Backend** | Python, FastAPI, SQLAlchemy (async), Alembic | 3.13, 0.115, 2.0 |
| **Telegram Bot** | aiogram, APScheduler | 3.19, 3.11 |
| **Frontend** | React, TypeScript, Vite, TailwindCSS, shadcn/ui | 19, 6.0, 8, v4 |
| **Database** | PostgreSQL | 16 |
| **Cache** | Redis | 7 |
| **AI** | Anthropic Claude, OpenAI GPT | Latest |
| **Auth** | JWT (python-jose) + bcrypt | HS256 |
| **Infra** | Docker Compose, Nginx, GitHub Actions | Multi-stage |
| **Logging** | structlog (JSON) | Request tracing |
| **Testing** | Pytest (async), 48 tests | 10 test files |

---

## Quick Start

### Prerequisites
- Docker & Docker Compose v2+
- Telegram bot token from [@BotFather](https://t.me/BotFather)
- (Optional) Anthropic or OpenAI API key for AI chat

### 1. Clone and configure

```bash
git clone https://github.com/AndrewSheff/telegram-business-assistant.git
cd telegram-business-assistant
cp .env.example .env
```

Edit `.env`:

```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
SECRET_KEY=your-random-32-char-secret-key-here
ADMIN_EMAIL=admin@yourcompany.com
ADMIN_DEFAULT_PASSWORD=SecurePass123
ANTHROPIC_API_KEY=sk-ant-...       # optional, for AI chat
```

### 2. Launch

```bash
docker compose up -d
```

### 3. Access

| Service | URL |
|---------|-----|
| Admin Panel | http://localhost |
| API Docs (Swagger) | http://localhost/docs |
| Health Check | http://localhost/api/v1/health |

Login with admin credentials from `.env`. You'll be prompted to change the password on first login.

### 4. Configure the bot

Go to **Settings** in the admin panel. Set your business name, working hours, and add services. The Telegram bot will automatically use this data for bookings and AI answers.

---

## API Documentation

Interactive Swagger documentation at `/docs`. **55 endpoints** across 13 groups:

| Group | Prefix | Description |
|-------|--------|-------------|
| **Auth** | `/api/v1/auth` | Login, password change, token refresh |
| **Dashboard** | `/api/v1/dashboard` | Aggregated metrics and charts |
| **Services** | `/api/v1/services` | Service catalog CRUD with categories |
| **Schedule** | `/api/v1/schedule` | Weekly hours and day exceptions |
| **Bookings** | `/api/v1/bookings` | Booking management, status transitions |
| **Clients** | `/api/v1/clients` | Client profiles and booking history |
| **FAQ** | `/api/v1/faq` | FAQ CRUD with categories |
| **Knowledge** | `/api/v1/knowledge` | AI knowledge base blocks |
| **Broadcasts** | `/api/v1/broadcasts` | Mass messaging campaigns |
| **Chat** | `/api/v1/chat` | Live chat, conversations, handoff |
| **Settings** | `/api/v1/settings` | Business profile configuration |
| **Users** | `/api/v1/users` | Admin user management and roles |
| **Health** | `/api/v1/health` | Liveness and readiness probes |

All endpoints use Pydantic v2 validation, structured error responses, and rate limiting.

---

## Telegram Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and main menu |
| `/book` | Start the booking flow (select service, date, time) |
| `/my_bookings` | View and cancel upcoming bookings |
| `/services` | Browse the service catalog |
| `/faq` | View frequently asked questions |
| `/help` | Show available commands |

Users can send free-text messages at any time. The AI assistant answers using the knowledge base and FAQ. If it can't help, it offers to connect with a human operator.

---

## Project Structure

```
telegram-business-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app with lifespan
│   │   ├── config.py                # Pydantic settings from .env
│   │   ├── database.py              # Async SQLAlchemy engine
│   │   ├── api/v1/                  # 13 REST API routers
│   │   ├── bot/                     # Telegram bot module
│   │   │   ├── bot.py               # Bot instance and polling
│   │   │   ├── middlewares.py        # DB session middleware
│   │   │   ├── handlers/            # FSM handlers (booking, chat, FAQ)
│   │   │   ├── keyboards/           # Inline and reply keyboards
│   │   │   └── states/              # FSM state groups
│   │   ├── models/                  # 14 SQLAlchemy models
│   │   ├── schemas/                 # Pydantic v2 schemas
│   │   ├── services/                # Business logic layer
│   │   ├── tasks/                   # APScheduler jobs
│   │   └── core/                    # Security, logging, exceptions
│   ├── tests/                       # 48 pytest tests (10 files)
│   ├── Dockerfile                   # Multi-stage build
│   └── entrypoint.sh                # Migrations + server
├── frontend/
│   ├── src/
│   │   ├── api/                     # Axios clients with JWT interceptor
│   │   ├── hooks/                   # React Query custom hooks
│   │   ├── contexts/                # Auth context provider
│   │   ├── components/              # UI components (layout, shared)
│   │   ├── pages/                   # 16 page components
│   │   ├── types/                   # TypeScript interfaces
│   │   └── lib/                     # Utilities
│   └── Dockerfile                   # Node build + Nginx serve
├── docker/nginx/                    # Reverse proxy config
├── .github/workflows/               # CI (lint + test + build)
├── docker-compose.yml               # 5 services with health checks
└── .env.example
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | -- | Bot token from @BotFather |
| `SECRET_KEY` | Yes | -- | JWT signing key (min 32 chars) |
| `ADMIN_EMAIL` | No | `admin@company.com` | Initial owner email |
| `ADMIN_DEFAULT_PASSWORD` | No | -- | Initial owner password |
| `DATABASE_URL` | No | Auto-configured | PostgreSQL async connection |
| `REDIS_URL` | No | Auto-configured | Redis connection |
| `ANTHROPIC_API_KEY` | No | -- | Anthropic API key for Claude |
| `OPENAI_API_KEY` | No | -- | OpenAI API key for GPT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | JWT token lifetime |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |
| `CORS_ORIGINS` | No | `localhost` | Allowed CORS origins |
| `TIMEZONE` | No | `UTC` | Business timezone |

---

## Development

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

docker compose up -d postgres redis
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev    # http://localhost:5173
```

### Testing

```bash
cd backend && pytest tests/ -v
```

48 tests across 10 files covering auth, bookings, bot handlers, broadcasts, scheduling, clients, and AI service.

### Linting

```bash
ruff check backend/             # Python
cd frontend && npm run lint     # TypeScript (oxlint)
npx tsc --noEmit                # Type check
```

---

## Bot Setup

1. Message [@BotFather](https://t.me/BotFather) in Telegram and send `/newbot`
2. Copy the token and set `TELEGRAM_BOT_TOKEN` in `.env`
3. (Optional) Send `/setcommands` to BotFather:
   ```
   book - Book an appointment
   my_bookings - View my bookings
   services - Browse services
   faq - Frequently asked questions
   help - Show available commands
   ```
4. Start the app with `docker compose up -d` -- the bot begins polling automatically

---

## License

[MIT](LICENSE) -- free for commercial use.
