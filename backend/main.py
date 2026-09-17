from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, chat, tools, questions, career
import sys
from routers import community
from routers import qa
from pathlib import Path
from routers import feedback
from routers import profile_card
from routers import evaluation
from routers import learning_plan
from routers import video
from routers import video_social
from routers import xiaoji
from routers import subject_plan
from routers import exam_papers
from routers import admin
from routers import admin_video
from routers import agent_center
from routers import vocab
from agents.tuning import start_background_tuning
from services.video_gen import start_video_worker
sys.path.insert(0, str(Path(__file__).resolve().parent))


@asynccontextmanager
async def lifespan(app):
    # 磨合规则引擎：每日对近 14 天活跃用户自动评估（参数自动托管）
    tuning_task = start_background_tuning()
    # 视频库生成 worker：知识点级模板视频后台排产（2026-09-04）
    video_task = start_video_worker()
    yield
    tuning_task.cancel()
    video_task.cancel()


app = FastAPI(title="基智学习助手 API", version="1.0.0", lifespan=lifespan)

# ====== CORS 配置 - 允许所有前端域名 ======
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://jizhi-learn.com",
        "https://www.jizhi-learn.com",
        "https://frontend-ebon-gamma-45.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",  # 加上 5174 以防你用了其他端口
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(tools.router)
app.include_router(questions.router)
app.include_router(career.router)
app.include_router(video.router)
app.include_router(video_social.router)
app.include_router(community.router)
app.include_router(profile_card.router)
app.include_router(feedback.router)
app.include_router(qa.router)
app.include_router(evaluation.router)
app.include_router(learning_plan.router)
app.include_router(xiaoji.router)
app.include_router(subject_plan.router)
app.include_router(exam_papers.router)
app.include_router(admin.router)
app.include_router(admin_video.router)
app.include_router(agent_center.router, prefix="/agent-center")
app.include_router(vocab.router)

@app.get("/")
def root():
    return {"message": "基智学习助手后端已启动"}

@app.get("/health")
def health():
    return {"status": "ok"}
