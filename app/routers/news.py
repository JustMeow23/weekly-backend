from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_session
from app.dao.user import UserDAO
from app.dao.news import NewsDAO
from app.models import User
from app.utils.auth_utils import admin_only
from app.services.fcm import send_multicast
from app.schemas import NewsPushRequest, NewsPushResponse, ChangelogItem, ChangelogCreateRequest
from app.exceptions import AppException
from app.schemas import ErrorCode

router = APIRouter(tags=["News"])


@router.get("/news", response_model=List[ChangelogItem])
async def get_news(session: AsyncSession = Depends(get_session)):
    return await NewsDAO.get_all(session)


@router.get("/news/latest", response_model=Optional[ChangelogItem])
async def get_latest_news(session: AsyncSession = Depends(get_session)):
    return await NewsDAO.get_latest(session)


@router.post("/news", response_model=ChangelogItem, status_code=201)
async def create_news(
        payload: ChangelogCreateRequest,
        session: AsyncSession = Depends(get_session),
        admin: User = Depends(admin_only),
):
    return await NewsDAO.create(session, payload.version, payload.items)


@router.delete("/news/{changelog_id}", status_code=204)
async def delete_news(
        changelog_id: int,
        session: AsyncSession = Depends(get_session),
        admin: User = Depends(admin_only),
):
    deleted = await NewsDAO.delete(session, changelog_id)
    if not deleted:
        raise AppException(status_code=404, error_code=ErrorCode.NOT_FOUND, detail="Changelog entry not found")
    return Response(status_code=204)


@router.post("/news/push", response_model=NewsPushResponse)
async def push_news(
        payload: NewsPushRequest,
        session: AsyncSession = Depends(get_session),
        admin: User = Depends(admin_only),
):
    tokens = await UserDAO.find_all_fcm_tokens(session)
    sent = await send_multicast(tokens, payload.title, payload.body)
    return NewsPushResponse(sent=sent, total_tokens=len(tokens))