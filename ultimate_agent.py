import os
import sys
import requests
import tkinter as tk
from tkinter import scrolledtext
import difflib
import threading
import subprocess

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen3:8b"

current_file = None
cached_code = ""
last_error = ""

# ===== 安全执行命令 =====
def safe_run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        return None

# ===== 检查 Git =====
def check_git():
    return safe_run(["git", "--version"]) is not None

# ===== 初始化 Git =====
def init_git():
    if not check_git():
        print("⚠️ Git 未安装或未加入 PATH")
        return
    if not os.path.exists(".git"):
        safe_run(["git", "init"])
        safe_run(["git", "add", "."])
        safe_run(["git", "commit", "-m", "init"])

# ===== 检查 Ollama =====
def check_ollama():
    try:
        requests.get("http://127.0.0.1:11434", timeout=1)
        return True
    except:
        return False

# ===== 调用模型 =====
def call_model(prompt):
    try:
        res = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False},
            timeout=60
        )
        return res.json().get("response", "")
    except Exception as e:
        return f"❌ 模型错误: {e}"

# ===== 文件操作 =====
def list_files():
    files = []
    for root, _, fs in os.walk("."):
        for f in fs:
            if f.endswith(".py"):
                files.append(os.path.join(root, f))
    return files

def load_file(path, editor):
    global current_file
    current_file = path
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    editor.delete("1.0", tk.END)
    editor.insert(tk.END, content)

def save_file(content):
    if current_file:
        with open(current_file, "w", encoding="utf-8") as f:
            f.write(content)

# ===== diff =====
def get_diff(old, new):
    return "\n".join(difflib.unified_diff(
        old.splitlines(),
        new.splitlines(),
        lineterm=""
    ))

# ===== AI修改 =====
def run_ai(editor, diff_box, status, user_input):
    global cached_code

    if not check_ollama():
        status.set("❌ Ollama未启动")
        return

    old_code = editor.get("1.0", tk.END)

    prompt = f"""
修改代码：
{user_input}

代码：
{old_code}

只输出完整代码，不解释
"""

    new_code = call_model(prompt)

    if not new_code.strip():
        status.set("❌ AI无响应")
        return

    cached_code = new_code

    diff_box.delete("1.0", tk.END)
    diff_box.insert(tk.END, get_diff(old_code, new_code))

    status.set("🟡 已生成修改")


# ===== 运行代码 =====
def run_code(output_box, status):
    global last_error, current_file

    if not current_file:
        status.set("❌ 请先选文件")
        return

    result = safe_run([sys.executable, os.path.abspath(current_file)])

    if result is None:
        status.set("❌ Python执行失败")
        return

    output = result.stdout + result.stderr
    output_box.delete("1.0", tk.END)
    output_box.insert(tk.END, output)

    if result.returncode != 0:
        last_error = output
        status.set("🔴 运行出错")
    else:
        last_error = ""
        status.set("🟢 运行成功")

# ===== 修Bug =====
def fix_bug(editor, diff_box, status):
    global cached_code, last_error

    if not last_error:
        status.set("❌ 没有报错")
        return

    code = editor.get("1.0", tk.END)

    prompt = f"""
修复错误：

错误：
{last_error}

代码：
{code}

输出修复后的完整代码
"""

    new_code = call_model(prompt)

    cached_code = new_code

    diff_box.delete("1.0", tk.END)
    diff_box.insert(tk.END, get_diff(code, new_code))

    status.set("🟡 已生成修复")

# ===== 应用修改 =====
def apply_change(editor, status):
    global cached_code

    if not cached_code:
        status.set("❌ 没有修改")
        return

    if check_git():
        safe_run(["git", "add", "."])
        safe_run(["git", "commit", "-m", "AI修改备份"])

    editor.delete("1.0", tk.END)
    editor.insert(tk.END, cached_code)

    save_file(cached_code)

    status.set("🟢 已应用修改")

# ===== Git回滚 =====
def rollback(status):
    if not check_git():
        status.set("❌ Git不可用")
        return

    safe_run(["git", "reset", "--hard", "HEAD~1"])
    status.set("⏪ 已回滚")

# ===== 项目理解 =====
def analyze(status, output_box):
    if not check_ollama():
        status.set("❌ Ollama未启动")
        return

    text = ""
    for root, _, files in os.walk("."):
        for f in files:
            if f.endswith(".py"):
                try:
                    with open(os.path.join(root, f), encoding="utf-8") as file:
                        text += file.read()[:1000]
                except:
                    pass

    result = call_model("分析项目：\n" + text)

    output_box.delete("1.0", tk.END)
    output_box.insert(tk.END, result)

    status.set("🧠 分析完成")


# ===== UI =====
init_git()

root = tk.Tk()
root.title("🔥 Ultimate AI Agent IDE")
root.geometry("1200x700")

# 左
file_list = tk.Listbox(root, width=30)
file_list.pack(side=tk.LEFT, fill=tk.Y)

for f in list_files():
    file_list.insert(tk.END, f)

# 中
editor = scrolledtext.ScrolledText(root)
editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# 右
right = tk.Frame(root)
right.pack(side=tk.RIGHT, fill=tk.Y)

input_box = tk.Entry(right)
input_box.pack()

diff_box = scrolledtext.ScrolledText(right, height=10)
diff_box.pack()

output_box = scrolledtext.ScrolledText(right, height=10)
output_box.pack()

status = tk.StringVar()
status.set("就绪")
tk.Label(right, textvariable=status).pack()

tk.Button(right, text="AI修改",
          command=lambda: threading.Thread(
              target=run_ai,
              args=(editor, diff_box, status, input_box.get()),
              daemon=True).start()).pack()

tk.Button(right, text="运行",
          command=lambda: run_code(output_box, status)).pack()

tk.Button(right, text="修Bug",
          command=lambda: fix_bug(editor, diff_box, status)).pack()

tk.Button(right, text="应用",
          command=lambda: apply_change(editor, status)).pack()

tk.Button(right, text="回滚",
          command=lambda: rollback(status)).pack()

tk.Button(right, text="分析",
          command=lambda: threading.Thread(
              target=analyze,
              args=(status, output_box),
              daemon=True).start()).pack()

def select_file(event):
    idx = file_list.curselection()
    if idx:
        load_file(file_list.get(idx), editor)

file_list.bind("<<ListboxSelect>>", select_file)

root.mainloop()