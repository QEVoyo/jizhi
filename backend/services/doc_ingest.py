"""文档解析（上传文件生成题目的第一层，2026-10-30）

只做一件事：把任意文件变成**带来源坐标的结构化块**。
不在这里判断「能不能出题」——那是 doc_profile / question_seeds 的事。

对外接口（upload_questions / doc_profile 依赖）：
    check_supported(filename, mime) -> (ok, message)
    ext_of(filename, mime) -> ".pdf" 等（带点）
    await ingest(data, filename, mime) -> IngestResult

支持：PDF（文本层/扫描件）、PPTX、DOCX、XLSX/CSV、图片、TXT/MD。
明确拒绝：视频/音频/压缩包/可执行文件。

⚠️ 依赖 pymupdf / pypdf / python-docx / python-pptx / openpyxl 已写进
   backend/requirements.txt。缺依赖时抛 UnsupportedFile 并给出可读提示。
"""
from __future__ import annotations

import asyncio
import base64
import csv
import io
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from logging_config import logger


MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_PDF_OCR_PAGES = 20
MAX_PPT_OCR_SLIDES = 5
MAX_XLSX_ROWS = 500
MAX_CHUNK_CHARS = 2400

_ANSWER_KEY_RE = re.compile(
    r"(参考答案|答案\s*[:：]|解析\s*[:：]|answer\s*key|solutions?)", re.I)
_HEADING_STYLE_RE = re.compile(r"^(heading|标题)", re.I)

_SUPPORTED = {
    "pdf", "pptx", "docx", "xlsx", "xlsm", "csv",
    "png", "jpg", "jpeg", "webp", "heic", "bmp",
    "txt", "md", "markdown",
}
_REJECT = {
    "mp4", "avi", "mov", "mkv", "flv", "wmv", "webm", "mp3", "wav", "m4a",
    "aac", "flac", "zip", "rar", "7z", "tar", "gz", "exe", "msi", "apk", "dmg",
}
_MIME_EXT = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "text/csv": "csv", "text/plain": "txt", "text/markdown": "md",
    "image/png": "png", "image/jpeg": "jpg", "image/webp": "webp",
    "image/heic": "heic", "image/bmp": "bmp",
}


class UnsupportedFile(ValueError):
    """文件类型不支持 / 解析依赖缺失 / 文件损坏。"""


@dataclass
class Chunk:
    text: str
    kind: str = "text"              # text / table / image_ocr
    answer_key: bool = False
    page: Optional[int] = None
    slide: Optional[int] = None
    sheet: str = ""
    chunk_id: str = ""
    meta: dict = field(default_factory=dict)

    def label(self) -> str:
        if self.page:
            return f"p{self.page}"
        if self.slide:
            return f"slide {self.slide}"
        if self.sheet:
            return f"sheet {self.sheet}"
        return ""

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id, "text": self.text, "kind": self.kind,
            "answer_key": self.answer_key, "page": self.page,
            "slide": self.slide, "sheet": self.sheet, "meta": self.meta,
        }


@dataclass
class IngestResult:
    filename: str
    source_type: str
    chunks: list[Chunk]
    warnings: list[str] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    def text_excerpt(self, max_chars: int = 9000) -> str:
        """给 LLM 看的节选：优先正文块，带来源标签，去答案区。"""
        parts = []
        total = 0
        for c in self.chunks:
            if c.answer_key:
                continue
            label = c.label()
            body = (c.text or "").strip()
            if not body:
                continue
            piece = f"[{label}]\n{body}" if label else body
            if total + len(piece) > max_chars:
                piece = piece[:max(0, max_chars - total)]
            if piece:
                parts.append(piece)
                total += len(piece)
            if total >= max_chars:
                break
        return "\n\n".join(parts)

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "source_type": self.source_type,
            "warnings": self.warnings,
            "meta": self.meta,
            "chunk_count": len(self.chunks),
            "chunks": [c.to_dict() for c in self.chunks],
        }


# 兼容旧名（P0 早期写的是 ParsedDoc）
ParsedDoc = IngestResult


# ============================================================
# 对外入口
# ============================================================

def ext_of(filename: str, mime: str = "") -> str:
    m = re.search(r"\.([a-zA-Z0-9]{1,10})$", filename or "")
    if m:
        return "." + m.group(1).lower()
    ext = _MIME_EXT.get((mime or "").split(";")[0].strip().lower())
    return "." + ext if ext else ""


def check_supported(filename: str, mime: str = "") -> tuple[bool, str]:
    ext = ext_of(filename, mime).lstrip(".").lower()
    if not ext:
        return False, "无法识别文件类型；请上传 PDF / PPTX / DOCX / 图片 / Excel / CSV / TXT。"
    if ext in _REJECT:
        return False, ("视频/音频/压缩包暂不支持。可以截图关键页，或上传讲义/PPT/PDF。")
    if ext not in _SUPPORTED:
        return False, (f"暂不支持 .{ext} 文件。可上传 PDF / PPTX / DOCX / 图片 / "
                       f"Excel / CSV / TXT；视频请截图关键页后再传。")
    return True, ""


async def ingest(data: bytes, filename: str, mime: str = "") -> IngestResult:
    if not data:
        raise UnsupportedFile("文件是空的")
    if len(data) > MAX_FILE_BYTES:
        raise UnsupportedFile(
            f"文件超过 {MAX_FILE_BYTES // 1024 // 1024}MB，请拆分后再传")
    ext = ext_of(filename, mime).lstrip(".").lower()
    if ext == "pdf":
        return await _parse_pdf(data, filename)
    if ext == "pptx":
        return await _parse_pptx(data, filename)
    if ext == "docx":
        return _parse_docx(data, filename)
    if ext in ("xlsx", "xlsm"):
        return _parse_xlsx(data, filename)
    if ext == "csv":
        return _parse_csv(data, filename)
    if ext in ("png", "jpg", "jpeg", "webp", "heic", "bmp"):
        return await _parse_image(data, filename, ext)
    if ext in ("txt", "md", "markdown"):
        return _parse_text(data, filename)
    raise UnsupportedFile(f"暂不支持 .{ext or '未知'} 文件")


# 兼容旧名
async def parse_bytes(data: bytes, filename: str, mime: str = "") -> IngestResult:
    return await ingest(data, filename, mime)


# ============================================================
# 内部
# ============================================================

def _is_answer_key(text: str) -> bool:
    return bool(_ANSWER_KEY_RE.search((text or "")[:300]))


def _clean(text: str) -> str:
    text = (text or "").replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _mk_chunk(idx: int, text: str, kind: str = "text", **kw) -> Optional[Chunk]:
    text = _clean(text)
    if not text:
        return None
    label = kw.get("page") or kw.get("slide") or kw.get("sheet") or idx
    return Chunk(
        text=text[:MAX_CHUNK_CHARS], kind=kind,
        answer_key=_is_answer_key(text),
        page=kw.get("page"), slide=kw.get("slide"),
        sheet=kw.get("sheet") or "", chunk_id=f"c{idx}-{label}",
        meta=kw.get("meta") or {},
    )


_OCR_PROMPT = """请把这张图片里的文字逐字转写出来，保留标题、段落、表格与公式的结构。
不要解释、不要总结、不要补全看不清的内容；看不清的字用「□」代替。
如果是讲义/教材页，保留章节标题；如果是题目页，保留题号与选项。"""


async def _ocr_image_bytes(img: bytes, mime: str = "image/jpeg") -> str:
    b64 = base64.b64encode(img).decode()
    from agents.qwen_client import call_qwen_vision
    return await asyncio.to_thread(
        call_qwen_vision, f"data:{mime};base64,{b64}",
        _OCR_PROMPT, 0.1, "doc_ocr")


# ---------------- PDF ----------------

async def _parse_pdf(data: bytes, filename: str) -> IngestResult:
    warnings: list[str] = []
    chunks: list[Chunk] = []
    meta: dict = {}
    try:
        # pymupdf 新版本把 `fitz` 作为兼容别名保留了，但官方已提示将来移除。
        # 优先用新包名，老环境回落到 fitz。
        try:
            import pymupdf as fitz
        except ImportError:  # pragma: no cover
            import fitz
    except Exception as e:  # pragma: no cover
        raise UnsupportedFile(f"服务器缺少 pymupdf，无法解析 PDF: {e}")
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as e:
        raise UnsupportedFile(f"PDF 打不开（可能损坏或加密）: {e}")

    meta["pages"] = doc.page_count
    ocr_pages = 0
    for i in range(doc.page_count):
        page = doc.load_page(i)
        text = (page.get_text("text") or "").strip()
        kind = "text"
        if len(text) < 80 and ocr_pages < MAX_PDF_OCR_PAGES:
            try:
                pix = page.get_pixmap(dpi=150)
                text = await _ocr_image_bytes(pix.tobytes("jpeg"), "image/jpeg")
                kind = "image_ocr"
                ocr_pages += 1
            except Exception as e:
                warnings.append(f"第 {i + 1} 页 OCR 失败：{str(e)[:80]}")
        if len(text) < 80:
            warnings.append(f"第 {i + 1} 页文字很少，可能识别不全")
        c = _mk_chunk(i + 1, text, kind, page=i + 1)
        if c:
            chunks.append(c)
    if ocr_pages:
        meta["ocr_pages"] = ocr_pages
        warnings.append(f"{ocr_pages} 页是扫描件，已用视觉模型识别，可能有误差")
    doc.close()
    if not chunks:
        raise UnsupportedFile("这份 PDF 里没有读到可用文字（可能是纯图片且识别失败）")
    return IngestResult(filename=filename, source_type="pdf", chunks=chunks,
                        warnings=warnings, meta=meta)


# ---------------- PPTX ----------------

async def _parse_pptx(data: bytes, filename: str) -> IngestResult:
    try:
        from pptx import Presentation
        from pptx.enum.shapes import MSO_SHAPE_TYPE
    except Exception as e:  # pragma: no cover
        raise UnsupportedFile(f"服务器缺少 python-pptx，无法解析 PPT: {e}")
    try:
        prs = Presentation(io.BytesIO(data))
    except Exception as e:
        raise UnsupportedFile(f"PPT 打不开（可能损坏）: {e}")

    chunks: list[Chunk] = []
    warnings: list[str] = []
    ocr_done = 0
    for sidx, slide in enumerate(prs.slides, 1):
        parts = []
        images = []
        table_text = []
        for shape in slide.shapes:
            try:
                if shape.has_text_frame and shape.text_frame.text.strip():
                    parts.append(shape.text_frame.text.strip())
                if getattr(shape, "has_table", False) and shape.has_table:
                    for row in shape.table.rows:
                        table_text.append(" | ".join(
                            (cell.text or "").strip() for cell in row.cells))
                if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                    images.append(shape)
            except Exception:
                continue
        try:
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip():
                parts.append("【备注】" + slide.notes_slide.notes_text_frame.text.strip())
        except Exception:
            pass

        text = "\n".join(p for p in parts if p)
        kind = "text"
        if len(text) < 60 and images and ocr_done < MAX_PPT_OCR_SLIDES:
            try:
                text = await _ocr_image_bytes(images[0].image.blob, "image/png")
                kind = "image_ocr"
                ocr_done += 1
            except Exception as e:
                warnings.append(f"第 {sidx} 页图片识别失败：{str(e)[:60]}")
        c = _mk_chunk(sidx, text, kind, slide=sidx)
        if c:
            chunks.append(c)
        if table_text:
            c = _mk_chunk(f"{sidx}t", "\n".join(table_text), "table", slide=sidx)
            if c:
                chunks.append(c)
    if ocr_done:
        warnings.append(f"{ocr_done} 页是图片型幻灯片，已用视觉模型识别")
    if not chunks:
        raise UnsupportedFile("这份 PPT 里没有读到可用文字")
    return IngestResult(filename=filename, source_type="pptx", chunks=chunks,
                        warnings=warnings, meta={"slides": len(prs.slides)})


# ---------------- DOCX ----------------

def _parse_docx(data: bytes, filename: str) -> IngestResult:
    try:
        from docx import Document
    except Exception as e:  # pragma: no cover
        raise UnsupportedFile(f"服务器缺少 python-docx，无法解析 Word: {e}")
    try:
        doc = Document(io.BytesIO(data))
    except Exception as e:
        raise UnsupportedFile(f"Word 打不开（可能损坏）: {e}")

    chunks: list[Chunk] = []
    current: list[str] = []
    heading = ""
    idx = 0

    def flush():
        nonlocal current, idx
        if not current:
            return
        idx += 1
        c = _mk_chunk(idx, "\n".join(current), "text", meta={"heading": heading})
        if c:
            chunks.append(c)
        current = []

    for p in doc.paragraphs:
        text = (p.text or "").strip()
        if not text:
            continue
        style = (getattr(p.style, "name", "") or "")
        if _HEADING_STYLE_RE.match(style):
            flush()
            heading = text
            current.append(text)
        else:
            current.append(text)
            if sum(len(x) for x in current) > MAX_CHUNK_CHARS:
                flush()
    flush()

    for ti, table in enumerate(doc.tables, 1):
        rows = [" | ".join((cell.text or "").strip() for cell in row.cells)
                for row in table.rows]
        idx += 1
        c = _mk_chunk(idx, "\n".join(rows), "table", meta={"table": ti})
        if c:
            chunks.append(c)
    if not chunks:
        raise UnsupportedFile("这份 Word 里没有读到可用文字")
    return IngestResult(filename=filename, source_type="docx", chunks=chunks,
                        warnings=[], meta={"paragraphs": len(doc.paragraphs)})


# ---------------- XLSX / CSV ----------------

def _parse_xlsx(data: bytes, filename: str) -> IngestResult:
    try:
        import openpyxl
    except Exception as e:  # pragma: no cover
        raise UnsupportedFile(f"服务器缺少 openpyxl，无法解析 Excel: {e}")
    try:
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    except Exception as e:
        raise UnsupportedFile(f"Excel 打不开（可能损坏）: {e}")

    chunks: list[Chunk] = []
    warnings: list[str] = []
    idx = 0
    for ws in wb.worksheets:
        rows = []
        for ri, row in enumerate(ws.iter_rows(values_only=True), 1):
            if ri > MAX_XLSX_ROWS:
                warnings.append(f"工作表「{ws.title}」超过 {MAX_XLSX_ROWS} 行，已截断")
                break
            vals = ["" if v is None else str(v) for v in row]
            if any(v.strip() for v in vals):
                rows.append(" | ".join(vals))
        idx += 1
        c = _mk_chunk(idx, f"工作表：{ws.title}\n" + "\n".join(rows),
                      "table", sheet=ws.title)
        if c:
            chunks.append(c)
    if not chunks:
        raise UnsupportedFile("这份 Excel 里没有读到数据")
    return IngestResult(filename=filename, source_type="xlsx", chunks=chunks,
                        warnings=warnings, meta={"sheets": len(wb.worksheets)})


def _parse_csv(data: bytes, filename: str) -> IngestResult:
    text = _decode_text(data)
    rows = []
    for i, row in enumerate(csv.reader(io.StringIO(text))):
        if i >= MAX_XLSX_ROWS:
            break
        rows.append(" | ".join(row))
    c = _mk_chunk(1, f"CSV 数据：{filename}\n" + "\n".join(rows),
                  "table", sheet="csv")
    if not c:
        raise UnsupportedFile("CSV 是空的")
    warnings = [f"超过 {MAX_XLSX_ROWS} 行已截断"] if len(rows) >= MAX_XLSX_ROWS else []
    return IngestResult(filename=filename, source_type="csv", chunks=[c],
                        warnings=warnings, meta={"rows": len(rows)})


# ---------------- 图片 / 文本 ----------------

async def _parse_image(data: bytes, filename: str, ext: str) -> IngestResult:
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    try:
        text = await _ocr_image_bytes(data, mime)
    except Exception as e:
        raise UnsupportedFile(f"图片识别失败：{str(e)[:120]}")
    c = _mk_chunk(1, text, "image_ocr", meta={"image": filename})
    if not c:
        raise UnsupportedFile("图片里没有识别到可用文字（可能太模糊）")
    return IngestResult(filename=filename, source_type="image", chunks=[c],
                        warnings=["图片由视觉模型识别，可能有误差"],
                        meta={"mime": mime})


def _parse_text(data: bytes, filename: str) -> IngestResult:
    text = _decode_text(data)
    chunks: list[Chunk] = []
    idx = 0
    parts = re.split(r"(?m)^(#{1,6}\s+.+)$", text)
    if len(parts) > 1:
        buf = []
        for p in parts:
            if re.match(r"^#{1,6}\s+", p or ""):
                if buf:
                    idx += 1
                    c = _mk_chunk(idx, "\n".join(buf), "text")
                    if c:
                        chunks.append(c)
                buf = [p]
            else:
                buf.append(p)
        if buf:
            idx += 1
            c = _mk_chunk(idx, "\n".join(buf), "text")
            if c:
                chunks.append(c)
    else:
        for i in range(0, len(text), MAX_CHUNK_CHARS):
            idx += 1
            c = _mk_chunk(idx, text[i:i + MAX_CHUNK_CHARS], "text")
            if c:
                chunks.append(c)
    if not chunks:
        raise UnsupportedFile("文本文件是空的")
    return IngestResult(filename=filename, source_type="text", chunks=chunks,
                        warnings=[], meta={"chars": len(text)})


def _decode_text(data: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "gb18030", "gbk"):
        try:
            return data.decode(enc)
        except Exception:
            continue
    return data.decode("utf-8", errors="replace")
