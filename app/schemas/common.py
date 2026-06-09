from pydantic import BaseModel


class PingResponse(BaseModel):
    status: str = "ok"


class AppStatusResponse(BaseModel):
    captcha: bool
    emailCode: bool
