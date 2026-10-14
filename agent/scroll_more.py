import common.pi_common as utils
from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition

# node_name -> {"signature": ..., "scrolls": ...}
# 按节点名存在 agent 进程里，跨任务保留。指纹带脏没关系（它只在这个节点前后两次调用之间比对，
# 最坏是下一次"第一次滑"多滑一次）；计数器则在一段连滑结束时归零，见 _analyze。
_SCROLL_STATE = {}

@AgentServer.custom_recognition("scroll_more")
class ScrollMore(CustomRecognition):
    """通用滚动操作及识别，通过操作前后roi画面是否变化判断是否滚动到底

    参数：
        roi         要观察的区域，必填。要包含随滚动一起位移的内容。
        max_scroll  一段最多连滑几次，必填。
                    "一段" = 一次进入本节点后的连续滑动，止于"画面不再变化"或"用满 max_scroll"。
                    两种收尾都归零，所以它是"每段重新计数"，**不是**"本进程总共只准滑几次"。
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
            # 用满预算也要归零——原因和上面那条一样：本段到此为止，下次再进这个节点
            # 该重新给满预算。不归零的话，只要有一次赶上"roi 里有动画"或"列表比预算深"，
            # 计数器就永久卡在上限，之后每次调用都在这里早退，节点在该进程里静默失效。
            # 真正防无限滑的是引擎侧按 task 重置的 max_hit，不是这个计数器。
            state["scrolls"] = 0
            utils.log("scroll_more", f"已连滑 {limit} 次，本段到此为止")
            return CustomRecognition.AnalyzeResult(box=None, detail={"原因": "预算用尽"})

        current = self._region_signature(argv.image, roi)
        if self._same_scene(state["signature"], current):
            # 这一段连滑结束了（到顶/到底/滑不动）：计数归零，让下一段从满预算开始。
            # 不归零的话 max_scroll 会变成"本进程一辈子只准滑几次"，第二次跑任务就静默不动了。
            state["scrolls"] = 0
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