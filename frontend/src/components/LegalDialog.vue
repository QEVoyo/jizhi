<template>
  <el-dialog
    :model-value="modelValue"
    title=""
    width="min(760px, 92vw)"
    top="5vh"
    class="legal-dialog"
    append-to-body
    destroy-on-close
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <div class="legal-dialog-body">
      <LegalContent :doc="doc" compact />
    </div>
    <template #footer>
      <div class="legal-dialog-footer">
        <span class="legal-dialog-tip">继续使用前，请确认你已阅读并同意</span>
        <div class="legal-dialog-actions">
          <el-button @click="close">关闭</el-button>
          <el-button v-if="showAgree" type="primary" @click="agree">我已阅读并同意</el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'
import LegalContent from '@/components/LegalContent.vue'
import { LEGAL_DOCS, SERVICE_AGREEMENT } from '@/utils/legalDocs'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  type: { type: String, default: 'service' },
  showAgree: { type: Boolean, default: true },
})
const emit = defineEmits(['update:modelValue', 'agree'])

const doc = computed(() => LEGAL_DOCS[props.type] || SERVICE_AGREEMENT)

function close() {
  emit('update:modelValue', false)
}
function agree() {
  emit('agree')
  close()
}
</script>

<style scoped>
.legal-dialog-body {
  max-height: 68vh;
  overflow-y: auto;
  padding: 2px 10px 0 2px;
  scrollbar-width: thin;
}
.legal-dialog-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}
.legal-dialog-tip {
  font-size: 12px;
  color: var(--text-muted);
}
.legal-dialog-actions { display: flex; gap: 8px; }
</style>

<!-- 弹窗会被 teleport 到 body，scoped 样式够不到，单独写全局样式 -->
<style>
.legal-dialog.el-dialog {
  background: var(--surface, #fff);
  border: 1px solid var(--line-soft, rgba(128, 128, 128, .14));
  border-radius: 18px;
  box-shadow: 0 24px 80px rgba(0, 0, 0, .22);
  padding: 0;
  overflow: hidden;
}
.legal-dialog .el-dialog__header {
  padding: 18px 24px 0;
  margin-right: 0;
}
.legal-dialog .el-dialog__headerbtn { top: 14px; right: 14px; }
.legal-dialog .el-dialog__body { padding: 14px 24px 0; }
.legal-dialog .el-dialog__footer {
  padding: 14px 24px 18px;
  border-top: 1px solid var(--line-soft, rgba(128, 128, 128, .12));
}
.legal-dialog .el-button--primary {
  --el-button-bg-color: var(--brand, #3556d8);
  --el-button-border-color: var(--brand, #3556d8);
  --el-button-hover-bg-color: color-mix(in srgb, var(--brand, #3556d8) 82%, #000);
  --el-button-hover-border-color: color-mix(in srgb, var(--brand, #3556d8) 82%, #000);
}
</style>
