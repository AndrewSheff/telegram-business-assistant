"""
Скрипт демо-данных -- заполняет базу тестовыми данными для разработки.
Запуск: python -m scripts.seed
"""

import asyncio
import sys
from datetime import date, time, timedelta

from sqlalchemy import select

# чтобы запускалось из корня backend/
sys.path.insert(0, ".")

from app.core.security import hash_password
from app.database import async_session
from app.models import (
    Booking,
    BusinessSettings,
    ChatMessage,
    Client,
    FaqItem,
    KnowledgeBlock,
    Service,
    ServiceCategory,
    User,
    WorkingHours,
)

# ---------------------------------------------------------------------------
# хелпер -- проверяет, есть ли уже запись с таким полем
# ---------------------------------------------------------------------------


async def _get_or_create(session, model, filter_field, filter_value, **kwargs):
    """
    Ищем запись по полю, если нет -- создаем.
    Возвращает (instance, created: bool).
    """
    stmt = select(model).where(filter_field == filter_value)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return existing, False
    instance = model(**kwargs)
    session.add(instance)
    await session.flush()
    return instance, True


# ---------------------------------------------------------------------------
# 1. Пользователи админки
# ---------------------------------------------------------------------------


async def seed_users(session):
    """Создаем аккаунты владельца и оператора"""
    print("[1/11] Пользователи...")

    owner, created = await _get_or_create(
        session,
        User,
        User.email,
        "admin@demo.com",
        email="admin@demo.com",
        name="Demo Owner",
        password_hash=hash_password("demo123456"),
        role="owner",
        is_active=True,
        must_change_password=False,
    )
    if created:
        print("  + Владелец admin@demo.com создан")
    else:
        print("  . Владелец admin@demo.com уже есть, пропускаем")

    operator, created = await _get_or_create(
        session,
        User,
        User.email,
        "operator@demo.com",
        email="operator@demo.com",
        name="Наталья",
        password_hash=hash_password("demo123456"),
        role="operator",
        is_active=True,
        must_change_password=False,
    )
    if created:
        print("  + Оператор operator@demo.com создан")
    else:
        print("  . Оператор operator@demo.com уже есть, пропускаем")

    return owner, operator


# ---------------------------------------------------------------------------
# 2-3. Категории и услуги
# ---------------------------------------------------------------------------


async def seed_categories_and_services(session):
    """Категории услуг и сами услуги"""
    print("[2/11] Категории услуг...")

    categories_data = [
        {"name": "Стрижки", "sort_order": 0},
        {"name": "Окрашивание", "sort_order": 1},
        {"name": "Уход", "sort_order": 2},
    ]

    categories = {}
    for cat_data in categories_data:
        cat, created = await _get_or_create(
            session,
            ServiceCategory,
            ServiceCategory.name,
            cat_data["name"],
            **cat_data,
        )
        categories[cat_data["name"]] = cat
        label = "+" if created else "."
        print(f"  {label} Категория '{cat_data['name']}'")

    print("[3/11] Услуги...")

    services_data = [
        # стрижки
        {
            "category": "Стрижки",
            "name": "Мужская стрижка",
            "description": "Классическая мужская стрижка с консультацией мастера",
            "price": 500,
            "duration_minutes": 30,
            "sort_order": 0,
        },
        {
            "category": "Стрижки",
            "name": "Женская стрижка",
            "description": "Стрижка любой сложности, включая мытье головы и укладку",
            "price": 1200,
            "duration_minutes": 60,
            "sort_order": 1,
        },
        {
            "category": "Стрижки",
            "name": "Детская стрижка",
            "description": "Стрижка для детей до 12 лет",
            "price": 400,
            "duration_minutes": 20,
            "sort_order": 2,
        },
        # окрашивание
        {
            "category": "Окрашивание",
            "name": "Окрашивание корней",
            "description": "Окрашивание отросших корней краской премиум-класса",
            "price": 2500,
            "duration_minutes": 90,
            "sort_order": 0,
        },
        {
            "category": "Окрашивание",
            "name": "Мелирование",
            "description": "Мелирование на фольгу, любая длина волос",
            "price": 3500,
            "duration_minutes": 120,
            "sort_order": 1,
        },
        # уход
        {
            "category": "Уход",
            "name": "Кератиновое выпрямление",
            "description": "Кератиновое восстановление и выпрямление волос",
            "price": 4000,
            "duration_minutes": 150,
            "sort_order": 0,
        },
        {
            "category": "Уход",
            "name": "Маска для волос",
            "description": "Питательная маска для восстановления волос",
            "price": 800,
            "duration_minutes": 30,
            "sort_order": 1,
        },
        {
            "category": "Уход",
            "name": "Укладка",
            "description": "Профессиональная укладка феном или плойкой",
            "price": 1000,
            "duration_minutes": 45,
            "sort_order": 2,
        },
    ]

    services = {}
    for svc_data in services_data:
        cat_name = svc_data.pop("category")
        svc_data["category_id"] = categories[cat_name].id

        svc, created = await _get_or_create(
            session,
            Service,
            Service.name,
            svc_data["name"],
            **svc_data,
        )
        services[svc.name] = svc
        label = "+" if created else "."
        print(f"  {label} {svc.name} ({svc.price} руб., {svc.duration_minutes} мин.)")

    return categories, services


# ---------------------------------------------------------------------------
# 4. Рабочее расписание
# ---------------------------------------------------------------------------


async def seed_working_hours(session):
    """Расписание: Пн-Пт 9-19, обед 13-14, Сб 10-17, Вс выходной"""
    print("[4/11] Рабочее расписание...")

    # проверяем, есть ли уже расписание
    result = await session.execute(select(WorkingHours))
    existing = result.scalars().all()
    if existing:
        print("  . Расписание уже заполнено, пропускаем")
        return

    # шаблон для рабочих будней: 9:00-19:00, обед 13:00-14:00
    weekday = {
        "start_time": time(9, 0),
        "end_time": time(19, 0),
        "break_start": time(13, 0),
        "break_end": time(14, 0),
        "is_working_day": True,
    }
    schedule_data = [
        # пн-пт
        {"day_of_week": 0, **weekday},
        {"day_of_week": 1, **weekday},
        {"day_of_week": 2, **weekday},
        {"day_of_week": 3, **weekday},
        {"day_of_week": 4, **weekday},
        # суббота: 10:00-17:00, без обеда
        {
            "day_of_week": 5, "start_time": time(10, 0),
            "end_time": time(17, 0), "break_start": None,
            "break_end": None, "is_working_day": True,
        },
        # воскресенье: выходной
        {
            "day_of_week": 6, "start_time": time(0, 0),
            "end_time": time(0, 0), "break_start": None,
            "break_end": None, "is_working_day": False,
        },
    ]

    day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    for day_data in schedule_data:
        wh = WorkingHours(**day_data)
        session.add(wh)
        day_name = day_names[day_data["day_of_week"]]
        if day_data["is_working_day"]:
            print(f"  + {day_name}: {day_data['start_time']}-{day_data['end_time']}")
        else:
            print(f"  + {day_name}: выходной")

    await session.flush()


# ---------------------------------------------------------------------------
# 5. FAQ
# ---------------------------------------------------------------------------


async def seed_faq(session):
    """Часто задаваемые вопросы -- типовые, чтобы бот не тратил AI на них"""
    print("[5/11] FAQ...")

    faq_data = [
        {
            "question": "Как записаться?",
            "answer": (
                "Нажмите кнопку 'Записаться' в меню бота, выберите услугу, "
                "удобную дату и время. Подтверждение придет сообщением."
            ),
            "category": "Общие",
            "sort_order": 0,
        },
        {
            "question": "Где вы находитесь?",
            "answer": (
                "Мы находимся по адресу: ул. Примерная, д. 15, Москва. "
                "Ближайшее метро -- Примерная, 5 минут пешком. "
                "Есть парковка для клиентов."
            ),
            "category": "Общие",
            "sort_order": 1,
        },
        {
            "question": "Какие способы оплаты?",
            "answer": (
                "Принимаем наличные, банковские карты (Visa, MasterCard, МИР), "
                "а также оплату через СБП."
            ),
            "category": "Оплата",
            "sort_order": 2,
        },
        {
            "question": "Можно ли отменить запись?",
            "answer": (
                "Да, запись можно отменить минимум за 2 часа до назначенного времени. "
                "Для отмены напишите нам или используйте кнопку 'Мои записи' в боте."
            ),
            "category": "Запись",
            "sort_order": 3,
        },
        {
            "question": "Есть ли скидки?",
            "answer": (
                "Действует скидка 10% для постоянных клиентов (от 5 посещений). "
                "Также следите за нашими акциями -- мы регулярно публикуем спецпредложения."
            ),
            "category": "Оплата",
            "sort_order": 4,
        },
    ]

    for faq in faq_data:
        _, created = await _get_or_create(
            session,
            FaqItem,
            FaqItem.question,
            faq["question"],
            **faq,
        )
        label = "+" if created else "."
        print(f"  {label} {faq['question']}")


# ---------------------------------------------------------------------------
# 6. Блоки знаний
# ---------------------------------------------------------------------------


async def seed_knowledge_blocks(session):
    """Блоки знаний для AI -- контекст, который бот подтягивает при ответах"""
    print("[6/11] Блоки знаний...")

    blocks_data = [
        {
            "title": "О салоне",
            "content": (
                "Салон красоты 'Стиль' работает с 2018 года. "
                "Наша команда -- это 5 опытных мастеров с профессиональным образованием. "
                "Мы используем только премиальную косметику: L'Oreal Professionnel, Kerastase, Olaplex. "
                "Салон оборудован современным оборудованием, есть зона ожидания с кофе и чаем. "
                "Мы ценим каждого клиента и стремимся к тому, чтобы каждый визит был приятным."
            ),
            "sort_order": 0,
        },
        {
            "title": "Уход за волосами",
            "content": (
                "Советы по уходу за волосами от наших мастеров:\n"
                "1. Мойте голову теплой, а не горячей водой.\n"
                "2. Используйте кондиционер после каждого мытья.\n"
                "3. Сушите волосы естественным способом, когда это возможно.\n"
                "4. Регулярно подстригайте кончики -- раз в 2-3 месяца.\n"
                "5. Делайте питательные маски хотя бы раз в неделю.\n"
                "Подробную консультацию можно получить у наших мастеров на приеме."
            ),
            "sort_order": 1,
        },
        {
            "title": "Акции",
            "content": (
                "Текущие акции:\n"
                "- Скидка 15% на первое посещение для новых клиентов.\n"
                "- 'Приведи друга' -- 10% скидка вам и вашему другу.\n"
                "- Комплекс 'Стрижка + Укладка' со скидкой 20%.\n"
                "- Каждая 6-я стрижка бесплатно по программе лояльности.\n"
                "Акции не суммируются между собой."
            ),
            "sort_order": 2,
        },
    ]

    for block in blocks_data:
        _, created = await _get_or_create(
            session,
            KnowledgeBlock,
            KnowledgeBlock.title,
            block["title"],
            **block,
        )
        label = "+" if created else "."
        print(f"  {label} {block['title']}")


# ---------------------------------------------------------------------------
# 7. Настройки бизнеса
# ---------------------------------------------------------------------------


async def seed_business_settings(session):
    """Настройки бизнеса -- синглтон, одна запись на всю таблицу"""
    print("[7/11] Настройки бизнеса...")

    result = await session.execute(select(BusinessSettings))
    existing = result.scalar_one_or_none()

    if existing:
        print("  . Настройки уже есть, пропускаем")
        return existing

    bs = BusinessSettings(
        business_name="Салон красоты 'Стиль'",
        description="Современный салон красоты с опытными мастерами",
        address="ул. Примерная, д. 15, Москва",
        phone="+7 (999) 123-45-67",
        welcome_message=(
            "Добро пожаловать в салон 'Стиль'!\n\n"
            "Чем могу помочь?"
        ),
        offline_message="Сейчас мы не в сети. Оставьте сообщение, и мы ответим в рабочее время.",
        timezone="Europe/Moscow",
        ai_model="claude",
        min_cancel_hours=2,
    )
    session.add(bs)
    await session.flush()
    print("  + Настройки бизнеса созданы")
    return bs


# ---------------------------------------------------------------------------
# 8. Telegram-клиенты
# ---------------------------------------------------------------------------


async def seed_clients(session):
    """Демо-клиенты с фейковыми telegram_id"""
    print("[8/11] Telegram-клиенты...")

    clients_data = [
        {"telegram_id": 100000001, "first_name": "Алексей", "last_name": "Иванов", "username": "alexey_iv"},
        {"telegram_id": 100000002, "first_name": "Мария", "last_name": "Петрова", "username": "masha_p"},
        {"telegram_id": 100000003, "first_name": "Дмитрий", "last_name": None, "username": "dmitry_k"},
        {"telegram_id": 100000004, "first_name": "Елена", "last_name": "Сидорова", "username": None},
        {"telegram_id": 100000005, "first_name": "Олег", "last_name": "Козлов", "username": "oleg_kz"},
    ]

    clients = {}
    for cl_data in clients_data:
        cl, created = await _get_or_create(
            session,
            Client,
            Client.telegram_id,
            cl_data["telegram_id"],
            **cl_data,
        )
        clients[cl_data["first_name"]] = cl
        label = "+" if created else "."
        display_name = cl_data["first_name"]
        if cl_data.get("last_name"):
            display_name += f" {cl_data['last_name']}"
        print(f"  {label} {display_name} (tg_id: {cl_data['telegram_id']})")

    return clients


# ---------------------------------------------------------------------------
# 9. Записи (бронирования)
# ---------------------------------------------------------------------------


async def seed_bookings(session, clients, services):
    """Демо-записи -- микс из разных статусов и дат"""
    print("[9/11] Записи на услуги...")

    # проверяем, есть ли уже записи
    result = await session.execute(select(Booking))
    existing = result.scalars().first()
    if existing:
        print("  . Записи уже есть, пропускаем")
        return

    today = date.today()

    bookings_data = [
        # прошедшие -- завершенные
        {
            "client": "Алексей",
            "service": "Мужская стрижка",
            "booking_date": today - timedelta(days=14),
            "start_time": time(10, 0),
            "end_time": time(10, 30),
            "status": "completed",
        },
        {
            "client": "Мария",
            "service": "Женская стрижка",
            "booking_date": today - timedelta(days=10),
            "start_time": time(11, 0),
            "end_time": time(12, 0),
            "status": "completed",
        },
        {
            "client": "Мария",
            "service": "Окрашивание корней",
            "booking_date": today - timedelta(days=10),
            "start_time": time(12, 0),
            "end_time": time(13, 30),
            "status": "completed",
        },
        # прошедшая -- отмененная
        {
            "client": "Дмитрий",
            "service": "Мужская стрижка",
            "booking_date": today - timedelta(days=5),
            "start_time": time(14, 0),
            "end_time": time(14, 30),
            "status": "cancelled",
            "notes": "Клиент отменил по личным причинам",
        },
        # прошедшая -- неявка
        {
            "client": "Елена",
            "service": "Укладка",
            "booking_date": today - timedelta(days=3),
            "start_time": time(15, 0),
            "end_time": time(15, 45),
            "status": "no_show",
        },
        # будущие -- подтвержденные
        {
            "client": "Алексей",
            "service": "Мужская стрижка",
            "booking_date": today + timedelta(days=2),
            "start_time": time(10, 0),
            "end_time": time(10, 30),
            "status": "confirmed",
        },
        {
            "client": "Олег",
            "service": "Кератиновое выпрямление",
            "booking_date": today + timedelta(days=3),
            "start_time": time(11, 0),
            "end_time": time(13, 30),
            "status": "confirmed",
        },
        # будущие -- ожидают подтверждения
        {
            "client": "Мария",
            "service": "Мелирование",
            "booking_date": today + timedelta(days=5),
            "start_time": time(10, 0),
            "end_time": time(12, 0),
            "status": "pending",
        },
        {
            "client": "Елена",
            "service": "Маска для волос",
            "booking_date": today + timedelta(days=7),
            "start_time": time(16, 0),
            "end_time": time(16, 30),
            "status": "pending",
        },
        {
            "client": "Дмитрий",
            "service": "Детская стрижка",
            "booking_date": today + timedelta(days=4),
            "start_time": time(9, 0),
            "end_time": time(9, 20),
            "status": "confirmed",
            "notes": "Ребенку 7 лет",
        },
    ]

    for b_data in bookings_data:
        client = clients[b_data["client"]]
        service = services[b_data["service"]]

        booking = Booking(
            client_id=client.id,
            service_id=service.id,
            booking_date=b_data["booking_date"],
            start_time=b_data["start_time"],
            end_time=b_data["end_time"],
            status=b_data["status"],
            notes=b_data.get("notes"),
        )
        session.add(booking)
        print(
            f"  + {b_data['client']}: {b_data['service']} "
            f"({b_data['booking_date']}, {b_data['status']})"
        )

    await session.flush()


# ---------------------------------------------------------------------------
# 10. Сообщения в чатах
# ---------------------------------------------------------------------------


async def seed_chat_messages(session, clients):
    """Демо-переписки -- пара диалогов для наглядности"""
    print("[10/11] Сообщения в чатах...")

    # проверяем, есть ли уже сообщения
    result = await session.execute(select(ChatMessage))
    existing = result.scalars().first()
    if existing:
        print("  . Сообщения уже есть, пропускаем")
        return

    # диалог Алексея -- типичная запись
    alexey = clients["Алексей"]
    conversations = [
        # разговор с Алексеем
        (alexey.id, "user", "Привет! Хочу записаться на стрижку"),
        (
            alexey.id, "bot",
            "Здравствуйте, Алексей! С удовольствием помогу "
            "записаться. Какая стрижка вас интересует?",
        ),
        (alexey.id, "user", "Мужская, на ближайшие дни"),
        (
            alexey.id, "bot",
            "Отлично! Мужская стрижка -- 500 руб., 30 минут. "
            "Есть свободное время послезавтра в 10:00. Подходит?",
        ),
        (alexey.id, "user", "Да, записывайте!"),
        (
            alexey.id, "bot",
            "Готово! Вы записаны на мужскую стрижку. Ждем вас!",
        ),
    ]

    # диалог Марии -- вопрос об услугах
    maria = clients["Мария"]
    conversations += [
        (
            maria.id, "user",
            "Добрый день, подскажите, сколько стоит мелирование?",
        ),
        (
            maria.id, "bot",
            "Добрый день, Мария! Мелирование на фольгу стоит "
            "3500 руб., длительность -- около 2 часов. "
            "Хотите записаться?",
        ),
        (maria.id, "user", "Да, можно на следующую неделю?"),
        (
            maria.id, "bot",
            "Конечно! Есть время в понедельник в 10:00. Записать?",
        ),
        (maria.id, "user", "Давайте!"),
        (maria.id, "bot", "Записала вас на мелирование. До встречи!"),
    ]

    # диалог Елены -- обращение к оператору
    elena = clients["Елена"]
    conversations += [
        (elena.id, "user", "Можно с оператором поговорить?"),
        (
            elena.id, "bot",
            "Конечно! Сейчас переключу на оператора. "
            "Подождите, пожалуйста.",
        ),
        (elena.id, "operator", "Здравствуйте, Елена! Чем могу помочь?"),
        (elena.id, "user", "У меня вопрос по акции для новых клиентов"),
        (
            elena.id, "operator",
            "Для новых клиентов действует скидка 15% на первое "
            "посещение. Могу записать вас со скидкой!",
        ),
    ]

    for client_id, role, content in conversations:
        msg = ChatMessage(
            client_id=client_id,
            role=role,
            content=content,
            is_handoff=(role == "operator"),
        )
        session.add(msg)

    await session.flush()
    print(f"  + Создано {len(conversations)} сообщений в 3 диалогах")


# ---------------------------------------------------------------------------
# 11. Финальная сводка
# ---------------------------------------------------------------------------


async def print_summary(session):
    """Выводим, сколько чего в итоге в базе"""
    print("[11/11] Итого в базе:")

    counts = [
        ("Пользователей", User),
        ("Категорий", ServiceCategory),
        ("Услуг", Service),
        ("Дней расписания", WorkingHours),
        ("FAQ", FaqItem),
        ("Блоков знаний", KnowledgeBlock),
        ("Клиентов", Client),
        ("Записей", Booking),
        ("Сообщений", ChatMessage),
    ]

    for label, model in counts:
        result = await session.execute(select(model))
        total = len(result.scalars().all())
        print(f"  {label}: {total}")


# ---------------------------------------------------------------------------
# main -- точка входа
# ---------------------------------------------------------------------------


async def main():
    """Главная функция -- заполняет базу демо-данными"""
    print("=" * 50)
    print("Заполнение базы демо-данными")
    print("=" * 50)
    print()

    async with async_session() as session:
        async with session.begin():
            # пользователи
            owner, operator = await seed_users(session)

            # категории и услуги
            categories, services = await seed_categories_and_services(session)

            # расписание
            await seed_working_hours(session)

            # faq
            await seed_faq(session)

            # блоки знаний
            await seed_knowledge_blocks(session)

            # настройки бизнеса
            await seed_business_settings(session)

            # клиенты
            clients = await seed_clients(session)

            # записи
            await seed_bookings(session, clients, services)

            # сообщения
            await seed_chat_messages(session, clients)

        # сводка -- в отдельной сессии, чтобы все было закоммичено
        async with session.begin():
            await print_summary(session)

    print()
    print("Готово! Демо-данные загружены.")
    print("Вход: admin@demo.com / demo123456")


if __name__ == "__main__":
    asyncio.run(main())
