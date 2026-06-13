from datetime import datetime

from fastapi_users import schemas
from pydantic import BaseModel, Field


class UserRead(schemas.BaseUser[int]):
    role: str = Field(pattern="^(client|counselor)$")
    display_name: str | None = None
    created_at: datetime | None = None


class UserCreate(schemas.BaseUserCreate):
    role: str = Field(default="client", pattern="^(client|counselor)$")
    display_name: str | None = Field(default=None, max_length=120)


class UserUpdate(schemas.BaseUserUpdate):
    display_name: str | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
