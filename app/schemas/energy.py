"""能量 / 兑换相关 Pydantic。"""

from typing import Optional, List

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
    new_leaves: int = 0
    garden_item: dict
    # v2.4.2：附加资源变动信息（种满 10 朵花 → 花间客徽章）
    badge_new_leaves: int = 0
    badge_leaves_balance: int = 0
    new_badges: Optional[List[dict]] = None
