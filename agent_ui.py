import requests
import json
import os
import re
from datetime import datetime
import gradio as gr

# ===== 工具 =====

def calculate(expression):
    try:
        return str(eval(expression))
    except:
        return "计算错误"

def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()[:1000]
    except Exception as e:
        return f"读取失败: {e}"

def list_files(path="."):
    try:
        return "\n".join(os.listdir(path))
    except Exception as e:
        return f"读取目录失败: {e}"

def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

TOOLS = {
    "calculate": calculate,
    "read_file": read_file,
    "list_files": list_files,
    "get_time": lambda: get_time()
}

# ===== JSON容错解析（关键） =====

def extract_json(text):
    try:
        return json.loads(text)
    except:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                return None
    return None


# ===== Agent逻辑 =====

def agent_logic(user_input, history):
    url = "http://127.0.0.1:11434/api/generate"

    system_prompt = """
你是一个AI助手，可以调用工具。

【工具列表】
calculate(expression)
read_file(path)
list_files(path)
get_time()

【规则（必须严格遵守）】
1. 如果需要调用工具，只能输出JSON
2. 不要输出任何解释文字
3. 格式必须是：

{"tool": "工具名", "args": {"参数": "值"}}

【示例】
用户：2+2是多少
输出：
{"tool": "calculate", "args": {"expression": "2+2"}}

用户：现在几点
输出：
{"tool": "get_time", "args": {}}

如果不需要工具，正常回答。
"""

    prompt = system_prompt + "\n用户：" + user_input

    data = {
        "model": "qwen3:8b",
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(url, json=data)
    result = response.json()["response"].strip()
       # 👉 调试输出（非常重要）
    print("模型原始输出：", result)

    # ===== 工具调用判断 =====
    tool_call = extract_json(result)

    if tool_call:
        tool_name = tool_call.get("tool")
        args = tool_call.get("args", {})

        if tool_name in TOOLS:
            tool_result = TOOLS[tool_name](**args)

            final_prompt = f"""
用户问题：{user_input}
工具执行结果：{tool_result}
请用自然语言给出最终回答
"""

            final_data = {
                "model": "qwen3:8b",
                "prompt": final_prompt,
                "stream": True
            }

            stream_response = requests.post(url, json=final_data, stream=True)

            full = ""
            for line in stream_response.iter_lines():
                if line:
                    chunk = line.decode("utf-8")
                    try:
                        data = json.loads(chunk)
                        content = data.get("response", "")
                        full += content
                        yield full
                    except:
                        continue
        return
           # ===== 普通聊天（流式）=====
    data["stream"] = True
    stream_response = requests.post(url, json=data, stream=True)

    full = ""
    for line in stream_response.iter_lines():
        if line:
            chunk = line.decode("utf-8")
            try:
                data = json.loads(chunk)
                content = data.get("response", "")
                full += content
                yield full
            except:
                continue

# ===== UI =====

demo = gr.ChatInterface(
    fn=agent_logic,
    title="🔥 本地多技能Agent（稳定版）",
    description="支持：计算 / 文件 / 时间 / 自动工具调用"
)

demo.launch()