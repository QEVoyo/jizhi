from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any
from config import settings
import httpx
from datetime import datetime

router = APIRouter(prefix="/tools", tags=["工具"])


def get_supabase_headers():
    return {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }


# ========== 打卡 ==========
@router.get("/checkin/{user_id}")
async def get_checkin(user_id: str):
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}"
    }
    url = f"{settings.SUPABASE_URL}/rest/v1/checkins?user_id=eq.{user_id}&select=projects"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code == 200 and res.json():
            return {"projects": res.json()[0].get("projects", [])}
        return {"projects": []}


@router.post("/checkin/{user_id}")
async def save_checkin(user_id: str, data: Dict[str, Any]):
    """保存打卡数据"""
    print(f"收到打卡数据: {data}")
    print(f"projects 内容: {data.get('projects', [])}")

    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    projects = data.get("projects", [])

    async with httpx.AsyncClient() as client:
        # 检查是否存在
        check_url = f"{settings.SUPABASE_URL}/rest/v1/checkins?user_id=eq.{user_id}"
        check_res = await client.get(check_url, headers=headers)

        if check_res.status_code == 200 and check_res.json():
            # 更新
            update_url = f"{settings.SUPABASE_URL}/rest/v1/checkins?user_id=eq.{user_id}"
            res = await client.patch(update_url, headers=headers,
                                     json={"projects": projects})
        else:
            # 插入
            insert_url = f"{settings.SUPABASE_URL}/rest/v1/checkins"
            res = await client.post(insert_url, headers=headers,
                                    json={"user_id": user_id, "projects": projects})

        print(f"打卡保存响应: {res.status_code} - {res.text}")

        if res.status_code not in [200, 201, 204]:
            raise HTTPException(status_code=400, detail=f"保存失败: {res.text}")

        return {"success": True}


# ========== 倒计时 ==========
@router.get("/countdown/{user_id}")
async def get_countdown(user_id: str):
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}"
    }
    url = f"{settings.SUPABASE_URL}/rest/v1/countdowns?user_id=eq.{user_id}&select=events"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code == 200 and res.json():
            return {"events": res.json()[0].get("events", [])}
        return {"events": []}


@router.post("/countdown/{user_id}")
async def save_countdown(user_id: str, data: Dict[str, Any]):
    """保存倒计时数据"""
    print(f"收到倒计时数据: {data}")

    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    events = data.get("events", [])

    async with httpx.AsyncClient() as client:
        check_url = f"{settings.SUPABASE_URL}/rest/v1/countdowns?user_id=eq.{user_id}"
        check_res = await client.get(check_url, headers=headers)

        if check_res.status_code == 200 and check_res.json():
            update_url = f"{settings.SUPABASE_URL}/rest/v1/countdowns?user_id=eq.{user_id}"
            res = await client.patch(update_url, headers=headers,
                                     json={"events": events, "updated_at": datetime.now().isoformat()})
        else:
            insert_url = f"{settings.SUPABASE_URL}/rest/v1/countdowns"
            res = await client.post(insert_url, headers=headers,
                                    json={"user_id": user_id, "events": events})

        if res.status_code not in [200, 201, 204]:
            print(f"倒计时保存失败: {res.status_code} - {res.text}")
            raise HTTPException(status_code=400, detail=f"保存失败: {res.text}")

        return {"success": True}


# ========== 计时器 ==========
@router.get("/timer/{user_id}")
async def get_timer(user_id: str):
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}"
    }
    url = f"{settings.SUPABASE_URL}/rest/v1/timers?user_id=eq.{user_id}&select=timers"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code == 200 and res.json():
            return {"timers": res.json()[0].get("timers", [])}
        return {"timers": []}


@router.post("/timer/{user_id}")
async def save_timer(user_id: str, data: Dict[str, Any]):
    """保存计时器数据"""
    print(f"收到计时器数据: {data}")

    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    timers = data.get("timers", [])

    async with httpx.AsyncClient() as client:
        check_url = f"{settings.SUPABASE_URL}/rest/v1/timers?user_id=eq.{user_id}"
        check_res = await client.get(check_url, headers=headers)

        if check_res.status_code == 200 and check_res.json():
            update_url = f"{settings.SUPABASE_URL}/rest/v1/timers?user_id=eq.{user_id}"
            res = await client.patch(update_url, headers=headers,
                                     json={"timers": timers, "updated_at": datetime.now().isoformat()})
        else:
            insert_url = f"{settings.SUPABASE_URL}/rest/v1/timers"
            res = await client.post(insert_url, headers=headers,
                                    json={"user_id": user_id, "timers": timers})

        if res.status_code not in [200, 201, 204]:
            print(f"计时器保存失败: {res.status_code} - {res.text}")
            raise HTTPException(status_code=400, detail=f"保存失败: {res.text}")

        return {"success": True}


# ========== 学习日志 ==========
@router.get("/learning-logs/{user_id}")
async def get_learning_logs(user_id: str):
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}"
    }
    # 查询 data 列
    url = f"{settings.SUPABASE_URL}/rest/v1/learning_logs?user_id=eq.{user_id}&select=data"

    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        if res.status_code == 200 and res.json():
            return {"logs": res.json()[0].get("data", [])}
        return {"logs": []}


@router.post("/learning-logs/{user_id}")
async def add_learning_log(user_id: str, data: Dict[str, Any]):
    """添加学习日志条目"""
    print(f"收到学习日志数据: {data}")

    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }

    keyword = data.get("keyword", "学习记录")
    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))

    async with httpx.AsyncClient() as client:
        # 获取现有日志
        get_url = f"{settings.SUPABASE_URL}/rest/v1/learning_logs?user_id=eq.{user_id}&select=data"
        get_res = await client.get(get_url, headers=headers)

        if get_res.status_code == 200 and get_res.json():
            logs = get_res.json()[0].get("data", [])
        else:
            logs = []

        # 添加新日志
        new_log = {
            "id": f"log_{int(datetime.now().timestamp())}",
            "keyword": keyword[:50],
            "date": date,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        logs.insert(0, new_log)

        # 更新或插入
        if get_res.status_code == 200 and get_res.json():
            update_url = f"{settings.SUPABASE_URL}/rest/v1/learning_logs?user_id=eq.{user_id}"
            res = await client.patch(update_url, headers=headers, json={"data": logs})
        else:
            insert_url = f"{settings.SUPABASE_URL}/rest/v1/learning_logs"
            res = await client.post(insert_url, headers=headers,
                                    json={"user_id": user_id, "data": logs})

        if res.status_code not in [200, 201, 204]:
            print(f"学习日志保存失败: {res.status_code} - {res.text}")
            raise HTTPException(status_code=400, detail=f"保存失败: {res.text}")

        return {"success": True}


@router.delete("/learning-logs/{user_id}")
async def clear_learning_logs(user_id: str):
    """清空学习日志"""
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    url = f"{settings.SUPABASE_URL}/rest/v1/learning_logs?user_id=eq.{user_id}"

    async with httpx.AsyncClient() as client:
        # 先检查是否存在
        check_res = await client.get(url, headers=headers)
        if check_res.status_code == 200 and check_res.json():
            # 存在则删除
            res = await client.delete(url, headers=headers)
            if res.status_code in [200, 204]:
                return {"success": True}

        # 不存在或删除失败都返回成功（因为没有数据可删）
        return {"success": True}


# ========== 学情报告 ==========
@router.get("/report/{user_id}")
async def get_report(user_id: str):
    """生成学情报告"""
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}"
    }

    async with httpx.AsyncClient() as client:
        try:
            # 获取学习日志
            log_url = f"{settings.SUPABASE_URL}/rest/v1/learning_logs?user_id=eq.{user_id}&select=data"
            log_res = await client.get(log_url, headers=headers)
            logs = []
            if log_res.status_code == 200 and log_res.json():
                logs = log_res.json()[0].get("data", [])

            # 获取打卡数据
            checkin_url = f"{settings.SUPABASE_URL}/rest/v1/checkins?user_id=eq.{user_id}&select=projects"
            checkin_res = await client.get(checkin_url, headers=headers)
            projects = []
            if checkin_res.status_code == 200 and checkin_res.json():
                projects = checkin_res.json()[0].get("projects", [])
            total_checkin_days = sum(p.get("completed_days", 0) for p in projects)

            # 获取倒计时数据
            countdown_url = f"{settings.SUPABASE_URL}/rest/v1/countdowns?user_id=eq.{user_id}&select=events"
            countdown_res = await client.get(countdown_url, headers=headers)
            events = []
            if countdown_res.status_code == 200 and countdown_res.json():
                events = countdown_res.json()[0].get("events", [])

            # 提取关键词
            keywords = list(set([log.get("keyword", "") for log in logs[-50:]]))[:20]

            return {
                "logs": logs[-30:],
                "keywords": keywords,
                "total_checkin_days": total_checkin_days,
                "project_count": len(projects),
                "events": events
            }
        except Exception as e:
            print(f"学情报告错误: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.delete("/learning-log")
async def delete_learning_log(user_id: str = Query(...), log_id: str = Query(...)):
    """删除单条学习日志"""
    headers = get_supabase_headers()

    async with httpx.AsyncClient() as client:
        # 先获取当前日志
        get_url = f"{settings.SUPABASE_URL}/rest/v1/learning_logs?user_id=eq.{user_id}&select=data"
        res = await client.get(get_url, headers=headers)
        if res.status_code != 200 or not res.json():
            raise HTTPException(status_code=404, detail="日志不存在")

        logs = res.json()[0].get("data", [])
        # 过滤掉要删除的日志
        new_logs = [log for log in logs if log.get("id") != log_id]

        if len(new_logs) == len(logs):
            raise HTTPException(status_code=404, detail="日志条目不存在")

        # 更新
        update_url = f"{settings.SUPABASE_URL}/rest/v1/learning_logs?user_id=eq.{user_id}"
        await client.patch(update_url, headers=headers, json={"data": new_logs})

        return {"success": True}