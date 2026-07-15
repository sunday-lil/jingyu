"""古琴音乐相关 Pydantic。"""

from pydantic import BaseModel, Field


class MusicOut(BaseModel):
    id: int
    title: str
    audio_url: str
    cover_image: str
    yin_type: str
    duration: float
    tags: list[str]


class ListenCompleteIn(BaseModel):
    """前端在播放进度 ≥ 90% 时调用，记录「听完」以发放能量。"""
    music_id: int
    progress: float = Field(..., ge=0, le=1)
