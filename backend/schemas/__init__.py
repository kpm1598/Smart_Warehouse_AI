"""Pydantic v2 request schemas."""
from typing import Optional

from pydantic import BaseModel, Field, field_validator


def _clean_name(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("Product name must not be empty")
    return cleaned


class ProductCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        return _clean_name(v)


class StoreRequest(BaseModel):
    product_name: str
    quantity: int = Field(gt=0)

    @field_validator("product_name")
    @classmethod
    def validate_name(cls, v):
        return _clean_name(v)


class DispatchRequest(BaseModel):
    product_name: str
    quantity: int = Field(gt=0)

    @field_validator("product_name")
    @classmethod
    def validate_name(cls, v):
        return _clean_name(v)


class GreedySearchRequest(BaseModel):
    start_location: str = "RECEIVING"
    goal_location: Optional[str] = None
    quantity_required: Optional[int] = Field(default=None, gt=0)


class DLSSearchRequest(BaseModel):
    start_location: str = "RECEIVING"
    goal_location: str
    depth_limit: int = Field(ge=0)


class CompareRequest(BaseModel):
    start_location: str = "RECEIVING"
    goal_location: str
    depth_limit: int = Field(ge=0)


class ConnectionPatch(BaseModel):
    is_blocked: bool
