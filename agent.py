import requests
import json

# ===== 技能1：计算器 =====
def calculate(expression):
    try:
        return str(eval(expression))
    except:
        return "计算错误"


# ===== Agent =====
def agent_chat(user_input):
    url = "http://127.0.0.1:11434/api/generate"

    # 给模型一个“工具说明”
    system_prompt = """
你是一个智能助手，可以使用工具。

如果用户让你计算，请返回：
CALL_TOOL: calculate(表达式)

否则正常回答。
"""

    prompt = system_prompt + "\n用户：" + user_input

    data = {
        "model": "qwen3:8b",
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(url, json=data)
    result = response.json()["response"]

    # ===== 判断是否调用工具 =====
    if result.startswith("CALL_TOOL:"):
        tool_call = result.replace("CALL_TOOL:", "").strip()

        if tool_call.startswith("calculate"):
            expr = tool_call[10:-1]  # 取括号里的内容
            tool_result = calculate(expr)

            return f"计算结果：{tool_result}"

    return result


# ===== 测试 =====
while True:
    user_input = input("你：")
    reply = agent_chat(user_input)
    print("AI：", reply)