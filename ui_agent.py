import requests
import threading
import time
import tkinter as tk
from tkinter import scrolledtext

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "qwen3:8b"

# ===== 检查 Ollama 状态 =====
def check_ollama():
    try:
        requests.get("http://127.0.0.1:11434", timeout=1)
        return True
    except:
        return False

# ===== 调用模型 =====
def ask_model(prompt):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        return response.json()["response"]
    except Exception as e:
        return f"❌ 调用失败: {e}"

# ===== UI 主类 =====
class ChatUI:
    def __init__(self, root):
        self.root = root
        self.root.title("本地AI Agent（Ollama版）")
        self.root.geometry("600x500")

        # 状态标签
        self.status_label = tk.Label(root, text="检测中...", fg="orange")
        self.status_label.pack()

        # 聊天框
        self.chat_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=20)
        self.chat_box.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # 输入框
        self.entry = tk.Entry(root)
        self.entry.pack(fill=tk.X, padx=10)
        self.entry.bind("<Return>", self.send_message)

        # 发送按钮
        self.send_btn = tk.Button(root, text="发送", command=self.send_message)
        self.send_btn.pack(pady=5)

        # 启动状态检测线程
        threading.Thread(target=self.update_status, daemon=True).start()

    # ===== 更新状态灯 =====
    def update_status(self):
        while True:
            if check_ollama():
                self.status_label.config(text="🟢 模型已连接", fg="green")
            else:
                self.status_label.config(text="🔴 模型未启动", fg="red")
            time.sleep(2)

    # ===== 发送消息 =====
    def send_message(self, event=None):
        user_input = self.entry.get()
        if not user_input:
            return

        self.chat_box.insert(tk.END, f"你：{user_input}\n")
        self.entry.delete(0, tk.END)

        threading.Thread(target=self.handle_response, args=(user_input,), daemon=True).start()

    # ===== 处理回复 =====
    def handle_response(self, user_input):
        if not check_ollama():
            self.chat_box.insert(tk.END, "❌ Ollama 未启动，请先运行 ollama serve\n\n")
            return

        reply = ask_model(user_input)
        self.chat_box.insert(tk.END, f"AI：{reply}\n\n")
        self.chat_box.see(tk.END)


# ===== 启动 UI =====
if __name__ == "__main__":
    root = tk.Tk()
    app = ChatUI(root)
    root.mainloop()