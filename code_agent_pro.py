import requests
import json
import re
import difflib

# ===== 工具 =====

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return "写入成功"


# ===== 清洗输出 =====

def clean_code(text):
    text = text.strip()
    text = re.sub(r"```.*?\n", "", text)
    text = text.replace("```", "")
    return text.strip()


# ===== 生成 diff =====

def show_diff(old, new):
    diff = difflib.unified_diff(
        old.splitlines(),
        new.splitlines(),
        lineterm=""
    )
    return "\n".join(diff)


# ===== Agent =====

def code_agent(user_input):
    url = "http://127.0.0.1:11434/api/generate"

    # ===== 读取文件 =====
    path = "test.py"
    old_code = read_file(path)

    print("\n📄 原始代码：\n", old_code)

    # ===== 让模型修改 =====
    prompt = f"""
你是一个专业代码修改助手。

必须修改代码：
- 根据用户要求修改
- 必须产生实际变化
- 只输出代码
- 不要解释

原始代码：
{old_code}

用户要求：
{user_input}
"""

    data = {
        "model": "qwen3:8b",
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(url, json=data)
    new_code = clean_code(response.json()["response"])

    print("\n✏️ 修改后代码：\n", new_code)

    # ===== 差异检查 =====
    if new_code.strip() == old_code.strip():
        print("⚠️ 模型未修改代码，执行兜底修复")
        new_code = old_code.replace("+", "-").replace("add", "subtract")

    # ===== 显示 diff =====
    print("\n📊 差异对比：")
    diff = show_diff(old_code, new_code)
    print(diff)

    # ===== 用户确认 =====
    confirm = input("\n是否应用修改？(y/n): ")

    if confirm.lower() != "y":
        return "❌ 已取消修改"

  # ===== 写入 =====
    result = write_file(path, new_code)

    return f"\n✅ 修改完成\n{result}"


# ===== CLI =====

if __name__ == "__main__":
    while True:
        try:
            user_input = input("\n你：")
            print("AI：", code_agent(user_input))
        except KeyboardInterrupt:
            print("\n👋 已退出")
            break        