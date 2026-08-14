import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    # DeepSeek
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    # 阿里云 DashScope
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

    # Redis
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

    # 火山引擎（豆包）
    VOLC_ACCESS_KEY = os.getenv("VOLC_ACCESS_KEY")
    VOLC_SECRET_KEY = os.getenv("VOLC_SECRET_KEY")
    VOLC_ROLE_ENDPOINT_ID = os.getenv("VOLC_ROLE_ENDPOINT_ID")
    VOLC_API_KEY = os.getenv("VOLC_API_KEY")
    ARK_API_KEY = os.getenv("ARK_API_KEY")
    VOLC_VISION_ENDPOINT_ID = os.getenv("VOLC_VISION_ENDPOINT_ID")

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
    # 后端外网地址（微信 OAuth 回调用，手机扫码后微信浏览器要能访问到）
    BACKEND_EXTERNAL_URL = os.getenv("BACKEND_EXTERNAL_URL", "https://api.jizhi-learn.com")

settings = Settings()