"""MaaFramework 自定义节点的公共工具。
"""

import json
import re

from maa.pipeline import JOCR


def log(prefix, message):
    """agent 的 stdout 会被 GUI 捕获显示，所以直接 print 并立刻 flush。"""
    print(f"[{prefix}] {message}", flush=True)


def load_param(raw):
    """`custom_recognition_param` / `custom_action_param` -> dict。

    到 agent 这边它是 JSON 字符串，但也兼容调用方直接给 dict 的情况。
    """
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def alias_patterns(aliases):
    """别名列表 -> 带 ASCII 边界守卫的正则列表。空别名会被丢掉。"""
    patterns = []
    for alias in aliases or []:
        text = (alias or "").strip()
        if not text:
            continue
        body = re.escape(text)
        if text[0].isascii() and text[0].isalnum():
            body = r"(?<![A-Za-z0-9])" + body
        if text[-1].isascii() and text[-1].isalnum():
            body = body + r"(?![A-Za-z0-9])"
        patterns.append(body)
    return patterns


def box_tuple(box):
    """识别结果的 box -> (x, y, w, h)。

    同一个 box 在不同接口上分别以对象（`.x/.y/.w/.h`）或四元组出现，两种都要吃。
    """
    if box is None:
        return None
    if isinstance(box, (list, tuple)):
        return tuple(int(v) for v in box)
    return (int(box.x), int(box.y), int(box.w), int(box.h))


def ocr_words(context, image, roi, expected=None):
    """跑一次 OCR，返回区域内所有文字 `[(text, box), ...]`。

    传 `expected` 时引擎会顺带过滤并应用 `replace` 之类的全局修正；
    返回的不保证只有命中的那些，调用方仍按需自己筛（`match_alias`）。

    **一次调用拿全区域**是关键：逐个别名各跑一次 OCR 会让每个商品都多付一次
    全屏识别的开销。
    """
    params = JOCR(roi=tuple(roi), expected=list(expected or []))
    reco = context.run_recognition_direct("OCR", params, image)
    if not reco:
        return []
    results = (getattr(reco, "all_results", None)
               or getattr(reco, "filtered_results", None)
               or [])
    return [((getattr(r, "text", "") or ""), box_tuple(getattr(r, "box", None)))
            for r in results]


def match_alias(text, patterns):
    """这段文字是否命中任一别名正则。`patterns` 由 `alias_patterns()` 生成。"""
    return any(re.search(pattern, text or "") for pattern in patterns)


# 再导出：`shop_exchange` 之类的模块是按 `utils.State` / `utils.reset_action` 用的。
# 只能放在文件末尾，而且 state 那边对 pi_common 的引用必须是惰性的——否则
# 先 import 哪个模块就会撞上"部分初始化的模块"，整个 agent 起不来。
from .state import State, reset_action  # noqa: E402
