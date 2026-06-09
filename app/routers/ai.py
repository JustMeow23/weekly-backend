import anthropic
import json
import logging
from datetime import datetime, timezone, time as time_type
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.exceptions import AppException
from app.models import User
from app.schemas.enums import ErrorCode, AiFeatureKey
from app.schemas.ai import SplitTaskRequest, SplitTaskResponse, SubtaskSuggestion
from app.utils.auth_utils import get_current_user
from app.dao.ai_usage import AiUsageDAO
from app.dao.ai_config import AiConfigDAO

router = APIRouter(tags=["AI"])
logger = logging.getLogger(__name__)


def _get_client() -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(
        api_key=settings.ANTHROPIC_API_KEY,
        base_url=settings.ANTHROPIC_BASE_URL,
    )


def _parse_time(t: str) -> time_type:
    h, m = map(int, t.split(":"))
    return time_type(h, m)


def _distribute_slots(
    time_from: time_type, time_to: time_type, count: int
) -> list[tuple[str, str]]:
    start_min = time_from.hour * 60 + time_from.minute
    end_min = time_to.hour * 60 + time_to.minute
    total = end_min - start_min
    if total <= 0 or count <= 0:
        s = f"{time_from.hour:02d}:{time_from.minute:02d}"
        return [(s, s)] * count
    slot_len = total // count
    slots = []
    for i in range(count):
        s = start_min + i * slot_len
        e = s + slot_len if i < count - 1 else end_min
        slots.append((f"{s // 60:02d}:{s % 60:02d}", f"{e // 60:02d}:{e % 60:02d}"))
    return slots


def _build_prompt(body: SplitTaskRequest) -> str:
    return (
        f"Ты — помощник по управлению временем. "
        f"Пользователь хочет разбить задачу «{body.title}» "
        f"(с {body.timeFrom} до {body.timeTo}) на несколько подзадач.\n\n"
        f"Разбей её на 2–5 логичных подзадач. "
        f"Ответь строго JSON-массивом строк — только названия подзадач, без нумерации, без пояснений. "
        f"Пример: [\"Изучить материал\", \"Написать план\", \"Оформить результат\"]\n\n"
        f"Задача: {body.title}"
    )


def _parse_claude_response(text: str) -> list[str]:
    if "```" in text:
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        if text.startswith("json"):
            text = text[4:]
    titles = json.loads(text.strip())
    if not isinstance(titles, list) or not titles:
        raise ValueError("Not a list")
    titles = [str(t).strip() for t in titles[:5] if str(t).strip()]
    if len(titles) < 2:
        titles = titles + [titles[0]] * (2 - len(titles))
    return titles


@router.post("/ai/split-task", response_model=SplitTaskResponse)
async def split_task(
    body: SplitTaskRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    iso = now.isocalendar()
    week_number, year = iso.week, iso.year

    feature_key = AiFeatureKey.SPLIT_TASK
    limit = await AiConfigDAO.get_limit(session, feature_key)
    usage = await AiUsageDAO.get_or_create(session, current_user.id, feature_key, week_number, year)

    if usage.count >= limit:
        raise AppException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            detail=f"Бесплатный лимит ИИ исчерпан ({limit}/{limit} в неделю)",
            extra_details={"limit": limit, "used": usage.count, "feature_key": feature_key},
        )

    prompt = _build_prompt(body)
    try:
        client = _get_client()
        message = await client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = message.content[0].text.strip()
        subtask_titles = _parse_claude_response(raw_text)
    except AppException:
        raise
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        raise AppException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            detail="Ошибка при обращении к ИИ. Попробуйте ещё раз.",
        )

    time_from = _parse_time(body.timeFrom)
    time_to = _parse_time(body.timeTo)
    slots = _distribute_slots(time_from, time_to, len(subtask_titles))

    subtasks = [
        SubtaskSuggestion(title=title, timeFrom=tf, timeTo=tt)
        for title, (tf, tt) in zip(subtask_titles, slots)
    ]

    usage = await AiUsageDAO.increment(session, usage)

    return SplitTaskResponse(subtasks=subtasks, usedThisWeek=usage.count, weeklyLimit=limit)