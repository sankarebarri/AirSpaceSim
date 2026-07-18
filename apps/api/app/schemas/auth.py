"""Authentication and profile API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=80)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class ProfileUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=80)
    preferred_language: str | None = Field(default=None, max_length=8)


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str | None
    preferred_language: str
    created_at: datetime

    model_config = {"from_attributes": True}
