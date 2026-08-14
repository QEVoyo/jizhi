from fastapi import APIRouter, HTTPException, Query, Body, Path, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from config import settings
import httpx
import uuid
import re
from utils.email import send_report_email
from collections import defaultdict
from utils.notification import create_notification
import json
from utils.sensitive_words import check_content_safety
from utils.auth_middleware import get_current_user, verify_user_match

router = APIRouter(prefix="/community", tags=["社区"])


# ========== 模型定义 ==========
class PostCreate(BaseModel):
    content: str
    title: Optional[str] = None
    topic: Optional[str] = None
    tags: Optional[str] = None
    images: Optional[str] = None


class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[str] = None


class ReportCreate(BaseModel):
    target_type: str
    target_id: str
    reason: str


class PrivateMessageCreate(BaseModel):
    receiver_id: str
    message_type: str = "text"
    content: str
    media_url: Optional[str] = None
    question_id: Optional[str] = None
    question_set_id: Optional[str] = None
    question_data: Optional[dict] = None  # ✅ 新增这一行


class QuestionSetShareCreate(BaseModel):
    set_id: str
    receiver_id: str


class XiaojiMessage(BaseModel):
    content: str
