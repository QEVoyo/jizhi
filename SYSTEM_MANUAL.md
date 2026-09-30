# 基智学习助手 (Jizhi Learn) — 系统说明书

> **文档版本** `2.2` · **最后更新** 2026-09-29
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
     - 5.1.7 [真题套卷系统](#517-真题套卷系统exampaper)
   - 5.2 [AI 对话系统](#52-ai-对话系统)
     - 5.2.1 [主对话系统 — 多智能体学习助手](#521-主对话系统chatarea-多智能体学习助手)
     - 5.2.2 [小基语音助手 — 人格化 AI 伴侣](#522-小基语音助手xiaojicall-人格化-ai-伴侣)
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
   - 5.10 [API 模型中心](#510-api-模型中心预览形式)
     - 5.10.1 [页面结构与预览形式](#5101-页面结构与预览形式)
     - 5.10.2 [模型清单](#5102-模型清单)
     - 5.10.3 [自配 Key（演示）](#5103-自配-key演示)
     - 5.10.4 [后期规划：用户自带 Key](#5104-后期规划用户自带-key)
     - 5.10.7 [实现状态与规划](#5107-实现状态与规划)
   - 5.11 [账号体系与登录](#511-账号体系与登录)
     - 5.11.0 [为什么去掉「扫码登录 + 账号绑定」](#5110-为什么去掉扫码登录--账号绑定2026-09-28)
     - 5.11.1 [小程序登录（当前实现）](#5111-小程序登录当前实现)
     - 5.11.2 [不用「账号合并」的补法](#5112--这里有个洞以及不用账号合并的补法)
     - 5.11.2b [向后兼容](#5112b-向后兼容当时特意确认过)
     - 5.11.2c [已删除的端点（历史）](#5112c-已删除的端点历史勿再引用)
     - 5.11.3 [自签 JWT 双模认证](#5113-自签-jwt-双模认证auth_middlewarepy)
     - 5.11.4 [小程序登录](#5114-小程序登录)
     - 5.11.5 [环境配置](#5115-环境配置)
     - 5.11.6 [状态管理与并发控制](#5116-登录态管理与并发控制当前实现)
     - 5.11.7 [错误处理矩阵](#5117-错误处理矩阵当前实现)
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
   - 5.13 [统一设置中心](#513-统一设置中心settings)
     - 5.13.1 [十大模块](#5131-十大模块)
     - 5.13.2 [个人中心去重](#5132-个人中心去重profile-信息展示页)
   - 5.14 [智能体中心](#514-智能体中心)
     - 5.14.1 [数据设计与触点清单](#5141-数据设计与触点清单)
     - 5.14.2 [聚合路由](#5142-聚合路由)
     - 5.14.3 [磨合规则引擎](#5143-磨合规则引擎)
     - 5.14.4 [前端页面](#5144-前端页面)
   - 5.15 [词条本](#515-词条本)
     - 5.15.1 [词条生命周期](#5151-词条生命周期)
     - 5.15.2 [数据设计](#5152-数据设计)
     - 5.15.3 [后端 API](#5153-后端-api)
     - 5.15.4 [前端交互](#5154-前端交互)
   - 5.16 [视频库](#516-视频库2026-09-04-新建)
     - 5.16.1 [生成引擎与分镜脚本](#5161-生成引擎与分镜脚本)
     - 5.16.2 [广场·详情·互动](#5162-广场详情互动)
     - 5.16.3 [播放器与视觉语言](#5163-播放器与视觉语言)
     - 5.16.4 [数据表与后台](#5164-数据表与后台)
   - 5.17 [自定义快捷键](#517-自定义快捷键2026-09-28-新增)
     - 5.17.1 [目录结构](#5171-目录结构)
     - 5.17.2 [为什么要有「分发器」这一层](#5172-为什么要有分发器这一层)
     - 5.17.3 [存储：本地缓存 + 账号权威](#5173-存储本地缓存--账号权威)
     - 5.17.4 [一个不存在过的动作](#5174-一个不存在过的动作)
   - 5.18 [异步任务队列（Redis + arq）](#518-异步任务队列redis--arq2026-09-28-新增)
     - 5.18.1 [为什么需要](#5181-为什么需要)
     - 5.18.2 [一个重要取舍：不是所有 create_task 都该迁](#5182-一个重要取舍不是所有-create_task-都该迁)
     - 5.18.3 [落地与约束](#5183-落地与约束)
     - 5.18.4 [考试批量分析没有迁](#5184--考试批量分析没有迁理由是它还不满足前提)
6. [后端 API 参考](#6-后端-api-参考)
   - 6.1 [学科计划 API](#61-学科计划-api)
   - 6.2 [认证 API](#62-认证-api)
   - 6.3 [管理后台 API](#63-管理后台-api)
   - 6.4 [对话 API](#64-对话-api)
   - 6.5 [小基语音助手 API](#65-小基语音助手-api)
   - 6.6 [智能体中心 API](#66-智能体中心-api)
   - 6.7 [词条本 API](#67-词条本-api)
   - 6.8 [通用响应规范与错误码](#68-通用响应规范与错误码)
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
   - 9.4 [微信 OAuth 接入（已移除）](#94-微信-oauth-接入2026-09-28-已整节移除)
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
    - 14.5 [⚠️ 导出与截图的现代颜色适配](#145--导出与截图的现代颜色适配)
15. [开发与运维](#15-开发与运维)
    - 15.1 [开发工作流](#151-开发工作流)
    - 15.2 [Git 分支策略](#152-git-分支策略)
    - 15.3 [故障排查指南](#153-故障排查指南)
16. [已知问题与解决方案](#16-已知问题与解决方案)
17. [微信小程序端](#17-微信小程序端)
    - 17.1 [端定位与技术栈](#171-端定位与技术栈)
    - 17.2 [导航形态](#172-导航形态与网页端对齐无底部-tabbar)
    - 17.3 [双主题系统](#173-双主题系统浅色--深色)
    - 17.4 [分类色板与页面色调](#174-分类色板与页面色调)
    - 17.5 [包体积与启动优化](#175-包体积与启动优化)
    - 17.6 [隐私接口与合规](#176-隐私接口与合规)
    - 17.7 [与网页端的有意差异](#177-与网页端的有意差异)
    - 17.8 [全量 token 化](#178-全量-token-化已完成)
    - 17.9 [已知未验证项](#179-已知未验证项截至-2026-09-18)
18. [桌面版（Tauri 壳）](#18-桌面版tauri-壳)
    - 18.1 [定位与技术栈](#181-定位与技术栈)
    - 18.2 [双窗口模型](#182-双窗口模型)
    - 18.3 [桌宠](#183-桌宠)
    - 18.4 [配置桥：为什么需要它](#184-配置桥为什么需要它)
    - 18.5 [ACL：Tauri v2 权限的两个坑](#185-acltauri-v2-权限的两个坑)
    - 18.6 [开发配置：tauri.dev.conf.json 是死文件](#186--开发配置tauridevconfjson-是死文件)
    - 18.7 [打包与发布](#187-打包与发布)
    - 18.8 [已知未验证项](#188-已知未验证项)
19. [附录](#19-附录)
    - 19.1 [环境变量完整参考](#191-环境变量完整参考)
    - 19.2 [考纲配置规范](#192-考纲配置规范)
    - 19.3 [题目 JSON Schema](#193-题目-json-schema)
    - 19.4 [术语表](#194-术语表)

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
| **认证系统** | 邮箱密码 + 邮箱验证码 + 小程序微信一键登录（自动建号） | Supabase Auth + 自签 JWT | ✅ 完善 |
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
│                        Uvicorn :8000 (dev) / :80 (prod)                      │
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
│  │  query / random /     │   │   REST API 封装     │   │  DeepSeek V4.1  │   │
│  │  add / delete / save  │   │   统一 headers/错误 │   │   60s timeout   │   │
│  └──────────────────────┘   └────────────────────┘   └─────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
          │                        │                          │
          │ 本地文件 I/O           │ HTTP REST                │ HTTP REST
          ▼                        ▼                          ▼
┌──────────────────┐  ┌──────────────────────┐  ┌────────────────────────────┐
│ backend/data/*.json│  │ Supabase (PostgreSQL) │  │    DeepSeek API            │
│ 17 题库 + 1 配置 │  │  • 用户认证 (Auth)    │  │    api.deepseek.com         │
│ ~21MB JSON 文件  │  │  • 关系数据 (REST)    │  │    model: deepseek-flash    │
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
| **路由** | Vue Router 4.x | History 模式，45+ 路由 |
| **HTTP 客户端** | Axios (前端) / httpx (后端) | 拦截器：401 → 自动登出 |
| **数据库** | Supabase (PostgreSQL 15) | REST API 风格交互，非直连 SQL |
| **认证** | PyJWT 2.x (HS256) + Supabase Auth | 双模融合验证 |
| **3D / 可视化** | Three.js r185 + ECharts 6 | 维度宇宙的 3D 场景；详情面板图表。已开 ACES tone mapping + antialias |
| **AI** | DeepSeek V4.1 Flash (OpenAI SDK) | `deepseek-flash`, 8K tokens，思考模式默认关；文本与识图同一模型 |
| **代码沙箱** | `subprocess.run()` + MinGW GCC/G++ + **仓库内置 OpenJDK 17** | 本地编译执行；Java 走 `backend/utils/jdk/`，不依赖系统安装 |
| **二维码** | ~~qrcode 7.x + Pillow~~ **2026-09-28 起不再需要** | 原用于微信扫码登录（该功能已移除） |
| **邮箱** | SMTP (QQ 邮箱) | 验证码发送 |
| **语音** | 千问 TTS + 科大讯飞 ASR | 08-25 起 TTS 收编千问，讯飞只留 ASR |

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
BACKEND_EXTERNAL_URL=http://192.168.1.100:80    # 后端外网地址（原用于微信 OAuth 回调；该功能已移除）

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

步骤 6: backend/sql/exam_paper_records.sql
        └── 真题答卷记录表（交卷成绩 + 逐题结果 + AI 错因分析缓存）

步骤 7: backend/sql/migrate_plan_columns.sql
        └── subject_plans 补 syllabus_id 列 + plan_daily_tasks 补列

步骤 8: backend/sql/migrate_daily_learning.sql
        └── 计划三阶段 phase/讲解缓存 learning_content/难度/每日时长列

步骤 9: backend/sql/xiaoji_rls_policies.sql
        └── xiaoji_messages / xiaoji_config 表 RLS 放行策略（小基上下文记忆必需）
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

# 需要后端监听 80 端口时（原微信扫码登录用；该功能 2026-09-28 已移除）改用：
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
│   ├── routers/                      # 路由层 (16 个模块)
│   │   ├── subject_plan.py           # ★ 核心路由 (1245行, 19 端点)
│   │   ├── auth.py                   # 认证路由 (976行, 18 端点)
│   │   ├── admin.py                  # 管理后台路由 (1110行, 22 端点)
│   │   ├── career.py                 # 生涯规划模块
│   │   ├── chat.py                   # AI 对话 (按 intent 路由 / 流式)
│   │   ├── community/                # 社区模块 (子路由)
│   │   ├── evaluation.py             # 评估模块
│   │   ├── exam_papers.py            # 真题套卷路由 (列表/双模式/交卷/答卷生成计划)
│   │   ├── feedback.py               # 用户反馈
│   │   ├── learning_plan.py          # 学习计划 (旧版, 已基本被 subject_plan 取代)
│   │   ├── profile_card.py           # 个人画像 (维度宇宙星图)
│   │   ├── qa.py                     # 帮助中心 Q&A
│   │   ├── questions.py              # 题目管理 (旧版, Supabase 题目)
│   │   ├── tools.py                  # 工具集
│   │   ├── video.py                  # 视频模块
│   │   └── xiaoji.py                # 小基 AI 语音助手
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
│   │   ├── algorithm_ds_questions.json
│   │   └── exam_papers/              # 12 套真题卷 JSON（卷面分区+评分标准+解析）
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
│   │   ├── grant_permissions.sql     # Supabase 权限
│   │   ├── exam_paper_records.sql    # 真题答卷记录表
│   │   ├── migrate_plan_columns.sql  # subject_plans/daily_tasks 补列
│   │   ├── migrate_daily_learning.sql# 阶段/讲解缓存/难度/时长列
│   │   └── xiaoji_rls_policies.sql   # 小基消息/配置表 RLS 放行策略
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
        │   └── index.js              # ★ 路由注册 (45+ 路由 + 守卫)
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
        │   └── xiaoji.js             # 小基 API
        │
        ├── utils/                    # 前端工具
        │   ├── request.js            # ★ Axios 实例 (401 拦截 → 登出)
        │   ├── questionLabels.js     # ★ 题型标签 (11 种类型 + 分类映射)
        │   ├── constants.js          # 常量 (后端地址/题型/段位；BG_MAP 已随背景图体系移除)
        │   ├── storage.js            # localStorage 封装
        │   ├── procedural.js         # 程序化生成基础件：3D 值噪声 / fBm / 脊状噪声 / 色彩转换 / 画布
        │   ├── planetTexture.js      # 九颗行星的程序化地表（6 生成器 × 9 配方）+ 云层 + 光环
        │   ├── blackHole.js          # 中央黑洞（事件视界 + 光子环 + 吸积盘）+ 星尘粒子系统
        │   ├── appearanceCode.js     # 外观码：主题配置的编解码与分享
        │   ├── pageMeta.js           # 页面元信息（标题/图标/分类）
        │   ├── mockAgents.js         # 智能体中心的演示数据
        │   ├── videoLib.js           # 视频库数据访问
        │   ├── videoRender.js        # 视频渲染管线
        │   └── videoExport.js        # 视频导出
        │
        ├── views/                    # 页面组件
        │   ├── SyllabusHub.vue       # ★ 考纲列表 (搜索/筛选/收藏)
        │   ├── SyllabusDetail.vue    # ★ 考纲详情 (5 Tab 总控台, 55K)
        │   ├── SubjectPractice.vue   # ★ 做题页 (编程 OJ 分栏, 43K)
        │   ├── ExamPaper.vue         # 真题套卷 (做题/解析双模式 + 交卷出分)
        │   ├── Settings.vue          # 统一设置中心 (8 大模块)
        │   ├── XiaojiSearch.vue      # 小基搜索页 (实时模糊+历史+定位高亮)
        │   ├── Login.vue             # 登录页 (三栏 Tab；扫码面板已移除, 21K)
        │   ├── Landing.vue           # 落地页
        │   ├── Home.vue              # 首页
        │   ├── Profile.vue           # 个人中心 (信息展示页: 账号/学习画像/跳设置)
                │   ├── ProfileCard.vue       # 个人画像「维度宇宙」：程序化星球 + 中央黑洞 + 详情面板
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
            ├── XiaojiCall.vue        # 小基 AI 语音通话
            ├── XiaojiSettings.vue    # 小基设置
            ├── LoadingSpinner.vue    # 加载动画
            ├── GenerateForm.vue      # 题目生成表单
            ├── GenerationHistory.vue # 生成历史
            ├── MistakeBook.vue       # 错题本组件
            ├── QuestionSets.vue      # 题目集管理
            ├── BubbleBackground.vue  # 气泡背景
            ├── WaterBackground.vue   # 水纹背景
            └── community/            # 社区组件 (8 个)
```

### 4.2 后端模块职责

| 模块 | 职责 | 行数 |
|------|------|------|
| `local_question_bank.py` | 启动时加载 17 JSON → dict 内存；提供 query/random/get_by_ids/add/delete/save；支持跨考纲搜索 | 322 |
| `subject_plan.py` | 核心业务路由：考纲/题库/诊断/计划/每日任务/做题/掌握度/错题/代码判题 | 1,245 |
| `auth.py` | 邮箱验证码注册/登录 + 小程序微信一键登录（自动建号）+ 补邮箱密码 + 个人资料 CRUD | 976 |
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
| `Login.vue` | 三栏 Tab（用户/管理员/注册）。**微信扫码面板 2026-09-28 已移除** | 529 |
| `QAPage.vue` | 7 分类 29 FAQ；搜索过滤；跳转按钮 | 921 |
| `request.js` | Axios 实例：baseURL + 60s timeout + Bearer token 注入 + 401 → 自动登出 | 46 |
| `questionLabels.js` | 11 种题型中文标签；从 syllabus.dimensions 动态构建 category→name 映射；题型判断工具 | 122 |
| `auth.js` (store) | 登录/注册/账号状态/补邮箱密码/偏好更新/首次引导判断 | 222 |
| `ExamPaper.vue` | 真题套卷：做题模式（计时+分区导航+交卷出分）/ 解析模式（历史答案+正确率+AI 错因分析） | 🆕 |
| `Settings.vue` | 统一设置中心：8 模块（个人信息/学习偏好/外观/隐私/通知/账号安全/AI 与 API/关于） | 969 |
| `XiaojiSearch.vue` | 小基搜索页：防抖 350ms 实时模糊搜索 + 抖音风搜索历史 + 跳回定位高亮 | 🆕 |
| `Profile.vue` | 个人中心（信息展示页）：账号信息只读 + 学习画像 + 退出登录 + 跳设置 | 重写 |
| `procedural.js` | 程序化生成基础件：3D 值噪声 / fBm / 脊状噪声 / HSL 色彩转换 / ImageData 画布。行星与黑洞共用一份 | 🆕 |
| `planetTexture.js` | 九颗行星的程序化地表（terran/gas/ice/rock/lava/ocean 六生成器 × 9 配方）+ 云层贴图 + 光环贴图。球面方向采 3D 噪声，无接缝无极点挤压 | 🆕 |
| `blackHole.js` | 中央黑洞三部件（事件视界 / 光子环 billboard / 吸积盘）+ `createStardust()` 星尘粒子系统 | 🆕 |
| `ProfileCard.vue` | 维度宇宙主页面：3D 黑洞星系 + 九维详情面板（ECharts）+ 进出场转场 | 重写 |

---

## 5. 核心业务模块

### 5.1 学科计划系统

> 考纲驱动的备考主线：选考纲 → 摸底诊断 → 生成三阶段计划 → 每日任务 → 真题冲刺。
> 数据落 `subject_plans` / `plan_daily_tasks` / `question_records` / `user_kp_mastery`。

#### 5.1.1 业务流程全景

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

  "exam_papers": [                        // 真题套卷 (12 套真题，见 5.1.7)
    { "name": "2024年6月真题", "file": "cet4_2024_06.json", "available_score": 568 }
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

### 5.1.7 真题套卷系统（ExamPaper）

**数据**：`backend/data/exam_papers/` 12 套真题 JSON（卷面分区 sections + 评分标准 grading_rubric + 中文解析 + ai_analysis_hint）。CET-4/6 跳过听力（缺音频）、二级 Office 仅选择题、二级 Python/C 与行测为精选卷；雅思/托福因版权保护未收录（规划 AI 仿真卷另标）。

**双模式**（`/subject-plan/:syllabusId/exam/:paperId`）：
- **做题模式**：计时器 + 分区导航 + 交卷弹窗（总分 + 分区得分）
- **解析模式**：做过 → 你的答案/正确率/解析/AI 批改反馈/AI 错因分析；没做过 → 标准答案 + 提示"先做题才能获得 AI 个性化批改"

**交卷链路**：客观题自动判 + 主观题 AI 批改（按 grading_rubric）→ 错题后台异步批量 AI 分析（每批 5 题，输出错因/正确思路/学习建议）→ 缓存到 `exam_paper_records.question_results`，解析模式秒开不重复烧 AI。

**备考计划双通道**（考纲详情「生成备考计划」弹窗）：
```
通道一：摸底生成 — 诊断答题 → AI 评估 → 生成计划
通道二：答卷生成 — 已完成真题卷 → AI 分析错题 → 生成计划（未完成卷灰色禁用）
```
答卷通道 AI 只能从考纲真实维度/题型列表选题 → 任务带 category+question_type+question_count 可被 bank_query 查到真实题目；三阶段设计（基础期易/强化期中/冲刺期综合）+ fallback 兜底。

**每日学习闭环**：每日任务卡片 → 📖 学习讲解（AI 按本日题目实时生成，首次后缓存 learning_content）/ ✏️ 去练习（带真实题目）/ 🎬 知识点讲解视频（自营视频库，2026-09-04 上线，见 5.16）。阶段标签：基础绿/强化橙/冲刺红。

**API**（`backend/routers/exam_papers.py`）：`GET /syllabi/{id}/exam-papers`、`GET /exam-papers/{paper_id}?mode=`、`POST /exam-papers/{paper_id}/submit`、`POST /exam-papers/{paper_id}/generate-plan`。

### 5.2 AI 对话系统


基智内置两套 AI 对话系统，分别覆盖生产力场景和陪伴场景。

#### 5.2.1 主对话系统（ChatArea）—— 多智能体学习助手

位于首页 `/home`。用户发送消息后，系统自动进行**意图识别**，将请求路由到对应的专业 Agent。

**意图识别（关键词单轨）**：

```
前端关键词匹配 → 匹配"规划/计划/安排"→plan
               → 匹配"生成/出题/题目"→generate
               → 匹配"评估/评价/批改"→evaluate
               → 默认 → chat
```

> 原「双轨策略」的优先级 1（`POST /chat/detect-intent` AI 分类）已于 2026-09-11 **连同端点整体删除**（全站零引用）。现在只剩关键词这一条路径，没有再往模型层兜底。

**四 Agent 路由**：

| 意图 | Agent | 图标 | 调用的后端函数 | 功能 |
|------|-------|------|---------------|------|
| `plan` | 规划 Agent | 📋 | `plan_with_history_stream()` | 根据用户画像+历史生成 N 天备考计划 |
| `generate` | 生成 Agent | 📖 | `generate_with_history_stream()` | AI 出题，按知识点/难度生成题目 |
| `evaluate` | 评估 Agent | 🔍 | `evaluate_with_history_stream()` | 批改主观题，给出评分+反馈 |
| `chat` | 对话 Agent | 💬 | `call_llm_stream()` + 个性化 system prompt | 通用问答，注入用户学习阶段/强弱知识点 |

**流式响应流水线**：

```
1. 用户输入 → 前端关键词匹配 → 确定 intent
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
| `/chat/send` | POST | 流式对话主端点，按意图路由到对应 Agent |
| `/chat/title` | POST | 从首轮对话生成标题（≤20 字） |
| `/chat/summary` | POST | 从 AI 回复提取摘要标签（≤15 字） |
| `/chat/log` | POST | 保存摘要到 Supabase learning_logs |
| `/chat/vision` | POST | 多模态图片理解（DeepSeek V4.1 Flash 原生多模态，09-10 切换，流式 SSE 解析） |
| `/chat/advice` | POST | 从 prompt 生成学习建议（非流式） |

#### 5.2.2 小基语音助手（XiaojiCall）—— 人格化 AI 伴侣

位于 `/xiaoji/call`，独立的全屏沉浸式体验。小基拥有角色形象、语音输出、丰富交互反馈。

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
| 图片理解 | `POST /community/xiaoji/vision` | 千问 qwen3-vl-flash（08-25 收编阿里云） |
| 语音合成 | 浏览器 `SpeechSynthesis` API | 中文 (zh-CN)，可开关 |
| 语音输入 | 浏览器 `SpeechRecognition` API | 中文识别 → 自动发送 |
| 题目评估 | `POST /community/xiaoji/evaluate-question` | 4 步 Agent 流水线 |
| 题集评估 | `POST /community/xiaoji/evaluate-set` | 综合评估含难度匹配/薄弱分析/学习建议 |
| 上下文记忆 | `xiaoji_messages` 表 | 每轮对话存库，回复前拼入最近 10 条上下文 |
| 历史搜索 | `GET /community/xiaoji/messages?search=` | 独立搜索页，ilike 模糊匹配 |

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

**聊天记录**（2026-08-17 新增）：
- 进入页面自动定位到最新消息（先渲染再滚动，瞬时跳转避免平滑滚动动画）
- 跨天消息插入日期分隔线（今天 / 昨天 / M月D日 周几 / 跨年带年份），每条消息右侧显示 HH:MM
- 清空记录按钮 → `DELETE /xiaoji/messages/{user_id}`

**搜索页（`/xiaoji/search`，2026-08-17 新增）**：
- 顶部 🔍 按钮进入独立搜索页，输入框自动聚焦
- 防抖 350ms 实时模糊搜索，结果 = 头像 + 我/小基标签 + 时间 + 内容摘要；序号机制丢弃过期结果防竞态
- 输入为空时展示抖音风搜索历史（localStorage 去重最近优先 10 条，可清空；回车/点标签/点结果才写入历史）
- 点击结果 → `/xiaoji/call?highlight={msg_id}` → 聊天页滚动定位居中 + 黄色高亮闪烁 2.4s
- 后端模糊匹配语法为 PostgREST `ilike.*关键词*`（`*` 是通配符；写裸 `%` 会 500）

**记忆链路**：`xiaoji_messages` 表 + `xiaoji_rls_policies.sql` RLS 放行策略（后端统一匿名 key 访问，身份校验在应用层）；未配策略时写入 401、读取空 → 表现为"没有记忆"。

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

**后端文件**：`backend/routers/community/xiaoji.py`（~480 行，含消息搜索），独立于主 Chat 系统；顶层 `routers/xiaoji.py` 为兼容层（清空记录等端点仍被前端使用）。

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

`POST /chat/vision` 支持图片理解，当前实现使用 **DeepSeek V4.1 Flash 原生多模态**（`deepseek-flash`，2026-09-10 由 `deepseek-v4-flash-vision-exp` 实验版切换而来——V4.1 Flash 原生支持图文混合输入，**文本与识图共用同一个模型**，复用 `DEEPSEEK_API_KEY`，图片按 Token 计费单张最多 384 tokens）：

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
| 好友列表 | 小基 AI 置顶（特殊蓝卡 → 点击跳 `/xiaoji/call`）+ 真实好友（头像/昵称/账号/在线绿点 → 聊天/删除） |
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

**小基模式**：与小基对话时切换 API → `POST /community/xiaoji/chat`（火山引擎豆包）→ TTS 朗读回复。

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
  │ 动态广场  │ │ 好友系统  │ │ 私聊     │ │ 小基助手     │
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
| `xiaoji.py` | 小基聊天/视觉/TTS/ASR/题目评估/题集评估/流式评估 | ~13 |
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
 │ 1. 按「题型轴 × 学科轴」拼 prompt                          │
 │    ┌── 题型轴 QTYPE_SPECS（7 种题型各自一份）               │
 │    │     任务说明 + 答案写法 + 输出字段表 + 禁止项           │
 │    │     只有选择题带 options；判断题答案是「正确/错误」、    │
 │    │     计算题是数值或表达式、编程题是完整可跑程序           │
 │    ├── 学科轴 SUBJECT_DISCIPLINE（11 个学科各自的用词/      │
 │    │     例子/禁止项）                                     │
 │    └── 角度池 ANGLES_COMMON / ANGLES_CS（按学科选池）       │
 │                                                          │
 │    ⚠ 2026-09-11 之前是**所有题型共用一套固定模板**（下面这段   │
 │    就是被删掉的旧写法）。后果实测过：判断题和计算题的答案    │
 │    双双变成选项字母 "A"——因为 hardcode 的 options 被硬塞给了 │
 │    根本不该有选项的题型。                                   │
 │      旧:  "options": {{"A": "...", "B": "...", ...}},     │
 │           "answer": "A",        ← 判断题也这么返回         │
 │    现在: 输出字段完全由题型决定，编程题沿用题库已有的标准      │
 │          schema（题库 19,338 题就是它生成的）               │
 │                                                          │
 │ 2. call_llm(prompt, temperature=0.9, schema=该题型 schema) │
 │                                                          │
 │ 3. 按 schema 校验并提取 JSON（不合法则带错误重试）           │
 │                                                          │
 │ 4. 敏感词过滤                                             │
 │    check_content_safety(title + content + answer)         │
 │    → 不通过: HTTP 400 + "生成内容包含敏感信息"              │
 │                                                          │
 │ 4.5 编程题质检闸 ★（只对编程题）                            │
 │    「改提示词」解决不了「模型自己算错数」——实测 17 条用例里   │
 │    只有 13 条跟它自己的参考答案对得上（76%）。               │
 │    所以生成后**真跑一遍参考答案**：                          │
 │      ├─ 全部用例通过      → 放行                           │
 │      ├─ 与参考解不一致    → 带上实跑证据让模型修（≤2 轮）     │
 │      │                     ⚠ 修复调用必须带 schema，否则模型  │
 │      │                       只能自己编格式，每轮都白修       │
 │      └─ 2 轮后仍不过      → HTTP 502 如实报错，**不落库**     │
 │    效果：落库题用例通过率 76% → 100%（15/15）；生成耗时 6s→9s │
 │                                                          │
 │ 5. 写入 Supabase                                         │
 │    POST /rest/v1/questions {                             │
 │      user_id, title, question_type, difficulty_score,    │
 │      category, topic, options, answer, explanation,      │
 │      hint, source: "generated", parent_id: null,         │
 │      starter_code, test_cases    ← 09-11 起补齐（原先整体丢弃）│
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
        # 单题生成按题型 schema 校验，不合法就带错误信息让模型重试，
        # 不做题库批量生成那种多层剥离容错
        raise ValueError("JSON 解析失败")
```

**与批量题库生成的区别**：

| 维度 | 单题生成 (`/questions/generate`) | 批量生成 (`seed_all_banks.py`) |
|------|----------------------------------|-------------------------------|
| 触发方式 | 用户手动，UI 交互 | 脚本执行，命令行触发 |
| 生成量 | 1 题/次 | 按批次 (BATCH_SIZE=6)，可达数千题 |
| Temperature | 0.9（高多样性） | 0.7（平衡质量和多样性） |
| JSON 容错 | 按题型 schema 校验，不合法带错误重试 | 多层容错链（括号计数+回退+剥离+类型过滤） |
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


位于 `/profile-card`，平台最具视觉冲击力的页面——一个**黑洞星系**：正中是黑洞，九颗程序化行星各有轨道，数据源与评估表共用 `GET /evaluation/profile-data`。

> 2026-09-12 星图化重做、2026-09-15 程序化星球 + 中央天体改黑洞。下面描述的是这两轮之后的现状。

#### 5.7.1 3D 场景架构

**深空背景**：远层 18000 颗微星（范围 ±1600，让机位能落在星空内部——从外面看会看到立方体轮廓，从里面看只有满天星、没有边界）+ 填充星 + 近景亮星 + 尘埃带 + 星云光斑。
`sizeAttenuation` 全部关闭，否则远处的星会缩到亚像素等于消失。

**中央黑洞**（`utils/blackHole.js`）：三个部件
- **事件视界**：纯黑球。`MeshBasicMaterial` 不受光照，贴上去就是全黑，把背后星空彻底吃掉
- **光子环 + 透镜弧**：一张朝向镜头的程序化贴图（billboard）。真做引力透镜要单独一整套后处理，而招牌观感——视界边缘一圈细亮环、外加吸积盘远侧的光被弯折到视界上下各成一道弧——一张贴图就能拿到，且镜头转到任何角度都成立
- **吸积盘**：赤道面上的环，缓慢自转（0.0022/帧）。内缘白热、向外幂律冷却，叠角向条纹做湍流

配色跟随用户「外观色」：视界按物理就该是黑的，主题色落在吸积盘与光子环上。中心那盏点光源保留（黑洞不发光，但吸积盘极亮，行星仍该被中心照亮）。

**9 颗行星**（`utils/planetTexture.js`）：**全部地表都是运行时程序化生成的**，不依赖任何图片资源。
- 六个生成器 × 九套配方，按维度主题分配：`terran`（大陆+海洋+极冠）/ `gas`（纬向条纹+大红斑）/ `ice`（冰板块+裂纹）/ `rock`（fBm 地形+16 个陨坑）/ `lava`（冷壳+发光熔岩缝）/ `ocean`（全球皆水+域扭曲洋流）
- 关键做法：**不按 (u,v) 平面采噪声**，而是先把每个纹素换算成它在球面上的真实单位方向，再拿这个方向采 3D 噪声——噪声本身就定义在球面上，等距圆柱投影的**左右接缝与两极挤压**自然都不存在
- 每颗另有独立云层球（转得比地表快，0.016 vs 0.010 → 有视差）+ 径向分带光环，部分指标星带环

**星图坐标系**：同心刻度环 + 12 条辐射线构成极坐标网格，让"几个球在飘"变成"一张星图"。

**侧栏维度清单**：九维各带真实数值与数据状态（标「N / 9 有数据」），点它和点星球是同一条路径。

**右上角坐标面板**：常驻显示当前（悬停或默认第一颗）行星的轨道半径 R / 相位角 θ / 轨道倾角 i / 离面高度 y，实时跳动。

**交互**：OrbitControls（拖动旋转/滚轮缩放）→ Raycaster 悬停检测 → 点击 → 摄像机飞入动画 → 展开详情面板。
**退出宇宙靠点中央黑洞**（2026-09-12 移除了顶栏返回键；底栏有「点中央黑洞退出」提示——黑洞比原来的亮恒星暗得多，不加提示不好找）。
**维度深链** `/profile-card?dim=knowledge` 可直达某个维度，可分享、刷新保持。

**转场**：
- **进场**：从虚空推进（起点距离 1100，落在星空内部），**对数插值**——线性插值时视张角按 1/d 变化，前 80% 时间几乎没动静、最后 15% 猛扑进来，观感就成了硬切而不是靠近
- **出场**：九颗行星依次螺旋坠入黑洞（内圈先落，角速度随半径暴涨）→ 星尘从远处旋转着涌来 → 直接切主页。全程在 3D 里完成，**不盖 DOM 遮罩**
  - 两个关键项：角速度必须随半径暴涨（少了它行星只是沿半径笔直滑向中心，像掉下去而不是被卷进去）；缩放跟着**半径**而不是时间走（行星半径与视界相当，不在贴近时收掉的话是行星盖住黑洞，而不是黑洞吃掉行星）

#### 5.7.2 九维详情

| 行星 | 名称 | 图表类型 | 数据来源 | 颜色 | 轨道半径 | 速度 |
|------|------|---------|---------|------|---------|------|
| 1 | 知识星系 | **极坐标星爆图** | `knowledge_base.list` → 每个知识点一根射线，**长度与颜色表掌握度**，取最高 18 个 | #409eff | 2.8 | 0.15 |
| 2 | 能力雷达 | ECharts 雷达图（**轴数 < 3 时自动降级为横向渐变条**） | `ability_radar` — 5 项能力指标（概念理解/计算能力/逻辑推理/记忆能力/应用实践） | #8b5cf6 | 3.6 | 0.12 |
| 3 | 学习节奏 | ECharts 日历热力图 | `learning_rhythm.calendar[]` — 90 天活跃度 + 连续天数/最长连续/总活跃天数 | #10b981 | 4.4 | 0.10 |
| 4 | 认知偏好 | ECharts 横向柱状图 | `cognitive_preference.types` — 各题型分布 | #f59e0b | 5.2 | 0.09 |
| 5 | 易错地图 | ECharts 矩形树图 | `mistake_map.list[]` — **色相表攻克率、明度表错题量**（只按攻克率上色的话，攻克率低的账号会糊成一堵一模一样的红墙） | #ef4444 | 6.0 | 0.08 |
| 6 | 成长轨迹 | ECharts 折线图（发光折线 + 渐变面积 + 均值参考线） | `growth_trajectory.points[]` — 掌握度从首次到最近 | #06b6d4 | 6.8 | 0.07 |
| 7 | 学习人格 | CSS 动画卡片 | `personality` — 类型(梯度微光字体) + 标签 + 描述文案 + 浮动 emoji | #ec4899 | 7.6 | 0.06 |
| 8 | 兴趣星云 | Three.js CSS3DRenderer 球面 | `interest_field.list[]` — 黄金角分布标签球 | #f97316 | 8.4 | 0.05 |
| 9 | AI 洞见 | 洞察卡 | `ai_summary` + `ai_actions` — **一条非显而易见的洞察 + 2~3 条可执行行动**（每条锚定真实知识点或数字）。LLM 挂了用规则从真实数据兜底 | #a78bfa | 9.2 | 0.04 |

**统一视觉语言**：每个维度一张 `dim-card` 容器（渐变面 + 描边 + 内高光 + 投影，图表不再裸浮在面板上）+ 一行**真实数据的 KPI 摘要**（绿=好、琥珀=弱）；所有图表共用 `TIP` / `AXIS_LABEL` / `SPLIT_LINE` 三个常量，并统一带 tooltip——没有 tooltip 时知识/能力/认知/成长四个图根本读不出数值。

#### 5.7.3 后端数据聚合（evaluation.py）

`GET /evaluation/profile-data` 聚合以下 Supabase 表：

| 数据域 | 来源表 | 聚合方式 |
|--------|--------|---------|
| knowledge_base | `questions` | 按 `normalized_topic` 分组取 avg(mastery_score)，**只统计已作答的题** |
| ability_radar | `questions` | **关键词优先 + 题型兜底**（`TYPE_TO_ABILITY`）映射到 5 个能力类目 |
| learning_rhythm | **`user_actions`** | 近 90 天日历 + current/max streak + 活跃时段分布 |
| cognitive_preference | `generation_history` | 题型分布统计 → 标签（视觉型/文字型/综合型） |
| mistake_map | `questions` | `is_mistake` 按 topic 计数 + 攻克率 |
| growth_trajectory | `questions` | 按日期聚合 mastery_score，取最近 30 个点 |
| personality | 综合推导 | 学习阶段 + 风格 + 强弱项 → 类型标签 + 描述 |
| interest_field | `generation_history` | topic 频率排名 TOP12 |
| ai_summary / ai_actions | LLM 生成 | 一条洞察 + 2~3 条可执行行动；失败时用规则从真实数据兜底 |

**两个容易踩的坑（2026-09-11 修）**：

1. **`mastery_score = 0` 不是真分数**。生成题默认值就是 0，用户 200 道生成题里 161 道从没作答过；把它们一起算平均会把知识星系的平均掌握度拉到 ~0。过滤条件是 `mastery_score > 0 **或** is_mistake=True`——后半句兜住「答了但全错」的题。实测过滤后平均掌握度 **0 → 87**。
2. **能力维度不能只靠知识点关键词硬匹配**。「集合」「微积分」「三角函数」这类真实知识点一个关键词都命中不了，维度会整片落空。改成关键词优先 + 题型兜底，保证每道练过的题都计入某个维度。

> **前端契约**：2026-09-11 前前后端字段名对不上——前端读 `cognitive_preference` / `mistake_map` / `growth_trajectory`，后端给的是 `cognitive_style` / `mistake_pattern`，第三个压根没算过，导致三块整块不显示。现在后端**两套名字都返回**（老名字给其它消费方，末尾「前端契约」块给 `ProfileCard.vue`）。改字段名时两边都要看。

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


侧边栏"工具"区图标点击 → 侧边栏内滑出工具面板（面板逻辑内置于 `Sidebar.vue`；原独立组件 `Workbench.vue` 已于 2026-08-17 死代码清理时删除）。所有工具数据存储在 Supabase 独立表中，每个用户一行，核心数据以 JSONB 列存储。API 前缀 `/tools`（`backend/routers/tools.py`, 339 行）。

#### 5.9.0 整体架构

```
工具箱数据架构
═══════════════════════════════════════════════════════

  前端 Sidebar.vue 工具面板              后端 tools.py          Supabase
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

**前端展示逻辑**（`Sidebar.vue` 工具面板）：
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


### 5.10 API 模型中心（预览形式）


位于 `/api-center`，以**模型画廊 + 示例预览**的形式展示平台 AI 能力背后的各模型。当前所有 AI 调用统一走后端 `.env` 中的平台官方 Key，页面上的自配 Key 仅为演示预留；**后期规划切换为「用户自带 Key 优先、平台 Key 兜底」**。

#### 5.10.1 页面结构与预览形式

**页面结构**：返回按钮 → 页头 → 概览条（已接入平台 x/6 · 文本主力 · 视觉模型 · 语音/视频）→ 模型画廊（6 张卡片）→ 底部提示（语音输入走浏览器内置能力 + Q&A 指南链接）。

**卡片结构**：徽章 + 名称 + 状态标（官方已接入 / 可自配 Key）+ 模型 ID + 能力标签 + 简介 + 预览区；点击卡片展开详情（官方模型显示接入说明，可自配模型显示 Key 表单）。

**预览形式（2026-08-23 改版，替代原纯文字块预览）**：

| 类型 | 卡片 | 表现 |
|------|------|------|
| 对话气泡 | DeepSeek V4.1 Flash / 智谱 GLM | 「我」提问气泡 + 小基头像回答气泡（`xiaoji_idle.png`）；展开卡片时打字机逐字重播，打字中头像切换 `xiaoji_speaking.png` + 闪烁光标 |
| 识图 | DeepSeek V4.1 Flash（原生多模态） | 左侧「示例题目截图」纸质 mockup（斜置仿拍照）+ 右侧小基解析气泡 |
| 语音 | 讯飞星火 | 播放按钮 → `POST /xiaoji/tts` 真实讯飞合成，base64 mp3 本地播放（取回后缓存复用）；播放中均衡器动画 + 实际时长 |
| 状态 | 豆包 | 主链路 / 待命备用状态行 |
| 视频 | 腾讯云数字人 | 16:9 占位帧（渐变 + 播放按钮），点击提示占位中 |

#### 5.10.2 模型清单

| 卡片 | 厂商 | 模型 / 接口 | 接入方式 | 预览形式 | 用途 |
|------|------|------------|---------|---------|------|
| DeepSeek V4.1 Flash | DeepSeek | deepseek-flash（文本·思考默认关） | ✅ 官方 | 对话气泡+打字动画 | 全站文本主力：对话/规划/出题/批改/小基 |
| DeepSeek 识图 | DeepSeek | deepseek-flash（原生多模态，与文本同模型） | ✅ 官方 | 截图 mockup+解析气泡 | 图片理解/拍题识别/小基识图 |
| 豆包（火山方舟） | 火山引擎 | Ark endpoint 接入 | ✅ 官方 | 状态行 | 对话备用通道 |
| 讯飞星火 | 科大讯飞 | ASR / TTS 接口 | ✅ 官方 | 可播放真实合成语音 | 小基语音对话 |
| 腾讯云数字人 | 腾讯云 | 数字人视频生成 | ⬜ 可自配 Key | 视频占位帧 | 每日任务视频推送（占位中） |
| 智谱 GLM | 智谱 AI | GLM 系列 | ⬜ 可自配 Key | 对话气泡+打字动画 | 出题备用通道 |

#### 5.10.3 自配 Key（演示）

腾讯云数字人、智谱 GLM 两张卡展开后可填写自己的凭证（SecretId/SecretKey、API Key），保存到浏览器 `localStorage`（key: `apicenter-keys`）。**目前仅作演示**：实际 AI 调用仍走后端 `.env` 官方 Key，页面注明「留作备用通道」；后期接入后端存储后，此表单直接对接用户 Key 保存接口。

#### 5.10.4 后期规划：用户自带 Key

**定位**：当前全部 AI 调用使用平台官方 Key。后期允许用户在模型卡上配置自己的 Key——**用户个人 Key 优先、平台 Key 兜底**（未配置或调用失败时自动回落平台 Key）。


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

**凭证安全模型**：

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

**规划中的数据库设计（user_api_keys）**：

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

**规划中的后端 API 端点**：

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

#### 5.10.7 实现状态与规划

| 项 | 现状 | 后期 |
|------|------|------|
| AI 调用 | 全部走平台 `.env` 官方 Key | 用户配置后走个人 Key，未配置/失败自动回落平台 Key |
| 页面形式 | 模型画廊 + 示例预览（2026-08-23 改版） | 保持预览形式，自配卡接入真实保存/验证 |
| 凭证存储 | localStorage（仅演示） | Supabase `user_api_keys` + RLS + 掩码回显 |
| 语音预览 | 真实讯飞合成（缓存复用） | 沿用 |
| 视频推送 | 占位中 | 腾讯云数字人上线后启用 |

---
### 5.11 账号体系与登录


> **⚠️ 2026-09-28 账号模型重构 —— 本节前半部分是历史，已废弃。**
> 旧的「网页扫码登录 + 登录后绑定微信」整条链路**已删除**，原因见下。

#### 5.11.0 为什么去掉「扫码登录 + 账号绑定」（2026-09-28）

用户的原话是「个人开发，不是企业，不能直接绑微信」。查下来**对一半**：

| 能力 | 个人主体能不能做 |
|---|---|
| 小程序 `wx.login` 一键登录 | ✅ **能做**，不需要企业资质 |
| 网页 / APP 的微信登录（开放平台） | ❌ 要企业主体 + 300 元/年认证 |
| 公众号网页授权 | ❌ 个人订阅号没有这个接口权限 |
| UnionID 打通小程序 ↔ 网页 | ❌ 必须企业 |

**受限的只有网页/APP 那条**，而网页端当时是用**公众号测试号**兜的 ——
那是开发调试工具，不该上生产（`auth.py` 的注释里自己写着「请前往
mp.weixin.qq.com/debug 获取测试号」）。

于是定下：

- **小程序两条登录路径**：① 微信一键登录（**首次由后端直接建号**）② 邮箱/用户名 + 密码
- **不再做「绑定」**：原来的「微信登录 → need_bind → 绑定网页账号或注册」整条删掉
- **公众号测试号扫码整条删除**（后端删 4 个端点，路由 **22 → 18**）
- **扫码登录推迟到 Flutter App 出来之后**（用户明确：扫码那一端只做手机应用）

#### 5.11.1 小程序登录（当前实现）

| 端点 | 行为 |
|---|---|
| `POST /auth/wx-login` | 用 code 换 openid；**查不到就当场建号**（原来是返回 `need_bind`）。Admin API 建 auth 用户 + 写 profile |
| `POST /auth/set-credentials` | 补真实邮箱 + 密码，复用邮箱验证码。**只对占位邮箱账号开放** |
| `GET /auth/account-status` | 让客户端知道该显示「修改密码」还是「设置邮箱和密码」 |

**建号那条路做了三层防护**（这个项目在「静默失败」上吃的亏太多了）：

1. profile 写失败 → **回滚删掉刚建的 auth 用户**（不回滚的话，每次重试漏一个孤儿账号）
2. **回读校验 openid 真的落库** —— 它是这个账号唯一的找回凭据，
   INSERT 失败会报错但值被改写不会，**只有回读能发现**
3. 缺 `SUPABASE_SERVICE_ROLE_KEY` 直接 500，**不静默降级**

#### 5.11.2 ⚠️ 这里有个洞，以及不用「账号合并」的补法

微信建的号**没有邮箱密码** → 用户在网页/桌面/手机端**够不着它**，会导致学习数据分裂。

补法**不是**账号合并（那要迁移 `user_id`，是数据工程），而是**给账号补一把钥匙**：
微信建号后，在设置页可以补真实邮箱 + 密码。补完同一个账号到处都能登。

数据模型因此定为：**占位邮箱 `wx_{openid}@miniapp.local`**
（`.local` 是 RFC 6762 保留 TLD，永远不可投递）。

**设置页的「账号安全」按账号状态二选一** —— 这不是设计偏好，是**必须的**：
原来的「修改密码」表单第一步要输**当前密码**，而微信建号的用户根本不知道那个随机密码，
照原样加个入口就是把用户送进一个必然失败的表单。

#### 5.11.2b 向后兼容（当时特意确认过）

老版本小程序（已提审那个包）拿到 `need_bind: false` + `access_token` 会**直接登录成功**。
所以**不会出现「用户更新前完全登不进去」**。

#### 5.11.2c 已删除的端点（历史，勿再引用）

`GET /auth/wechat/qrcode`、`GET /auth/wechat/bind-qrcode`、`GET /auth/wechat/callback`、
`GET /auth/wechat/poll/{token}` —— 以及只服务于它们的 `_cleanup_expired` /
`_find_wechat_user` / `_bind_wechat_to_user`。网页端同步删掉 `Login.vue` 的扫码段、
`Settings.vue` 的「绑定微信」段、`api/auth.js` 与 `stores/auth.js` 里对应的 7 个函数。

> ⚠️ `/auth/wx-bind` 端点**还留着**（客户端已无调用）—— 删不删尚未决定。

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

#### 5.11.6 登录态管理与并发控制（当前实现）

| 场景 | 处理方式 |
|------|---------|
| 小程序重复点登录 | 前端按钮 loading；后端按 openid 唯一 —— 已存在直接返回该账号 JWT，**不会重复建号** |
| 建号中途失败 | profile 写失败 → **回滚删掉刚建的 auth 用户**（不回滚的话每次重试漏一个孤儿账号） |
| openid 被静默改写 | **回读校验** —— INSERT 失败会报错，但值被改写不会，**只有回读能发现** |
| 缺 `SUPABASE_SERVICE_ROLE_KEY` | 直接 500，**不静默降级**（否则拼出 `Bearer None`，比报错更难查） |
| 补邮箱密码中途失败 | **验证码不能被消耗**（已有测试守住这条重试安全性） |
| 同一账号多端同时登录 | 无冲突：JWT 无状态，各端各自持有 |

#### 5.11.7 错误处理矩阵（当前实现）

| 环节 | 错误 | 前端行为 | 恢复方式 |
|---|---|---|---|
| 小程序 `wx.login` | code 换 openid 失败 | Toast「微信登录失败」 | 重试 |
| 建号（首次登录） | profile 写失败 | 后端已回滚并返回 500 | 重试（**不会留下孤儿账号**） |
| 建号 | 缺 service key | 后端 500 + 日志 | **运维问题**，用户重试无用 |
| 补邮箱密码 | 邮箱已被占用 | Toast 明确提示 | 换一个邮箱 |
| 补邮箱密码 | 验证码错误 / 过期 | Toast | 重新发码 |
| 补邮箱密码 | 中途失败 | **验证码不消耗** | 直接重试 |
| 补邮箱密码 | 对非占位邮箱账号调用 | 后端拒绝 | 该账号应走「修改密码」而非「设置邮箱和密码」 |

> **已删除的轮询有限状态机**：原 `Login.vue` 里还有一套 2 秒轮询 / 5 分钟超时 /
> `{ready, bound, access_token}` 分支的 FSM，**随扫码登录一起删掉了**，本节不再保留。

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


### 5.13 统一设置中心（Settings）

位于 `/settings`（2026-08-06 新增，2026-08-17 配合个人中心去重完善，2026-09-28 整合小基设置与快捷键）。将原本散落在 6 处的设置项统一收拢：侧边栏（主题/状态）、个人中心（昵称/密码）、引导页（学习偏好）、**小基设置**（2026-09-28 内嵌进来，原 `/xiaoji/settings` 改为重定向）、**快捷键**（2026-09-28 新增）、通知设置（原只有后端 API 无前端 UI）。

**全站只有这一处设置**：首页右上角的齿轮也指向 `/settings` —— 原来它指向 `/xiaoji/settings`，和左侧轮盘里的「设置」是两个页面，同一个东西两处维护。

#### 5.13.1 十大模块

| 模块 | 内容 | 数据来源 |
|------|------|---------|
| 个人信息 | 昵称 / 简介 / 头像上传 | `PUT /auth/update-nickname`、`/update-bio`、`POST /auth/upload-avatar/{id}` |
| 学习偏好 | 7 项下拉（阶段/年级/专业/目标/难度/讲解方式/每日时长） | `PUT /auth/update-learning-info` |
| 外观 | 主题定制四轴（2026-09-03 后无浅/深/跟随系统开关，明暗由**背景色亮度自动派生**）：**背景色 / 组件色(毛玻璃) / 主题色 / 字体色**（各带预设 + 高级 rgb 选色）；**预设一套**方案一键换四轴；**默认方案 = 深空蓝四轴**（新用户首次进入 + 恢复默认）；**实时预览小界面 + 适配度提醒**（5 组 WCAG 对比度加权百分比 + 逐项建议 + 自动调整字体色）；组件色经 `var(--surface)` 收编全站 500+ 白描层；**仅落地页跟随系统明暗、不可改**；**外观码**（2026-09-04）：四轴打包成可分享码（`JZ1-bg-surface-brand-字体档-校验`，官方套装为 `JZ1-space` 超短别名，校验防抄错）+/theme?code= 免登录直达预览一键应用 | themeStore（localStorage 缓存，`GET/PUT /auth/theme` 账号同步） |
| 隐私 | 在线 / 隐身 | `PUT /auth/status` |
| 通知设置 | 8 开关 + 每日推荐/总结时间 | `GET/PUT /community/notification-settings` |
| 账号安全 | 修改密码。**微信绑定已删（2026-09-28）** —— 公众号测试号扫码整条移除，改由「微信建号 + 补邮箱密码」承担（见 5.11.2） | `PUT /auth/update-password`、`POST /auth/set-credentials` |
| 快捷键 | 25 个动作可改键；录制态 + 冲突提示；**跟随账号**（`user_shortcuts` 表） | `GET /auth/shortcuts/{user_id}`、`PUT /auth/shortcuts`（见 5.17） |
| 桌宠 | 显示开关 / 轮盘项开关 / 小基大小（滑杆）/ 开机自启。**仅桌面壳里出现**（网页版整块隐藏） | 壳的 `set_pet_visible` / `set_pet_prefs`、`plugin:autostart`（见 18.3） |
| AI 与 API | 跳转小基设置 + API 管理中心（链接卡） | `/xiaoji/settings`、`/api-center` |
| 关于 | 当前版本（读 `package.json` 的 version 字段；桌面壳里另有壳自己的版本号，问壳要）+ ICP 备案号（2026-09-02 新增，链工信部备案查询）+ 使用指引/帮助中心/开源文档入口（2026-08-24 新增） | 前端本地 + 壳的 `app_version` |

#### 5.13.2 个人中心去重（Profile 信息展示页）

2026-08-17 重构：`Profile.vue` 重写为信息展示页 —— 头像 + 昵称/账号/邮箱只读展示、学习画像展示卡（含「重新填写偏好问卷」入口）、退出登录、「编辑资料与设置」按钮跳 `/settings`。所有编辑操作（头像/昵称/简介/密码/微信绑定）只保留设置中心一个入口，避免双入口维护与状态不一致。

### 5.14 智能体中心

位于 `/agent-center`（2026-08-22 硬编码预览版，2026-08-23 后端全量落地）。5 个核心智能体（对话 / 规划 / 生成 / 评估 / 小基）散落在 ~20 个触点，本模块把这些触点的行为数据聚合为「使用情况 + 效果指标」，并提供参数调节与**自动磨合**——不做模型微调，做参数自适应：行为数据（正确率/完成率/👍👎）→ 规则引擎自动微调 agent 参数 → 下次调用实时拼装生效。

数据原则：**每个数字要么解释学习效果、要么导向动作**；统计只是调整效果的证据。

#### 5.14.1 数据设计与触点清单

**原则：能用现有表就不建新表**。调用计数统一走 `user_actions`（action_type + metadata.touchpoint），效果指标统一走业务表（`plan_daily_tasks` / `question_records` / `exam_paper_records` / `generation_history` / `questions` / `question_sets` / `learning_logs` / `xiaoji_messages` / `user_kp_mastery` / `diagnosis_results` / `subject_plans` / `profile_card_settings` / `vocab_lookups` / `word_mastery`）。真正新建只有 2 张表 + 2 个补列（`backend/sql/agent_center_tables.sql`，可重复执行）：

| 对象 | 说明 |
|------|------|
| `agent_prefs` | 智能体参数持久化：UNIQUE(user_id, agent_key, param_key)，`param_value` JSONB，`auto_managed` 自动托管开关（开启后磨合规则接管、前端控件禁用） |
| `agent_tuning_log` | 磨合记录：old/new value + reason + source(auto/manual)，趋势图 markLine 数据源 |
| `xiaoji_messages.kind` | 补列：chat / vision / evaluate 触点区分 |
| `subject_plans.source` | 补列：diagnosis / exam_paper / chat 计划来源区分 |

**19 个触点清单**（12 个现成可计数、4 个补埋点、2 个词条触点随词条本走、0 个为计数建新表）：

| 智能体 | 触点 |
|--------|------|
| 对话 chat | 答疑对话（user_actions.chat）、词义讲解（vocab_lookups·chat_ask）、规划/生成/评估分流（use_*_agent）、日志摘要（learning_logs） |
| 规划 plan | 聊天里问规划（use_plan_agent）、诊断生成计划（diagnosis_results）、答卷生成计划（subject_plans.source=exam_paper）、每日学习讲解（learning_content 非空） |
| 生成 generate | 聊天里出题（use_generate_agent）、资源库生成 / 掌握度定向生成（generate_question + touchpoint）、题集创建（create_set） |
| 评估 evaluate | 聊天里问评估（use_evaluate_agent）、做题提交批改（question_records.ai_feedback 非空）、真题交卷分析（exam_paper_records）、画像 AI 总结（profile_card_settings） |
| 小基 xiaoji | 小基聊天 / 识图 / 评价题目题集（xiaoji_messages.kind）、词条抓取（vocab_lookups·xiaoji_vision）、**快捷提问分流**（use_*_agent·touchpoint=xiaoji_quick_ask/xiaoji_gen_card，2026-09-02 补） |

#### 5.14.2 聚合路由

`backend/routers/agent_center.py`，挂载 `/agent-center`，全部需登录 + `verify_user_match`：

| 端点 | 说明 |
|------|------|
| `GET /agent-center/overview?user_id=&days=` | 总览：KPI 六格（总调用/活跃智能体/计划完成率/生成题量/批改题量/词条抓取）+ 协作闭环 5 步（问题入口→计划→练习批改→错题定向→掌握度）+ 小基陪伴线 + **协同增益 5 对**跨表对照（陪伴日 vs 非陪伴日、有讲解 vs 无讲解、首答 vs 批改后重做等）+ 路由转化 + 动态结论文案 |
| `GET /agent-center/agents/{key}` | 单智能体详情：30 天趋势序列 + 4 统计格 + 触点计数表 + 2 个特点面板（每个 agent 不同，如对话 Agent 的意图路由分布、规划 Agent 的三阶段完成率） |
| `GET/PUT /agent-center/agents/{key}/prefs` | 参数读写（agent_prefs） |
| `GET/POST /agent-center/agents/{key}/tuning` | 磨合记录读写（agent_tuning_log） |
| `POST /agent-center/tuning/run` | 立即执行磨合规则评估（详情页「立即评估」按钮） |

**性能**：单请求要拉 15 张表 → **单连接 + asyncio.gather 并发拉取**（串行要 10s+），跨表联合全部在 Python 侧完成（PostgREST 只做单表过滤）；任何查询失败优雅降级返回 `[]`，分析接口不因单表故障整体报错。

#### 5.14.3 磨合规则引擎

`backend/agents/tuning.py`，6 条规则与详情页参数卡「磨合规则」文案一一对应：

| 规则 | 触发条件 | 动作 |
|------|---------|------|
| 规划·每日任务量 | 计划完成率 <50% / >85% | 任务量 -2（下限 1）/ +1（上限 10） |
| 规划·阶段节奏 | 完成率 <40% / 近 14 天 >80% | 降一档 / 升一档（舒缓→适中→紧凑） |
| 生成·出题难度 | 题集收录率 <60% / >85% | 难度 -2 / +1 |
| 生成·错题针对性 | 错题本 ≥10 题且未开启 | 开启 |
| 评估·错因颗粒度 | 重做正确率 <70% | 加细到知识点级别 |
| 小基·关心频率 | 连续 3 天没学习 | 主动关心 +1 档 |

保护机制：用户关闭「自动托管」的参数不碰；同一参数自动调整有 7-14 天冷却期；没有学习记录的新用户不打扰；单条规则失败不影响其余。

触发方式：① 详情页「立即评估」按钮（`POST /tuning/run`）；② **后台每日任务**——main.py lifespan 启动 asyncio 循环，每 24h 对近 14 天活跃用户逐个评估（用户间限速 1s），应用关闭时 cancel。

#### 5.14.4 前端页面

- `views/AgentCenter.vue`：KPI 行（范围筛选 7/30/90 天联动）+ 协作闭环 + 协同增益 + 路由转化 + 5 张智能体卡（效果指标 + 触点明细 + 可行动建议）→ 点击进详情
- `views/AgentDetail.vue`：Hero + 4 统计格 + 近 30 天趋势图（ECharts 平滑折线 + 渐变面积 + 十字准线 tooltip + 图表/表格双视图，**磨合记录 markLine 竖虚线标注**形成「调整点 vs 指标变化」证据链）+ 触点明细表 + 可行动建议横幅（「一键应用」直接落库 prefs）+ **参数调节**（分段选择/滑块/开关三类控件，每参数独立「自动托管」开关，开启后控件禁用并显示磨合规则与上次调整记录）+ 磨合时间线 + 重置出厂/保存/立即评估
- `api/agentCenter.js`：七个 API 封装；`utils/mockAgents.js` 保留作为字段级映射注释（已全部替换为真实数据）

#### 5.14.5 小基页队长制：呼叫对象下拉 + 队员真实分流（2026-09-02 全套改造）

**定位（08-27 定方向，09-02 落地）**：小基是队长（常驻陪聊调度），专业队员以自己身份在小基世界干活；「对话 Agent」**并入队长**（小基 = 通用对话能力），智能体中心保留其数据卡片。

**交互（用户拍板）**：输入区**工具行**内「呼叫」下拉框选角色（与上传图片/语音等按键同一行）——**小基 5 种模式**：小基（队长）/ 生成 Agent / 规划 Agent / 评估 Agent / 自定义出题（动作不是身份：选中即弹表单并回退上一选择）。选择 localStorage 记忆；**顶部导航**状态（小基名字下方）由「在线」**改为当前角色身份**（按所选队员配色：队长 · 陪聊 / 生成 Agent · 出题…）；输入框 placeholder 按角色切换。

**真实分流（后端按 agent_key 分道，`routers/community/xiaoji.py`）**：

| 呼叫对象 | 真实行为 |
|---------|---------|
| 小基（队长） | 原陪伴聊天通道（人设/语气/上下文不变） |
| 生成 Agent | `POST /community/xiaoji/agent-generate`：用户说了知识点→指定出题；口头禅/留空→**自动选题**（60 天掌握度薄弱→错题主题→综合）→ 复用 `/questions/generate` 真实生成落库 → 题目卡回聊 + 「🎯 选题依据」；薄弱定向自动降「简单」档 |
| 规划 Agent | chat-stream 带 `agent_key=plan`：规划师人设 + **服务端注入真实数据**（学科计划数 / 30 天任务完成率 / 近 7 天逐日 / 自定义计划进度），回复带「查看我的学习计划」行动条 |
| 评估 Agent | chat-stream 带 `agent_key=evaluate`：裁判人设 + 真实数据（30 天做题量/正确率/近 7 天对错/薄弱 TOP5/已掌握/真题卷数），回复带「查看评估报告」行动条 |
| 自定义出题 | 弹窗卡片：新增**学科锚定下拉**（通用自动判定，堵住「不指定科目默认偏 Python」）；沿用真实生成管线逐道出题卡 |

**署名持久化**：assistant 消息落库 `agent` 字段（`backend/sql/fix_xiaoji_agent_column.sql` 补列，幂等），历史消息/刷新后徽章不丢；库表未执行时降级普通保存不阻塞聊天。智能体中心小基卡新增「快捷提问分流」触点（action_touch 组合计数）。

### 5.15 词条本

位于 `/wordbook`（2026-08-23 新增）。把「查词 → 抓取 → 熟练度 → 复习 → 定向出题」串成闭环：用户在对话里问词义、用小基识图拍题时自动收集生词，词条卡打分累积熟练度，薄弱词可复习、可一键生成练习题。

#### 5.15.1 词条生命周期

```
对话问词义 / 小基识图提词（ChatArea detectVocabCards 三模式提取）
  → 渲染词条卡（GET /vocab/entries/{word}，无则 AI 生成全局缓存）
  → 自动记录触点（POST /vocab/lookups，chat_ask / xiaoji_vision）
  → 「认识/不认识」打分（POST /vocab/mastery，EWMA 平滑）
  → 词条本（GET /vocab/wordbook，统计 + 筛选 + 列表）
  → 复习模式（薄弱词逐卡过关） / 薄弱词定向出题（POST /vocab/practice-set
     → questions + generation_history → 资源库「生成历史」练习）
```

#### 5.15.2 数据设计

`backend/sql/vocab_tables.sql`（可重复执行）：

| 表 | 说明 |
|----|------|
| `vocab_entries` | **词条本体全局共享**：word 唯一，AI 生成一次全员复用（phonetic/meaning/example/tags/source） |
| `vocab_lookups` | 抓取/讲解记录（user + word + touchpoint：chat_ask 对话问词义 / xiaoji_vision 识图提词），兼作智能体中心触点计数源 |
| `word_mastery` | 熟练度（UNIQUE(user_id, word)，EWMA 平滑，与知识点掌握度同构） |

熟练度算法：`新分 = 旧分 × 0.7 + 目标 × 0.3`（认识 → 100，不认识 → 20），初始即目标值；≥80 已掌握、<60 薄弱。

#### 5.15.3 后端 API

`backend/routers/vocab.py`，路径内嵌 `/vocab` 前缀，全部需登录：

| 端点 | 说明 |
|------|------|
| `GET /vocab/entries/{word}` | 查词条；不存在 → call_llm(t=0.4) 生成（system prompt 限定只输出 JSON + 容错正则提取）→ 缓存入库；插入失败也返回内存条目 |
| `POST /vocab/lookups` | 记录触点（去重、小写、单次 ≤20 词） |
| `POST /vocab/mastery` | 认识/不认识打分 → EWMA 更新 + 计数 |
| `GET /vocab/stats?user_id=` | 词条本统计：总数 / 已掌握 / 薄弱 / 平均熟练度 |
| `GET /vocab/wordbook?user_id=&filter=` | 词条本列表（熟练度升序薄弱在前；filter: all/weak/mastered；释义 `in()` 批量补全前 100 条，避免 N+1） |
| `POST /vocab/practice-set` | 薄弱词定向出题：call_llm(t=0.8) 每词一道单选题（含中文解析）→ 写入 questions（source=generated）+ generation_history → 资源库练习 |

#### 5.15.4 前端交互

- `components/ChatArea.vue` 词条提取 `detectVocabCards` 三模式：① 问词义（"abandon 是什么意思"）② 整句就是一个单词 ③ 识图模式从 AI 回复提取英文生词（stopwords 过滤，≤5 个）；回复下方渲染词条卡
- `components/VocabCard.vue`：词 + 音标 + 释义 + 例句 + 「认识 ✓ / 不认识 ✗」打分（实时显示熟练度）；挂载自动记录 lookups；触点可复用（chat_ask / xiaoji_vision / wordbook）
- `views/Wordbook.vue`：4 统计格 → 筛选（全部/薄弱/已掌握）→ 列表（词 + 释义 + 音标 + 熟练度条 + 对/总次数）→ **复习模式**（薄弱词逐卡过关，进度 N/M）→ **薄弱词出题**（生成后跳资源库）
- 入口：侧边栏「词条本」（蓝绿渐变图标），路由 `/wordbook`
- 说明：`xiaoji_vision` 触点当前实际来自**主对话区带图消息**（ChatArea 识图模式提词），小基页（XiaojiCall）尚未接入词条卡；复习模式打分不重复记 lookups

### 5.16 视频库（2026-09-04 新建）

**定位**：轮盘一级模块（NAV_ITEMS「视频库」+ `video-library.png` 图标，`/video-square`）。自营「知识点级」模板生成视频库，取代外部视频推荐。视频与题目解耦——检索键 = 知识点（subject + 短哈希），一个知识点其下所有题复用同一条；覆盖资源库生成题与学科计划题库，天然适配多端（小程序复用同一 API 与公共桶音频）。

#### 5.16.1 生成引擎与分镜脚本

- **链路**：qwen-turbo 分镜脚本（DashScope，`settings.QWEN_VIDEO_MODEL`）→ 千问 TTS（小基同款四音色 longan\*，语速 6 档 `VIDEO_TTS_SPEED`，**只用阿里云模型**）→ Supabase Storage 公共桶 `video-lib/{id}/audio.mp3`
- **分镜脚本 v3**：`title / hook / scenes[{mood, widget, params, narration}] / narration`；构件白名单 point·array·balance·example·phrase；口播 ≥240 字质检 + 失败修补重写一次；mood 四态（lecture 严谨 / story 轻松比喻 / highlight 重点强调 / demo 例题示范）逐镜切换，旁白语气随之变化
- **队列**：进程内 asyncio worker（lifespan 挂载，`VIDEO_WORKERS` 默认 1）；`(subject, knowledge_key, angle)` 唯一格 + generating 占位幂等；失败自动重试 1 次，failed 旧格 409 自愈复活（先复活后新插，杜绝重复行）
- **触发**：题目落库 fire-and-forget `ensure_videos`（`questions.py`）；学科计划暖库 CLI `scripts/warm_video_lib.py --per N`（每考纲各取热搜前 N）/ 后台批量生成；`POST /video/lib/ensure|warm`、`GET /video/lib/related`（100 本知识点 / 70 同学科 / 55 全局 + `question_video_links` 快照）
- **省钱原则**：知识点级去重、按格生产（低 1 / 中 3 / 高 6+ 待热度扩产）、脚本与音轨解耦、命中即复用、失败降级 B 站搜索卡

#### 5.16.2 广场·详情·互动

- `/video-square` 广场：学科 chips（17 考纲）+ 搜索 + 最热/最新/点赞榜；卡片 = 脚本首节内容预览 + 播放键 + 角度/时长/作者/播放点赞
- `/video/:id` 详情：点赞/收藏（toggle 幂等 + 冗余计数）、评论（软删除、本人可删）、举报（6 理由 → 后台）、分享链接复制、播放上报（use_count + 人日去重 views_count + **热点词库** video_keyword_hits）
- 我的：生成（学科 + 知识点 + 角度可选，作者 = 本人昵称头像，初始仅自留）、发布审核流（private → pending → public/rejected）、重试、删除；收藏列表
- 生成主（author）：官方基智（logo 头像角标）；用户生成走昵称头像

#### 5.16.3 播放器与视觉语言

- `VideoLessonPlayer`：16:9 舞台 + 电影黑边/暗角/颗粒 + 镜头缓推；背景池 4 套程序化背景（按视频身份稳定抽取）+ 4 mood 氛围色联动（讲知识冷静蓝 → 比喻暖橙 → 重点脉冲红 → 例题紫）
- **分镜演出台**（真·演示动画，画面主体 = 图形在演）：array（**带「左指针/右指针」标签的大指针连续滑行**、数字飞出相加、和值 0→N 滚动、判决「太大/太小」、命中绿爆）/ balance（易错对比 + 双印章）/ example（例题演算台：题干 → 步骤推进 → 答案盖章弹入）/ phrase（金句逐字砸入）+ point 批注（限用）
- 开场 = **钩子屏**（悬念问题，无标题屏）；片尾小结 + 金句；**单行字幕**（10~18 字按标点合并切句、句尾符号不显示、整句上屏）
- 旧 sections 脚本优雅降级（板书/卡片两模板）

#### 5.16.4 数据表与后台

- 表：`video_library`（含 owner_user_id / publish_status / 四计数）、video_likes、video_favorites、video_comments、video_reports、video_views、video_keyword_hits——RLS 全放行 + 三角色授权
- SQL 四件套（幂等）：`create_video_library.sql` + `fix_video_library_author.sql` + `fix_video_social.sql` + `fix_video_storage_policy.sql`
- 后台 `/admin/videos`：概览 7 格（总数/在播/待审核/生成中/失败/总播放/待处理举报）→ 全量视频表（通过/驳回/下架/重试）→ 举报台（驳回 or 下架）→ 批量暖库（考纲 × 每科 N × 角度数）→ 全部写审计日志

### 5.17 自定义快捷键（2026-09-28 新增）

用户要求：「搞一个自定义快捷键，在设置里面搞」+「**应用内生效**」+「**跟随账号**」。

#### 5.17.1 目录结构

```
frontend/src/shortcuts/
  registry.js           动作清单（唯一数据源 · 25 个动作）
  combo.js              组合键规范化 / 解析 / 匹配
  store.js              绑定状态 + 本地缓存 + 账号同步 + 冲突检测
  manager.js            分发器（全站唯一 keydown 点）
  ShortcutsSection.vue  设置页 UI（录制态 + 冲突提示）
backend/sql/user_shortcuts.sql   表（照 user_theme_settings 先例）
backend/routers/auth.py          GET/PUT /auth/shortcuts
```

**新增一个可绑定的动作 = 只在 `registry.js` 加一条**，分发器、设置页列表、冲突检测、恢复默认全部从那里读。

#### 5.17.2 为什么要有「分发器」这一层

键盘事件原来散在三处，**先后取决于监听器注册顺序**：`desktop/index.js` 的浏览器快捷键拦截、`GlobalSearch.vue` 的 Ctrl+K、各组件的 `@keyup.enter`。那是隐式依赖 —— 用户把 Ctrl+R 绑成别的动作时，谁吃掉事件就变得不可预测。

收进一个分发器后，优先级是**写在代码里的常量**：

```
① 内置屏蔽（internal）—— preventDefault 后什么都不做
② 输入态保护 —— 焦点在输入框时放行一切无修饰键的按键（否则打字就被吃）
③ 用户绑定
④ 默认绑定
```

> ⚠️ **① 必须排在 ② 之前。** 屏蔽的那几个键里 **F5 / F12 是裸键**（无修饰键），
> 正好落进 ② 的放行条件；顺序反了，焦点一在输入框里它们就漏网 ——
> 用户打着字按 F5，页面刷新、草稿没了。
>
> 这个 bug 特别容易看着「好像是好的」：同批的 Ctrl+R / Ctrl+P / Ctrl+U / Ctrl+Shift+I
> 都带修饰键，根本不进 ② 的放行分支，**一直是对的**。实测确认过：
> 焦点在页面时 6 个全屏蔽，焦点在输入框时**只有 F5 和 F12 漏**。

已拆掉两处旧监听：`desktop/index.js` 的拦截 → 变成 `sys.block*` 内置动作；
`GlobalSearch.vue` 的 Ctrl+K → 变成 `action.search`，**用户现在能改它了**。

#### 5.17.3 存储：本地缓存 + 账号权威

| 层 | 作用 |
|---|---|
| localStorage | 缓存。首屏立刻能响应按键，不用等账号资料回来；未登录时它是唯一来源 |
| `user_shortcuts` 表 | **权威**。登录后拉取、改动后回写，换电脑也在 |

**合并规则：账号里有的以账号为准，账号里没有的保留本地** ——
「没登录时改过、然后登录」不会把本地改动吞掉。

表结构用 JSONB 存整个映射（`{"nav.home": "Ctrl+Shift+H", ...}`）：
快捷键是**变长映射**，没法像主题那样「一个设置一列」。**空串表示主动解绑**
（与「没有这个键」区分开）。增删动作**不需要动这张表**，注册表里没有的 id 会被忽略。

#### 5.17.4 一个不存在过的动作

第一版按惯例加了 `action.theme`「切换深浅色」。查了才发现：**项目 09-03 就去掉了浅/深开关**，外观改成四轴定制，theme store 里根本没有这个方法。那个动作按了不会有任何反应 —— 已删，并在 `registry.js` 里留了说明。

> 这正是这个项目最忌讳的「看起来有、其实是空的」。

### 5.18 异步任务队列（Redis + arq，2026-09-28 新增）

用户：「**最好先架构好这个消息队列，不然后期麻烦一大堆**」。

#### 5.18.1 为什么需要

`video_gen.py` 原本已有**进程内队列**（`asyncio.Queue` + `_pending` 去重 + worker 循环），设计底子是对的（队列只传标识、状态落在数据库行里）。但有四个洞：

1. **只在进程内** → 重启全丢
2. **多 worker 不协调** → 起两个 uvicorn = 两套队列，同一格重复跑
3. **没有统一重试/退避** → 每个模块自己实现一遍
4. **前端只能轮询，且会提前放弃** → 视频生成实测 **4 分 14 秒**，小程序轮询 5×8s=40s 就放弃 —— 这正是「视频一直加载不出来」的根因之一

而且 `asyncio.create_task` 已经在四处各写各的。

#### 5.18.2 一个重要取舍：不是所有 create_task 都该迁

| 类型 | 例子 | 处理 |
|---|---|---|
| **用户等着的长任务** | 视频生成、交卷后批量 AI 分析 | **进队列** |
| **藏延迟的优化** | 记忆压缩、智能体 grounding 预取 | **留在原地** |

第二类本来就是「顺手做掉、丢了也无所谓」，挪进队列会从「让响应更快」变成「延迟执行的副作用」，反而错。

#### 5.18.3 落地与约束

```
services/task_queue.py   队列封装 + 任务实现 + 完成通知
worker.py                常驻 worker 入口（带 Redis 预检）
config.py                REDIS_URL + TASK_QUEUE_FALLBACK_INLINE
```

**关键设计：Redis 连不上时默认抛错，不静默降级。** 这个项目在「看起来在跑、其实没跑」上吃的亏太多了。真要退回进程内执行，必须显式打开 `TASK_QUEUE_FALLBACK_INLINE=true`，且日志里会有 ERROR。

**完成通知**：任务跑完写一条进 `notifications` 表（复用 `create_notification`，它做了聚合 upsert 不会刷屏），用户去消息中心看。**不推 SSE/WebSocket**。

#### 5.18.4 ⚠️ 考试批量分析**没有迁**，理由是它还不满足前提

`exam_papers._batch_ai_analyze_wrong` 是模块私有函数、入参是**内存里的列表**，且它在 `_save_paper_record` **之前**触发 —— worker 无从按 ID 重读。要迁得先重构：**先存记录、再按 `record_id` 入队**。

> **排队的前提是「任务能被标识符重新捞起来」**。不满足就别硬塞 ——
> 硬塞进来只会做出一个跑不通的任务。

**部署依赖**：服务器要装 Redis 并常驻 `python worker.py`，`REDIS_URL` 要进生产 `.env`。

## 6. 后端 API 参考

> 全部端点挂 `https://api.jizhi-learn.com`。生产共 **217 条路由**（`GET /openapi.json` 可查）。
> 除公开端点外都需要 JWT，身份校验在 FastAPI 层（`verify_user_match`）。

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
      "exam_papers": [                    // 12 套真题卷元数据（disabled 标注不可练卷面）
        { "name": "2024年6月真题", "file": "cet4_2024_06.json", "available_score": 568 }
      ]
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

#### 微信登录 / 账号（2026-09-28 重构后）

```
POST /auth/wx-login                           # 小程序 code 换 JWT；openid 查不到则**当场建号**
POST /auth/set-credentials                    # 补真实邮箱 + 密码（只对占位邮箱账号开放）
GET  /auth/account-status                     # 客户端据此决定显示「修改密码」还是「设置邮箱和密码」
GET  /auth/wechat/user/{user_id}              # 查询用户 (本地缓存回退)
GET  /auth/shortcuts/{user_id}                # 读快捷键绑定（不返回默认值，默认键在前端注册表）
PUT  /auth/shortcuts                          # 全量保存快捷键绑定
```

**`/auth/wx-login` 返回值**：已有账号与首次登录**返回同一种形状** ——
`{ access_token, user, need_bind: false }`。首次登录时后端已静默建号（占位邮箱
`wx_{openid}@miniapp.local`），所以 `need_bind` 恒为 `false`。

> ⚠️ **已删除的 4 个扫码端点**（历史，勿再引用）：
> `GET /auth/wechat/qrcode`、`GET /auth/wechat/bind-qrcode`、
> `GET /auth/wechat/callback`、`GET /auth/wechat/poll/{poll_token}`
> —— 连同它们的轮询返回值语义（`ready` / `bound`）一起移除。**路由数 22 → 18**。
> 原因见 5.11.0。

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
POST /chat/send { messages, intent, user_id }   # 流式对话主端点 (SSE)，按 intent 路由
POST /chat/title { messages }                    # 从首轮对话生成标题 (≤20 字)
POST /chat/vision { image_url, question }# 图片识别 (DeepSeek V4.1 Flash)
```

### 6.5 小基语音助手 API

前缀 `/community/xiaoji`（`backend/routers/community/xiaoji.py`，主路由，全部需登录）：

```
POST /community/xiaoji/chat                # 文字聊天 (豆包角色模型，最近 10 条上下文)
POST /community/xiaoji/vision              # 图片理解 (千问 qwen3-vl-flash)
GET  /community/xiaoji/messages            # 聊天记录 (asc；?search= 模糊搜索 ilike.*kw*)
GET  /community/xiaoji/config              # 获取配置 (?user_id=)
PUT  /community/xiaoji/config              # 更新配置 (查→PATCH / 无→INSERT Upsert)
POST /community/xiaoji/evaluate-question   # 单题 AI 批改
POST /community/xiaoji/evaluate-set        # 题集 AI 评估
POST /community/xiaoji/evaluate-question-stream  # 流式批改 (SSE)
POST /community/xiaoji/tts / asr           # 语音合成/识别 (讯飞)
```

前缀 `/xiaoji`（`backend/routers/xiaoji.py`，兼容层；清空记录等端点仍被前端使用）：

```
GET    /xiaoji/config/{user_id}            # 获取配置
PUT    /xiaoji/config/{user_id}            # 更新配置
GET    /xiaoji/messages/{user_id}?search=  # 聊天记录 (desc，支持搜索)
DELETE /xiaoji/message/{message_id}?user_id=  # 删除单条
DELETE /xiaoji/messages/{user_id}          # 清空全部 (前端「清空记录」按钮)
POST   /xiaoji/tts / asr                   # 语音合成/识别
```

### 6.6 智能体中心 API

前缀 `/agent-center`（`backend/routers/agent_center.py`），全部需登录：

```
GET    /agent-center/overview?user_id=&days=        # 总览：KPI + 协作闭环 + 协同增益 + 路由转化
GET    /agent-center/agents/{key}?user_id=&days=    # 单智能体详情（chat/plan/generate/evaluate/xiaoji）
GET    /agent-center/agents/{key}/prefs?user_id=    # 参数读取（agent_prefs）
PUT    /agent-center/agents/{key}/prefs?user_id=    # 参数保存（批量 upsert）
GET    /agent-center/agents/{key}/tuning?user_id=   # 磨合记录（近 100 条，倒序）
POST   /agent-center/agents/{key}/tuning            # 写入磨合记录（source: manual/auto）
POST   /agent-center/tuning/run?user_id=            # 立即执行磨合规则评估
```

### 6.7 词条本 API

前缀 `/vocab`（`backend/routers/vocab.py`），全部需登录：

```
GET  /vocab/entries/{word}                          # 查词条（无则 AI 生成并全局缓存）
POST /vocab/lookups { user_id, words, touchpoint }  # 记录触点（chat_ask / xiaoji_vision，≤20 词）
POST /vocab/mastery { user_id, word, known }        # 认识/不认识打分（EWMA 熟练度）
GET  /vocab/stats?user_id=                          # 总数 / 已掌握 / 薄弱 / 平均
GET  /vocab/wordbook?user_id=&filter=               # 词条本列表（all/weak/mastered，薄弱在前）
POST /vocab/practice-set { user_id, words }         # 薄弱词定向出题（写入 questions + generation_history）
```

### 6.8 通用响应规范与错误码

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
| `/profile` | Profile | `{requiresAuth:true}` | 个人中心 (信息展示页) |
| `/resource-lib` | ResourceLib | `{requiresAuth:true}` | 资源库 |
| `/video-square` | VideoSquare | `{requiresAuth:true}` | 视频库广场（09-04） |
| `/video/:id` | VideoDetail | `{requiresAuth:true}` | 视频详情（点赞/收藏/评论/举报/分享） |
| `/evaluation-center` | EvaluationCenter | `{requiresAuth:true}` | 评估中心 |
| `/evaluation-report` | EvaluationReport | `{requiresAuth:true}` | 评估报告 |
| `/evaluation-table` | EvaluationTable | `{requiresAuth:true}` | 评估表 |
| `/career` | Career | `{requiresAuth:true}` | 生涯规划 |
| `/career/rank` | CareerRank | `{requiresAuth:true}` | 排行榜 |
| `/career/tasks` | CareerTasks | `{requiresAuth:true}` | 生涯任务 |
| `/career/achievements` | CareerAchievements | `{requiresAuth:true}` | 生涯成就 |
| `/do-question/:taskId` | DoQuestion | `{requiresAuth:true}` | 做题(旧版，带任务 id) |
| `/do-question` | DoQuestion | `{requiresAuth:true}` | 做题(旧版，无任务) |
| `/set-detail` | SetDetail | `{requiresAuth:true}` | 题集详情 |
| `/generate-from-mastery` | GenerateFromMastery | `{requiresAuth:true}` | 按掌握度生成计划 |
| `/animation-demo` | AnimationDemo | （无 meta） | 动画演示页（开发用） |
| `/vlp-debug` | VlpDebug | `{requiresAuth:false}` | 视频播放器调试页（临时） |
| `/mastery-board` | MasteryBoard | `{requiresAuth:true}` | 掌握度看板 |
| `/learning-plan` | LearningPlan | `{requiresAuth:true}` | 学习计划 |
| `/plan-preview` | PlanPreview | `{requiresAuth:true}` | 计划预览 |
| `/plan-detail/:id` | PlanDetail | `{requiresAuth:true}` | 计划详情 |
| `/profile-card` | ProfileCard | `{requiresAuth:true}` | 个人画像星图 |
| `/qa` | QAPage | `{requiresAuth:false}` | 帮助中心（08-22 公开） |
| `/message` | MessageCenter | `{requiresAuth:true}` | 消息中心 |
| `/api-center` | ApiCenter | `{requiresAuth:true}` | API 模型中心 |
| `/agent-center` | AgentCenter | `{requiresAuth:true}` | 智能体中心 |
| `/agent-center/:agentKey` | AgentDetail | `{requiresAuth:true}` | 智能体详情调节 |
| `/wordbook` | Wordbook | `{requiresAuth:true}` | 词条本 |
| `/open-source` | OpenSource | `{requiresAuth:false}` | 开源项目（08-22 公开） |
| `/guide` | Guide | `{requiresAuth:true}` | 使用指引 |
| `/theme` | ThemeShare | `{requiresAuth:false}` | 外观码分享直达页（免登录预览 + 一键应用） |
| `/settings` | Settings | `{requiresAuth:true}` | **统一设置中心（10 模块，含桌宠 / 快捷键）** |
| `/community` | Community (子路由) | `{requiresAuth:true}` | 社区 (8 子路由) |
| ~~`/xiaoji/settings`~~ | → **redirect 到 `/settings`** | —— | 小基设置已内嵌进设置中心（2026-09-28），保留路由只为老书签不断 |
| ~~`/xiaoji/call`~~ | → **redirect 到 `/home`** | —— | 小基 = 主界面（2026-08-25） |
| `/xiaoji/voice-call` | XiaojiVoiceCall | `{requiresAuth:true}` | 小基语音通话（独立沉浸页） |
| `/xiaoji/search` | XiaojiSearch | `{requiresAuth:true}` | 小基搜索页 |
| **学科计划 (新)** |
| `/subject-plan` | SyllabusHub | `{requiresAuth:true}` | ★ 考纲列表 |
| `/subject-plan/:syllabusId` | SyllabusDetail | `{requiresAuth:true}` | ★ 考纲详情 |
| `/subject-plan/:syllabusId/practice` | SubjectPractice | `{requiresAuth:true}` | ★ 做题页 |
| `/subject-plan/:syllabusId/exam/:paperId` | ExamPaper | `{requiresAuth:true}` | ★ 真题套卷 |
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
│  来源 A: 邮箱密码登录     来源 B: 小程序微信一键登录      │
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

### 9.4 微信 OAuth 接入（2026-09-28 已整节移除）

> **本节作废。** 网页端的「公众号测试号扫码登录」与「登录后绑定微信」两条链路
> 已于 2026-09-28 全部删除。原因见 5.11.0：测试号是开发调试工具不该上生产，
> 而个人主体**也做不了**网页/APP 的微信登录（要企业主体 + 300 元/年认证）。

**当前各端的登录方式**：

| 端 | 登录方式 |
|---|---|
| 网页 / 桌面 | 邮箱 + 密码、邮箱验证码 |
| 微信小程序 | `wx.login()` → `POST /auth/wx-login`，**首次自动建号**（占位邮箱 `wx_{openid}@miniapp.local`）；之后可在设置页补真实邮箱 + 密码，把这个账号「打通」到其他端 |

**为小程序仍保留的**：`profiles.wechat_openid` / `wechat_unionid` 两列
（`backend/sql/add_wechat_columns.sql`）—— 小程序的 openid 仍存在这里，**别删**。

**同时失效的**：`BACKEND_EXTERNAL_URL`（原为微信回调地址，现无消费方）、
`qrcode` + `Pillow` 依赖、后端监听 80 端口的要求。

**扫码登录没有取消，只是推迟**：用户明确——扫码那一端**只做 Flutter 手机应用**，
等它出来再做，小程序不掺和。

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
        model=get_model(),          # deepseek-flash（V4.1 Flash）
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

# 批改 Prompt：按题型给「批改重点 + 专属结构化字段」（EVAL_SPECS）
# 2026-09-11 之前是所有题型共用一段 detailed_analysis 自由文本，
# 模型返回什么全看运气，前端也没法按题型展示。
prompt = f"""批改以下{type_label}题：
题目: {stem}
参考答案: {ref}
学生答案: {user_answer}

输出 JSON（字段随题型而定）：
{{"score": 0-100, "is_pass": true/false,
  "feedback": "简短批改意见（50字内）",
  ...该题型的专属字段}}
"""

# 使用 low temperature 保证一致性
fb = call_llm([...], temperature=0.3)  # ← 0.3: 减少随机性，评分更稳定
```

**各题型的专属结构化字段**：

| 题型 | 专属字段 | 说明 |
|------|---------|------|
| 选择题 | `option_analysis` | A/B/C/D **逐项**对错与理由 |
| 计算题 | `steps` | 分步对错，能定位到哪一步错的 |
| 简答题 | `key_points` | 得分点逐个命中情况 |
| 编程题 | —— | **有测试用例时已由沙箱判分，明确要求 AI 不要推翻判分结果** |

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
  ├── 1. 取题：本地题库优先 (bank_get_by_ids)
  │     → 找不到则**回落到 Supabase `questions` 表**（AI 生成的题走这条）
  │     → content.test_cases[] 或 content 文本中的 ---TEST_CASES--- 块
  │     题型闸接受 `programming` 与 `coding` 两种写法
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
  │     │       │   javac -encoding UTF-8 Main.java → java Main < stdin
  │     │       │   （-encoding 不能省：源码按 UTF-8 落盘而 javac 跟随平台
  │     │       │    编码，中文 Windows 是 GBK，含中文的代码必然编译失败）
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
```

**Java（JDK 17）——不要用 winget 装。**

2026-09-11 实测：`winget install Microsoft.OpenJDK.17` 在**非交互会话里是"假成功"**——
MSI 请求管理员提权但 UAC 弹不出来，安装器根本没执行（MSI 日志没生成、注册表/磁盘/`winget list`
三处查无此物），winget 却回报"已成功安装"。

实际方案是**免管理员的 zip 解压到仓库内预留路径**：

```
backend/utils/jdk/          # OpenJDK 17.0.20.1 LTS，已进 .gitignore
```

`code_runner.py` 通过 `_JDK_BIN = _UTILS_DIR / "jdk" / "bin"` 直接找它，无需装到系统、无需配 PATH。

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

### 14.5 ⚠️ 导出与截图的现代颜色适配

**这是一条硬约定，改导出相关代码前必读。**（2026-09-27 排查「导出失败」时定位）

#### 根因

项目里 `color-mix()` 用了 **1124 处、74 个文件**。而图片/PDF 导出走的是 `html2canvas@1.4.1` —— 一个 2022 年的库，它的颜色解析器：

```js
// node_modules/html2canvas/dist/html2canvas.js:1837
var SUPPORTED_COLOR_FUNCTIONS = { hsl, hsla, rgb, rgba };   // ← 只有这四个
// :1726
throw new Error("Attempting to parse an unsupported color function \"" + value.name + "\"");
```

**Chrome 在 computed value 阶段就把 `color-mix()` 算掉了**，序列化成：

```
color(srgb 0.62549 0.809804 1)      ← 函数名是 "color"，不在表里 → 直接 throw
```

实测四种位置**全都是这个形式**：`color` / `backgroundColor` / `borderColor`、连渐变里的色标。

#### 修法：把已算好的颜色降级，不加依赖

**关键洞察：混色数学不用重算** —— 浏览器已经算完了，只需把 `color(srgb r g b / a)`
转成 `rgba(R,G,B,A)` 写成 inline style（inline 优先级最高，会带进 html2canvas 的 clone）。

`frontend/src/utils/exportColor.js`：`normalizeModernColors(el)` + `withNormalizedColors(el, fn)`。

**这和项目已有约定是一致的**：`stores/theme.js` 的 `withAlpha()` 注释写着
「ECharts canvas 不认 CSS var()/color-mix —— 品牌色半透明需 JS 解析成 rgba」。
同一次主题改版里 **ECharts 适配了、html2canvas 漏了**。所以补共用 util 比引新库更贴既有架构。

#### 实现上的一个坑

第一版是**边读 computed style 边写 inline style**，交替进行会「写一次 → 下次读强制重排」，
资料卡有几百个节点，会明显卡。必须**两趟**：先全读收集、再全写。各只触发一次布局。

#### 连带修掉的静默失败

`EvaluationReport.vue` / `EvaluationTable.vue` 有一字不差的
`if (!reportContentRef.value) return`，而 `pdfExporting` 在 return **之后**才置位。
导出根节点只存在于 `v-else` 分支 → **报告加载中点击什么都不会发生**（没 toast、没 loading、没报错）。
这是与「导出失败」**不同的症状**，容易被当成另一个 bug 去查。已改为明确提示。

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
| ~~微信扫码无法回调~~ | 该功能 2026-09-28 已整条移除 | 保留此行仅作历史 |
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
| 34 | 无微信扫码登录 | 小程序有但网页版没有 | 公众号测试号 OAuth + 扫码轮询 ⚠️ **2026-09-28 整套移除**（测试号是开发工具不该上生产；个人主体也做不了网页微信登录） | auth.py |
| 35 | 微信登录不安全（扫码即创建用户） | 自动创建用户有冒用风险 | 区分 login/bind 模式，login 必须已绑定 ⚠️ **2026-09-28 反向改回**：小程序端改为「微信一键登录**直接建号** + 之后可补邮箱密码」，不再有 bind 模式（见 5.11） | auth.py |

---

## 17. 微信小程序端

> 代码位于 **`D:\jizhi-miniapp`**，独立于本仓库，**不受版本控制**（改动前请手工备份）。
> 复用本仓库的同一套 FastAPI 后端，无独立服务端。

### 17.1 端定位与技术栈

| 项 | 值 |
|---|---|
| 框架 | uni-app 3（`3.0.0-5010520260709002`）+ Vue 3.4 组合式 API |
| 编译目标 | 微信小程序（`mp-weixin`），appid `wx6db1f1a6e3f3969c` |
| 状态管理 | Pinia（`stores/auth.js`、`stores/theme.js`） |
| 后端地址 | `utils/constants.js` 按 `NODE_ENV` 切换：dev → `localhost:8000`，build → `https://api.jizhi-learn.com` |
| 规模 | 42 个页面 / 全部 `<script setup>` |

**页面写法约定**：42 个页面无例外全部使用 `<script setup>`，模板根节点为单个 `<view>`。

### 17.2 导航形态（与网页端对齐，无底部 TabBar）

网页端的应用外壳不是多 Tab 站点，而是**小基主界面 + 18 项弧形轮盘**（`Home.vue` 仅 19 行，整个是 `<XiaojiCall/>`）。小程序按同一形态实现：

- 底部 5 Tab **已撤**（`CustomTabBar.vue` 已删除）
- 小基首页承载 **18 项功能宫格**，另设**全局搜索页** `pages/search/index`（对齐网页端 Ctrl+K）
- 每个一级页面顶栏都有 🔍 入口
- `uni.switchTab` 在项目中已不存在

**跳转规则（`utils/constants.js`）**：

| 场景 | API | 原因 |
|---|---|---|
| 一级模块平级切换 | `goTop(url)` → `redirectTo` | 替换当前页，栈深度恒为 2，**原生导航栏会画返回箭头** |
| 回首页 | `goTop()` 内部走 `reLaunch` | 首页是根，不该有返回 |
| 二级页面 | `navigateTo` | 保留返回 |
| 自定义导航栏页面的返回 | `goBackHome()` | 能退就退，退不了回首页 |

> ⚠️ **踩过的坑**：曾用 `uni.reLaunch` 做一级模块切换，结果 `reLaunch` 清空页面栈、栈里只剩自己，**微信原生导航栏认为「没地方可回」就连返回箭头都不画**，那些页面进去出不来。改用 `redirectTo` 解决。
> `学科计划` / `我的` / `小基` / `搜索` / `登录` 五页是 `navigationStyle: custom`（无原生栏），需自绘左上角返回。

### 17.3 双主题系统（浅色 / 深色）

**刻意不同于网页端的四轴主题**（背景/组件/主题/字体 + 外观码分享 + 适配度打分）。小程序只做两档，理由：四轴的复杂度在小程序上收益极低。

| 项 | 实现 |
|---|---|
| 模式 | `'system'`（默认，跟随系统）/ `'light'` / `'dark'` |
| 持久化 | `uni.setStorageSync('jizhi-theme-mode')` |
| 系统监听 | `uni.onThemeChange`，需 `manifest.json` 开 `"darkmode": true`（否则读不到系统主题） |
| 入口 | 设置页「外观」分区，分段控件 |
| token 定义 | `App.vue` 全局 `<style>`，两套值挂 `.t-dark` / `.t-light` |
| 挂载 | 页面根节点 `:class="themeStore.rootClass()"` |

**token 清单（约 25 个）**：背景 4 / 表面 3 / 描边 2 / 弹窗与遮罩 2 / 吸底栏 1 / 文字 4 / 品牌 5 / 语义 6。

**原生导航栏联动**：`uni.setNavigationBarColor` 只作用于**当前页**。用户改完主题返回其他页面时，那些页面的原生栏仍停在旧色，顶部出现割裂边。解法是 `main.js` 里一个全局混入：

```js
app.mixin({ onShow() { useThemeStore(pinia).syncChrome() } })
```

比在 42 个页面各写一遍 `onShow` 可靠。

> ⚠️ `page` 元素拿不到主题类（它没有 class），`App.vue` 里 `page { background-color: var(--bg) }` 只能是深色默认值。浅色下真正露出的底色由两处兜住：根 view 的 `min-height:100vh` + 自带背景，以及运行时 `uni.setBackgroundColor`（管回弹区）。

### 17.4 分类色板与页面色调

**配色分工（重要）**：

- **语义色**（`--success` / `--warning` / `--danger` 及 `-soft`）**只表状态**——对错、警告、分数档位
- **分类色**（`--c-<hue>` / `--c-<hue>-soft`）**只表归属**——模块、学科、分类、分组

两者严格分开，不可混用。

**9 个色相**：`red` `orange` `amber` `green` `teal` `cyan` `blue` `violet` `pink`

**页面色调 `--tone`**：`stores/theme.js` 按**路由前缀**推导（`ROUTE_TONE` 表），根节点挂 `tone-xxx` 类，页面内标题统一引用 `var(--tone)`。于是每个模块自动带自己的色，不必逐页写死。认不出路由时回落品牌色。

| 模块 | 色调 | 模块 | 色调 |
|---|---|---|---|
| 小基 / 个人画像 / 登录 | violet | 学程 / 时间胶囊 | amber |
| 个人中心 / 学科计划 / API | blue | 社区 / 计时器 / 工具箱 | orange |
| 设置 / Q&A | teal | 评估中心 / 智能体中心 | pink |
| 资源库 / 消息中心 / 搜索 | cyan | 词条本 / 打卡 | green |
| 视频库（未接入） | red | | |

> ⚠️ **两个必须遵守的顺序约束**：
> 1. `.tone-*` 规则必须排在 `.t-dark` / `.t-light` **之后**——两者特异性相同，靠源码顺序决胜。写在前面会被 `--tone` 的兜底值覆盖，色调永远出不来。
> 2. `rootClass()` 是**函数不是 computed**——路由是页面级状态，computed 会被 Pinia store 单例缓存，第二个页面拿到的还是第一个页面的色调。

### 17.5 包体积与启动优化

微信主包**硬限制 2 MB**，开发者工具建议线 1.5 MB。

| 项 | 改前 | 改后 |
|---|---|---|
| 主包精确体积 | **2.32 MB（超硬限制，无法上传）** | **0.99 MB** |
| `static/` | 1724 KB | 366 KB |
| 页面数 | 42 | 42 |

**做法**：

1. **图片转 WebP + 缩放**（省 1358 KB）
   - 5 张 xiaoji 形象图：415–426px → 360px，`216 KB/张 → 17 KB/张`
   - 26 个图标：200×200 → 128×128，`630 KB → 254 KB`
   - 图标实际显示仅 `46rpx`（3x 屏需 69px），原图大了 3 倍
   - **用 WebP 而非 JPEG**：xiaoji 有 20–25% 全透明像素（角色抠图），JPEG 不支持透明会出白框
2. **按需注入**（`manifest.json` → `mp-weixin.lazyCodeLoading: "requiredComponents"`）
   - 本项目**无任何自定义组件**（`components/` 为空，无 `usingComponents` 声明），开启零风险
   - 收益主要在**页面**：42 个页面之前启动时全部注入执行，开启后只注入当前页

### 17.6 隐私接口与合规

**实际使用的隐私接口（仅 2 类）**：

| 接口 | 微信隐私类别 | 用在哪 |
|---|---|---|
| `chooseMedia` ×3、`chooseImage` ×1 | **选中的照片或视频信息** | 小基识图、发动态配图、私聊发图、OCR 拍照识别 |
| `setClipboardData` ×1 | **剪切板** | 评估表「复制诊断结果」 |

**不涉及**：位置、麦克风/录音（TTS 是**播放**，走 `InnerAudioContext`，非隐私接口）、用户信息（登录走 `uni.login` 拿 code，非 `getUserProfile`）、手机号、通讯录、蓝牙、微信运动。

**上线前必须在微信公众平台配置**：「设置 → 服务内容声明 → 用户隐私保护指引」勾选上表两类。**不勾的后果**：用户首次用到时不弹授权框，接口直接失败——识图、发图、复制诊断全部不可用。此项仅在后台配置，代码改不了。

> ⚠️ `manifest.json` 里的 `permission.scope.userLocation`（"用于展示学习打卡地理位置"）是**早期残留**，代码中零调用。提审时可能被审核员质疑。
> 将来真要做定位，**必须同时在 `requiredPrivateInfos` 里加 `"getLocation"`**——2022 年后微信要求如此，光写 `permission.desc` 不够，调用会直接失败。

### 17.7 与网页端的有意差异

用户定调原则：**「能上的就上，上不了的就不上，不要低质量」**。以下为**刻意不做**，非遗漏：

| 模块 | 为什么不上 |
|---|---|
| **视频库** | 网页端**没有 mp4**——库里是 mp3 音轨 + JSON 分镜脚本，播放靠前端 canvas 实时绘制。小程序 `<video>` 无源可放；重写播放器约 2000 行。真要上得**后端加 mp4 合成产线** |
| 个人画像 3D 维度宇宙 | three.js + CSS3DRenderer 需要 DOM。已改 **2D 九维版**，信息量一条没少 |
| 全双工语音通话 | 小程序录音无 AEC，外放会把 AI 的声音录回去，抢话逻辑必自激 |
| B站 iframe / PDF 导出 / 本地视频抽帧 | 域名白名单 / 无对应能力 / canvas 不接受 video 元素 |

### 17.8 全量 token 化（已完成）

42 个页面的硬编码色值已全部迁到 CSS 变量：

```
984 处硬编码 hex  →  1346 处 var()
残留 28 处为有意保留（品牌渐变配白字、模型厂商品牌色等内容色）
```

> ⚠️ **迁移时的两个硬约束**（将来再加色值务必遵守）：
> 1. **颜色替换只能作用于 `<style>` 块**。项目里有 93 处颜色是 **JS 数据**，且 `hexToRgba()` 会解析 hex 字符串——盲替会直接打断它们。
> 2. **深色 rgba 是单独的坑**：`rgba(15,23,42,0.92)` 这类既不是 `#0f172a` 也不是白色叠加，初次迁移整类漏掉，导致浅色模式下 7 处吸底栏/弹窗仍是黑块。现由 `--bar` / `--sheet` 承载。

### 17.9 已知未验证项（截至 2026-09-18）

**小程序从未真机 / 开发者工具实测过**，只跑通了编译。以下全部待验证：

| 项 | 状态 |
|---|---|
| 双主题实际观感、浅色配色定稿 | 对比度已算过（文字四档 ≥3:1、9 个分类色全部达标），但**观感未经肉眼确认** |
| WebP 兼容性 | 微信 `<image>` 支持 webp（iOS 需基础库 2.9.0+），**未实测** |
| `darkmode: true` 副作用 | 开启后微信会给原生组件套深色样式，已加运行时覆盖 |
| 按需注入后页面表现 | 无自定义组件、风险极低，但官方要求修改后必须确认表现正常 |
| 隐私接口授权弹窗 | 依赖后台配置，配好后需真机验一次识图与复制 |
| 后端接口实际返回 | 接口层已核对（95 个端点全部存在、零方法不匹配），但**带登录态的返回内容未验** |

**下一步应该是实跑，而不是继续加功能。**

### 17.10 2026-09-23 视觉大轮（43 页放大 + 上色）

用户：「适当的放大一些东西，然后多彩一些，**要按照两种背景色分配不同的多彩**」+「视觉上要让用户感觉这个小程序有意思」。范围选的是**全项目 43 个页面一起**。

#### 先派审计摸底数，结论出乎意料

> **九色分类色板基本是死代码** —— `var(--c-*)` 全项目**只有 2 处活的引用**；
> `--tone-soft` **0 消费者**，而它正是用来做彩色底托的；
> `--tone` 有 32 处，**每一处都只是标题的文字颜色**。

量化底数：135 处 ≤56rpx（28px）的尺寸声明散在 34 个文件；五个「尺寸源头」（8rpx 进度条轨道 15 文件、72rpx 控件框 18 文件、80rpx 14 文件…）；`<style>` 里 108 处颜色字面量；**147 处颜色写在 `<script>` 里**（24 个文件，通过 `:style` 注入，**结构上不跟主题**）。

#### 尺寸：36 个文件 / 117 条规则

| 模式 | 变化 |
|---|---|
| 进度条轨道 | 8rpx (4px) → **14rpx (7px)** |
| 控件 / 头像框 | 72rpx → **88rpx** |
| 主按钮 / 列表头像 | 80rpx → **96rpx** |
| 状态圆点 | 14rpx → **20rpx** |
| 小色块 / 编号圆 | 34→44、44→56、52→64、56→68、60→72 |

**头像类必须宽、高、圆角三个值一起改** —— 只改 height 会变成椭圆。这条写进脚本判断里了。

#### 浅色主题的真 bug（15 处，已修）

| bug | 症状 |
|---|---|
| 分类色写死成深色值 | 浅色下**色相错 + alpha 只有 0.10（该 0.18）** |
| 同一按钮两个红 | 底 `#f56c6c`（Element-UI 红）、字 `#f87171`（深色 `--danger`） |
| 深色 brand 当描边 | 白卡上几乎看不见 |
| 深色遮罩 | 浅色下比该有的暗一倍 |
| 选中态用错靛蓝 | 6 个文件，每个选中描边都是错的 |

#### 一条规则点亮 29 个页面

```css
.sec-title, .page-title, .block-title, .section-title, .action-title, .group-title {
  background: var(--tone-soft);
  border-left: 8rpx solid var(--tone);
  border-radius: 0 12rpx 12rpx 0;
  padding: 6rpx 18rpx;
}
```

只加背景和左右内边距，**不动 `display` 与字号**，避免打乱各页排版。

#### 根背景（43 页共用）

原来只有 **2 个同色（品牌靛蓝）光晕**，所以整页是「空」的。新增三档彩色氛围光，**深浅两套是两组不同的值**：

```
深色：rgba(167,139,250,.11)  rgba(56,189,248,.075)  rgba(244,114,182,.075)
浅色：rgba(124,58,237,.075)  rgba(2,132,199,.055)   rgba(219,39,119,.05)
```

**浅色必须压得更低** —— 白底会把颜色冲淡，给高了就糊成一片脏色。

#### emoji → uni-icons

26 个 WebP 图标混了四种风格（3D 渲染插画 / 扁平单色），不适合当 UI 小图标。改用 `uni-icons`。

**⚠️ 先验证字体会不会加载**：微信的 `loadFontFace` **不认本地文件路径**，必须 base64 或 https 白名单域名。如果 uni-icons 从 CDN 取字体，小程序里会整片豆腐块——比 emoji 更糟。
**先只加一个图标构建，查产物**：`uni-icons.wxss` → `url(data:font/ttf;base64,...)` —— **base64 内联**，不依赖网络、不需要配域名白名单。161 个图标，整个 wxss 54 KB。

#### 胶囊避让：全项目只留一处

根因不只是位置：页面用 `env(safe-area-inset-top)` 定位顶栏，而**这个值在安卓上常常是 0**，顶栏会整体顶进状态栏和胶囊里。

全项目 **18 个页面自绘顶栏**，但只有**自定义导航栏**的会被胶囊压到（5 个页面）。胶囊几何计算本来散在 4 处 —— **这个 bug 就是这么来的：首页有留白、搜索页漏了**。收进 `utils/constants.js` 的 `getNavMetrics()`，4 个页面统一成一行 style。

> **同一个算式出现第二次时就该抽出来。**

#### ⚠️ 本轮未验证

**所有改动只验证到「编译通过」** —— 没有进过微信开发者工具，没有真机实测。从「个人中心重做」到「117 条尺寸规则 + 29 页上色」，**全部没有肉眼确认过**。验证清单见 17.9。

---

## 18. 桌面版（Tauri 壳）

> **2026-09-27 立项，09-28 加桌宠，09-29 补齐轮盘与设置。**
> 产物在 `_devtools/jizhi-desktop/` —— 刻意放在 `project1` 仓库**之外**，
> 不会被提交、也不会被部署脚本带上。

### 18.1 定位与技术栈

| | |
|---|---|
| 框架 | Tauri **v2**（Rust 壳 + 系统 WebView2） |
| 安装包 | **1.4 MB**（对比 Electron 同功能约 150 MB —— 国内下载体验差距是决定性的） |
| 与网页端的关系 | **不是重写**，是壳。主窗口直接加载线上站点 |
| 与小程序的关系 | 无。桌面版是「网页端 + 桌面能力」，不是第四套 UI |

**为什么是「加载线上站点」而不是本地打包前端**：

- 零 CORS 问题（来源即站点自身）
- 网站一更新，客户端就是最新的，**不需要做前端更新机制**
- 代价：**桌面版依赖网页端已部署**。前端没上线，桌面版跟着一起停摆
  —— 这条在打包流程里是硬约束，见 18.7

### 18.2 双窗口模型

| | `main` | `pet`（桌宠） |
|---|---|---|
| 内容 | 远程站点 `https://www.jizhi-learn.com` | 壳内本地 `ui/pet.html` |
| 尺寸 | 1600×1000（**设计宽度**，见下） | 220×220（基准，可被设置页缩放） |
| 装饰 | `decorations: false` —— 无边框，窗口按钮由**网页端**画 | 无边框、透明、`alwaysOnTop`、`skipTaskbar` |
| 焦点 | 常规 | `focus: false` —— 不抢焦点，不打断你正在做的事 |

**设计宽度 1600 不是随手定的**。项目里有一条居中补偿规则
`@media (max-width:1500px) { .call-main { padding-left:420px } }`，
`padding-left: P` 会把内容中心推到 `视口中心 + P/2`（实测 1440 宽时右偏 210px）。
桌面版用 Tauri 的**浏览器缩放**把视口钉在 1600，那条媒体查询永不触发，小基才是真居中。

⚠️ **不能用 CSS `zoom` 代替**：`zoom` 不放大布局视口，`100vh` 仍按真实视口算
（内容画不满窗口、底部露底色），且媒体查询照样按真实宽度触发 —— 等于没缩放。

### 18.3 桌宠

桌宠是**桌面级**的：独立透明置顶窗口，关掉主程序也还在（这是用户明确选的形态）。

#### 交互：悬停轮盘（2026-09-29 定稿）

| 手势 | 行为 |
|---|---|
| 鼠标移入小基 | 轮盘展开，窗口从 220 长到 340（**中心不动**） |
| 滚轮上下 | 转着选，**循环**（到底绕回开头） |
| 左键单击 | 确认选中项；有下级的进第二层，**内层同一套操作** |
| 右键 / Esc | 退回上一层；已在第一层则整体收起 |
| 按住拖动 | 换位置 |
| 鼠标移开 | 收起轮盘 |

**第一层四项**（可在设置页逐项开关）：`🎙 语音` · `🎨 换个样子` · `⏱ 专注计时` · `👋 先躲起来`。

**两种特殊的层**：

- `kind: 'look'` —— **滚动即预览**。滚到哪一项小基当场变脸，不必确认；
  确认才固定，退回则还原成进来之前那张脸。
- `kind: 'dial'` —— **转盘**。不是固定几个选项，滚动连续调时长（5–90 分钟，另有「停止」档），
  当前值固定在正上方，滚动时整圈数字一起变 —— 看着像表盘在转。

#### 两个必须记住的实现约束

**① 无焦点的窗口照样收得到滚轮。** 已实测：鼠标悬停在桌宠上滚动，
窗口 `hasFocus=false` 也能收到；鼠标移开再滚，一次都收不到。
所以**不需要在移入时 `setFocus()`** —— 那会在用户打字时把焦点夺走。
（依赖 Windows 的「悬停时滚动非活动窗口」+ WebView2 支持。）

**② 展开与收起必须用同一个锚点。** 展开用 `center`、收起用默认的右下角，
300 多像素的差会让小基整个平移一下。表现就是用户报的「松开鼠标它自己挪了一点点」。

#### 「先躲起来」不能关

它是**收起桌宠的唯一入口**（没有托盘图标、没有别的恢复路径）。
设置页里刻意**不给它开关**（`pinned: true`）—— 关掉它 = 桌宠再也收不起来。

#### 专注计时

到点小基换「开心」脸并冒一句话。计时中脚下显示 `⏱ 24:31`。
选择的时长走转盘层，第二层。

### 18.4 配置桥：为什么需要它

**桌宠窗口与主窗口是两个不同的 origin**（一个是本地 `pet.html`，一个是远程站点）。
同源策略下，桌宠**读不到主窗口的 localStorage** —— 拿不到登录 token、
不知道后端地址、也不知道用户在设置页选了什么。

所以由主窗口把这三样**推给壳**（只存内存、不落盘，它是令牌），桌宠再问壳要：

| 通道 | 内容 | 为什么不能写死 |
|---|---|---|
| `set_pet_token` | 登录 JWT | 退出登录时推空串 |
| `set_pet_api_base` | 后端地址 | 开发是 `localhost:8000`、生产是 `api.jizhi-learn.com`，写死在 html 里必有一边是错的 |
| `set_pet_prefs` | 设置页里的偏好（轮盘项开关、尺寸） | 见下 |

**偏好走的是「改动即广播」，不是轮询。** `set_pet_prefs` 存下之后会
`emit("pet-prefs")`，桌宠监听后立刻重渲染。

> 这条是踩坑换来的：第一版桌宠是轮询取配置的，而且轮询被写成
> `if (!cfg.token) await loadCfg()` —— 语义变成「只有还没拿到才去要」，
> token 一到就**再也不回读**。结果设置页改了开关，桌宠毫无反应。
> 事件驱动之后是即时的，轮询只留作兜底。

### 18.5 ACL：Tauri v2 权限的两个坑

`src-tauri/permissions/app-commands.toml` 声明允许的命令。**这个文件是必须的**：

1. **Tauri v2 默认拒绝所有插件命令**，不显式授权则自绘标题栏的按钮**静默失效**
   —— 点了毫无反应、无任何报错。
2. **壳自定义的 `#[tauri::command]` 不会自动获得许可。** 本地页面调用一般没事，
   但本项目主窗口加载的是**远程站点**，远程内容受 ACL 管辖。没声明的命令会被拒，报错是
   `<命令名> not allowed. plugin not found`。
   **「plugin not found」极具误导性** —— 它让人以为插件没装，实际是「这个命令不在许可名单里」。

另需 `capabilities/default.json` 里的 `remote.urls` 声明远程源，
否则权限只对本地页面生效——**等于没配**。

#### Rust 侧命令清单

| 命令 | 用途 |
|---|---|
| `save_file` | 原生「另存为」（导出 PDF/图片走它，不走浏览器下载栏） |
| `open_external` | 外链交给系统浏览器（只放行 http/https，防命令注入） |
| `app_version` | 壳的版本号（网页端无从知道壳的版本，只能问壳） |
| `show_main_window` | 拉主窗口到前台。**当前无调用方**（用户定：桌宠不打开主窗口） |
| `set_pet_visible` / `is_pet_visible` | 桌宠显隐 |
| `set_pet_token` / `set_pet_api_base` / `set_pet_prefs` | 配置桥（18.4） |
| `get_pet_config` | 桌宠一次性取回 token + 后端地址 + 偏好（少一轮 IPC） |
| `set_pet_size` | 改窗口尺寸，带 `anchor`：`center`（轮盘，中心不动）/ 默认右下角（语音面板） |

### 18.6 ⚠️ 开发配置：`tauri.dev.conf.json` 是**死文件**

**Tauri v2 只认这五个平台配置名**：
`tauri.{linux,windows,macos,android,ios}.conf.json`。
**没有 `.dev.` 这一档。**

本项目曾把 dev 用的地址写进 `tauri.dev.conf.json`，
**它从来没被读过** —— 于是 `tauri dev` 里主窗口一直加载的是**线上站**
（base 配置里的生产地址），表现为「本地改了半天看不到变化」。
更糟的是它**静默**：没有任何报错，只是行为和你预期的不一样。

**正确做法是 CLI 的 `--config`**（`package.json`）：

```json
"dev": "tauri dev --config src-tauri/tauri.dev.conf.json"
```

**不能改名成 `tauri.windows.conf.json`** —— 那个名字在 `tauri build` 时也会生效，
会把**生产安装包**指到 `localhost:5173`，装出来的客户端直接白屏。

> **验收信号**（改完必须看这三个，缺一不可）：
> ① Vite 上出现 **ESTABLISHED 连接**；② 落地页消失；③ 右上角出现窗口控制按钮。

### 18.7 打包与发布

```bash
cd _devtools/jizhi-desktop
npm run dev     # 开发：主窗口加载 localhost:5173
npm run build   # 产出 src-tauri/target/release/bundle/nsis/JIZHI_x.y.z_x64-setup.exe
```

**⚠️ 顺序是硬约束：先部署网页前端，再打安装包。**

桌面版加载的是线上站。前端没上线就打安装包，用户装到的是**旧前端 + 新壳**：

- 没有窗口控制按钮 → **无边框窗口既拖不动也关不掉**
- 没有落地页跳过 → 装了客户端还看一遍营销页
- 没有桌宠开关 → 设置了也打不开

（用户拿到的是一个必须用任务管理器杀的窗口。这条在 09-27 和 09-28 各记过一次。）

### 18.8 已知未验证项

| 项 | 状态 |
|---|---|
| 桌宠的行为验证 | 09-29 实测了：轮盘展开/收起、中心不动、贴边夹取、滚轮选择、换表情实时预览、缩放联动。**语音面板（按住说话 → TTS）未实测** |
| 语音输入 | 用浏览器自带 `SpeechRecognition`（WebView2），**不是**服务端 ASR（服务器缺 `websocket-client`，`/xiaoji/asr` 一直 500） |
| 开机自启 | 用 `tauri-plugin-autostart`，开关状态**问壳要**（注册表 Run 项才是真相）。**未实际重启验证过** |
| 打包安装包 | 现存安装包是 **09-27** 的，**不含桌宠**（桌宠 09-28 才做）。要重打 |
| 真机验收 | 只在本机跑过 |

---

## 19. 附录

### 19.1 环境变量完整参考

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
| `BACKEND_EXTERNAL_URL` | ❌ | `http://localhost:8000` | 后端外网地址。**当前无消费方**（原用于微信 OAuth 回调，该功能已移除） |
| `VOLC_ACCESS_KEY` | ❌ | — | 火山引擎 AK |
| `VOLC_SECRET_KEY` | ❌ | — | 火山引擎 SK |
| `ARK_API_KEY` | ❌ | — | 豆包 API Key |
| `XUNFEI_APPID` | ❌ | — | 科大讯飞 APPID |
| `XUNFEI_API_KEY` | ❌ | — | 科大讯飞 API Key |
| `XUNFEI_API_SECRET` | ❌ | — | 科大讯飞 API Secret |
| `REDIS_HOST` | ❌ | `localhost` | Redis 主机 |
| `REDIS_PORT` | ❌ | `6379` | Redis 端口 |
| `REDIS_PASSWORD` | ❌ | — | Redis 密码 |

### 19.2 考纲配置规范

新增一个考纲的完整步骤：

1. **编辑 `backend/data/syllabi.json`**，添加考纲条目（参考第 5.2 节 schema）
2. **创建题库文件** `backend/data/{question_bank}.json`，初始为 `[]`
3. **运行生成脚本** `python scripts/seed_all_banks.py {id}` 生成初始题目
4. **前端无需改动** — 考纲列表、详情、做题页均从 `syllabi.json` 动态渲染

### 19.3 题目 JSON Schema

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

### 19.4 术语表

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

> **文档结束** · 基智学习助手 (Jizhi Learn) · v2.2 · 2026-09-29