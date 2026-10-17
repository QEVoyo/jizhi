<template>
  <article class="legal-doc" :class="{ compact }">
    <header class="legal-head">
      <span class="legal-kicker">基智 · 法律文件</span>
      <h1>{{ doc.title }}</h1>
      <div class="legal-meta">
        <span>更新日期：{{ doc.updated }}</span>
        <span>生效日期：{{ doc.effective }}</span>
        <span>版本：{{ LEGAL_VERSION }}</span>
      </div>
    </header>

    <div v-if="doc.lead" class="legal-lead">{{ doc.lead }}</div>

    <section
      v-for="(sec, i) in doc.sections"
      :id="'legal-sec-' + i"
      :key="i"
      class="legal-section"
    >
      <h2>{{ sec.h }}</h2>
      <template v-for="(it, j) in sec.items" :key="j">
        <p v-if="it.li" class="legal-li">{{ it.t }}</p>
        <p v-else-if="it.b" class="legal-p legal-strong">{{ it.t }}</p>
        <p v-else class="legal-p">{{ it.t }}</p>
      </template>
    </section>

    <footer class="legal-foot">— 全文完 —</footer>
  </article>
</template>

<script setup>
import { LEGAL_VERSION } from '@/utils/legalDocs'

defineProps({
  doc: { type: Object, required: true },
  compact: { type: Boolean, default: false },
})
</script>

<style scoped>
.legal-doc {
  color: var(--text-primary);
  font-size: 14.5px;
  line-height: 1.95;
}

/* ===== 头部 ===== */
.legal-head {
  padding-bottom: 22px;
  border-bottom: 1px solid var(--line-soft, rgba(128, 128, 128, .14));
  margin-bottom: 22px;
}
.legal-kicker {
  display: inline-block;
  font-size: 11px;
  letter-spacing: 2px;
  color: var(--brand);
  font-weight: 600;
  margin-bottom: 10px;
  opacity: .85;
}
.legal-head h1 {
  margin: 0;
  font-size: 30px;
  line-height: 1.3;
  font-weight: 750;
  letter-spacing: .5px;
}
.legal-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 18px;
  margin-top: 12px;
  font-size: 12.5px;
  color: var(--text-muted);
}

/* ===== 导语 ===== */
.legal-lead {
  margin: 0 0 26px;
  padding: 18px 20px;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--brand) 18%, transparent);
  background: color-mix(in srgb, var(--brand) 7%, transparent);
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.9;
  text-align: justify;
}

/* ===== 正文 ===== */
.legal-section { margin-bottom: 24px; scroll-margin-top: 90px; }
.legal-section h2 {
  margin: 0 0 12px;
  padding-left: 12px;
  position: relative;
  font-size: 17.5px;
  line-height: 1.5;
  font-weight: 700;
  color: var(--text-primary);
}
.legal-section h2::before {
  content: '';
  position: absolute;
  left: 0;
  top: .22em;
  bottom: .22em;
  width: 3px;
  border-radius: 2px;
  background: var(--brand);
}
.legal-p {
  margin: 0 0 9px;
  color: var(--text-secondary);
  text-align: justify;
  text-justify: inter-ideograph;
}
.legal-strong {
  color: var(--text-primary);
  font-weight: 600;
}
.legal-li {
  position: relative;
  margin: 0 0 7px;
  padding-left: 16px;
  color: var(--text-secondary);
  text-align: justify;
  text-justify: inter-ideograph;
}
.legal-li::before {
  content: '';
  position: absolute;
  left: 2px;
  top: .82em;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: color-mix(in srgb, var(--brand) 55%, transparent);
}

.legal-foot {
  margin-top: 34px;
  padding-top: 18px;
  border-top: 1px dashed var(--line-soft, rgba(128, 128, 128, .14));
  text-align: center;
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 1px;
}

/* ===== 弹窗里的紧凑版 ===== */
.compact { font-size: 13.5px; line-height: 1.85; }
.compact .legal-head h1 { font-size: 24px; }
.compact .legal-head { padding-bottom: 16px; margin-bottom: 16px; }
.compact .legal-lead { margin-bottom: 18px; padding: 14px 16px; font-size: 13px; }
.compact .legal-section { margin-bottom: 18px; }
.compact .legal-section h2 { font-size: 16px; margin-bottom: 9px; }

@media (max-width: 720px) {
  .legal-doc { font-size: 14px; }
  .legal-head h1 { font-size: 24px; }
  .legal-section h2 { font-size: 16px; }
  .legal-lead { padding: 14px 16px; }
}
</style>
