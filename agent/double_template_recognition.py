import json

from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context


@AgentServer.custom_recognition("double_template_recognition")
class DoubleTemplateRecognition(CustomRecognition):

    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        # 解析param json字符串
        custom_params = json.loads(argv.custom_recognition_param)

        # 调用agent_template_recognition节点，并修改template来进行识别
        reco_detail = context.run_recognition(
            "agent_template_recognition",
            argv.image,
            pipeline_override={"agent_template_recognition": {"template": custom_params["template"]}}
        )
        
        if not reco_detail.hit:
            return None
        
        # 再次调用agent_template_recognition节点，修改template和上一个识别得到的roi来进行识别
        target_reco_detail=context.run_recognition(
            "agent_template_recognition",
            argv.image,
            pipeline_override={
                "agent_template_recognition": {
                    "template": custom_params["target_template"],
                    # 注意是数组的形式
                    "roi": [reco_detail.box.x, reco_detail.box.y, reco_detail.box.w, reco_detail.box.h]
                }
            }
        )

        if not target_reco_detail.hit:
            return None
        
        return CustomRecognition.AnalyzeResult(
            box=target_reco_detail.box, detail="target定位成功"
        )