"""Music（古琴曲目）模型。"""

from __future__ import annotations

from sqlalchemy import Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Music(Base):
    """古琴曲目表。

    - ``yin_type``：五音枚举字符串（gong/shang/jue/zhi/yu）。
    - ``category``：曲目分类（classic 五音古曲 / western 古琴弹西洋曲谱）。v2.3 新增。
    - ``tags``：JSON 字符串或逗号分隔的标签列表。
    - ``audio_url``：/static/audio/xxx.mp3 的相对路径。
    """

    __tablename__ = "musics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    audio_url: Mapped[str] = mapped_column(String(255), nullable=False)
    cover_image: Mapped[str] = mapped_column(String(255), nullable=False, default="/static/images/cover_default.svg")
    yin_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(20), default="classic", nullable=False, index=True)
    duration: Mapped[float] = mapped_column(Float, default=180.0, nullable=False)
    tags: Mapped[str] = mapped_column(String(255), default="", nullable=False)

    def __repr__(self) -> str:
        return f"<Music id={self.id} title={self.title!r} yin={self.yin_type} cat={self.category}>"

    def tag_list(self) -> list[str]:
        """解析 tags 字符串为列表。"""
        return [t.strip() for t in self.tags.split(",") if t.strip()]
