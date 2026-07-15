"""Encouragement（陌生人鼓励语）模型。"""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Encouragement(Base):
    """陌生人鼓励语表。

    用户拾取陌生人的漂流瓶后，可留下一条匿名鼓励语，对方在「我的瓶子」详情页能看到。
    - ``from_user_id``：拾取者（用于防刷，但展示给日记所有者时匿名）
    - ``to_user_id``：日记所有者
    - ``diary_id``：被鼓励的日记
    - ``content``：鼓励文本（<= 200 字）
    """

    __tablename__ = "encouragements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    from_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    to_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    diary_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("diaries.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False
    )

    # 关系
    diary: Mapped["Diary"] = relationship("Diary", back_populates="encouragements")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<Encouragement id={self.id} from={self.from_user_id} to={self.to_user_id} diary={self.diary_id}>"
