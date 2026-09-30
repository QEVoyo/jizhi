<template>
  <div class="sc-wrap">
    <p class="sc-hint">
      点「改」后按下想用的组合键即可。设置**跟随账号**，换设备也在。
    </p>

    <div v-for="g in groups" :key="g.name" class="sc-group">
      <div class="sc-group-title">{{ g.name }}</div>
      <div class="sc-list">
        <div v-for="item in g.items" :key="item.id" class="sc-row">
          <div class="sc-info">
            <span class="sc-label">{{ item.label }}</span>
            <span class="sc-desc">{{ item.desc }}</span>
          </div>

          <!-- 录制态：显示提示 + 取消 -->
          <template v-if="recording === item.id">
            <span class="sc-recording">请按下组合键…</span>
            <button class="sc-btn" @click="stopRecording">取消</button>
          </template>

          <template v-else>
            <kbd class="sc-key" :class="{ changed: item.changed }">{{ formatCombo(item.combo) }}</kbd>
            <button class="sc-btn" @click="startRecording(item.id)">改</button>
            <button
              v-if="item.changed"
              class="sc-btn ghost"
              title="恢复这个动作的默认键"
              @click="onResetOne(item.id)"
            >恢复默认</button>
          </template>
        </div>
      </div>
    </div>

    <div class="sc-footer">
      <button class="sc-btn ghost" @click="onResetAll">全部恢复默认</button>
      <span v-if="state.syncing" class="sc-sync">正在同步…</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { shortcutState, bindingsForDisplay, setBinding, resetOne, resetAll } from './store'
import { comboFromEvent, formatCombo, isBareKey } from './combo'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const state = shortcutState

/** 正在录制的动作 id；空串 = 没在录 */
const recording = ref('')

const groups = computed(() => {
  const out = []
  for (const item of bindingsForDisplay()) {
    let g = out.find((x) => x.name === item.group)
    if (!g) { g = { name: item.group, items: [] }; out.push(g) }
    g.items.push(item)
  }
  return out
})

function startRecording(id) {
  recording.value = id
}

function stopRecording() {
  recording.value = ''
}

/**
 * 录制：捕获下一个组合键。
 *
 * ⚠️ 用**捕获阶段 + stopPropagation**，否则刚录的键会立刻被分发器执行一遍
 * （用户想绑 Ctrl+K，结果当场弹出了搜索面板）。
 */
function onKeydown(e) {
  if (!recording.value) return
  e.preventDefault()
  e.stopPropagation()

  // Esc 单独处理成「取消录制」，不当作一个可绑的键 —— 它在各种面板里都要用
  if (e.key === 'Escape') { stopRecording(); return }

  const combo = comboFromEvent(e)
  if (!combo) return   // 只按了修饰键，继续等

  if (isBareKey(combo)) {
    // 裸键（无修饰）做全局快捷键极易误触：在输入框里打字就会触发。
    // 不硬禁，但要用户确认一次。
    ElMessageBox.confirm(
      `「${formatCombo(combo)}」没有修饰键，任何地方按下都会触发（包括在输入框里打字时）。确定要用吗？`,
      '确认使用裸键',
      { confirmButtonText: '用', cancelButtonText: '换一个', type: 'warning' }
    ).then(() => commit(combo)).catch(() => {})
    return
  }
  commit(combo)
}

function commit(combo) {
  const id = recording.value
  const res = setBinding(id, combo, { userId: authStore.user?.id || '' })
  if (!res.ok) {
    // **冲突不静默覆盖** —— 说清撞了谁，让用户自己决定
    ElMessage.warning(`「${formatCombo(combo)}」已被「${res.conflictWith.label}」占用，请换一个`)
    return
  }
  stopRecording()
  ElMessage.success(`已设为 ${formatCombo(combo)}`)
}

function onResetOne(id) {
  resetOne(id, { userId: authStore.user?.id || '' })
  ElMessage.success('已恢复默认')
}

function onResetAll() {
  ElMessageBox.confirm('所有快捷键都会回到默认值，确定吗？', '恢复默认', {
    confirmButtonText: '恢复', cancelButtonText: '取消', type: 'warning',
  }).then(() => {
    resetAll({ userId: authStore.user?.id || '' })
    ElMessage.success('已全部恢复默认')
  }).catch(() => {})
}

onMounted(() => window.addEventListener('keydown', onKeydown, true))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown, true)
  // 组件卸载时别把录制态留在全局
  recording.value = ''
})
</script>

<style scoped>
.sc-wrap { display: flex; flex-direction: column; }
.sc-hint { font-size: 12px; color: var(--text-muted); margin: 0 0 14px; line-height: 1.6; }

.sc-group { margin-bottom: 16px; }
.sc-group-title {
  font-size: 12px; color: var(--text-muted); letter-spacing: 1px;
  margin-bottom: 8px; padding-left: 2px;
}
.sc-list { display: flex; flex-direction: column; gap: 6px; }

.sc-row {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 12px; border-radius: 10px;
  background: var(--input-bg); border: 1px solid var(--border-color);
}
.sc-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.sc-label { font-size: 14px; color: var(--text-primary); }
.sc-desc { font-size: 12px; color: var(--text-muted); }

.sc-key {
  font-family: Consolas, Monaco, monospace; font-size: 12px;
  padding: 4px 9px; border-radius: 6px; white-space: nowrap;
  background: var(--card-bg); border: 1px solid var(--border-color);
  color: var(--text-secondary);
}
.sc-key.changed { color: var(--brand); border-color: var(--brand); }

.sc-recording {
  font-size: 12px; color: var(--brand);
  animation: sc-pulse 1.2s ease-in-out infinite;
}
@keyframes sc-pulse { 0%,100% { opacity: .45 } 50% { opacity: 1 } }

.sc-btn {
  font-size: 12px; padding: 4px 11px; border-radius: 8px; cursor: pointer;
  background: transparent; color: var(--text-secondary);
  border: 1px solid var(--border-color);
  transition: all .15s ease;
}
.sc-btn:hover { border-color: var(--brand); color: var(--brand); }
.sc-btn.ghost { color: var(--text-muted); }

.sc-footer {
  display: flex; align-items: center; gap: 12px;
  margin-top: 4px; padding-top: 14px;
  border-top: 1px solid var(--border-color);
}
.sc-sync { font-size: 12px; color: var(--text-muted); }
</style>
