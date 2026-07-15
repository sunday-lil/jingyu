"""能量 / 兑换相关 Pydantic。"""

from typing import Optional

from pydantic import BaseModel, Field


class EnergyRecordOut(BaseModel):
    id: int
    amount: int
    source: str
    note: Optional[str] = None
    created_at: str


class ExchangeIn(BaseModel):
    item_id: int = Field(..., gt=0)


class ExchangeOut(BaseModel):
    success: bool
    new_total_energy: int
    garden_item: dict
