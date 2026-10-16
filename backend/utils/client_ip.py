"""
真实客户端 IP —— 全仓唯一入口。

为什么需要这个文件
------------------
线上拓扑是：客户端 → Nginx(宝塔) → 127.0.0.1:8000 → uvicorn。

于是 `request.client.host` 拿到的是 **Nginx 自己**（127.0.0.1），不是用户。
2026-09-27 已经踩过一次，当时的症状是：wx-bind 的限流写的是
「5 次 / 60 秒」，实测第 6 次就 429 —— 而且**换账号、换人、换楼都还是 429**，
因为整个校园网在 nginx 眼里是同一个 127.0.0.1。
当天的修复是把 key 从「纯 IP」改成「IP + 账号」绕过去，**根因没动**。

本文件修的就是那个根因。

读哪个头：只认 X-Real-IP
-----------------------
Nginx 侧（/www/server/panel/vhost/nginx/proxy/api.jizhi-learn.com/*.conf）：

    proxy_set_header X-Real-IP       $remote_addr;                  ← 覆盖式
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;    ← 追加式

- `X-Real-IP` 是**覆盖**写入的：客户端自己带什么都会被 Nginx 用真实 $remote_addr 顶掉。
  所以它在经过我们这台 Nginx 之后是可信的。
- `X-Forwarded-For` 是**追加**的（`$proxy_add_x_forwarded_for` 会把客户端传来的原值
  拼在前面，再接上真实地址）。也就是说 **XFF 的第一段是攻击者自己写的**。
  谁要是图省事取 `xff.split(",")[0]`，等于把限流键和 IP 黑名单拱手交给攻击者
  —— 每次请求换一个假 IP，限流就永远不会命中。

  真要读 XFF 的话，**只能取最后一段**（那是 Nginx 追加的真实 $remote_addr）。
  本文件把它作为 X-Real-IP 缺失时的兜底，并在代码里写死这一点。

⚠️ 但「可信」有个前提：请求真的经过了 Nginx
--------------------------------------------
uvicorn 的启动命令是 `--host 0.0.0.0`，也就是**监听所有网卡**。
如果 8000 端口对外可达，攻击者可以绕过 Nginx 直连后端，
那时他自带的 `X-Real-IP` 就**没有任何人覆盖它** —— 直接变成伪造。

所以本文件不无条件信任 X-Real-IP，而是先看**直连对端**是不是本机回环：
- 对端是 127.0.0.1 / ::1  → 一定经过了本机 Nginx，X-Real-IP 可信
- 对端是别的地址         → 说明是直连（或被别的东西代理），**忽略 X-Real-IP**，用对端地址

这是标准的 proxy-header 信任模型，不依赖运维把 8000 端口关掉。

返回 None 的含义
---------------
取不到可信 IP 时返回 **None**，而不是返回 "unknown" 之类的占位串。
调用方必须把 None 当作「这个维度不可用」并**跳过**按 IP 的判定 ——
绝不能把它聚成一个桶，否则又回到「全校共用一个限流配额」的老毛病上。
"""

from __future__ import annotations

import ipaddress
import logging

from fastapi import Request

logger = logging.getLogger(__name__)

# 可信代理（直连对端）。本机 Nginx 走 127.0.0.1，所以回环就是全部。
# 若将来 Nginx 换到别的机器，把它的地址加进来即可。
_TRUSTED_PEERS = {"127.0.0.1", "::1", "::ffff:127.0.0.1"}


def _normalize(raw: str | None) -> str | None:
    """
    把候选值收敛成一个干净的 IP 字符串，非法一律返回 None。

    两件事：
    1. 合法性校验 —— 存进 security_events 的 ip 列、以及限流的 key 都是它，
       不校验的话攻击者能塞进任意字符串（换行、超长串、伪造的「多个 IP」）。
    2. 归一化 IPv4-mapped IPv6 —— 服务端如果绑在 :: 上，IPv4 连接会呈现为
       `::ffff:1.2.3.4`，和纯 `1.2.3.4` 是两个不同的 key，
       同一个用户会分成两桶计数。这里统一压成 IPv4。
    """
    if not raw:
        return None
    raw = raw.strip()
    if not raw:
        return None
    try:
        ip = ipaddress.ip_address(raw)
    except ValueError:
        return None
    # ::ffff:1.2.3.4 → 1.2.3.4
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return str(ip)


def get_peer_ip(request: Request) -> str | None:
    """
    直连对端地址（不做任何信任判断）。
    正常线上环境下它**恒为 127.0.0.1** —— 拿到别的值就说明有人绕过 Nginx 直连了，
    这本身值得记一条安全事件。
    """
    return _normalize(request.client.host if request.client else None)


def is_via_trusted_proxy(request: Request) -> bool:
    """
    这个请求是不是经过了可信代理（本机 Nginx）。

    为什么需要单独一个函数：
        调用方很容易想当然地写「peer != ip 就说明是直连」——**这是错的**。
        直连时 get_client_ip() 返回的本来就是 peer，两者相等；
        正常经代理时 peer 恒为 127.0.0.1 而 ip 是真实地址，两者才不等。
        方向正好相反。判断"经没经代理"只能看 peer 本身，看不了 ip。

    False 表示有人绕过 Nginx 直连后端 —— 这是异常拓扑，值得记一条安全事件。
    """
    return get_peer_ip(request) in _TRUSTED_PEERS


def get_client_ip(request: Request) -> str | None:
    """
    返回可信的真实客户端 IP，取不到返回 None。

    调用方约定：
        ip = get_client_ip(request)
        if ip is not None:
            ...按 IP 限流/记事件...
        # ip 为 None 时跳过 IP 维度，改用 user_id 或其它维度
    """
    peer = get_peer_ip(request)

    # 只有「直连对端是本机回环」时才相信代理头 —— 见文件头的信任模型。
    if peer in _TRUSTED_PEERS:
        raw_real = request.headers.get("x-real-ip")
        real = _normalize(raw_real)
        if real:
            return real

        # 走到这里 = X-Real-IP 没给出一个能用的值。分两种情况报，因为处置方式不同：
        #
        # (a) 头在、但值非法。Nginx 写的是 $remote_addr，**内核给的，不可能是非法 IP**。
        #     出现非法值只有两种可能：中间还有别的东西在改写这个头，或配置被人动过。
        #     这比"缺失"严重，要报得更响 —— 它可能是有人在试探。
        if raw_real is not None:
            logger.error(
                "X-Real-IP 存在但非法：%r（peer=%s）。"
                "Nginx 写的是 $remote_addr，不该出现非法值 —— "
                "请检查反代链路里是否还有别的东西在改写此头。",
                raw_real[:100], peer,
            )

        # (b) 头缺失 / 值不可用 → 兜底取 XFF 的**最后一段**。
        #     Nginx 用 $proxy_add_x_forwarded_for 追加，真实地址永远在末尾。
        #     ⚠️ 取 [0] 是错的，那是攻击者自己填的（见 tests/test_client_ip.py 第 4 组）。
        xff = request.headers.get("x-forwarded-for")
        if xff:
            last = _normalize(xff.split(",")[-1])
            if last:
                if raw_real is None:
                    logger.warning(
                        "X-Real-IP 缺失，回落到 X-Forwarded-For 末段 %s —— "
                        "请检查 Nginx 是否仍配置了 proxy_set_header X-Real-IP",
                        last,
                    )
                return last

        # 经了 Nginx 却拿不到任何可用地址：放弃 IP 维度，不要瞎猜。
        # （debug 级：本地直连接口调试时会频繁触发，不该刷满生产日志）
        logger.debug("请求来自可信代理但无可用客户端 IP 头，IP 维度不可用")
        return None

    # 非回环对端 = 有人在直连后端，或链路结构变了。
    # 此时任何代理头都不可信，用对端地址本身（至少它是内核给的，伪造不了）。
    if peer is not None:
        logger.warning(
            "检测到非代理直连：peer=%s，已忽略请求头里的 X-Real-IP/XFF。"
            "若这是预期拓扑，请把该地址加入 _TRUSTED_PEERS；"
            "否则应确认 8000 端口未对外暴露。",
            peer,
        )
    return peer


def get_client_ip_or_unknown(request: Request) -> str:
    """
    只给「展示用」的场景（日志文案、事件详情）——
    取不到时返回字符串 'unknown'，方便阅读。

    ⚠️ 不要拿它去做限流键或聚合统计：所有取不到 IP 的请求会被并成一个桶，
       那正是本文件要消灭的问题。限流请用 get_client_ip() 并处理 None。
    """
    return get_client_ip(request) or "unknown"
