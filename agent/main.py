import sys

from maa.agent.agent_server import AgentServer
from maa.toolkit import Toolkit

# 注意要把实现的自定义识别、动作的代码import进来才会生效
import double_template_recognition

def main():
    Toolkit.init_option("./")

    if len(sys.argv) < 2:
        print("Usage: python main.py <socket_id>")
        print("socket_id is provided by AgentIdentifier.")
        sys.exit(1)
        
    socket_id = sys.argv[-1]

    AgentServer.start_up(socket_id)
    AgentServer.join()
    AgentServer.shut_down()


if __name__ == "__main__":
    main()