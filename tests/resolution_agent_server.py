"""Minimal Agent transport fixture; no game inputs or other custom actions."""

import sys
from pathlib import Path

from maa.agent.agent_server import AgentServer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agent"))
from resolution_check import PCResolutionCheck

AgentServer.register_custom_action("CheckPCResolution", PCResolutionCheck())
AgentServer.start_up(sys.argv[-1])
AgentServer.join()
AgentServer.shut_down()
