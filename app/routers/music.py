"""古琴音乐 API。"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user_optional, get_current_user
from app.models.music import Music
from app.models.user import User
from app.schemas.music import MusicOut, ListenCompleteIn
from app.services.energy_service import grant_energy


router = APIRouter(prefix="/api/music", tags=["music"])


@router.get("", response_model=List[MusicOut])
def list_music(
    yin_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """列出所有曲目（或按 yin_type 过滤）。"""
    q = db.query(Music)
    if yin_type:
        q = q.filter(Music.yin_type == yin_type)
    rows = q.order_by(Music.id.asc()).all()
    return [
        MusicOut(
            id=m.id,
            title=m.title,
            audio_url=m.audio_url,
            cover_image=m.cover_image,
            yin_type=m.yin_type,
            duration=m.duration,
            tags=m.tag_list(),
        )
        for m in rows
    ]


@router.get("/{music_id}", response_model=MusicOut)
def get_music(music_id: int, db: Session = Depends(get_db)):
    m = db.get(Music, music_id)
    if m is None:
        raise HTTPException(status_code=404, detail="这首曲子找不到了")
    return MusicOut(
        id=m.id, title=m.title, audio_url=m.audio_url, cover_image=m.cover_image,
        yin_type=m.yin_type, duration=m.duration, tags=m.tag_list(),
    )


@router.post("/listen-complete")
def listen_complete(
    body: ListenCompleteIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """前端在播放进度 ≥ 90% 时调用，发 +1 露水。

    - 单日上限 20
    - 同一首歌 24h 内重复调用不重复发放
    """
    if body.progress < 0.9:
        return {"granted": False, "reason": "进度不足 90%"}

    music = db.get(Music, body.music_id)
    if music is None:
        raise HTTPException(status_code=404, detail="曲子不存在")

    record = grant_energy(
        db, user, amount=1, source="listen_music",
        note=f"听完《{music.title}》"
    )
    if record is None:
        return {"granted": False, "reason": "今日露水已达上限"}
    db.commit()
    return {
        "granted": True,
        "amount": 1,
        "new_total_energy": user.total_energy,
    }
