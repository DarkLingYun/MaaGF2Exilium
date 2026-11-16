"""Validate PC screenshots before game tasks, using MaaFramework's 720p space.

Like MaaEnd's aspect-ratio check, validate a fresh capture rather than the last
cached frame. A synchronous action gates the game steps across Agent RPC.
Do not resize the game window or change its settings.
"""

import os
import time
from dataclasses import dataclass
from html import escape

from maa.custom_action import CustomAction

TARGET = (1280, 720)


@dataclass(frozen=True)
class ResolutionResult:
    raw: tuple[int, int] = (0, 0)
    scaled: tuple[int, int] = (0, 0)
    error: str = ""


def validate_resolution(raw, scaled):
    """The actual recognition image must have the resource's coordinate space.

    Never stretch an unsupported ratio into 1280x720. Check both raw dimensions
    and scaled dimensions so a tiny window, raw-size mode or wrong scaling
    cannot silently pass. Using the real scaled size also avoids rounding
    differences between Python and the framework.
    """
    width, height = raw
    if width <= 0 or height <= 0 or min(scaled) <= 0:
        return ResolutionResult(raw, scaled, "capture")
    if width < TARGET[0] or height < TARGET[1]:
        return ResolutionResult(raw, scaled, "minimum")
    # Integer equivalent of rounding the long edge after short-edge scaling.
    normalized_width = (width * TARGET[1] * 2 + height) // (height * 2)
    if normalized_width != TARGET[0] or width <= height:
        return ResolutionResult(raw, scaled, "ratio")
    if tuple(scaled) != TARGET:
        return ResolutionResult(raw, scaled, "scaling")
    return ResolutionResult(tuple(raw), tuple(scaled))


def check_controller(controller):
    """Retry transient capture failures, but reject a known wrong size at once."""
    for attempt in range(3):
        try:
            if controller.post_screencap().wait().succeeded:
                raw = tuple(controller.resolution)
                image = controller.cached_image
                if image is not None and image.size and min(raw) > 0:
                    return validate_resolution(raw, (image.shape[1], image.shape[0]))
        except Exception:
            # A failed capture must not reuse a previous valid size or escape a
            # ctypes callback (whose exception would otherwise be swallowed).
            pass
        if attempt < 2:
            time.sleep(0.2)
    return ResolutionResult(error="capture")


def format_result(result, english=False):
    raw = f"{result.raw[0]}×{result.raw[1]}"
    scaled = f"{result.scaled[0]}×{result.scaled[1]}"
    if english:
        title = (
            "PC resolution check failed — tasks stopped"
            if result.error
            else "PC resolution check passed"
        )
        reasons = {
            "capture": "Could not capture the game or read its resolution. Restore the game window, check the capture method and permissions, then retry. Update the complete package if the framework is too old.",
            "minimum": "The game must be in landscape orientation and at least 1280×720.",
            "ratio": "The game must use a 16:9 resolution that scales to 1280×720. 16:10, ultrawide and 1360/1366×768 are not supported.",
            "scaling": "The captured image is not 1280×720. Use the PC controller and PC resource with screenshot short side set to 720; disable raw-size/custom scaling.",
        }
        size_line = f"Game capture: {raw}; recognition image: {scaled}."
        advice = "Use 1280×720, 1600×900, 1920×1080, 2560×1440 or 3840×2160, then retry. Check the game client area, not the monitor resolution."
    else:
        title = "PC 分辨率校验失败，任务已停止" if result.error else "PC 分辨率校验通过"
        reasons = {
            "capture": "无法截图或读取实际分辨率。请恢复游戏窗口、检查截图方式和权限后重试；框架版本过旧时请更新完整安装包。",
            "minimum": "游戏需为横屏，实际分辨率至少为 1280×720。",
            "ratio": "游戏需使用缩放后为 1280×720 的 16:9 分辨率，不支持 16:10、超宽屏及 1360/1366×768。",
            "scaling": "识别截图不是 1280×720。请使用 PC 控制器与 PC 资源，将截图短边设为 720，关闭原始尺寸或自定义缩放。",
        }
        size_line = f"游戏截图：{raw}；识别截图：{scaled}。"
        advice = "请在游戏中选择 1280×720、1600×900、1920×1080、2560×1440 或 3840×2160，然后重新运行。检查的是游戏客户区，不是显示器分辨率。"
    lines = [title, size_line]
    if result.error:
        lines.extend([reasons[result.error], advice])
    # MXU renders Agent stdout as rich text. Keep the entire diagnostic on one
    # line so it remains a single visible log entry, as in MaaEnd's warning.
    color = "#c0392b" if result.error else "#238636"
    return (
        f'<div style="color:{color}"><b>{escape(lines[0])}</b><br>'
        + "<br>".join(escape(line) for line in lines[1:])
        + "</div>"
    )


class PCResolutionCheck(CustomAction):
    """A synchronous gate: only PC resources enable this action on task entries.

    Agent event notifications do not block the host task. A custom action does,
    so even a zero-delay first game node cannot race ahead of validation.
    """

    def run(self, context, argv):
        tasker = context.tasker
        try:
            result = check_controller(tasker.controller)
        except Exception:
            result = ResolutionResult(error="capture")

        english = os.environ.get("PI_CLIENT_LANGUAGE", "").lower().startswith("en")
        try:
            print(format_result(result, english), flush=True)
        finally:
            if result.error:
                # Never wait inside an action callback: the running task cannot
                # finish until we return. Also return False to block its next
                # node independently of queue cancellation over Agent RPC.
                tasker.post_stop()
        return not result.error
