from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class CustomerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=10, max_length=15)
    email: EmailStr | None = None

class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    phone: str | None = Field(default=None, min_length=10, max_length=15)
    email: EmailStr | None = None

class CustomerResponse(BaseModel):
    id: str
    name: str
    phone: str
    email: EmailStr | None = None 
    created_at: datetime
    updated_at: datetime