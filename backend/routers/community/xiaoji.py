from fastapi import APIRouter, HTTPException, Query, Body, Path, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from config import settings
import httpx, uuid, re, json
from collections import defaultdict
from utils.volc_client import VolcClient
from utils.xunfei_client import XunfeiClient
from agents.llm_client import call_llm, call_llm_stream
from utils.auth_middleware import get_current_user, verify_user_match
from services.supabase import get_supabase_headers
from logging_config import logger
from .models import *
import base64
from fastapi.responses import StreamingResponse
router = APIRouter(prefix="/community", tags=["社区-小基"])
# ============================================================
# 小基（AI好友）相关接口
# ============================================================

@router.get("/xiaoji/messages")
async def get_xiaoji_messages(user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """获取用户与小基的聊天记录"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages?user_id=eq.{user_id}&order=created_at.asc"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)
        if res.status_code == 200:
            messages = res.json()
            for msg in messages:
                if msg.get("role") == "user":
                    msg["sender_id"] = msg.get("user_id")
                else:
                    msg["sender_id"] = "xiaoji"
            return {"messages": messages}
        return {"messages": []}


@router.post("/xiaoji/chat")
async def send_xiaoji_message(
        user_id: str = Query(...),
        data: dict = Body(...),
        current_user: str = Depends(get_current_user)
):
    """与小基聊天（调用豆包角色模型）"""
    verify_user_match(user_id, current_user)

    user_content = data.get("content", "")
    if not user_content:
        raise HTTPException(status_code=400, detail="内容不能为空")

    headers = get_supabase_headers()

    async with httpx.AsyncClient(timeout=30.0) as client:
        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}"
        profile_res = await client.get(profile_url, headers=headers)
        profile = profile_res.json()[0] if profile_res.json() else {}
        nickname = profile.get("nickname", "同学")

    system_prompt = f"""你是一个温暖、幽默、有耐心的AI学习伙伴，名字叫「小基」。

你的性格特点：
- 温暖友善，像朋友一样聊天
- 偶尔幽默，会用一些轻松的语气词
- 耐心倾听，不会打断用户
- 擅长鼓励和引导，不直接给答案

你的角色定位：
- 你是用户「{nickname}」的学习伙伴
- 你会关心用户的学习状态和情绪
- 你会用轻松自然的方式聊学习

说话风格：
- 自然口语化，不用官方腔
- 适当使用「哈哈」「嗯嗯」「好呀」等语气词
- 不要用 Markdown 格式

记住：你是朋友，不是老师。你的目标是让学习变得有趣。
"""

    async with httpx.AsyncClient(timeout=30.0) as client:
        history_url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages?user_id=eq.{user_id}&order=created_at.desc&limit=10"
        history_res = await client.get(history_url, headers=headers)
        history = history_res.json() if history_res.status_code == 200 else []
        history.reverse()

    messages = [
        {"role": "system", "content": system_prompt}
    ]
    for msg in history:
        messages.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", "")
        })
    messages.append({"role": "user", "content": user_content})

    volc_client = VolcClient()
    response = volc_client.chat(messages, temperature=0.8)

    async with httpx.AsyncClient(timeout=30.0) as client:
        user_msg = {"user_id": user_id, "role": "user", "content": user_content}
        user_res = await client.post(f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages", headers=headers, json=user_msg)
        logger.info(f"=== 保存用户消息状态: {user_res.status_code} ===")

        assistant_msg = {"user_id": user_id, "role": "assistant", "content": response}
        assistant_res = await client.post(f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages", headers=headers,
                                          json=assistant_msg)
        logger.info(f"=== 保存助手消息状态: {assistant_res.status_code} ===")

    return {"reply": response}


@router.post("/xiaoji/vision")
async def xiaoji_vision(
        user_id: str = Query(...),
        data: dict = Body(...),
        current_user: str = Depends(get_current_user)
):
    """小基图片理解"""
    verify_user_match(user_id, current_user)

    image_url = data.get("image_url", "")
    question = data.get("question", "这张图片里有什么？")

    if not image_url:
        raise HTTPException(status_code=400, detail="请提供图片")

    headers = get_supabase_headers()

    user_msg = {
        "user_id": user_id,
        "role": "user",
        "content": question or "[图片]",
        "image_url": image_url
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        await client.post(
            f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages",
            headers=headers,
            json=user_msg
        )

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": question or "这张图片里有什么？"},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }
    ]

    volc_client = VolcClient()
    response = volc_client.chat(messages, temperature=0.8)

    assistant_msg = {
        "user_id": user_id,
        "role": "assistant",
        "content": response

    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        await client.post(
            f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages",
            headers=headers,
            json=assistant_msg
        )

    return {"reply": response}


@router.get("/xiaoji/config")
async def get_xiaoji_config(user_id: str = Query(...), current_user: str = Depends(get_current_user)):
    """获取小基配置"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()
    url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_config?user_id=eq.{user_id}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(url, headers=headers)
        if res.status_code == 200 and res.json():
            return res.json()[0]
        return {
            "user_id": user_id,
            "name": "小基",
            "personality": "温暖学伴",
            "voice_enabled": True,
            "proactive_enabled": True
        }


@router.put("/xiaoji/config")
async def update_xiaoji_config(user_id: str = Query(...), data: dict = Body(...), current_user: str = Depends(get_current_user)):
    """更新小基配置"""
    verify_user_match(user_id, current_user)
    headers = get_supabase_headers()

    check_url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_config?user_id=eq.{user_id}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        check_res = await client.get(check_url, headers=headers)

        if check_res.status_code == 200 and check_res.json():
            url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_config?user_id=eq.{user_id}"
            res = await client.patch(url, headers=headers, json=data)
        else:
            data["user_id"] = user_id
            url = f"{settings.SUPABASE_URL}/rest/v1/xiaoji_config"
            res = await client.post(url, headers=headers, json=data)

        if res.status_code not in [200, 201, 204]:
            raise HTTPException(status_code=400, detail=f"更新失败: {res.text}")
        return {"success": True, "message": "更新成功"}

@router.post("/xiaoji/tts")
async def xiaoji_tts(data: dict = Body(...)):
    """文字转语音"""

    client = XunfeiClient()
    text = data.get("text", "")
    speed = data.get("speed", 5)
    volume = data.get("volume", 5)
    voice_name = data.get("voice_name", "xiaoyan")

    if not text:
        raise HTTPException(status_code=400, detail="text 不能为空")

    audio_data = client.get_tts_audio(text, speed, volume, 5, voice_name)

    if not audio_data:
        raise HTTPException(status_code=500, detail="语音合成失败")

    return {
        "success": True,
        "audio_base64": base64.b64encode(audio_data).decode("utf-8"),
        "format": "wav"
    }


@router.post("/xiaoji/asr")
async def xiaoji_asr(data: dict = Body(...)):
    """语音转文字 - 使用讯飞 ASR"""

    client = XunfeiClient()
    audio_base64 = data.get("audio_base64", "")
    audio_format = data.get("format", "wav")

    if not audio_base64:
        raise HTTPException(status_code=400, detail="audio_base64 不能为空")

    try:
        audio_bytes = base64.b64decode(audio_base64)
        result = client.speech_to_text(audio_bytes, audio_format)

        if not result:
            raise HTTPException(status_code=500, detail="语音识别失败")

        return {"success": True, "text": result}
    except Exception as e:
        logger.info(f"ASR 错误: {e}")
        raise HTTPException(status_code=500, detail=f"ASR 错误: {str(e)}")

# ============================================================
# 小基 - 题目评价接口
# ============================================================

@router.post("/xiaoji/evaluate-question")
async def xiaoji_evaluate_question(
    user_id: str = Query(...),
    data: dict = Body(...),
    current_user: str = Depends(get_current_user)
):
    """小基评价用户发送的题目 - 4维度输出"""
    verify_user_match(user_id, current_user)
    from agents.llm_client import call_llm

    question = data.get("question", {})
    if not question:
        raise HTTPException(status_code=400, detail="请提供题目")

    # ===== 提取题目信息 =====
    question_title = question.get("title", "")
    question_content = question.get("question_content", "") or question.get("title", "")
    question_type = question.get("question_type", "未知")
    difficulty = question.get("difficulty_score", 5)
    correct_answer = question.get("answer", "未提供")
    explanation = question.get("explanation", "")

    # ===== 获取用户昵称 =====
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}&select=nickname"
        profile_res = await client.get(profile_url, headers=headers)
        nickname = profile_res.json()[0].get("nickname", "同学") if profile_res.json() else "同学"

    # ===== 4维度 Prompt =====
    eval_prompt = f"""你是一位资深学习导师，请从4个维度评价用户发送的题目。

【题目信息】
标题：{question_title}
内容：{question_content}
题型：{question_type}
难度：{difficulty}
正确答案：{correct_answer}
解析：{explanation}

请按以下4个维度输出，每个维度用 ## 标题分隔：

## 📖 理解题目
- 这道题在考什么知识点？
- 题目的核心难点是什么？

## 📊 评估
- 这道题对用户来说难度如何？
- 用户可能在哪一步卡住？

## 💡 解析思路
- 给出解题思路（不要直接给答案）
- 关键步骤和提示

## 📚 学习规划
- 如果用户做对了，接下来应该学什么？
- 如果用户没做对，应该补什么知识点？
- 给出具体的学习建议

请用温暖、鼓励的语气，像朋友一样自然。不要直接给答案，要引导用户思考。
"""

    messages = [
        {"role": "system", "content": f"你是小基，一个温暖幽默的学习伙伴。用户叫「{nickname}」。"},
        {"role": "user", "content": eval_prompt}
    ]

    try:
        response = call_llm(messages, temperature=0.7)

        # ===== 保存到数据库 =====
        headers = {
            "apikey": settings.SUPABASE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            assistant_msg = {
                "user_id": user_id,
                "role": "assistant",
                "content": response,
                "is_evaluation": True
            }
            await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages",
                headers=headers,
                json=assistant_msg
            )

        return {"reply": response}

    except Exception as e:
        logger.info(f"评价失败: {e}")
        raise HTTPException(status_code=500, detail=f"评价失败: {str(e)}")


@router.post("/xiaoji/evaluate-set")
async def xiaoji_evaluate_set(
    user_id: str = Query(...),
    data: dict = Body(...),
    current_user: str = Depends(get_current_user)
):
    """
    小基评价用户发送的整个题集
    """
    verify_user_match(user_id, current_user)
    from agents.llm_client import call_llm

    set_data = data.get("set", {})
    questions = data.get("questions", [])

    if not set_data or not questions:
        raise HTTPException(status_code=400, detail="请提供题集数据")

    # 获取掌握度
    headers = get_supabase_headers()
    async with httpx.AsyncClient(timeout=30.0) as client:
        mastery_url = f"{settings.SUPABASE_URL}/rest/v1/questions?user_id=eq.{user_id}&select=normalized_topic,mastery_score"
        mastery_res = await client.get(mastery_url, headers=headers)
        qs = mastery_res.json() if mastery_res.status_code == 200 else []
        topic_mastery = {}
        for q in qs:
            topic = q.get("normalized_topic") or q.get("topic") or "未分类"
            if topic not in topic_mastery:
                topic_mastery[topic] = {"sum": 0, "count": 0}
            topic_mastery[topic]["sum"] += q.get("mastery_score", 0)
            topic_mastery[topic]["count"] += 1
        mastery_summary = [f"{t}: {round(d['sum']/d['count'])}%" for t, d in topic_mastery.items()]
        mastery_text = "用户的知识点掌握度：\n" + "\n".join(mastery_summary) if mastery_summary else "暂无掌握度数据"

    # 构建题集评价 Prompt
    set_name = set_data.get("name", "未命名题集")
    question_count = len(questions)

    eval_prompt = f"""用户发送了一个题集「{set_name}」，包含 {question_count} 道题目。

【用户掌握度数据】
{mastery_text}

【题集题目列表】
{json.dumps([{
    "title": q.get("title", ""),
    "type": q.get("question_type", ""),
    "difficulty": q.get("difficulty_score", 5)
} for q in questions], ensure_ascii=False, indent=2)}

请从以下几个维度评价这个题集：
1. 这个题集的整体难度和主题是什么
2. 用户当前的掌握度与这个题集的匹配度如何
3. 哪些题目用户可能会觉得困难
4. 给出整体鼓励和学习建议
5. 如果题集难度适中，夸夸用户选得好
6. 如果题集偏难，告诉用户不用着急

用温暖、鼓励的语气回复。"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}&select=nickname"
            profile_res = await client.get(profile_url, headers=headers)
            nickname = profile_res.json()[0].get("nickname", "同学") if profile_res.json() else "同学"

        messages = [
            {"role": "system", "content": f"你是小基，一个温暖幽默的学习伙伴。用户叫「{nickname}」。"},
            {"role": "user", "content": eval_prompt}
        ]

        response = call_llm(messages, temperature=0.7)

        # 保存
        assistant_msg = {
            "user_id": user_id,
            "role": "assistant",
            "content": response,
            "is_evaluation": True
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages",
                headers=headers,
                json=assistant_msg
            )

        return {"reply": response}

    except Exception as e:
        logger.info(f"评价题集失败: {e}")
        raise HTTPException(status_code=500, detail=f"评价失败: {str(e)}")



@router.post("/xiaoji/evaluate-question-stream")
async def xiaoji_evaluate_question_stream(
    user_id: str = Query(...),
    data: dict = Body(...),
    current_user: str = Depends(get_current_user)
):
    """流式评价题目 - 4个智能体依次输出"""
    verify_user_match(user_id, current_user)
    from agents.llm_client import call_llm_stream

    question = data.get("question", {})
    if not question:
        raise HTTPException(status_code=400, detail="请提供题目")

    question_title = question.get("title", "")
    question_content = question.get("question_content", "") or question.get("title", "")
    question_type = question.get("question_type", "未知")
    difficulty = question.get("difficulty_score", 5)
    correct_answer = question.get("answer", "未提供")
    explanation = question.get("explanation", "")

    eval_prompt = f"""你是一位资深学习导师，请从4个维度评价用户发送的题目。

【题目信息】
标题：{question_title}
内容：{question_content}
题型：{question_type}
难度：{difficulty}
正确答案：{correct_answer}
解析：{explanation}

请按以下4个维度输出，每个维度用 ## 标题分隔：

## 📖 理解题目
- 这道题在考什么知识点？
- 题目的核心难点是什么？

## 📊 评估
- 这道题对用户来说难度如何？
- 用户可能在哪一步卡住？

## 💡 解析思路
- 给出解题思路（不要直接给答案）
- 关键步骤和提示

## 📚 学习规划
- 如果用户做对了，接下来应该学什么？
- 如果用户没做对，应该补什么知识点？

请用温暖、鼓励的语气，像朋友一样自然。不要直接给答案，要引导用户思考。
"""

    # 获取用户昵称
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        profile_url = f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}&select=nickname"
        profile_res = await client.get(profile_url, headers=headers)
        nickname = profile_res.json()[0].get("nickname", "同学") if profile_res.json() else "同学"

    messages = [
        {"role": "system", "content": f"你是小基，一个温暖幽默的学习伙伴。用户叫「{nickname}」。"},
        {"role": "user", "content": eval_prompt}
    ]

    stream = call_llm_stream(messages, temperature=0.7)

    async def generate():
        full_content = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_content += content
                yield content

        # 保存到数据库
        headers = {
            "apikey": settings.SUPABASE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            assistant_msg = {
                "user_id": user_id,
                "role": "assistant",
                "content": full_content,
                "is_evaluation": True
            }
            await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/xiaoji_messages",
                headers=headers,
                json=assistant_msg
            )

    return StreamingResponse(generate(), media_type="text/plain")
