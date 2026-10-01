import common.pi_common as utils
from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition

_SCROLL_STATE = {}  # node_name -> {"signature": ..., "scrolls": ...}

@AgentServer.custom_recognition("scroll_more")
class ScrollMore(CustomRecognition):
    """通用滚动操作及识别，通过操作前后roi画面是否变化判断是否滚动到底

    参数：
        roi         要观察的区域，必填。
        max_scroll  最多连滑几次，必填。
    """

    def analyze(self, context, argv):
        try:
            return self._analyze(argv)
        except Exception as error:
            utils.log("scroll_more", f"识别异常，按未命中处理：{error!r}")
            return CustomRecognition.AnalyzeResult(box=None, detail={"异常": repr(error)})

    def _analyze(self, argv):
        params = utils.load_param(argv.custom_recognition_param)
        roi = params.get("roi")
        if not roi:
            utils.log("scroll_more", "roi未配置，不允许使用")
            return CustomRecognition.AnalyzeResult(box=None, detail={"原因": "roi未配置，不允许使用"})

        limit = params.get("max_scroll")
        if limit is None:
            utils.log("scroll_more", "max_scroll未配置，不允许使用")
            return CustomRecognition.AnalyzeResult(box=None, detail={"原因": "max_scroll未配置，不允许使用"})

        state = _SCROLL_STATE.setdefault(argv.node_name, {"signature": None, "scrolls": 0})
        if state["scrolls"] >= limit:
            utils.log("scroll_more", f"已连滑 {state['scrolls']} 次，预算用尽")
            return CustomRecognition.AnalyzeResult(box=None, detail={"原因": "预算用尽"})

        current = self._region_signature(argv.image, roi)
        if self._same_scene(state["signature"], current):
            utils.log("scroll_more", "roi画面内容未变化，停止滑动")
            return CustomRecognition.AnalyzeResult(box=None, detail={"原因": "roi画面内容未变化，停止滑动"})

        state["signature"] = current
        state["scrolls"] += 1
        utils.log("scroll_more", f"第 {state['scrolls']} 次下滑")
        return CustomRecognition.AnalyzeResult(box=(0, 0, 1, 1), detail={"下滑": f"第 {state['scrolls']} 次下滑"})


    def _region_signature(self, image, roi, cols=64, rows=36, levels=8):
        """把 `roi` 区域压成一个粗指纹，用来判断"屏幕有没有变"。

        做法是按步长抽样成至多 cols x rows 的灰度小块、再量化到 `levels` 级。
        不做插值、不做精确比对——只回答"变了没有"，所以抗噪比精度重要。
        """
        x, y, w, h = (int(v) for v in roi)
        height, width = image.shape[0], image.shape[1]
        patch = image[max(0, y):min(height, y + h), max(0, x):min(width, x + w)]
        if patch.size == 0:
            return ()

        step_y = max(1, patch.shape[0] // rows)
        step_x = max(1, patch.shape[1] // cols)
        coarse = patch[::step_y, ::step_x]
        if coarse.ndim == 3:
            coarse = coarse.mean(axis=2)
        return tuple((coarse // max(1, 256 // levels)).astype(int).ravel().tolist())
    
    def _same_scene(self, before, after):
        """两个区域指纹是否表示同一屏。

        量化本身就是容差——`levels=8` 意味着每级 32 个灰阶，这个幅度内的抖动不会改变指纹。
        所以抗噪不需要额外阈值；真要更钝就调 `region_signature` 的 `levels`。
        """
        return bool(before) and before == after