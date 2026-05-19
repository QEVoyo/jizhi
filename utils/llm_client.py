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
    client = OpenAI(
        api_key=get_api_key(),
        base_url=get_base_url()
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=temperature
    )
    return response.choices[0].message.content