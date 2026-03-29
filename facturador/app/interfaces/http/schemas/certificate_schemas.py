from pydantic import BaseModel


class CertificateIn(BaseModel):
    alias: str
    p12_path: str
    p12_password: str
    is_active: bool = True
