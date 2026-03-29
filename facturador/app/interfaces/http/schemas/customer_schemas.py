from pydantic import BaseModel, EmailStr


class CustomerIn(BaseModel):
    name: str
    id_type: str
    id_number: str
    email: EmailStr | None = None
    address: str | None = None
