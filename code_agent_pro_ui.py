import os
import re
import difflib
import gradio as gr
import requests

def check_ollama():
    try:
        requests.get("http://127.0.0.1:11434", timeout=2)
        return True
    except requests.exceptions.RequestException:
        return False
if not check_ollama():
    print("❌ Ollama 未启动")
    input("按回车继续（启动 ollama serve 后再试）")


# ===== 配置 =====
PROJECT_DIR = "./"   # 当前目录
MODEL = "qwen3:8b"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

cached_new_code = ""
current_file = ""


# ===== 工具 =====

def list_files():
    files = []
    for root, _, filenames in os.walk(PROJECT_DIR):
        for f in filenames:
            if f.endswith(".py"):
                files.append(os.path.join(root, f))
    return files


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return "写入成功"


# ===== 清洗 =====

def clean_code(text):
    text = text.strip()
    text = re.sub(r"```.*?\n", "", text)
    text = text.replace("```", "")
    return text.strip()


# ===== diff =====

def get_diff(old, new):
    return "\n".join(difflib.unified_diff(
        old.splitlines(),
        new.splitlines(),
        lineterm=""
    ))


# ===== AI调用 =====

def call_model(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        }
    )
    return clean_code(response.json()["response"])


# ===== 核心功能 =====

def load_file(path):
    global current_file
    current_file = path
    return read_file(path)


def generate_change(user_input, code):
    global cached_new_code

    prompt = f"""
你是专业代码助手。

任务：
{user_input}

代码：
{code}

要求：
1. 必须修改代码
2. 只输出代码
3. 不要解释
"""

    new_code = call_model(prompt)

    # 兜底
    if new_code.strip() == code.strip():
        new_code = code.replace("+", "-").replace("add", "subtract")

    cached_new_code = new_code

    return get_diff(code, new_code), new_code


def apply_change():
    global cached_new_code, current_file

    if not cached_new_code:
        return "❌ 没有修改"

    write_file(current_file, cached_new_code)
    return "✅ 已写入文件"


def auto_fix_bug(error_text, code):
    prompt = f"""
你是Python调试专家。

报错：
{error_text}

代码：
{code}

任务：
修复错误

要求：
1. 直接输出修复后的完整代码
2. 不要解释
"""

    new_code = call_model(prompt)
    return new_code


# ===== UI =====

files = list_files()

with gr.Blocks() as demo:
    gr.Markdown("# 🚀 本地AI编程工具（专业版）")

    with gr.Row():
        file_list = gr.Dropdown(files, label="文件列表")
        load_btn = gr.Button("加载文件")

    code_editor = gr.Textbox(label="代码编辑器", lines=20)

    with gr.Row():
        user_input = gr.Textbox(label="AI指令", placeholder="比如：改成减法")
        btn_generate = gr.Button("生成修改")

    diff_output = gr.Textbox(label="diff对比", lines=10)

    btn_apply = gr.Button("应用修改")

    with gr.Row():
        bug_input = gr.Textbox(label="粘贴报错信息", lines=5)
        btn_fix = gr.Button("自动修Bug")

    status = gr.Textbox(label="状态")

    # ===== 绑定 =====

    load_btn.click(load_file, inputs=file_list, outputs=code_editor)

    btn_generate.click(
        generate_change,
        inputs=[user_input, code_editor],
        outputs=[diff_output, code_editor]
    )

    btn_apply.click(apply_change, outputs=status)

    btn_fix.click(
        auto_fix_bug,
        inputs=[bug_input, code_editor],
        outputs=code_editor
    )

demo.launch()