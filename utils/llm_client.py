import os
import streamlit as st
from openai import OpenAI

def get_api_key():
    try:
        return st.secrets["DEEPSEEK_API_KEY"]
    except:
        from dotenv import load_dotenv
        load_dotenv()
        return os.getenv("DEEPSEEK_API_KEY")

def get_base_url():
    try:
        return st.secrets.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    except:
        return os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

def call_llm(messages, temperature=0.7):
    """非流式调用，用于plan/evaluate等一次性场景"""
    client = OpenAI(api_key=get_api_key(), base_url=get_base_url())
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=temperature,
        stream=False
    )
    return response.choices[0].message.content

def call_llm_stream(messages, temperature=0.7):
    """流式调用，用于generate/chat等对话场景"""
    client = OpenAI(api_key=get_api_key(), base_url=get_base_url())
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=temperature,
        stream=True
    )
    return response