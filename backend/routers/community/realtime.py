# -*- coding: utf-8 -*-
"""社区私聊 · WebSocket 实时推送（2026-10-30）

设计取舍：
  · 发消息仍然走 POST /community/message（内容安全过滤、落库、通知都在那条链路里）；
    WS 只负责「把已落库的消息推给接收方」，不重复实现发送逻辑。
  · 一个浏览器连接只订阅一个 peer 频道（?peer=<friend_id>），
    避免把别人的消息推到当前聊天框，也省掉前端过滤。
  · 鉴权与 /xiaoji/asr-ws 一致：浏览器 WS 不能自定义 Header，token 走 query。
    已知残留风险：token 会进 nginx 访问日志，与现有 WS 端点保持同一套做法。
  · 心跳用应用层 {"type":"ping"} / {"type":"pong"}，浏览器无法发协议层 ping。

⚠️ 连接表是**进程内**字典：当前 Docker 用单 worker（uvicorn 默认），所以能直接推。
   将来开多 worker / 多实例时，发消息落到 A 进程、收件人连在 B 进程就推不到 ——
   那时必须换成 Redis pub/sub（部署里已有 Redis，arq 在用）或粘性会话。
"""
import asyncio
from typing import Dict, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from logging_config import logger
from routers.xiaoji import _verify_ws_token

router = APIRouter(prefix="/community", tags=["社区-实时"])


class ChatHub:
    """user_id -> {websocket: peer_id or None}"""

    def __init__(self):
        self._conns: Dict[str, Dict[WebSocket, Optional[str]]] = {}
        self._lock = asyncio.Lock()

    async def register(self, user_id: str, ws: WebSocket, peer: Optional[str]):
        async with self._lock:
            self._conns.setdefault(user_id, {})[ws] = peer

    async def unregister(self, user_id: str, ws: WebSocket):
        async with self._lock:
            conns = self._conns.get(user_id)
            if conns is not None:
                conns.pop(ws, None)
                if not conns:
                    self._conns.pop(user_id, None)

    async def set_peer(self, user_id: str, ws: WebSocket, peer: Optional[str]):
        async with self._lock:
            self._conns.setdefault(user_id, {})[ws] = peer

    async def push(self, user_id: str, payload: dict, from_user: Optional[str] = None):
        """推给 user_id 的所有连接；带 peer 的连接只收 from_user 这个人的消息。"""
        async with self._lock:
            targets = list((self._conns.get(user_id) or {}).items())

        for ws, peer in targets:
            if peer and from_user and peer != from_user:
                continue
            try:
                # 单个慢连接不能拖住发消息接口
                await asyncio.wait_for(ws.send_json(payload), timeout=2.0)
            except Exception:
                # 对端已断开 / 写超时：清掉，避免下次再往死连接写
                await self.unregister(user_id, ws)


hub = ChatHub()


@router.websocket("/ws")
async def community_chat_ws(websocket: WebSocket):
    user_id = await _verify_ws_token(websocket.query_params.get("token") or "")
    if not user_id:
        await websocket.close(code=1008)   # policy violation
        return

    peer = (websocket.query_params.get("peer") or "").strip() or None
    await websocket.accept()
    await hub.register(user_id, websocket, peer)

    try:
        while True:
            msg = await websocket.receive_json()
            msg_type = (msg or {}).get("type")
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif msg_type == "subscribe":
                await hub.set_peer(
                    user_id, websocket,
                    (msg.get("peer") or "").strip() or None,
                )
    except WebSocketDisconnect:
        pass
    except Exception as e:                                  # noqa: BLE001
        logger.info(f"[chat-ws] 连接异常 user={user_id}: {e}")
    finally:
        await hub.unregister(user_id, websocket)
