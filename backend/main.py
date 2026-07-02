from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, chat, tools, questions, career

app = FastAPI(title="基智学习助手 API", version="1.0.0")

# ====== CORS 配置 - 允许前端访问 ======
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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

@app.get("/")
def root():
    return {"message": "基智学习助手后端已启动"}

@app.get("/health")
def health():
    return {"status": "ok"}