from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction

class State:
    """自定义节点跨任务保留的状态。

    识别/动作的实例由框架持有并在整个进程里复用，所以状态**跨任务保留**：
    不清空的话第二次跑任务会带着上一次的结果。配套 `reset_action()` 挂到任务入口。

    构造时给一份"出厂值"，`reset()` 就恢复成它们（可变值会复制一份）。
    """

    def __init__(self, **defaults):
        self._defaults = defaults
        self.reset()

    def reset(self):
        for name, value in self._defaults.items():
            setattr(self, name, value.copy() if hasattr(value, "copy") else value)


def reset_action(action_name, state, label):
    """生成一个「把 state 清空」的自定义动作类并注册。

    返回类，注册靠的是装饰器副作用（本仓库的约定：`main.py` 里 import 即注册）。
    """

    @AgentServer.custom_action(action_name)
    class _ResetState(CustomAction):
        def run(self, context, argv):
            # 惰性导入：pi_common 末尾要再导出本模块，模块级互相 import 会成环
            from . import pi_common

            state.reset()
            pi_common.log(label, "已清空记录")
            return CustomAction.RunResult(success=True)

    return _ResetState