"""User and UserSession models"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone
from typing import Optional


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(alias="_id")
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
