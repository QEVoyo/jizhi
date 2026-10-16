"""
Supabase 服务层 - 封装所有 Supabase REST API 调用
消除各路由文件中重复的 headers 构造、URL 拼接和错误处理
"""
import httpx
from typing import Optional, Dict, Any, List
from urllib.parse import quote
from config import settings


def ilike_term(raw: str) -> str:
    """
    把用户搜索词收拾成能安全塞进 `ilike.*X*` 的片段
    （`or=(col.ilike.*X*,...)` 这种组合条件同样适用）。

    做两件事，对应两类不同的坏法：

    1. `,` `(` `)` 替换成空格 —— 它们会破坏 `or=` 的语法。
       ⚠️ 这里**百分号编码救不了**：PostgREST 是先把整个 `or` 的值解码、
          再按这些字符切分的，所以 `%2C` 解出来照样是分隔符。
          （services/video_gen.py 早就这么处理了，这里把它推广开。）

    2. 其余字符一律 `quote()` 编码，尤其是 `%`。
       Supabase 边缘 worker 遇到非法的百分号转义会直接抛异常
       （Cloudflare Error 1101 → HTTP 500）。2026-10-15 社区搜索整个是坏的
       就是这个原因 —— 而且被 `!= 200 → 返回空列表` 吞掉，表现成"搜不到"。

    ⚠️ 返回值**不含通配符**，调用方自己用 `*` 包起来。
       不要用 `%` 当通配符 —— 那正是第 2 条要防的东西。

    ⚠️ 这个函数**只给手工拼 URL 的调用方用**（db.select 的 or_、直接
       `url += f"&col=ilike.*{...}*"`）。走 httpx `params=` 的要用
       ilike_term_params() —— 两个混用会静默搜不到，见那个函数的说明。
    """
    cleaned = raw.replace(",", " ").replace("(", " ").replace(")", " ")
    return quote(cleaned, safe="")


def ilike_term_params(raw: str) -> str:
    """
    同样是 ilike 搜索词，但用于**走 httpx `params=`** 的调用方。

    与 ilike_term() 的唯一区别：**不做 quote()**，百分号编码交给 httpx。

    为什么必须分两个函数 —— 2026-10-16 在信誉列表上踩到的：
    ilike_term() 已经把中文编成了 %E6%B5%8B%E8%AF%95，params= 里再被 httpx
    编一次就成了 %25E6%25B5%258B...，服务端拿去当字面量匹配，结果
    **搜什么都搜不到，而且还是 HTTP 200** —— 静默失败，最难查的那种。
    实测（真库 profiles）：

        走 ilike_term()        搜「测试」命中 0   搜「a%b」命中 0
        走本函数               搜「测试」命中 2   搜「a%b」命中 1

    第 1 条（`,()` 换空格）仍然保留，而且**编码救不了它**：
    PostgREST 先把整个 or 的值解码、再按这些字符切分。
    实测 `,` 不换直接 PGRST100：
        {"code":"PGRST100","details":"unexpected \"*\" expecting letter, digit..."}
    `(` `)` 更阴 —— 不报错，静默 0 命中。

    ⚠️ 同样**不含通配符**，调用方自己用 `*` 包起来。
    """
    return raw.replace(",", " ").replace("(", " ").replace(")", " ")


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
        or_: Optional[str] = None,
        in_: Optional[Dict[str, list]] = None,
        use_service_role: bool = False,
    ) -> httpx.Response:
        """SELECT 查询

        in_：批量匹配，形如 {"id": [a, b, c]} → `id=in.(a,b,c)`。
             用于"按一批 id 精确取行"，避免为了筛几十条而全表拉取。
        """
        url = f"{self._url(table)}?select={select}"
        if eq:
            for col, val in eq.items():
                url += f"&{col}=eq.{val}"
        if in_:
            for col, vals in in_.items():
                if not vals:
                    continue
                url += f"&{col}=in.({','.join(str(v) for v in vals)})"
        if or_:
            url += f"&or={or_}"
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

    async def storage_upload(
        self, bucket: str, file_path: str, content: bytes, content_type: str = "image/png",
        upsert: bool = False, use_service_role: bool = False,
    ) -> httpx.Response:
        """文件上传到 Storage（默认 png，传音频等用 content_type 覆盖）。
        upsert=True 时带 x-upsert 头允许覆盖已存在对象——但覆盖路径会碰 storage.objects
        的 RLS，anon key 会被拒（403），需同时 use_service_role=True（重合成音轨等场景）。"""
        url = self._storage_url(f"{bucket}/{file_path}")
        headers = dict(self.service_headers if use_service_role else self.storage_headers)
        headers["Content-Type"] = content_type
        if upsert:
            headers["x-upsert"] = "true"
        return await self._request("POST", url, headers, content=content)


# 全局单例
db = SupabaseService()


# ============ 兼容旧代码的函数接口 ============

def get_supabase_headers() -> Dict[str, str]:
    """向后兼容：返回标准 Supabase headers"""
    return db.headers


def get_supabase_service_headers() -> Dict[str, str]:
    """向后兼容：返回 Service Role headers"""
    return db.service_headers
