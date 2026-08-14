<template>
  <div class="eval-fullpage">
    <button class="ev-back" @click="goBack">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
      <span>返回</span>
    </button>

    <div class="ev-section blue" @click="goReport">
      <div class="ev-icon-wrap">
        <svg viewBox="0 0 24 24" fill="none" stroke="#93c5fd" stroke-width="1.5"><path d="M18 20V10M12 20V4M6 20v-6"/></svg>
      </div>
      <div class="ev-title">学情报告</div>
      <div class="ev-desc">学习进度的数据仪表盘</div>
      <ul class="ev-points">
        <li>知识点掌握度汇总与趋势</li>
        <li>薄弱 / 待巩固 / 已掌握三段分布</li>
        <li>学习动态时间线记录</li>
        <li>支持导出 PDF 保存</li>
      </ul>
      <div class="ev-enter">进入 →</div>
    </div>

    <div class="ev-section amber" @click="goAssessment">
      <div class="ev-icon-wrap">
        <svg viewBox="0 0 24 24" fill="none" stroke="#fcd34d" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 12h6M9 16h6M9 8h6"/></svg>
      </div>
      <div class="ev-title">评估表</div>
      <div class="ev-desc">综合能力深度诊断工具</div>
      <ul class="ev-points">
        <li>九个维度加权综合评分</li>
        <li>开拓期 → 巅峰期五级评级</li>
        <li>雷达图展示维度强弱对比</li>
        <li>智能生成优势 / 短板 / 建议</li>
      </ul>
      <div class="ev-enter">进入 →</div>
    </div>

    <div class="ev-section green" @click="goPlan">
      <div class="ev-icon-wrap">
        <svg viewBox="0 0 24 24" fill="none" stroke="#6ee7b7" stroke-width="1.5"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/><path d="M9 14l2 2 4-4"/></svg>
      </div>
      <div class="ev-title">学习规划</div>
      <div class="ev-desc">量身定制的长期学习路线</div>
      <ul class="ev-points">
        <li>AI 拆分知识点 → 生成每日任务</li>
        <li>日期解锁机制，逐天推进</li>
        <li>学习内容 + 做题 + 视频三大板块</li>
        <li>评估表可一键跳转生成规划</li>
      </ul>
      <div class="ev-enter">进入 →</div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function goBack() {
  router.push('/resource-lib')
}

function goReport() {
  router.push('/evaluation-report')
}

function goAssessment() {
  router.push('/evaluation-table')
}

function goPlan() {
  router.push('/learning-plan')
}
</script>

<style scoped>
.eval-fullpage {
  display: flex; align-items: center; justify-content: center;
  gap: 16px; padding: 52px 24px 24px;
  height: 100vh;
  position: relative;
}

/* 返回按钮 */
.ev-back {
  position: absolute; top: 14px; left: 24px; z-index: 10;
  display: flex; align-items: center; gap: 6px; padding: 8px 14px;
  border-radius: 10px; border: 1px solid rgba(255,255,255,.06);
  background: rgba(0,0,0,.3); color: #94a3b8; font-size: 13px;
  cursor: pointer; backdrop-filter: blur(12px); transition: all .25s;
  font-family: inherit;
}
.ev-back:hover { background: rgba(0,0,0,.5); color: #e2e8f0; }
.ev-back svg { width: 14px; height: 14px; }

.ev-section {
  flex: 1; align-self: stretch;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 12px; cursor: pointer;
  border-radius: 20px;
  border: 1px solid rgba(255,255,255,.06);
  backdrop-filter: blur(20px);
  transition: all .3s ease;
  padding: 40px 28px;
}
.ev-section.blue  { background: linear-gradient(160deg, #3b82f6 0%, #6366f1 40%, #8b5cf6 100%); }
.ev-section.amber { background: linear-gradient(160deg, #f59e0b 0%, #f97316 40%, #ef4444 100%); }
.ev-section.green { background: linear-gradient(160deg, #10b981 0%, #06b6d4 40%, #3b82f6 100%); }
.ev-section:hover {
  border-color: rgba(255,255,255,.12);
  transform: translateY(-4px);
}

.ev-icon-wrap {
  width: 64px; height: 64px; border-radius: 16px;
  display: flex; align-items: center; justify-content: center;
  transition: transform .3s;
}
.ev-section.blue  .ev-icon-wrap { background: rgba(59,130,246,.12); border: 1px solid rgba(59,130,246,.15); }
.ev-section.amber .ev-icon-wrap { background: rgba(245,158,11,.12); border: 1px solid rgba(245,158,11,.15); }
.ev-section.green .ev-icon-wrap { background: rgba(16,185,129,.12); border: 1px solid rgba(16,185,129,.15); }
.ev-icon-wrap svg { width: 28px; height: 28px; }
.ev-section:hover .ev-icon-wrap { transform: scale(1.08); }

.ev-title { font-size: 20px; font-weight: 700; color: #e2e8f0; }
.ev-desc { font-size: 13px; color: #64748b; text-align: center; max-width: 280px; line-height: 1.6; }
.ev-points { margin: 0; padding: 0 0 0 16px; list-style: none; text-align: left; }
.ev-points li { font-size: 12px; color: #94a3b8; line-height: 2; position: relative; }
.ev-points li::before { content: '·'; position: absolute; left: -12px; color: #475569; font-weight: 700; }
.ev-enter {
  margin-top: 4px; font-size: 13px; color: #475569;
  opacity: 0; transform: translateY(6px); transition: all .3s;
}
.ev-section:hover .ev-enter { opacity: 1; transform: translateY(0); }

@media (max-width: 768px) {
  .eval-fullpage { flex-direction: column; padding: 60px 20px 40px; gap: 12px; }
  .ev-section { flex: none; width: 100%; max-width: 100%; min-height: 200px; padding: 32px 20px; }
}
</style>