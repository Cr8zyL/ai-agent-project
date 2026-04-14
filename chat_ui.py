import requests
import gradio as gr
import json

def chat_with_model(message, history):
    url = "http://127.0.0.1:11434/api/chat"

    # 把历史对话转换成 Ollama 格式
    messages = []

    for user, bot in history:
        messages.append({"role": "user", "content": user})
        messages.append({"role": "assistant", "content": bot})

    messages.append({"role": "user", "content": message})

    data = {
        "model": "qwen3:8b",
        "messages": messages,
        "stream": True
    }

    response = requests.post(url, json=data, stream=True)

    full_response = ""

    # 流式输出
    for line in response.iter_lines():
        if line:
            chunk = line.decode("utf-8")
            try:
                json_data = json.loads(chunk)
                content = json_data.get("message", {}).get("content", "")
                full_response += content
                yield full_response
            except:
                continue


demo = gr.ChatInterface(
    fn=chat_with_model,
    title="本地AI聊天（进阶版）",
    description="支持上下文 + 流式输出（类似ChatGPT）"
)

demo.launch()