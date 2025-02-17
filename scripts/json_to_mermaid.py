import json


def json_to_mermaid(json_file_path):
    # 1. 读取 JSON 文件
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 2. Mermaid 结果用列表存储，稍后join输出
    mermaid_lines = []
    mermaid_lines.append("graph TD")  # 可改为 graph LR, graph TB 等

    # 3. 遍历大字典
    for key, obj in data.items():
        # 取出 doc，如果没有 doc，就用空字符串或其他占位
        doc_str = obj.get("doc", "")

        # 构造节点名称：键|doc
        # 如果 doc 为空，就不显示 -doc 部分
        node_label = f"{key}-{doc_str}" if doc_str else key

        # 仅当有 next 且为列表时，才继续画连线
        if "next" in obj and isinstance(obj["next"], list):
            for i, next_key in enumerate(obj["next"]):
                # 找到 next_key 的 doc
                next_obj = data.get(next_key, {})
                next_doc_str = next_obj.get("doc", "")
                next_node_label = (
                    f"{next_key}-{next_doc_str}" if next_doc_str else next_key
                )

                # 生成一行 Mermaid 连线： 'A-DocA' -->|i| 'B-DocB'
                mermaid_lines.append(f"    '{node_label}' -->|{i}| '{next_node_label}'")

    # 拼成完整 Mermaid 字符串
    mermaid_result = "\n".join(mermaid_lines)
    return mermaid_result


if __name__ == "__main__":
    json_file = r"assets\resource\pipeline\public\SimulatedCombat\liveDrillCombatLogic.json"  # 你的 JSON 文件路径
    mermaid_code = json_to_mermaid(json_file)
    # 文件保存到项目根目录方便复制，控制台输出会有点格式的问题
    with open("mermaid.mmd", "w", encoding="utf-8") as f:
        f.write(mermaid_code)
    # 如果本地支持，可以直接放到本地运行，或者复制到 https://mermaid.live/ 上查看效果
