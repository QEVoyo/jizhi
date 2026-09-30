"""桌面版安装包下载。

安装包放在 `backend/static/downloads/` 下，跟着 backend 一起打包部署 ——
不需要额外对象存储或 CDN。

对外只暴露一个**稳定地址**：

    GET /download/JIZHI-setup.exe    永远指向目录里最新的那个 exe
    GET /download/latest             返回版本/大小等元信息（落地页可用它显示"最新版 1.37MB"）

这样落地页的下载链接不随版本号变动 —— 换版本只要把新 exe 丢进目录，
旧的一删即可，链接一个字都不用改。
"""
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/download", tags=["下载"])

DOWNLOAD_DIR = Path(__file__).resolve().parent.parent / "static" / "downloads"


def _latest_installer() -> Optional[Path]:
    """目录里最新的一个 .exe（按修改时间）。没有则返回 None。"""
    if not DOWNLOAD_DIR.is_dir():
        return None
    files = [p for p in DOWNLOAD_DIR.glob("*.exe") if p.is_file()]
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


# 同时支持 HEAD：FastAPI 的 @router.get 不会自动带上 HEAD，
# 而部分下载工具/CDN 探测会先发 HEAD，405 可能被误判成「文件不存在」。
@router.api_route("/JIZHI-setup.exe", methods=["GET", "HEAD"])
async def download_installer():
    installer = _latest_installer()
    if installer is None:
        # 明确报「还没上传」，别让前端/用户以为是自己网络的问题
        raise HTTPException(status_code=404, detail="安装包尚未上传")
    return FileResponse(
        installer,
        media_type="application/octet-stream",
        filename=installer.name,
    )


def _parse_version(filename: str) -> Optional[str]:
    """从安装包文件名里取版本号。

    Tauri 打包出的名字形如 `JIZHI_0.1.0_x64-setup.exe` —— **版本号只存在于文件名里**，
    目录里没有别的元数据文件。所以桌面端的「检查更新」必须靠它。
    取不到就返回 None，让调用方明确知道「有包但读不出版本」，
    而不是拿一个瞎编的版本去比对（那会导致永远不提示更新，或永远提示）。
    """
    m = re.search(r"_(\d+\.\d+(?:\.\d+)*)_", filename)
    return m.group(1) if m else None


@router.get("/latest")
async def latest_info():
    installer = _latest_installer()
    if installer is None:
        return {"available": False}
    size = installer.stat().st_size
    return {
        "available": True,
        "filename": installer.name,
        # 桌面端拿它和自己的版本比；落地页也可以显示「最新版 v0.1.0」
        "version": _parse_version(installer.name),
        "size": size,
        "size_mb": round(size / 1048576, 2),
        "url": "/download/JIZHI-setup.exe",
    }
