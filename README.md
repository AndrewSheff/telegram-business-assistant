# Telegram Business Assistant

[![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![aiogram 3](https://img.shields.io/badge/aiogram-3.19-26A5E4?logo=telegram&logoColor=white)](https://aiogram.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**An all-in-one Telegram bot platform for small businesses** -- salons, clinics, studios, and service providers. Customers book appointments, ask questions, and receive notifications directly in Telegram, while business owners manage everything through a modern admin panel.

---

## Features

- **Online Booking** -- Customers browse services, pick a date and time slot, and confirm appointments without leaving Telegram.
- **AI Assistant** -- Powered by Claude or GPT, the bot answers frequently asked questions using a configurable knowledge base. When it cannot help, it hands the conversation off to a human operator.
- **Live Chat with Handoff** -- Operators can take over any conversation from the admin panel in real time.
- **Broadcast Messaging** -- Send targeted announcements and promotions to all subscribers with scheduled delivery and rate-limited sending.
- **Client CRM** -- Automatic client profiles built from Telegram interactions, with booking history and conversation logs.
- **Schedule Management** -- Define weekly working hours, lunch breaks, and per-day exceptions (holidays, sick days).
- **Service Catalog** -- Organize services into categories with duration, price, and descriptions.
- **FAQ Management** -- Maintain a structured FAQ that the bot references before falling back to AI generation.
- **Knowledge Base** -- Upload text blocks that the AI assistant uses as context for answering questions.
- **Dashboard & Analytics** -- At-a-glance metrics: bookings today, new clients, revenue, and trend charts.
- **Multi-User Access** -- Role-based access control (owner, admin, operator) for the admin panel.
- **Automated Reminders** -- Background scheduler sends booking confirmations and upcoming appointment reminders.

---

## Screenshots

| Login | Dashboard | Bookings |
|:-----:|:---------:|:--------:|
| ![Login](screenshots/login.png) | ![Dashboard](screenshots/dashboard.png) | ![Bookings](screenshots/bookings.png) |

| Services | Chat | Settings |
|:--------:|:----:|:--------:|
| ![Services](screenshots/services.png) | ![Chat](screenshots/chat.png) | ![Settings](screenshots/settings.png) |

---

## Tech Stack

### Backend

| Component | Technology |
|-----------|------------|
| Framework | FastAPI 0.115 |
| Language | Python 3.13 |
| ORM | SQLAlchemy 2.0 (async) |
| Database driver | asyncpg |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Auth | JWT (python-jose) + bcrypt |
| Telegram Bot | aiogram 3.19 |
| Task scheduler | APScheduler 3.11 |
| AI providers | Anthropic SDK, OpenAI SDK |
| Rate limiting | SlowAPI |
| Logging | structlog |
| HTTP client | httpx |

### Frontend

| Component | Technology |
|-----------|------------|
| Framework | React 19 |
| Language | TypeScript 6.0 |
| Build tool | Vite 8 |
| Styling | Tailwind CSS 4 |
| UI components | shadcn/ui 4 |
| Data fetching | TanStack React Query 5 |
| HTTP client | Axios |
| Charts | Recharts 3 |
| Routing | React Router 7 |
| Icons | Lucide React |
| Linter | oxlint |

### Infrastructure

| Component | Technology |
|-----------|------------|
| Containerization | Docker Compose |
| Reverse proxy | Nginx (Alpine) |
| Database | PostgreSQL 16 (Alpine) |
| Cache / message broker | Redis 7 (Alpine) |
| CI/CD | GitHub Actions |

---

## Architecture

```
                          +------------------+
                          |     Nginx:80     |
                          +--------+---------+
                                   |
                    +--------------+--------------+
                    |                             |
            +-------+-------+           +--------+--------+
            | Frontend:3000 |           |  Backend:8000   |
            |  React SPA    |           |  FastAPI + Bot  |
            +---------------+           +---+----+----+---+
                                            |    |    |
                              +-------------+    |    +-----------+
                              |                  |                |
                     +--------+---+    +---------+----+    +------+------+
                     | PostgreSQL |    |    Redis     |    | Telegram    |
                     |   :5432    |    |    :6379     |    | Bot API     |
                     +------------+    +--------------+    +------+------+
                                                                  |
                                                           +------+------+
                                                           |  APScheduler|
                                                           |  Reminders  |
                                                           |  Broadcasts |
                                                           +-------------+
```

---

## Quick Start

### Prerequisites

- Docker and Docker Compose v2+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- (Optional) Anthropic or OpenAI API key for the AI assistant

### 1. Clone the repository

```bash
git clone https://github.com/your-org/telegram-business-assistant.git
cd telegram-business-assistant
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

```dotenv
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
SECRET_KEY=change-me-to-a-random-32-char-string
ADMIN_EMAIL=admin@yourcompany.com
ADMIN_DEFAULT_PASSWORD=YourSecurePassword
```

### 3. Start the application

```bash
docker compose up -d
```

The application will be available at `http://localhost`. Log in to the admin panel with the credentials defined in `.env`.

### 4. Verify the deployment

```bash
curl http://localhost/api/v1/health
```

---

## API Documentation

Interactive API documentation is available at `/docs` (Swagger UI) after starting the application.

| Endpoint Group | Prefix | Description |
|----------------|--------|-------------|
| Auth | `/api/v1/auth` | Login, token refresh, password change |
| Dashboard | `/api/v1/dashboard` | Aggregated metrics and statistics |
| Services | `/api/v1/services` | Service catalog CRUD with categories |
| Schedule | `/api/v1/schedule` | Weekly hours and per-day exceptions |
| Bookings | `/api/v1/bookings` | Booking management, status transitions |
| Clients | `/api/v1/clients` | Client profiles and history |
| FAQ | `/api/v1/faq` | Frequently asked questions CRUD |
| Knowledge | `/api/v1/knowledge` | AI knowledge base blocks |
| Broadcasts | `/api/v1/broadcasts` | Mass messaging campaigns |
| Chat | `/api/v1/chat` | Live chat, conversation list, handoff |
| Settings | `/api/v1/settings` | Business profile and bot configuration |
| Users | `/api/v1/users` | Admin user management and roles |
| Health | `/api/v1/health` | Liveness and readiness probes |

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

Users can also send free-text messages at any time. The AI assistant will attempt to answer using the knowledge base and FAQ. If it cannot provide a satisfactory response, it offers to connect the user with a human operator.

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | -- | Bot token from @BotFather |
| `SECRET_KEY` | Yes | -- | JWT signing key (min 32 characters) |
| `DATABASE_URL` | No | `postgresql+asyncpg://postgres:postgres@postgres:5432/tg_business_bot` | PostgreSQL connection string |
| `POSTGRES_PASSWORD` | No | `postgres` | PostgreSQL password |
| `REDIS_URL` | No | `redis://redis:6379/0` | Redis connection string |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | JWT token lifetime |
| `ADMIN_EMAIL` | No | `admin@company.com` | Initial owner account email |
| `ADMIN_NAME` | No | `Admin` | Initial owner account name |
| `ADMIN_DEFAULT_PASSWORD` | No | `ChangeMe123` | Initial owner account password |
| `ANTHROPIC_API_KEY` | No | -- | Anthropic API key for Claude |
| `OPENAI_API_KEY` | No | -- | OpenAI API key for GPT |
| `LOG_LEVEL` | No | `INFO` | Application log level |
| `CORS_ORIGINS` | No | `["http://localhost:3000","http://localhost"]` | Allowed CORS origins (JSON array) |
| `TIMEZONE` | No | `UTC` | Business timezone |

---

## Project Structure

```
telegram-business-assistant/
|-- docker-compose.yml
|-- .env.example
|-- LICENSE
|-- backend/
|   |-- requirements.txt
|   |-- Dockerfile
|   |-- app/
|   |   |-- main.py                  # FastAPI application entry point
|   |   |-- config.py                # Pydantic settings
|   |   |-- database.py              # Async SQLAlchemy engine & session
|   |   |-- api/v1/                  # REST API routers
|   |   |   |-- auth.py
|   |   |   |-- bookings.py
|   |   |   |-- broadcasts.py
|   |   |   |-- chat.py
|   |   |   |-- clients.py
|   |   |   |-- dashboard.py
|   |   |   |-- faq.py
|   |   |   |-- health.py
|   |   |   |-- knowledge.py
|   |   |   |-- schedule.py
|   |   |   |-- services_mgmt.py
|   |   |   |-- settings.py
|   |   |   +-- users.py
|   |   |-- bot/                     # Telegram bot module
|   |   |   |-- bot.py               # Bot instance and webhook setup
|   |   |   |-- middlewares.py        # DB session middleware for handlers
|   |   |   |-- handlers/            # Conversation handlers
|   |   |   |   |-- start.py
|   |   |   |   |-- booking.py       # FSM-based booking flow
|   |   |   |   |-- my_bookings.py
|   |   |   |   |-- services.py
|   |   |   |   |-- faq.py
|   |   |   |   |-- ai_chat.py       # AI responses + human handoff
|   |   |   |   +-- handoff.py
|   |   |   |-- keyboards/           # Inline and reply keyboards
|   |   |   +-- states/              # FSM state groups
|   |   |-- models/                  # SQLAlchemy ORM models
|   |   |-- schemas/                 # Pydantic v2 request/response schemas
|   |   |-- services/                # Business logic layer
|   |   |-- tasks/                   # Background jobs
|   |   |   |-- scheduler.py         # APScheduler configuration
|   |   |   |-- reminders.py         # Booking reminder jobs
|   |   |   +-- broadcast_sender.py  # Rate-limited broadcast queue
|   |   +-- core/                    # Security, dependencies, exceptions
|   +-- tests/                       # 48 pytest tests
|       |-- conftest.py
|       |-- test_auth.py
|       |-- test_bookings.py
|       |-- test_bot_handlers.py
|       +-- ...
|-- frontend/
|   |-- package.json
|   |-- Dockerfile
|   |-- src/
|   |   |-- main.tsx
|   |   |-- App.tsx
|   |   |-- api/                     # Axios API clients
|   |   |-- hooks/                   # React Query hooks
|   |   |-- contexts/                # Auth context provider
|   |   |-- components/              # Shared UI components
|   |   |-- pages/                   # Route page components
|   |   |   |-- LoginPage.tsx
|   |   |   |-- DashboardPage.tsx
|   |   |   |-- BookingsPage.tsx
|   |   |   |-- ServicesPage.tsx
|   |   |   |-- SchedulePage.tsx
|   |   |   |-- ClientsPage.tsx
|   |   |   |-- ClientDetailPage.tsx
|   |   |   |-- ChatPage.tsx
|   |   |   |-- BroadcastsPage.tsx
|   |   |   |-- FaqPage.tsx
|   |   |   |-- KnowledgePage.tsx
|   |   |   |-- SettingsPage.tsx
|   |   |   |-- UsersPage.tsx
|   |   |   +-- ...
|   |   |-- types/                   # TypeScript type definitions
|   |   +-- lib/                     # Utilities and constants
|   +-- ...
+-- docker/
    +-- nginx/
        +-- nginx.conf               # Reverse proxy configuration
```

---

## Development

### Running the backend locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start PostgreSQL and Redis (use Docker or local instances)
docker compose up -d postgres redis

export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/tg_business_bot
export REDIS_URL=redis://localhost:6379/0
export SECRET_KEY=dev-secret-key-change-in-production
export TELEGRAM_BOT_TOKEN=your-token-here

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running the frontend locally

```bash
cd frontend
npm install
npm run dev
```

The dev server starts at `http://localhost:5173` with hot module replacement.

### Linting

```bash
# Backend
cd backend && ruff check .

# Frontend
cd frontend && npm run lint
```

---

## Testing

The project includes 48 tests covering authentication, booking logic, bot handlers, broadcasts, scheduling, and AI service integration.

```bash
cd backend
pip install pytest pytest-asyncio httpx
pytest -v
```

---

## Bot Setup

1. Open Telegram and message [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the prompts to choose a name and username.
3. Copy the token and set it as `TELEGRAM_BOT_TOKEN` in your `.env` file.
4. (Optional) Send `/setcommands` to BotFather and paste:
   ```
   book - Book an appointment
   my_bookings - View my bookings
   services - Browse services
   faq - Frequently asked questions
   help - Show available commands
   ```
5. Start the application with `docker compose up -d`. The bot will begin polling for updates automatically.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
