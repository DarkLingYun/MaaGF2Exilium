import common.pi_common as utils
from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition

# node_name -> {"signature": ..., "scrolls": ...}
# 按节点名存在 agent 进程里，跨任务保留。指纹带脏没关系（它只在这个节点前后两次调用之间比对，
# 最坏是下一次"第一次滑"多滑一次）；计数器则在一段连滑结束时归零，见 _analyze。
_SCROLL_STATE = {}

@AgentServer.custom_recognition("scroll_end")
class ScrollEnd(CustomRecognition):
    """通用滚动操作及识别，通过操作前后roi画面是否变化判断是否滚动到底

    参数：
        roi             要观察的区域，必填。要包含随滚动一起位移的内容。
        max_scroll      一段最多连滑几次，必填。
                        "一段" = 一次进入本节点后的连续滑动，止于"画面不再变化"或"用满 max_scroll"。
                        两种收尾都归零，所以它是"每段重新计数"，**不是**"本进程总共只准滑几次"。
        probe_on_same   可选，默认 false。画面与上次相同时先补滑一次再确认，用于同一节点
                        被多个调用方复用、且每段开始时可能回到同一位置的场景。
        same_tolerance  可选，默认 0.01。差异采样点占比不超过该值即视为同一屏（吸收孤立跳变）。
    """

    def analyze(self, context, argv):
        try:
            return self._analyze(argv)
        except Exception as error:
            utils.log("scroll_end", f"识别异常，按未命中处理：{error!r}")
            return CustomRecognition.AnalyzeResult(box=None, detail={"异常": repr(error)})

    def _analyze(self, argv):
        params = utils.load_param(argv.custom_recognition_param)
        roi = params.get("roi")
        if not roi:
            utils.log("scroll_end", "roi未配置，不允许使用")
            return CustomRecognition.AnalyzeResult(box=None, detail={"原因": "roi未配置，不允许使用"})

        limit = params.get("max_scroll")
        if limit is None:
            utils.log("scroll_end", "max_scroll未配置，不允许使用")
            return CustomRecognition.AnalyzeResult(box=None, detail={"原因": "max_scroll未配置，不允许使用"})

        # 状态按节点名跨任务保留，而指纹记的是"滑动前"的画面：某次滑动后直接找到了目标，
        # 指纹就会停在起始位置。同一节点被多个调用方复用时（如活动列表的各个子任务），
        # 下一次搜索重新打开页面又回到同一位置，会被误判成"没变化=已到底"。
        # probe_on_same 让首次相同先补滑一次，下一帧仍相同才收手。
        probe_on_same = bool(params.get("probe_on_same", False))
        try:
            tolerance = float(params.get("same_tolerance", 0.01))
        except (TypeError, ValueError):
            tolerance = 0.01
        state = _SCROLL_STATE.setdefault(
            argv.node_name, {"signature": None, "scrolls": 0, "same_streak": 0}
        )
        if state["scrolls"] >= limit:
            # 用满预算也要归零——原因和上面那条一样：本段到此为止，下次再进这个节点
            # 该重新给满预算。不归零的话，只要有一次赶上"roi 里有动画"或"列表比预算深"，
            # 计数器就永久卡在上限，之后每次调用都在这里早退，节点在该进程里静默失效。
            # 真正防无限滑的是引擎侧按 task 重置的 max_hit，不是这个计数器。
            state["scrolls"] = 0
            state["same_streak"] = 0
            utils.log("scroll_end", f"已连滑 {limit} 次，本段到此为止")
            return CustomRecognition.AnalyzeResult(box=None, detail={"原因": "预算用尽"})

        current = self._region_signature(argv.image, roi)
        if self._same_scene(state["signature"], current, tolerance):
            if probe_on_same and state.get("same_streak", 0) == 0:
                # 可能是上一段留下的旧指纹（页面已重新打开）。补滑一次：真到底则下一帧仍相同，
                # 若是旧指纹，这一滑会带来变化，搜索继续。
                state["same_streak"] = 1
                utils.log("scroll_end", "画面与上次相同，先补滑一次确认")
            else:
                # 这一段连滑结束了（到顶/到底/滑不动）：计数归零，让下一段从满预算开始。
                # 不归零的话 max_scroll 会变成"本进程一辈子只准滑几次"，第二次跑任务就静默不动了。
                state["scrolls"] = 0
                state["same_streak"] = 0
                utils.log("scroll_end", "roi画面内容未变化，停止滑动")
                return CustomRecognition.AnalyzeResult(box=None, detail={"原因": "roi画面内容未变化，停止滑动"})
        else:
            state["same_streak"] = 0

        state["signature"] = current
        state["scrolls"] += 1
        utils.log("scroll_end", f"第 {state['scrolls']} 次下滑")
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
    
    def _same_scene(self, before, after, tolerance=0.01):
        """两个区域指纹是否表示同一屏。

        量化（`levels=8`，每级 32 个灰阶）只吸收幅度抖动，吸收不了"个别采样点跨过量化
        边界"造成的孤立差异：列表到底后实测每帧仍有 1~3/2808 个点跳动，严格相等会
        让节点一直滑到 max_scroll。所以按差异点占比判定：默认 1% 以内算同一屏。
        真实滚动一屏的差异约 28%，离阈值很远。
        """
        if not before or not after or len(before) != len(after):
            return False
        if before == after:
            return True
        allowed = max(1, int(len(before) * tolerance))
        diff = sum(1 for a, b in zip(before, after) if a != b)
        return diff <= allowed