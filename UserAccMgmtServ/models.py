from pydantic import BaseModel, Field, field_validator
import re


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)

    @field_validator("password")
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        # if not re.search(r"[A-Z]", value):
        #     raise ValueError("Password must contain at least one uppercase letter")
        # if not re.search(r"[a-z]", value):
        #     raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", value):
            raise ValueError("Password must contain at least one digit")
        # if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        #     raise ValueError("Password must contain at least one special character")
        return value


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):

    access_token: str
    token_type: str
