import requests
import json
import os
from datetime import datetime

# ===== 工具定义 =====

def calculate(expression):
    try:
        return str(eval(expression))
    except:
        return "计算错误"

def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()[:1000]  # 防止太长
    except Exception as e:
        return f"读取失败: {e}"

def list_files(path="."):
    try:
        return "\n".join(os.listdir(path))
    except Exception as e:
        return f"读取目录失败: {e}"

def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ===== 工具映射 =====

TOOLS = {
    "calculate": calculate,
    "read_file": read_file,
    "list_files": list_files,
    "get_time": lambda: get_time()
}


# ===== Agent核心 =====

def agent_chat(user_input):
    url = "http://127.0.0.1:11434/api/generate"

    system_prompt = """
你是一个智能助手，可以使用工具。

可用工具：
1. calculate(expression) 计算数学
2. read_file(path) 读取文件
3. list_files(path) 列出目录
4. get_time() 获取当前时间

如果需要使用工具，请返回 JSON 格式：
{"tool": "工具名", "args": {"参数名": "值"}}

否则直接回答用户问题。
"""

    prompt = system_prompt + "\n用户：" + user_input

    data = {
        "model": "qwen3:8b",
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(url, json=data)
    result = response.json()["response"].strip()

    # ===== 判断是否是工具调用 =====
    try:
        tool_call = json.loads(result)

        tool_name = tool_call["tool"]
        args = tool_call.get("args", {})

        if tool_name in TOOLS:
            tool_result = TOOLS[tool_name](**args)

            # 再让模型总结结果
            final_prompt = f"用户问题：{user_input}\n工具结果：{tool_result}\n请给出最终回答"

            final_data = {
                "model": "qwen3:8b",
                "prompt": final_prompt,
                "stream": False
            }

            final_response = requests.post(url, json=final_data)
            return final_response.json()["response"]

    except:
        pass

    return result


# ===== 运行 =====

while True:
    user_input = input("你：")
    reply = agent_chat(user_input)
    print("AI：", reply)