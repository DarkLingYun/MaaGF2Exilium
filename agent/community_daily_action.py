"""社区每日操作 —— CommunityDailyAction 的 Python agent 实现。

原实现是 MFAAvalonia 专用的 C# 自定义动作
(assets/resource/custom/CommunityDailyHelper.cs)：它依赖 .NET 运行时，以及
MFAAvalonia.Helper 提供的日志与提示服务。MXU 是 Tauri + Rust 客户端，无法加载
C# 自定义动作，所以这里用 MaaFramework 的 agent 协议重新实现同一套逻辑。

pipeline 节点里的 ``"custom_action": "CommunityDailyAction"`` 匹配的就是下面
注册的这个名字，资源与 pipeline 都不需要改动。

与 C# 版本的差异：

- HTTP 全部使用标准库 ``urllib.request``。打包产物里的嵌入式 Python 只安装了
  ``maafw`` 和 ``maaagentbinary``，而 ``maafw`` 的依赖仅有
  ``maaagentbinary`` / ``numpy`` / ``strenum``，并不包含 ``requests``，
  因此这里不能引入第三方 HTTP 库。
- ``LoggerHelper.Info`` / ``Error`` 换成 ``print``，由 GUI 捕获 agent 的 stdout
  展示。``ToastHelper.Error`` 没有等价能力，失败信息只写日志。
- ``secret.json`` 改按「interface.json 所在目录 / config」定位，与 README 中
  「脚本程序根目录下 config 目录」的描述一致。
"""

import hashlib
import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction

API_BASE = "https://gf2-bbs-api.exiliumgf.com"

# C# 侧用的是 HttpClient 的默认超时（100s）。这里收紧到 30s：这几个都是小 JSON
# 接口，长时间挂起只会让整条任务链卡住而拿不到有效信息。
HTTP_TIMEOUT = 30

# 兑换的物品 id 与顺序，与 C# 版本保持一致（1 兑换两次）
EXCHANGE_IDS = (1, 1, 2, 3, 4, 5, 7)

# 两次兑换之间的间隔（秒），避免请求过于密集
EXCHANGE_INTERVAL = 1.0

# 浏览/点赞/分享的话题个数
TOPIC_COUNT = 3

SECRET_TEMPLATE = {
    "account_name": "手机号或邮箱密文",
    "passwd": "密码密文",
    "source": "phone或mail 根据登录的账号类型填写",
}

SECRET_HELP = (
    "请检查 `config/secret.json` 是否正确填写. `config/secret.json` 要填入三个字段: "
    "account_name 对应账户名称, passwd 对应密码密文, source 对应账户类型(mail或phone)."
)


# --------------------------------------------------------------------------
# 路径与日志
# --------------------------------------------------------------------------


def project_root() -> Path:
    """interface.json 所在目录，即 agent/ 的上一级。"""
    return Path(__file__).resolve().parents[1]


def secret_path() -> Path:
    return project_root() / "config" / "secret.json"


def log(message: str) -> None:
    """agent 的 stdout 会被 GUI 捕获显示，因此直接用 print。"""
    print(message, flush=True)


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------


def request(method: str, url: str, token: str = None, payload: dict = None) -> str:
    """发一次请求并返回响应体文本。

    非 2xx 会抛 ``urllib.error.HTTPError``，与 C# 的
    ``EnsureSuccessStatusCode()`` 行为一致，交由各调用方决定是否吞掉。
    """
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        # C# 用的是 new AuthenticationHeaderValue(token)，即 Authorization 头
        # 直接放 token 本身，没有 "Bearer " 前缀，这里保持一致。
        headers["Authorization"] = token

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as response:
        return response.read().decode("utf-8")


# --------------------------------------------------------------------------
# 社区接口
# --------------------------------------------------------------------------


def login(payload: dict) -> str:
    """登录并返回 JWT token。失败时上抛，与 C# 一致。"""
    body = request("POST", f"{API_BASE}/login/account", payload=payload)
    login_response = json.loads(body)

    if login_response.get("Code") != 0:
        raise RuntimeError(f"用户名或密码错误. {SECRET_HELP}")

    # C# 在这里会因为 data/account 为 null 抛 NullReferenceException，
    # 这里换成能看懂的错误信息。
    account = ((login_response.get("data") or {}).get("account")) or {}
    token = account.get("token")
    if not token:
        raise RuntimeError(f"登录响应中没有 token. {SECRET_HELP}")
    return token


def exchange_item(exchange_id: int, token: str) -> None:
    """兑换物品。失败只记日志不中断，与 C# 一致。"""
    try:
        body = request(
            "POST",
            f"{API_BASE}/community/item/exchange",
            token=token,
            payload={"exchange_id": exchange_id},
        )
        log(f"物品兑换: {body}")
    except Exception as exc:  # 与 C# 的 catch (Exception) 对齐
        log(f"社区每日操作: 兑换失败, {exc}")


def sign_in(token: str) -> None:
    """每日签到。失败会上抛，从而跳过后续的兑换步骤，与 C# 一致。"""
    try:
        request("POST", f"{API_BASE}/community/task/sign_in", token=token, payload={})
    except Exception as exc:
        # 沿用 C# 原文案（原文就是「登录失败」），避免改动用户可见字符串
        log(f"社区每日操作: 登录失败, {exc}")
        raise


def get_topic_list() -> list:
    """取前 TOPIC_COUNT 个话题 id。失败返回空列表不中断，与 C# 一致。"""
    try:
        body = request("GET", f"{API_BASE}/community/topic/list?sort_type=2")
        topics = ((json.loads(body).get("data") or {}).get("list")) or []
        topic_ids = [topic.get("topic_id") for topic in topics[:TOPIC_COUNT]]
        log(f"TopicIDs: {', '.join(str(topic_id) for topic_id in topic_ids)}")
        return topic_ids
    except Exception as exc:
        log(f"社区每日操作: Topic获取失败, {exc}")
        return []


def topic_handle(topic_id: int, token: str) -> None:
    """浏览 / 点赞 / 分享单个话题。失败只记日志，与 C# 一致。"""
    try:
        base = f"{API_BASE}/community/topic"
        log(f"TopicView: {request('GET', f'{base}/{topic_id}?id={topic_id}', token=token)}")
        log(f"TopicLike: {request('GET', f'{base}/like/{topic_id}?id={topic_id}', token=token)}")
        log(f"TopicShare: {request('GET', f'{base}/share/{topic_id}?id={topic_id}', token=token)}")
    except Exception as exc:
        log(f"社区每日操作: Topic操作失败, {exc}")


def execute_daily_task(payload: dict) -> None:
    """执行一轮社区每日操作：签到 + 话题互动 + 兑换。"""
    log("社区每日操作: 开始")

    # 登录与取话题列表互不依赖，并发执行（对应 C# 的 Task.WhenAll）
    with ThreadPoolExecutor(max_workers=2) as pool:
        login_future = pool.submit(login, payload)
        topics_future = pool.submit(get_topic_list)
        token = login_future.result()  # 登录失败在这里上抛
        topic_ids = topics_future.result()

    # 签到与话题互动并发。签到失败会上抛，跳过下面的兑换，与 C# 一致。
    with ThreadPoolExecutor(max_workers=1 + len(topic_ids)) as pool:
        futures = [pool.submit(sign_in, token)]
        futures += [pool.submit(topic_handle, topic_id, token) for topic_id in topic_ids]
        for future in futures:
            future.result()

    # 兑换串行执行并加间隔，避免请求过于密集
    for exchange_id in EXCHANGE_IDS:
        exchange_item(exchange_id, token)
        time.sleep(EXCHANGE_INTERVAL)
    log("社区每日操作: 兑换成功")


# --------------------------------------------------------------------------
# 密文与配置
# --------------------------------------------------------------------------


def md5_hashed_password(password: str) -> str:
    """把明文密码转成 secret.json 用的密文（小写十六进制 MD5）。

    与 C# 的 PasswordHelper.GetMD5HashedPassword 等价。注意 C# 原实现同样没有
    出现在调用链里 —— secret.json 填的是用户事先算好的密文，运行时不再二次
    加密。这里保留同名实现以维持 parity，需要时可直接调用。
    """
    if not password:
        raise ValueError("密码不能为空, 请检查 `config/secret.json` 内的 passwd 字段是否正确设置")
    return hashlib.md5(password.encode("utf-8")).hexdigest()


def strip_json_comments(text: str) -> str:
    """去掉 JSON 里的 ``//`` 与 ``/* */`` 注释，字符串内部的不动。

    C# 读取 secret.json 时用了 JsonCommentHandling.Skip，为了让带注释的历史
    文件继续可用，这里做等价处理。
    """
    out = []
    index = 0
    length = len(text)
    in_string = False

    while index < length:
        char = text[index]

        if in_string:
            out.append(char)
            if char == "\\" and index + 1 < length:
                out.append(text[index + 1])
                index += 2
                continue
            if char == '"':
                in_string = False
            index += 1
            continue

        if char == '"':
            in_string = True
            out.append(char)
            index += 1
            continue

        if char == "/" and index + 1 < length:
            following = text[index + 1]
            if following == "/":
                while index < length and text[index] not in "\r\n":
                    index += 1
                continue
            if following == "*":
                index += 2
                while index + 1 < length and not (text[index] == "*" and text[index + 1] == "/"):
                    index += 1
                index += 2
                continue

        out.append(char)
        index += 1

    return "".join(out)


def ensure_secret_file(path: Path) -> None:
    """首次运行时按模板生成 secret.json，与 C# 一致。"""
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(SECRET_TEMPLATE, ensure_ascii=False, indent=4),
        encoding="utf-8",
    )
    log(f"已生成配置模板: {path}")


def load_payload(path: Path) -> dict:
    """读取并校验 secret.json。"""
    text = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        # 兜底：兼容带注释的历史文件
        payload = json.loads(strip_json_comments(text))

    if payload is None:
        raise ValueError("反序列化结果为 null")

    source = payload.get("source")
    if not source or source not in ("mail", "phone"):
        raise ValueError(
            "source 字段值无效. 请检查 `config/secret.json` 中 source 字段只能为 `mail` 或 `phone`."
        )
    return payload


# --------------------------------------------------------------------------
# 自定义动作
# --------------------------------------------------------------------------


@AgentServer.custom_action("CommunityDailyAction")
class CommunityDailyAction(CustomAction):
    """pipeline 节点 CommunityDailyHelper 对应的自定义动作。"""

    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:
        try:
            path = secret_path()
            ensure_secret_file(path)
            payload = load_payload(path)

            # 用户填写的就是密文，这里不再做二次加密
            execute_daily_task(payload)

            log("社区每日操作: 执行成功")
            return True
        except Exception as exc:
            log(f"社区每日操作: 执行失败, {exc}")
            return False
