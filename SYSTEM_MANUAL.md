# 基智学习助手 (Jizhi Learn) — 系统说明书

> **文档版本** `2.0` · **最后更新** 2026-08-02
>
> **维护者** QEVoyo · **许可证** 未指定
>
> 基于 FastAPI + Vue 3 + Supabase + DeepSeek 的全栈 AI 学习平台

---

## 目录

1. [系统概述](#1-系统概述)
   - 1.1 [项目定位与设计理念](#11-项目定位与设计理念)
   - 1.2 [核心能力矩阵](#12-核心能力矩阵)
   - 1.3 [适用场景](#13-适用场景)
2. [技术架构](#2-技术架构)
   - 2.1 [总体架构图](#21-总体架构图)
   - 2.2 [技术栈分层详解](#22-技术栈分层详解)
   - 2.3 [关键设计决策](#23-关键设计决策)
3. [环境要求与安装部署](#3-环境要求与安装部署)
   - 3.1 [硬件与软件要求](#31-硬件与软件要求)
   - 3.2 [后端安装与配置](#32-后端安装与配置)
   - 3.3 [前端安装与配置](#33-前端安装与配置)
   - 3.4 [数据库初始化](#34-数据库初始化)
   - 3.5 [开发环境启动](#35-开发环境启动)
   - 3.6 [生产环境部署](#36-生产环境部署)
4. [项目结构与模块说明](#4-项目结构与模块说明)
   - 4.1 [完整目录树](#41-完整目录树)
   - 4.2 [后端模块职责](#42-后端模块职责)
   - 4.3 [前端模块职责](#43-前端模块职责)
5. [核心业务模块](#5-核心业务模块)
   - 5.1 [学科计划系统](#51-学科计划系统)
     - 5.1.1 [业务流程全景](#511-业务流程全景)
     - 5.1.2 [考纲体系](#512-考纲体系)
     - 5.1.3 [诊断摸底流程](#513-诊断摸底流程)
     - 5.1.4 [每日任务与做题流程](#514-每日任务与做题流程)
     - 5.1.5 [知识点掌握度算法](#515-知识点掌握度算法)
     - 5.1.6 [错题本机制](#516-错题本机制)
   - 5.2 [AI 对话系统](#52-ai-对话系统)
     - 5.2.1 [主对话系统 — 多智能体学习助手](#521-主对话系统chatarea--多智能体学习助手)
     - 5.2.2 [小吉语音助手 — 人格化 AI 伴侣](#522-小吉语音助手xiaojiocal--人格化-ai-伴侣)
     - 5.2.3 [SSE 流式响应处理流水线](#523-sse-流式响应处理流水线)
     - 5.2.4 [个性化 System Prompt 构建流水线](#524-个性化-system-prompt-构建流水线)
     - 5.2.5 [多模态集成（Vision）](#525-多模态集成vision)
     - 5.2.6 [对话后处理与系统集成](#526-对话后处理与系统集成)
   - 5.3 [学程系统](#53-学程系统)
     - 5.3.1 [双轨积分体系](#531-双轨积分体系)
     - 5.3.2 [三阶任务体系](#532-三阶任务体系)
     - 5.3.3 [领取动画流水线](#533-领取动画流水线)
     - 5.3.4 [25 个成就](#534-25-个成就)
     - 5.3.5 [数据表与 API](#535-数据表与-api)
   - 5.4 [社区模块](#54-社区模块)
     - 5.4.1 [动态广场](#541-动态广场communityfeed)
     - 5.4.2 [好友系统](#542-好友系统communityfriends)
     - 5.4.3 [私聊](#543-私聊communitychat)
     - 5.4.4 [好友排行](#544-好友排行rank)
     - 5.4.5 [学习成果卡](#545-学习成果卡communityprofilecard)
     - 5.4.6 [后端架构](#546-后端架构)
   - 5.5 [资源库](#55-资源库)
     - 5.5.1 [掌握度看板](#551-掌握度看板)
     - 5.5.2 [五大功能 Tab](#552-五大功能-tab)
     - 5.5.3 [错题本机制（学科计划侧）](#553-错题本机制学科计划侧)
     - 5.5.4 [知识点掌握度算法（EWMA）](#554-知识点掌握度算法ewma)
     - 5.5.5 [题目生成 Agent 流水线](#555-题目生成-agent-流水线)
     - 5.5.6 [资源库数据模型与持久化策略](#556-资源库数据模型与持久化策略)
   - 5.6 [评估中心](#56-评估中心)
     - 5.6.1 [学情报告](#561-学情报告evaluationreport)
     - 5.6.2 [评估表](#562-评估表evaluationtable)
     - 5.6.3 [学习规划](#563-学习规划learningplan)
   - 5.7 [个人画像（维度宇宙）](#57-个人画像维度宇宙)
     - 5.7.1 [3D 场景架构](#571-3d-场景架构)
     - 5.7.2 [九维详情](#572-九维详情)
     - 5.7.3 [后端数据聚合](#573-后端数据聚合evaluationpy)
   - 5.8 [消息中心](#58-消息中心)
     - 5.8.1 [通知分类](#581-通知分类10-个-tab)
     - 5.8.2 [通知创建与聚合](#582-通知创建与聚合notificationpy)
     - 5.8.3 [每日智能生成](#583-每日智能生成daily_generatorpy)
     - 5.8.4 [消息卡片展示](#584-消息卡片展示)
     - 5.8.5 [设置面板](#585-设置面板)
     - 5.8.6 [轮询与集成](#586-轮询与集成)
     - 5.8.7 [帮助中心 Q&A](#587-帮助中心-qa)
   - 5.9 [工具箱](#59-工具箱)
     - 5.9.0 [整体架构](#590-整体架构)
     - 5.9.1 [打卡](#591-打卡)
     - 5.9.2 [倒计时](#592-倒计时)
     - 5.9.3 [计时器](#593-计时器)
     - 5.9.4 [学习日志](#594-学习日志)
     - 5.9.5 [学情报告（工具版）](#595-学情报告工具版)
     - 5.9.6 [API 端点汇总](#596-api-端点汇总)
     - 5.9.7 [通用 Upsert 模式](#597-通用-upsert-模式)
   - 5.10 [API 中心](#510-api-中心)
     - 5.10.1 [架构设计](#5101-架构设计)
     - 5.10.2 [6 个可配置 AI 功能详细说明](#5102-6-个可配置-ai-功能详细说明)
     - 5.10.3 [平台路由与降级策略](#5103-平台路由与降级策略)
     - 5.10.4 [凭证安全模型](#5104-凭证安全模型)
     - 5.10.5 [UI 交互细节](#5105-ui-交互细节)
     - 5.10.6 [数据库设计](#5106-数据库设计)
     - 5.10.7 [后端 API 端点](#5107-后端-api-端点)
     - 5.10.8 [当前实现状态与规划](#5108-当前实现状态与规划)
   - 5.11 [微信登录与绑定](#511-微信登录与绑定)
     - 5.11.1 [扫码登录流程](#5111-扫码登录流程)
     - 5.11.2 [账号绑定](#5112-账号绑定)
     - 5.11.3 [自签 JWT 双模认证](#5113-自签-jwt-双模认证auth_middlewarepy)
     - 5.11.4 [小程序登录](#5114-小程序登录)
     - 5.11.5 [环境配置](#5115-环境配置)
     - 5.11.6 [状态管理与并发控制](#5116-状态管理与并发控制)
     - 5.11.7 [错误处理矩阵](#5117-错误处理矩阵)
     - 5.11.8 [安全加固](#5118-安全加固)
     - 5.11.9 [小程序登录差异](#5119-小程序登录差异)
   - 5.12 [管理后台](#512-管理后台)
     - 5.12.1 [后端架构设计](#5121-后端架构设计)
     - 5.12.2 [功能全景](#5122-功能全景)
     - 5.12.3 [仪表盘统计聚合算法](#5123-仪表盘统计聚合算法)
     - 5.12.4 [三级角色体系](#5124-三级角色体系)
     - 5.12.5 [题库批量导入流水线](#5125-题库批量导入流水线)
     - 5.12.6 [审计日志](#5126-审计日志admin_audit_logs)
     - 5.12.7 [管理员 API 完整参考](#5127-管理员-api-完整参考admin-前缀)
6. [后端 API 参考](#6-后端-api-参考)
   - 6.1 [学科计划 API](#61-学科计划-api)
   - 6.2 [认证 API](#62-认证-api)
   - 6.3 [管理后台 API](#63-管理后台-api)
   - 6.4 [对话 API](#64-对话-api)
   - 6.5 [小吉语音助手 API](#65-小吉语音助手-api)
   - 6.6 [通用响应规范与错误码](#66-通用响应规范与错误码)
7. [前端页面说明](#7-前端页面说明)
   - 7.1 [完整路由表](#71-完整路由表)
   - 7.2 [路由守卫逻辑](#72-路由守卫逻辑)
   - 7.3 [核心页面详解](#73-核心页面详解)
8. [数据库设计](#8-数据库设计)
   - 8.1 [ER 图（实体关系）](#81-er-图实体关系)
   - 8.2 [学科计划核心表 DDL](#82-学科计划核心表-ddl)
   - 8.3 [管理员系统表 DDL](#83-管理员系统表-ddl)
   - 8.4 [本地题库数据模型](#84-本地题库数据模型)
   - 8.5 [索引策略](#85-索引策略)
9. [认证与安全体系](#9-认证与安全体系)
   - 9.1 [认证架构](#91-认证架构)
   - 9.2 [JWT 双模验证流程](#92-jwt-双模验证流程)
   - 9.3 [三级角色鉴权](#93-三级角色鉴权)
   - 9.4 [微信 OAuth 接入](#94-微信-oauth-接入)
   - 9.5 [速率限制与安全措施](#95-速率限制与安全措施)
10. [AI 集成](#10-ai-集成)
    - 10.1 [LLM 客户端](#101-llm-客户端)
    - 10.2 [AI 批改引擎](#102-ai-批改引擎)
    - 10.3 [AI 学习规划生成](#103-ai-学习规划生成)
    - 10.4 [题库批量生成](#104-题库批量生成)
11. [代码判题沙箱](#11-代码判题沙箱)
    - 11.1 [沙箱架构](#111-沙箱架构)
    - 11.2 [编译器发现与配置](#112-编译器发现与配置)
    - 11.3 [测试点评分系统](#113-测试点评分系统)
    - 11.4 [安全边界与限制](#114-安全边界与限制)
12. [管理后台](#12-管理后台)
    - 12.1 [功能全景](#121-功能全景)
    - 12.2 [审计日志系统](#122-审计日志系统)
    - 12.3 [题库管理 CRUD](#123-题库管理-crud)
13. [本地题库引擎](#13-本地题库引擎)
    - 13.1 [设计动机](#131-设计动机)
    - 13.2 [数据加载流程](#132-数据加载流程)
    - 13.3 [查询与筛选机制](#133-查询与筛选机制)
    - 13.4 [持久化与热更新](#134-持久化与热更新)
14. [设计规范与 UX 指南](#14-设计规范与-ux-指南)
    - 14.1 [视觉风格定义](#141-视觉风格定义)
    - 14.2 [动画与过渡规范](#142-动画与过渡规范)
    - 14.3 [组件设计原则](#143-组件设计原则)
    - 14.4 [响应式与可访问性](#144-响应式与可访问性)
15. [开发与运维](#15-开发与运维)
    - 15.1 [开发工作流](#151-开发工作流)
    - 15.2 [Git 分支策略](#152-git-分支策略)
    - 15.3 [故障排查指南](#153-故障排查指南)
16. [已知问题与解决方案](#16-已知问题与解决方案)
17. [附录](#17-附录)
    - 17.1 [环境变量完整参考](#171-环境变量完整参考)
    - 17.2 [考纲配置规范](#172-考纲配置规范)
    - 17.3 [题目 JSON Schema](#173-题目-json-schema)
    - 17.4 [术语表](#174-术语表)

---

## 1. 系统概述

### 1.1 项目定位与设计理念

基智学习助手 (Jizhi Learn) 是一个**面向大学生和成人学习者的 AI 驱动备考平台**。系统的核心设计理念是：

> 以「考纲」(Syllabus) 为组织单元，将诊断摸底、AI 学习规划、每日刷题训练、AI 智能批改和知识点掌握度追踪串联为一个完整的备考闭环。

**三大设计原则**：

1. **本地优先 (Local-First)**：题库数据在服务启动时全量加载到 Python 内存，所有筛选、搜索、分页操作零网络延迟。代码判题优先使用本地编译器，不依赖外部 API。
2. **渐进式认证 (Graceful Auth)**：读操作端点不强制登录，Supabase 不可用时自动降级到自签 JWT。用户始终可以使用系统的核心浏览功能。
3. **考纲驱动 (Syllabus-Driven)**：所有功能（题库、诊断、计划、做题）均挂载在考纲之下。新增考试只需添加一个考纲配置 JSON 条目 + 题库 JSON 文件，无需改动代码。

### 1.2 核心能力矩阵

| 能力域 | 功能项 | 实现方式 | 成熟度 |
|--------|--------|----------|--------|
| **考纲管理** | 17 个标准化考纲，含维度/题型/真题/分数线配置 | `syllabi.json` 驱动 | ✅ 完善 |
| **题库引擎** | 16,889 题，11 种题型，内存索引，零延迟查询 | `local_question_bank.py` | ✅ 完善 |
| **诊断摸底** | 按考纲配置自动抽取组合题目，AI 评估水平 | DeepSeek 分析 | ✅ 完善 |
| **学习计划** | AI 根据诊断结果生成 N 天个性化备考计划 | DeepSeek GPT | ✅ 完善 |
| **每日任务** | 按计划天数分配题目，题目去重，题型均衡 | `bank_query + exclude_ids` | ✅ 完善 |
| **智能批改** | 客观题自动判对错，主观题（翻译/作文/编程）AI 批改 | 规则匹配 + DeepSeek | ✅ 完善 |
| **掌握度追踪** | EWMA 聚合算法，逐题更新知识点掌握分数 | `user_kp_mastery` 表 | ✅ 完善 |
| **错题本** | 跨考纲错题收集，随机取题练习，批量查询优化 | Supabase in() 聚合 | ✅ 完善 |
| **代码判题** | 编程题本地沙箱执行 + 测试点评分（AC/WA/TLE/RE） | 本地 subprocess + MinGW | ✅ 完善 |
| **认证系统** | 邮箱验证码 + 微信扫码 + 小程序登录，三重覆盖 | Supabase Auth + 自签 JWT | ✅ 完善 |
| **管理后台** | 6 大管理模块 >20 个端点，三级角色 + 审计日志 | FastAPI + Supabase RLS | ✅ 完善 |
| **UI 设计** | 科幻毛玻璃风格 + 粒子网格背景 + 响应式 | Vue 3 + Pure CSS | ✅ 完善 |

### 1.3 适用场景

- 大学生备考英语四六级、考研、计算机等级考试
- 自学者准备雅思/托福/教资/公务员/法考/CPA
- ACM 选手刷算法题（带测试点评分）
- 教育机构搭建私有题库 + AI 辅助教学平台（可在此基础上二次开发）

---

## 2. 技术架构

### 2.1 总体架构图

```
                                    ┌──────────────────────────────┐
                                    │      用户浏览器 (SPA)         │
                                    │   localhost:5173 (开发)       │
                                    │   Vue 3 + Pinia + Axios      │
                                    └─────────────┬────────────────┘
                                                  │ HTTP/HTTPS
                                                  │ Authorization: Bearer <jwt>
                                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FastAPI 后端 (Python 3.10+)                         │
│                        Uvicorn :8000 (dev) / :80 (wechat)                    │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         中间件层 (Middleware)                         │  │
│  │  ┌─────────────────┐ ┌──────────────────┐ ┌────────────────────────┐ │  │
│  │  │   CORS 中间件     │ │  auth_middleware  │ │  admin_middleware      │ │  │
│  │  │   允许 6 个域名    │ │  自签JWT/Supabase │ │  super_admin/admin/user│ │  │
│  │  │   * 方法 * 头     │ │  双重验证          │ │  三级角色鉴权           │ │  │
│  │  └─────────────────┘ └──────────────────┘ └────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        路由层 (15 个 Router)                          │  │
│  │  ┌─────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────────┐ │  │
│  │  │subject_plan  │ │    auth    │ │   admin    │ │  chat / career / │ │  │
│  │  │  ★ 主路由    │ │  邮箱/微信 │ │  管理后台  │ │  xiaoji / eval / │ │  │
│  │  │  19 个端点    │ │  18 个端点 │ │  22 个端点 │ │  community / ... │ │  │
│  │  └─────────────┘ └────────────┘ └────────────┘ └──────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────┐   ┌────────────────────┐   ┌─────────────────┐   │
│  │  local_question_bank  │   │   services/         │   │   agents/       │   │
│  │  17 JSON → dict 内存  │   │   supabase.py       │   │   llm_client.py │   │
│  │  query / random /     │   │   REST API 封装     │   │   DeepSeek v3   │   │
│  │  add / delete / save  │   │   统一 headers/错误 │   │   60s timeout   │   │
│  └──────────────────────┘   └────────────────────┘   └─────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
          │                        │                          │
          │ 本地文件 I/O           │ HTTP REST                │ HTTP REST
          ▼                        ▼                          ▼
┌──────────────────┐  ┌──────────────────────┐  ┌────────────────────────────┐
│ backend/data/*.json│  │ Supabase (PostgreSQL) │  │    DeepSeek API            │
│ 17 题库 + 1 配置 │  │  • 用户认证 (Auth)    │  │    api.deepseek.com         │
│ ~21MB JSON 文件  │  │  • 关系数据 (REST)    │  │    model: deepseek-chat     │
│ 内存 dict + index │  │  • 文件存储 (Storage)  │  │    max_tokens: 8192         │
│ 启动时全量加载    │  │  • RLS 行级安全       │  │    timeout: 55s             │
└──────────────────┘  └──────────────────────┘  └────────────────────────────┘
```

### 2.2 技术栈分层详解

| 层 | 组件 | 版本 / 说明 |
|----|------|-------------|
| **运行时** | Python 3.10+ / Node.js 18+ | 后端 / 前端 |
| **Web 框架** | FastAPI 0.x + Uvicorn | 异步 ASGI，自动 OpenAPI 文档 |
| **前端框架** | Vue 3 (Composition API) + Vite 5 | `<script setup>` 语法，HMR |
| **状态管理** | Pinia 2.x | 5 个 Store (auth/theme/session/tools) |
| **路由** | Vue Router 4.x | History 模式，35+ 路由 |
| **HTTP 客户端** | Axios (前端) / httpx (后端) | 拦截器：401 → 自动登出 |
| **数据库** | Supabase (PostgreSQL 15) | REST API 风格交互，非直连 SQL |
| **认证** | PyJWT 2.x (HS256) + Supabase Auth | 双模融合验证 |
| **AI** | DeepSeek v3 (OpenAI SDK) | `deepseek-chat`, 8K tokens |
| **代码沙箱** | `subprocess.run()` + MinGW GCC/G++ | 本地编译执行 |
| **二维码** | qrcode 7.x + Pillow | 微信扫码登录 |
| **邮箱** | SMTP (QQ 邮箱) | 验证码发送 |
| **语音** | 科大讯飞 API | TTS + ASR (小吉语音助手) |

### 2.3 关键设计决策

| 决策 | 原因 | 权衡 |
|------|------|------|
| **本地内存题库** | Supabase 每次查询走 HTTP，110 题查询需要网络往返，题库页面筛选慢 | 内存占用 ~50MB（17 文件），但查询零延迟 |
| **自签 JWT 双模认证** | Supabase 项目曾暂停导致全站 401，需要独立备用方案 | 需维护两套 token 校验逻辑，但高可用性有保障 |
| **代码沙箱本地化** | Piston 公共 API 于 2026-02 关闭，在线编译 API 被 GFW 屏蔽 | 需用户安装编译器，但无外部 API 依赖 |
| **Supabase REST API 交互** | 非直连 SQL —— 所有数据库操作通过 HTTP REST API | 简化了 Python 端连接管理，但每次操作一个 HTTP 往返 |
| **EWMA 掌握度算法** | 指数加权移动平均 (`0.7×旧 + 0.3×新`) 比简单平均更能反映最近水平变化 | 需要首次答题种子值 (70/30) |
| **DeepSeek 而非 OpenAI** | 中文出题质量好、价格低、API 国内可直连 | 偶有截断（~8K token 限制），需做 JSON 容错修复 |

---

## 3. 环境要求与安装部署

### 3.1 硬件与软件要求

| 项目 | 最低 | 推荐 |
|------|------|------|
| **操作系统** | Windows 10+ / macOS 12+ / Linux | Windows 11 / Ubuntu 22.04 |
| **内存** | 4GB RAM | 8GB+ (题库启动消耗 ~50MB) |
| **磁盘** | 500MB 空闲 | 2GB+ (题库 JSON 文件 ~21MB) |
| **Python** | 3.10 | 3.12+ |
| **Node.js** | 18 LTS | 20 LTS |
| **编译器(可选)** | — | winget MinGW-w64 (C/C++ 判题) |
| **JDK(可选)** | — | JDK 17+ (Java 判题) |

### 3.2 后端安装与配置

```bash
# 1. 克隆 / 进入项目
cd project1/backend

# 2. 创建虚拟环境 (推荐)
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# 3. 安装依赖
pip install -r requirements.txt
```

**`backend/requirements.txt` 完整清单**：
```
fastapi                 # Web 框架
uvicorn                 # ASGI 服务器
httpx                   # 异步 HTTP 客户端（调用 Supabase + 微信 API）
redis                   # 缓存（可选，当前未充分使用）
openai                  # DeepSeek API 客户端（OpenAI 兼容 SDK）
python-dotenv           # .env 环境变量加载
Pillow                  # 图片处理（头像压缩 + 二维码）
python-multipart        # 文件上传支持
pydantic                # 请求/响应模型校验
requests                # 同步 HTTP（volc_client / xunfei_client）
PyJWT                   # 自签 JWT 签发与验证
qrcode                  # 微信登录二维码生成
```

**环境变量 (`.env`) 完整参考**：
```env
# ===== DeepSeek AI (必填) =====
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com

# ===== Supabase (必填) =====
SUPABASE_URL=https://xxxxxxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...        # anon / public key
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6... # service_role key (绕过 RLS)

# ===== 邮箱验证码 (QQ 邮箱) =====
EMAIL_HOST=smtp.qq.com
EMAIL_PORT=587
EMAIL_USER=your_qq_number@qq.com
EMAIL_PASSWORD=xxxxxxxxxxxxxxx    # QQ邮箱 → 设置 → 账户 → POP3/SMTP → 授权码
EMAIL_RECEIVER=your_qq_number@qq.com

# ===== 微信登录 (可选，公众号测试号免费获取) =====
# 获取地址: https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login
WECHAT_WEB_APPID=wxXXXXXXXXXXXXXXXX
WECHAT_WEB_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ===== 微信小程序 (可选) =====
WECHAT_MP_APPID=wxXXXXXXXXXXXXXXXX
WECHAT_MP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ===== 自签 JWT =====
JWT_SECRET=your-production-secret-key-change-me
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=720           # 30 天

# ===== 网络地址 =====
FRONTEND_URL=http://localhost:5173
BACKEND_EXTERNAL_URL=http://192.168.1.100:80    # 微信 OAuth 回调地址（需标准端口）

# ===== 火山引擎 / 豆包 (可选) =====
VOLC_ACCESS_KEY=...
VOLC_SECRET_KEY=...
ARK_API_KEY=...

# ===== 科大讯飞 (可选) =====
XUNFEI_APPID=...
XUNFEI_API_KEY=...
XUNFEI_API_SECRET=...
```

### 3.3 前端安装与配置

```bash
cd project1/frontend

# 安装依赖
npm install

# 开发模式启动
npm run dev
# → http://localhost:5173
```

**前端依赖**（`package.json` 关键项）：
- `vue` ^3.x — 框架
- `vue-router` ^4.x — 路由
- `pinia` ^2.x — 状态管理
- `axios` ^1.x — HTTP 请求
- `vite` ^5.x — 构建工具
- `@vitejs/plugin-vue` — Vue SFC 编译

### 3.4 数据库初始化

在 Supabase Dashboard → **SQL Editor** 中按顺序执行以下脚本：

```
步骤 1: backend/sql/subject_plan_tables.sql
        └── 创建 6 张学科计划核心表
            ├── cet4_questions       (已废弃 — 题库已转为本地 JSON)
            ├── subject_plans        (★ 活跃)
            ├── plan_daily_tasks     (★ 活跃)
            ├── diagnosis_results    (★ 活跃)
            ├── question_records     (★ 活跃)
            └── user_kp_mastery     (★ 活跃)

步骤 2: backend/sql/admin_tables.sql
        └── 创建管理员系统表 + 扩展 profiles
            ├── ALTER profiles (is_admin, is_active)
            ├── user_feedback
            ├── user_qa
            ├── content_reports
            ├── system_announcements
            └── admin_audit_logs

步骤 3: backend/sql/add_wechat_columns.sql
        └── ALTER profiles ADD wechat_openid, wechat_unionid

步骤 4: backend/sql/add_announcement_image.sql
        └── ALTER system_announcements ADD image_url

步骤 5: backend/sql/grant_permissions.sql
        └── GRANT service_role 权限
```

### 3.5 开发环境启动

```bash
# 终端 1 — 启动后端
cd project1/backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
# FastAPI 启动日志:
#   已加载 17 个考纲
#   [题库] cet4 (CET-4 英语四级): OK 已加载 1098 题
#   [题库] cet6 ... OK 已加载 1073 题
#   ...共 17 个考纲
#   [题库] 总计 17 个考纲题库，16889 道题目
#   Uvicorn running on http://0.0.0.0:8000

# 终端 2 — 启动前端
cd project1/frontend
npm run dev
# → http://localhost:5173

# 微信扫码登录需要后端监听 80 端口，改用：
uvicorn main:app --reload --host 0.0.0.0 --port 80
```

**访问地址**：
- 前端页面: `http://localhost:5173`
- 后端 API 文档 (Swagger): `http://localhost:8000/docs`
- 后端 API 文档 (ReDoc): `http://localhost:8000/redoc`
- 健康检查: `http://localhost:8000/health`

### 3.6 生产环境部署

```bash
# === 后端部署 ===
# 方案 A: Gunicorn + Uvicorn Workers (Linux)
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.main:app \
    --bind 0.0.0.0:8000

# 方案 B: Docker 容器
# (Dockerfile 待补充)

# === 前端部署 ===
cd frontend
npm run build
# 产出: frontend/dist/
# 部署到 Nginx / Vercel / Netlify

# === Nginx 配置示例 ===
# server {
#     listen 80;
#     server_name jizhi-learn.com;
#     root /var/www/jizhi/dist;
#     index index.html;
#
#     location /api/ {
#         proxy_pass http://127.0.0.1:8000/;
#         proxy_set_header Host $host;
#         proxy_set_header X-Real-IP $remote_addr;
#     }
#
#     location / {
#         try_files $uri $uri/ /index.html;
#     }
# }
```

---

## 4. 项目结构与模块说明

### 4.1 完整目录树

```
project1/
├── .env                              # 后端环境变量 (不入 git)
├── .env.example                      # 环境变量模板
├── .gitignore                        # Git 忽略规则
├── requirements.txt                  # 外层 pip 引用 → `-r backend/requirements.txt`
├── PROJECT_LOG.md                    # ★ 开发日志 (37 条问题记录)
├── SYSTEM_MANUAL.md                  # ★ 本文件
│
├── supabase_migration.sql            # Supabase DDL (v1, 通知/偏好)
├── supabase_migration_cet4.sql       # Supabase DDL (CET-4 学科计划 6 表)
│
├── backend/                          # ─────────── 后端源码 ───────────
│   ├── main.py                       # FastAPI 应用工厂：CORS + 15 路由注册
│   ├── config.py                     # Settings 类，读取所有环境变量
│   ├── local_question_bank.py        # ★ 本地题库引擎 (322行)
│   ├── logging_config.py             # 统一 logging 配置
│   ├── requirements.txt              # Python 依赖清单
│   │
│   ├── agents/                       # AI 代理层
│   │   ├── llm_client.py             # DeepSeek API 客户端
│   │   ├── evaluator.py              # AI 批改评估代理
│   │   ├── generator.py              # AI 内容生成代理
│   │   └── planner.py               # AI 学习规划代理
│   │
│   ├── routers/                      # 路由层 (15 个模块)
│   │   ├── subject_plan.py           # ★ 核心路由 (1245行, 19 端点)
│   │   ├── auth.py                   # 认证路由 (976行, 18 端点)
│   │   ├── admin.py                  # 管理后台路由 (1110行, 22 端点)
│   │   ├── career.py                 # 生涯规划模块
│   │   ├── chat.py                   # AI 对话 (含意图识别/流式)
│   │   ├── community/                # 社区模块 (子路由)
│   │   ├── evaluation.py             # 评估模块
│   │   ├── feedback.py               # 用户反馈
│   │   ├── learning_plan.py          # 学习计划 (旧版, 已基本被 subject_plan 取代)
│   │   ├── profile_card.py           # 个人画像 (维度宇宙星图)
│   │   ├── qa.py                     # 帮助中心 Q&A
│   │   ├── questions.py              # 题目管理 (旧版, Supabase 题目)
│   │   ├── tools.py                  # 工具集
│   │   ├── video.py                  # 视频模块
│   │   └── xiaoji.py                # 小吉 AI 语音助手
│   │
│   ├── utils/                        # 工具层
│   │   ├── auth_middleware.py         # JWT 双模认证中间件
│   │   ├── admin_middleware.py        # 三级角色鉴权 + 审计日志写入
│   │   ├── code_runner.py            # ★ 代码沙箱 (334行)
│   │   ├── email.py                  # SMTP 邮件发送
│   │   ├── notification.py           # 站内通知
│   │   ├── rate_limit.py             # 内存速率限制
│   │   ├── sensitive_words.py        # 敏感词过滤
│   │   ├── volc_client.py            # 火山引擎(豆包)客户端
│   │   └── xunfei_client.py          # 科大讯飞语音客户端
│   │
│   ├── services/                     # 服务层
│   │   └── supabase.py               # ★ Supabase REST API 封装 (165行)
│   │
│   ├── data/                         # 数据文件 (~21MB)
│   │   ├── syllabi.json              # ★ 17 考纲配置
│   │   ├── cet4_questions.json, cet6_questions.json, ...
│   │   ├── grad_english_questions.json, grad_math_questions.json, ...
│   │   ├── ielts_questions.json, toefl_questions.json
│   │   ├── ncre2_*.json (3 文件)
│   │   ├── acm_icpc_questions.json
│   │   ├── mandarin_questions.json, teacher_cert_questions.json
│   │   ├── public_service_questions.json, judicial_questions.json
│   │   ├── cpa_questions.json
│   │   └── algorithm_ds_questions.json
│   │
│   ├── scripts/                      # 运维脚本
│   │   ├── seed_all_banks.py         # ★ 批量题库生成 (263行)
│   │   ├── check_progress.py         # 题库进度统计
│   │   ├── seed_cet4_questions.py    # CET-4 单独生成
│   │   ├── seed_local_bank.py        # 本地题库种子
│   │   └── seed_v2.py               # 早期种子脚本
│   │
│   ├── sql/                          # 数据库迁移
│   │   ├── subject_plan_tables.sql   # 学科计划 6 表
│   │   ├── admin_tables.sql          # 管理员 5 表 + profiles 扩展
│   │   ├── add_wechat_columns.sql    # profiles 加微信字段
│   │   ├── add_announcement_image.sql# 公告加图片字段
│   │   └── grant_permissions.sql     # Supabase 权限
│   │
│   └── tests/                        # 测试 (待完善)
│
└── frontend/                         # ─────────── 前端源码 ───────────
    ├── index.html                    # HTML 入口
    ├── vite.config.js                # Vite 配置
    ├── package.json                  # npm 依赖 + 脚本
    │
    ├── public/
    │   └── assets/
    │       └── icons/
    │           └── sidebar/          # 侧边栏 13 张 PNG 图标
    │
    └── src/
        ├── App.vue                   # ★ 根组件 (主题背景 + 路由过渡)
        ├── main.js                   # 入口 (Pinia + Router 挂载)
        │
        ├── router/
        │   └── index.js              # ★ 路由注册 (35+ 路由 + 守卫)
        │
        ├── stores/                   # Pinia 状态
        │   ├── auth.js               # ★ 认证 (登录/注册/微信/JWT)
        │   ├── theme.js              # 主题切换 (暗色/亮色)
        │   ├── session.js            # 会话管理
        │   └── tools.js              # 工具状态
        │
        ├── api/                      # API 调用层
        │   ├── auth.js               # 认证 API (邮箱 + 微信)
        │   ├── subjectPlan.js        # ★ 学科计划 API (17 个函数)
        │   ├── admin.js              # 管理后台 API
        │   ├── career.js             # 生涯 API
        │   ├── chat.js               # 对话 API
        │   ├── community.js          # 社区 API
        │   ├── learningPlan.js       # 学习计划 API (旧版)
        │   ├── profileCard.js        # 个人画像 API
        │   ├── questions.js          # 题目 API
        │   ├── tools.js, video.js    # 工具/视频 API
        │   ├── upload.js             # 文件上传 API
        │   ├── xiaoji.js             # 小吉 API
        │   └── index.js              # API 聚合导出
        │
        ├── utils/                    # 前端工具
        │   ├── request.js            # ★ Axios 实例 (401 拦截 → 登出)
        │   ├── questionLabels.js     # ★ 题型标签 (11 种类型 + 分类映射)
        │   ├── constants.js          # 常量 (后端地址/背景图/BG_MAP)
        │   └── storage.js            # localStorage 封装
        │
        ├── views/                    # 页面组件
        │   ├── SyllabusHub.vue       # ★ 考纲列表 (搜索/筛选/收藏)
        │   ├── SyllabusDetail.vue    # ★ 考纲详情 (5 Tab 总控台, 55K)
        │   ├── SubjectPractice.vue   # ★ 做题页 (编程 OJ 分栏, 43K)
        │   ├── Login.vue             # 登录页 (三栏 Tab + 微信扫码, 21K)
        │   ├── Landing.vue           # 落地页
        │   ├── Home.vue              # 首页
        │   ├── Profile.vue           # 个人中心 (含微信绑定卡片, 24K)
        │   ├── ProfileCard.vue       # 个人画像 (学习星图, 37K)
        │   ├── EvaluationCenter.vue  # 评估中心 (3 竖排卡片, 5.6K)
        │   ├── EvaluationReport.vue  # 评估报告
        │   ├── EvaluationTable.vue   # 评估表
        │   ├── DoQuestion.vue        # 做题页 (旧版)
        │   ├── Career.vue            # 生涯规划
        │   ├── CareerAchievements.vue# 生涯成就
        │   ├── CareerRank.vue        # 排行榜
        │   ├── CareerTasks.vue       # 生涯任务
        │   ├── LearningPlan.vue      # 学习计划
        │   ├── PlanDetail.vue        # 计划详情
        │   ├── PlanPreview.vue       # 计划预览
        │   ├── MasteryBoard.vue      # 掌握度看板
        │   ├── Community.vue         # 社区 (子路由容器)
        │   ├── ApiCenter.vue         # API 中心
        │   ├── OpenSource.vue        # 开源项目
        │   ├── Onboarding.vue        # 新用户引导
        │   ├── AnimationDemo.vue     # 动画演示
        │   └── admin/                # 管理后台页面
        │       ├── AdminLayout.vue   # 管理后台布局
        │       ├── AdminDashboard.vue# 仪表盘
        │       ├── AdminUsers.vue    # 用户管理
        │       ├── AdminQuestions.vue# 题库管理
        │       ├── AdminReports.vue  # 内容审核 (3 Tab)
        │       ├── AdminAnnouncements.vue # 公告管理
        │       └── AdminLogs.vue     # 操作日志
        │
        └── components/               # 通用组件
            ├── Sidebar.vue           # ★ App 图标网格侧边栏 (54K)
            ├── AppLayout.vue         # 全局布局 (毛玻璃 + 淡彩流光)
            ├── QAPage.vue            # ★ 帮助中心 (7 分类 29 FAQ, 36K)
            ├── MessageCenter.vue     # 消息中心 (含公告 Tab, 21K)
            ├── ChatArea.vue          # AI 对话区
            ├── CareerSidebar.vue     # 生涯模块侧边栏
            ├── XiaojiCall.vue        # 小吉 AI 语音通话
            ├── XiaojiSettings.vue    # 小吉设置
            ├── LoadingSpinner.vue    # 加载动画
            ├── GenerateForm.vue      # 题目生成表单
            ├── GenerationHistory.vue # 生成历史
            ├── MistakeBook.vue       # 错题本组件
            ├── QuestionSets.vue      # 题目集管理
            ├── Workbench.vue         # 工作台
            ├── BubbleBackground.vue  # 气泡背景
            ├── WaterBackground.vue   # 水纹背景
            ├── ResourceSidebar.vue   # 资源侧边栏
            └── community/            # 社区组件 (8 个)
```

### 4.2 后端模块职责

| 模块 | 职责 | 行数 |
|------|------|------|
| `local_question_bank.py` | 启动时加载 17 JSON → dict 内存；提供 query/random/get_by_ids/add/delete/save；支持跨考纲搜索 | 322 |
| `subject_plan.py` | 核心业务路由：考纲/题库/诊断/计划/每日任务/做题/掌握度/错题/代码判题 | 1,245 |
| `auth.py` | 邮箱验证码注册/登录 + 微信扫码 OAuth + 小程序登录 + 个人资料 CRUD | 976 |
| `admin.py` | 仪表盘/用户管理/内容审核/题库 CRUD/公告/日志/系统设置 | 1,110 |
| `code_runner.py` | Python subprocess + MinGW 编译器查找 + C/C++/Java 编译执行 + 测试判断 | 334 |
| `supabase.py` | Supabase REST API 服务层：统一 headers/URL 拼接/CRUD 兼容接口 | 165 |
| `auth_middleware.py` | 自签 JWT 验证 → Supabase 验证 → 返回 user_id | 79 |
| `admin_middleware.py` | 查 profiles.role → 三级角色鉴权 + `write_audit_log()` 非阻塞写入 | 96 |
| `llm_client.py` | OpenAI SDK → DeepSeek API: `call_llm()` 非流式 + `call_llm_stream()` 流式 | 45 |
| `seed_all_banks.py` | 读 syllabi.json → 算差值 → 按维度/题型批量生成 → 括号计数法提取 JSON → 修复截断 → 持久化 | 263 |

### 4.3 前端模块职责

| 模块 | 职责 | 行数 |
|------|------|------|
| `Sidebar.vue` | 3 列 App 图标网格 + 工具面板 + 对话面板；毛玻璃 + 淡彩流光背景 | 1,159 |
| `SyllabusDetail.vue` | 5 Tab 总控台：概览/题库/每日/知识/错题；题目状态颜色条；诊断按钮；删除计划 | 1,356 |
| `SubjectPractice.vue` | 做题引擎：11 种题型渲染；编程题 OJ 左右分栏；倒计时；语言选择持久化 | 1,052 |
| `Login.vue` | 三栏 Tab（用户/管理员/注册）；微信扫码面板 + 轮询机制 | 529 |
| `QAPage.vue` | 7 分类 29 FAQ；搜索过滤；跳转按钮 | 921 |
| `request.js` | Axios 实例：baseURL + 60s timeout + Bearer token 注入 + 401 → 自动登出 | 46 |
| `questionLabels.js` | 11 种题型中文标签；从 syllabus.dimensions 动态构建 category→name 映射；题型判断工具 | 122 |
| `auth.js` (store) | 登录/注册/微信扫码/微信绑定/轮询/偏好更新/首次引导判断 | 222 |

---

## 5. 核心业务模块

### 5.1.1 业务流程全景

```
用户旅程（完整闭环）
═════════════════════════════════════════════════════════════════════════

  ① 进入考纲列表           ② 浏览考纲详情             ③ 诊断摸底
  SyllabusHub.vue          SyllabusDetail.vue         → start_diagnosis
  ┌──────────────┐        ┌──────────────────┐       ┌──────────────┐
  │ 17 个考纲卡片 │  ────→ │「概览」Tab        │ ────→ │ 随机抽取 ~14题│
  │ 搜索 + 筛选   │        │  考试介绍+适合人群 │       │ 按 diagnosis_ │
  │ 收藏          │        │「题库」Tab         │       │ config 配置   │
  └──────────────┘        │  16,889 题浏览     │       └──────┬───────┘
                          └──────────────────┘              │
                                                            │ 提交答案
                                                            ▼
  ④ AI 批改 → 生成计划    ⑤ 每日任务                ⑥ 做题页
  submit_diagnosis         get_today_tasks            SubjectPractice.vue
  ┌──────────────┐        ┌──────────────────┐       ┌──────────────┐
  │ 客观题: 自动判 │        │ 按 day_number     │ ────→ │ ⏱ 正向计时   │
  │ 主观题: AI 批 │        │ 获取当天任务       │       │ 题目面板+答案  │
  │               │        │ 排除已做ID         │       │ 编程: OJ分栏   │
  │ DeepSeek 生成 │        │ 随机取题(去重)     │       │ ▶运行+提交    │
  │ N天备考计划    │        └──────────────────┘       └──────┬───────┘
  │               │                                         │
  │ 写入 Supabase │                                         │ 提交
  │ subject_plans │                                         ▼
  │ daily_tasks   │        ⑦ AI 批改                    ⑧ 掌握度更新
  └──────────────┘        ┌──────────────────┐       ┌──────────────┐
                          │ 客观题: 规则匹配  │       │ EWMA 算法:    │
                          │   choice/fill    │       │ new = old×0.7 │
                          │   /cloze/calc    │       │ + result×0.3  │
                          │                  │       │               │
                          │ 主观题: DeepSeek │       │ INSERT 或     │
                          │   translation/   │       │ UPDATE 聚合   │
                          │   essay/program  │       └──────────────┘
                          │   ming/analysis  │
                          └──────────────────┘

  ⑨ 学习追踪（持续）
  ┌──────────────────────────────────────────────────────────────┐
  │ 「知识」Tab → 知识点掌握度列表      GET /plans/{id}/mastery   │
  │ 「错题」Tab → 错题本 + 随机练习     GET /plans/{id}/mistakes  │
  │ 「题库」Tab → 题目颜色条状态         红<40%薄弱 / 黄40-60% / 绿>60%│
  │ 「总错题」  → 跨考纲随机错题练习    GET /mistakes/practice    │
  └──────────────────────────────────────────────────────────────┘
```

### 5.1.2 考纲体系

每个考纲由 `backend/data/syllabi.json` 中的一个 JSON 对象定义，17 个考纲共用一个数据结构：

```json
{
  "id": "cet4",                           // 唯一标识，用于路由、文件名
  "name": "CET-4 英语四级",               // 显示名
  "abbr": "C4",                           // 缩写 (考纲卡片图标)
  "color": "#409eff",                     // 主题色 (考纲卡片 + 详情页)
  "description": "...",                   // 一句话描述
  "intro": "...",                         // 长介绍 (概览 Tab)
  "suitable_for": "...",                  // 适合人群
  "max_score": 710,                       // 满分
  "pass_score": 425,                      // 及格线
  "target_count": 1000,                   // 目标题量
  "question_bank": "cet4_questions.json", // 题库文件名
  "question_types": [...],                // 全部题型
  "question_types_enabled": [...],        // 可用题型 (排除 听力等)
  "languages": ["python"],                // 编程语言限制

  "dimensions": [                         // 考察维度
    {
      "name": "词汇",                     // 中文显示名
      "category": "vocabulary",           // 机器标识 (匹配题目的 category 字段)
      "count": 98,                        // 题目数 (用于概览展示)
      "grey": false                       // 灰色占位 (听力等不可用维度)
    }
  ],

  "diagnosis_config": [                   // 诊断题目抽取规则
    {
      "category": "vocabulary",           // 匹配维度
      "sub": "高频核心词",                // 知识点子分类
      "type": "choice",                   // 题型
      "count": 3                          // 抽取数量
    }
  ],

  "exam_papers": [                        // 真题套卷 (灰色占位，待实现)
    { "name": "2024年6月真题", "count": 0, "grey": true }
  ]
}
```

**考纲数量与题量统计**：

| ID | 名称 | 题目数 | 目标 | 完成 | 题型数 | 维度数 |
|----|------|--------|------|------|--------|--------|
| cet4 | CET-4 | 1,098 | 1,000 | 110% ✅ | 8 | 6 |
| cet6 | CET-6 | 1,073 | 1,000 | 107% ✅ | 8 | 6 |
| grad-english | 考研英语 | 819 | 800 | 102% ✅ | 8 | 6 |
| ielts | 雅思 | 1,020 | 1,000 | 102% ✅ | 8 | 5 |
| toefl | 托福 | 1,019 | 1,000 | 102% ✅ | 8 | 5 |
| grad-math | 考研数学 | 1,209 | 1,200 | 101% ✅ | 6 | 4 |
| grad-politics | 考研政治 | 1,523 | 1,500 | 102% ✅ | 6 | 5 |
| ncre2-python | 计算机二级 Python | 1,017 | 1,000 | 102% ✅ | 3 | 6 |
| ncre2-c | 计算机二级 C | 818 | 800 | 102% ✅ | 3 | 6 |
| ncre2-office | 计算机二级 Office | 1,014 | 1,000 | 101% ✅ | 3 | 4 |
| acm-icpc | ACM-ICPC | 529 | 500 | 106% ✅ | 1 | 6 |
| mandarin | 普通话 | 595 | 600 | 99% 🟡 | 5 | 4 |
| teacher-cert | 教资 | 789 | 800 | 99% 🟡 | 7 | 4 |
| public-service | 公务员 | 1,769 | 2,000 | 88% 🟡 | 5 | 5 |
| judicial | 法考 | 1,090 | 1,500 | 73% 🟡 | 5 | 6 |
| cpa | CPA | 644 | 1,200 | 54% 🔴 | 5 | 7 |
| algorithm-ds | 算法与数据结构 | 863 | 2,000 | 43% 🔴 | 1 | 7 |
| **合计** | | **16,889** | **18,900** | **89%** | | |

### 5.1.3 诊断摸底流程

```
┌─ 前端 ─────────────────────────── ┌─ 后端 ───────────────────────────┐
                                    │
  点击「诊断摸底」按钮               │
  ↓                                 │
  GET /syllabi/{id}/diagnosis/start │
  ─────────────────────────────────→│  1. 读取 syllabi.json 的
                                    │     diagnosis_config[]
                                    │  2. 逐条调用 bank_query()
                                    │     category + sub + type
                                    │     + count + random_order
                                    │  3. 合并所有抽取题目
                                    │  4. random.shuffle()
  ←── { questions: [...14题],       │
         dimensions: [...] }        │
                                    │
  用户逐题作答 (答案 + 用时)        │
  ↓                                 │
  POST /{id}/diagnosis/submit       │
  ─────────────────────────────────→│  1. 查已有活跃计划 → already_exists
  { user_id, answers: [            │     (防重复创建)
    { question_id, user_answer,    │  2. 按 ID 精确取题 → q_map
      time_spent }, ...],          │  3. 逐题判对错 (_check_answer)
    preferences: {                 │     → correct_count
      goal_score, period_days,     │  4. 构建 AI prompt
      daily_minutes }              │     - 考纲名称/维度/题型
  }                                 │     - 目标分数/天数/分钟
                                    │     - 诊断详情(含对错)
   ←── { plan_id, plan_name,       │  5. call_llm(t=0.7) → 解析 JSON
         accuracy: 57,             │  6. 写入 Supabase:
         already_exists: false }   │     - subject_plans (1 行)
                                    │     - diagnosis_results (1 行)
                                    │     - plan_daily_tasks (N 行)
                                    │  7. 返回 plan_id
```

**防重复计划**：`submit_diagnosis()` 第一步即调用 `_get_user_plan(syllabus_id, user_id)` 检查是否已有非归档计划。若存在则直接返回已有 `plan_id`，前端展示已有计划而不创建新计划。

### 5.1.4 每日任务与做题流程

```
后端 get_today_tasks() 关键逻辑：
─────────────────────────────────────────────────────────────
1. 查计划 → 计算 day_number = (today - created_at).days + 1
           → day_number = clamp(1, day_number, period_days)

2. 查 plan_daily_tasks WHERE day_number = 当前天数
   → 返回该天的任务列表 (不含具体题目)

3. 获取已做题目ID: _get_done_ids(plan_id, user_id)
   → SELECT question_id FROM question_records WHERE plan_id=... AND user_id=...

4. 为每个任务分配题目:
   used_ids = set(done_ids)  // 初始排除所有已做题目
   for task in tasks:
       questions = bank_query(
           syllabus_id=sid,
           category=task.category,
           question_type=task.question_type,
           limit=task.question_count,
           random_order=True,
           exclude_ids=used_ids    // ← 排除已做 + 已分配给前面任务
       )
       for q in questions:
           used_ids.add(q.id)      // ← 累计，防止后续任务重复
```

**题目去重保证**：同一天的不同任务不会分配到相同题目；同一用户已做过的题目不会被再次分配。

### 5.1.5 知识点掌握度算法

**EWMA (指数加权移动平均)**：

```
IF 首次答题该知识点:
    mastery_score = 70.0  (答对) 或 30.0  (答错)
    total_count = 1
    correct_count = 1 或 0

ELSE (已有记录):
    total_count += 1
    correct_count += (1 if 答对 else 0)
    mastery_score = mastery_score × 0.7 + (100 if 答对 else 0) × 0.3
    // EWMA: 历史占 70%，最近一次占 30%
    // 例: 80 → 答对 → 80×0.7 + 100×0.3 = 86
    //     80 → 答错 → 80×0.7 + 0×0.3   = 56
```

算法位于 `submit_answer()` (subject_plan.py 行 862-904)：

```python
# 查询是否已有该知识点的掌握度记录
existing = await client.get(lookup_url, headers=headers)

if existing:
    row = existing[0]
    total_count = (row.get("total_count") or 0) + 1
    correct_count = (row.get("correct_count") or 0) + (1 if is_correct else 0)
    old_score = row.get("mastery_score") or 50
    new_score = round(old_score * 0.7 + (100 if is_correct else 0) * 0.3, 1)
    await client.patch(patch_url, headers=headers, json={...})
else:
    # 首次 INSERT
    await client.post(..., json={
        "mastery_score": 70.0 if is_correct else 30.0,
        "total_count": 1, ...
    })
```

### 5.1.6 错题本机制

```
单计划错题: GET /plans/{id}/mistakes
  → SELECT question_records WHERE is_correct=false + plan_id + user_id
  → 提取 question_id 列表
  → bank_get_by_ids(sid, ids) 从本地题库查题目详情
  → 返回 { mistakes: [{...record, question: {...}}] }

跨计划错题总览: GET /mistakes/overview
  → 查该用户所有 is_correct=false 记录
  → 用 Counter 统计每道题答错次数
  → 返回 { total_mistakes: N, unique_questions: M }

跨计划随机练习: GET /mistakes/practice
  → 查所有错题记录 → 按 plan_id 分组
  → 批量查询 plan_id → syllabus_id 映射 (单次 Supabase in() 查询)
  → 跨考纲 bank_get_by_ids() 查题目
  → random.shuffle() → 返回 limit 题
```

**N+1 优化**：跨考纲错题练习中，所有 plan_id 用 `in.()` 语法一次查询获取 syllabus_id 映射，避免了逐个请求。

---



### 5.2 AI 对话系统


基智内置两套 AI 对话系统，分别覆盖生产力场景和陪伴场景。

#### 5.2.1 主对话系统（ChatArea）—— 多智能体学习助手

位于首页 `/home`。用户发送消息后，系统自动进行**意图识别**，将请求路由到对应的专业 Agent。

**意图识别双轨策略**：

```
优先级 1: AI 分类 → POST /chat/detect-intent (temperature=0.1)
           → 返回 plan | generate | evaluate | chat
优先级 2: 前端关键词降级 → 匹配"规划/计划/安排"→plan
                         → 匹配"生成/出题/题目"→generate
                         → 匹配"评估/评价/批改"→evaluate
                         → 默认 → chat
```

**四 Agent 路由**：

| 意图 | Agent | 图标 | 调用的后端函数 | 功能 |
|------|-------|------|---------------|------|
| `plan` | 规划 Agent | 📋 | `plan_with_history_stream()` | 根据用户画像+历史生成 N 天备考计划 |
| `generate` | 生成 Agent | 📖 | `generate_with_history_stream()` | AI 出题，按知识点/难度生成题目 |
| `evaluate` | 评估 Agent | 🔍 | `evaluate_with_history_stream()` | 批改主观题，给出评分+反馈 |
| `chat` | 对话 Agent | 💬 | `call_llm_stream()` + 个性化 system prompt | 通用问答，注入用户学习阶段/强弱知识点 |

**流式响应流水线**：

```
1. 用户输入 → detectIntent (AI/keyword) → 确定 intent
2. 显示 "📋 Calling Plan Agent" 动画 (1 秒)
3. POST /chat/send { messages, intent, user_id, temperature }
   → 后端路由到对应 Agent → StreamingResponse (text/event-stream)
4. 前端 ReadableStream 逐块读取 → 打字机效果实时渲染
5. 完成 → "✅ Plan Agent Complete"
6. 后处理:
   - 首次对话 → /chat/title 生成标题 (≤20字)
   - generate 意图 → /chat/summary 提取摘要 → /chat/log 保存学习日志
   - 所有意图 → recordAction() 写入学程系统
```

**个性化系统提示**：

每次对话前从 Supabase 拉取用户画像并注入 system prompt：
- 学习阶段 (`learning_stage`) / 年级 (`grade`) / 专业 (`major`)
- 学习目标 (`learning_goal`) / 难度偏好 (`difficulty_preference`)
- 学习风格 (`learning_style`) / 每日学习时长 (`daily_study_time`)
- 弱知识点 TOP5 / 强知识点 TOP5
- 反幻觉规则（不确定时明确说"不确定"）

**会话管理（sessionStore）**：

- 存储：Pinia + `localStorage` (key: `jizhi-sessions`)
- 结构：`{ sessions: [{id, title, messages, createdAt}], currentSessionId }`
- 操作：新建 / 切换 / 删除 / 重命名（AI 生成标题）
- 限制：仅保存最近 20 条消息作为历史上下文发送

**API 端点（/chat 前缀）**：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/chat/detect-intent` | POST | AI 意图分类（temperature=0.1） |
| `/chat/send` | POST | 流式对话主端点，按意图路由到对应 Agent |
| `/chat/title` | POST | 从首轮对话生成标题（≤20 字） |
| `/chat/summary` | POST | 从 AI 回复提取摘要标签（≤15 字） |
| `/chat/log` | POST | 保存摘要到 Supabase learning_logs |
| `/chat/vision` | POST | 多模态图片理解（火山引擎豆包，流式 SSE 解析） |
| `/chat/advice` | POST | 从 prompt 生成学习建议（非流式） |

#### 5.2.2 小吉语音助手（XiaojiCall）—— 人格化 AI 伴侣

位于 `/xiaoji/call`，独立的全屏沉浸式体验。小吉拥有角色形象、语音输出、丰富交互反馈。

**5 种动画状态（useXiaojiAvatar composable）**：

| 状态 | 图片 | 触发条件 | 自动恢复 |
|------|------|---------|---------|
| idle | xiaoji_idle.png | 默认待命 | — |
| thinking | xiaoji_thinking.png | 等待 AI 响应 | 收到回复后 → speaking |
| speaking | xiaoji_speaking.png | AI 回复中 | 回复完成后 → happy |
| happy | xiaoji_happy.png | 完成任务 | 2 秒后 → idle |
| sleeping | xiaoji_sleeping.png | 离线/错误 | — |

**交互反馈**（~45 条随机短语库）：

- **单击** → 随机俏皮回应（"嘿嘿，干嘛~ 😄 想跟我聊天吗？"）
- **双击** → 幽默抗议（"救命！我被戳到不行了！"）
- **悬停** → 简短鼓励（"我在听呢 随时都在！"）
- **页面加载** → 随机问候（"你好呀~ 今天想学点什么？"）

每条短语自动 TTS 朗读 + 气泡弹窗（CSS 弹出动画 + 三角尾巴），3 秒自动消失。

**核心功能**：

| 功能 | 实现 | 说明 |
|------|------|------|
| 文字聊天 | `POST /community/xiaoji/chat` | 火山引擎豆包，temperature=0.8，最近 10 条消息为上下文 |
| 图片理解 | `POST /community/xiaoji/vision` | 豆包 Vision 多模态 |
| 语音合成 | 浏览器 `SpeechSynthesis` API | 中文 (zh-CN)，可开关 |
| 语音输入 | 浏览器 `SpeechRecognition` API | 中文识别 → 自动发送 |
| 题目评估 | `POST /community/xiaoji/evaluate-question` | 4 步 Agent 流水线 |
| 题集评估 | `POST /community/xiaoji/evaluate-set` | 综合评估含难度匹配/薄弱分析/学习建议 |

**题目评估 Agent 流水线**（评估时动画展示）：

```
理解 Agent (分析知识点) → 评估 Agent (判断难度等级)
  → 生成 Agent (生成解题思路) → 规划 Agent (制定学习建议)
每步 1.5 秒推进，进度条 + avatar 状态同步
```

**圆柱体滚动效果**：消息区采用半球渐变——远离底部的消息逐渐透明缩小，产生 3D 纵深感。

**消息卡片类型**：
- 文字消息 / 图片消息（点击放大）/ 题目卡片（标题+题型+难度+选项预览）
- 题集卡片（名称+题数+展开详情）/ 评估结果（📊 小基评价 + 格式化分析）

**设置页（XiaojiSettings）**：

| 设置项 | 可选值 |
|--------|--------|
| 名称 | 自定义文本 |
| 性格风格 | 温暖 / 幽默 / 正式 / 鼓励型 |
| 语音速度 | 滑块 1-9（映射 utterance.rate） |
| 音量 | 滑块 1-9 |
| 音色 | 标准女声/男声/童声/温柔女声/甜美女声/知性女声/年轻男声/活力女声（8 种） |
| 主动问候 | 开关 |
| 语音播报 | 开关 |

**后端文件**：`backend/routers/community/xiaoji.py`（~300 行），独立于主 Chat 系统。

#### 5.2.3 SSE 流式响应处理流水线

AI 对话和题目生成等均采用 **Server-Sent Events (SSE)** 协议实现流式输出。以下是全链路处理细节：

```
流式响应全链路
═══════════════════════════════════════════════════════════════════════

 前端 (ChatArea.vue)                后端 (chat.py)              AI 服务
 ┌───────────────────┐    ┌──────────────────────────┐    ┌──────────┐
 │                   │    │                          │    │          │
 │ 1. 用户输入消息    │    │ POST /chat/send          │    │          │
 │    + 意图识别      │───→│                          │    │          │
 │                   │    │ 2. 敏感词过滤              │    │          │
 │                   │    │    check_content_safety()  │    │          │
 │                   │    │                          │    │          │
 │                   │    │ 3. 获取用户画像            │    │          │
 │                   │    │    get_user_profile()     │    │          │
 │                   │    │                          │    │          │
 │                   │    │ 4. 路由 Agent:            │    │          │
 │                   │    │    intent == "plan"       │    │          │
 │                   │    │    → plan_with_history_   │    │          │
 │                   │    │      stream()             │───→│ DeepSeek │
 │                   │    │                          │    │  (SSE)   │
 │                   │    │ 5. StreamingResponse      │    │          │
 │                   │    │    media_type=            │←───│ 逐 token │
 │                   │    │    "text/event-stream"    │    │ 返回     │
 │                   │    │                          │    │          │
 │ 6. ReadableStream  │←───│  stream_generator():     │    │          │
 │    逐块读取         │    │    for chunk in stream:  │    │          │
 │                   │    │        yield chunk        │    │          │
 │ 7. 打字机渲染      │    │                          │    │          │
 │    text += chunk   │    │                          │    │          │
 │    scrollToBottom()│    │                          │    │          │
 │                   │    │                          │    │          │
 │ 8. 完成标记 ✅     │    │                          │    │          │
 │    后处理:         │    │                          │    │          │
 │    · /chat/title  │    │                          │    │          │
 │    · /chat/summary│    │                          │    │          │
 │    · /chat/log    │    │                          │    │          │
 │    · recordAction │    │                          │    │          │
 └───────────────────┘    └──────────────────────────┘    └──────────┘
```

**前端 ReadableStream 解析**（`ChatArea.vue` 关键逻辑）：

```javascript
// 1. 发起流式请求
const response = await fetch('/api/chat/send', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
  body: JSON.stringify({ messages, user_id, temperature, intent })
})

// 2. 获取 ReadableStream reader
const reader = response.body.getReader()
const decoder = new TextDecoder()
let buffer = ''

// 3. 循环读取
while (true) {
  const { done, value } = await reader.read()
  if (done) break

  buffer += decoder.decode(value, { stream: true })
  // 追加到消息文本，触发 Vue 响应式更新 → 打字机效果
  aiMessage.content += buffer
  buffer = ''
  await nextTick()
  scrollToBottom()
}
```

**豆包流式特殊处理**（`doubao_stream_generator()`）：

豆包（火山引擎）的 SSE 格式与 DeepSeek 不完全兼容，需要专门的解析器：

```python
def doubao_stream_generator(stream):
    """豆包返回格式: data:{"choices":[{"delta":{"content":"字"}}]}\n\n"""
    for line in stream:
        if line:
            if line.startswith("data:") and line != "data: [DONE]":
                try:
                    data = json.loads(line[5:])
                    if "choices" in data and len(data["choices"]) > 0:
                        delta = data["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]  # ← 逐字推送
                except Exception:
                    continue  # ← 单行解析失败不中断整体流
```

**故障恢复策略**：

| 故障场景 | 检测方式 | 恢复策略 |
|---------|---------|---------|
| AI 响应超时 (55s) | `httpx.ReadTimeout` | 返回错误提示"AI 响应超时，请重试" → 前端显示重试按钮 |
| 流中断（网络波动） | `reader.read()` 异常 | 保留已接收内容 + "[回复中断]" 标记 → 前端显示"继续"按钮 |
| JSON 解析失败 | JSONDecodeError | 降级为纯文本展示（不做结构化解析） |
| 意图识别失败 | `detect-intent` 异常 | 降级为 `intent=chat`，不阻塞对话流程 |
| 用户画像获取失败 | `get_user_profile()` 异常 | 使用默认画像（`learning_stage="未知"` 等），不影响对话 |

#### 5.2.4 个性化 System Prompt 构建流水线

每次对话请求进入 `/chat/send` 时，系统从 Supabase 拉取用户最新画像并动态构建 system prompt：

```
get_user_profile(user_id) 聚合流程
═══════════════════════════════════════════════════════════════

 ① 查询 profiles 表（学习基础信息）
    GET /rest/v1/profiles?id=eq.{uid}&select=learning_stage,grade,major,
        learning_goal,difficulty_preference,learning_style,daily_study_time
    → profile: { learning_stage: "大学", grade: "大三", major: "计算机科学", ... }

 ② 查询 questions 表（知识点掌握度数据）
    GET /rest/v1/questions?user_id=eq.{uid}&select=topic,mastery_score&limit=50
    → 按 topic 聚合 → 计算 topic 均值 → 排序

 ③ 计算强弱项 TOP5
    weak_topics  = [topic for topic in topics if avg_score < 50][:3]
    strong_topics = [topic for topic in topics if avg_score >= 80][:3]

 ④ 组装返回
    return {
      learning_stage, grade, major, learning_goal,
      difficulty_preference, learning_style, daily_study_time,
      weak_topics, strong_topics
    }

 ⑤ build_system_prompt(profile) 构建完整 prompt
    → 注入角色定义 + 用户背景 + 学习偏好 + 强弱项 + 防幻觉规则
```

**最终 System Prompt 示例**：

```
你是基智，一个热情、博学的AI学习助手。

用户背景：用户是 大学 · 大三 · 计算机科学。

学习偏好：学习目标：通过CET-4考试，偏好难度：中等，讲解偏好：详细讲解。

薄弱知识点：虚拟语气、定语从句。
擅长知识点：一般现在时、名词性从句。

## 行为准则：
1. 根据用户背景和偏好调整回答的深度和风格
2. 如果用户背景未知，保持通用回答
3. 优先关联用户薄弱知识点进行引导

## ⚠️ 防幻觉原则：
1. 不确定的直接说"我不确定"
2. 不编造事实、数据或代码
3. 部分了解时明确说明范围
```

**Agent 模式的 System Prompt 差异**：

| Agent | System Prompt 特点 | Temperature |
|-------|-------------------|-------------|
| Plan Agent | 强调"你是学习规划专家"，注入考纲结构 + 诊断数据 | 0.7 |
| Generate Agent | 强调"你是出题专家"，注入题型限制 + 难度范围 | 0.9 |
| Evaluate Agent | 强调"你是评分专家"，注入评分标准 + 输出 JSON 格式 | 0.3 |
| Chat Agent | 使用 `build_system_prompt()` 动态构建 | 0.7 (默认) |

#### 5.2.5 多模态集成（Vision）

`POST /chat/vision` 支持图片理解，当前实现使用**火山引擎豆包 Vision API**：

```
图片理解流程：
═════════════════════════════════════════════════

  用户上传图片 + 可选提问
      │
      ▼
  POST /chat/vision { user_id, image_url, question }
      │
      ├─ image_url: 前端将图片转为 base64 Data URL
      │   (支持 JPEG/PNG/GIF/WebP, ≤10MB → 前端压缩)
      │
      ├─ question: 默认 "请描述这张图片的内容"
      │   用户可自定义 (如 "这道题的正确答案是？")
      │
      ▼
  VolcClient.vision_stream(image_url, question)
      │
      ├─ POST https://ark.cn-beijing.volces.com/api/v3/chat/completions
      │   model: endpoint_id (视觉模型)
      │   messages: [{ role: "user", content: [
      │       { type: "image_url", image_url: { url: "data:image/..." }},
      │       { type: "text", text: question }
      │   ]}]
      │   stream: true
      │
      ▼
  StreamingResponse(doubao_stream_generator(stream))
      → 前端流式渲染
```

**支持场景**：
- 拍题搜答案：用户拍摄纸质试卷 → AI 识别题目 + 给出解答
- 公式 OCR：识别手写/印刷数学公式 → LaTeX 输出
- 图表理解：分析统计图表、流程图 → 文字描述 + 解读
- 多轮图片对话：连续发送多张图片，AI 关联上下文回答

#### 5.2.6 对话后处理与系统集成

每次 AI 回复完成后，前端自动执行后处理流水线：

```
对话后处理流水线（前端异步，不阻塞 UI）
═══════════════════════════════════════════════════════════════

  AI 回复完成 (流结束)
      │
      ├── 1. 首次对话 → POST /chat/title
      │       { user_id, content: 用户首条消息, response: AI 首条回复 }
      │       → call_llm(t=0.5) → "CET-4词汇辨析方法"
      │       → 存储到 sessionStore 作为对话标题
      │       → 失败降级: 取用户消息前20字 + "..."
      │
      ├── 2. generate 意图 → POST /chat/summary
      │       { user_id, content: AI 回复全文 }
      │       → call_llm(t=0.3) → "定语从句专项练习"
      │       → 提取 ≤15 字摘要标签
      │       → 失败降级: 取 AI 回复前15字
      │       ↓
      │    3. POST /chat/log
      │       { user_id, keyword: 摘要标签 }
      │       → 写入 learning_logs 表 (data[] JSONB)
      │       → 时间线中可见 ("定语从句专项练习 - 今天 14:30")
      │
      ├── 4. 所有意图 → recordAction()
      │       POST /career/actions/record { action_type: "chat", metadata: {...} }
      │       → 学程系统计数 (chats 累计、今日消息数)
      │       → 触发成就检查 (messages_500 等)
      │
      └── 5. 敏感内容回扫（异步）
              对 AI 回复做 check_content_safety()
              → 不通过: 标记警告但不删除（人工审核）
```

**各意图后处理差异**：

| 意图 | 标题生成 | 摘要提取 | 日志保存 | 学程记录 |
|------|---------|---------|---------|---------|
| plan | ✅ | — | — | ✅ action_type="use_plan_agent" |
| generate | ✅ | ✅ | ✅ | ✅ action_type="generate_question" |
| evaluate | ✅ | — | — | ✅ action_type="use_evaluate_agent" |
| chat | ✅ | — | — | ✅ action_type="chat" |

---

### 5.3 学程系统


学程是平台的**游戏化激励体系**，通过段位、等级、任务、成就四个维度将学习行为转化为可视化成长路径。采用中国传统文化"求学问道"隐喻——播种、施肥、发芽、拾贝。4 个子页面共用 `CareerSidebar`。

```
学程系统整体数据流
═══════════════════════════════════════════════════════════════

  用户操作 (全平台)              action记录               积分计算 & 晋升
  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
  │ 做题              │    │                  │    │                  │
  │ 对话              │    │ POST /career/    │    │ user_stats 表     │
  │ 打卡              │───→│   actions/record │───→│ points (段位分)   │
  │ 计时器完成         │    │                  │    │ level_points     │
  │ 生成题目           │    │ { action_type,   │    │ (等级分)          │
  │ 创建题集           │    │   user_id,       │    │                  │
  │ 查看报告           │    │   metadata }     │    │ rank (段位)       │
  │ 分享              │    │                  │    │ sub_rank (小段)   │
  │ 消息              │    │ → user_actions   │    │ is_legend        │
  └──────────────────┘    │   表 (原始日志)   │    └────────┬─────────┘
                          └──────────────────┘             │
                                                           │ 计算晋升
  任务系统                    成就系统                      ▼
  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
  │ 播种 (新手/17个)  │    │ 25 个成就         │    │ rank_history[]   │
  │ 施肥 (每日/36池)  │    │ first_checkin     │    │ 保留最近 50 条   │
  │ 发芽 (长期/21个)  │    │ rank_zhizhi       │    │                  │
  │                  │    │ questions_100     │    │ 前端检测晋升      │
  │ 领取 → claim 表  │    │ ...               │    │ → 升级弹窗       │
  │ → stats/update   │    │                  │    │ → 粒子动画       │
  │ → bonus/claim    │    │ 领取 → achievements│   │                  │
  │                  │    │ 表 → stats/update │    │                  │
  └──────────────────┘    └──────────────────┘    └──────────────────┘

  CareerSidebar (30s 轮询)
  ┌──────────────────────────────────────────────────────┐
  │ GET /career/stats/{user_id}                          │
  │ → 段位图标 + 小段符号 + 积分显示                      │
  │ GET /career/task-progress/{user_id}                  │
  │ → 待领取任务数 红色角标                               │
  │ → 待领取成就数 红色角标                               │
  └──────────────────────────────────────────────────────┘
```

#### 5.3.1 双轨积分体系

两套积分独立运行、并行推进：

**段位积分 (`points`)**：来自任务 `reward` 和成就奖励，驱动段位晋升。

| 段位 | 最低积分 | 小段区间 | 图标 | 颜色 | 权重 |
|------|---------|---------|------|------|------|
| 启程 (Qicheng) | 0 | 0-499 | ◈ | #8B8B8B 灰 | 1 |
| 求索 (Qiusuo) | 500 | 500-999 | ❖ | #4FC3F7 蓝 | 2 |
| 明理 (Mingli) | 1,000 | 1,000-1,499 | ✧ | #4CAF50 绿 | 3 |
| 致知 (Zhizhi) | 1,500 | 1,500-1,999 | ⬖ | #FF9800 橙 | 4 |
| 笃行 (Duxing) | 2,000 | 2,000-2,499 | ⬡ | #CE93D8 紫 | 5 |
| 臻境 (Zhenjing) | 2,500 | 2,500-4,999 | ◆ | #FFD54F 金 | 6 |
| 传说 (Legend) | 5,000 | — (无小段) | ★ | #FF6B6B 红 | 7 |

**小段计算**：每大段 500 分 ÷ 5 小段 = 每小段 100 分。

```
sub = floor((points - rank_base) / 100) + 1  (capped at 5)
符号: ○(V) ◌(IV) ◎(III) ◍(II) ●(I)
```

**晋升触发**：`new_rank ≠ old_rank` 或 `new_sub ≠ old_sub` 时，记录到 `rank_history[]`（保留最近 50 条），前端弹出毛玻璃升级弹窗（自动消失 2.5 秒）。

**等级积分 (`level_points`)**：来自任务 `value` 值，驱动等级提升。等差数列公式：

```
Lv.n 所需总分 = Σ(i+1) for i=1..n  (三角数)
例: Lv.1=2, Lv.2=5, Lv.3=9, Lv.4=14, Lv.5=20, Lv.10=65
```

**等级进度**：
```
currentNeeded = level + 1
currentProgress = levelPoints - Σ(i+1) for i=1..(level-1)
levelProgress = min(100, currentProgress / currentNeeded × 100)%
```

#### 5.3.2 三阶任务体系

所有任务进度由 `user_actions` 表动态计算（每次操作 → `POST /career/actions/record`）。

**播种任务（新手）**：17 个一次性任务，覆盖首次使用各功能。例如：

| 任务 | action | reward | value |
|------|--------|--------|-------|
| 首次登录 | first_login | 5 | 1 |
| 设置昵称 | first_nickname | 10 | 1 |
| 设置头像 | first_avatar | 10 | 1 |
| 首次对话 | first_chat | 15 | 2 |
| 首次出题 | first_generate | 20 | 3 |
| 首次评估 | first_evaluate | 20 | 3 |
| 首次打卡 | first_checkin | 10 | 2 |
| 首次完成题目 | first_complete_question | 15 | 2 |
| 首次创建题集 | first_create_set | 20 | 3 |

进度：二进制（100% 或 0%），记录过即 100%。领取后永久标记"已领取"。

**施肥任务（每日）**：池 36 个，每日随机展示 5 个。例如：

| 任务 | target | reward | value |
|------|--------|--------|-------|
| 发送 5 条消息 | 5 | 10 | 1 |
| 发送 10 条消息 | 10 | 15 | 2 |
| 发送 20 条消息 | 20 | 20 | 3 |
| 做 3 道题 | 3 | 15 | 2 |
| 做 8 道题 | 8 | 25 | 3 |
| 做 15 道题 | 15 | 40 | 5 |
| 学习 15 分钟 | — | 15 | 2 |
| 学习 30 分钟 | — | 25 | 3 |
| 生成 1 道题 | 1 | 15 | 2 |
| 生成 3 道题 | 3 | 25 | 3 |

- 进度 = `min(100%, today_count / target × 100%)`
- 可换一批（日限 1 次），从池中排除当前 5 个后重新随机
- **全部 5 个完成奖励**：+20 段位分 +30 等级分（`POST /career/bonus/claim`）

**发芽任务（长期）**：21 个阶梯式累计任务，设 `requires` 前置链：

| 任务 | 前置 | reward | value |
|------|------|--------|-------|
| 累计打卡 3 天 | — | 30 | 3 |
| 累计打卡 7 天 | checkin_3 | 60 | 4 |
| 累计打卡 30 天 | checkin_7 | 150 | 5 |
| 累计打卡 100 天 | checkin_30 | 300 | 7 |
| 累计答 50 题 | — | 40 | 5 |
| 累计答 100 题 | questions_50 | 80 | 6 |
| 累计答 500 题 | questions_100 | 200 | 8 |
| 累计答 1000 题 | questions_500 | 400 | 10 |
| 累计生成 10 题 | — | 30 | 4 |
| 累计生成 50 题 | generate_10 | 80 | 6 |
| 累计生成 200 题 | generate_50 | 200 | 8 |

进度 = `min(100%, total_count / target × 100%)`。未解锁前置任务时显示"🔒 需先完成 XXX"。

#### 5.3.3 领取动画流水线

领取任务/成就时触发完整动画序列：

```
1. 粒子爆散 (25 颗 ★/✦，随机颜色/大小/角度，~900ms)
2. 金币飞行 (🪙 从领取按钮弧线飞入顶部积分栏，旋转 720°，~600ms)
3. 屏幕闪光 (白色 overlay 淡入淡出)
4. 分数跳动 (积分数字 scale 放大)
5. 毛玻璃 Toast (获得的 rank + level 分弹出)
6. 若触发晋升 → 升级弹窗 ("启程 V → 启程 IV"，2.5 秒自动消失)
7. window.dispatchEvent('task-claimed') → CareerRank 页面实时刷新
```

#### 5.3.4 25 个成就

| ID | 名称 | 条件 | reward | value |
|----|------|------|--------|-------|
| first_checkin | 初入书海 | 首次打卡 | 20 | 5 |
| checkin_7 | 持之以恒 | 打卡 7 次 | 50 | 6 |
| checkin_30 | 勤耕不辍 | 打卡 30 次 | 150 | 7 |
| first_chat | 初试锋芒 | 首次对话 | 15 | 4 |
| first_plan | 思维缜密 | 首次使用规划 Agent | 20 | 5 |
| first_generate | 妙笔生花 | 首次生成题目 | 20 | 5 |
| first_evaluate | 明察秋毫 | 首次使用评估 Agent | 20 | 5 |
| questions_100 | 百题斩 | 答 100 题 | 100 | 6 |
| questions_1000 | 千题斩 | 答 1000 题 | 300 | 9 |
| mistakes_10 | 错题猎手 | 攻克 10 道错题 | 80 | 6 |
| mistakes_100 | 错题克星 | 错题 100 道 | 200 | 9 |
| sets_5 | 题集收藏家 | 创建 5 个题集 | 50 | 6 |
| sets_20 | 题集达人 | 创建 20 个题集 | 150 | 7 |
| sets_50 | 筑梦者 | 创建 50 个题集 | 300 | 8 |
| rank_mingli | 学有所成 | 达明理段位 | 100 | 7 |
| rank_zhizhi | 融会贯通 | 达致知段位 | 150 | 8 |
| rank_duxing | 独当一面 | 达笃行段位 | 200 | 8 |
| rank_zhenjing | 臻于至善 | 达臻境段位 | 300 | 9 |
| legend | 传说 | 达传说段位 | 500 | 10 |
| share_10 | 分享达人 | 分享 10 次 | 80 | 6 |
| study_7 | 学习狂人 | 连续学习 7 天 | 100 | 7 |
| timer_10h | 时间管理 | 计时器累计 10h | 120 | 7 |
| logs_50 | 知识沉淀 | 50 条学习日志 | 100 | 6 |
| report_10 | 学海无涯 | 查看 10 次报告 | 80 | 6 |
| messages_500 | 对话大师 | 发送 500 条消息 | 150 | 7 |

**状态视觉**：🔒 锁定（灰暗低透明度）→ ✨ 待领取（金色脉冲光晕 + "领取"按钮）→ ✅ 已解锁（绿色勾 + 完成日期）。

**前端页面**：`CareerAchievements.vue` 每张成就卡片含自定义 PNG 图标（`/assets/achievements/`）、进度条、点击展开详情弹窗。

#### 5.3.5 数据表与 API

**Supabase 表**：
- `user_stats` — `{user_id, points, level_points, rank, sub_rank, is_legend, achievements[], rank_history[]}`
- `user_actions` — `{user_id, action_type, action_at, metadata}` 原始操作日志
- `user_achievements` — `{user_id, achievement_id, created_at}`
- `user_task_claims` — `{user_id, task_id, task_type}`

**后端 API（/career 前缀，`routers/career.py`）**：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/stats/{user_id}` | GET | 获取段位/等级/成就/晋升历史（首次访问自动创建记录） |
| `/stats/update` | POST | `{points_change, level_points_change}` → 重新计算 rank/sub/level |
| `/task-progress/{user_id}` | GET | 三类任务 + 成就全部进度（动态计算） |
| `/task/claim` | POST | 领取任务 → 写 claims 表 → 调用 stats/update |
| `/bonus/claim` | POST | 领取每日五任务奖励（+20 rank +30 level） |
| `/achievement/claim` | POST | 领取成就 → 检查未重复 → 写入 achievements 表 → stats/update |
| `/actions/record` | POST | 记录操作 `{action_type, metadata}` |
| `/actions/{user_id}` | GET | 获取操作历史 |
| `/actions/stats/{user_id}` | GET | 操作统计（总计各类型/今日各类型/首次标记） |

**侧边栏集成**：`CareerSidebar` 每 30 秒轮询 `getSidebarBadges()` 获取待领取任务数和待领取成就数，显示为红色角标。

---


### 5.4 社区模块


轻量化学习社交空间。8 个子路由挂在 `/community` 下，共用 `CommunitySidebar`（7 项导航 + 好友请求/消息角标每 30 秒轮询）。

#### 5.4.1 动态广场（CommunityFeed）

**发布**：标题 + 正文（500 字上限）+ 逗号分隔标签 + 单图上传（base64 Data URL）。提交时自动提取 `#话题` + 敏感词过滤。

**信息流**：
- 全部动态 / 好友动态 双筛选
- 关键词搜索（防抖）
- 分页加载（"加载更多"按钮）

**互动操作**：

| 操作 | 实现 | 视觉 |
|------|------|------|
| 点赞 | 乐观更新（本地先切换）→ `POST /community/post/{id}/like` → `like_count++` | ❤ 红色高亮 |
| 取消赞 | `DELETE /community/post/{id}/like` → `like_count--` | ❤ 灰色 |
| 收藏 | `POST /community/post/{id}/collect` → `collect_count++` | 🔖 橙色高亮 |
| 取消收藏 | `DELETE /community/post/{id}/collect` | 🔖 灰色 |
| 评论 | `POST /community/post/{id}/comment`（支持 `parent_id` 嵌套回复） | 展开评论区 |
| 举报 | 选择原因 → `POST /community/report` → 写入 `reports` 表 + 发邮件给管理员 | — |
| 删除 | 仅自己帖子 → `DELETE /community/post/{id}` → `ElMessageBox` 确认 | — |

**PostCard 组件**：统一卡片样式——头像(点击→用户主页) / 昵称 / 相对时间("3分钟前"/"2天前") / 更多菜单(举报/删除) / 标题 / 正文(pre-wrap) / #标签(可点击) / 图片缩略图(100×100→点击放大 via `el-image-viewer`) / 互动栏(赞数+评论数+收藏数)。

**后端优化**：帖子列表批量查询 likes/collects/comments（单次 HTTP 获取所有帖子的互动数据，避免 N+1）。

#### 5.4.2 好友系统（CommunityFriends）

**三栏 Tab**：

| Tab | 功能 |
|-----|------|
| 好友列表 | 小吉 AI 置顶（特殊蓝卡 → 点击跳 `/xiaoji/call`）+ 真实好友（头像/昵称/账号/在线绿点 → 聊天/删除） |
| 好友请求 | 待处理请求列表（头像/昵称/时间 → 接受/拒绝），角标实时更新 |
| 搜索用户 | 按账号搜索 → 结果标注状态（已是好友 / 已发送请求 / 添加好友） |

**好友关系**：双向查询（`WHERE user_id=x OR friend_id=x`），状态 `pending → accepted → rejected`。

**30 秒轮询**保持在线状态和请求列表最新。

#### 5.4.3 私聊（CommunityChat）

**消息类型**：

| 类型 | 实现 | 视觉 |
|------|------|------|
| 文本 | 右对齐蓝底（我方）/ 左对齐灰底（对方） | 气泡 |
| 图片 | base64 传输 → 缩略图 → 点击 `el-image-viewer` 放大 | 带阴影圆角 |
| 题目卡片 | 含 `question_data` 完整题目 JSON → 标题+题型徽章+难度+内容预览 | 可点击 → 跳转 `/do-question/{id}` |

**题目分享**：从生成历史或题集选择题目 → 以完整 JSON 嵌入消息 → 接收方直接做题。

**语音输入**：浏览器 `SpeechRecognition` API（zh-CN）→ 识别结果自动填入并发送。

**小吉模式**：与小吉对话时切换 API → `POST /community/xiaoji/chat`（火山引擎豆包）→ TTS 朗读回复。

#### 5.4.4 好友排行（Rank）

- 数据源：`GET /community/friends/rank`（好友 + 本人）
- 排序：段位权重（传说 7→启程 1）→ 小段（V→I）→ 积分
- 前三名 🥇🥈🥉 金银铜底色 + 本人蓝色边框 "(我)"

#### 5.4.5 学习成果卡（CommunityProfileCard）

**暗色主题卡片**内容：
- 几何 SVG 装饰（多边形/圆形/线条/点）+ 5 色渐变背景
- 4 个彩色光晕（蓝/紫/粉/绿 glow blob）
- 72px 头像 + 渐变边框 + 昵称 + 账号 + 简介（引用线）
- 等级/段位/积分 徽章
- 统计行：总积分 / 学习天数 / 成就数 / 打卡天数
- 知识点掌握度色卡（红→绿 20 级渐变，每张标签：薄弱/待巩固/优势）
- 成就徽章（图标+名称，主题色背景）
- 最近 5 条活动（图标+文字+相对时间）

**自定义**：可选展示知识点（最多 10）+ 成就（最多 8），保存到 `profile_card_settings` 表。

**导出**：html2canvas (4x scale) + jsPDF → PNG/PDF（`基智学习成果卡_{昵称}.png`）。

#### 5.4.6 后端架构

`backend/routers/community/` 下设 5 个子路由（`__init__.py` 组合挂载在 `/community` 前缀）：

```
community/ 包结构
═══════════════════════════════════════════════════════

  __init__.py (路由组装)
  ┌───────────────────────────────────────────────────┐
  │ router = APIRouter(prefix="/community")           │
  │ router.include_router(posts.router)               │
  │ router.include_router(friends.router)            │
  │ router.include_router(messages.router)           │
  │ router.include_router(notifications.router)      │
  │ router.include_router(xiaoji.router)  ← 独立挂载  │
  └───────────────────────────────────────────────────┘
           │          │          │          │
           ▼          ▼          ▼          ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
  │ posts.py │ │friends.py│ │messages  │ │xiaoji.py     │
  │          │ │          │ │.py       │ │              │
  │ 动态广场  │ │ 好友系统  │ │ 私聊     │ │ 小吉助手     │
  │ 点赞收藏  │ │ 请求排行  │ │ 题集分享  │ │ 评估流水线   │
  │ 评论举报  │ │ 在线状态  │ │ 语音消息  │ │ TTS/ASR     │
  └──────────┘ └──────────┘ └──────────┘ └──────────────┘
                          │
                          ▼
                  ┌──────────────┐
                  │notification  │
                  │s.py          │
                  │ 消息中心      │
                  │ 每日生成      │
                  └──────────────┘
```

| 文件 | 职责 | 端点数 |
|------|------|--------|
| `posts.py` | 动态 CRUD + 点赞/收藏/评论 + 批量查询优化 | ~10 |
| `friends.py` | 好友关系/请求/搜索/排行 | ~7 |
| `messages.py` | 私聊/题集分享(接受/拒绝)/举报(含邮件通知)/收藏/资料卡 | ~12 |
| `xiaoji.py` | 小吉聊天/视觉/TTS/ASR/题目评估/题集评估/流式评估 | ~13 |
| `notifications.py` | 消息中心/角标/通知设置/每日生成（见 5.8） | ~10 |
| `models.py` | Pydantic schema 定义 | — |

**批量查询优化模式**（以帖子列表为例）：

```python
# ❌ N+1 问题：逐帖查询互动数据
for post in posts:
    likes = await get_likes(post.id)    # 每个帖子 1 次 HTTP 请求
    collects = await get_collects(post.id)
    comments = await get_comments(post.id)

# ✅ 批量查询：1 次 HTTP 请求获取所有帖子的互动数据
post_ids = [p["id"] for p in posts]
likes = await client.get(
    f"/post_likes?post_id=in.({','.join(post_ids)})"
)
# Supabase in() 语法：多个值用逗号分隔，单次查询返回所有结果
# 然后在 Python 中按 post_id 分组分发到各帖子
```

**好友排行算法**：
```python
# GET /community/friends/rank
# 1. 获取好友列表 + 本人
friend_ids = [...] + [current_user]

# 2. 批量查好友的 user_stats
stats = await client.get(
    f"/user_stats?user_id=in.({','.join(friend_ids)})"
)

# 3. 排序：段位权重 DESC → 小段 DESC → 积分 DESC
RANK_WEIGHTS = {
    "legend": 7, "zhenjing": 6, "duxing": 5,
    "zhizhi": 4, "mingli": 3, "qiusuo": 2, "qicheng": 1
}

def sort_key(stat):
    rank_w = RANK_WEIGHTS.get(stat.get("rank", ""), 0)
    sub_w = 5 - (stat.get("sub_rank") or 1)  # V=4, IV=3, III=2, II=1, I=0
    return (rank_w, sub_w, stat.get("points", 0))

sorted_stats = sorted(stats, key=sort_key, reverse=True)
```

**举报邮件通知**：
```python
# 用户举报 → 后端处理:
# 1. 写入 content_reports 表
# 2. 异步发送邮件给管理员
asyncio.create_task(
    send_email(
        to=settings.EMAIL_RECEIVER,
        subject=f"[举报] {reporter_name} 举报了 {target_type}",
        body=f"举报人: {reporter_name}\n"
             f"举报类型: {target_type}\n"
             f"举报原因: {reason}\n"
             f"投诉对象ID: {target_id}\n"
             f"处理链接: {FRONTEND_URL}/admin/reports"
    )
)
# 邮件发送失败不影响举报提交
```

所有用户内容经 `sensitive_words.check_content_safety()` 过滤。

---


### 5.5 资源库


位于 `/resource-lib`，是学习内容的创作和管理中心。顶部掌握度看板 + 5 个功能 Tab。

#### 5.5.1 掌握度看板

数据源：`GET /questions/mastery/{user_id}` → 按 `normalized_topic` 聚合，返回 `[{topic, mastery_score, question_count}]`。

**统计指标**：
- 总知识点数 `totalTopics`
- 已掌握 (≥80%) `masteredTopics`
- 薄弱 (<60%) `weakTopics`
- 平均掌握度 `avgMastery`

**展示**：
- 红→绿 20 级渐变色条（`#FF0000` → `#006600`，每 5 分一阶）
- 三个比例条：薄弱(红) / 待巩固(黄) / 优势(绿) 百分比
- 最薄弱 4 个知识点卡片（渐变红底 → "攻克"按钮 → 跳转 `/generate-from-mastery?topic=X`）

#### 5.5.2 五大功能 Tab

**生成题目（GenerateForm）**：

选分类/知识点/题型（choice/fill/cloze/translation/essay/short_answer/programming）/难度（简单=2.0/中等=6.0/困难=8.5）/额外备注 → `POST /questions/generate` → DeepSeek 出题（temperature=0.9）→ 写入 `questions` 表 + `generation_history` 表 → `recordAction('generate_question')` → 跳转 `/do-question`。

**我的题集（QuestionSets）**：

- 创建：名称 + 描述 + 类型 → 写入 `question_sets` 表
- 管理：添加/移除题目，按掌握度排序
- 掌握度：客户端遍历题目 mastery_score 取加权平均
- 进度条：红→绿渐变色
- 分享：`POST /community/share/set` 发送给好友 → 好友接收后 " (来自分享)" 后缀保存

**错题本（MistakeBook）**：

```
收录: mastery_score < 60 → is_mistake=true, mistake_status="learning"
攻克: 再次作答 mastery_score ≥ 60 → mistake_status="conquered"
```

双 Tab："学习中" / "已攻克"。每道错题显示题目 + 你的答案 + 正确答案 + "复习"按钮 → 跳转做题。

**生成历史（GenerationHistory）**：所有 AI 生成题目列表，按题型筛选 + 关键词搜索 + 分页。状态：待练习 / 已练习 / 已掌握。

**评估中心**：内嵌 4 张快捷卡片（学情报告/维度宇宙/评估表/学习建议）→ 点击跳转对应页面。

#### 5.5.3 错题本机制（学科计划侧）

在学科计划详情页的"错题本"Tab 中：

```
单计划错题: GET /plans/{plan_id}/mistakes
  → 查 question_records WHERE is_correct=false AND plan_id=...
  → 提取 question_id → bank_get_by_ids() 从本地题库取题目详情
  → 返回 { mistakes: [{record, question}] }

跨考纲错题总览: GET /mistakes/overview
  → 查所有 is_correct=false 记录 → 按 question_id 计数

跨考纲随机练习: GET /mistakes/practice?limit=10
  → 批量查 plan→syllabus 映射 (Supabase in() 单次查询)
  → 跨考纲查题 → shuffle → 返回
```

#### 5.5.4 知识点掌握度算法（EWMA）

```
IF 首次答题该知识点:
    mastery_score = 70.0 (答对) 或 30.0 (答错)
    total_count = 1, correct_count = 1 或 0

ELSE:
    total_count += 1
    correct_count += (1 if 答对 else 0)
    mastery_score = mastery_score × 0.7 + (100 if 答对 else 0) × 0.3
```

历史权重 70%，最近一次 30%。防止一次失误/超常发挥剧烈波动。存储于 `user_kp_mastery` 表（`UNIQUE(user_id, plan_id, kp_name)` 保证每个知识点仅一行）。

#### 5.5.5 题目生成 Agent 流水线

```
POST /questions/generate 全链路
═══════════════════════════════════════════════════════════════

 前端 GenerateForm
 ┌──────────────────────────┐
 │ 分类: [vocabulary ▼]     │
 │ 知识点: [高频核心词]      │
 │ 题型: [choice ▼]         │
 │ 难度: [●●●○○] 6.0       │
 │ 额外备注: "侧重近义词辨析" │
 │ [🚀 生成题目]            │
 └──────────┬───────────────┘
            │ POST /questions/generate
            ▼
 后端 questions.py
 ┌──────────────────────────────────────────────────────────┐
 │                                                          │
 │ 1. 构建 AI Prompt（模板注入）                              │
 │    prompt = f"""                                         │
 │    你是一位专业的出题老师。请生成一道{category}题目：        │
 │    - 题型: {question_type_label}                         │
 │    - 知识点: {topic}                                     │
 │    - 难度: {difficulty_score}/10                         │
 │    - 额外要求: {extra_notes}                             │
 │                                                          │
 │    返回 JSON: {{                                         │
 │      "title": "...",                                     │
 │      "question_type": "{question_type}",                 │
 │      "options": {{"A": "...", "B": "...", ...}},        │
 │      "answer": "A",                                      │
 │      "explanation": "...",                               │
 │      "hint": "..."                                       │
 │    }}                                                    │
 │    """                                                   │
 │                                                          │
 │ 2. call_llm(prompt, temperature=0.9)  ← 高温度增加多样性   │
 │                                                          │
 │ 3. extract_json_from_response(ai_resp)                   │
 │    ├─ 找第一个 { 和最后一个 }                              │
 │    ├─ json.loads()                                       │
 │    └─ JSONDecodeError → 返回错误提示                       │
 │                                                          │
 │ 4. 敏感词过滤                                             │
 │    check_content_safety(title + content + answer)         │
 │    → 不通过: HTTP 400 + "生成内容包含敏感信息"              │
 │                                                          │
 │ 5. 写入 Supabase                                         │
 │    POST /rest/v1/questions {                             │
 │      user_id, title, question_type, difficulty_score,    │
 │      category, topic, options, answer, explanation,      │
 │      hint, source: "generated", parent_id: null          │
 │    }                                                     │
 │                                                          │
 │ 6. 写入生成历史                                           │
 │    POST /rest/v1/generation_history {                    │
 │      user_id, question_id, topic, question_type,         │
 │      difficulty_score, created_at                        │
 │    }                                                     │
 │                                                          │
 │ 7. 记录学程动作                                           │
 │    POST /career/actions/record {                         │
 │      action_type: "generate_question"                    │
 │    }                                                     │
 │                                                          │
 │ 8. 返回 → 前端跳转 /do-question/{new_id}                  │
 └──────────────────────────────────────────────────────────┘
```

**AI 出题的 JSON 容错提取**（`extract_json_from_response()`）：

```python
def extract_json_from_response(response: str) -> dict:
    text = response.strip()
    # 策略 1: 找第一个 { 和最后一个 }
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1:
        raise ValueError("未找到 JSON 对象")
    json_str = text[start:end + 1]
    # 策略 2: 尝试直接解析
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # 记录失败详情但不做更多修复（与题库批量生成不同，单题生成失败直接报错)
        raise ValueError(f"JSON 解析失败")
```

**与批量题库生成的区别**：

| 维度 | 单题生成 (`/questions/generate`) | 批量生成 (`seed_all_banks.py`) |
|------|----------------------------------|-------------------------------|
| 触发方式 | 用户手动，UI 交互 | 脚本执行，命令行触发 |
| 生成量 | 1 题/次 | 按批次 (BATCH_SIZE=6)，可达数千题 |
| Temperature | 0.9（高多样性） | 0.7（平衡质量和多样性） |
| JSON 容错 | 简单提取（失败直接报错） | 多层容错链（括号计数+回退+剥离+类型过滤） |
| 存储位置 | Supabase `questions` 表 | 本地 JSON 文件 (`data/*.json`) |
| 去重 | 无（用户手动生成不检查重复） | UUID + ID 去重 |

#### 5.5.6 资源库数据模型与持久化策略

**涉及的 Supabase 表**：

| 表名 | 用途 | 关键列 | 索引 |
|------|------|--------|------|
| `questions` | AI 生成题目 + 用户创建的题目 | `user_id, topic, question_type, difficulty_score, mastery_score` | `user_id`, `topic` |
| `question_sets` | 用户创建的题集 | `user_id, name, description, set_type, question_ids[]` | `user_id` |
| `generation_history` | 题目生成记录（用于历史Tab） | `user_id, question_id, topic, question_type, difficulty_score` | `user_id`, `created_at DESC` |
| `learning_logs` | 学习日志 | `user_id, data (JSONB)` | `user_id` |

**掌握度看板数据聚合流程**：

```
GET /questions/mastery/{user_id}
═══════════════════════════════════════════════════════

  ① 查询 questions 表
     GET /rest/v1/questions?user_id=eq.{uid}
        &select=topic,mastery_score,normalized_topic
        &order=created_at.desc&limit=200

  ② 按 normalized_topic 分组聚合
     topics = {}
     for q in questions:
         nt = q.get("normalized_topic") or q.get("topic") or "未分类"
         if nt not in topics:
             topics[nt] = { "scores": [], "count": 0 }
         topics[nt]["scores"].append(q.get("mastery_score", 0))
         topics[nt]["count"] += 1

  ③ 计算每个 topic 的统计值
     result = []
     for topic_name, data in topics.items():
         avg_score = sum(data["scores"]) / len(data["scores"])
         result.append({
             "topic": topic_name,
             "mastery_score": round(avg_score, 1),
             "question_count": data["count"]
         })

  ④ 排序 → 返回
     return sorted(result, key=lambda x: x["mastery_score"])
```

**前端色阶映射（红→绿 20 级）**：

```javascript
// mastery_score: 0-100
// 色阶: #FF0000 (0分, 红) → #FF9900 (25分) → #CCFF00 (50分) → #33CC00 (75分) → #006600 (100分, 绿)
function getMasteryColor(score) {
  const ratio = score / 100
  // 红色分量: 255→0
  const r = Math.round(255 * (1 - ratio))
  // 绿色分量: 0→102
  const g = Math.round(102 * ratio)
  return `rgb(${r}, ${Math.max(0, Math.round(255 * (0.5 - Math.abs(ratio - 0.5) * 2)))}, ${g})`
}
```

**题集管理的数据流**：

```
创建题集:
  POST /questions/sets { name, description, set_type }
  → INSERT INTO question_sets → 返回 set_id

添加题目:
  PUT /questions/sets/{set_id} { question_ids: [...new_ids] }
  → 读取当前 question_ids → 合并去重 → PATCH 更新

删除题目:
  PUT /questions/sets/{set_id} { question_ids: 过滤后的ids }
  → 过滤掉要删除的 id → PATCH 更新

掌握度计算:
  客户端遍历 question_ids → 逐题查 mastery_score → 取加权平均

分享题集:
  POST /community/share/set { friend_id, set_data }
  → 好友接收后保存为 "题集名 (来自分享)" → 写入好友的 question_sets
```

**GenerationHistory 的状态机**：

```
题目状态流转:
  generated ──→ practiced ──→ mastered
  (AI生成)     (用户做过)     (掌握度≥80%)

状态判定逻辑（客户端）:
  for each generation:
      question = findQuestion(generation.question_id)
      if !question: status = "generated"            // 题目可能已被删除
      else if question.mastery_score >= 80: status = "mastered"
      else if question.last_practiced_at: status = "practiced"
      else: status = "generated"
```

---


### 5.6 评估中心


位于 `/evaluation-center`，学习诊断和规划的总入口。三张渐变毛玻璃卡片作为导航枢纽。

#### 5.6.1 学情报告（EvaluationReport）

路由 `/evaluation-report`，数据源 `GET /questions/mastery/{user_id}`。

**4 项统计卡片**：总知识点 / 已掌握(≥80%) / 薄弱(<60%) / 平均掌握度(%)

**三层分布比例条**：薄弱(红) / 待巩固(黄) / 优势(绿)，各带百分比

**知识点详情列表**：筛选（全部/薄弱/待巩固/优势）+ 搜索 → 每条含名称 + 20 级色条 + 百分比 + 状态徽章

**近期活动时间线**：checkin / answer_question / generate_question / achievement_unlocked / set_created / timer_completed / mistake_conquered / level_up / rank_up / chat / view_report — 各有对应 emoji 图标

**PDF 导出**：html2canvas (2x scale, #1a1a2e 底色) + jsPDF → 多页 A4 切片（10mm 边距）

#### 5.6.2 评估表（EvaluationTable）

路由 `/evaluation-table`，数据源 `GET /evaluation/profile-data?user_id=...`。

**综合评分环**：SVG 圆环进度（0-100 分）→ 动画光晕 + 五级评价：

| 评分 | 等级 | 颜色 |
|------|------|------|
| ≥85 | 巅峰期 | #FFD700 金 |
| ≥70 | 卓越期 | #8B5CF6 紫 |
| ≥50 | 精进期 | #409EFF 蓝 |
| ≥30 | 筑基期 | #F59E0B 琥珀 |
| <30 | 开拓期 | #EF4444 红 |

**六维雷达图（K-C-E-G-I-P）**：

| 维度 | 评分逻辑 | 颜色 |
|------|---------|------|
| **K 知识基础** | `questions` 表所有 topic 的 mastery_score 取均值 (0-100) | #409EFF 蓝 |
| **C 认知风格** | `generation_history` 题型分布：选择题>55%→视觉型, >30%→综合型, 否则文字型（固定 55 分） | #8B5CF6 紫 |
| **E 易错偏好** | `conquered_mistakes / total_mistakes × 100`（已攻克比例） | #F59E0B 琥珀 |
| **G 学习目标** | `min(100, question_sets_count × 20)`（每个题集 20 分） | #22C55E 绿 |
| **I 兴趣领域** | `min(100, interest_fields_count × 20)`（每个兴趣方向 20 分） | #EC4899 粉 |
| **P 学习人格** | 综合标签评估（固定 55 分，含类型+标签+描述） | #06B6D4 青 |

**综合评分** = 六维算术平均。各维度卡片含图标 + 名称 + 分数 + 渐变色进度条（脉冲点）。

**学习人格卡片**：渐变微光字体 + 浮动 emoji + 类型名称（探索型/稳健型/创新型/专注型/均衡型）+ 特征标签 + 描述文案。

**智能诊断 4 卡**：
1. **核心优势**：分数 ≥70 的 TOP2 维度
2. **待提升维度**：分数 <60 的 TOP2 维度
3. **成长潜力**：60-70 区间的首个维度
4. **学习建议**：优先攻克最弱维度

**生成规划**：将诊断数据编码为 URL 参数 → `/plan-preview?name=强化X·攻克Y&weaknesses=...&strengths=...&stage=...&difficulty=...`

**PDF 导出**：与学情报告相同技术栈。

#### 5.6.3 学习规划（LearningPlan）

路由 `/learning-plan`，AI 驱动的长期学习路径生成。

**生成流程**：
```
POST /learning-plan/generate-tasks {keywords, difficulty, daily_minutes, total_days}
  → AI 按天拆分知识点 → 每天含 {topic, content, video_query, questions[]}
  → 失败时降级为 total_days 阶段模板计划

POST /learning-plan/create {user_id, name, stage, ..., tasks[]}
  → 写入 learning_plans + learning_tasks 表
```

**任务管理**：
- 按日期解锁（每日新任务自动开放）
- `PUT /learning-plan/task/status` 完成标记 → 自动计算计划总进度
- 进度 ≥100% → 计划自动标记 `completed`
- `DELETE /learning-plan/delete/{plan_id}` 级联删除

---


### 5.7 个人画像（维度宇宙）


位于 `/profile-card`，平台最具视觉冲击力的页面。使用 **Three.js 3D 太阳系** 呈现 9 维学习画像。数据源与评估表共用 `GET /evaluation/profile-data`。

#### 5.7.1 3D 场景架构

**深空背景**：5000 远景星 + 3000 填充星 + 2000 银河带星 + 300 近景亮星 + 2 条尘埃带 + 星云光斑

**中央太阳**：四层着色器（核心 + 内冕 + 外冕 + 远辉）

**9 颗行星**：各有轨道环（Three.js RingGeometry）+ 标签精灵（CanvasTexture）+ 周期性自转/公转

**交互**：OrbitControls（拖动旋转/滚轮缩放）→ Raycaster 悬停检测（行星放大+光晕）→ 点击 → Tween.js 摄像机飞入动画 → 展开详情面板

#### 5.7.2 九维详情

| 行星 | 名称 | 图表类型 | 数据来源 | 颜色 | 轨道半径 | 速度 |
|------|------|---------|---------|------|---------|------|
| 1 | 知识星系 | ECharts 力导向图 | `knowledge_base.list` → 节点大小=10+score×0.25, 颜色=绿(≥80)/黄(≥60)/橘(≥40)/红(<40) | #409eff | 2.8 | 0.15 |
| 2 | 能力雷达 | ECharts 雷达图 | `ability_radar` — 6 项能力指标（概念理解/计算/逻辑/记忆/应用/速度） | #8b5cf6 | 3.6 | 0.12 |
| 3 | 学习节奏 | ECharts 日历热力图 | `learning_rhythm.calendar[]` — 90 天活跃度 + 连续天数/最长连续/总活跃天数 | #10b981 | 4.4 | 0.10 |
| 4 | 认知偏好 | ECharts 横向柱状图 | `cognitive_style.distribution` — 各题型分布 | #f59e0b | 5.2 | 0.09 |
| 5 | 易错地图 | ECharts 矩形树图 | `mistake_map.list[]` — 错题知识点面积分布，绿(少)→红(多) | #ef4444 | 6.0 | 0.08 |
| 6 | 成长轨迹 | ECharts 折线图 | `growth_trajectory.points[]` — 掌握度从首次到最近 | #06b6d4 | 6.8 | 0.07 |
| 7 | 学习人格 | CSS 动画卡片 | `personality` — 类型(梯度微光字体) + 标签 + 描述文案 + 浮动 emoji | #ec4899 | 7.6 | 0.06 |
| 8 | 兴趣星云 | Three.js CSS3DRenderer 球面 | `interest_field.list[]` — 黄金角分布标签球 | #f97316 | 8.4 | 0.05 |
| 9 | AI 洞见 | 打字机动画 | `ai_summary` — LLM 生成的 50 字总结，逐字出现 + 闪烁光标 | #a78bfa | 9.2 | 0.04 |

#### 5.7.3 后端数据聚合（evaluation.py）

`GET /evaluation/profile-data` 聚合以下 Supabase 表：

| 数据域 | 来源表 | 聚合方式 |
|--------|--------|---------|
| knowledge_base | `questions` | 按 `normalized_topic` 分组取 avg(mastery_score) |
| ability_radar | `questions` | 按 topic 关键词映射 6 个能力类目 → 取均值 |
| learning_rhythm | `activities` | 90 天日历热力图 + streak 计算 |
| cognitive_style | `generation_history` | 题型分布统计 → 标签（视觉型/文字型/综合型） |
| mistake_map | `questions` | `mistake_status=learning` 按 topic 计数 |
| growth_trajectory | `questions` | 按时序排列 mastery_score |
| personality | 综合推导 | 学习阶段 + 风格 + 强弱项 → 类型标签 + 描述 |
| interest_field | `generation_history` | topic 频率排名 TOP12 |
| ai_summary | LLM 生成 | 火山引擎豆包 → 50 字总结 |

---


### 5.8 消息中心


位于 `/message`，全部平台通知的聚合中心。

#### 5.8.1 通知分类（10 个 Tab）

| Tab | 类型 | 聚合策略 |
|-----|------|---------|
| 全部 | — | 合并展示 |
| 好友消息 | `chat` | 同一 `source_id` 合并，`msg_count` 递增 |
| 社区互动 | `social` | 同上，同一 `source_id` 合并 |
| 学程动态 | `learning` | 每条独立 |
| 计划提醒 | `plan_reminder` | 每条独立 |
| 评估报告 | `evaluation` | 每条独立 |
| 每日推荐 | `daily_rec` | 每天一条 AI 生成 |
| 昨日总结 | `daily_summary` | 每天一条 AI 生成 |
| 系统消息 | `system` | 每条独立 |
| 公告 | `announcement` | 从 `GET /admin/announcements/active` 独立加载 |

#### 5.8.2 通知创建与聚合（notification.py）

```python
def create_notification(user_id, notif_type, title, content, source_id=None, ...):
    if notif_type in ('chat', 'social'):
        # 聚合模式：查找同一 source_id 的未读通知
        existing = GET /notifications?user_id=&type=&source_id=&is_read=false
        if existing:
            # UPDATE: msg_count++, content=最新
            UPDATE /notifications/{id} ...
        else:
            # INSERT 新行
    else:
        # 直接插入模式
        INSERT INTO notifications ...
```

#### 5.8.3 每日智能生成（daily_generator.py）

**昨日总结**：查询昨日 `question_records` + `user_kp_mastery` → LLM 分析答题情况/强弱知识点 → 生成 150 字鼓励性总结 → 写入通知

**每日推荐**：定位最弱知识点 → LLM 生成 120 字学习建议 + 跳转链接 → 写入通知

#### 5.8.4 消息卡片展示

- 头像（发送者头像或首字母 fallback）
- 类型彩色圆点
- 发送者名称 / 相对时间（"刚刚"/"X分钟前"/"X小时前"/"X天前"）
- 预览内容（截断）
- 消息计数标签（聚合类消息显示 "+N"）
- 未读消息蓝色左边框
- 点击：聊天消息 → `/community/chat/{sender_id}`；其他 → `link` 字段跳转
- 公告：点击展开完整内容 + 配图

#### 5.8.5 设置面板

8 个通知频道开关：聊天 / 社交 / 学习 / 计划提醒 / 评估报告 / 每日推荐 / 昨日总结 / 系统消息。每日推荐和昨日总结可设推送时间（07:00/08:00/09:00）。存储于 `notification_settings` 表。

#### 5.8.6 轮询与集成

- 30 秒轮询 `getUnreadSummary()`
- 侧边栏通过 `GET /community/sidebar-badges` 获取未读角标
- "全部已读" → `PUT /community/messages/read-all`
- "清空" → `DELETE /community/messages/clear`
- 单条删除 → `DELETE /community/messages?ids=...`

#### 5.8.7 帮助中心 Q&A

`frontend/src/components/QAPage.vue` — 7 分类 29 条 FAQ：
- 入门指南(4) / 学科计划(7) / 资源库(6) / 学程(6) / 社区(5) / 账号(4) / API(4)
- 每 FAQ 含标题 + 分步解答 + 跳转按钮
- 搜索过滤（匹配标题+内容）
- 底部在线提问表单 → 图片上传 → `POST /qa/submit` → 邮件通知管理员

---


### 5.9 工具箱


侧边栏"工具"区 4 个图标 + `Workbench.vue` 下拉面板。所有工具数据存储在 Supabase 独立表中，每个用户一行，核心数据以 JSONB 列存储。API 前缀 `/tools`（`backend/routers/tools.py`, 339 行）。

#### 5.9.0 整体架构

```
工具箱数据架构
═══════════════════════════════════════════════════════

  前端 Workbench.vue                     后端 tools.py          Supabase
  ┌───────────────────┐    ┌──────────────────────────┐    ┌──────────┐
  │                   │    │                          │    │          │
  │ 打卡面板           │───→│ GET/POST /tools/checkin   │───→│ checkins │
  │ · 项目列表        │    │ · 查已有行 → PATCH/INSERT │    │ user_id  │
  │ · 进度条           │    │ · projects JSONB 列      │    │ projects │
  │ · 打卡按钮         │    │ · 数据在客户端直接操作    │    │ JSONB    │
  │                   │    │                          │    │          │
  │ 倒计时面板         │───→│ GET/POST /tools/countdown │───→│countdowns│
  │ · 事件列表        │    │ · 查已有行 → PATCH/INSERT │    │ user_id  │
  │ · 剩余天数         │    │ · events JSONB 列        │    │ events   │
  │                   │    │                          │    │ JSONB    │
  │ 计时器面板         │───→│ GET/POST /tools/timer     │───→│ timers   │
  │ · 倒计时/正计时    │    │ · 查已有行 → PATCH/INSERT │    │ user_id  │
  │ · 模板列表         │    │ · timers JSONB 列        │    │ timers   │
  │                   │    │                          │    │ JSONB    │
  │ 学习日志面板       │───→│ GET/POST/DELETE           │───→│learning_ │
  │ · 按天分组        │    │   /tools/learning-logs    │    │ logs     │
  │ · 删除/清空        │    │                          │    │ user_id  │
  │                   │    │                          │    │ data     │
  │ 学情报告面板       │───→│ GET /tools/report         │───→│ JSONB    │
  │ · 日志聚合+打卡    │    │ · 并发查 3 表 → 聚合     │    │          │
  └───────────────────┘    └──────────────────────────┘    └──────────┘

通用数据模式（所有工具共用）：
═══════════════════════════════════════════════════════

  读操作: GET /tools/{模块}/{user_id}
     → 查 Supabase WHERE user_id=eq.{uid}&select={jsonb_col}
     → 存在: 返回 jsonb_col 内容
     → 不存在: 返回空数组/空对象

  写操作: POST /tools/{模块}/{user_id}  { body }
     → 查 Supabase WHERE user_id=eq.{uid}
     → 存在: PATCH 更新 jsonb_col
     → 不存在: INSERT { user_id, jsonb_col }
     → → 失败 → HTTP 400 + 详情

  认证: 所有端点要求 Bearer token + verify_user_match()
```

#### 5.9.1 打卡

**数据结构**（Supabase `checkins` 表，每用户一行）：
```json
{
  "user_id": "uuid",
  "projects": [
    {
      "id": "proj_1712345678",
      "name": "每日背单词",
      "target_days": 30,
      "completed_days": 12,
      "last_checkin": "2026-08-03",
      "created_at": "2026-07-15T10:30:00"
    }
  ]
}
```

**防重复打卡逻辑**（前端）：
```javascript
function canCheckin(project) {
  const today = new Date().toISOString().slice(0, 10) // "2026-08-04"
  return project.last_checkin !== today
}

function doCheckin(project) {
  if (!canCheckin(project)) {
    ElMessage.warning('今日已打卡')  // ← 按钮变灰 + toast 提示
    return
  }
  project.completed_days += 1
  project.last_checkin = new Date().toISOString().slice(0, 10)
  saveProjects()  // → POST /tools/checkin/{user_id}
  recordAction('checkin')  // → 通知学程系统
}
```

**进度条渲染**：
```javascript
progressPercent = Math.min(100, (project.completed_days / project.target_days) * 100)
// 色阶: 红(<25%) → 黄(<50%) → 蓝(<75%) → 绿(≥75%) → 金(100%)
```

**打卡与学程联动**：
```
打卡 → recordAction('checkin')
  → 更新 user_actions 表
  → 触发每日任务检查 (checkin_3/7/30 累计天数)
  → 触发成就检查 (first_checkin / checkin_7 / checkin_30)
```

#### 5.9.2 倒计时

**数据结构**（Supabase `countdowns` 表）：
```json
{
  "events": [
    {
      "id": "evt_1712345678",
      "name": "CET-4 考试",
      "target_date": "2026-12-14",
      "created_at": "2026-07-15T10:30:00"
    }
  ]
}
```

**剩余天数计算**（前端实时）：
```javascript
function getRemainingDays(targetDate) {
  const now = new Date()
  const target = new Date(targetDate)
  const diffMs = target.getTime() - now.getTime()
  const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24))
  if (diffDays < 0) return '已结束'
  if (diffDays === 0) return '今天'
  if (diffDays === 1) return '明天'
  return `剩余 ${diffDays} 天`
}
```

**排序**：按 `target_date` 升序（最近的事件排前面）。已结束事件降低透明度并移到列表末尾。

#### 5.9.3 计时器

**数据结构**（Supabase `timers` 表）：
```json
{
  "timers": [
    {
      "id": "tmpl_001",
      "name": "番茄钟 - 词汇练习",
      "mode": "countdown",     // "countdown" | "stopwatch"
      "minutes": 25,
      "is_template": true
    }
  ]
}
```

**两种模式对比**：

| 维度 | 倒计时 (countdown) | 正计时 (stopwatch) |
|------|-------------------|-------------------|
| 初始值 | 设定分钟 (1-180) | 00:00 |
| 方向 | 递减 → 00:00 | 递增 |
| 完成触发 | 倒计时归零 → "时间到"弹窗 | 用户手动点"完成" |
| 学习日志 | 不自动写（用户自己记录） | 自动写入 "学习了「任务名」X分Y秒" |
| 学程记录 | `recordAction('use_timer')` | `recordAction('timer_complete')` |
| 暂停/继续 | ✅ | ✅ |
| 模板功能 | 可保存为模板一键启动 | 可保存为模板一键启动 |

**计时器状态机**：
```
idle ──[开始]──→ running ──[暂停]──→ paused ──[继续]──→ running
                   │                                      │
                   │  [取消] → idle                       │  [完成] → done
                   │                                      │
                   └──────────────────────────────────────┘
```

**完成后的集成链**：
```
计时器完成
  ├─ recordAction('timer_complete') → 学程系统计入
  ├─ 自动写学习日志:
  │     keyword: "计时器 - {template_name or '学习'}"
  │     date: today
  │     → POST /tools/learning-logs/{user_id}
  └─ 前端 Toast： "✅ 已记录 X 分 Y 秒"
```

#### 5.9.4 学习日志

**数据结构**（Supabase `learning_logs` 表，每用户一行 `data` JSONB 列）：
```json
{
  "data": [
    {
      "id": "log_1722776400",
      "keyword": "阅读 - The Economist",
      "date": "2026-08-04",
      "created_at": "2026-08-04 14:30:22"
    },
    {
      "id": "log_1722776000", 
      "keyword": "计时器 - 番茄钟 - 词汇练习",
      "date": "2026-08-04",
      "created_at": "2026-08-04 11:15:00"
    }
  ]
}
```

**自动写入来源**：

| 来源 | 关键词格式 | 触发时机 |
|------|-----------|---------|
| 计时器完成 | `计时器 - {模板名称或"学习"}` | 正计时手动点"完成" |
| 学情报告查看 | `查看学情报告` | 进入 EvaluationReport 页面 |
| 对话摘要 | `/chat/summary` 返回的标签 | AI 对话完成后（仅 generate 意图） |

**前端展示逻辑**（`Workbench.vue`）：
```javascript
// 1. 按日期分组
const grouped = logs.reduce((acc, log) => {
  const date = log.date
  const label = date === today ? '今天' : date === yesterday ? '昨天' : date
  if (!acc[label]) acc[label] = []
  acc[label].push(log)
  return acc
}, {})

// 2. 每组内按 created_at 倒序
for (const group of Object.values(grouped)) {
  group.sort((a, b) => b.created_at.localeCompare(a.created_at))
}

// 3. 渲染: 日期标题 + 条目列表（时间 + 关键词 + 删除按钮）
```

**删除操作**：
- 单条删除：`DELETE /tools/learning-log?user_id=&log_id=` → 过滤掉该 id → PATCH 更新
- 全部清空：`DELETE /tools/learning-logs/{user_id}` → 删除整行

#### 5.9.5 学情报告（工具版）

`GET /tools/report/{user_id}` 聚合 3 个数据源：

```python
async def get_report(user_id: str):
    async with httpx.AsyncClient() as client:
        # 并发查询 3 个 Supabase 表
        # 1. learning_logs → 提取最近 50 条 → TOP20 关键词
        logs_res = await client.get(f"{SUPABASE_URL}/rest/v1/learning_logs?...")
        logs = logs_res.json()[0].get("data", [])
        keywords = list(set([log.get("keyword", "") for log in logs[-50:]]))[:20]

        # 2. checkins → 总打卡天数 + 项目数
        checkin_res = await client.get(f"{SUPABASE_URL}/rest/v1/checkins?...")
        projects = checkin_res.json()[0].get("projects", [])
        total_checkin_days = sum(p.get("completed_days", 0) for p in projects)

        # 3. countdowns → 活跃事件列表
        countdown_res = await client.get(f"{SUPABASE_URL}/rest/v1/countdowns?...")
        events = countdown_res.json()[0].get("events", [])

        return {
            "logs": logs[-30:],           # 最近 30 条日志
            "keywords": keywords,         # TOP20 关键词
            "total_checkin_days": total_checkin_days,
            "project_count": len(projects),
            "events": events              # 所有倒计时事件
        }
```

**前端展示格式**（纯文本块）：
```
📊 学情报告
────────────────────────────
📝 学习关键词 (TOP20)
词汇练习, 阅读训练, 语法, 写作, ...

✅ 打卡统计
累计打卡 127 天 · 进行中项目 3 个
1. 每日背单词 12/30天 (40%)
2. 每天阅读 8/21天 (38%)
3. CET-4冲刺 30/60天 (50%)

⏰ 倒计时事件
· CET-4 考试 — 剩余 132 天
· 期末考 — 剩余 45 天
```

#### 5.9.6 API 端点汇总

| 方法 | 端点 | 说明 | 数据列 |
|------|------|------|--------|
| GET | `/tools/checkin/{user_id}` | 获取打卡项目 | `checkins.projects` |
| POST | `/tools/checkin/{user_id}` | 保存打卡项目 (upsert) | `checkins.projects` |
| GET | `/tools/countdown/{user_id}` | 获取倒计时事件 | `countdowns.events` |
| POST | `/tools/countdown/{user_id}` | 保存倒计时事件 (upsert) | `countdowns.events` |
| GET | `/tools/timer/{user_id}` | 获取计时器模板 | `timers.timers` |
| POST | `/tools/timer/{user_id}` | 保存计时器模板 (upsert) | `timers.timers` |
| GET | `/tools/learning-logs/{user_id}` | 获取学习日志 | `learning_logs.data` |
| POST | `/tools/learning-logs/{user_id}` | 添加日志条目 | `learning_logs.data` |
| DELETE | `/tools/learning-logs/{user_id}` | 清空日志 | `learning_logs` (整行) |
| DELETE | `/tools/learning-log?user_id=&log_id=` | 删除单条日志 | `learning_logs.data` |
| GET | `/tools/report/{user_id}` | 生成学情报告 | 聚合 3 表 |

#### 5.9.7 通用 Upsert 模式

所有工具写操作遵循相同的 upsert 模式：

```python
# 通用模式: 读 → 判断存在 → 更新或插入
async def upsert_tool_data(table: str, user_id: str, 
                           json_col: str, new_data: list):
    headers = get_supabase_headers()
    
    async with httpx.AsyncClient() as client:
        # Step 1: 检查是否存在
        check_url = f"{SUPABASE_URL}/rest/v1/{table}?user_id=eq.{user_id}"
        check_res = await client.get(check_url, headers=headers)
        
        if check_res.status_code == 200 and check_res.json():
            # Step 2a: 存在 → PATCH 更新
            update_url = f"{SUPABASE_URL}/rest/v1/{table}?user_id=eq.{user_id}"
            res = await client.patch(update_url, headers=headers,
                                     json={json_col: new_data})
        else:
            # Step 2b: 不存在 → INSERT
            insert_url = f"{SUPABASE_URL}/rest/v1/{table}"
            res = await client.post(insert_url, headers=headers,
                                    json={"user_id": user_id, json_col: new_data})
        
        # Step 3: 检查结果
        if res.status_code not in [200, 201, 204]:
            raise HTTPException(400, f"保存失败: {res.text}")
        
        return {"success": True}
```

**设计考量**：
- JSONB 单列存储简化了表结构（不需要为每个工具项目建独立表）
- 但 JSONB 不支持 Supabase 的行级更新（必须整列读写），适合单用户数据量小的场景
- 每个用户每个工具仅 1 行，PATCH 操作不会产生冲突
- 30 秒轮询保证多端数据同步

---


### 5.10 API 中心


位于 `/api-center`，用户可在此配置自己的第三方 AI 服务凭证，使用个人 API 额度而非平台共享额度。设计目标是**降低平台运营成本 + 让高级用户自由选择模型**。

#### 5.10.1 架构设计

```
API 中心凭证管理架构
═══════════════════════════════════════════════════════════════

  前端 (Vue)                        后端 (FastAPI)                   第三方服务
  ┌──────────────────┐    ┌──────────────────────────┐    ┌──────────────────┐
  │ ApiCenter.vue    │    │ 凭证存储：Supabase        │    │                  │
  │                  │    │ user_api_keys 表           │    │  火山引擎 ARK     │
  │ ● 6 功能卡片     │    │ ┌──────────────────────┐  │    │  (豆包/DeepSeek)  │
  │ ● 平台选择器     │    │ │ user_id (PK)          │  │    │                  │
  │ ● 凭证输入(掩码) │    │ │ chat_provider         │──┼───→│  POST /api/v3/    │
  │ ● 一键验证       │    │ │ chat_api_key (加密)   │  │    │  chat/completions │
  │ ● 状态徽章       │    │ │ vision_provider       │  │    └──────────────────┘
  │                  │    │ │ generate_provider     │  │
  │  localStorage    │    │ │ evaluate_provider     │  │    ┌──────────────────┐
  │ (前端缓存)       │    │ │ video_provider        │  │    │  DeepSeek API     │
  └──────────────────┘    │ │ voice_provider        │──┼───→│  chat/completions │
                          │ └──────────────────────┘  │    └──────────────────┘
                          └──────────────────────────┘
```

**凭证生命周期**：
```
1. 用户输入凭证 → 前端 AES 加密 → POST /api-center/keys/save
2. 后端解密 → 写入 Supabase user_api_keys (RLS: 只能读写自己的行)
3. 使用时 → 后端从 user_api_keys 读取 → 构建对应平台的 API 调用
4. 验证: POST /api-center/keys/verify → 发起测试请求 → 返回成功/失败
5. 删除: DELETE → 清空对应字段
6. 前端 localStorage 缓存最近使用的 provider 选择（不存明文 key）
```

#### 5.10.2 6 个可配置 AI 功能详细说明

| 功能 | 可选平台 | 配置字段 | 使用场景 | 请求路由 |
|------|---------|---------|----------|----------|
| **AI 对话** | 火山引擎(豆包) / DeepSeek / 智谱 GLM | API Key + Endpoint ID（仅豆包） | ChatArea 主对话、学习建议生成 | `/chat/send` → 查 user_api_keys → 选用户配置的 provider |
| **图片理解** | 火山引擎(豆包 Vision) | API Key + Endpoint ID | 图片题目识别、公式 OCR、多模态问答 | `/chat/vision` → VolcClient.vision_stream() |
| **题目生成** | DeepSeek / 智谱 GLM | API Key | ResourceLib GenerateForm、批量出题 | `/questions/generate` → call_llm(t=0.9) |
| **学习评估** | DeepSeek | API Key | 评估表综合评分、AI 学情分析 | `/evaluation/*` → call_llm(t=0.3) |
| **视频推荐** | 腾讯云 VOD | SecretId + SecretKey + Region | 学习视频搜索与推荐 | — (待实现) |
| **视频通话** | 科大讯飞 RTC | APPID + API Key + API Secret | 小吉实时语音通话 | — (待实现) |

**各平台端点映射**：

| 平台 | API Base URL | 模型参数 | 鉴权方式 |
|------|-------------|---------|---------|
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` | `Authorization: Bearer <key>` |
| 火山引擎豆包 | `https://ark.cn-beijing.volces.com/api/v3` | Endpoint ID (如 `ep-xxx`) | `Authorization: Bearer <key>` |
| 智谱 GLM | `https://open.bigmodel.cn/api/paas/v4` | `glm-4-flash` | `Authorization: Bearer <key>` |
| 腾讯云 VOD | `vod.tencentcloudapi.com` | — | TC3-HMAC-SHA256 签名 |
| 科大讯飞 RTC | `rtc-api.xfyun.cn` | — | API Key + API Secret 签名 |

#### 5.10.3 平台路由与降级策略

```
POST /chat/send 时的 Provider 路由决策树：
═══════════════════════════════════════════════════

请求进入
  │
  ├─ 检查 user_api_keys 表 (user_id 匹配)
  │   │
  │   ├─ chat_provider = "volc" AND chat_api_key 非空
  │   │   → 使用 VolcClient(personal_key).chat_stream()
  │   │
  │   ├─ chat_provider = "deepseek" AND chat_api_key 非空
  │   │   → 使用 DeepSeekClient(personal_key).chat_stream()
  │   │
  │   ├─ chat_provider = "zhipu" AND chat_api_key 非空
  │   │   → 使用 ZhipuClient(personal_key).chat_stream()
  │   │
  │   └─ 未配置 OR 用户选择"平台默认"
  │       → 使用平台统一 DEEPSEEK_API_KEY (环境变量)
  │
  └─ 用户个人 key 调用失败
      → 自动降级到平台 key（如可用）
      → 返回 warning: "您的个人key调用失败，已切换为平台默认"
```

**降级优先级**：用户个人 key > 平台共享 key > 返回错误提示

#### 5.10.4 凭证安全模型

```
存储安全（Supabase RLS）：
┌─────────────────────────────────────────────────────┐
│ user_api_keys 表 RLS 策略                            │
│                                                     │
│ SELECT: auth.uid() = user_id   ← 只能读自己的       │
│ INSERT: auth.uid() = user_id   ← 只能为自己创建     │
│ UPDATE: auth.uid() = user_id   ← 只能改自己的       │
│ DELETE: auth.uid() = user_id   ← 只能删自己的       │
│                                                     │
│ 管理员: service_role 绕过 RLS（后端 service_key）    │
│         但管理员端点不做任何 key 查看操作             │
└─────────────────────────────────────────────────────┘

传输安全：
- HTTPS 加密传输（生产环境）
- 前端输入框 password 类型掩码
- 后端日志脱敏：API Key 只记录前 4 位 + 后 4 位，中间用 *** 替代
- 验证端点不返回完整 key，仅返回 { valid: true/false }

存储加密（建议）：
- 生产环境建议对 api_key 列启用 Supabase Vault 加密
- 或应用层 AES-256-GCM 加密后再写入
```

#### 5.10.5 UI 交互细节

**ApiCenter.vue 页面结构**：
```
┌──────────────────────────────────────────────────────┐
│ API 中心                                     [帮助 ?]│
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌─ AI 对话 ────────────────────────────────── 🟢 ─┐ │
│  │  选择大模型平台进行对话，支持多平台切换            │ │
│  │  平台: [DeepSeek ▼]     状态: 已配置 ✅          │ │
│  │  API Key: [••••••••••••••••]  [👁]              │ │
│  │  Endpoint ID: [ep-202501xxxxxxxx]  (仅豆包)     │ │
│  │  获取 Key: platform.deepseek.com →              │ │
│  │  [🔄 验证连接]  [💾 保存]                        │ │
│  └──────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─ 图片理解 ──────────────────────────────── ⬜ ─┐ │
│  │  ... (同上模式，仅支持火山引擎豆包)               │ │
│  └──────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─ 题目生成 ──────────────────────────────── ⬜ ─┐ │
│  │  ... (DeepSeek / 智谱 GLM)                       │ │
│  └──────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─ 学习评估 ──────────────────────────────── ⬜ ─┐ │
│  │  ... (仅 DeepSeek)                               │ │
│  └──────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─ 视频推荐 ─────────────────────── 🚧 开发中 ─┐ │
│  └──────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─ 视频通话 ─────────────────────── 🚧 开发中 ─┐ │
│  └──────────────────────────────────────────────────┘ │
│                                                      │
│  💡 提示：语音输入使用浏览器内置功能，无需配置        │
│  📖 各平台 Key 获取指南 → /qa                        │
└──────────────────────────────────────────────────────┘
```

**验证流程**：
```
点击「验证连接」
  → POST /api-center/keys/verify { function_type, provider, api_key, endpoint_id? }
  → 后端发起测试请求（1 条简单 prompt，timeout=10s）
  → 成功: HTTP 200 + { valid: true, model: "deepseek-chat", latency_ms: 342 }
  → 失败: { valid: false, error: "401 Unauthorized - API Key 无效" }
  → 网络错误: { valid: false, error: "连接超时，请检查网络" }
```

#### 5.10.6 数据库设计

```sql
CREATE TABLE IF NOT EXISTS user_api_keys (
    user_id UUID PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
    -- 对话
    chat_provider TEXT DEFAULT 'platform',    -- 'platform' | 'volc' | 'deepseek' | 'zhipu'
    chat_api_key TEXT,
    chat_endpoint_id TEXT,                    -- 仅火山引擎豆包需要
    -- 图片理解
    vision_provider TEXT DEFAULT 'platform',
    vision_api_key TEXT,
    vision_endpoint_id TEXT,
    -- 题目生成
    generate_provider TEXT DEFAULT 'platform',
    generate_api_key TEXT,
    -- 学习评估
    evaluate_provider TEXT DEFAULT 'platform',
    evaluate_api_key TEXT,
    -- 视频推荐
    video_secret_id TEXT,
    video_secret_key TEXT,
    video_region TEXT DEFAULT 'ap-shanghai',
    -- 视频通话
    voice_appid TEXT,
    voice_api_key TEXT,
    voice_api_secret TEXT,
    -- 元数据
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### 5.10.7 后端 API 端点

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api-center/keys/{user_id}` | 获取用户配置（敏感字段脱敏：`sk-***x1y2`） | 是 |
| POST | `/api-center/keys/save` | 保存/更新配置 `{user_id, function_type, provider, api_key, ...}` | 是 |
| POST | `/api-center/keys/verify` | 验证凭证有效性 `{function_type, provider, api_key}` → 发起测试请求 | 是 |
| DELETE | `/api-center/keys/{user_id}/{function_type}` | 删除某功能的个人配置（回退到平台默认） | 是 |

**脱敏规则**：
```python
def mask_key(key: str) -> str:
    if not key or len(key) < 8:
        return "***"
    return key[:4] + "****" + key[-4:]  # sk-1***x1y2
```

#### 5.10.8 当前实现状态与规划

| 功能 | 前端 | 后端 | 状态 |
|------|------|------|------|
| AI 对话 | ✅ 界面完整 | 🟡 provider 路由待完善 | 可用 |
| 图片理解 | ✅ 界面完整 | 🟡 仅支持豆包 Vision | 可用 |
| 题目生成 | ✅ 界面完整 | 🟡 当前仅用平台 key | 可用 |
| 学习评估 | ✅ 界面完整 | 🟡 当前仅用平台 key | 可用 |
| 视频推荐 | 🚧 界面占位 | ❌ 未开始 | 规划中 |
| 视频通话 | 🚧 界面占位 | ❌ 未开始 | 规划中 |
| 凭证存储 | ✅ localStorage | 🟡 user_api_keys 表已建 | 待对接 |
| 凭证验证 | ✅ 验证按钮 | 🟡 测试请求待实现 | 待对接 |

---


### 5.11 微信登录与绑定


采用**公众号测试号 OAuth 2.0** 方案（免费、个人可用），避免微信开放平台"网站应用"的企业资质要求（300 元/年）。

#### 5.11.1 扫码登录流程

```
网页点击「微信扫码登录」
  ├─ 后端 GET /auth/wechat/qrcode
  │   └→ 生成 qrcode (base64 PNG) + poll_token
  ├─ 前端展示二维码 + 每 2 秒轮询 GET /auth/wechat/poll/{token}
  │   └→ { ready: false } ... 直到有结果
  │
  └─ 用户手机微信扫码
      └→ 公众号授权页 → 确认
          └→ 微信浏览器回调 GET /auth/wechat/callback?code=xxx&state=xxx
              ├─ state → 查 _state_map → 获取 poll_token + mode(login/bind)
              ├─ code → POST api.weixin.qq.com/sns/oauth2/access_token
              │   └→ openid + nickname + headimgurl
              │
              ├─ mode=login:
              │   查 profiles.wechat_openid = openid
              │   └→ 找到: 签发 JWT → _poll_results = {access_token, user}
              │   └→ 未找到: _poll_results = {bound: false}
              │
              └─ mode=bind (已登录):
                  写入 profiles.wechat_openid → _poll_results = {bound: true}
```

**前端处理**：
- `{ ready: true, access_token, user }` → 登录成功，跳转 `/home`
- `{ ready: true, bound: false }` → Toast "请先登录后在个人中心绑定微信"

#### 5.11.2 账号绑定

个人中心「🔗 微信绑定」卡片 → `GET /auth/wechat/bind-qrcode`（需 Bearer token）→ 扫码 → openid 写入 `profiles.wechat_openid`

#### 5.11.3 自签 JWT 双模认证（auth_middleware.py）

```python
async def get_current_user(authorization: str = Header(None)) -> str:
    token = authorization.replace("Bearer ", "").strip()

    # Step 1: 尝试自签 JWT (微信登录，本地零延迟)
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub") or payload.get("user_id")
        if user_id: return user_id
    except ExpiredSignatureError: raise 401
    except InvalidTokenError: pass  # 继续 Step 2

    # Step 2: Supabase Auth 验证 (邮箱登录，需 HTTP 请求)
    res = await client.get(f"{SUPABASE_URL}/auth/v1/user", ...)
    if res.status_code == 200: return res.json()["id"]
    raise 401 或 503
```

**设计优势**：自签 JWT 本地验证，零网络延迟。Supabase 宕机时微信用户不受影响。

#### 5.11.4 小程序登录

`POST /auth/wx-login {code}` → `jscode2session` 换 openid → 自签 JWT 返回。用于 uni-app 微信小程序版（`D:/jizhi-miniapp`）。

#### 5.11.5 环境配置

```
WECHAT_WEB_APPID=wx888fb32157efcaf7      # 测试号 appid
WECHAT_WEB_SECRET=1ac2c63a416a205aa...   # 测试号 secret
BACKEND_EXTERNAL_URL=http://192.168.10.104 # 手机能访问的地址（无端口=80）
```

微信要求回调域名不含端口号 → 后端需监听 80 端口。测试号获取：https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login

#### 5.11.6 状态管理与并发控制

**服务端状态存储**（内存字典，非数据库）：

```python
# backend/routers/auth.py 中的内存状态
_state_map: dict[str, dict] = {}       # state → {poll_token, mode, created_at}
_poll_results: dict[str, dict] = {}    # poll_token → {ready, access_token?, user?, bound?}
_poll_tokens: dict[str, str] = {}      # state → poll_token (反向索引)
```

**状态生命周期**：

```
State (180s TTL)              Poll Token (180s TTL)          Poll Result (300s TTL)
┌─────────────────┐          ┌─────────────────┐          ┌─────────────────┐
│ state: "abc123" │          │ token: "xyz789" │          │ ready: false    │
│ poll_token:     │──────────→│ state: "abc123" │          │   ...等待中...   │
│   "xyz789"      │          │ mode: "login"   │          │   ↓              │
│ mode: "login"   │          │ created_at: ... │          │ ready: true     │
│ created_at: ... │          └─────────────────┘          │ access_token: ..│
└─────────────────┘                                       │ user: {...}     │
                                                          └─────────────────┘

清理策略:
  - 每次生成新 state/poll_token 前，遍历所有条目删除过期项
  - 过期判断: now - created_at > TTL
  - 防止内存泄漏: 最多保留 1000 条，超出时清理最旧 200 条
```

**并发场景处理**：

| 场景 | 处理方式 |
|------|---------|
| 同一用户多设备同时扫码 | 每次扫码生成新 `state` + 新 `poll_token`；旧 `state` 过期自动失效 |
| 轮询超时 (5分钟无扫码) | 返回 `{ ready: false, expired: true }`；前端停止轮询，显示"二维码已过期" |
| 微信重放回调 (重复 code) | `code` 只能兑换一次 `access_token`；第二次请求微信 API 返回 40163 (code been used) |
| 回调到达但轮询已停止 | `_poll_results` 保留 300s，用户刷新页面可重新获取结果 |

#### 5.11.7 错误处理矩阵

```
扫码登录全链路异常处理
═══════════════════════════════════════════════════════════

  环节            错误                          前端行为                    恢复方式
  ─────────────  ──────────────────────────    ────────────────────────    ──────────
  生成二维码     微信API不通/网络问题           显示错误提示 + "重试"按钮     点击重试
                (GET /auth/wechat/qrcode)     
  
  轮询扫码       5分钟未扫码                   二维码过期蒙层               点击刷新重新获取
                (poll 返回 expired=true)       + "刷新二维码"按钮           新二维码
  
  用户扫码后     已扫码但未绑定账号             Toast提示                    跳转登录页
  回调返回       (callback → openid查不到)     "请先登录后绑定微信"          先邮箱注册再绑定
  
  用户扫码后     微信API code换token失败        后端捕获异常                 前端收到错误
  回调返回       (code过期/已使用/网络错误)     _poll_results不更新           提示"授权失败请重新扫码"
  
  用户扫码后     Supabase写入失败              后端捕获异常                  openid已获取但
  绑定写入       (网络/RLS)                    _poll_results仍标记成功       profiles未更新
                                              日志记录错误供排查             → 异步补偿重试
  
  签发JWT       JWT库异常                     后端捕获异常                 前端收到错误
                (极罕见，密钥配置错误)          _poll_results不更新          提示"登录失败"
```

**前端轮询有限状态机**：

```javascript
// Login.vue 中的轮询逻辑
const POLL_INTERVAL = 2000   // 2秒
const POLL_TIMEOUT = 300000  // 5分钟
let pollTimer = null
let elapsedTime = 0

async function startPolling(pollToken) {
  elapsedTime = 0
  pollTimer = setInterval(async () => {
    elapsedTime += POLL_INTERVAL
    
    // 超时检查
    if (elapsedTime >= POLL_TIMEOUT) {
      stopPolling()
      state.qrcodeExpired = true  // → 显示过期蒙层
      return
    }
    
    const res = await fetch(`/auth/wechat/poll/${pollToken}`)
    const data = await res.json()
    
    if (!data.ready) return  // ← 继续轮询
    
    // 结果处理
    stopPolling()
    if (data.access_token) {
      // 登录成功
      authStore.setToken(data.access_token)
      authStore.setUser(data.user)
      router.push('/home')
    } else if (data.bound === false) {
      // 未绑定 → 提示用户先登录
      ElMessage.warning('请先登录后在个人中心绑定微信')
      state.showBindTip = true
    } else if (data.bound === true) {
      // 绑定成功
      ElMessage.success('微信绑定成功')
      state.wechatBound = true
      fetchUserProfile()  // 刷新个人信息
    }
  }, POLL_INTERVAL)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}
```

#### 5.11.8 安全加固

**防冒用措施**：

| 威胁 | 缓解措施 |
|------|---------|
| 扫码即自动创建账号 | `login` 模式必须先有账号 → 在 profiles 中查 openid → 查不到返回 `bound: false` 不自动创建 |
| 二维码劫持（中间人替换） | state 参数 1:1 绑定 poll_token，state 匹配才更新 _poll_results |
| 暴力轮询（猜 poll_token） | poll_token 为 `secrets.token_urlsafe(32)` (256 位随机)，碰撞概率 ≈ 2⁻²⁵⁶ |
| 重放攻击 (旧 code) | 微信 code 一次性，且 5 分钟过期；`_state_map` 条目也有 180s TTL |
| openid 泄露 | 自签 JWT 不含 openid，仅含 user_id；profiles.wechat_openid 不暴露给前端 |

**自签 JWT 安全参数**：
```python
# JWT payload 结构
{
  "sub": "user-uuid-xxxx",        # 用户ID (唯一标识)
  "user_id": "user-uuid-xxxx",    # 冗余字段
  "nickname": "微信昵称",         # 展示用
  "avatar": "https://...",        # 微信头像URL
  "iat": 1722776400,              # 签发时间
  "exp": 1725368400,              # 过期时间 (720小时后)
  "type": "wechat_login"          # token类型标记
}

# 签名: HMAC-SHA256(JWT_SECRET, header.payload)
# key 长度: ≥256 bits (JWT_SECRET 至少 32 字符)
```

**日志脱敏**：
```python
# 微信回调日志中不记录 openid 明文
logger.info(f"微信回调: state={state[:8]}... poll_token={poll_token[:8]}...")
logger.info(f"微信用户: openid={openid[:4]}****{openid[-4:]}")
# 仅在调试模式记录完整字段 → 生产环境关闭 DEBUG 日志
```

#### 5.11.9 小程序登录差异

| 维度 | 网页版 (公众号测试号) | 小程序版 |
|------|---------------------|---------|
| 认证方式 | OAuth 2.0 授权码模式 | `wx.login()` → code → jscode2session |
| 用户标识字段 | `openid` (公众号 openid) | `openid` (小程序 openid) |
| UnionID | ✅ (同主体下公众号+小程序共享) | ✅ |
| API 端点 | `GET /auth/wechat/*` (多个) | `POST /auth/wx-login` (单个) |
| Token 签发 | 自签 JWT (HS256) | 自签 JWT (HS256) |
| 域名要求 | 回调域名不能含端口号 | 不要求（小程序请求走 wx.request） |
| 头像昵称获取 | OAuth scope `snsapi_userinfo` | `wx.getUserProfile()` (需用户主动触发) |

**小程序 code 换 session**：
```
POST /auth/wx-login { code: "061aBcDe..." }
  → POST https://api.weixin.qq.com/sns/jscode2session
     ?appid={WECHAT_MP_APPID}&secret={WECHAT_MP_SECRET}
     &js_code={code}&grant_type=authorization_code
  → 返回: { openid, session_key, unionid? }
  → 查/创建 profiles → 签发自签 JWT → 返回 { access_token, user }
```

---


### 5.12 管理后台


位于 `/admin`，需 admin/super_admin 角色。深色侧边栏 + 内容区布局（`AdminLayout.vue`）。7 个子页面，22 个 API 端点，后端 `backend/routers/admin.py` (1,110 行)。

#### 5.12.1 后端架构设计

```
admin.py 内部架构
═══════════════════════════════════════════════════════

  辅助函数层（可复用）
  ┌──────────────────────────────────────────────────┐
  │ _supabase_url(path, params)   → 构建 REST URL     │
  │ _supabase_get(path, params)   → GET + 管理员头    │
  │ _supabase_get_with_count()    → GET + count=exact │
  │ _supabase_post(path, body)    → POST + return=rep │
  │ _supabase_patch(path, body)   → PATCH + 管理员头  │
  └──────────────────────────────────────────────────┘
           │              │              │
           ▼              ▼              ▼
  ┌────────────┐ ┌────────────┐ ┌──────────────┐
  │ 仪表盘端点  │ │ 用户管理    │ │ 内容审核     │
  │ dashboard  │ │ users CRUD │ │ reports/     │
  │ 7项统计    │ │ 封禁/设管理│ │ feedback/qa  │
  └────────────┘ └────────────┘ └──────────────┘
           │              │              │
           ▼              ▼              ▼
  ┌────────────┐ ┌────────────┐ ┌──────────────┐
  │ 题库管理    │ │ 公告管理    │ │ 审计日志     │
  │ questions  │ │ announce-  │ │ audit_logs  │
  │ CRUD+导入  │ │ ments CRUD │ │ 查询+筛选    │
  └────────────┘ └────────────┘ └──────────────┘
```

**鉴权中间件链**：
```python
# 所有 /admin/* 端点依赖链
get_current_user()           # Step 1: JWT 验证（auth_middleware）
  → get_current_admin()      # Step 2: 查 profiles.role → admin/super_admin
    → get_current_super_admin()  # Step 3 (部分端点): role == 'super_admin'

# admin_middleware.py 关键逻辑
async def get_current_admin(current_user = Depends(get_current_user)):
    res = await client.get(
        f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{current_user}&select=role,is_admin",
        headers=service_role_headers  # ← 用 service_role key 绕过 RLS
    )
    data = res.json()[0]
    role = data.get("role", "")
    is_admin = data.get("is_admin", False)
    
    if role not in ("admin", "super_admin") and not is_admin:
        raise HTTPException(403, "无权访问管理后台")
    return current_user
```

#### 5.12.2 功能全景

| 页面 | 路由 | 组件 | 核心功能 | 权限 |
|------|------|------|----------|------|
| 仪表盘 | `/admin` | AdminDashboard | 7 项统计卡片（用户数/今日新增/总做题数/今日做题/待处理举报/待处理反馈/总计划数） | admin+ |
| 用户管理 | `/admin/users` | AdminUsers | 列表搜索/封禁/解封/详情弹窗/设管理员（仅超管可见） | admin+ |
| 内容审核 | `/admin/reports` | AdminReports | 举报/反馈/Q&A 三 Tab 审核 | admin+ |
| 题库管理 | `/admin/questions` | AdminQuestions | 题目 CRUD + 考纲选择器 + 维度/题型动态筛选 + 批量导入 JSON | admin+ |
| 公告管理 | `/admin/announcements` | AdminAnnouncements | 发布/编辑/下架 + 图片上传（Supabase Storage, ≤5MB）+ 预览 | admin+ |
| 操作日志 | `/admin/logs` | AdminLogs | 按操作类型筛选审计日志 | admin+ |

#### 5.12.3 仪表盘统计聚合算法

`GET /admin/dashboard` 并发查询 6 个 Supabase 端点：

```python
async def get_dashboard():
    async with httpx.AsyncClient(timeout=15.0) as client:
        # 并发查询 6 个数据源（asyncio.gather）
        # 1. 用户总数
        total_users_res = await client.get(
            f"{SUPABASE_URL}/rest/v1/profiles?select=id",
            headers=admin_headers_with_count
        )
        total_users = extract_count(total_users_res)  # ← 从 Content-Range 头提取

        # 2. 今日新增用户
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_users_res = await client.get(
            f"{SUPABASE_URL}/rest/v1/profiles"
            f"?select=id&created_at=gte.{today}",
            headers=admin_headers_with_count
        )
        today_new_users = extract_count(today_users_res)

        # 3. 总做题数
        total_questions_res = await _supabase_get_with_count("question_records", select="id")
        total_questions_done = total_questions_res[1]

        # 4. 今日做题数
        today_questions_res = await _supabase_get_with_count(
            "question_records",
            select="id",
            created_at=f"gte.{today}"
        )
        today_questions_done = today_questions_res[1]

        # 5. 待处理举报
        pending_reports_res = await _supabase_get_with_count(
            "content_reports",
            select="id",
            status="eq.pending"
        )
        pending_reports = pending_reports_res[1]

        # 6. 待处理反馈 + 总计划数
        pending_feedback = ...
        total_plans = ...

        return {
            "total_users": total_users,
            "today_new_users": today_new_users,
            "total_questions_done": total_questions_done,
            "today_questions_done": today_questions_done,
            "pending_reports": pending_reports,
            "pending_feedback": pending_feedback,
            "total_plans": total_plans
        }
```

**count=exact 计数机制**：
```
Supabase REST API 默认不返回总数（分页性能考虑）。
加上 Prefer: count=exact 头后，响应头会包含：
  Content-Range: 0-0/16889
                           ↑ 总数
后端从 Content-Range 解析总数。
```

#### 5.12.4 三级角色体系

`profiles.role` 字段（TEXT），兼容旧 `is_admin` 布尔。

| 角色 | 标识 | 权限 |
|------|------|------|
| `super_admin` | `role = 'super_admin'` | 全部权限 + 可设/撤管理员 + 审计日志全量查看 |
| `admin` | `role = 'admin'` 或 `is_admin = true` | 管理用户和内容（举报/题库/公告），不能管其他管理员 |
| `user` | `role = 'user'` 或其他 | 无后台权限 |

**鉴权中间件**（admin_middleware.py）：
- `get_current_admin` → 查 `profiles` 的 `role` + `is_admin` → 403 拦截
- `get_current_super_admin` → 要求 `role == 'super_admin'`

**角色提升流程**：
```
超管操作: PUT /admin/users/{user_id}/admin { is_admin: true }
  → 后端:
    1. get_current_super_admin 验证
    2. UPDATE profiles SET role='admin' WHERE id=user_id
    3. write_audit_log('set_admin', 'user', user_id)
    4. 返回成功
  → 撤销: { is_admin: false } → role='user'
```

#### 5.12.5 题库批量导入流水线

`POST /admin/questions/import?syllabus_id=cet4`：

```
批量导入全链路
═══════════════════════════════════════════════════════

  管理员上传 JSON
  ┌──────────────────────────────┐
  │ {                            │
  │   "questions": [             │
  │     {                        │
  │       "category": "vocab",  │
  │       "question_type": "choice",
  │       "difficulty": 3,      │
  │       "content": {...},     │
  │       "answer": "A",        │
  │       ...                    │
  │     },                       │
  │     ...更多题目               │
  │   ]                          │
  │ }                            │
  └──────────┬───────────────────┘
             │
             ▼
  后端 admin.py
  ┌──────────────────────────────────────────────────────┐
  │                                                      │
  │ 1. 验证 json 格式                                     │
  │    try: data = json.loads(body)                       │
  │    → 不是有效 JSON → HTTP 400                         │
  │                                                      │
  │ 2. 提取 questions 数组                                │
  │    questions = data.get("questions", [data])          │
  │    → 空数组 → HTTP 400 "没有题目数据"                   │
  │                                                      │
  │ 3. 补充必要字段（每道题）                               │
  │    for q in questions:                                │
  │        q.setdefault("id", str(uuid.uuid4()))          │
  │        q.setdefault("source", "imported")             │
  │        # 分类/知识点/难度等字段不补充（要求用户提供）     │
  │                                                      │
  │ 4. 写入本地题库                                       │
  │    local_question_bank.add_questions(syllabus_id,     │
  │                                      questions)      │
  │    → 内部:                                            │
  │      bank["questions"].extend(questions)              │
  │      重建 index: {q["id"]: q}                         │
  │      save_bank_to_file(syllabus_id) → JSON 持久化     │
  │                                                      │
  │ 5. 审计日志                                          │
  │    write_audit_log(admin_id, "import_questions",      │
  │                    "question", syllabus_id,           │
  │                    {"count": len(questions)})          │
  │                                                      │
  │ 6. 返回                                              │
  │    { "imported": len(questions),                      │
  │      "total_in_bank": len(bank["questions"]) }        │
  └──────────────────────────────────────────────────────┘
```

**导入去重策略**：
```python
# local_question_bank.add_questions() 内部
existing_ids = set(bank["index"].keys())
new_questions = [q for q in questions if q["id"] not in existing_ids]
skipped = len(questions) - len(new_questions)
bank["questions"].extend(new_questions)
# 重建索引
bank["index"] = {q["id"]: q for q in bank["questions"]}
```

#### 5.12.6 审计日志（admin_audit_logs）

每次管理员操作自动调用 `write_audit_log(admin_id, action, target_type, target_id, detail)`：

| action | target_type | 触发场景 |
|--------|-------------|---------|
| `ban_user` / `unban_user` | `user` | 封禁/解封 |
| `set_admin` / `unset_admin` | `user` | 设/撤管理员（仅超管） |
| `create_question` / `update_question` / `delete_question` | `question` | 题库 CRUD |
| `import_questions` | `question` | 批量导入 |
| `resolve_report` | `report` | 处理举报 |
| `resolve_feedback` | `feedback` | 处理反馈 |
| `create_announcement` / `update_announcement` / `delete_announcement` | `announcement` | 公告管理 |
| `upload_image` | `image` | 图片上传 |

**非阻塞写入**：`try...except: pass`，日志失败不影响主操作。

```python
async def write_audit_log(admin_id, action, target_type, target_id, detail):
    try:
        # 获取管理员昵称（用于日志可读性）
        nick_res = await _supabase_get(
            "profiles",
            select="nickname",
            id=f"eq.{admin_id}"
        )
        nickname = nick_res[0].get("nickname", "") if nick_res else ""
        
        # 写入日志
        await _supabase_post("admin_audit_logs", {
            "admin_id": admin_id,
            "admin_nickname": nickname,
            "action": action,
            "target_type": target_type,
            "target_id": str(target_id),
            "detail": detail or {}
        })
    except Exception:
        pass  # ← 日志写入失败不抛异常，不影响主业务流程
```

**日志查询**：
```
GET /admin/logs?action=ban_user&page=1&page_size=20
→ SELECT * FROM admin_audit_logs
  WHERE action = 'ban_user'
  ORDER BY created_at DESC
  LIMIT 20 OFFSET 0
```

#### 5.12.7 管理员 API 完整参考（/admin 前缀）

| 方法 | 端点 | 说明 | 角色要求 |
|------|------|------|---------|
| GET | `/admin/dashboard` | 仪表盘 7 项统计 | admin+ |
| GET | `/admin/users` | 用户列表（搜索/状态筛选/分页） | admin+ |
| GET | `/admin/users/{user_id}` | 用户详情 + 统计 | admin+ |
| PUT | `/admin/users/{user_id}/status` | 封禁/解封 `{is_active: bool}` | admin+ |
| PUT | `/admin/users/{user_id}/admin` | 设/撤管理员 `{is_admin: bool}` | super_admin |
| GET | `/admin/reports` | 举报列表（状态筛选/分页） | admin+ |
| PUT | `/admin/reports/{id}/resolve` | 处理举报 `{status, admin_note}` | admin+ |
| GET | `/admin/feedback` | 反馈列表 | admin+ |
| PUT | `/admin/feedback/{id}` | 处理反馈 `{admin_note}` | admin+ |
| GET | `/admin/qa` | Q&A 列表 | admin+ |
| PUT | `/admin/qa/{id}` | 处理 Q&A `{admin_note}` | admin+ |
| GET | `/admin/questions` | 题库列表（考纲/维度/题型筛选） | admin+ |
| GET | `/admin/questions/{id}` | 题目详情 | admin+ |
| POST | `/admin/questions` | 创建题目 | admin+ |
| PUT | `/admin/questions/{id}` | 更新题目 | admin+ |
| DELETE | `/admin/questions/{id}` | 删除题目 | admin+ |
| POST | `/admin/questions/import` | 批量导入 JSON | admin+ |
| GET | `/admin/announcements` | 公告全量 | admin+ |
| GET | `/admin/announcements/active` | 活跃公告（公开，免认证） | 无 |
| POST | `/admin/announcements` | 发布公告 | admin+ |
| PUT | `/admin/announcements/{id}` | 编辑公告 | admin+ |
| DELETE | `/admin/announcements/{id}` | 删除公告 | admin+ |
| POST | `/admin/upload-image` | 上传图片（PNG/JPEG/GIF/WebP, ≤5MB） | admin+ |
| GET | `/admin/logs` | 操作日志（按 action 筛选） | admin+ |
| GET | `/admin/settings` | 系统配置信息 | admin+ |

---


### 6.1 学科计划 API

全部端点挂载在 `/subject-plan` 下（`backend/routers/subject_plan.py`）。

#### 6.1.1 考纲列表

```
GET /subject-plan/syllabi?user_id={optional}
```

**响应**：
```json
{
  "syllabi": [
    {
      "id": "cet4",
      "name": "CET-4 英语四级",
      "abbr": "C4",
      "color": "#409eff",
      "description": "全国大学英语四级考试...",
      "intro": "四级考试是大学生英语能力的基准线...",
      "suitable_for": "在校大学生、专升本考生、社会考生",
      "has_plan": true,
      "plan": {
        "id": "uuid",
        "goal_score": 500,
        "period_days": 60,
        "daily_minutes": 90,
        "status": "active",
        "created_at": "2026-07-15T10:30:00Z"
      },
      "question_count": 1098,
      "question_types": ["choice", "choice_multi", "fill", ...],
      "question_types_enabled": ["choice", "choice_multi", "fill", ...],
      "dimensions": [
        { "name": "词汇", "category": "vocabulary", "count": 98 }
      ],
      "languages": ["python"],
      "target_count": 1000,
      "max_score": 710,
      "pass_score": 425,
      "exam_papers": [...]
    }
    // ... 16 more
  ]
}
```

**说明**：`user_id` 可选。传入时尝试批量查询该用户在每个考纲下的活跃计划（1 次 Supabase 请求），失败时降级为无计划状态。

#### 6.1.2 考纲详情

```
GET /subject-plan/syllabi/{syllabus_id}?user_id={optional}
```

返回考纲完整信息 + 用户计划摘要 + 诊断结果。

#### 6.1.3 题库查询

```
GET /subject-plan/syllabi/{syllabus_id}/questions
  ?user_id=xxx
  &category=vocabulary
  &sub_category=高频核心词
  &question_type=choice
  &difficulty=3
  &search=adopt
  &limit=20
  &offset=0
  &random_order=true
```

**响应**：`{ "questions": [...], "total": 98 }`

**实现**：所有筛选和搜索在 Python 内存中完成 (`local_question_bank.query()`)，零网络延迟。`search` 参数同时匹配 `content.stem` 和 `kp_name` 字段（忽略大小写）。

#### 6.1.4 诊断题目抽取

```
GET /subject-plan/syllabi/{syllabus_id}/diagnosis/start
```

无需认证。返回按 `diagnosis_config` 配置随机抽取的题目组合。

#### 6.1.5 提交诊断

```
POST /subject-plan/syllabi/{syllabus_id}/diagnosis/submit
Content-Type: application/json
Authorization: Bearer <token>

{
  "user_id": "uuid",
  "answers": [
    { "question_id": "xxx", "user_answer": "A", "time_spent": 45 },
    { "question_id": "yyy", "user_answer": "译文...", "time_spent": 120 }
  ],
  "preferences": {
    "goal_score": 500,
    "period_days": 60,
    "daily_minutes": 90
  }
}
```

**响应**：
```json
{
  "plan_id": "uuid",
  "plan_name": "CET-4 60天冲刺计划",
  "accuracy": 57,
  "correct_count": 8,
  "total_count": 14,
  "already_exists": false
}
```

**防重复**：若该考纲已有活跃计划，直接返回已有 `plan_id` 且 `already_exists: true`。

#### 6.1.6 计划 CRUD

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/plans/{plan_id}?user_id=` | 获取计划详情 + 诊断结果 |
| PUT | `/plans/{plan_id}?user_id=` | 更新计划字段 (name/goal/daily_minutes/status) |
| DELETE | `/plans/{plan_id}?user_id=` | 删除计划 (Cascade: 关联任务/记录/掌握度由 DB 级联删除) |

#### 6.1.7 每日任务

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/plans/{plan_id}/tasks?user_id=` | 全部任务列表 |
| GET | `/plans/{plan_id}/tasks/today?user_id=` | 今日任务 + 题目 (去重分配) |
| GET | `/plans/{plan_id}/done-ids?user_id=` | 已完成题目 ID 集合 |
| GET | `/plans/{plan_id}/question-states?user_id=` | 每题作答状态 (薄弱/待巩固/优势) |
| GET | `/plans/{plan_id}/questions-count?user_id=` | 答题统计 (总数/已做/正确/正确率) |

#### 6.1.8 提交答案

```
POST /subject-plan/plans/{plan_id}/submit
Authorization: Bearer <token>

{
  "user_id": "uuid",
  "plan_id": "uuid",
  "question_id": "id",
  "user_answer": "A",
  "source": "daily",
  "task_id": "uuid (optional)",
  "time_spent": 45
}
```

**响应**：
```json
{
  "is_correct": true,
  "ai_feedback": null,
  "correct_answer": "A",
  "explanation": "adopt 意为「采纳」..."
}
```

**批改逻辑**：

| 题型 | 判对错方式 | AI 介入 |
|------|-----------|---------|
| `choice`, `choice_single` | 规范化选项字母 → 精确比较 | 否 |
| `choice_multi`, `choice_indefinite` | 解析多选集合 → 集合相等比较 | 否 |
| `fill` | 去空白 + 小写 → 精确匹配 | 否 |
| `cloze` | 与答案列表逐一比较 | 否 |
| `calculation` | 浮点数容差 1e-6 比较 | 是（备选） |
| `translation`, `essay` | — | **是**（DeepSeek 0.3 温度批改） |
| `short_answer`, `case_analysis` | — | **是** |
| `teaching_design`, `analysis` | — | **是** |
| `programming` | 有测试用例→沙箱执行；无→AI | **是**（降级） |

#### 6.1.9 掌握度与错题

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/plans/{plan_id}/mastery?user_id=` | 知识点掌握度列表 |
| GET | `/plans/{plan_id}/mistakes?user_id=&limit=&offset=` | 该计划错题本（含题目详情） |
| GET | `/mistakes/overview?user_id=` | 跨计划错题总览统计 |
| GET | `/mistakes/practice?user_id=&limit=10` | 跨考纲随机错题练习 |

#### 6.1.10 代码判题

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/code/languages` | 返回可用语言列表及状态 | 否 |
| POST | `/code/run` | 运行代码（自定义输入），返回 stdout/stderr | 否 |
| POST | `/code/submit` | 提交判题：逐测试点执行 → AC/WA/TLE/RE | 否 |

**`POST /code/submit` 请求**：
```json
{
  "user_id": "",
  "plan_id": "",
  "question_id": "algo-ds-binary-search-001",
  "syllabus_id": "algorithm-ds",
  "language": "python",
  "code": "def binary_search(arr, target):\n    ...",
  "source": "daily",
  "task_id": null
}
```

**`POST /code/submit` 响应**：
```json
{
  "is_correct": false,
  "score": 75,
  "passed_points": 75,
  "total_points": 100,
  "test_results": [
    { "index": 1, "description": "基本查找", "status": "AC",
      "passed": true, "points": 25, "earned": 25,
      "stdout": "3\n", "stderr": "" },
    { "index": 2, "description": "边界值测试", "status": "WA",
      "passed": false, "points": 25, "earned": 0,
      "stdout": "-1\n", "stderr": "" },
    { "index": 3, "description": "大数组测试", "status": "TLE",
      "passed": false, "points": 25, "earned": 0,
      "stdout": "", "stderr": "执行超时 (5s)" },
    { "index": 4, "description": "空数组", "status": "AC",
      "passed": true, "points": 25, "earned": 25,
      "stdout": "-1\n", "stderr": "" }
  ],
  "passed_count": 2,
  "total_count": 4,
  "language": "python",
  "has_test_cases": true,
  "supported_languages": ["python", "cpp", "java"]
}
```

#### 6.1.11 公共查询

```
GET /subject-plan/questions/by-ids?ids=id1,id2,id3&syllabus_id=cet4&user_id=
```

无需认证。按 ID 列表从本地题库精确取题，用于做题页加载多道题目。

### 6.2 认证 API

全部在 `backend/routers/auth.py`，前缀 `/auth`。

#### 邮箱认证

```
POST /auth/send-code          # 发送邮箱验证码 (速率限制: 60s/次/IP)
POST /auth/register           # 邮箱 + 验证码 + 密码 → 创建 Supabase Auth 用户 + profile
POST /auth/login              # 邮箱/账号 + 密码 → JWT token + 用户资料
POST /auth/logout             # 登出
PUT  /auth/update-password    # 修改密码 (需验证旧密码)
```

**验证码生命周期**：
- 生成：6 位数字，存入 `email_verification_codes` 表
- 有效期：10 分钟 (`expires_at = now + 600`)
- 状态：`used` 字段标记是否已使用
- 约束：注册前需先发送验证码 (`POST /send-code`)，新请求会先删除旧记录

#### 个人资料

```
GET  /auth/profile/{user_id}                  # 公开查询
PUT  /auth/update-nickname                    # 改昵称
PUT  /auth/update-bio                         # 改简介
PUT  /auth/update-learning-info               # 更新学习阶段/年级/专业/偏好
POST /auth/upload-avatar/{user_id}            # 上传头像 (200×200 PNG)
PUT  /auth/status?user_id=&status=            # 更新在线状态 (online/offline/invisible)
```

#### 微信登录

```
GET  /auth/wechat/qrcode?redirect=/home       # 获取扫码登录二维码 (base64 PNG + poll_token)
GET  /auth/wechat/bind-qrcode                 # 已登录用户绑定微信 (需 Bearer token)
GET  /auth/wechat/callback?code=&state=       # 微信 OAuth 回调 (被手机微信浏览器访问)
GET  /auth/wechat/poll/{poll_token}           # 轮询扫码结果
GET  /auth/wechat/user/{user_id}              # 查询用户 (本地缓存回退)
POST /auth/wx-login                           # 微信小程序 code 换 JWT
```

**轮询返回值语义**：
```json
// 等待中
{ "ready": false }

// 登录成功
{ "ready": true, "access_token": "jwt...", "user": {...} }

// 未绑定 (已扫码但 openid 不在 profiles)
{ "ready": true, "bound": false }

// 绑定成功
{ "ready": true, "bound": true, "nickname": "微信昵称" }
```

### 6.3 管理后台 API

全部在 `backend/routers/admin.py`，前缀 `/admin`，需要 admin/super_admin 角色。

#### 仪表盘
```
GET /admin/dashboard
→ { total_users, today_new_users, total_questions_done, today_questions_done,
    pending_reports, pending_feedback, total_plans }
```

#### 用户管理
```
GET  /admin/users?search=&status=active|banned&page=1&page_size=20
GET  /admin/users/{user_id}                             # 详情+统计(计划数/答题数/帖子数)
PUT  /admin/users/{user_id}/status { is_active: bool }    # 封禁/解封
PUT  /admin/users/{user_id}/admin  { is_admin: bool }     # 设/撤管理员 (仅超管)
```

#### 内容审核
```
GET  /admin/reports?status=pending|resolved|dismissed&page=1&page_size=20
PUT  /admin/reports/{id}/resolve { status, admin_note }
GET  /admin/feedback?status=&page=&page_size=
PUT  /admin/feedback/{id} { admin_note }
GET  /admin/qa?status=&page=&page_size=
PUT  /admin/qa/{id} { admin_note }
```

#### 题库管理
```
GET    /admin/questions?category=&syllabus_id=&search=&page=1&page_size=20
GET    /admin/questions/{question_id}
POST   /admin/questions?syllabus_id=cet4 { ...题目字段 }
PUT    /admin/questions/{question_id} { ...字段 }
DELETE /admin/questions/{question_id}
POST   /admin/questions/import?syllabus_id=cet4 { questions: [...] }
```

#### 公告管理
```
GET    /admin/announcements                              # 全量 (含未激活)
GET    /admin/announcements/active                       # 公开 (无需管理员)
POST   /admin/announcements { title, content, image_url, is_active }
PUT    /admin/announcements/{id} { ... }
DELETE /admin/announcements/{id}
```

#### 其他
```
GET  /admin/logs?action=&page=&page_size=                # 审计日志
GET  /admin/settings                                      # 系统配置信息
POST /admin/upload-image                                  # 图片上传 (≤5MB, PNG/JPEG/GIF/WebP)
```

### 6.4 对话 API

前缀 `/chat`（`backend/routers/chat.py`）：

```
POST /chat/detect-intent { text }        # 意图识别: plan/generate/evaluate/chat
POST /chat/stream                        # 流式对话 (SSE)
POST /chat/generate-title                # AI 生成对话标题
POST /chat/vision { image_url, question }# 图片识别 (火山引擎豆包 Vision)
```

### 6.5 小吉语音助手 API

前缀 `/xiaoji`（`backend/routers/xiaoji.py`）：

```
GET /xiaoji/config/{user_id}             # 获取配置
PUT /xiaoji/config/{user_id}             # 更新配置 (名称/性格/语音参数)
POST /xiaoji/tts                         # TTS 文字转语音 (科大讯飞)
POST /xiaoji/asr                         # ASR 语音转文字 (科大讯飞)
```

### 6.6 通用响应规范与错误码

| HTTP 状态 | 含义 | 响应体格式 |
|-----------|------|-----------|
| 200 | 成功 | `{ ...业务字段 }` |
| 201 | 创建成功 | `{ ...业务字段 }` |
| 400 | 请求参数错误 | `{ "detail": "描述" }` |
| 401 | 未认证 / Token 无效 | `{ "detail": "未登录，请先登录" }` |
| 403 | 无权限 | `{ "detail": "无权操作其他用户的数据" }` |
| 404 | 资源不存在 | `{ "detail": "考纲不存在" }` |
| 429 | 速率限制 | `{ "detail": "验证码已发送，请60秒后重试" }` |
| 500 | 服务端错误 | `{ "detail": "创建计划失败" }` |
| 503 | 服务不可用 | `{ "detail": "认证服务不可用" }` |

---

## 7. 前端页面说明

### 7.1 完整路由表

| 路由 | 组件 | meta | 说明 |
|------|------|------|------|
| `/` | Landing | `{requiresAuth:false}` | 落地页 |
| `/login` | Login | `{requiresAuth:false}` | 三栏登录/注册 |
| `/onboarding` | Onboarding | `{requiresAuth:true}` | 新用户引导 |
| `/home` | Home | `{requiresAuth:true}` | 首页工作台 |
| `/profile` | Profile | `{requiresAuth:true}` | 个人中心 |
| `/resource-lib` | ResourceLib | `{requiresAuth:true}` | 资源库 |
| `/evaluation-center` | EvaluationCenter | `{requiresAuth:true}` | 评估中心 |
| `/evaluation-report` | EvaluationReport | `{requiresAuth:true}` | 评估报告 |
| `/evaluation-table` | EvaluationTable | `{requiresAuth:true}` | 评估表 |
| `/career` | Career | `{requiresAuth:true}` | 生涯规划 |
| `/career/rank` | CareerRank | `{requiresAuth:true}` | 排行榜 |
| `/career/tasks` | CareerTasks | `{requiresAuth:true}` | 生涯任务 |
| `/career/achievements` | CareerAchievements | `{requiresAuth:true}` | 生涯成就 |
| `/do-question/:taskId` | DoQuestion | `{requiresAuth:true}` | 做题(旧版) |
| `/mastery-board` | MasteryBoard | `{requiresAuth:true}` | 掌握度看板 |
| `/learning-plan` | LearningPlan | `{requiresAuth:true}` | 学习计划 |
| `/plan-preview` | PlanPreview | `{requiresAuth:true}` | 计划预览 |
| `/plan-detail/:id` | PlanDetail | `{requiresAuth:true}` | 计划详情 |
| `/profile-card` | ProfileCard | `{requiresAuth:true}` | 个人画像星图 |
| `/qa` | QAPage | `{requiresAuth:true}` | 帮助中心 |
| `/message` | MessageCenter | `{requiresAuth:true}` | 消息中心 |
| `/api-center` | ApiCenter | `{requiresAuth:true}` | API 中心 |
| `/open-source` | OpenSource | `{requiresAuth:true}` | 开源项目 |
| `/community` | Community (子路由) | `{requiresAuth:true}` | 社区 (8 子路由) |
| `/xiaoji/settings` | XiaojiSettings | `{requiresAuth:true}` | 小吉设置 |
| `/xiaoji/call` | XiaojiCall | `{requiresAuth:true}` | 小吉通话 |
| **学科计划 (新)** |
| `/subject-plan` | SyllabusHub | `{requiresAuth:true}` | ★ 考纲列表 |
| `/subject-plan/:syllabusId` | SyllabusDetail | `{requiresAuth:true}` | ★ 考纲详情 |
| `/subject-plan/:syllabusId/practice` | SubjectPractice | `{requiresAuth:true}` | ★ 做题页 |
| **管理后台** |
| `/admin` | AdminLayout (子路由) | `{requiresAuth, requiresAdmin}` | 管理后台 |

### 7.2 路由守卫逻辑

`router.beforeEach()` 中的判定链（按优先级）：

```
1. 未登录 访问 requiresAuth 页面 → redirect /login?redirect=原路径
2. 非管理员 访问 requiresAdmin 页面 → redirect /home
3. 已登录 访问 /login 或 /        → redirect /onboarding (需引导) 或 /home
4. 已登录 访问 /home 且需引导      → redirect /onboarding
5. 已登录 访问 /onboarding 且无需引导且非编辑模式 → redirect /home
6. 其他情况 → 放行
```

**`needsOnboarding` 判断**：`isLoggedIn && !user.learning_stage` — 用户已登录但未设置学习阶段。

### 7.3 核心页面详解

#### 7.3.1 SyllabusHub（考纲列表）

**功能**：
- 17 考纲卡片网格布局
- 搜索（按名称模糊匹配）
- 筛选（按题目数量范围 / 是否有计划）
- 收藏（localStorage 持久化，key: `jizhi-fav-syllabi`）
- 每张卡片显示：缩写标 + 颜色 + 名称 + 简介 + 题目数 + 计划状态

**N+1 优化**：所有用户的计划通过一次 `In()` 查询批量获取，不做逐考纲请求。

#### 7.3.2 SyllabusDetail（考纲详情）— 5 Tab 总控台

| Tab | 内容 | 认证要求 | 计划要求 |
|-----|------|---------|----------|
| 概览 | intro + suitable_for + 维度卡片 + 3 个真题按钮 + 诊断/题库入口 | 否 | 否 |
| 题库 | 题目列表 + 分类筛选 + 题型筛选 + 搜索 + 收藏 + 分页 + 题目颜色状态条 | 否 | 否 |
| 每日任务 | 当天任务列表 + 已分配题目 + 做题按钮 | 是 | 是 |
| 知识点 | 掌握度列表（名称/分数/总次数/正确次数/最后练习时间） | 是 | 是 |
| 错题本 | 错题列表 + 题目详情 + 答错次数 | 是 | 是 |

**题目颜色状态条**：
```css
.red    → rate < 40%  → 薄弱 (weak)
.yellow → 40% ≤ rate < 60% → 待巩固 (consolidating)
.green  → rate ≥ 60% → 优势 (strong)
```

#### 7.3.3 SubjectPractice（做题页）

**布局切换**：
- 非编程题 → 单栏居中 (题目面板 + 选项/答案区 + 提交按钮)
- 编程题 → 左右分栏 OJ 风格
  - 左 34%：题目面板（独立滚动） + 输入输出说明 + 限制条件 + 样例
  - 右 66%：暗色终端代码编辑器 + `<details>` 折叠自定义输入 + ▶运行 + 提交

**11 种题型渲染**：
```vue
<!-- choice / choice_single → 单选按钮组 -->
<template v-if="isSingleChoice(qtype)">...</template>

<!-- choice_multi / choice_indefinite → 多选复选框 -->
<template v-else-if="isMultiChoice(qtype)">...</template>

<!-- fill → 输入框 -->
<template v-else-if="qtype === 'fill'">...</template>

<!-- cloze → 多个下拉框 -->
<template v-else-if="qtype === 'cloze'">...</template>

<!-- calculation → 数值输入框 -->
<template v-else-if="qtype === 'calculation'">...</template>

<!-- translation/essay/short_answer/... → 多行文本框 -->
<template v-else-if="isLongTextType(qtype)">...</template>

<!-- programming → 代码编辑器分栏 (特殊处理) -->
<template v-else-if="qtype === 'programming'">...</template>
```

**倒计时器**：正向计时，换题自动重置，提交停止。格式 `⏱ MM:SS`。

**编程题特性**：
- 代码编辑器：`#0a0f1a` 暗色底 + 等宽字体 + Tab 缩进 + Enter 自动缩进
- 语言选择器：`<select>` 下拉，选项从考纲 `languages` 字段取
- 语言记忆：`localStorage.setItem('code-language-{syllabusId}', lang)`
- 判题动画：逐测试点顺序揭示，AC 绿色 / WA 红色 / TLE 黄色 / RE 紫色

---

## 8. 数据库设计

### 8.1 ER 图（实体关系）

```
profiles (Supabase Auth)
  │
  │ 1:N
  ▼
subject_plans ──────────┬────────── plan_daily_tasks
  │ id (PK)             │             │ id (PK)
  │ user_id (FK)        │             │ plan_id (FK)
  │ syllabus_id          │             │ day_number
  │ name                 │             │ question_ids[]
  │ goal_score           │             │ completed_ids[]
  │ period_days          │             │ completed
  │ status               │             └────────────┘
  │
  ├─── diagnosis_results
  │      │ id (PK)
  │      │ plan_id (FK)
  │      │ answers (JSONB)
  │      │ accuracy
  │
  ├─── question_records
  │      │ id (PK)
  │      │ user_id (FK)
  │      │ plan_id (FK)
  │      │ question_id
  │      │ user_answer (JSONB)
  │      │ is_correct
  │      │ source
  │      │ time_spent
  │
  └─── user_kp_mastery
         │ id (PK)
         │ user_id (FK)
         │ plan_id (FK)
         │ kp_id, kp_name
         │ mastery_score
         │ correct_count, total_count

管理后台表:
  user_feedback ───────── content_reports ───────── user_qa
  system_announcements    admin_audit_logs
```

### 8.2 学科计划核心表 DDL

#### subject_plans
```sql
CREATE TABLE IF NOT EXISTS subject_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    syllabus_id TEXT,         -- ★ 关联考纲 ID (cet4, cet6, ...)
    subject TEXT NOT NULL DEFAULT 'cet4',
    name TEXT NOT NULL DEFAULT 'CET-4 备考计划',
    goal_score INTEGER NOT NULL DEFAULT 425,
    period_days INTEGER NOT NULL DEFAULT 30,
    daily_minutes INTEGER NOT NULL DEFAULT 60,
    daily_question_count INTEGER NOT NULL DEFAULT 0,
    total_days INTEGER NOT NULL DEFAULT 0,
    completed_days INTEGER NOT NULL DEFAULT 0,
    total_questions INTEGER NOT NULL DEFAULT 0,
    completed_questions INTEGER NOT NULL DEFAULT 0,
    end_date TEXT,            -- ★ 计划结束日期 (YYYY-MM-DD)
    status TEXT NOT NULL DEFAULT 'active',  -- active / paused / completed / archived
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- 索引
CREATE INDEX IF NOT EXISTS idx_subject_plans_user ON subject_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_subject_plans_status ON subject_plans(status);
```

#### plan_daily_tasks
```sql
CREATE TABLE IF NOT EXISTS plan_daily_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL,
    user_id UUID,
    day_number INTEGER NOT NULL DEFAULT 1,
    title TEXT,               -- 任务标题 (e.g. "高频词练习")
    question_type TEXT,       -- 题型 (e.g. "choice")
    category TEXT,            -- 分类 (e.g. "vocabulary")
    question_count INTEGER DEFAULT 5,
    estimated_minutes INTEGER DEFAULT 15,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### diagnosis_results
```sql
CREATE TABLE IF NOT EXISTS diagnosis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL,
    user_id UUID NOT NULL,
    answers JSONB DEFAULT '[]',   -- 数组: [{question_id, user_answer, is_correct, ...}]
    accuracy INTEGER DEFAULT 0,
    correct_count INTEGER DEFAULT 0,
    total_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### question_records
```sql
CREATE TABLE IF NOT EXISTS question_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    plan_id UUID NOT NULL,
    question_id TEXT NOT NULL,    -- 题目ID (对应 JSON 中的 id)
    task_id UUID,
    source TEXT DEFAULT 'daily',  -- daily / free / diagnosis
    user_answer TEXT,             -- 用户答案 (JSON 或 文本)
    is_correct BOOLEAN DEFAULT FALSE,
    score INTEGER DEFAULT 0,
    ai_feedback JSONB DEFAULT '{}',
    time_spent INTEGER DEFAULT 0, -- 用时(秒)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- 索引
CREATE INDEX IF NOT EXISTS idx_question_records_user ON question_records(user_id);
CREATE INDEX IF NOT EXISTS idx_question_records_plan ON question_records(plan_id);
CREATE INDEX IF NOT EXISTS idx_question_records_correct ON question_records(is_correct);
```

#### user_kp_mastery
```sql
CREATE TABLE IF NOT EXISTS user_kp_mastery (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    plan_id UUID NOT NULL,
    kp_id TEXT NOT NULL,
    kp_name TEXT DEFAULT '',
    category TEXT DEFAULT '',
    sub_category TEXT DEFAULT '',
    mastery_score NUMERIC(5,1) DEFAULT 0,   -- ★ EWMA 分数 0-100
    correct_count INTEGER DEFAULT 0,
    total_count INTEGER DEFAULT 0,
    last_practiced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, plan_id, kp_name)       -- ★ 每个计划每个知识点仅一行
);
```

### 8.3 管理员系统表 DDL

#### user_feedback
```sql
CREATE TABLE IF NOT EXISTS user_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID, nickname TEXT, email TEXT,
    feedback_type TEXT,              -- bug / suggestion / other
    content TEXT NOT NULL,
    status TEXT DEFAULT 'pending',   -- pending / resolved
    admin_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);
```

#### content_reports
```sql
CREATE TABLE IF NOT EXISTS content_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reporter_id UUID, reporter_nickname TEXT,
    target_type TEXT NOT NULL,       -- post / comment
    target_id UUID, reason TEXT,
    status TEXT DEFAULT 'pending',   -- pending / resolved / dismissed
    admin_id UUID, admin_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);
```

#### system_announcements
```sql
CREATE TABLE IF NOT EXISTS system_announcements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT,
    image_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### admin_audit_logs
```sql
CREATE TABLE IF NOT EXISTS admin_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID NOT NULL,
    admin_nickname TEXT,
    action TEXT NOT NULL,            -- ban_user / set_admin / create_question / resolve_report / ...
    target_type TEXT,                -- user / post / question / report / feedback / ...
    target_id TEXT,
    detail JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 8.4 本地题库数据模型

题库是 **17 个独立 JSON 文件**，不在 Supabase 中。每道题目的 JSON Schema：

```json
{
  "id": "cet4-vocab-001",
  "category": "vocabulary",
  "sub_category": "高频核心词",
  "kp_id": "cet4-vocab-highfreq",
  "kp_name": "高频词辨析",
  "question_type": "choice",
  "difficulty": 2,
  "content": {
    "stem": "The company has ____ a new policy...",
    "options": ["A. adopted", "B. adapted", "C. adjusted", "D. admitted"],
    "input_description": "输入格式说明",       // 仅编程题
    "output_description": "输出格式说明",      // 仅编程题
    "constraints": "数据范围",                // 仅编程题
    "test_cases": [                           // 仅编程题
      { "input": "样例输入", "output": "样例输出", "description": "说明" }
    ]
  },
  "answer": "A",                              // choice: "A", fill: "word", programming: "参考代码"
  "explanation": "adopt 意为「采纳」...",
  "distractor_analysis": {                    // 干扰项分析 (可选)
    "B": "adapt 意为「适应」",
    "C": "adjust 意为「调整」",
    "D": "admit 意为「承认」"
  }
}
```

### 8.5 索引策略

| 表 | 索引 | 查询场景 |
|----|------|----------|
| `subject_plans` | `user_id`, `status` | 用户计划列表 |
| `plan_daily_tasks` | `plan_id` | 按计划查任务 |
| `question_records` | `user_id`, `plan_id`, `is_correct` | 已做题目/错题查询 |
| `user_kp_mastery` | `user_id`, `plan_id` | 掌握度查询 |
| `user_feedback` | `status`, `created_at DESC` | 待处理反馈排序 |
| `content_reports` | `status`, `(target_type, target_id)` | 举报查询 |
| `admin_audit_logs` | `admin_id`, `action`, `created_at DESC` | 日志查询 |

---

## 9. 认证与安全体系

### 9.1 认证架构

```
┌─────────────────────────────────────────────────────────┐
│                    认证入口                              │
│                                                         │
│  来源 A: 邮箱密码登录     来源 B: 微信扫码登录            │
│  ┌─────────────────┐   ┌──────────────────────┐        │
│  │ POST /auth/login │   │ GET /auth/wechat/     │        │
│  │ → Supabase Auth  │   │   qrcode → callback   │        │
│  │ → 返回 Supabase  │   │   → poll/login        │        │
│  │   JWT            │   │ → 自签 JWT (HS256)    │        │
│  └────────┬────────┘   └──────────┬───────────┘        │
│           │                       │                     │
│           ▼                       ▼                     │
│  ┌─────────────────────────────────────────────────┐   │
│  │            Token: Authorization Header           │   │
│  │           Authorization: Bearer <token>          │   │
│  └─────────────────────┬───────────────────────────┘   │
│                        │                                │
│                        ▼                                │
│  ┌─────────────────────────────────────────────────┐   │
│  │       auth_middleware.get_current_user()          │   │
│  │                                                   │   │
│  │  Step 1: 尝试自签 JWT 解码                        │   │
│  │    jwt.decode(token, JWT_SECRET, HS256)            │   │
│  │    → 成功: 返回 payload.sub (user_id)              │   │
│  │    → ExpiredSignatureError → HTTP 401              │   │
│  │    → InvalidTokenError → 继续 Step 2               │   │
│  │                                                   │   │
│  │  Step 2: Supabase Auth 验证                        │   │
│  │    GET https://xxx.supabase.co/auth/v1/user        │   │
│  │    Authorization: Bearer <token>                   │   │
│  │    apikey: SUPABASE_KEY                            │   │
│  │    → 200: 返回 user_id                             │   │
│  │    → 4xx/5xx: HTTP 401/503                         │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 9.2 JWT 双模验证流程

```python
# backend/utils/auth_middleware.py (79行)
async def get_current_user(authorization: str = Header(None)) -> str:
    # 1. 提取 token
    token = authorization.replace("Bearer ", "").strip()

    # 2. 尝试自签 JWT (微信登录 token，本地零延迟)
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub") or payload.get("user_id")
        if user_id:
            return user_id     # ← 成功，立刻返回
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token 已过期")
    except jwt.InvalidTokenError:
        pass                   # ← 不是自签 JWT，继续走 Supabase

    # 3. Supabase 验证 (邮箱登录 token，需网络请求)
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.get(
            f"{settings.SUPABASE_URL}/auth/v1/user",
            headers={"apikey": settings.SUPABASE_KEY, "Authorization": f"Bearer {token}"}
        )
        if res.status_code != 200:
            raise HTTPException(401, "Token 无效或已过期")
        return res.json().get("id")
```

**设计优势**：
- 自签 JWT 验证在本地完成，零网络延迟，Supabase 宕机时微信用户仍可正常使用
- 优先验证自签 JWT 是因为它更快且更可靠（不依赖外部服务）
- Supabase JWT 作为补充，兼容传统的邮箱密码登录

### 9.3 三级角色鉴权

`profiles` 表的 `role` 字段（TEXT）控制权限：

| 角色 | 标识 | 权限 |
|------|------|------|
| `super_admin` | `role = 'super_admin'` | 全部权限 + 设/撤管理员 + 审计日志查看 |
| `admin` | `role = 'admin'` 或 `is_admin = TRUE` | 用户管理 + 内容审核 + 题库 CRUD + 公告 |
| `user` | `role = 'user'` 或其他 | 无后台权限 |

```python
# backend/utils/admin_middleware.py (96行)
async def get_current_admin(current_user = Depends(get_current_user)) -> str:
    """验证管理员身份"""
    # 用 service_role key 查 profiles (绕过 RLS)
    res = await client.get(
        f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{current_user}&select=role,is_admin"
    )
    role = data[0].get("role", "")
    is_admin = data[0].get("is_admin", False)
    if role not in ("admin", "super_admin") and not is_admin:
        raise HTTPException(403, "无权访问管理后台")
    return current_user

async def get_current_super_admin(current_user = Depends(get_current_user)) -> str:
    """验证超级管理员身份"""
    # 同上，但要求 role == "super_admin"
```

### 9.4 微信 OAuth 接入

```
配置前提：
  1. 前往 https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login
     扫码获取测试号 appID 和 appsecret
  2. 在测试号页面配置「授权回调页面域名」为后端外网 IP (不含端口号)
  3. 确保后端监听标准 HTTP 端口 (80)，微信不允许非标准端口回调

OAuth 流程图:
  ┌─ 网页端 ────────────────────────────────────────────┐
  │                                                      │
  │  GET /auth/wechat/qrcode                              │
  │  ← 返回 { qrcode: "data:image/png;base64,...",       │
  │            poll_token: "xxx" }                        │
  │                                                      │
  │  显示二维码                                           │
  │  开始轮询: GET /auth/wechat/poll/{token} (每2秒)      │
  │  ← { ready: false }  ... 直到结果                     │
  │                                                      │
  └──────────────────────────────────────────────────────┘
                          │
         用户用手机微信扫二维码
                          │
                          ▼
  ┌─ 微信服务器 ─────────────────────────────────────────┐
  │                                                      │
  │  微信浏览器访问:                                      │
  │  https://open.weixin.qq.com/connect/oauth2/authorize  │
  │    ?appid=...&redirect_uri=                           │
  │     {BACKEND_EXTERNAL_URL}/auth/wechat/callback       │
  │    &scope=snsapi_userinfo&state={state}               │
  │                                                      │
  │  用户点击授权                                         │
  │                                                      │
  │  重定向到: GET /auth/wechat/callback?code=&state=     │
  │                                                      │
  └──────────────────────────────────────────────────────┘
                          │
                          ▼
  ┌─ 后端 callback ──────────────────────────────────────┐
  │                                                      │
  │  1. state → 查 _state_map → 获取 poll_token + mode   │
  │  2. code → POST api.weixin.qq.com/sns/oauth2/        │
  │           access_token → openid + nickname + avatar  │
  │                                                      │
  │  3. if mode == "bind":                               │
  │       写 openid → profiles (已登录用户的绑定)         │
  │       _poll_results[poll_token] = { bound: true }    │
  │                                                      │
  │  4. if mode == "login":                              │
  │       查 profiles.wechat_openid = openid             │
  │       → 找到: 签发 JWT, _poll_results[poll_token]    │
  │               = { access_token, user }                │
  │       → 未找到: _poll_results[poll_token]            │
  │               = { bound: false }                     │
  │                                                      │
  └──────────────────────────────────────────────────────┘
```

### 9.5 速率限制与安全措施

| 端点 | 限制 | 窗口 | 实现 |
|------|------|------|------|
| `POST /auth/login` | 同一 IP+账号 5 次 | 60s | `rate_limit.py` 内存计数器 |
| `POST /auth/send-code` | 同一 IP+邮箱 1 次 | 60s | `rate_limit.py` 内存计数器 |
| `POST /auth/register` | 同一 IP 3 次 | 60s | `rate_limit.py` 内存计数器 |
| 上传图片 | 类型限制 PNG/JPEG/GIF/WebP + 5MB 上限 | — | admin.py 校验 |
| 头像上传 | 强制 resize → 200×200 PNG | — | Pillow 处理 |

**XSS 防护**：`SubjectPractice.vue` 中使用 `v-html` 渲染完形填空题干前，通过 `fillStemHtml()` 函数剥离所有 HTML 标签。

---

## 10. AI 集成

### 10.1 LLM 客户端

`backend/agents/llm_client.py` (45行)：

```python
from openai import OpenAI

def call_llm(messages, temperature=0.7, use_cache=True) -> str:
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        timeout=60.0          # ← 客户端级别超时
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        temperature=temperature,
        stream=False,
        timeout=55.0,          # ← 请求级别超时
        max_tokens=8192,
    )
    return response.choices[0].message.content

def call_llm_stream(messages, temperature=0.7):
    """流式调用，用于 AI 对话"""
    # 同上，但 stream=True
    for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

**超时策略**：
- 客户端超时 (60s)：如果 DeepSeek 完全无响应
- 请求超时 (55s)：如果请求建立了连接但耗时过长
- 双超时保证任何 AI 请求不会永久挂起

### 10.2 AI 批改引擎

主观题批改流程（`subject_plan.py` `submit_answer()`）：

```python
# AI 批改题型列表
AI_JUDGE_TYPES = {
    "translation", "essay", "short_answer",
    "case_analysis", "teaching_design",
    "programming", "calculation", "analysis"
}

# 批改 Prompt 模板
prompt = f"""批改以下{type_label}题：
题目: {stem}
参考答案: {ref}
学生答案: {user_answer}

输出 JSON：
{{"score": 0-100, "is_pass": true/false,
  "feedback": "简短批改意见（50字内）",
  "highlights": ["亮点", "改进点"]}}
"""

# 使用 low temperature 保证一致性
fb = call_llm([...], temperature=0.3)  # ← 0.3: 减少随机性，评分更稳定
```

**JSON 容错**：
```python
m = re.search(r'\{[\s\S]*\}', fb)       # 从 AI 回复中提取 JSON 块
if m:
    ai_feedback = json.loads(m.group())
```

### 10.3 AI 学习规划生成

```python
# temperature=0.7: 有一定随机性但结构可控
plan_prompt = f"""
你是学习规划专家。根据诊断结果生成备考计划：
- 考纲名称/维度/可用题型
- 目标分数/学习天数/每日分钟
- 诊断正确率 + 逐题详情

返回 JSON 格式：
{{
  "plan_name": "xxx",
  "daily_tasks": [
    {{"day_number": 1, "tasks": [
      {{"title": "...", "type": "choice", "category": "vocabulary",
        "question_count": 5, "minutes": 15}}
    ]}}
  ]
}}
"""
ai_resp = call_llm([...], temperature=0.7)

# JSON 提取 + 解析
json_match = re.search(r'\{[\s\S]*\}', ai_resp)
plan_data = json.loads(json_match.group())

# Fallback: AI 失败时用默认计划
if not plan_data:
    plan_data = { "plan_name": f"{考纲名} 备考计划", "daily_tasks": [...] }
```

### 10.4 题库批量生成

`backend/scripts/seed_all_banks.py` 的生成策略：

```
输入: syllabi.json (17 考纲 × 目标题量)
      已有题库文件 (*.json)

算法:
  for each syllabus:
      current = len(load_questions(bank_file))
      needed = target_count - current
      per_dim = needed / len(dimensions) + 5

      for each dimension:
          for each batch (BATCH_SIZE=6):
              1. 轮换子分类和题型 (dim_done % len(subs/types) 取模)
              2. build_prompt() → 构造题型特定的 prompt
              3. call_llm(t=0.7) → 获取 AI 响应
              4. 括号计数法提取 JSON 数组 (处理嵌套 [])
              5. 剥离 markdown 代码块 (```json ... ```)
              6. 修复尾逗号、截断
              7. 逐字符回退修复
              8. 类型过滤 (只保留 dict 条目)
              9. 补充 category/sub_category/kp_name/question_type
              10. save_questions() → 去重 → 写入 JSON
              sleep(1.5s)
```

**JSON 提取容错链**：正则初步匹配 → 括号计数 → 代码块剥离 → 尾逗号修复 → 逐字符回退 → 类型过滤。每道题都保证有 `id` (UUID)、`category`、`sub_category`、`question_type` 等必要字段。

---

## 11. 代码判题沙箱

### 11.1 沙箱架构

```
POST /subject-plan/code/submit
  │
  ├── 1. 从本地题库获取题目 (bank_get_by_ids)
  │     → content.test_cases[] 或 content 文本中的 ---TEST_CASES--- 块
  │
  ├── 2a. 有测试用例 → 沙箱执行模式
  │     │
  │     │   for each test_case:
  │     │       ├─ Python → _run_python_local()
  │     │       │   subprocess.run([sys.executable, tmp.py],
  │     │       │                  input=stdin, timeout=5s)
  │     │       │
  │     │       ├─ C/C++ → _run_compiled_local()
  │     │       │   gcc/g++ src.c -o exe → ./exe < stdin
  │     │       │
  │     │       ├─ Java → _run_compiled_local()
  │     │       │   javac Main.java → java Main < stdin
  │     │       │
  │     │       └─ 无编译器 → 回退 AI 批改
  │     │
  │     │   执行完毕后:
  │     │       judge_test_case(stdout, expected) → AC/WA
  │     │       检查 exit_code → RE
  │     │       检查 timeout → TLE
  │     │
  │     └── 返回测试结果数组 + 总分
  │
  └── 2b. 无测试用例 → AI 批改降级模式
        call_llm(programming judge prompt, t=0.3)
        → { score, is_pass, feedback }
```

### 11.2 编译器发现与配置

```python
# compiler 发现优先级
def _find_compiler(names: list[str]) -> str | None:
    # 1. 内置路径 (utils/mingw/bin/)
    for base in [_MINGW_BIN, _JDK_BIN]:
        for name in names:
            if (base / f"{name}.exe").exists():
                return str(base / f"{name}.exe")

    # 2. winget 安装路径
    #    ~/AppData/Local/Microsoft/WinGet/Packages/*WinLibs*/mingw64/bin/
    if _WINGET_MINGW_BIN:
        for name in names:
            if (_WINGET_MINGW_BIN / f"{name}.exe").exists():
                return str(_WINGET_MINGW_BIN / f"{name}.exe")

    # 3. 系统 PATH
    import shutil
    for name in names:
        found = shutil.which(name)
        if found: return found

    return None
```

**编译器安装** (Windows)：
```powershell
# MinGW GCC/G++ (C/C++ 判题)
winget install WinLibs.MinGW-w64

# OpenJDK (Java 判题)
winget install Microsoft.OpenJDK.17
```

### 11.3 测试点评分系统

```python
def judge_test_case(stdout: str, expected: str) -> bool:
    # 策略 1: 逐行精确匹配 (去首尾空白)
    out_lines = stdout.strip().splitlines()
    exp_lines = expected.strip().splitlines()
    if len(out_lines) == len(exp_lines):
        for a, b in zip(out_lines, exp_lines):
            if a.strip() == b.strip(): continue
            try:  # 浮点数容差
                if abs(float(a.strip()) - float(b.strip())) < 1e-6:
                    continue
            except (ValueError, TypeError): pass
            return False
        return True

    # 策略 2: 单行匹配 (忽略空格差异)
    out_flat = stdout.strip().replace(" ", "").replace("\n", "")
    exp_flat = expected.strip().replace(" ", "").replace("\n", "")
    return out_flat == exp_flat
```

**测试点结果状态**：
```python
if result.get("timeout"):
    status = "TLE"                    # Time Limit Exceeded – 黄色
elif result.get("exit_code", 0) != 0:
    status = "RE"                     # Runtime Error – 紫色
elif judge_test_case(stdout, expected):
    status = "AC"                     # Accepted – 绿色
else:
    status = "WA"                     # Wrong Answer – 红色
```

### 11.4 安全边界与限制

- 代码写入**临时文件** → subprocess 执行 → 执行后**立刻删除**临时文件
- 默认执行超时 **5 秒**，测试点可自定义 `timeout_ms`
- 无持久化进程，无网络访问权限（subprocess 默认不继承网络 socket）
- 编译错误直接返回 `stderr`，不影响沙箱进程
- **仅 Linux/macOS 上 Piston 有真正隔离**；本地 subprocess 依赖于操作系统级别的进程隔离

---

## 12. 管理后台

### 12.1 功能全景

| 页面 | 路由 | 组件 | 核心功能 | 权限 |
|------|------|------|----------|------|
| 仪表盘 | `/admin` | AdminDashboard | 7 项统计卡片 + 快捷入口 | admin+ |
| 用户管理 | `/admin/users` | AdminUsers | 列表搜索/封禁/设管理员（超管）/用户详情 | admin+ |
| 内容审核 | `/admin/reports` | AdminReports | 举报/反馈/Q&A 三 Tab 审核 | admin+ |
| 题库管理 | `/admin/questions` | AdminQuestions | 题目 CRUD + 筛选 + 批量导入 | admin+ |
| 公告管理 | `/admin/announcements` | AdminAnnouncements | 公告 CRUD + 图片上传 | admin+ |
| 操作日志 | `/admin/logs` | AdminLogs | 审计日志查询 | admin+ |

### 12.2 审计日志系统

每次管理员操作自动调用 `write_audit_log()`：

```python
async def write_audit_log(admin_id, action, target_type, target_id, detail):
    """非阻塞写入审计日志（失败不影响主流程）"""
    try:
        # 获取管理员昵称
        nick = await client.get(f"/profiles?id=eq.{admin_id}&select=nickname")

        # 写入日志
        await client.post("/admin_audit_logs", json={
            "admin_id": admin_id,
            "admin_nickname": nick,
            "action": action,           # e.g. "ban_user", "delete_question"
            "target_type": target_type, # e.g. "user", "question"
            "target_id": target_id,
            "detail": detail or {}
        })
    except Exception:
        pass  # ← 日志写入失败不抛异常
```

### 12.3 题库管理 CRUD

所有题库操作通过 `local_question_bank` 模块：

```
新增题目: POST /admin/questions?syllabus_id=cet4
  → add_questions(sid, [new_q])      # 追加到内存 + 持久化 JSON

更新题目: PUT /admin/questions/{id}
  → find_question_global(id)         # 跨考纲查找
  → q.update(update_data)            # 更新内存对象
  → save_bank_to_file(sid)           # 写回 JSON 文件

删除题目: DELETE /admin/questions/{id}
  → delete_question_global(id)       # 从内存列表 + index 移除
  → save_bank_to_file(sid)           # 写回 JSON 文件

批量导入: POST /admin/questions/import?syllabus_id=cet4
  → add_questions(sid, [...])        # 去重 + 追加 + 持久化
```

所有 CRUD 操作触发审计日志写入。

---

## 13. 本地题库引擎

### 13.1 设计动机

原系统题库存储在 Supabase 中，每次查询都需要 HTTP 请求往返：

```
旧方案: 前端 → 后端 → Supabase HTTP GET → 返回 → 筛选
         110 题 3 次往返，每次 ~200ms → 共 ~600ms

新方案: 前端 → 后端 → 内存 dict[key]  O(1) 查找
         110 题 1 次内存查找 < 1ms
```

### 13.2 数据加载流程

```python
# backend/local_question_bank.py
DATA_DIR = Path(__file__).parent / "data"
_banks: dict[str, dict] = {}  # syllabus_id → {questions: [...], index: {id: q}}

def load():
    syllabi = json.load(open(DATA_DIR / "syllabi.json"))

    for s in syllabi:
        bank_file = s.get("question_bank")
        if not bank_file: continue

        questions = json.load(open(DATA_DIR / bank_file))
        _banks[s["id"]] = {
            "questions": questions,          # list[dict] — 用于筛选/搜索
            "index": {q["id"]: q for q in questions}  # dict — O(1) 精确查找
        }

    total = sum(len(b["questions"]) for b in _banks.values())
    print(f"[题库] 总计 {len(_banks)} 个考纲题库，{total} 道题目")

# 模块导入时自动加载
load()
```

**内存占用估算**：
- 17 个 JSON 文件合计 ~21MB
- Python 内存 dict/list 开销 ~2-3x → 总内存约 50-60MB
- 远低于现代服务器的可用内存

### 13.3 查询与筛选机制

```python
def query(syllabus_id, category=None, sub_category=None,
          question_type=None, difficulty=None, search=None,
          limit=20, offset=0, random_order=False,
          exclude_ids=None) -> tuple[list[dict], int]:

    bank = _banks.get(syllabus_id)
    results = bank["questions"]  # 起始：全部题目

    # 逐步过滤（Python 列表推导式，O(n) 但 n 最大仅 1769）
    if category:      results = [q for q in results if q.get("category") == category]
    if sub_category:  results = [q for q in results if q.get("sub_category") == sub_category]
    if question_type: results = [q for q in results if q.get("question_type") == question_type]
    if difficulty:    results = [q for q in results if q.get("difficulty") == difficulty]
    if exclude_ids:   results = [q for q in results if q.get("id") not in exclude_ids]
    if search:
        kw = search.lower()
        results = [q for q in results
                   if kw in _get_stem(q) or kw in (q.get("kp_name") or "").lower()]

    total = len(results)

    if random_order: random.shuffle(results)
    return results[offset:offset+limit], total
```

**复杂度**：最坏 O(N) 遍历整个题库（最大 1769 题），Python 列表推导式约 0.1-0.5ms，远低于网络请求延迟。无分页的全局 count 也是 O(1)（`len(bank["questions"])`）。

### 13.4 持久化与热更新

```python
# 持久化：修改后完整写入 JSON 文件
def save_bank_to_file(syllabus_id):
    for s in syllabi:
        if s["id"] == syllabus_id and s.get("question_bank"):
            with open(DATA_DIR / s["question_bank"], "w", encoding="utf-8") as f:
                json.dump(bank["questions"], f, ensure_ascii=False, indent=2)

# 热更新：管理员新增/删除题目后无需重启
def reload():
    global _banks
    _banks = {}
    load()
```

---
---

## 14. 设计规范与 UX 指南

### 14.1 视觉风格定义

```css
/* ===== 核心颜色 ===== */
--bg-deep:        #080d18;      /* 深空背景 */
--glass-bg:       rgba(255,255,255,0.04);
--glass-border:   rgba(255,255,255,0.08);
--text-primary:   #e8ecf1;
--text-secondary: #8892a4;

/* ===== 毛玻璃 ===== */
.card {
  background: var(--glass-bg);
  backdrop-filter: blur(24px) saturate(1.2);
  -webkit-backdrop-filter: blur(24px) saturate(1.2);
  border: 1px solid var(--glass-border);
  border-radius: 16px;
}

/* ===== 呼吸光晕边框 ===== */
.card::before {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: inherit;
  background: linear-gradient(135deg,
    rgba(108,140,255,0.4), rgba(0,255,200,0.2),
    rgba(108,140,255,0.4));
  z-index: -1;
  animation: border-sweep 3s ease-in-out infinite;
}
@keyframes border-sweep {
  0%, 100% { opacity: 0.3; }
  50%      { opacity: 0.7; }
}

/* ===== 粒子网格背景 ===== */
body {
  background-color: var(--bg-deep);
  background-image:
    linear-gradient(rgba(108,140,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(108,140,255,0.03) 1px, transparent 1px);
  background-size: 60px 60px;
  mask-image: radial-gradient(ellipse at center,
    black 30%, transparent 70%);
}

/* ===== 按钮光泽扫光 ===== */
.btn::after {
  content: '';
  position: absolute;
  top: 0; left: -100%;
  width: 100%; height: 100%;
  background: linear-gradient(90deg,
    transparent, rgba(255,255,255,0.15), transparent);
  transition: left 0.6s ease;
}
.btn:hover::after {
  left: 100%;
}

/* ===== 侧边栏 ===== */
.sidebar {
  background: rgba(10, 15, 28, 0.85);
  backdrop-filter: blur(20px);
  /* 淡彩流光 */
  &::before {
    background: linear-gradient(135deg,
      rgba(138, 43, 226, 0.15),   /* 紫 */
      rgba(70, 130, 255, 0.15),   /* 蓝 */
      rgba(0, 200, 180, 0.1),     /* 青 */
      rgba(100, 220, 100, 0.1),   /* 绿 */
      rgba(138, 43, 226, 0.15)    /* 紫 */
    );
  }
}

/* ===== 代码编辑器 ===== */
.code-editor {
  background: #0a0f1a;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  border: 1px solid rgba(0, 255, 150, 0.2);
  box-shadow: 0 0 20px rgba(0, 255, 150, 0.05);
}
```

### 14.2 动画与过渡规范

| 动画 | 用途 | 实现 |
|------|------|------|
| `page-fade` | 路由页面切换 (方向改变) | `opacity 0.25s + translateY(±8px)` |
| `page-slide` | 同层级子页切换 | `opacity 0.25s + translateX(±16px)` |
| `card-enter` | 卡片入场 | `opacity 0→1 + translateY(12px→0)` |
| `row-reveal` | 列表行交错入场 | `transition-delay: calc(var(--i) * 60ms)` |
| `border-sweep` | 卡片边框呼吸 | `opacity 0.3↔0.7, 3s infinite` |
| `btn-shine` | 按钮扫光 | `::after translateX(-100%→100%), 0.6s` |
| `test-reveal` | 判题结果逐测试点揭示 | 每个测试点 `transition-delay` 递增 |

### 14.3 组件设计原则

1. **考纲图标**：双字母缩写 (abbr) + 考纲颜色 (color)，永远不用 emoji
2. **卡片样式**：统一玻璃态 (`backdrop-filter` + 半透明 bg + 细边框)
3. **交互反馈**：所有可交互元素必须有 hover（位移/光晕/边框变色）和 active 态
4. **滚动条**：统一透明底 + 半透明拇指 (6px 宽)
5. **Loading**：使用 `LoadingSpinner.vue`（科幻风格加载动画）

### 14.4 响应式与可访问性

- 当前设计以桌面端为主（≥1024px）
- 侧边栏支持收缩模式（图标更小、可滚动）
- 编程题 OJ 分栏在窄屏幕 (<900px) 可堆叠为上下布局
- 所有文本颜色满足 WCAG AA 标准 (对比度 ≥4.5:1)

---

## 15. 开发与运维

### 15.1 开发工作流

```bash
# 1. 拉取代码
git pull origin main

# 2. 后端开发 (支持热重载)
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 3. 前端开发 (支持 HMR)
cd frontend
npm run dev

# 4. API 测试 (Swagger UI)
open http://localhost:8000/docs

# 5. 题库生成
cd backend
python scripts/seed_all_banks.py              # 全部考纲
python scripts/seed_all_banks.py cet4 cet6    # 指定考纲
python scripts/seed_all_banks.py --dry        # 预览不生成

# 6. 题库统计
python scripts/check_progress.py
```

### 15.2 Git 分支策略

```
main ──── 主分支 (当前工作分支)
  ├── feat/*    功能分支
  ├── fix/*     修复分支
  └── refactor/* 重构分支
```

### 15.3 故障排查指南

| 症状 | 可能原因 | 排查步骤 |
|------|----------|----------|
| 后端启动后 401 | Supabase 项目暂停 / 未配置 | 检查 `.env` SUPABASE_URL/KEY 是否正确；Supabase Dashboard 确认项目 Active |
| 题库查询返回空 | JSON 文件不存在或格式错误 | 查看启动日志 `[题库]` 前缀；检查 `data/*.json` 文件存在且为有效 JSON |
| AI 批改一直失败 | DeepSeek API Key 无效 / 超时 | `curl -H "Authorization: Bearer $KEY" https://api.deepseek.com/v1/models` |
| 代码判题 AC/WA 异常 | 编译器未安装或版本不对 | `GET /subject-plan/code/languages` 检查返回的 available 字段 |
| 微信扫码无法回调 | 端口非80 / 域名不匹配 | 确保 `BACKEND_EXTERNAL_URL` 无端口号；检查测试号后台回调域名配置 |
| 前端 401 不断跳转登录 | localStorage token 过期 | 清除 Application → Local Storage → 重新登录 |
| npm run dev 报错 | node_modules 不完整 | `rm -rf node_modules && npm install` |
| 邮件验证码收不到 | QQ 邮箱 SMTP 授权码问题 | QQ邮箱 → 设置 → 账户 → POP3/SMTP → 开启并获取授权码 |

---

## 16. 已知问题与解决方案

以下内容来自 `PROJECT_LOG.md`（37 条已解决问题），此处仅列重要项：

| # | 问题 | 根因 | 修复 | 影响文件 |
|---|------|------|------|----------|
| 1 | 访问 `/questions` 返回 404 | FastAPI 路由 `/{plan_id}` 先匹配了 `/questions` | 调整路由注册顺序 | subject_plan.py |
| 4 | Supabase 查询延迟高 | 每次 HTTP 往返 ~200ms | 创建`local_question_bank.py` 内存加载 | local_question_bank.py |
| 8 | 掌握度每次 INSERT 新行 | 未查已有记录，字段名也不匹配 DB | 先 SELECT 再 PATCH (EWMA)，字段统一 | subject_plan.py |
| 9 | 同一考纲可堆积多个计划 | submit_diagnosis 不检查已有计划 | 提交前 `_get_user_plan()` 防重复 | subject_plan.py |
| 10 | 每日任务题目重复 | 不同任务独立查题，无去重 | 累计 `used_ids` 传递 | subject_plan.py |
| 22 | 考纲无概览入口 | 默认直接进题库 | 新增「概览」Tab 首页 + 行动按钮 | SyllabusDetail.vue |
| 26 | 管理后台多处不可用 | 题库考纲硬编码、公告缺 column、API 格式不一致 | 全部重写 + SQL 补字段 + 统一数据格式 | admin/* |
| 29 | Supabase 暂停全站 401 | 所有端点强依赖 `get_current_user` | 读操作免认证，user_id 可选 | subject_plan.py |
| 31 | Piston 公共 API 关闭 | GFW 屏蔽 + Piston 2026-02 停服 | winget MinGW 本地编译 | code_runner.py |
| 32 | AI 生成的 JSON 大量解析失败 | 截断、嵌套、尾逗号、markdown 包裹 | 括号计数 + 回退 + 剥离 + 类型过滤 | seed_all_banks.py |
| 34 | 无微信扫码登录 | 小程序有但网页版没有 | 公众号测试号 OAuth + 扫码轮询 | auth.py |
| 35 | 微信登录不安全（扫码即创建用户） | 自动创建用户有冒用风险 | 区分 login/bind 模式，login 必须已绑定 | auth.py |

---

## 17. 附录

### 17.1 环境变量完整参考

| 变量 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `DEEPSEEK_API_KEY` | ✅ | — | DeepSeek API 密钥 |
| `DEEPSEEK_BASE_URL` | ❌ | `https://api.deepseek.com` | 自定义 API 端点 |
| `SUPABASE_URL` | ✅ | — | Supabase 项目 URL |
| `SUPABASE_KEY` | ✅ | — | Supabase anon/public key |
| `SUPABASE_SERVICE_ROLE_KEY` | ✅ | — | Supabase service_role key |
| `EMAIL_HOST` | ✅ | — | SMTP 服务器地址 |
| `EMAIL_PORT` | ❌ | `587` | SMTP 端口 |
| `EMAIL_USER` | ✅ | — | 邮箱地址 |
| `EMAIL_PASSWORD` | ✅ | — | SMTP 授权码 |
| `EMAIL_RECEIVER` | ❌ | — | 默认收件人 |
| `WECHAT_WEB_APPID` | ❌ | — | 公众号测试号 appID |
| `WECHAT_WEB_SECRET` | ❌ | — | 公众号测试号 appsecret |
| `WECHAT_MP_APPID` | ❌ | `wx6db1f1a6e3f3969c` | 小程序 appID |
| `WECHAT_MP_SECRET` | ❌ | — | 小程序 appsecret |
| `JWT_SECRET` | ❌ | `jizhi-dev-...` | JWT 签名密钥 |
| `JWT_ALGORITHM` | ❌ | `HS256` | JWT 算法 |
| `JWT_EXPIRE_HOURS` | ❌ | `720` | JWT 过期时间（30天） |
| `FRONTEND_URL` | ❌ | `http://localhost:5173` | 前端地址 |
| `BACKEND_EXTERNAL_URL` | ❌ | `http://localhost:8000` | 后端外网地址（微信 OAuth 回调用） |
| `VOLC_ACCESS_KEY` | ❌ | — | 火山引擎 AK |
| `VOLC_SECRET_KEY` | ❌ | — | 火山引擎 SK |
| `ARK_API_KEY` | ❌ | — | 豆包 API Key |
| `XUNFEI_APPID` | ❌ | — | 科大讯飞 APPID |
| `XUNFEI_API_KEY` | ❌ | — | 科大讯飞 API Key |
| `XUNFEI_API_SECRET` | ❌ | — | 科大讯飞 API Secret |
| `REDIS_HOST` | ❌ | `localhost` | Redis 主机 |
| `REDIS_PORT` | ❌ | `6379` | Redis 端口 |
| `REDIS_PASSWORD` | ❌ | — | Redis 密码 |

### 17.2 考纲配置规范

新增一个考纲的完整步骤：

1. **编辑 `backend/data/syllabi.json`**，添加考纲条目（参考第 5.2 节 schema）
2. **创建题库文件** `backend/data/{question_bank}.json`，初始为 `[]`
3. **运行生成脚本** `python scripts/seed_all_banks.py {id}` 生成初始题目
4. **前端无需改动** — 考纲列表、详情、做题页均从 `syllabi.json` 动态渲染

### 17.3 题目 JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["id", "category", "sub_category", "question_type", "difficulty", "content", "answer"],
  "properties": {
    "id": { "type": "string", "description": "UUID 唯一标识" },
    "category": { "type": "string", "description": "对应 syllabi.json dimensions[].category" },
    "sub_category": { "type": "string", "description": "知识点子分类" },
    "kp_id": { "type": "string", "description": "知识点唯一标识" },
    "kp_name": { "type": "string", "description": "知识点显示名" },
    "question_type": {
      "type": "string",
      "enum": ["choice", "choice_single", "choice_multi", "choice_indefinite",
               "fill", "cloze", "translation", "essay", "short_answer",
               "calculation", "programming", "case_analysis", "teaching_design", "analysis"]
    },
    "difficulty": { "type": "integer", "minimum": 1, "maximum": 8 },
    "content": {
      "type": "object",
      "properties": {
        "stem": { "type": "string" },
        "options": { "type": "array", "items": { "type": "string" }},
        "input_description": { "type": "string" },
        "output_description": { "type": "string" },
        "constraints": { "type": "string" },
        "test_cases": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "input": { "type": "string" },
              "output": { "type": "string" },
              "description": { "type": "string" },
              "points": { "type": "integer", "default": 25 },
              "timeout_ms": { "type": "integer", "default": 5000 }
            }
          }
        }
      }
    },
    "answer": {},
    "explanation": { "type": "string" },
    "distractor_analysis": { "type": "object" }
  }
}
```

### 17.4 术语表

| 术语 | 英文 | 说明 |
|------|------|------|
| 考纲 | Syllabus | 一个标准化考试的定义，包含维度、题型、分数线、题库等 |
| 学科计划 | Subject Plan | 挂在考纲下的用户备考计划 |
| 诊断摸底 | Diagnosis | 用户首次做题评估，用于 AI 生成个性化计划 |
| 知识点掌握度 | KP Mastery | 对某个知识点（kp_name）的 EWMA 聚合分数 (0-100) |
| 题目状态 | Question State | 薄弱(weak <40%) / 待巩固(consolidating 40-60%) / 优势(strong ≥60%) |
| 每日任务 | Daily Task | 按计划天数分配的当天学习任务（含自动抽取题目） |
| 错题本 | Mistake Book | 按 plan/跨 plan 收集的答错题目列表 |
| AI 批改 | AI Judge | DeepSeek 对主观题（翻译/作文等）打分+反馈 |
| 代码判题 | Code Judge | 本地沙箱执行编程题 + 测试点评分 (AC/WA/TLE/RE) |
| EWMA | Exponentially Weighted Moving Average | 掌握度算法：`0.7×旧 + 0.3×新` |

---

> **文档结束** · 基智学习助手 (Jizhi Learn) · v2.0 · 2026-08-02
