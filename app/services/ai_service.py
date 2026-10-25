"""AI 服务层 — 封装 NVIDIA NIM API（OpenAI 兼容）。

NVIDIA NIM 免费层：
- Base URL: https://integrate.api.nvidia.com/v1
- 端点: /chat/completions
- Header: Authorization: Bearer nvapi-...
- 限速: 约 40 RPM（按账户）

本模块所有方法在 ``settings.nvidia_api_key`` 为空时抛 ``AIServiceUnavailable``，
路由层捕获后返回「AI 暂时不在」友好提示，不影响其他功能。

设计原则（与静屿治愈系调性一致）：
- 温柔、倾听、不评判，像一个安静的陪伴者
- 回答简短（一般 2-4 句），不说教、不灌输正能量套路
- 借用自然意象（海、月光、花瓣、古琴、五音）表达
- 不是医生，不诊断不开药；危机倾向温柔引导寻求专业帮助
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional

import httpx

from app.config import settings


logger = logging.getLogger("qi.ai")


# ─────────────────────────────────────────────────────────────
# 异常
# ─────────────────────────────────────────────────────────────

class AIServiceUnavailable(Exception):
    """AI 功能未启用（无 API key）或调用失败。"""


# ─────────────────────────────────────────────────────────────
# 系统提示词
# ─────────────────────────────────────────────────────────────

# 漂流瓶鼓励语：单向、温暖、匿名
SYSTEM_PROMPT_ENCOURAGEMENT = """你正在给一个陌生人写一句匿名的漂流瓶鼓励语。
要求：
- 1-2 句话，简短温柔，不说教。
- 可以借用海、月光、花瓣、古琴等意象。
- 不评判对方的处境，只让 ta 知道有人路过、有人听见。
- 用简体中文，语气像轻轻放在 ta 手心的一颗小石头。
- 不要出现"你应该""加油""努力"这类话。
"""

# 情绪日历治愈语：根据当日心情生成一句
SYSTEM_PROMPT_HEALING = """用户刚刚在情绪日历里记下了今日心情。请根据 ta 的心情，给一句轻轻的治愈话语。
要求：
- 1 句话，不超过 30 字。
- 不评判心情好坏，只是陪伴。
- 可以借用自然意象（海、月光、花瓣、古琴、五音）。
- 用简体中文，语气温柔。
- 不要出现"加油""努力""你应该"。
"""

# 音乐推荐：根据状态推荐五音之一
SYSTEM_PROMPT_MUSIC = """你是静屿的古琴向导。用户会用一句话描述自己当下的状态，你需要从「宫商角徵羽」五音里推荐一个最合适的音给 ta 听。

五音对应：
- 宫（土/脾胃）：温厚、安定，适合需要被托住、想吃顿热饭的感觉
- 商（金/肺大肠）：清肃、收敛，适合心里堵、想叹气的感觉
- 角（木/肝胆）：舒展、生发，适合憋闷、想出去走走的感觉
- 徵（火/心小肠）：温暖、明亮，适合低落、想被照一下的感觉
- 羽（水/肾膀胱）：沉静、下行，适合浮躁、想安静下来的感觉

只回复一个 JSON 对象，格式严格如下，不要任何多余文字：
{"yin": "gong|shang|jue|zhi|yu", "reason": "一句简短的治愈系推荐理由，不超过 30 字"}
"""


# ─────────────────────────────────────────────────────────────
# 底层调用
# ─────────────────────────────────────────────────────────────

def _check_available() -> None:
    """无 key 直接抛异常，路由层捕获。"""
    if not settings.nvidia_api_key:
        raise AIServiceUnavailable("AI 暂时不在（未配置 NVIDIA_API_KEY）")


def _call_nvidia(
    system_prompt: str,
    user_content: str,
    *,
    max_tokens: int = 300,
    temperature: float = 0.7,
    history: Optional[List[dict]] = None,
) -> str:
    """同步调用 NVIDIA NIM chat/completions，返回 assistant 文本。

    Args:
        system_prompt: 系统提示词
        user_content: 本轮用户输入
        history: 之前的对话历史（OpenAI messages 格式，不含 system）
    """
    _check_available()

    messages: List[dict] = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_content})

    url = f"{settings.ai_base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.nvidia_api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "model": settings.ai_model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.9,
        "stream": False,
    }

    # v2.5.3：免费层偶发 RemoteDisconnected / 超时 / 5xx / 429，
    # 自动重试最多 2 次（间隔 1s → 2s），全部失败才抛"AI 暂时不在"。
    max_attempts = 3
    data = None
    for attempt in range(1, max_attempts + 1):
        try:
            # 同步调用，超时 60s（冷启动可能 30-60s，后续会快）
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            break
        except httpx.TimeoutException:
            logger.warning("AI 调用超时（第 %s 次）", attempt)
            last_err = "AI 现在有点慢，稍后再来"
        except httpx.HTTPStatusError as e:
            code = e.response.status_code
            logger.warning("AI 调用 HTTP %s（第 %s 次）: %s", code, attempt, e.response.text[:200])
            # 429/5xx 属瞬时错误可重试；4xx（如 401/404）重试无意义
            last_err = "AI 暂时不在"
            if code not in (429, 500, 502, 503, 504):
                raise AIServiceUnavailable(last_err)
        except Exception as e:
            logger.warning("AI 调用失败（第 %s 次）: %s", attempt, e)
            last_err = "AI 暂时不在"
        if attempt < max_attempts:
            time.sleep(1.0 * attempt)  # 1s → 2s 线性退避

    if data is None:
        raise AIServiceUnavailable(last_err)

    try:
        # v2.5.3：glm 系 reasoning 模型偶发 content=None（思考内容挤占 token 配额），
        # 容错成空串统一走"迷路"提示
        content = (data["choices"][0]["message"].get("content") or "").strip()
        if not content:
            logger.warning("AI 返回空 content: %s", str(data)[:200])
            raise AIServiceUnavailable("AI 迷路了，稍后再来")
        return content
    except (KeyError, IndexError):
        logger.warning("AI 返回格式异常: %s", str(data)[:200])
        raise AIServiceUnavailable("AI 迷路了，稍后再来")


# ─────────────────────────────────────────────────────────────
# 上层业务方法
# ─────────────────────────────────────────────────────────────

def generate_encouragement(
    diary_preview: Optional[str] = None,
    mood_label: Optional[str] = None,
) -> str:
    """漂流瓶 AI 鼓励语。"""
    # 只发送前 120 字，减少 token 与隐私暴露面（与文档一致）
    diary_preview = (diary_preview or "")[:120]
    parts = []
    if mood_label:
        parts.append(f"作者此刻的心情大概是：{mood_label}。")
    if diary_preview:
        parts.append(f"ta 在日记里写了一句：「{diary_preview}」")
    if not parts:
        parts.append("ta 没有留下文字，只是把一个瓶子放进海里。")
    user_content = " ".join(parts) + "\n请给 ta 写一句匿名的鼓励语。"
    return _call_nvidia(
        SYSTEM_PROMPT_ENCOURAGEMENT,
        user_content,
        max_tokens=900,  # v2.5.3：预留 reasoning token 空间
        temperature=0.8,
    )


def generate_healing_message(mood_label: str) -> str:
    """情绪日历打卡后的治愈语。"""
    user_content = f"用户今天的心情是：{mood_label}。请给 ta 一句轻轻的话。"
    return _call_nvidia(
        SYSTEM_PROMPT_HEALING,
        user_content,
        max_tokens=900,  # v2.5.3：预留 reasoning token 空间
        temperature=0.85,
    )


def recommend_music(user_state: Optional[str] = None) -> dict:
    """音乐 AI 心情推荐。

    Returns:
        {"yin": "gong|shang|jue|zhi|yu", "reason": "..."}
    """
    import json as _json

    state = user_state.strip() if user_state and user_state.strip() else "我心里有点乱，说不上来"
    user_content = f"用户描述自己当下的状态：{state}\n请推荐一个音给 ta。"
    raw = _call_nvidia(
        SYSTEM_PROMPT_MUSIC,
        user_content,
        max_tokens=900,  # v2.5.3：预留 reasoning token 空间
        temperature=0.5,
    )
    # 容错解析：模型偶尔会包 ```json 或多说话
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()
    # 找第一个 { 到最后一个 }
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1:
        raise AIServiceUnavailable("AI 迷路了，稍后再来")
    try:
        obj = _json.loads(raw[start:end + 1])
    except _json.JSONDecodeError:
        raise AIServiceUnavailable("AI 迷路了，稍后再来")
    yin = obj.get("yin", "").strip().lower()
    if yin not in ("gong", "shang", "jue", "zhi", "yu"):
        raise AIServiceUnavailable("AI 迷路了，稍后再来")
    return {"yin": yin, "reason": str(obj.get("reason", "去听一听，让心慢下来。"))[:60]}
