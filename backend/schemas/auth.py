from pydantic import BaseModel, EmailStr
from typing import Any, Optional


class UserRegister(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    csrf_token: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    created_at: str

    model_config = {"from_attributes": True}

    @classmethod
    def __get_validators__(cls):  # type: ignore[override]
        yield cls.model_validate

    from pydantic import field_validator

    @field_validator("created_at", mode="before")
    @classmethod
    def datetime_to_str(cls, v: Any) -> str:
        return v.isoformat() if hasattr(v, "isoformat") else v
