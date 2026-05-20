import dashscope
import streamlit as st
import os
import tempfile


def get_api_key():
    try:
        return st.secrets["DASHSCOPE_API_KEY"]
    except:
        from dotenv import load_dotenv
        load_dotenv()
        return os.getenv("DASHSCOPE_API_KEY")


dashscope.api_key = get_api_key()


def analyze_image(image_bytes, prompt="请描述这张图片的内容"):
    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            tmp_file.write(image_bytes)
            tmp_path = tmp_file.name

        from dashscope import MultiModalConversation
        messages = [{"role": "user", "content": [{"image": f"file://{tmp_path}"}, {"text": prompt}]}]
        response = MultiModalConversation.call(model="qwen-vl-plus", messages=messages)
        os.unlink(tmp_path)

        if response.status_code == 200:
            return response.output.choices[0].message.content[0]["text"]
        else:
            return f"图片分析失败: {response.message}"
    except Exception as e:
        return f"调用失败: {str(e)}"