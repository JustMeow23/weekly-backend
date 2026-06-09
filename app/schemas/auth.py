from typing import Optional
import re
from .user import User
from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=8, max_length=72, examples=["LikonPassword1234"])
    fullName: str = Field(min_length=2, max_length=200, examples=["Likon"])
    referralCode: Optional[str] = Field(default=None, max_length=100)
    captchaToken: Optional[str] = Field(default=None)
    verificationCode: Optional[str] = Field(default=None, min_length=6, max_length=6)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.match(r"^(?=.*[A-Za-z])(?=.*\d).+$", v):
            raise ValueError("Password does not match pattern")
        return v


class SendCodeRequest(BaseModel):
    email: EmailStr = Field(max_length=254)
    captchaToken: Optional[str] = Field(default=None)


class SendCodeResponse(BaseModel):
    message: str
    retryAfterSeconds: int = 0


class LoginRequest(BaseModel):
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=8, max_length=72)


class AuthResponse(BaseModel):
    accessToken: str
    refreshToken: str
    expiresIn: int
    user: User

class RefreshTokenRequest(BaseModel):
    refreshToken: str


class ChangePasswordRequest(BaseModel):
    oldPassword: str = Field(min_length=8, max_length=72)
    newPassword: str = Field(min_length=8, max_length=72, examples=["LikonPassword1234"])

    @field_validator("newPassword")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if not re.match(r"^(?=.*[A-Za-z])(?=.*\d).+$", v):
            raise ValueError("Password does not match pattern")
        return v