from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, chat  # 一行导入两个

app = FastAPI(title="基智学习助手 API", version="1.0.0")
from routers import auth, chat, tools  # 添加 tools

# 允许前端调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:8502"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由（每个只写一次）
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(tools.router)  # 添加这行
@app.get("/")
def root():
    return {"message": "基智学习助手后端已启动"}

@app.get("/health")
def health():
    return {"status": "ok"}