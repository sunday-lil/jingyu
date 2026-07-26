"""树洞对话历史 — 文件存储服务。

v2.3 新增。

设计：
- 每个用户每次开启一段对话，分配一个 conversation_id（uuid）。
- 历史以 JSON 文件存于 data/chat_history/<user_id>/<conversation_id>.json。
- 每条消息：{ role, content, ts }。
- 每次对话给模型加载历史再对话。
- 用户可选择"保留"/"不保留"历史；不保留则在结束时删除文件。
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from app.config import settings


logger = logging.getLogger("qi.chat_history")

# 历史存储根目录
CHAT_HISTORY_DIR = settings.data_dir / "chat_history"

# 单个对话最大保留消息数（防止文件无限膨胀）
MAX_MESSAGES_PER_CONVERSATION = 100


def _user_dir(user_id: int) -> Path:
    """用户的对话历史目录。"""
    d = CHAT_HISTORY_DIR / str(user_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _conv_path(user_id: int, conversation_id: str) -> Path:
    """单个对话文件路径。"""
    # 防御性：conversation_id 只允许 uuid 字符
    safe = "".join(c for c in conversation_id if c.isalnum() or c == "-")
    if not safe or len(safe) > 64:
        raise ValueError("invalid conversation_id")
    return _user_dir(user_id) / f"{safe}.json"


def create_conversation(user_id: int) -> str:
    """新建一段对话，返回 conversation_id。"""
    conversation_id = uuid.uuid4().hex
    # 写一个空文件占位
    path = _conv_path(user_id, conversation_id)
    data = {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "created_at": datetime.now().isoformat(),
        "messages": [],
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return conversation_id


def load_messages(user_id: int, conversation_id: str) -> List[dict]:
    """加载某段对话的所有消息（OpenAI messages 格式 [{role, content}, ...]）。"""
    try:
        path = _conv_path(user_id, conversation_id)
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        msgs = data.get("messages", [])
        # 仅返回 role/content，去掉 ts
        return [{"role": m["role"], "content": m["content"]} for m in msgs]
    except Exception as e:
        logger.warning("加载对话历史失败 user=%s conv=%s: %s", user_id, conversation_id, e)
        return []


def append_message(
    user_id: int,
    conversation_id: str,
    role: str,
    content: str,
) -> None:
    """向某段对话追加一条消息。"""
    try:
        path = _conv_path(user_id, conversation_id)
        if not path.exists():
            # 文件不在了，重建一个
            create_conversation(user_id)
            # 重新路径
            path = _conv_path(user_id, conversation_id)

        data = json.loads(path.read_text(encoding="utf-8"))
        msgs = data.get("messages", [])
        msgs.append({
            "role": role,
            "content": content,
            "ts": datetime.now().isoformat(),
        })
        # 截断：只保留最近 N 条
        if len(msgs) > MAX_MESSAGES_PER_CONVERSATION:
            msgs = msgs[-MAX_MESSAGES_PER_CONVERSATION:]
        data["messages"] = msgs
        data["updated_at"] = datetime.now().isoformat()
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning("写入对话历史失败 user=%s conv=%s: %s", user_id, conversation_id, e)


def list_conversations(user_id: int) -> List[dict]:
    """列出用户的所有对话（按更新时间倒序）。"""
    udir = _user_dir(user_id)
    result = []
    for f in udir.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            result.append({
                "conversation_id": data.get("conversation_id", f.stem),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at") or data.get("created_at"),
                "message_count": len(data.get("messages", [])),
                "preview": (data.get("messages", [{}])[0].get("content", "")[:30]) if data.get("messages") else "",
            })
        except Exception:
            continue
    # 按 updated_at 倒序
    result.sort(key=lambda x: x.get("updated_at") or "", reverse=True)
    return result


def delete_conversation(user_id: int, conversation_id: str) -> bool:
    """删除一段对话（用户选择"不保留"时调用）。"""
    try:
        path = _conv_path(user_id, conversation_id)
        if path.exists():
            path.unlink()
            return True
        return False
    except Exception as e:
        logger.warning("删除对话历史失败 user=%s conv=%s: %s", user_id, conversation_id, e)
        return False


def get_or_create_conversation(user_id: int, conversation_id: Optional[str] = None) -> str:
    """获取或创建一段对话。"""
    if conversation_id:
        try:
            path = _conv_path(user_id, conversation_id)
            if path.exists():
                return conversation_id
        except Exception:
            pass
    return create_conversation(user_id)
