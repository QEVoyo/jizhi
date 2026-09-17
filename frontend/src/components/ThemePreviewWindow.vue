<template>
  <!-- 小页面预览窗（2026-09-03 从 Settings 抽出，2026-09-04 供外观码导入/分享页复用）：
       窗口框 + 侧栏 + 主内容，背景/组件/主题/字体四轴全 inline 联动，与真实 App 同款氛围公式 -->
  <div class="pvw-window">
    <div class="pvw-titlebar">
      <span class="pvw-dots"><i></i><i></i><i></i></span>
      <span>基智 · 学习主页</span>
    </div>
    <div class="pvw-stage" :style="{ background: stageBg }">
      <div class="pvw-glow" :style="{ background: glow }"></div>

      <!-- mini 侧栏：组件色玻璃 + 品牌 logo/激活项 -->
      <aside class="pvw-side" :style="{ backgroundColor: ghost }">
        <i class="pvw-logo" :style="{ background: brand, color: btnInk }">基</i>
        <i v-for="(n, k) in ['首页', '计划', '题库', '我的']" :key="k"
           class="pvw-nav"
           :class="{ on: k === 1 }"
           :style="{
             color: k === 1 ? text.primary : text.secondary,
             backgroundColor: k === 1 ? brandSoft : 'transparent',
             borderColor: k === 1 ? brandBorder : 'transparent' }">
          {{ n[0] }}
        </i>
      </aside>

      <!-- mini 主内容 -->
      <div class="pvw-main">
        <div class="pvw-head">
          <div>
            <div class="pvw-htitle" :style="{ color: text.primary }">今日学习计划</div>
            <div class="pvw-hsub" :style="{ color: text.muted }">{{ today }}</div>
          </div>
          <span class="pvw-hbtn" :style="{ background: brand, color: btnInk }">开始学习</span>
        </div>

        <div class="pvw-stats">
          <div v-for="(s, i) in [[12, '今日任务'], [8, '已完成'], [96, '正确率']]" :key="i"
               class="pvw-stat" :style="{ backgroundColor: glassSoft }">
            <b :style="{ color: text.primary }">{{ s[0] }}{{ i === 2 ? '%' : '' }}</b>
            <i :style="{ color: text.muted }">{{ s[1] }}</i>
          </div>
        </div>

        <div class="pvw-card2" :style="{ backgroundColor: cardBg }">
          <div class="pvw-row">
            <span class="pvw-t" :style="{ color: text.primary }">定语从句专项 · 任务 3</span>
            <span class="pvw-tag" :style="{ background: brandSoft, color: link, borderColor: brandBorder }">中等</span>
          </div>
          <div class="pvw-row">
            <span :style="{ color: text.secondary }">已完成 8 / 10 题</span>
            <span :style="{ color: text.muted }">剩 25 分钟</span>
          </div>
          <div class="pvw-bar"><i :style="{ width: '80%', background: brand }"></i></div>
          <div class="pvw-row">
            <span :style="{ color: text.secondary }">错题 2 · 有知识点薄弱</span>
            <span class="pvw-link2" :style="{ color: link }">查看讲解 →</span>
          </div>
        </div>

        <div class="pvw-inputrow">
          <span class="pvw-input" :style="{ backgroundColor: glassSoft, color: text.muted }">给小基提问…</span>
          <span class="pvw-send" :style="{ background: brand, color: btnInk }">发送</span>
        </div>
        <div class="pvw-foot">
          <span :style="{ color: text.muted }">更新于 2 分钟前</span>
          <span :style="{ color: link }">学习报告</span>
          <span :style="{ color: text.muted }">·</span>
          <span :style="{ color: link }">个人中心</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { withAlpha, mixColor, luminance } from '@/stores/theme'

const props = defineProps({
  bg: { type: String, required: true },        // 背景色 hex（无 #）
  surface: { type: String, required: true },   // 组件色 hex
  brand: { type: String, required: true },     // 主题色 hex
  text: { type: Object, required: true },      // { primary, secondary, muted }
})

const dark = computed(() => luminance(props.bg) <= 0.5)

// 毛玻璃卡片底色：组件色按明暗透明度（与 themeStore 的 --card-bg 同公式）
const cardBg = computed(() => withAlpha(props.surface, dark.value ? 0.8 : 0.85))
// 主题色块上的可读字色（与 --brand-on 同口径）
const btnInk = computed(() => luminance(props.brand) > 0.5 ? '#1a1a2e' : '#ffffff')

const ghost = computed(() => withAlpha(props.surface, dark.value ? 0.3 : 0.45))
const glassSoft = computed(() => withAlpha(props.surface, dark.value ? 0.5 : 0.72))
const brandSoft = computed(() => withAlpha(props.brand, 0.16))
const brandBorder = computed(() => withAlpha(props.brand, 0.45))
const link = computed(() => mixColor(props.brand, '#ffffff', 0.5))

// 页面底色：与真实 App 同款氛围——底色 + 背景色上下明暗渐变（92% 混白 → 96% 混黑）
const stageBg = computed(() => {
  const b = props.bg
  return `linear-gradient(180deg, color-mix(in srgb, ${b} 92%, #ffffff) 0%, ${b} 45%, color-mix(in srgb, ${b} 96%, #000000) 100%)`
})
// 品牌双层径向微光（与 .app-container 同款 16%/9%）
const glow = computed(() =>
  `radial-gradient(60% 55% at 88% -12%, color-mix(in srgb, ${props.brand} 16%, transparent), transparent 62%), radial-gradient(50% 45% at 0% 110%, color-mix(in srgb, ${props.brand} 9%, transparent), transparent 60%)`)

const today = new Date().toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit', weekday: 'short' }).replace(/\//g, '-')
</script>

<style scoped>
.pvw-window {
  margin: 10px 0 8px;
  border-radius: 12px; overflow: hidden;
  border: 1px solid rgba(128,128,128,.2);
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
}
.pvw-titlebar {
  display: flex; align-items: center; gap: 10px;
  padding: 7px 12px; font-size: 11px; color: var(--text-muted);
  border-bottom: 1px solid rgba(128,128,128,.12);
  background: rgba(128,128,128,.08);
}
.pvw-dots { display: inline-flex; gap: 5px; }
.pvw-dots i { width: 9px; height: 9px; border-radius: 50%; background: rgba(128,128,128,.42); }

.pvw-stage {
  position: relative; display: flex; gap: 10px;
  height: 300px; padding: 12px;
}
.pvw-glow { position: absolute; inset: 0; pointer-events: none; }

.pvw-side {
  position: relative; z-index: 1;
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  width: 46px; padding: 10px 0;
  border-radius: 12px; border: 1px solid rgba(128,128,128,.16);
  backdrop-filter: blur(8px);
}
.pvw-logo {
  display: flex; align-items: center; justify-content: center;
  width: 30px; height: 30px; border-radius: 9px;
  font-size: 14px; font-weight: 700; font-style: normal;
  box-shadow: 0 2px 10px rgba(0,0,0,.18);
}
.pvw-nav {
  display: flex; align-items: center; justify-content: center;
  width: 30px; height: 30px; border-radius: 9px;
  font-size: 10.5px; font-style: normal;
  border: 1px solid transparent;
}
.pvw-nav.on { font-weight: 600; }

.pvw-main {
  position: relative; z-index: 1; flex: 1; min-width: 0;
  display: flex; flex-direction: column; gap: 8px;
}
.pvw-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.pvw-htitle { font-size: 15px; font-weight: 700; }
.pvw-hsub { font-size: 10px; margin-top: 2px; }
.pvw-hbtn {
  flex: none; padding: 5px 12px; border-radius: 999px;
  font-size: 11.5px; font-weight: 600;
  box-shadow: 0 2px 10px rgba(0,0,0,.2);
}
.pvw-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.pvw-stat {
  display: flex; flex-direction: column; gap: 2px;
  padding: 8px 10px; border-radius: 10px;
  border: 1px solid rgba(128,128,128,.16);
  backdrop-filter: blur(8px);
}
.pvw-stat b { font-size: 15px; font-weight: 700; font-style: normal; }
.pvw-stat i { font-size: 9.5px; font-style: normal; }
.pvw-card2 {
  display: flex; flex-direction: column; gap: 6px;
  padding: 10px 12px; border-radius: 12px;
  border: 1px solid rgba(128,128,128,.18);
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 16px rgba(0,0,0,.12);
}
.pvw-row { display: flex; align-items: center; justify-content: space-between; gap: 8px; font-size: 11px; }
.pvw-t { font-weight: 600; }
.pvw-tag {
  flex: none; padding: 1px 8px; border-radius: 999px;
  font-size: 9.5px; border: 1px solid transparent;
}
.pvw-bar { height: 5px; border-radius: 3px; background: rgba(128,128,128,.22); overflow: hidden; }
.pvw-bar i { display: block; height: 100%; border-radius: 3px; transition: width .3s ease; }
.pvw-link2 { font-size: 11px; font-weight: 600; }
.pvw-inputrow { display: flex; align-items: center; gap: 8px; }
.pvw-input {
  flex: 1; padding: 6px 10px; border-radius: 999px;
  font-size: 10.5px; border: 1px solid rgba(128,128,128,.16);
  backdrop-filter: blur(8px);
}
.pvw-send {
  flex: none; padding: 5px 12px; border-radius: 999px;
  font-size: 11px; font-weight: 600;
  box-shadow: 0 2px 8px rgba(0,0,0,.18);
}
.pvw-foot { display: flex; gap: 8px; font-size: 9.5px; }

/* 窄屏：侧栏让位，主内容全宽 */
@media (max-width: 520px) {
  .pvw-side { display: none; }
  .pvw-stage { height: auto; min-height: 260px; }
}
</style>