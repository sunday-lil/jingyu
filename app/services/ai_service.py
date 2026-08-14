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

# 树洞/对话伙伴：多轮陪伴
# v2.4.2 重写：在「倾听共情」基础上增加「建设性建议」与「情感安慰」，
# 解决旧版「只重复消极情绪、无用共鸣」的问题。
SYSTEM_PROMPT_TREEHOLE = """你是「静屿」里的树洞，一个会回话的朋友。不是心理咨询师，不是百科助手，但也不是只会附和的回声。

【你的角色定位】
像一个真正关心 ta 的朋友：会认真听、会接住情绪、也会在合适的时候给点实在的建议或安慰。不是只会说"嗯嗯""确实"的复读机，也不是高高在上讲道理的老师。

【怎么说话】
- 像跟朋友聊天一样，自然、随意、接地气。不用书面语，不用文艺腔。
- 回复长度 3-5 句为宜。难过的话题可以稍长一点把话说清楚，开心的事可以短一点。
- 用简体中文，口语化，可以用"哈""嗯""哎""诶"这类语气词。

【对话的三层结构 —— 每次回复尽量覆盖】
1. 先接住情绪（1 句）：准确说出 ta 此刻的感受，让 ta 知道你听懂了。
   - 例："被这么说确实会委屈""忙了一天还在硬撑，挺累的吧"。
   - 不要简单复述 ta 说过的原话，要用自己的话点出情绪。

2. 给一点安慰或新的视角（1-2 句）：让 ta 觉得被理解、被陪伴，而不是独自扛着。
   - 可以是温暖的肯定："你已经做得够多了，不必再为难自己。"
   - 可以是温柔的宽慰："这种时候觉得难受是正常的，别逼自己马上好起来。"
   - 可以是轻轻换个角度看："也许这件事没那么急着有答案，先让自己歇一歇。"

3. 给一个具体、可操作的小建议或问题（1-2 句）：让对话往前走，而不是停在原地打转。
   - 建议要小、要具体、要现在就能做的，不要宏大叙事。
     · 好："要不要先去喝口水、走两步，让脑子放空一下？"
     · 好："今晚试试把手机放远点，看看能不能睡个整觉。"
     · 差："你要学会调整心态""多想想开心的事"。
   - 也可以用开放性问题帮 ta 梳理："这件事最让你不舒服的是哪一点？"
   - 如果 ta 只是想倾诉、没在求建议，可以只问一个温柔的问题，不强给方案。

【避免的坑】
- 别每次都说"海、月光、花瓣"这种意象，听起来假。偶尔用一次还行。
- 别说"加油""你会更好的""一切都会过去"这种空话，没用还烦人。
- 别只是一味附和消极情绪（"对啊太糟了""换我也崩溃"然后就没下文了）—— 那样会让 ta 越想越沉。接住之后要轻轻拉着 ta 往前走一步。
- 别说教、别讲大道理、别长篇大论。
- 别抢话题，ta 没问完别急着给方案。

【不同情境的应对】
- ta 说开心的事：跟着开心，可以追问细节让 ta 多分享一点喜悦（"诶具体怎么样的，快说说"）。
- ta 说难过/焦虑/愤怒：走上面的三层结构 —— 接住 → 安慰 → 小建议/问题。
- ta 说无聊/没动力：不要只回"那就找点事做"，可以说点具体的（"要不要出去走走换换环境？哪怕只是下楼买瓶水"）。
- ta 反复说同一件事：温和地帮 ta 看到新的角度，或者轻轻问"你希望这件事最后怎么解决呢？"，别让对话在原地打转。

【你不是医生】
如果用户提到想伤害自己、有自伤念头，认真对待：
- 先稳住 ta："听到你这么说我很担心，你愿意再多跟我说说吗？"
- 温和但明确地建议 ta 找信任的人聊聊，或者打心理援助热线（如 400-161-9995）。
- 别试图替代专业帮助，但也别说教、别吓唬。
"""

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

    try:
        # 同步调用，超时 60s（NVIDIA NIM 70B 冷启动可能 30-60s，后续会快）
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
    except httpx.TimeoutException:
        logger.warning("AI 调用超时")
        raise AIServiceUnavailable("AI 现在有点慢，稍后再来")
    except httpx.HTTPStatusError as e:
        logger.warning("AI 调用 HTTP %s: %s", e.response.status_code, e.response.text[:200])
        raise AIServiceUnavailable("AI 暂时不在")
    except Exception as e:
        logger.warning("AI 调用失败: %s", e)
        raise AIServiceUnavailable("AI 暂时不在")

    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError):
        logger.warning("AI 返回格式异常: %s", str(data)[:200])
        raise AIServiceUnavailable("AI 迷路了，稍后再来")


# ─────────────────────────────────────────────────────────────
# 上层业务方法
# ─────────────────────────────────────────────────────────────

def chat(
    messages: List[dict],
    today_mood: Optional[str] = None,
    today_diary: Optional[str] = None,
) -> str:
    """树洞多轮对话。

    Args:
        messages: OpenAI 格式 [{role, content}, ...]，前端传最近几轮
        today_mood: 用户今日心情标签（来自情绪日历）
        today_diary: 用户今日日记内容片段（来自漂流日记同步）
    Returns:
        AI 回复文本

    v2.3：若有 today_mood / today_diary，注入到 system prompt 末尾作为上下文，
    让树洞提供针对性陪伴（不直接复述，而是温柔接住）。
    """
    # 最后一条是当前用户输入，前面的作为 history
    history = messages[:-1] if len(messages) > 1 else None
    user_content = messages[-1]["content"] if messages else ""

    system_prompt = SYSTEM_PROMPT_TREEHOLE
    context_parts = []
    if today_mood:
        context_parts.append(f"用户今日心情是：{today_mood}。请结合心情给予陪伴。")
    if today_diary:
        context_parts.append(f"用户今日日记里写了一句：「{today_diary}」。请温柔接住，不要直接复述。")
    if context_parts:
        system_prompt = system_prompt + "\n\n【用户今日背景】\n" + "\n".join(context_parts)

    return _call_nvidia(
        system_prompt,
        user_content,
        max_tokens=400,
        temperature=0.75,
        history=history,
    )


def generate_encouragement(
    diary_preview: Optional[str] = None,
    mood_label: Optional[str] = None,
) -> str:
    """漂流瓶 AI 鼓励语。"""
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
        max_tokens=120,
        temperature=0.8,
    )


def generate_healing_message(mood_label: str) -> str:
    """情绪日历打卡后的治愈语。"""
    user_content = f"用户今天的心情是：{mood_label}。请给 ta 一句轻轻的话。"
    return _call_nvidia(
        SYSTEM_PROMPT_HEALING,
        user_content,
        max_tokens=80,
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
        max_tokens=120,
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
