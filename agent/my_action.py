from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context


@AgentServer.custom_action("日常任务前准备")
class MyCustomAction(CustomAction):

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        context.run_task(
            "claimIntelligenceSupplyStaminaTaskTimed"
        )  # 限时任务次序：1 领取情报补给体力任务(限时)
        context.run_task(
            "claimSevenDayCheckInResourceTaskTimed"
        )  # 限时任务次序：2 领取七日签到资源任务(限时)
        context.run_task("getNewEmails")  # 领取邮件任务
        # context.run_task(
        #     "staminaReplenishment"
        # )  # 用光全部体力，这个功能的退出有点问题，但是没人反馈可见没人用，暂时不修了
        context.run_task("enterShop")  # 进入商店购买每日补给
        context.run_task("enterBoundaryAdvanceAction")  # 进入边界推进
        context.run_task("organizeStoreroom")  # 整理仓库
        context.run_task("HomePage")  # 返回主页

        print("MyCustomAction is running!")
        return True
