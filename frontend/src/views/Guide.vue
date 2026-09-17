<template>
  <div class="guide-page">
    <div class="guide-container">
      <!-- 封面 -->
      <div class="guide-cover">
        <button class="guide-back" @click="$router.back()">
          <i class="fas fa-arrow-left"></i> 返回
        </button>
        <h1 class="guide-product">基智学习助手</h1>
        <h2 class="guide-title">使用说明书</h2>
        <p class="guide-tagline">选一门考试，AI 陪你学到上岸</p>
        <span class="guide-ver">v{{ appVersion }} · Beta</span>
      </div>

      <!-- 产品简介 -->
      <section class="guide-section">
        <h3>产品简介</h3>
        <p class="guide-text">
          基智学习助手是一款 AI 备考平台：覆盖 17 个考纲、19,000+ 道题、12 套真题，
          从摸底诊断 → 三阶段备考计划 → 每日任务 → 真题冲刺，全程由 5 个 AI 智能体（对话/规划/生成/评估/小基）陪伴学习。
        </p>
      </section>

      <!-- 一、快速上手 -->
      <section class="guide-section">
        <h3>一、快速上手</h3>
        <ol class="guide-steps">
          <li><strong>注册登录</strong> — 邮箱注册或微信扫码，完成学习偏好引导（阶段/目标/每日时长）</li>
          <li><strong>选考纲，生成计划</strong> — 学科计划 17 考纲任选，摸底诊断或真题答卷生成三阶段计划</li>
          <li><strong>每日任务</strong> — AI 实时讲解 → 做题练习 → 错题复习，掌握度自动更新</li>
          <li><strong>真题冲刺</strong> — 12 套真题计时做题、交卷出分、AI 错因分析</li>
          <li><strong>磨合智能体</strong> — 智能体中心调节参数或开启自动托管，越用越贴合</li>
        </ol>
      </section>

      <!-- 二、功能速览 -->
      <section class="guide-section">
        <h3>二、功能速览</h3>
        <div class="guide-table">
          <div v-for="m in modules" :key="m.path" class="guide-row" @click="$router.push(m.path)">
            <span class="guide-module">{{ m.name }}</span>
            <span class="guide-desc">{{ m.desc }}</span>
            <span class="guide-go">→</span>
          </div>
        </div>
      </section>

      <!-- 三、常用操作 -->
      <section class="guide-section">
        <h3>三、常用操作</h3>
        <ul class="guide-ops">
          <li><kbd>Ctrl</kbd>+<kbd>K</kbd> — 任意页面全局搜索，快速跳转页面 / 考纲 / 真题 / 智能体 / 词条</li>
          <li><strong>自定义钉选</strong> — 全局搜索「＋ 添加自定义项」，点选收录常用入口，✎ 可重命名</li>
          <li><strong>词条打分</strong> — 词条卡点「认识 ✓ / 不认识 ✗」，熟练度实时更新</li>
          <li><strong>交卷出分</strong> — 真题交卷即出分，客观题自动判、主观题 AI 批改</li>
          <li><strong>参数托管</strong> — 智能体参数开启「自动托管」，系统按你的行为自动微调</li>
        </ul>
      </section>

      <!-- 四、注意事项 -->
      <section class="guide-section">
        <h3>四、注意事项</h3>
        <ul class="guide-notes">
          <li>听力、上机操作等无法模拟的卷面标注「不可练习」，分数按可练部分计算</li>
          <li>词条释义与题目讲解由 AI 生成，仅供参考，重要知识点以教材为准</li>
          <li>视频推送、视频数字人功能正在建设中，即将上线</li>
          <li>全站 AI 调用使用平台官方 Key，无需自行配置即可使用</li>
        </ul>
      </section>

      <!-- 五、更多帮助 -->
      <section class="guide-section">
        <h3>五、更多帮助</h3>
        <p class="guide-text">
          遇到具体问题，可在 <router-link class="guide-link" to="/qa">帮助中心</router-link> 按关键词查找解答，
          或通过侧边栏「意见反馈」联系我们。
        </p>
      </section>

      <p class="guide-foot">基智学习助手 · 使用说明书 · 更新于 2026-08</p>
    </div>
  </div>
</template>

<script setup>
import pkg from '../../package.json'

const appVersion = pkg.version

const modules = [
  { name: '小基',        path: '/home',          desc: 'AI 学习伙伴：聊天双模式 + 语音通话 + 推荐/关心/日志' },
  { name: '学科计划',   path: '/subject-plan',  desc: '17 考纲 · 题库 · 诊断 · 每日任务' },
  { name: '词条本',     path: '/wordbook',      desc: '生词收集 · 熟练度 · 复习 · 定向出题' },
  { name: '资源库',     path: '/resource-lib',  desc: '生成题目 · 题集 · 错题本 · 掌握度' },
  { name: '智能体中心', path: '/agent-center',  desc: '5 个智能体统计 · 参数调节 · 磨合' },
  { name: '学程',       path: '/career',        desc: '段位 · 等级 · 任务 · 成就' },
  { name: '个人画像',   path: '/profile-card',  desc: '维度宇宙学情画像' },
  { name: '设置',       path: '/settings',      desc: '资料 · 偏好 · 外观 · 通知 · 安全' },
  { name: '社区',       path: '/community',     desc: '动态广场 · 好友 · 排行 · 收藏' },
  { name: '消息中心',   path: '/message',       desc: '公告 · 消息' },
  { name: '帮助中心',   path: '/qa',            desc: 'FAQ 常见问题解答' },
  { name: 'API 管理',   path: '/api-center',    desc: '模型平台总览 · 预览演示' },
]
</script>

<style scoped>
.guide-page {
  min-height: 100vh;
  padding: 32px 20px 48px;
  display: flex;
  justify-content: center;
}
.guide-container {
  width: 100%;
  max-width: 760px;
  border-radius: 18px;
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--line-soft);
  padding: 30px 40px 24px;
  height: fit-content;
}
[data-theme="light"] .guide-container { background: color-mix(in srgb, var(--surface, #ffffff) 92%, transparent); border-color: rgba(15,23,42,.09); }

/* ===== 封面 ===== */
.guide-cover {
  text-align: center;
  padding-bottom: 22px;
  border-bottom: 2px solid color-mix(in srgb, var(--brand) 35%, transparent);
  position: relative;
}
.guide-back {
  position: absolute; left: 0; top: 0;
  display: inline-flex; align-items: center; gap: 6px;
  background: transparent; border: none; color: var(--text-secondary);
  font-size: 13px; cursor: pointer; padding: 4px 8px; border-radius: 8px;
  transition: all .2s ease; font-family: inherit;
}
.guide-back:hover { color: var(--text-primary); background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent); }
.guide-product { margin: 0; font-size: 26px; font-weight: 800; color: var(--text-primary); letter-spacing: 2px; }
.guide-title {
  margin: 8px 0 6px; font-size: 18px; font-weight: 600; color: var(--brand);
  letter-spacing: 6px;
}
.guide-tagline { margin: 0 0 10px; font-size: 13px; color: var(--text-secondary); }
.guide-ver {
  display: inline-block; font-size: 11px; color: var(--text-muted);
  border: 1px solid var(--border-color); border-radius: 10px; padding: 2px 10px;
}

/* ===== 章节 ===== */
.guide-section { padding: 20px 0 6px; }
.guide-section h3 {
  margin: 0 0 12px; font-size: 16px; font-weight: 700; color: var(--text-primary);
  display: flex; align-items: center; gap: 10px;
}
.guide-section h3::before {
  content: ''; width: 4px; height: 16px; border-radius: 2px;
  background: linear-gradient(180deg, var(--brand), #8b5cf6);
}
.guide-text { margin: 0; font-size: 14px; color: var(--text-secondary); line-height: 1.9; }
.guide-link { color: var(--brand); text-decoration: none; }
.guide-link:hover { text-decoration: underline; }

/* 快速上手 */
.guide-steps { margin: 0; padding-left: 4px; list-style: none; counter-reset: step; display: flex; flex-direction: column; gap: 10px; }
.guide-steps li {
  counter-increment: step;
  font-size: 14px; color: var(--text-secondary); line-height: 1.7;
  display: flex; gap: 12px; align-items: baseline;
}
.guide-steps li::before {
  content: counter(step);
  flex-shrink: 0; width: 24px; height: 24px; border-radius: 50%;
  background: linear-gradient(135deg, color-mix(in srgb, var(--brand) 25%, transparent), rgba(139,92,246,.25));
  border: 1px solid color-mix(in srgb, var(--brand) 40%, transparent);
  color: var(--brand-bright); font-size: 12px; font-weight: 700;
  display: inline-flex; align-items: center; justify-content: center;
}
.guide-steps strong { color: var(--text-primary); }

/* 功能速览表 */
.guide-table {
  border: 1px solid rgba(255,255,255,.06); border-radius: 12px; overflow: hidden;
}
[data-theme="light"] .guide-table { border-color: rgba(15,23,42,.08); }
.guide-row {
  display: flex; align-items: center; gap: 14px;
  padding: 11px 16px; cursor: pointer;
  border-bottom: 1px solid rgba(255,255,255,.04);
  transition: all .2s ease;
}
.guide-row:last-child { border-bottom: none; }
.guide-row:hover { background: color-mix(in srgb, var(--brand) 8%, transparent); }
[data-theme="light"] .guide-row { border-bottom-color: rgba(15,23,42,.05); }
.guide-module { font-size: 14px; font-weight: 600; color: var(--text-primary); width: 96px; flex-shrink: 0; }
.guide-desc { flex: 1; font-size: 12.5px; color: var(--text-muted); }
.guide-go { color: var(--brand); font-size: 14px; opacity: 0; transition: all .2s; }
.guide-row:hover .guide-go { opacity: 1; transform: translateX(2px); }

/* 常用操作 / 注意事项 */
.guide-ops, .guide-notes { margin: 0; padding-left: 0; list-style: none; display: flex; flex-direction: column; gap: 9px; }
.guide-ops li, .guide-notes li {
  font-size: 13.5px; color: var(--text-secondary); line-height: 1.7;
  padding-left: 18px; position: relative;
}
.guide-ops li::before {
  content: '·'; position: absolute; left: 4px; color: var(--brand); font-weight: 700;
}
.guide-notes li::before {
  content: '⚠'; position: absolute; left: 0; color: color-mix(in srgb, #e6a23c 70%, var(--text-primary)); font-size: 12px;
}
.guide-ops strong { color: var(--text-primary); }
.guide-ops kbd {
  border: 1px solid var(--line); background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent);
  border-radius: 4px; padding: 1px 5px; font-size: 11px; font-family: inherit; color: var(--text-secondary);
}

/* 页脚 */
.guide-foot {
  margin-top: 24px; padding-top: 14px; text-align: center;
  font-size: 11.5px; color: var(--text-muted);
  border-top: 1px solid rgba(255,255,255,.06);
}
[data-theme="light"] .guide-foot { border-top-color: rgba(15,23,42,.06); }

@media (max-width: 640px) {
  .guide-container { padding: 22px 18px; }
  .guide-row { flex-wrap: wrap; }
  .guide-module { width: 100%; }
}
</style>
