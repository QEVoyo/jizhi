<template>
  <!--
    骨架屏（2026-10-30）：用灰块占位代替转圈，页面看起来"已经开了"。
    三种形态：
      list     —— 社区动态 / 列表卡片
      cards    —— 资源库掌握度 / 横排卡片
      question —— 做题页（题干 + 选项）
  -->
  <div class="sk-wrap" :class="`sk-${variant}`" aria-busy="true" aria-live="polite">
    <template v-if="variant === 'list'">
      <div v-for="i in count" :key="i" class="sk-post">
        <div class="sk-head">
          <span class="sk-circle"></span>
          <span class="sk-head-lines">
            <i class="sk-line w30"></i>
            <i class="sk-line w18"></i>
          </span>
        </div>
        <i class="sk-line w85"></i>
        <i class="sk-line w70"></i>
        <i class="sk-line w40"></i>
        <div class="sk-media"></div>
        <div class="sk-foot">
          <i class="sk-pill w14"></i>
          <i class="sk-pill w14"></i>
          <i class="sk-pill w14"></i>
        </div>
      </div>
    </template>

    <template v-else-if="variant === 'cards'">
      <div class="sk-cards">
        <div v-for="i in count" :key="i" class="sk-card">
          <i class="sk-line w55"></i>
          <i class="sk-line w30"></i>
        </div>
      </div>
    </template>

    <template v-else>
      <div class="sk-question">
        <i class="sk-line w20"></i>
        <i class="sk-line w90"></i>
        <i class="sk-line w75"></i>
        <div class="sk-options">
          <i v-for="i in 4" :key="i" class="sk-option"></i>
        </div>
        <div class="sk-foot">
          <i class="sk-pill w18"></i>
          <i class="sk-pill w14"></i>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
defineProps({
  variant: { type: String, default: 'list' }, // list | cards | question
  count: { type: Number, default: 3 },
})
</script>

<style scoped>
.sk-wrap { width: 100%; }

.sk-line,
.sk-circle,
.sk-media,
.sk-card,
.sk-option,
.sk-pill {
  display: block;
  border-radius: 8px;
  background: linear-gradient(
    90deg,
    rgba(128, 128, 128, .08) 25%,
    rgba(128, 128, 128, .17) 37%,
    rgba(128, 128, 128, .08) 63%
  );
  background-size: 400% 100%;
  animation: sk-shimmer 1.25s ease infinite;
}

@keyframes sk-shimmer {
  0% { background-position: 100% 50%; }
  100% { background-position: 0 50%; }
}

@media (prefers-reduced-motion: reduce) {
  .sk-line, .sk-circle, .sk-media, .sk-card, .sk-option, .sk-pill {
    animation: none;
  }
}

.w14 { width: 14%; }
.w18 { width: 18%; }
.w20 { width: 20%; }
.w30 { width: 30%; }
.w40 { width: 40%; }
.w55 { width: 55%; }
.w70 { width: 70%; }
.w75 { width: 75%; }
.w85 { width: 85%; }
.w90 { width: 90%; }

.sk-line { height: 12px; margin: 8px 0; }
.sk-circle { width: 38px; height: 38px; border-radius: 50%; flex-shrink: 0; }

/* ===== list ===== */
.sk-post {
  border: 1px solid rgba(128, 128, 128, .12);
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 12px;
}
.sk-head { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.sk-head-lines { flex: 1; }
.sk-head-lines .sk-line { margin: 4px 0; }
.sk-media { height: 120px; border-radius: 12px; margin-top: 10px; }
.sk-foot { display: flex; gap: 10px; margin-top: 12px; }
.sk-pill { height: 22px; width: 18%; border-radius: 11px; }

/* ===== cards ===== */
.sk-cards { display: flex; gap: 12px; flex-wrap: wrap; }
.sk-card {
  flex: 1 1 150px;
  min-height: 86px;
  padding: 16px;
  border-radius: 16px;
}
.sk-card .sk-line { margin: 10px 0; }

/* ===== question ===== */
.sk-question {
  border: 1px solid rgba(128, 128, 128, .12);
  border-radius: 18px;
  padding: 24px;
  margin: 24px auto;
  max-width: 820px;
}
.sk-options { display: flex; flex-direction: column; gap: 10px; margin-top: 18px; }
.sk-option { height: 46px; border-radius: 12px; }
</style>
