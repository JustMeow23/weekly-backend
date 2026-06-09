from fastapi import APIRouter, Depends, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import User as UserSchema, UserUpdateRequest, UserRole, ErrorCode, PagedUsers, FcmTokenRequest
from app.models import User
from app.utils.auth_utils import get_current_user, admin_only, get_password_hash
from app.database import get_session
from app.dao.user import UserDAO
from app.exceptions import AppException
from app.schemas.auth import RegisterRequest
from app.services.s3 import upload_avatar
from sqlalchemy.exc import IntegrityError

from typing import List
import uuid

router = APIRouter(tags=["Users"])


@router.get("/users", response_model=PagedUsers)
async def get_users(
        page: int = Query(0, ge=0),
        size: int = Query(20, ge=1, le=100),
        session: AsyncSession = Depends(get_session),
        admin: User = Depends(admin_only)
):
    """Admin only. Get all users"""
    items, total = await UserDAO.find_all_paged(session, page, size)
    return PagedUsers(items=items, total=total, page=page, size=size)


@router.get("/users/me", response_model=UserSchema)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/users/me", response_model=UserSchema)
async def update_me(
        update_data: UserUpdateRequest,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    update_dict = update_data.model_dump(exclude_unset=True)

    if current_user.role != UserRole.ADMIN:
        if "role" in update_dict and update_dict["role"] != current_user.role:
            raise AppException(status_code=status.HTTP_403_FORBIDDEN,
                               error_code=ErrorCode.FORBIDDEN,
                               detail="Cannot change role")
        if "is_active" in update_dict and update_dict["is_active"] != current_user.is_active:
            raise AppException(status_code=status.HTTP_403_FORBIDDEN,
                               error_code=ErrorCode.FORBIDDEN,
                               detail="Cannot change isActive")

        update_dict.pop("role", None)
        update_dict.pop("is_active", None)

    updated_user = await UserDAO.update(session, current_user, update_dict)
    return updated_user


ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png"}
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("/users/me/avatar", response_model=UserSchema)
async def upload_my_avatar(
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    if file.content_type not in ALLOWED_AVATAR_TYPES:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=ErrorCode.BAD_REQUEST,
            detail="Недопустимый формат файла. Разрешены: jpeg, png"
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_AVATAR_SIZE:
        raise AppException(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=ErrorCode.BAD_REQUEST,
            detail="Файл слишком большой. Максимальный размер: 5 МБ"
        )

    avatar_url = await upload_avatar(file_bytes, file.content_type)
    updated_user = await UserDAO.update(session, current_user, {"avatar_url": avatar_url})
    return updated_user


@router.post("/users/me/fcm-token", status_code=status.HTTP_204_NO_CONTENT)
async def register_fcm_token(
        body: FcmTokenRequest,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    await UserDAO.update(session, current_user, {"fcm_token": body.token})


@router.get("/users/{user_id}", response_model=UserSchema)
async def get_user_by_id(
        user_id: uuid.UUID,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    """Admin only. Get a user by id"""
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise AppException(status_code=status.HTTP_403_FORBIDDEN,
                           error_code=ErrorCode.FORBIDDEN)

    user = await UserDAO.find_by_id(session, user_id)
    if not user:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND,
                           error_code=ErrorCode.NOT_FOUND)
    return user


@router.put("/users/{user_id}", response_model=UserSchema)
async def update_user(
        user_id: uuid.UUID,
        update_data: UserUpdateRequest,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    """Admin only. Update a user"""
    user_to_update = await UserDAO.find_by_id(session, user_id)
    if not user_to_update:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND,
                           error_code=ErrorCode.NOT_FOUND)

    # Если пользователь хочет обновить не себя
    if current_user.role != UserRole.ADMIN and current_user.id != user_to_update.id:
        raise AppException(status_code=status.HTTP_403_FORBIDDEN,
                           error_code=ErrorCode.FORBIDDEN)

    update_dict = update_data.model_dump(exclude_unset=True)

    if current_user.role != UserRole.ADMIN:
        # Если пользователь хочет обновить role или isActive
        if "role" in update_dict and update_dict["role"] != current_user.role:
            raise AppException(status_code=status.HTTP_403_FORBIDDEN,
                               error_code=ErrorCode.FORBIDDEN,
                               detail="Cannot change role")
        if "is_active" in update_dict and update_dict["is_active"] != user_to_update.is_active:
            raise AppException(status_code=status.HTTP_403_FORBIDDEN,
                               error_code=ErrorCode.FORBIDDEN,
                               detail="Cannot change isActive")

    update_dict.pop("role", None)
    update_dict.pop("is_active", None)

    updated_user = await UserDAO.update(session, user_to_update, update_dict)
    return updated_user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
        user_id: uuid.UUID,
        session: AsyncSession = Depends(get_session),
        admin: User = Depends(admin_only)
):
    """Admin only. Delete a user"""
    user_to_delete = await UserDAO.find_by_id(session, user_id)
    if not user_to_delete:
        raise AppException(status_code=status.HTTP_404_NOT_FOUND,
                           error_code=ErrorCode.NOT_FOUND)

    if user_to_delete.id == admin.id:
        raise AppException(status_code=status.HTTP_403_FORBIDDEN,
                           error_code=ErrorCode.FORBIDDEN,
                           detail="Cannot deactivate yourself")

    await UserDAO.update(session, user_to_delete, {"is_active": False})
    return None


@router.post("/users", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
        user_data: RegisterRequest,
        session: AsyncSession = Depends(get_session),
        admin: User = Depends(admin_only)
):
    existing_user = await UserDAO.find_by_email(session, user_data.email)
    if existing_user:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            error_code=ErrorCode.EMAIL_ALREADY_EXISTS,
            detail="User already exists"
        )

    data = user_data.model_dump(by_alias=False)
    data["password"] = get_password_hash(data["password"])
    data["role"] = UserRole.USER
    data["is_active"] = True

    try:
        new_user = await UserDAO.add(session, data)
        return new_user
    except IntegrityError:
        raise AppException(
            status_code=status.HTTP_409_CONFLICT,
            error_code=ErrorCode.EMAIL_ALREADY_EXISTS,
            detail="User already exists"
        )
