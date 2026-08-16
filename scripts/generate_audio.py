# -*- coding: utf-8 -*-
"""古琴五音音频生成器（v2.4.6）

用纯 Python（无第三方依赖）合成 5 段古琴风格的拨弦音频，
替换 static/audio/ 下的静音占位文件。

原理：
- Karplus-Strong 拨弦物理建模：用噪声激励 + 延迟线反馈滤波，
  听感即真实的琴弦拨弦（该算法本就是为模拟弦振动设计的）。
- 五音各用对应的中国五声调式（宫商角徵羽 = do re mi sol la 起），
  低音区 + 慢速 + 稀疏音符 + 长延音，贴近古琴「散音泛音按音」气质。
- 输出 22.05kHz / 16bit / mono WAV（古琴以中低频为主，音质足够，
  单文件约 3-4MB）。

运行：python scripts/generate_audio.py
幂等：直接覆盖 static/audio/{yin}.wav
"""
from __future__ import annotations

import random
import struct
import sys
import wave
from pathlib import Path

SR = 22050          # 采样率
DUR = 78.0          # 每段时长（秒）
MASTER = Path(__file__).resolve().parent.parent / "static" / "audio"

# ── 五音调式定义 ──────────────────────────────────────────────
# 音名: (基准频率 C3=130.81 起, 调式音阶级, 节拍秒/音, 性格说明)
# 中国五声：宫=do 商=re 角=mi 徵=sol 羽=la（各以其为主音）
YIN_CFG = {
    # 宫调（土）——中正平和，C 宫系统：C D E G A
    "gong":  dict(base=130.81, scale=[0, 2, 4, 7, 9], beat=2.6, seed=11),
    # 商调（金）——清肃飘逸，D 商系统：D E G A C（偏高音区一点）
    "shang": dict(base=146.83, scale=[0, 3, 5, 7, 10], beat=2.2, seed=22),
    # 角调（木）——舒展生发，E 角系统：E G A B D
    "jue":   dict(base=164.81, scale=[0, 3, 5, 7, 10], beat=2.4, seed=33),
    # 徵调（火）——明快温暖，G 徵系统：G A C D E（节奏稍快）
    "zhi":   dict(base=196.00, scale=[0, 2, 5, 7, 9], beat=1.9, seed=44),
    # 羽调（水）——柔润安宁，A 羽系统：A C D E G（小调色彩）
    "yu":    dict(base=220.00, scale=[0, 3, 5, 7, 10], beat=2.9, seed=55),
}


def ks_note(freq: float, dur: float, decay: float = 0.9955) -> list[float]:
    """Karplus-Strong 合成一次拨弦，返回 [-1,1] 样本列表。"""
    n = int(SR / freq)
    buf = [random.uniform(-0.7, 0.7) for _ in range(n)]
    out = []
    total = int(dur * SR)
    idx = 0
    for i in range(total):
        v = buf[idx]
        nxt = buf[(idx + 1) % n]
        buf[idx] = decay * 0.5 * (v + nxt)
        idx = (idx + 1) % n
        out.append(v)
    return out


def midi_hz(semi: float, base: float) -> float:
    return base * (2.0 ** (semi / 12.0))


def synth_track(yin: str) -> list[float]:
    cfg = YIN_CFG[yin]
    random.seed(cfg["seed"])  # 每音固定随机种子 → 可复现
    master = [0.0] * int(DUR * SR)
    scale = cfg["scale"]

    t = 0.6  # 起始留白
    while t < DUR - 8.0:
        # 一句 5-9 个音，级进为主、偶跳进；隔句留气口
        phrase_len = random.choice([5, 6, 7, 8, 9])
        degree = random.randrange(len(scale))
        gap = cfg["beat"]
        for k in range(phrase_len):
            step = random.choice([-1, -1, 0, 1, 1, 1, 2, -2])
            degree = max(0, min(len(scale) + 7, degree + step))
            octave = 0
            if degree >= len(scale):          # 越界升高八度
                octave = 12 * (degree // len(scale))
                semi = scale[degree % len(scale)] + octave
            else:
                semi = scale[degree]
            freq = midi_hz(semi, cfg["base"])
            # 偶尔低八度散音（古琴标志性的低音空弦）
            if random.random() < 0.18:
                freq *= 0.5
            note_dur = random.uniform(3.5, 6.5)
            amp = random.uniform(0.32, 0.5)
            samples = ks_note(freq, note_dur)
            start = int(t * SR)
            for i, s in enumerate(samples):
                j = start + i
                if j >= len(master):
                    break
                master[j] += amp * s
            t += gap * random.uniform(0.85, 1.3)
            if random.random() < 0.12:       # 句中气口
                t += gap * 0.6
        t += gap * random.uniform(1.2, 2.2)   # 句间气口

    # 归一化 + 2.5s 淡入淡出
    peak = max(abs(x) for x in master) or 1.0
    fade = int(2.5 * SR)
    out = []
    n = len(master)
    for i, x in enumerate(master):
        g = x / peak * 0.88
        if i < fade:
            g *= i / fade
        elif i > n - fade:
            g *= (n - i) / fade
        out.append(g)
    return out


def write_wav(path: Path, samples: list[float]) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        frames = bytearray()
        for s in samples:
            v = int(max(-1.0, min(1.0, s)) * 32767)
            frames += struct.pack("<h", v)
        w.writeframes(bytes(frames))


def main() -> None:
    MASTER.mkdir(parents=True, exist_ok=True)
    for yin in YIN_CFG:
        print(f"[synth] {yin} ...", flush=True)
        samples = synth_track(yin)
        path = MASTER / f"{yin}.wav"
        write_wav(path, samples)
        print(f"  -> {path.name}  {path.stat().st_size / 1024 / 1024:.2f} MB  "
              f"{len(samples) / SR:.1f}s", flush=True)
    print("done.")


if __name__ == "__main__":
    sys.exit(main())
