import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    # DeepSeek（文本 + 识图同一个模型：V4.1 Flash 原生多模态，2026-09-10 上线）
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-flash")
    DEEPSEEK_VISION_MODEL = os.getenv("DEEPSEEK_VISION_MODEL", "deepseek-flash")
    # 思考模式：默认关（首字 ~0.6s）；设 1 开启（首字 1~13s，输出 token 翻数倍）
    DEEPSEEK_THINKING = os.getenv("DEEPSEEK_THINKING", "0") == "1"

    # 阿里云 DashScope（小基：推理/识图/语音合成/语音通话共用一个 key）
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
    # 聊天：qwen-flash（实测首字节 0.9s、总耗时 1.2s，陪伴质量够用，¥0.15 入/¥1.5 出）
    QWEN_CHAT_MODEL = os.getenv("QWEN_CHAT_MODEL", "qwen-flash")
    # 评价题目/题集：qwen-plus（四维度分析需要推理质量，非延迟敏感）
    QWEN_REASON_MODEL = os.getenv("QWEN_REASON_MODEL", "qwen-plus")
    # 视觉（小基识图 / 视频抽帧）：qwen3.8-flash（2026-10-11 由 qwen3-vl-flash 换过来）
    # qwen3-vl-flash 已于 2026-10-10 00:00 下线（官方《部分历史主线模型下线通知》），
    # 留旧值会让 /xiaoji/vision 与 /xiaoji/video-analyze 全部 404。
    # 候选实跑对比见开发仓库 _devtools/bench_vision_model.py：
    #   qwen3.8-flash 真实截图核对 4/4、题干逐字转写 12/12、2.5s   ← 选中
    #   qwen3.7-flash 3/4、12/12  ｜  qwen3-vl-plus 2/4、5/12、最慢
    QWEN_VISION_MODEL = os.getenv("QWEN_VISION_MODEL", "qwen3.8-flash")
    # 视频库讲解脚本：qwen-flash（2026-10-11 由 qwen-turbo 换过来）
    # qwen-turbo 已不在官方模型清单（快照版 404/403），且实测初稿 0/5 合格：
    # 口播 189~226 字（闸门要 240）、只给 4~5 镜，修补后仍 2/5 出不了片。
    # qwen-flash 初稿 5/5、一次调用到位、均耗 9.9s。
    QWEN_VIDEO_MODEL = os.getenv("QWEN_VIDEO_MODEL", "qwen-flash")
    # 视频库生成并发生成数（1 = 串行，压低 API 并发与限流风险；env 可调）
    VIDEO_WORKERS = int(os.getenv("VIDEO_WORKERS", "1"))
    # 视频库 TTS：千问(小基同款声色)；语速 6 档（7 档用户实测偏快，2026-09-04 收回一档）
    VIDEO_TTS_SPEED = int(os.getenv("VIDEO_TTS_SPEED", "5"))   # 2026-09-05 用户定调：6 档仍偏快 → 5 档

    # Redis
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

    # ===== 异步任务队列（Redis）=====
    # 视频生成、批量 AI 分析这类几十秒到几分钟的活走队列，不要在请求里同步跑，
    # 也不要用裸 asyncio.create_task（进程重启就丢、多 worker 不协调）。
    # 服务器上需要跑一个 Redis，以及一个 `python worker.py` 常驻进程。
    REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
    # 队列连不上时是否退回进程内执行。**默认 False** ——
    # 静默降级正是这个项目反复吃亏的地方：看起来在跑，其实没进队列，
    # 重启就丢且没人知道。要退回必须显式打开，并且日志里会有 ERROR。
    TASK_QUEUE_FALLBACK_INLINE = os.getenv("TASK_QUEUE_FALLBACK_INLINE", "false").lower() == "true"

    # 火山引擎（豆包）
    VOLC_ACCESS_KEY = os.getenv("VOLC_ACCESS_KEY")
    VOLC_SECRET_KEY = os.getenv("VOLC_SECRET_KEY")
    VOLC_ROLE_ENDPOINT_ID = os.getenv("VOLC_ROLE_ENDPOINT_ID")
    VOLC_VISION_ENDPOINT_ID = os.getenv("VOLC_VISION_ENDPOINT_ID")
    VOLC_API_KEY = os.getenv("VOLC_API_KEY")
    ARK_API_KEY = os.getenv("ARK_API_KEY")

    # 邮箱配置
    EMAIL_HOST = os.getenv("EMAIL_HOST")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

    # ===== 科大讯飞语音 =====
    XUNFEI_APPID = os.getenv("XUNFEI_APPID")
    XUNFEI_API_KEY = os.getenv("XUNFEI_API_KEY")
    XUNFEI_API_SECRET = os.getenv("XUNFEI_API_SECRET")

    # ===== 微信公众平台测试号（网页扫码登录）=====
    # 前往 https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login 扫码获取
    WECHAT_WEB_APPID = os.getenv("WECHAT_WEB_APPID", "")
    WECHAT_WEB_SECRET = os.getenv("WECHAT_WEB_SECRET", "")
    # 微信小程序
    WECHAT_MP_APPID = os.getenv("WECHAT_MP_APPID", "wx6db1f1a6e3f3969c")
    WECHAT_MP_SECRET = os.getenv("WECHAT_MP_SECRET", "")

    # ===== 自签 JWT（微信登录用，不依赖 Supabase）=====
    JWT_SECRET = os.getenv("JWT_SECRET", "jizhi-dev-secret-change-in-production")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "720"))  # 30 天

    # 前端地址（OAuth 回调后跳转用）— 公网部署默认值，本地开发用 .env 覆盖
    FRONTEND_URL = os.getenv("FRONTEND_URL", "https://jizhi-learn.com")
    # 后端外网地址（微信 OAuth 回调用）
    BACKEND_EXTERNAL_URL = os.getenv("BACKEND_EXTERNAL_URL", "https://api.jizhi-learn.com")

settings = Settings()