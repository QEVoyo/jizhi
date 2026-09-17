<template>
  <div class="edge-dock" :style="dockStyle">
    <!-- 双轨线（2026-08-27 用户拍板：80px 粗带掏空中间 64px 图标槽，留两侧各 8px 边线，图标在双轨间滑动） -->
    <canvas ref="railRef" class="dock-rail"></canvas>
    <!-- ===== 中枢（固定内容竖排：Logo + 用户完整信息 + 搜索，置于圆心右侧完整可见） ===== -->
    <div class="dock-hub" :style="hubStyle">
      <!-- 顶部行（2026-08-26 用户拍板：上箭头在左、logo 在右，整体靠左收） -->
      <div class="hub-top-row">
        <button class="dock-arrow up" @click="rotate(1)" title="向前转">
          <i class="fas fa-chevron-up"></i>
        </button>
        <img src="/logo.png" alt="基智" class="hub-logo" />
      </div>
      <div class="hub-user" @click="$router.push('/profile')" title="个人中心">
        <el-avatar :size="54" :src="authStore.user?.avatar_url || ''">
          {{ authStore.user?.nickname?.[0] || 'U' }}
        </el-avatar>
        <div class="hub-user-col">
          <div class="hub-nick-row">
            <span class="hub-nickname">{{ authStore.user?.nickname || '用户' }}</span>
            <span v-if="rankName" class="hub-rank">{{ rankName }}</span>
          </div>
          <span class="hub-account">{{ authStore.user?.user_account || '—' }}</span>
          <span class="hub-grade">
            {{ [authStore.user?.grade, authStore.user?.major].filter(Boolean).join(' · ') || '未设置年级专业' }}
          </span>
        </div>
      </div>
      <!-- 中枢时钟（2026-08-26：实时时间，用户信息下方——不抬高中枢顶部，避开 -45° 轨道图标） -->
      <div class="hub-clock">
        <div class="hub-clock-time">{{ clockTime }}</div>
        <div class="hub-clock-date">{{ clockDate }}</div>
      </div>
      <div class="hub-search" @click="navStore.openSearch()">
        <i class="fas fa-search"></i>
        <span>搜索…</span>
        <span class="hub-kbd">Ctrl K</span>
      </div>

      <!-- 底部 4 键：2×2 磁贴铺满（2026-08-26 从轨道移入中枢） -->
      <div class="hub-actions">
        <button class="hub-action" @click="showFeedback = true">
          <i class="fas fa-envelope"></i><span>意见反馈</span>
        </button>
        <button class="hub-action" @click="$router.push('/guide')">
          <i class="fas fa-compass"></i><span>使用指引</span>
        </button>
        <button class="hub-action" @click="$router.push('/open-source')">
          <i class="fas fa-book-open"></i><span>开源文档</span>
        </button>
        <button class="hub-action logout" @click="handleLogout">
          <i class="fas fa-right-from-bracket"></i><span>退出登录</span>
        </button>
      </div>
      <!-- 落款（2026-08-26：canvas 手写毛笔行书，飞白笔触 + 渐变蓝） -->
      <div class="hub-name-wrap">
        <canvas ref="calligraphyRef" class="hub-name-art"></canvas>
      </div>
      <button class="dock-arrow down" @click="rotate(-1)" title="向后转">
        <i class="fas fa-chevron-down"></i>
      </button>
    </div>

    <!-- ===== 意见反馈弹窗（原侧边栏同款 el-dialog） ===== -->
    <el-dialog
      v-model="showFeedback"
      title="📬 意见反馈"
      width="420px"
      :append-to-body="true"
      :modal="false"
      class="feedback-dialog-wrapper"
      destroy-on-close
    >
      <div class="feedback-dialog">
        <p class="feedback-tip">感谢你的反馈，我们会认真对待每一条建议 💪</p>
        <el-form>
          <el-form-item>
            <div class="custom-select" @click.stop="feedbackMenuVisible = !feedbackMenuVisible">
              <span class="select-display">{{ feedbackTypeLabel }}</span>
              <i class="fas fa-chevron-down select-arrow" :class="{ rotated: feedbackMenuVisible }"></i>
            </div>
            <div v-if="feedbackMenuVisible" class="custom-select-dropdown" @click.stop>
              <div
                v-for="opt in feedbackOptions"
                :key="opt.value"
                class="select-option"
                :class="{ active: feedbackType === opt.value }"
                @click="selectFeedbackType(opt.value)"
              >
                {{ opt.label }}
              </div>
            </div>
          </el-form-item>
          <el-form-item>
            <el-input
              v-model="feedbackContent"
              type="textarea"
              :rows="4"
              placeholder="请详细描述你的想法或遇到的问题..."
              maxlength="1000"
              show-word-limit
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showFeedback = false">取消</el-button>
        <el-button type="primary" :loading="feedbackSubmitting" @click="submitFeedback">
          <i class="fas fa-paper-plane"></i> 提交
        </el-button>
      </template>
    </el-dialog>

    <!-- ===== 半椭圆轨道图标（可视窗口 9 个，左半被屏幕边缘裁掉） ===== -->
    <div
      v-for="(item, j) in wheelItems"
      :key="item.key"
      v-show="isVisible(j)"
      class="dock-icon"
      :class="{ active: item.active }"
      :style="iconStyle(j)"
      :title="item.label"
      @click="onItemClick(item)"
    >
      <img :src="iconPath(item.icon)" :alt="item.label" class="dock-icon-img" />
      <span v-if="isFront(j)" class="dock-icon-label">{{ item.label }}</span>
    </div>

    <ToolPanel ref="toolPanelRef" />
  </div>
</template>

<script setup>
// ===== 边缘半椭圆中枢轮盘（2026-08-26 修订）=====
// 椭圆圆心贴屏幕左缘：整个左半弧被屏幕边缘裁掉（真·嵌入边边），只有右半弧可见；
// 小基独立固定在屏幕正中间；中枢卡片放圆心右侧完整可见；旋转无回弹动画（平滑缓动）
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { useNavStore } from '@/stores/nav'
import { getUserStats } from '@/api/career'
import ToolPanel from '@/components/ToolPanel.vue'

const props = defineProps({
  hidden: { type: Boolean, default: false },   // 纯净模式隐藏：停用全局滚轮旋转
})

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const themeStore = useThemeStore()
const navStore = useNavStore()

const toolPanelRef = ref(null)
let onGlobalWheel = null   // 全局滚轮监听（挂载/卸载时管理）

// 中枢用户段位（学程数据，展示用）
const rankName = ref('')

// ===== 中枢时钟（2026-08-26：实时当前时间，秒针每秒刷新） =====
const nowTick = ref(Date.now())
let clockTimer = null
const clockTime = computed(() => {
  const d = new Date(nowTick.value)
  const pad = n => String(n).padStart(2, '0')
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
})
const WEEK = ['日', '一', '二', '三', '四', '五', '六']
const clockDate = computed(() => {
  const d = new Date(nowTick.value)
  return `${d.getMonth() + 1}月${d.getDate()}日 周${WEEK[d.getDay()]}`
})

// ===== 「基智」canvas 手写行书（2026-08-26：矢量渐变，无噪点干净笔画） =====
const calligraphyRef = ref(null)
function drawCalligraphy() {
  const canvas = calligraphyRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const text = '基智'
  const scale = 2
  const fs = 36          // 字号（2026-08-27：60→36 缩小）
  const slot = 44        // 字槽
  const padX = 10, padY = 8
  const W_logical = padX * 2 + slot * text.length
  const H_logical = padY + Math.ceil(fs * 1.2) + padY
  canvas.width = W_logical * scale
  canvas.height = H_logical * scale
  ctx.scale(scale, scale)
  // 纯字无底片（2026-08-30 用户拍板：不用卡片，改回蓝色字）
  ctx.font = `400 ${fs}px 'STXingkai', '华文行楷', 'KaiTi', '楷体', cursive`   // 2026-08-27：700→400 笔画变细
  ctx.textAlign = 'center'
  ctx.textBaseline = 'alphabetic'
  // 字色：渐变蓝（08-26 用户拍板同款 #9cc4ff→#4d8dff→#2f6fe0）
  const grad = ctx.createLinearGradient(padX, 0, W_logical - padX, 0)
  grad.addColorStop(0, '#9cc4ff')
  grad.addColorStop(0.5, '#4d8dff')
  grad.addColorStop(1, '#2f6fe0')
  ctx.fillStyle = grad
  for (let i = 0; i < text.length; i++) {
    ctx.fillText(text[i], padX + slot * i + slot / 2, padY + fs * 0.9)
  }
  canvas.style.width = W_logical + 'px'
  canvas.style.height = H_logical + 'px'
}
// 主题切换时重绘（双轨线配色随主题；艺术字为纯蓝字双主题通用）
// ===== 双轨线：椭圆两侧各一条 8px 边线，中间 64px 槽空置嵌图标（canvas，2026-08-27 用户拍板） =====
const railRef = ref(null)
function drawRail() {
  const canvas = railRef.value
  if (!canvas) return
  const scale = 2
  const bleed = 64                         // 出血区：半带宽 40 + 辉光，双轨不被画布裁断
  canvas.width = (584 + bleed) * scale
  canvas.height = (700 + bleed * 2) * scale
  const ctx = canvas.getContext('2d')
  ctx.setTransform(scale, 0, 0, scale, 0, 0)
  ctx.clearRect(0, 0, 584 + bleed, 700 + bleed * 2)

  const light = themeStore.currentTheme === 'light'
  // 蓝灰方案（2026-08-27 用户拍板）：深色主题亮蓝灰、浅色主题深蓝灰，自动适配
  const color = light ? 'rgba(96, 106, 168, .36)' : 'rgba(176, 190, 255, .38)'
  ctx.strokeStyle = color
  ctx.lineWidth = 8                       // 边线宽 8px
  ctx.lineCap = 'round'
  ctx.shadowColor = color
  ctx.shadowBlur = light ? 12 : 14
  // 内/外两条同心椭圆边线：错开 ±36px，中间恰留 64px 空槽（图标 64px 骑槽滑动）
  for (const k of [36, -36]) {
    ctx.beginPath()
    // 椭圆中心随出血区上移 bleed：容器坐标 (272, 350) 平移为 (272, 350+64)
    ctx.ellipse(272, 350 + bleed, 272 + k, 350 + k, 0, -Math.PI / 2, Math.PI / 2)
    ctx.stroke()
  }
  ctx.shadowBlur = 0
}

watch(() => themeStore.currentTheme, () => { drawCalligraphy(); drawRail() })

// ===== 几何：竖椭圆（RY > RX），圆心在屏幕左缘（固定尺寸，不随窗口变化） =====
const RX = 272          // 椭圆横半轴（2026-08-27：240→272 轴距扩大，图标与中枢拉开距离）
const RY = 350          // 椭圆纵半轴（2026-08-27：330→350）
const HUB_OFFSET = 95   // 中枢中心距屏幕左缘（2026-08-26：左移贴边，宽 188 撑满 0..189，不压轨道图标）
const VISIBLE = 9       // 可视窗口：一次最多展示 9 个图标
const FRONT_SLOT = Math.floor(VISIBLE / 2)   // 窗口正中间 = 正前方（0°）

// 导航 + 工具
const NAV_ITEMS = [
  { to: '/home', icon: 'xiaoji.png', label: '小基', key: 'home' },
  { to: '/profile', icon: 'profile.png', label: '个人中心', key: 'profile' },
  { to: '/settings', icon: 'settings.png', label: '设置', key: 'settings' },
  { to: '/resource-lib', icon: 'resource-lib.png', label: '资源库', key: 'resource-lib' },
  { to: '/evaluation-center', icon: 'evaluation.png', label: '评估中心', key: 'evaluation-center' },
  { to: '/career', icon: 'career.png', label: '学程', key: 'career' },
  { to: '/profile-card', icon: 'profile-card.png', label: '个人画像', key: 'profile-card' },
  { to: '/subject-plan', icon: 'subject-plan.png', label: '学科计划', key: 'subject-plan' },
  { to: '/video-square', icon: 'video-library.png', label: '视频库', key: 'video-square' },
  { to: '/community', icon: 'community.png', label: '社区', key: 'community' },
  { to: '/qa', icon: 'qa.png', label: 'Q&A', key: 'qa' },
  { to: '/message', icon: 'messages.png', label: '消息中心', key: 'messages' },
  { to: '/agent-center', icon: 'agent-center.png', label: '智能体中心', key: 'agent-center' },
  { to: '/wordbook', icon: 'wordbook.png', label: '词条本', key: 'wordbook' },
  { to: '/api-center', icon: 'api-center.png', label: 'API管理', key: 'api-center' },
  { to: '', icon: 'checkin.png', label: '打卡', key: 'tool-checkin', tool: 'checkin' },
  { to: '', icon: 'countdown.png', label: '时间胶囊', key: 'tool-countdown', tool: 'countdown' },
  { to: '', icon: 'timer.png', label: '计时器', key: 'tool-timer', tool: 'timer' },
]
if (authStore.user?.role !== 'user') {
  NAV_ITEMS.push({ to: '/admin', icon: 'admin.png', label: '管理后台', key: 'admin' })
}

const wheelItems = computed(() =>
  NAV_ITEMS.map(item => ({
    ...item,
    active: item.to ? route.path.startsWith(item.to) : false,
  }))
)

// ===== 旋转状态（2026-08-27：RAF 连续旋转——图标逐帧落在椭圆参数点上，沿轨道线滑动不「发飘」） =====
const offset = ref(0)      // 整数目标偏移（前端高亮/卡片等展示逻辑按它算）
const viewOff = ref(0)     // 连续旋转位置（小数槽位），驱动图标沿椭圆逐帧滑动
let animRaf = null
const N = computed(() => wheelItems.value.length)

function fracSlot(j) {
  // 每个图标当前的小数槽位（0..VISIBLE-1 为可视窗口）
  const n = N.value
  return ((j - viewOff.value + FRONT_SLOT) % n + n) % n
}

// 连续角度：从小数槽位映射到 [-90°, 90°]，两端钳制防越出右半弧
function angleOf(j) {
  const s = fracSlot(j)
  if (s < -0.75 || s > VISIBLE - 0.25) return null
  const deg = -90 + (180 * s) / Math.max(1, VISIBLE - 1)
  return Math.max(-90, Math.min(90, deg))
}

function isVisible(j) {
  // 小数窗口判定：图标滑出两端才隐藏（避免整数切换时半途弹掉）
  const s = fracSlot(j)
  return s > -0.6 && s < VISIBLE - 1 + 0.6
}

// 容器坐标：椭圆圆心在 (RX, RY)（屏幕 x=0），图标只在右半弧（cos≥0）——逐帧都在椭圆线上
function iconStyle(j) {
  const deg = angleOf(j)
  if (deg === null) return { display: 'none' }
  const a = (deg * Math.PI) / 180
  const x = RX + RX * Math.cos(a)
  const y = RY + RY * Math.sin(a)
  const abs = Math.abs(a)
  const scale = 1 - 0.42 * (abs / (Math.PI / 2))
  const opacity = 1 - 0.55 * (abs / (Math.PI / 2))
  return {
    display: '',
    left: `${x}px`,
    top: `${y}px`,
    transform: `translate(-50%, -50%) scale(${scale})`,
    opacity,
    zIndex: Math.round((1 - abs / (Math.PI / 2)) * 10),
  }
}

function isFront(j) {
  const deg = angleOf(j)
  if (deg === null) return false
  return Math.abs((deg * Math.PI) / 180) < Math.PI / 12
}

function rotate(step) {
  offset.value = (offset.value + step + N.value) % N.value
  // 旋转变量的插值对象是「槽位」而非 left/top：每帧重算椭圆参数点，图标永远贴轨
  const from = viewOff.value
  let delta = offset.value - from
  const n = N.value
  delta = ((delta % n) + n) % n
  if (delta > n / 2) delta -= n               // 最短路径
  const t0 = performance.now()
  const dur = 380
  cancelAnimationFrame(animRaf)
  const tick = now => {
    const p = Math.min(1, (now - t0) / dur)
    const e = 1 - Math.pow(1 - p, 3)          // easeOutCubic
    viewOff.value = from + delta * e
    if (p < 1) animRaf = requestAnimationFrame(tick)
  }
  animRaf = requestAnimationFrame(tick)
}

function onItemClick(item) {
  if (item.tool) {
    toolPanelRef.value?.openTool(item.tool)
  } else if (item.to) {
    router.push(item.to)
  }
}

// ===== 退出登录（与其他入口一致：先确认再退出） =====
function handleLogout() {
  ElMessageBox.confirm('确定要退出登录吗？', '确认退出')
    .then(async () => {
      await authStore.logout()
      ElMessage.success('已退出')
      await new Promise(resolve => setTimeout(resolve, 100))
      router.push('/login')
    })
    .catch(() => {})
}

// ===== 意见反馈（原侧边栏同款弹窗逻辑） =====
const showFeedback = ref(false)
const feedbackType = ref('suggestion')
const feedbackContent = ref('')
const feedbackSubmitting = ref(false)
const feedbackMenuVisible = ref(false)
const feedbackOptions = [
  { value: 'suggestion', label: '💡 功能建议' },
  { value: 'bug', label: '🐛 问题反馈' },
  { value: 'feature', label: '✨ 功能请求' },
  { value: 'other', label: '📝 其他' }
]
const feedbackTypeLabel = computed(() => {
  const found = feedbackOptions.find(o => o.value === feedbackType.value)
  return found ? found.label : '选择反馈类型'
})
function selectFeedbackType(value) {
  feedbackType.value = value
  feedbackMenuVisible.value = false
}
async function submitFeedback() {
  if (!feedbackContent.value || feedbackContent.value.length < 10) {
    ElMessage.warning('内容至少10个字')
    return
  }
  if (!feedbackType.value) {
    ElMessage.warning('请选择反馈类型')
    return
  }
  feedbackSubmitting.value = true
  try {
    const res = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'}/feedback/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`
      },
      body: JSON.stringify({
        user_id: authStore.user.id,
        user_email: authStore.user.email,
        user_nickname: authStore.user.nickname,
        type: feedbackType.value,
        content: feedbackContent.value
      })
    })
    if (res.ok) {
      ElMessage.success('感谢反馈！🎉')
      showFeedback.value = false
      feedbackContent.value = ''
      feedbackType.value = 'suggestion'
    } else {
      ElMessage.error('提交失败，请稍后重试')
    }
  } catch {
    ElMessage.error('网络错误')
  } finally {
    feedbackSubmitting.value = false
  }
}

const dockStyle = computed(() => ({
  left: `-${RX}px`,                 // 圆心贴屏幕左缘
  width: `${RX + HUB_OFFSET + 130}px`,
  height: `${RY * 2}px`,
}))
const hubStyle = computed(() => ({
  left: `${RX + HUB_OFFSET}px`,
  top: `${RY - 20}px`,   // 2026-08-26：上移 50→20（顶部行 logo 与 -67.5° 轨道图标重叠，整体下移 30px）
}))

// 全局滚轮：页面任意空白处滚动都能转轮盘——同步注册（不等接口）。
// 从事件目标沿 DOM 向上逐个检查：任一祖先「确实可滚动」（overflow auto/scroll 且内容溢出）
// 就放行原生滚动（如右栏日志区的 .log-scroll / 通话记录 / 聊天列表），其余一律转轮盘
function onGlobalWheelHandler(e) {
  if (props.hidden) return   // 纯净模式隐藏中，不转也不拦截滚动
  let el = e.target
  while (el && el !== document.documentElement) {
    if (el.scrollHeight > el.clientHeight + 4) {
      const style = getComputedStyle(el)
      if (/auto|scroll|overlay/.test(style.overflowY) || /auto|scroll|overlay/.test(style.overflow)) return
    }
    el = el.parentElement
  }
  e.preventDefault()
  rotate(e.deltaY > 0 ? 1 : -1)
}

onMounted(() => {
  onGlobalWheel = onGlobalWheelHandler
  window.addEventListener('wheel', onGlobalWheel, { passive: false })
  clockTimer = setInterval(() => { nowTick.value = Date.now() }, 1000)
  drawCalligraphy()
  drawRail()
  // 段位信息异步加载，不阻塞滚轮注册
  if (authStore.user?.id) {
    getUserStats(authStore.user.id)
      .then(stats => { if (stats?.rank) rankName.value = stats.rank })
      .catch(() => {})
  }
})

onUnmounted(() => {
  if (onGlobalWheel) window.removeEventListener('wheel', onGlobalWheel)
  if (clockTimer) clearInterval(clockTimer)
})

const iconBase = '/assets/icons/sidebar/'
function iconPath(name) { return iconBase + name }
</script>

<style scoped>
/* 轨道粗线 canvas：四周外扩 64px 出血区（带厚 40 + 辉光 24），防止粗轨带上下端被裁断 */
.dock-rail {
  position: absolute;
  left: 0;
  top: -64px;
  width: 648px;
  height: 828px;
  pointer-events: none;
  z-index: 0;   /* 中枢/轨道图标都在其上 */
}
.edge-dock {
  position: fixed;
  top: 50%;
  transform: translateY(-50%);
  z-index: 60;
  pointer-events: none;   /* 容器不挡内容，子元素各自可点 */
}



/* ===== 中枢（无卡片：信息直接浮在椭圆内部；2026-08-26 宽 188 贴左缘撑满，右缘止于轨道图标前） ===== */
.dock-hub {
  position: absolute;
  transform: translate(-50%, -50%);
  width: 188px;
  display: flex;
  flex-direction: column;
  gap: 9px;
  pointer-events: auto;
  z-index: 30;
  text-shadow: 0 1px 8px rgba(0,0,0,.35);
}
.hub-top-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.hub-top-row .dock-arrow { align-self: center; }   /* 顶部行内箭头与 logo 垂直居中 */
.hub-logo {
  width: 68px;
  height: 68px;
  border-radius: 14px;
  object-fit: contain;
}
/* 落款（2026-08-26：canvas 自制手写行书，飞白笔触 + 渐变蓝） */
.hub-name-wrap {
  align-self: center;
  display: flex;
  justify-content: center;
}
.hub-name-art {
  display: block;
}
/* 中枢时钟（2026-08-26：圆心内实时时间，用户信息下方居中） */
.hub-clock {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
  padding: 1px 0;
}
.hub-clock-time {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 2px;
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
  color: var(--text-primary);
  text-shadow: 0 0 18px rgba(139, 92, 246, .5);
}
.hub-clock-date {
  font-size: 11px;
  letter-spacing: .5px;
  color: var(--text-muted);
}
.hub-user {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}
.hub-user-col {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}
.hub-nick-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.hub-nickname {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 110px;
}
.hub-rank {
  font-size: 10px;
  padding: 1px 7px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--brand) 12%, transparent);
  color: var(--brand-bright);
  white-space: nowrap;
}
.hub-account {
  font-size: 12px;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.hub-grade {
  font-size: 12px;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.hub-search {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent);
  border: 1px solid rgba(255,255,255,.07);
  font-size: 13px;
  color: var(--text-muted);
  cursor: pointer;
  transition: all .2s ease;
}
.hub-search:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 10%, transparent);
  color: var(--text-secondary);
}
.hub-kbd {
  margin-left: auto;
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  background: color-mix(in srgb, var(--surface, #ffffff) 8%, transparent);
}
/* 底部 4 键：2×2 磁贴铺满 */
.hub-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  pointer-events: auto;
}
.hub-action {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 11px 4px 10px;
  border: none;
  border-radius: 12px;
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent);
  color: var(--text-secondary);
  font-size: 11px;
  white-space: nowrap;
  cursor: pointer;
  transition: all .2s ease;
  pointer-events: auto;
}
.hub-action i {
  font-size: 15px;
  color: var(--text-muted);
  transition: color .2s ease;
}
.hub-action:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 12%, transparent);
  color: var(--text-primary);
  transform: translateY(-1px);
}
.hub-action:hover i { color: var(--text-primary); }
.hub-action.logout:hover {
  background: rgba(239,68,68,.14);
  color: #f87171;
}
.hub-action.logout:hover i { color: #f87171; }

/* ===== 轨道图标 ===== */
.dock-icon {
  position: absolute;
  width: 64px;   /* 2026-08-26：56→64 用户要求图标放大 */
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  /* 位置由 RAF 沿椭圆逐帧写入，不用 left/top CSS 过渡——直线过渡会让图标插值走弦线脱离椭圆轨道「发飘」（2026-08-27 修复） */
  pointer-events: auto;
}
.dock-icon-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
  filter: drop-shadow(0 2px 6px rgba(0,0,0,.3));
}
.dock-icon.active .dock-icon-img {
  filter: brightness(1.25) drop-shadow(0 0 8px rgba(120,160,255,.75));
}
.dock-icon-label {
  position: absolute;
  top: 100%;
  margin-top: 3px;
  font-size: 11px;
  color: var(--text-secondary);
  white-space: nowrap;
  pointer-events: none;
}

/* ===== 旋转箭头（圆心里上/下，随中枢列布局） ===== */
.dock-arrow {
  align-self: flex-start;   /* 2026-08-26：用户要求箭头靠左边（贴中枢左缘） */
  width: 34px;
  height: 26px;
  border: none;
  border-radius: 8px;
  background: rgba(128,128,128,.14);
  backdrop-filter: blur(6px);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background .2s ease, color .2s ease;
  pointer-events: auto;
  z-index: 25;
  flex-shrink: 0;
}
.dock-arrow:hover {
  background: rgba(128,128,128,.3);
  color: var(--text-primary);
}

/* ===== 窄屏缩放 ===== */
@media (max-width: 1400px) {
  .edge-dock {
    transform: translateY(-50%) scale(.8);
    transform-origin: center center;
  }
}
@media (max-width: 1100px) {
  .edge-dock {
    transform: translateY(-50%) scale(.62);
    transform-origin: center center;
  }
}

/* ===== 意见反馈弹窗（原侧边栏同款样式） ===== */
.custom-select {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent);
  border: 1px solid rgba(255,255,255,0.06);
  cursor: pointer;
  transition: all 0.3s ease;
  color: var(--text-secondary);
  font-size: 14px;
  user-select: none;
}
.custom-select:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 10%, transparent);
  border-color: var(--line-soft);
  transform: translateY(-1px);
}
[data-theme="dark"] .custom-select {
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
}
.select-display {
  color: var(--text-primary);
}
.select-arrow {
  font-size: 12px;
  color: var(--text-muted);
  transition: transform 0.3s ease;
}
.select-arrow.rotated {
  transform: rotate(180deg);
}
.custom-select-dropdown {
  position: absolute;
  top: 44px;
  left: 0;
  right: 0;
  background: color-mix(in srgb, var(--surface, #ffffff) 10%, transparent);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--line-soft);
  border-radius: 10px;
  padding: 4px 0;
  box-shadow: 0 8px 32px rgba(0,0,0,0.15);
  z-index: 100;
  min-width: 160px;
}
[data-theme="dark"] .custom-select-dropdown {
  background: var(--well);
}
.select-option {
  padding: 8px 14px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-secondary);
  transition: all 0.2s ease;
  border-radius: 6px;
  margin: 2px 4px;
}
.select-option:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 8%, transparent);
  color: var(--text-primary);
  transform: translateX(2px);
}
.select-option.active {
  background: color-mix(in srgb, var(--surface, #ffffff) 10%, transparent);
  color: var(--text-primary);
}
.feedback-dialog {
  padding: 4px 0;
}
.feedback-tip {
  color: var(--text-muted);
  font-size: 14px;
  margin-bottom: 16px;
  text-align: center;
}
.feedback-dialog :deep(.el-form-item) {
  margin-bottom: 16px;
  position: relative;
}
.feedback-dialog :deep(.el-textarea__inner) {
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent) !important;
  border-color: rgba(255,255,255,0.06) !important;
  color: var(--text-primary) !important;
  border-radius: 10px !important;
  transition: all 0.3s ease !important;
}
.feedback-dialog :deep(.el-textarea__inner:hover) {
  border-color: var(--line) !important;
}
[data-theme="dark"] .feedback-dialog :deep(.el-textarea__inner) {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent) !important;
}
.feedback-dialog :deep(.el-textarea__inner:focus) {
  border-color: var(--line-strong) !important;
}
.feedback-dialog :deep(.el-input__wrapper) {
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent) !important;
  border-color: rgba(255,255,255,0.06) !important;
  border-radius: 10px !important;
  transition: all 0.3s ease !important;
}
.feedback-dialog :deep(.el-input__wrapper:hover) {
  border-color: var(--line) !important;
}
[data-theme="dark"] .feedback-dialog :deep(.el-input__wrapper) {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent) !important;
}
</style>

<style>
/* ===== 反馈弹窗外层（teleport 到 body，需全局选择器） ===== */
.feedback-dialog-wrapper {
  --el-dialog-bg-color: transparent;
}
.feedback-dialog-wrapper .el-overlay {
  background: transparent !important;
  backdrop-filter: none !important;
}
.feedback-dialog-wrapper .el-dialog {
  background: color-mix(in srgb, var(--surface, #ffffff) 8%, transparent) !important;
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  border: 1px solid var(--line-soft) !important;
  border-radius: 16px !important;
  box-shadow: 0 8px 40px rgba(0,0,0,0.2) !important;
}
[data-theme="dark"] .feedback-dialog-wrapper .el-dialog {
  background: var(--well) !important;
  border-color: rgba(255,255,255,0.06) !important;
  box-shadow: 0 8px 40px rgba(0,0,0,0.4) !important;
}
.feedback-dialog-wrapper .el-dialog__header {
  padding: 16px 20px 0;
}
.feedback-dialog-wrapper .el-dialog__title {
  color: var(--text-primary) !important;
  font-weight: 600;
}
.feedback-dialog-wrapper .el-dialog__body {
  padding: 12px 20px 8px;
}
.feedback-dialog-wrapper .el-dialog__footer {
  padding: 0 20px 16px;
}
.feedback-dialog-wrapper .el-button {
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent) !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
  color: var(--text-secondary) !important;
  border-radius: 8px !important;
  transition: all 0.3s ease !important;
}
.feedback-dialog-wrapper .el-button:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 12%, transparent) !important;
  transform: translateY(-2px);
}
.feedback-dialog-wrapper .el-button--primary {
  background: color-mix(in srgb, var(--brand) 15%, transparent) !important;
  border-color: color-mix(in srgb, var(--brand) 20%, transparent) !important;
  color: var(--brand-bright) !important;
}
.feedback-dialog-wrapper .el-button--primary:hover {
  background: color-mix(in srgb, var(--brand) 25%, transparent) !important;
}
</style>
