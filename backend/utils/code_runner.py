"""
代码执行沙箱 — 混合模式
  Python: 本地 subprocess 执行（快速、无 API 依赖）
  C++/Java/JS: Piston API（云端沙箱，安全隔离）

Piston API docs: https://github.com/engineer-man/piston
"""
import subprocess
import sys
import re
import tempfile
import os
import httpx
import json
from pathlib import Path
from logging_config import logger

PISTON_URL = os.getenv("PISTON_URL", "http://localhost:2000/api/v2/piston/execute")

# 语言 → (Piston language, Piston version, 文件扩展名)
LANGUAGE_CONFIG = {
    "python":  ("python", "3.10.0", "py"),
    "python3": ("python", "3.10.0", "py"),
    "cpp":     ("c++", "10.2.0", "cpp"),
    "c++":     ("c++", "10.2.0", "cpp"),
    "java":    ("java", "15.0.2", "java"),
    "javascript": ("javascript", "18.15.0", "js"),
    "js":      ("javascript", "18.15.0", "js"),
    "typescript": ("typescript", "5.0.3", "ts"),
    "c":       ("c", "10.2.0", "c"),
    "go":      ("go", "1.16.2", "go"),
    "rust":    ("rust", "1.68.2", "rs"),
}

# 内置编译器路径
_UTILS_DIR = Path(__file__).parent
_MINGW_BIN = _UTILS_DIR / "mingw" / "bin"
_JDK_BIN = _UTILS_DIR / "jdk" / "bin"
# winget 安装的 MinGW 路径
_WINGET_MINGW = Path.home() / "AppData/Local/Microsoft/WinGet/Packages"
# 查找 winget mingw 目录
_WINGET_MINGW_BIN = None
if _WINGET_MINGW.exists():
    for d in _WINGET_MINGW.glob("*WinLibs*"):
        candidate = d / "mingw64" / "bin"
        if candidate.exists():
            _WINGET_MINGW_BIN = candidate
            break

def _find_compiler(names: list[str]) -> str | None:
    """查找编译器：先查内置路径，再查 PATH"""
    import shutil
    bases = [_MINGW_BIN, _JDK_BIN]
    if _WINGET_MINGW_BIN: bases.append(_WINGET_MINGW_BIN)
    for base in bases:
        for name in names:
            exe = base / (name + ".exe")
            if exe.exists():
                return str(exe)
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return None

def get_available_languages() -> dict:
    """返回所有可用语言及其状态"""
    langs = {
        "python": {"label": "Python 3", "available": True},
        "c": {"label": "C", "available": _find_compiler(["gcc"]) is not None},
        "cpp": {"label": "C++", "available": _find_compiler(["g++"]) is not None},
        "java": {"label": "Java", "available": _find_compiler(["javac"]) is not None and _find_compiler(["java"]) is not None},
    }
    return langs


LANGUAGE_LABELS = {
    "python": "Python 3",
    "python3": "Python 3",
    "cpp": "C++",
    "c++": "C++",
    "java": "Java",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "c": "C",
    "go": "Go",
    "rust": "Rust",
}


def _run_python_local(code: str, stdin: str, timeout_sec: int = 5) -> dict:
    """本地 subprocess 执行 Python 代码"""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(code)
        tmp_path = f.name

    try:
        proc = subprocess.run(
            [sys.executable, tmp_path],
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        return {
            "stdout": proc.stdout or "",
            "stderr": proc.stderr or "",
            "exit_code": proc.returncode,
            "timeout": False,
            "language": "python",
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": f"执行超时 ({timeout_sec}s)",
            "exit_code": -1,
            "timeout": True,
            "language": "python",
        }
    except FileNotFoundError:
        # python3 not found, try python
        try:
            proc = subprocess.run(
                ["python", tmp_path],
                input=stdin,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
            return {
                "stdout": proc.stdout or "",
                "stderr": proc.stderr or "",
                "exit_code": proc.returncode,
                "timeout": False,
                "language": "python",
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"执行超时 ({timeout_sec}s)",
                "exit_code": -1,
                "timeout": True,
                "language": "python",
            }
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


async def _run_piston(lang_key: str, code: str, stdin: str, timeout_ms: int = 5000) -> dict:
    """通过 Piston API 执行代码"""
    config = LANGUAGE_CONFIG.get(lang_key)
    if not config:
        return {
            "stdout": "",
            "stderr": f"不支持的语言: {lang_key}",
            "exit_code": -1,
            "timeout": False,
        }

    piston_lang, version, ext = config
    filename = f"main.{ext}"

    payload = {
        "language": piston_lang,
        "version": version,
        "files": [{"name": filename, "content": code}],
        "stdin": stdin,
        "compile_timeout": 15000,
        "run_timeout": min(timeout_ms, 15000),
        "compile_memory_limit": 512 * 1024,   # 512 MB in KB
        "run_memory_limit": 512 * 1024,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(PISTON_URL, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                run = data.get("run", {})
                return {
                    "stdout": run.get("stdout", "") or "",
                    "stderr": run.get("stderr", "") or "",
                    "exit_code": run.get("code", 0) or 0,
                    "timeout": bool(run.get("signal")),
                    "language": lang_key,
                }
            else:
                return {
                    "stdout": "",
                    "stderr": f"Piston API 错误: {resp.status_code}",
                    "exit_code": -1,
                    "timeout": False,
                }
    except Exception as e:
        logger.error(f"Piston 执行失败: {e}")
        return {
            "stdout": "",
            "stderr": f"代码执行服务暂不可用: {e}",
            "exit_code": -1,
            "timeout": False,
        }


async def run_code(lang: str, code: str, stdin: str = "",
                   timeout_ms: int = 5000) -> dict:
    """
    执行代码，优先级：本地编译器 > Piston API。
    """
    lang = lang.lower().strip()

    # Python → 本地 subprocess
    if lang in ("python", "python3"):
        return _run_python_local(code, stdin, timeout_sec=max(1, timeout_ms // 1000))

    # C/C++/Java → 优先本地编译，否则 Piston
    local_compilers = {
        "c": (["gcc", "-x", "c", "-O2", "-o"], "gcc"),
        "cpp": (["g++", "-x", "c++", "-O2", "-o"], "g++"),
        "c++": (["g++", "-x", "c++", "-O2", "-o"], "g++"),
        "java": (None, "javac"),  # Java 特殊处理
    }
    if lang in local_compilers:
        result = _run_compiled_local(lang, code, stdin, timeout_ms)
        if result is not None:
            return result

    # 回退到 Piston
    return await _run_piston(lang, code, stdin, timeout_ms)


def _run_compiled_local(lang: str, code: str, stdin: str, timeout_ms: int = 5000) -> dict | None:
    """本地编译执行 C/C++/Java。编译器不存在返回 None"""
    import shutil

    exts = {"c": ".c", "cpp": ".cpp", "c++": ".cpp", "java": ".java"}
    ext = exts.get(lang, ".cpp")
    timeout_sec = max(1, timeout_ms // 1000)

    with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False, encoding="utf-8") as f:
        f.write(code)
        src_path = f.name

    exe_path = None
    try:
        if lang == "java":
            javac = shutil.which("javac")
            java = shutil.which("java")
            if not javac or not java:
                return None  # 回退到 Piston
            work_dir = os.path.dirname(src_path)
            # 从源码中提取类名
            class_match = re.search(r'public\s+class\s+(\w+)', code)
            class_name = class_match.group(1) if class_match else "Main"
            # 重命名源文件以匹配类名
            class_path = os.path.join(work_dir, class_name + ".java")
            os.rename(src_path, class_path)
            src_path = class_path
            # 编译
            subprocess.run([javac, class_path], capture_output=True, text=True, timeout=timeout_sec, cwd=work_dir)
            # 运行
            proc = subprocess.run([java, "-cp", work_dir, class_name], input=stdin, capture_output=True, text=True, timeout=timeout_sec)
        else:
            compiler = shutil.which("gcc") if lang == "c" else shutil.which("g++")
            if not compiler:
                return None  # 回退到 Piston
            exe_path = src_path + ".exe"
            compile_proc = subprocess.run([compiler, src_path, "-O2", "-o", exe_path], capture_output=True, text=True, timeout=timeout_sec)
            if compile_proc.returncode != 0:
                return {"stdout": "", "stderr": compile_proc.stderr, "exit_code": compile_proc.returncode, "timeout": False, "language": lang}
            proc = subprocess.run([exe_path], input=stdin, capture_output=True, text=True, timeout=timeout_sec)

        return {"stdout": proc.stdout or "", "stderr": proc.stderr or "", "exit_code": proc.returncode, "timeout": False, "language": lang}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": f"执行超时 ({timeout_sec}s)", "exit_code": -1, "timeout": True, "language": lang}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "exit_code": -1, "timeout": False, "language": lang}
    finally:
        try:
            os.unlink(src_path)
            if exe_path: os.unlink(exe_path)
            # 清理 Java class 文件
            if lang == "java":
                work_dir = os.path.dirname(src_path)
                class_name = os.path.splitext(os.path.basename(src_path))[0]
                try: os.unlink(os.path.join(work_dir, class_name + ".class"))
                except OSError: pass
        except OSError:
            pass


def judge_test_case(stdout: str, expected: str) -> bool:
    """
    判断输出是否匹配预期。
    支持：
      - 精确匹配（去首尾空白）
      - 多行输出逐行比较
      - 允许浮点数误差 1e-6
    """
    out_lines = stdout.strip().splitlines()
    exp_lines = expected.strip().splitlines()

    if len(out_lines) != len(exp_lines):
        # 尝试单行匹配（忽略空格差异）
        out_flat = stdout.strip().replace(" ", "").replace("\n", "")
        exp_flat = expected.strip().replace(" ", "").replace("\n", "")
        if out_flat == exp_flat:
            return True
        return False

    for out_line, exp_line in zip(out_lines, exp_lines):
        out_line = out_line.strip()
        exp_line = exp_line.strip()
        if out_line == exp_line:
            continue
        # 尝试浮点数比较
        try:
            out_num = float(out_line)
            exp_num = float(exp_line)
            if abs(out_num - exp_num) < 1e-6:
                continue
        except (ValueError, TypeError):
            pass
        # 尝试忽略尾部空格
        if out_line.rstrip() == exp_line.rstrip():
            continue
        return False
    return True
