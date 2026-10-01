"""通用商店兑换 —— 识别用户勾选的商品并购买。

## 使用说明

1. 统一在本文件最底下注册节点`SHOP_REPUTATION = _register_shop("{pipeline_name}", "{log_prefix}")`。

2. 在json资源里写 pipeline 节点：
注册后会生成两个节点{pipeline_name}和{pipeline_name}_reset，前者是识别选择商品节点，后者是状态清除节点，状态包含已购买商品标记等信息。各注册节点的状态是独立的，互不干扰。

3. {pipeline_name}节点配置示例：
"myShop-selection": {
    "recognition": "Custom",
    "custom_recognition": "{pipeline_name}",
    "custom_recognition_param": {
        "roi": [205, 80, 1013, 600] // 必须指定识别区域
    },
    "attach": { // 货架清单，键 → false(未勾选)。在interface.json中使用pipeline_override配置OCR识别内容(支持多语言)
        "ppsh_neural_archive": false,
        "...": false
    },
    "next": ["myShop-soldOut", "myShop-selectItem"]
}
"""

import common.pi_common as utils
from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition


def read_catalog(context, node_name, label):
    """读出本节点 `attach` 里被勾选的商品，返回 `[(键, 别名, 正则), ...]`。
    """
    data = context.get_node_data(node_name) or {}
    attach = data.get("attach") or {}
    if not isinstance(attach, dict):
        utils.log(label, f"attach 不是对象（{type(attach).__name__}），当作没勾选")
        return []

    catalog = []
    for key, aliases in attach.items():
        # 没勾的键由 pipeline 里那份 `false` 兜着；被勾的 case 才写别名列表。
        # 判的是**假值**不是 None：写个空列表进来同样算没勾。
        if not aliases:
            continue
        patterns = utils.alias_patterns(aliases)
        if not patterns:
            # 勾了，但别名全被过滤掉了（空串或只有空白）。这一项永远不会命中，
            # 表现成"勾了却买不到"，不吭声的话很难查。
            utils.log(label, f"「{key}」的别名表是空的，这一项永远不会命中")
            continue
        catalog.append((key, aliases, patterns))
    return catalog


def center_box(box):
    """把一段文字的框收成它的中心点（1x1）。"""
    x, y, w, h = box
    return (x + w // 2, y + h // 2, 1, 1)


def _register_shop(name, label, reset_name=None):
    """把商店注册成一对自定义节点（识别 + 配套的重置动作），返回识别器的类对象。

    参数：
        name        识别器注册名，= pipeline `custom_recognition` 的值。
        label       日志前缀，用来分辨是哪家商店。重置动作共用它。
        reset_name  配套重置动作的注册名，默认 `<name>_reset`。

    ⚠️ 这个函数在**模块 import 时**被调用：节点名字重复会当场抛 RuntimeError
    （框架那边抛的），整个 agent 进程起不来，GUI 上看不到任何诊断。
    """
    state = utils.State(done=set(), catalog=None)
    utils.reset_action(reset_name or f"{name}_reset", state, label)

    @AgentServer.custom_recognition(name)
    class _ShopPicker(CustomRecognition):
        """按用户的勾选，挑出屏幕上下一个该买的商品。"""

        # 别在这里加 __init__：基类的 __init__ 要设 self._handle，漏调会炸在注册那步。
        # 状态也**不要**挂到 self 上——探针会给同一个类再 new 一个实例去注册资源，
        # self 上的东西不共享，闭包里的 state 才共享。

        def analyze(self, context, argv):
            # 自定义识别跑在 ctypes 回调里，抛出去的异常只会被静默吞掉、表现为"任务瞬间
            # 跑完什么都没做"，所以整体兜底并显式返回一次失败。
            try:
                return self._pick(context, argv)
            except Exception as error:
                utils.log(label, f"识别异常，按未命中处理：{error!r}")
                return CustomRecognition.AnalyzeResult(box=None, detail={"异常": repr(error)})

        def _catalog(self, context, node_name):
            """本节点要买的清单。第一次用到时才读，之后一直用缓存。
            """
            cached = state.catalog
            if cached is None or cached[0] != node_name:
                cached = (node_name, read_catalog(context, node_name, label))
                utils.log(label, f"加载购买商品清单")
                state.catalog = cached
            return cached[1]

        def _pick(self, context, argv):
            params = utils.load_param(argv.custom_recognition_param)
            roi = params.get("roi")
            if not roi:
                utils.log(label, "roi未配置，不允许使用")
                return CustomRecognition.AnalyzeResult(box=None, detail={"原因": "roi未配置，不允许使用"})

            catalog = self._catalog(context, argv.node_name)
            if not catalog:
                return CustomRecognition.AnalyzeResult(box=None, detail={"原因": "购买商品清单为空/未勾选任何商品"})

            # 别名先合并成一次 OCR
            words = [(text, box) for text, box in utils.ocr_words(
                context, argv.image, roi,
                expected=[p for _, _, patterns in catalog for p in patterns]) if box]
            if not words:
                utils.log(label, "roi区域未识别到商品")
                return CustomRecognition.AnalyzeResult(box=None, detail={"原因": "roi区域未识别到商品"})

            # 按屏幕位置从上到下、从左到右挑——和用户看到的顺序一致。
            for text, box in sorted(words, key=lambda word: (word[1][1], word[1][0])):
                matched = [key for key, _, patterns in catalog
                           if key not in state.done and utils.match_alias(text, patterns)]
                if not matched:
                    continue
                if len(matched) > 1:
                    utils.log(label, f"别名重复：「{text}」同时命中 {matched}，取第一个。")
                return self._hit(matched[0], text, box)

            utils.log(label, "本页商品已全部购买/本页未命中商品")
            return CustomRecognition.AnalyzeResult(box=None, detail={"原因": "本页商品已全部购买/本页未命中商品"})

        def _hit(self, key, text, box):
            state.done.add(key)
            utils.log(label, f"选择商品「{text}」→ {key}，文字框 {tuple(box)}")
            return CustomRecognition.AnalyzeResult(
                box=center_box(box), detail={"选择商品": key, "文字": text, "文字框": list(box)})

    return _ShopPicker


# 商店登记表
SHOP_REPUTATION = _register_shop("reputation_shop", "声望商店")
