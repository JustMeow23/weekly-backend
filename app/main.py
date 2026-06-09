import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.routers import tasks, users, auth, common, news, ai, deeplinks, notes
from app.schemas.enums import AiFeatureKey
from app.config import settings
from app.exceptions import AppException
from contextlib import asynccontextmanager
import logging
from app.db_migrate import run_migrations
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

#TODO: Вынести в другое место
INITIAL_CHANGELOGS = [
    {
        "version": "v2.0.0",
        "items": [
            "Обновлен пользовательский интерфейс приложения (UI 2.0)",
            "Был переработан начальный экран приложения",
            "Добавлена возможность переключаться между Напоминанием и Задачей",
            "Улучшена система дублированных задач",
            "Monochrome theme получила обновление и стала частью приложения в виде Светлой темы",
            "В директорию разработчика добавлена уникальная тема приложения Nothing theme",
            "Перенос задач в платной версии тоже получил обновление",
            "Были переработаны напоминания",
        ],
    }
]


AI_FEATURE_CONFIGS = [
    {"feature_key": AiFeatureKey.SPLIT_TASK, "free_weekly_limit": 3, "description": "Разбить задачу на подзадачи"},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.get_running_loop().run_in_executor(None, run_migrations)
    from app.database import async_session
    from app.dao.news import NewsDAO
    from app.dao.ai_config import AiConfigDAO
    async with async_session() as session:
        await NewsDAO.seed(session, INITIAL_CHANGELOGS)
        await AiConfigDAO.seed(session, AI_FEATURE_CONFIGS)
    yield

app = FastAPI(title="Weekly API", lifespan=lifespan)
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router, prefix="/api")
app.include_router(notes.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(common.router, prefix="/api")
app.include_router(news.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(deeplinks.router)

@app.get("/")
async def root():
    return {"status": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=True)