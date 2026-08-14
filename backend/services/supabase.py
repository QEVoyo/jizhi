"""
Supabase 服务层 - 封装所有 Supabase REST API 调用
消除各路由文件中重复的 headers 构造、URL 拼接和错误处理
"""
import httpx
from typing import Optional, Dict, Any, List
from config import settings


class SupabaseService:
    """Supabase REST API 客户端"""

    def __init__(self):
        self._base_url = settings.SUPABASE_URL
        self._anon_key = settings.SUPABASE_KEY
        self._service_key = settings.SUPABASE_SERVICE_ROLE_KEY

    # ============ Headers ============

    @property
    def headers(self) -> Dict[str, str]:
        """标准 headers（匿名 key）"""
        return {
            "apikey": self._anon_key,
            "Authorization": f"Bearer {self._anon_key}",
            "Content-Type": "application/json"
        }

    @property
    def service_headers(self) -> Dict[str, str]:
        """Service Role headers（最高权限，绕过 RLS）"""
        return {
            "apikey": self._anon_key,
            "Authorization": f"Bearer {self._service_key}",
            "Content-Type": "application/json"
        }

    @property
    def storage_headers(self) -> Dict[str, str]:
        """Storage 上传专用 headers"""
        return {
            "apikey": self._anon_key,
            "Authorization": f"Bearer {self._anon_key}",
            "Content-Type": "image/png"
        }

    def auth_headers(self, token: str) -> Dict[str, str]:
        """用户 token headers"""
        return {
            "apikey": self._anon_key,
            "Authorization": token,
            "Content-Type": "application/json"
        }

    # ============ REST 方法 ============

    def _url(self, table: str) -> str:
        return f"{self._base_url}/rest/v1/{table}"

    def _storage_url(self, path: str) -> str:
        return f"{self._base_url}/storage/v1/object/{path}"

    async def _request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        timeout: float = 30.0,
        **kwargs
    ) -> httpx.Response:
        async with httpx.AsyncClient(timeout=timeout) as client:
            return await client.request(method, url, headers=headers, **kwargs)

    # ============ CRUD 操作 ============

    async def select(
        self,
        table: str,
        *,
        eq: Optional[Dict[str, Any]] = None,
        select: str = "*",
        order: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        use_service_role: bool = False,
    ) -> httpx.Response:
        """SELECT 查询"""
        url = f"{self._url(table)}?select={select}"
        if eq:
            for col, val in eq.items():
                url += f"&{col}=eq.{val}"
        if order:
            url += f"&order={order}"
        if limit is not None:
            url += f"&limit={limit}"
        if offset is not None:
            url += f"&offset={offset}"

        h = self.service_headers if use_service_role else self.headers
        return await self._request("GET", url, h, timeout=60.0)

    async def insert(
        self,
        table: str,
        data: Dict[str, Any],
        *,
        use_service_role: bool = False,
    ) -> httpx.Response:
        """INSERT 操作"""
        h = self.service_headers if use_service_role else self.headers
        return await self._request("POST", self._url(table), h, json=data)

    async def update(
        self,
        table: str,
        *,
        eq: Dict[str, Any],
        data: Dict[str, Any],
        use_service_role: bool = False,
    ) -> httpx.Response:
        """UPDATE 操作（通过 eq 条件定位）"""
        url = self._url(table)
        params = "&".join(f"{col}=eq.{val}" for col, val in eq.items())
        url += f"?{params}"

        h = self.service_headers if use_service_role else self.headers
        return await self._request("PATCH", url, h, json=data)

    async def delete(
        self,
        table: str,
        *,
        eq: Optional[Dict[str, Any]] = None,
        use_service_role: bool = False,
    ) -> httpx.Response:
        """DELETE 操作"""
        url = self._url(table)
        if eq:
            params = "&".join(f"{col}=eq.{val}" for col, val in eq.items())
            url += f"?{params}"

        h = self.service_headers if use_service_role else self.headers
        return await self._request("DELETE", url, h)

    async def storage_upload(self, bucket: str, file_path: str, content: bytes) -> httpx.Response:
        """文件上传到 Storage"""
        url = self._storage_url(f"{bucket}/{file_path}")
        return await self._request("POST", url, self.storage_headers, content=content)


# 全局单例
db = SupabaseService()


# ============ 兼容旧代码的函数接口 ============

def get_supabase_headers() -> Dict[str, str]:
    """向后兼容：返回标准 Supabase headers"""
    return db.headers


def get_supabase_service_headers() -> Dict[str, str]:
    """向后兼容：返回 Service Role headers"""
    return db.service_headers
