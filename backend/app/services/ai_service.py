"""
AI-сервис — генерация ответов на вопросы клиентов.
Подтягивает контекст бизнеса (расписание, услуги, FAQ, база знаний)
и кидает все это в Claude или GPT. Если AI не тянет — не беда, есть фоллбек.
"""

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.business_settings import BusinessSettings
from app.models.faq import FaqItem
from app.models.knowledge_block import KnowledgeBlock
from app.models.schedule import WorkingHours
from app.models.service import Service

logger = structlog.get_logger(__name__)

# Дни недели для красивого вывода в промпте
_DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Фразы, на которые AI по сути говорит «я хз» — значит пора передавать оператору
_HANDOFF_PHRASES = [
    "i don't know",
    "i'm not sure",
    "cannot answer",
    "i am not sure",
    "i do not know",
    "can't answer",
    "unable to answer",
    "don't have information",
    "do not have information",
    "не знаю",
    "не могу ответить",
    "не уверен",
    "нет информации",
    "затрудняюсь ответить",
    "не располагаю информацией",
    "обратитесь к оператору",
    "свяжитесь с нами",
]


async def generate_answer(question: str, db: AsyncSession, client_id=None) -> dict:
    """
    Главная функция — берем вопрос клиента, собираем весь контекст бизнеса
    и отправляем в AI. Возвращаем dict с answer и should_handoff.
    client_id пока не используется, но пригодится для истории диалога.
    """
    # Достаем настройки бизнеса
    result = await db.execute(select(BusinessSettings))
    biz_settings = result.scalar_one_or_none()

    business_name = (biz_settings.business_name or "Наш бизнес") if biz_settings else "Наш бизнес"
    description = (biz_settings.description or "") if biz_settings else ""
    address = (biz_settings.address or "не указан") if biz_settings else "не указан"
    phone = (biz_settings.phone or "не указан") if biz_settings else "не указан"
    website = (biz_settings.website or "не указан") if biz_settings else "не указан"
    ai_model = (biz_settings.ai_model or "claude") if biz_settings else "claude"
    custom_prompt = (biz_settings.ai_system_prompt or "") if biz_settings else ""

    # Собираем рабочие часы
    hours_result = await db.execute(
        select(WorkingHours).order_by(WorkingHours.day_of_week)
    )
    working_hours = hours_result.scalars().all()
    formatted_hours = _format_working_hours(list(working_hours))

    # Активные услуги
    services_result = await db.execute(
        select(Service).where(Service.is_active == True).order_by(Service.sort_order)  # noqa: E712
    )
    services = services_result.scalars().all()
    services_list = _format_services(list(services))

    # FAQ — только активные
    faq_result = await db.execute(
        select(FaqItem).where(FaqItem.is_active == True).order_by(FaqItem.sort_order)  # noqa: E712
    )
    faq_items = faq_result.scalars().all()
    faq_text = _format_faq(list(faq_items))

    # База знаний — тоже только активные блоки
    kb_result = await db.execute(
        select(KnowledgeBlock)
        .where(KnowledgeBlock.is_active == True)  # noqa: E712
        .order_by(KnowledgeBlock.sort_order)
    )
    knowledge_blocks = kb_result.scalars().all()
    knowledge_text = _format_knowledge(list(knowledge_blocks))

    # Собираем системный промпт по шаблону из TDD
    system_prompt = _build_system_prompt(
        business_name=business_name,
        description=description,
        address=address,
        phone=phone,
        website=website,
        formatted_hours=formatted_hours,
        services_list=services_list,
        knowledge_text=knowledge_text,
        faq_text=faq_text,
        custom_prompt=custom_prompt,
    )

    # Вызываем AI
    try:
        if ai_model.lower().startswith("gpt") or ai_model.lower() == "openai":
            response_text = await _call_openai(system_prompt, question)
        else:
            # По дефолту — Claude, наш фаворит
            response_text = await _call_anthropic(system_prompt, question)

        logger.info(
            "ai_answer_generated",
            model=ai_model,
            question_len=len(question),
            answer_len=len(response_text),
        )
        return {
            "answer": response_text,
            "should_handoff": should_handoff(response_text),
        }

    except Exception as exc:
        logger.error("ai_answer_failed", error=str(exc), model=ai_model)
        return {
            "answer": (
                "К сожалению, AI-ассистент сейчас недоступен. "
                "Пожалуйста, попробуйте позже или свяжитесь с нами напрямую."
            ),
            "should_handoff": True,
        }


def should_handoff(response: str) -> bool:
    """
    Проверяем, не сдался ли AI — если в ответе есть фразы типа
    «не знаю» или «cannot answer», пора подключать живого человека.
    """
    response_lower = response.lower()
    return any(phrase in response_lower for phrase in _HANDOFF_PHRASES)


# -- Приватные хелперы --


def _build_system_prompt(
    business_name: str,
    description: str,
    address: str,
    phone: str,
    website: str,
    formatted_hours: str,
    services_list: str,
    knowledge_text: str,
    faq_text: str,
    custom_prompt: str,
) -> str:
    """Собираем системный промпт из всего контекста бизнеса."""
    prompt = f"""You are a helpful assistant for {business_name}.
{description}

Business information:
- Address: {address}
- Phone: {phone}
- Website: {website}
- Working hours:
{formatted_hours}

Available services:
{services_list}

Knowledge base:
{knowledge_text}

FAQ:
{faq_text}

Instructions:
- Answer questions about the business politely and accurately
- If you cannot find the answer, say so and suggest contacting support
- Keep answers concise and helpful
- Respond in the same language as the question"""

    # Если владелец задал кастомный промпт — добавляем
    if custom_prompt:
        prompt += f"\n\nAdditional instructions:\n{custom_prompt}"

    return prompt


def _format_working_hours(hours: list[WorkingHours]) -> str:
    """Форматируем расписание для промпта — кратко и понятно."""
    if not hours:
        return "  Not specified"

    lines = []
    for wh in hours:
        day_name = _DAY_NAMES[wh.day_of_week] if 0 <= wh.day_of_week <= 6 else "?"
        if not wh.is_working_day:
            lines.append(f"  {day_name}: Day off")
        else:
            start = wh.start_time.strftime("%H:%M")
            end = wh.end_time.strftime("%H:%M")
            line = f"  {day_name}: {start} - {end}"
            if wh.break_start and wh.break_end:
                br_start = wh.break_start.strftime("%H:%M")
                br_end = wh.break_end.strftime("%H:%M")
                line += f" (break {br_start}-{br_end})"
            lines.append(line)

    return "\n".join(lines)


def _format_services(services: list[Service]) -> str:
    """Форматируем список услуг — название, цена, длительность."""
    if not services:
        return "  No services available"

    lines = []
    for svc in services:
        line = f"  - {svc.name}: {svc.price}₽, {svc.duration_minutes} min"
        if svc.description:
            line += f" — {svc.description}"
        lines.append(line)

    return "\n".join(lines)


def _format_faq(items: list[FaqItem]) -> str:
    """Форматируем FAQ — вопрос и ответ парами."""
    if not items:
        return "  No FAQ items"

    lines = []
    for item in items:
        lines.append(f"  Q: {item.question}")
        lines.append(f"  A: {item.answer}")
        lines.append("")

    return "\n".join(lines)


def _format_knowledge(blocks: list[KnowledgeBlock]) -> str:
    """Форматируем блоки знаний — заголовок и содержимое."""
    if not blocks:
        return "  No additional information"

    lines = []
    for block in blocks:
        lines.append(f"  [{block.title}]")
        lines.append(f"  {block.content}")
        lines.append("")

    return "\n".join(lines)


async def _call_anthropic(system_prompt: str, question: str) -> str:
    """
    Вызов Claude через Anthropic API — наш основной AI-движок.
    Температура низкая (0.3) — нам важна точность, а не креатив.
    """
    import anthropic

    api_key = settings.ANTHROPIC_API_KEY
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY не задан в настройках")

    client = anthropic.AsyncAnthropic(api_key=api_key)

    message = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        temperature=0.3,
        system=system_prompt,
        messages=[
            {"role": "user", "content": question},
        ],
    )

    # Достаем текст из ответа
    return message.content[0].text


async def _call_openai(system_prompt: str, question: str) -> str:
    """
    Вызов GPT через OpenAI API — запасной вариант, если кому-то ближе OpenAI.
    Те же параметры что и для Claude — температура 0.3, макс 500 токенов.
    """
    import openai

    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OPENAI_API_KEY не задан в настройках")

    client = openai.AsyncOpenAI(api_key=api_key)

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=500,
        temperature=0.3,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
    )

    return response.choices[0].message.content
