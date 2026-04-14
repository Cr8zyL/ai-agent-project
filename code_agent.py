import requests
import json
import re

# ===== 工具 =====

def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"读取失败: {e}"

def write_file(path, content):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return "写入成功"
    except Exception as e:
        return f"写入失败: {e}"


# ===== JSON容错解析 =====

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


# ===== 清洗模型输出 =====

def clean_code(text):
    text = text.strip()
    text = re.sub(r"```.*?\n", "", text)
    text = text.replace("```", "")
    return text.strip()


# ===== Agent =====

def code_agent(user_input):
    url = "http://127.0.0.1:11434/api/generate"

    system_prompt = """
你是一个代码修改助手。

你必须调用工具，不能直接回答。

规则：
1. 只能返回JSON
2. 必须先调用 read_file
3. 默认文件 test.py

格式：
{"tool": "read_file", "args": {"path": "test.py"}}
"""

    prompt = system_prompt + "\n用户：" + user_input

    data = {
        "model": "qwen3:8b",
        "prompt": prompt,
        "stream": False
    }

 # ===== 第一步：模型决策 =====
    response = requests.post(url, json=data)
    result = response.json()["response"].strip()

    print("\n🧠 模型输出：")
    print(result)

    tool_call = extract_json(result)

    if not tool_call or "tool" not in tool_call:
        return f"❌ 工具调用失败：\n{result}"

    tool_name = tool_call.get("tool")
    args = tool_call.get("args", {})

    if "path" not in args:
        args["path"] = "test.py"

    # ===== 核心逻辑 =====
    if tool_name == "read_file":
        file_content = read_file(**args)

        if "读取失败" in file_content:
            return file_content

        print("\n📄 原始代码：\n", file_content)

        # ===== 修改代码 =====
        modify_prompt = f"""
你是一个严格的代码修改器。

必须修改代码：
- 把 add 改成 subtract
- 把 + 改成 -

只输出代码，不要解释

原始代码：
{file_content}

用户要求：
{user_input}
"""

        modify_data = {
            "model": "qwen3:8b",
            "prompt": modify_prompt,
            "stream": False
        }

        modify_response = requests.post(url, json=modify_data)
        new_code = clean_code(modify_response.json()["response"])

        print("\n✏️ 修改后代码：\n", new_code)

        # ===== 强制修复（兜底）=====
        if new_code.strip() == file_content.strip() or len(new_code) < 10:
            print("⚠️ 模型没有正确修改，执行强制修复")
            new_code = file_content.replace("+", "-").replace("add", "subtract")

        print("\n📦 最终写入代码：\n", new_code)

        # ===== 写回文件（关键就在这里）=====
        write_result = write_file(args["path"], new_code)

        return f"\n✅ 修改完成\n{write_result}"

    elif tool_name == "write_file":
        return write_file(**args)

    return "未执行任何操作"


# ===== CLI =====

if __name__ == "__main__":
    while True:
        try:
            user_input = input("\n你：")
            print("AI：", code_agent(user_input))
        except KeyboardInterrupt:
            print("\n👋 已退出")
            break