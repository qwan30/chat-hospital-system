"""Các schema Pydantic cơ sở dùng chung cho toàn hệ thống API.

Cung cấp cấu hình mặc định như tương thích ORM mode và cho phép gán thuộc tính bằng field name.
"""

from pydantic import BaseModel


class ApiSchema(BaseModel):
    """Lớp nền (Base Schema) cho tất cả các Pydantic schema trả về từ API."""
    class Config:
        orm_mode = True
        allow_population_by_field_name = True

