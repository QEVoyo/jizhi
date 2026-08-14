"""社区模块 - 组合所有子路由"""
from fastapi import APIRouter
from .posts import router as posts_router
from .friends import router as friends_router
from .messages import router as messages_router
from .xiaoji import router as xiaoji_router
from .notifications import router as notifications_router

router = APIRouter(tags=["社区"])
router.include_router(posts_router)
router.include_router(friends_router)
router.include_router(messages_router)
router.include_router(xiaoji_router)
router.include_router(notifications_router)
