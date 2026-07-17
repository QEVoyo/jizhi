<template>
  <div class="xiaoji-settings-page">
    <!-- ===== 顶部导航 ===== -->
    <div class="settings-header">
      <el-button text class="back-btn" @click="goBack">
        <i class="fas fa-arrow-left"></i>
      </el-button>
      <h2>🤖 小基设置</h2>
      <span class="dev-tag">Beta</span>
    </div>

    <el-divider />

    <!-- ===== 形象轮播（无背景，带阴影底盘） ===== -->
    <div class="avatar-carousel-wrapper">
      <div class="avatar-stage">
        <div
          class="avatar-slide"
          v-for="(item, index) in avatarStates"
          :key="item.key"
          :class="{ active: currentSlide === index }"
        >
          <img :src="item.image" :alt="item.label" class="avatar-full" />
          <div class="avatar-shadow"></div>
        </div>
      </div>

      <!-- 状态标签 -->
      <div class="slide-label">{{ avatarStates[currentSlide].label }}</div>

      <!-- 指示点 -->
      <div class="carousel-dots">
        <span
          v-for="(item, index) in avatarStates"
          :key="item.key"
          class="dot"
          :class="{ active: currentSlide === index }"
          @click="currentSlide = index"
        ></span>
      </div>

      <!-- 左右控制 -->
      <div class="carousel-controls">
        <button class="carousel-btn prev" @click="handleManualSlide(prevSlide)">
          <i class="fas fa-chevron-left"></i>
        </button>
        <button class="carousel-btn next" @click="handleManualSlide(nextSlide)">
          <i class="fas fa-chevron-right"></i>
        </button>
      </div>
    </div>

    <el-divider />

    <!-- ===== 设置内容 ===== -->
    <div class="settings-body">
      <!-- 基础设置 -->
      <div class="setting-group">
        <div class="group-title">
          <i class="fas fa-sliders-h"></i>
          <span>基础设置</span>
        </div>

        <div class="setting-item">
          <div class="setting-left">
            <span class="setting-label">小基名称</span>
            <span class="setting-value">{{ settings.name }}</span>
          </div>
          <el-input v-model="settings.name" size="small" style="width:140px" />
          <el-button size="small" type="primary" @click="saveSetting">保存</el-button>
        </div>

        <div class="setting-item">
          <div class="setting-left">
            <span class="setting-label">主动问候</span>
            <span class="setting-desc">开启后小基会主动打招呼</span>
          </div>
          <el-switch v-model="settings.proactive_enabled" @change="saveSetting" />
        </div>

        <div class="setting-item">
          <div class="setting-left">
            <span class="setting-label">语音播报</span>
            <span class="setting-desc">小基回复时自动朗读</span>
          </div>
          <el-switch v-model="settings.voice_enabled" @change="saveSetting" />
        </div>
      </div>

      <el-divider />

      <!-- 语音设置 -->
      <div class="setting-group">
        <div class="group-title">
          <i class="fas fa-voice"></i>
          <span>语音设置</span>
        </div>

        <div class="setting-item">
          <div class="setting-left">
            <span class="setting-label">语速</span>
            <span class="setting-value">{{ settings.voice_speed }}</span>
          </div>
          <el-slider
            v-model="settings.voice_speed"
            :min="1"
            :max="9"
            style="width:160px"
            @change="saveSetting"
          />
        </div>

        <div class="setting-item">
          <div class="setting-left">
            <span class="setting-label">音量</span>
            <span class="setting-value">{{ settings.voice_volume }}</span>
          </div>
          <el-slider
            v-model="settings.voice_volume"
            :min="1"
            :max="9"
            style="width:160px"
            @change="saveSetting"
          />
        </div>

        <div class="setting-item">
          <div class="setting-left">
            <span class="setting-label">音色</span>
          </div>
          <el-select v-model="settings.voice_name" size="small" style="width:160px" @change="saveSetting">
            <el-option
              v-for="v in voiceList"
              :key="v.value"
              :label="v.label"
              :value="v.value"
            />
          </el-select>
          <el-button size="small" @click="testVoice">试听</el-button>
        </div>
      </div>

      <el-divider />

      <!-- 风格 -->
      <div class="setting-group">
        <div class="group-title">
          <i class="fas fa-theater-masks"></i>
          <span>语气风格</span>
        </div>

        <div class="setting-item">
          <el-radio-group v-model="settings.personality" @change="saveSetting">
            <el-radio-button value="warm">温暖</el-radio-button>
            <el-radio-button value="humorous">幽默</el-radio-button>
            <el-radio-button value="formal">正式</el-radio-button>
            <el-radio-button value="encouraging">鼓励型</el-radio-button>
          </el-radio-group>
        </div>
      </div>

      <el-divider />

      <!-- 高级功能 -->
      <div class="setting-group">
        <div class="group-title">
          <i class="fas fa-rocket"></i>
          <span>高级功能</span>
          <el-tag size="small" type="warning">开发中</el-tag>
        </div>

        <div class="setting-item">
          <div class="setting-left">
            <span class="setting-label">语音通话</span>
            <span class="setting-desc">实时语音对话</span>
          </div>
          <el-button size="small" type="primary" @click="goCall">进入</el-button>
        </div>

        <div class="setting-item">
          <div class="setting-left">
            <span class="setting-label">数字人</span>
            <span class="setting-desc">虚拟形象视频通话</span>
          </div>
          <el-button size="small" disabled>开发中</el-button>
        </div>

        <div class="setting-item">
          <div class="setting-left">
            <span class="setting-label">历史对话检索</span>
            <span class="setting-desc">搜索聊天记录</span>
          </div>
          <el-button size="small" @click="showDeveloping">搜索</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { getXiaojiConfig, updateXiaojiConfig } from '@/api/xiaoji'

const router = useRouter()
const authStore = useAuthStore()

const settings = ref({
  name: '小基',
  personality: 'warm',
  voice_enabled: true,
  voice_speed: 5,
  voice_volume: 5,
  voice_name: 'xiaoyan',
  proactive_enabled: true
})

const voiceList = [
  { value: 'xiaoyan', label: '标准女声' },
  { value: 'xiaofeng', label: '标准男声' },
  { value: 'xiaokun', label: '童声' },
  { value: 'xiaorui', label: '温柔女声' },
  { value: 'xiaomei', label: '甜美女声' },
  { value: 'xiaoxuan', label: '知性女声' },
  { value: 'xiaoyu', label: '年轻男声' },
  { value: 'xiaomeng', label: '活力女声' }
]

// ===== 形象轮播 =====
const avatarStates = [
  { key: 'idle', label: '待命 · 在线', image: '/images/xiaoji/xiaoji_idle.png' },
  { key: 'thinking', label: '思考中', image: '/images/xiaoji/xiaoji_thinking.png' },
  { key: 'speaking', label: '输出中', image: '/images/xiaoji/xiaoji_speaking.png' },
  { key: 'happy', label: '已完成', image: '/images/xiaoji/xiaoji_happy.png' },
  { key: 'sleeping', label: '休眠', image: '/images/xiaoji/xiaoji_sleeping.png' }
]

const currentSlide = ref(0)
let autoSlideTimer = null

function nextSlide() {
  currentSlide.value = (currentSlide.value + 1) % avatarStates.length
}

function prevSlide() {
  currentSlide.value = (currentSlide.value - 1 + avatarStates.length) % avatarStates.length
}

function startAutoSlide() {
  autoSlideTimer = setInterval(() => {
    nextSlide()
  }, 4000)
}

function stopAutoSlide() {
  if (autoSlideTimer) {
    clearInterval(autoSlideTimer)
    autoSlideTimer = null
  }
}

function handleManualSlide(fn) {
  stopAutoSlide()
  fn()
  setTimeout(startAutoSlide, 3000)
}

// ===== 功能函数 =====
function goBack() {
  router.back()
}

function goCall() {
  router.push('/xiaoji/call')
}

function showDeveloping() {
  ElMessage.info('功能开发中，敬请期待')
}

function testVoice() {
  const text = '你好，我是小基'
  if (window.speechSynthesis) {
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'zh-CN'
    utterance.rate = settings.value.voice_speed / 5
    window.speechSynthesis.speak(utterance)
  } else {
    ElMessage.warning('浏览器不支持语音播报')
  }
}

async function saveSetting() {
  try {
    await updateXiaojiConfig(authStore.user.id, settings.value)
    ElMessage.success('设置已保存')
  } catch {
    ElMessage.warning('保存失败，但本地已生效')
  }
}

async function loadConfig() {
  try {
    const data = await getXiaojiConfig(authStore.user.id)
    if (data) {
      settings.value = { ...settings.value, ...data }
    }
  } catch {
    // 用默认值
  }
}

onMounted(() => {
  loadConfig()
  startAutoSlide()
})

onUnmounted(() => {
  stopAutoSlide()
})
</script>

<style scoped>
.xiaoji-settings-page {
  padding: 20px 28px;
  max-width: 760px;
  margin: 0 auto;
  min-height: 100vh;
}

/* ===== 顶部 ===== */
.settings-header {
  display: flex;
  align-items: center;
  gap: 12px;
}
.settings-header h2 {
  margin: 0;
  font-size: 22px;
}
.dev-tag {
  font-size: 12px;
  padding: 2px 12px;
  border-radius: 10px;
  background: rgba(34,197,94,0.12);
  color: #22c55e;
}
.back-btn {
  color: var(--text-secondary) !important;
  font-size: 18px;
}
.back-btn:hover {
  color: var(--text-primary) !important;
}

/* ===== 轮播 ===== */
.avatar-carousel-wrapper {
  position: relative;
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
  padding: 16px 0 8px;
}

.avatar-stage {
  position: relative;
  width: 100%;
  aspect-ratio: 1/1;
  max-height: 380px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-slide {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.6s ease;
}
.avatar-slide.active {
  opacity: 1;
}

.avatar-full {
  width: 90%;
  height: 90%;
  object-fit: contain;
  display: block;
  position: relative;
  z-index: 2;
}

/* ===== 阴影底盘 ===== */
.avatar-shadow {
  position: absolute;
  bottom: 4%;
  left: 50%;
  transform: translateX(-50%);
  width: 55%;
  height: 16%;
  border-radius: 50%;
  background: radial-gradient(ellipse, rgba(0,0,0,0.25) 0%, rgba(0,0,0,0.08) 50%, transparent 70%);
  pointer-events: none;
  z-index: 1;
}

/* ===== 状态标签 ===== */
.slide-label {
  text-align: center;
  font-size: 16px;
  font-weight: 500;
  color: var(--text-secondary);
  padding: 4px 0 8px;
  letter-spacing: 0.5px;
}

/* ===== 指示点 ===== */
.carousel-dots {
  display: flex;
  justify-content: center;
  gap: 8px;
  padding: 6px 0 4px;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
  opacity: 0.3;
  cursor: pointer;
  transition: all 0.3s ease;
}
.dot.active {
  opacity: 1;
  width: 20px;
  border-radius: 4px;
  background: #409eff;
}

/* ===== 控制按钮 ===== */
.carousel-controls {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  transform: translateY(-50%);
  display: flex;
  justify-content: space-between;
  padding: 0 4px;
  pointer-events: none;
  z-index: 5;
}
.carousel-btn {
  pointer-events: auto;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: rgba(0,0,0,0.3);
  backdrop-filter: blur(4px);
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}
.carousel-btn:hover {
  background: rgba(0,0,0,0.5);
  transform: scale(1.05);
}

/* ===== 设置 ===== */
.settings-body {
  padding: 4px 0;
}

.setting-group {
  padding: 4px 0;
}
.group-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 12px;
  font-size: 15px;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  gap: 12px;
  flex-wrap: wrap;
  border-bottom: 1px solid rgba(128,128,128,0.04);
}
.setting-item:last-child {
  border-bottom: none;
}

.setting-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 120px;
}
.setting-label {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}
.setting-desc {
  font-size: 12px;
  color: var(--text-muted);
}
.setting-value {
  font-size: 13px;
  color: var(--text-secondary);
  background: rgba(128,128,128,0.06);
  padding: 0 10px;
  border-radius: 4px;
  display: inline-block;
}

[data-theme="dark"] .xiaoji-settings-page {
  background: rgba(0,0,0,0.1);
}
[data-theme="dark"] .setting-item {
  border-bottom-color: rgba(255,255,255,0.04);
}

@media (max-width: 640px) {
  .xiaoji-settings-page {
    padding: 14px 16px;
  }
  .setting-item {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  .setting-left {
    min-width: unset;
  }
  .avatar-carousel-wrapper {
    max-width: 100%;
  }
  .avatar-shadow {
    width: 70%;
  }
}
</style>