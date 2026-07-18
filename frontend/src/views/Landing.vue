<template>
  <WaterBackground>
    <div class="landing-content">
      <!-- ===== 顶部导航 ===== -->
      <div class="landing-nav">
        <div class="nav-left">
          <img src="/logo.png" alt="基智" class="nav-logo" />
          <span class="nav-brand">基智</span>
        </div>
        <div class="nav-actions">
          <button class="nav-link" @click="goLogin">登录</button>
          <button class="nav-btn-primary" @click="goRegister">注册</button>
        </div>
      </div>

      <!-- ===== 主体 ===== -->
      <div class="landing-main">
        <div class="hero">
          <div class="hero-logo">
            <img src="/logo.png" alt="基智" class="hero-logo-img" />
            <div class="hero-logo-text">
              <span class="hero-logo-main">基智</span>
              <span class="hero-logo-sub">学习助手</span>
            </div>
          </div>
          <div class="hero-badge">AI · 多智能体学习系统</div>
          <h1 class="hero-title">让学习更高效</h1>
          <p class="hero-desc">
            规划 · 生成 · 评估 · 掌握<br />
            多智能体协作，个性化学习体验
          </p>
          <div class="hero-actions">
            <button class="cta-primary" @click="goLogin">开始学习</button>
            <button class="cta-ghost" @click="goLogin">已有账号？登录 →</button>
          </div>
        </div>

        <!-- ===== 右侧视频轮播 ===== -->
        <div class="screenshot-section">
          <div class="screenshot-frame">
            <div class="screenshot-carousel">
              <!-- 科幻光晕 -->
              <div class="cyber-glow"></div>
              <div class="cyber-glow-2"></div>

              <!-- 视频轨道 -->
              <div
                class="slide-track"
                :style="{ transform: `translateX(-${currentSlide * 100}%)` }"
              >
                <div
                  v-for="(slide, idx) in slides"
                  :key="idx"
                  class="slide-item"
                >
                  <video
                    :src="slide.video"
                    autoplay
                    muted
                    loop
                    playsinline
                    preload="auto"
                    class="slide-video"
                    @mouseenter="pauseVideo(idx)"
                    @mouseleave="playVideo(idx)"
                    ref="videoRefs"
                  ></video>

                  <!-- 视频信息叠加 -->
                  <div class="slide-overlay">
                    <div class="overlay-header">
                      <span class="overlay-index">0{{ idx + 1 }}</span>
                      <span class="overlay-title">{{ slide.label }}</span>
                    </div>
                    <div class="overlay-divider"></div>
                    <p class="overlay-desc">{{ slide.desc }}</p>
                    <div class="overlay-tags">
                      <span
                        v-for="(tag, ti) in slide.tags"
                        :key="ti"
                        class="overlay-tag"
                      >
                        {{ tag }}
                      </span>
                    </div>
                  </div>

                  <!-- 科幻扫描线 -->
                  <div class="scan-line-effect"></div>
                </div>
              </div>

              <!-- 箭头 -->
              <button class="carousel-arrow prev" @click="prevSlide">
                <svg viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/></svg>
              </button>
              <button class="carousel-arrow next" @click="nextSlide">
                <svg viewBox="0 0 24 24"><path d="M9 18l6-6-6-6" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/></svg>
              </button>

              <!-- 底部指示点 -->
              <div class="carousel-dots">
                <span
                  v-for="(slide, idx) in slides"
                  :key="idx"
                  class="dot"
                  :class="{ active: currentSlide === idx }"
                  @click="goToSlide(idx)"
                >
                  <span class="dot-tooltip">{{ slide.label }}</span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 底部功能卡片 ===== -->
      <div class="features-section">
        <div class="features-grid">
          <div
            v-for="(slide, idx) in slides"
            :key="idx"
            class="feature-card"
            :class="{ active: currentSlide === idx }"
            @click="goToSlide(idx)"
          >
            <div class="feature-icon" v-html="slide.iconSvg"></div>
            <h3>{{ slide.featureTitle }}</h3>
            <p>{{ slide.featureDesc }}</p>
          </div>
        </div>
      </div>

      <!-- ===== 底部 ===== -->
      <div class="landing-footer">
        <span>AI 驱动 · 免费使用 · 随时随地学习</span>
      </div>
    </div>
  </WaterBackground>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import WaterBackground from '@/components/WaterBackground.vue'

const router = useRouter()

// ===== 5 个视频 + 数据 =====
const slides = [
  {
    video: '/videos/slides/slide1.mp4',
    label: '主界面对话',
    desc: '多智能体协作，AI 实时对话解答。系统自动识别用户意图，调度规划、生成、评估三类 Agent 协同工作，提供精准的个性化学习支持。',
    tags: ['多智能体', '意图识别', '实时对话'],
    iconSvg: `<svg viewBox="0 0 24 24" width="28" height="28"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.8" fill="none"/><path d="M8 14s1.5 2 4 2 4-2 4-2" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round"/><circle cx="9" cy="10" r="1.2" fill="currentColor"/><circle cx="15" cy="10" r="1.2" fill="currentColor"/></svg>`,
    featureTitle: '主界面对话',
    featureDesc: '多智能体协作 · 实时对话解答'
  },
  {
    video: '/videos/slides/slide2.mp4',
    label: '资源库生成',
    desc: 'AI 驱动个性化出题，支持选择题、填空题、判断题、简答题、计算题、编程题等 7 种题型。可根据用户指定的学科、知识点、难度自动生成高质量题目。',
    tags: ['AI 出题', '7 种题型', '题集管理'],
    iconSvg: `<svg viewBox="0 0 24 24" width="28" height="28"><rect x="2" y="2" width="20" height="20" rx="2" stroke="currentColor" stroke-width="1.8" fill="none"/><path d="M8 12h8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><path d="M8 16h5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><path d="M8 8h8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>`,
    featureTitle: '资源库生成',
    featureDesc: 'AI 出题 · 题集管理 · 错题本'
  },
  {
    video: '/videos/slides/slide3.mp4',
    label: '六维画像',
    desc: '从知识基础、认知风格、易错偏好、学习目标、学习人格、兴趣领域六个维度构建动态学生画像。画像随学习数据更新，真正实现个性化学习诊断。',
    tags: ['六维分析', '动态更新', '个性化诊断'],
    iconSvg: `<svg viewBox="0 0 24 24" width="28" height="28"><path d="M12 2L2 7l10 5 10-5-10-5z" stroke="currentColor" stroke-width="1.8" fill="none"/><path d="M2 17l10 5 10-5" stroke="currentColor" stroke-width="1.8" fill="none"/><path d="M2 12l10 5 10-5" stroke="currentColor" stroke-width="1.8" fill="none"/></svg>`,
    featureTitle: '六维画像',
    featureDesc: '评估中心 · 知识基础 / 认知风格 / 学习目标'
  },
  {
    video: '/videos/slides/slide4.mp4',
    label: 'AI伙伴小基',
    desc: '专属 AI 学习伙伴，支持文字聊天、图片理解、题目评价。调用 4 个智能体协同工作，从理解、评估、解析、规划四个维度深度分析学习内容。',
    tags: ['AI 伙伴', '图片理解', '4 个 Agent'],
    iconSvg: `<svg viewBox="0 0 24 24" width="28" height="28"><rect x="2" y="4" width="20" height="16" rx="2" stroke="currentColor" stroke-width="1.8" fill="none"/><circle cx="9" cy="12" r="1.5" fill="currentColor"/><circle cx="15" cy="12" r="1.5" fill="currentColor"/><path d="M8 16s1.5 1.5 4 1.5 4-1.5 4-1.5" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round"/></svg>`,
    featureTitle: 'AI伙伴小基',
    featureDesc: '社区智能伙伴 · 聊天 / 图片理解 / 题目评价'
  },
  {
    video: '/videos/slides/slide5.mp4',
    label: '动态广场',
    desc: '学习社区互动空间，支持发布图文动态、点赞收藏、评论互动、好友系统、排行榜、私聊分享题目。构建学习社交圈，让学习不再孤单。',
    tags: ['学习社区', '互动分享', '好友系统'],
    iconSvg: `<svg viewBox="0 0 24 24" width="28" height="28"><rect x="2" y="2" width="8" height="8" rx="1" stroke="currentColor" stroke-width="1.8" fill="none"/><rect x="14" y="2" width="8" height="8" rx="1" stroke="currentColor" stroke-width="1.8" fill="none"/><rect x="2" y="14" width="8" height="8" rx="1" stroke="currentColor" stroke-width="1.8" fill="none"/><rect x="14" y="14" width="8" height="8" rx="1" stroke="currentColor" stroke-width="1.8" fill="none"/></svg>`,
    featureTitle: '动态广场',
    featureDesc: '分享 · 交流 · 共同进步，学习不再孤单'
  },
]

const currentSlide = ref(0)
const videoRefs = ref([])
let autoPlayTimer = null
let isTransitioning = false

function goToSlide(index) {
  if (isTransitioning || index === currentSlide.value) return
  isTransitioning = true
  currentSlide.value = index
  setTimeout(() => { isTransitioning = false }, 500)
  resetAutoPlay()
}

function nextSlide() {
  const next = (currentSlide.value + 1) % slides.length
  goToSlide(next)
}

function prevSlide() {
  const prev = (currentSlide.value - 1 + slides.length) % slides.length
  goToSlide(prev)
}

function resetAutoPlay() {
  if (autoPlayTimer) {
    clearInterval(autoPlayTimer)
    autoPlayTimer = null
  }
  autoPlayTimer = setInterval(() => {
    nextSlide()
  }, 6000)
}

function pauseVideo(idx) {
  const el = videoRefs.value[idx]
  if (el) el.pause()
}

function playVideo(idx) {
  const el = videoRefs.value[idx]
  if (el) el.play()
}

function goLogin() {
  router.push('/login')
}

function goRegister() {
  router.push('/login?tab=register')
}

onMounted(() => {
  resetAutoPlay()
})

onUnmounted(() => {
  if (autoPlayTimer) {
    clearInterval(autoPlayTimer)
    autoPlayTimer = null
  }
})
</script>

<style scoped>
/* 样式和之前一样，保持不变 */
.landing-content {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 16px 32px 12px;
  animation: fadeIn 0.8s ease both;
}

.landing-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0 14px;
  flex-shrink: 0;
  border-bottom: 1px solid var(--border-color);
  animation: fadeInDown 0.6s ease both;
}
.nav-left {
  display: flex;
  align-items: center;
  gap: 14px;
}
.nav-logo {
  width: 44px;
  height: 44px;
  object-fit: contain;
}
.nav-brand {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}
.nav-actions {
  display: flex;
  align-items: center;
  gap: 18px;
}
.nav-link {
  background: none;
  border: none;
  font-size: 17px;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 8px 4px;
  transition: color 0.3s ease;
}
.nav-link:hover {
  color: var(--text-primary);
}
.nav-btn-primary {
  background: rgba(64, 158, 255, 0.12);
  border: 1px solid rgba(64, 158, 255, 0.2);
  color: #409eff;
  font-size: 17px;
  padding: 10px 34px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.nav-btn-primary:hover {
  background: rgba(64, 158, 255, 0.2);
}

.landing-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 40px;
  padding: 16px 0 12px;
  padding-left: 60px;
}

.hero {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 560px;
  margin-left: 40px;
}
.hero-logo {
  display: flex;
  align-items: center;
  gap: 22px;
  animation: fadeInUp 0.8s ease both 0.1s;
}
.hero-logo-img {
  width: 96px;
  height: 96px;
  object-fit: contain;
}
.hero-logo-text {
  display: flex;
  flex-direction: column;
  line-height: 1.05;
}
.hero-logo-main {
  font-size: 60px;
  font-weight: 700;
  background: linear-gradient(135deg, #409eff, #7c6df0);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.hero-logo-sub {
  font-size: 22px;
  font-weight: 400;
  color: var(--text-secondary);
  letter-spacing: 3px;
}
.hero-badge {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 3px;
  animation: fadeInUp 0.8s ease both 0.2s;
}
.hero-title {
  font-size: 44px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.15;
  animation: fadeInUp 0.8s ease both 0.3s;
}
.hero-desc {
  font-size: 20px;
  line-height: 1.8;
  color: var(--text-secondary);
  margin: 0;
  animation: fadeInUp 0.8s ease both 0.4s;
}
.hero-actions {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-top: 4px;
  animation: fadeInUp 0.8s ease both 0.5s;
}
.cta-primary {
  background: linear-gradient(135deg, #409eff, #7c6df0);
  border: none;
  color: #fff;
  font-size: 20px;
  font-weight: 500;
  padding: 18px 56px;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 24px rgba(64, 158, 255, 0.35);
}
.cta-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 36px rgba(64, 158, 255, 0.45);
}
.cta-ghost {
  background: none;
  border: none;
  font-size: 18px;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 10px 4px;
  transition: all 0.3s ease;
}
.cta-ghost:hover {
  color: var(--text-primary);
}

.screenshot-section {
  flex: 1.2;
  max-width: 780px;
  margin-right: -20px;
  animation: fadeInRight 0.9s ease both 0.2s;
}
.screenshot-frame {
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 20px;
  padding: 22px;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.04);
  aspect-ratio: 16 / 10;
  transition: all 0.4s ease;
}
.screenshot-frame:hover {
  border-color: rgba(64, 158, 255, 0.15);
  box-shadow: 0 12px 60px rgba(64, 158, 255, 0.06);
}
[data-theme="dark"] .screenshot-frame {
  background: rgba(0, 0, 0, 0.2);
  border-color: rgba(255, 255, 255, 0.04);
}

.screenshot-carousel {
  width: 100%;
  height: 100%;
  border-radius: 12px;
  position: relative;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.15);
}

.cyber-glow {
  position: absolute;
  top: -30%;
  right: -20%;
  width: 60%;
  height: 80%;
  background: radial-gradient(ellipse, rgba(64, 158, 255, 0.06) 0%, transparent 70%);
  z-index: 1;
  pointer-events: none;
  animation: glowFloat 6s ease-in-out infinite;
}
.cyber-glow-2 {
  position: absolute;
  bottom: -30%;
  left: -20%;
  width: 50%;
  height: 70%;
  background: radial-gradient(ellipse, rgba(124, 109, 240, 0.05) 0%, transparent 70%);
  z-index: 1;
  pointer-events: none;
  animation: glowFloat 8s ease-in-out infinite reverse;
}
@keyframes glowFloat {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(20px, -20px) scale(1.1); }
}

.slide-track {
  display: flex;
  width: 100%;
  height: 100%;
  transition: transform 0.7s cubic-bezier(0.34, 1.56, 0.64, 1);
  will-change: transform;
  position: relative;
  z-index: 2;
}

.slide-item {
  flex: 0 0 100%;
  height: 100%;
  position: relative;
  border-radius: 12px;
  overflow: hidden;
}

.slide-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  border-radius: 12px;
}

.slide-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 24px 28px 20px;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.7) 40%, rgba(0, 0, 0, 0.85) 100%);
  backdrop-filter: blur(2px);
  z-index: 3;
}
.overlay-header {
  display: flex;
  align-items: center;
  gap: 14px;
}
.overlay-index {
  font-size: 13px;
  font-weight: 700;
  color: #409eff;
  letter-spacing: 1px;
  background: rgba(64, 158, 255, 0.12);
  padding: 2px 12px;
  border-radius: 20px;
  border: 1px solid rgba(64, 158, 255, 0.15);
}
.overlay-title {
  font-size: 20px;
  font-weight: 600;
  color: #fff;
  letter-spacing: 1px;
}
.overlay-divider {
  width: 40px;
  height: 2px;
  background: linear-gradient(90deg, #409eff, transparent);
  margin: 6px 0 4px 0;
}
.overlay-desc {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.75);
  line-height: 1.6;
  margin: 4px 0 8px;
  max-width: 80%;
}
.overlay-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.overlay-tag {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.06);
  padding: 2px 12px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.scan-line-effect {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2;
  pointer-events: none;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(64, 158, 255, 0.01) 2px,
    rgba(64, 158, 255, 0.01) 4px
  );
}

.carousel-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  color: #fff;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  z-index: 20;
  opacity: 0;
}
.screenshot-carousel:hover .carousel-arrow {
  opacity: 1;
}
.carousel-arrow:hover {
  background: rgba(64, 158, 255, 0.5);
  transform: translateY(-50%) scale(1.08);
}
.carousel-arrow.prev {
  left: 14px;
}
.carousel-arrow.next {
  right: 14px;
}
.carousel-arrow svg {
  color: #fff;
  width: 24px;
  height: 24px;
}

.carousel-dots {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 10px;
  z-index: 20;
  background: rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(8px);
  padding: 6px 12px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.04);
}
.carousel-dots .dot {
  width: 28px;
  height: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.2);
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
.carousel-dots .dot.active {
  background: #409eff;
  width: 44px;
  box-shadow: 0 0 20px rgba(64, 158, 255, 0.3);
}
.carousel-dots .dot:hover {
  background: rgba(255, 255, 255, 0.5);
  transform: scaleY(1.8);
}
.carousel-dots .dot.active:hover {
  background: #409eff;
  transform: scaleY(1.8);
}
.dot-tooltip {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%) scale(0.8);
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  color: #fff;
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 6px;
  white-space: nowrap;
  opacity: 0;
  transition: all 0.3s ease;
  pointer-events: none;
}
.dot:hover .dot-tooltip {
  opacity: 1;
  transform: translateX(-50%) scale(1);
}

.features-section {
  flex-shrink: 0;
  padding: 18px 0 12px;
  border-top: 1px solid var(--border-color);
}
.features-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}
.feature-card {
  padding: 16px 18px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  opacity: 0;
  animation: fadeInUp 0.6s ease forwards;
  text-align: center;
}
.feature-card:nth-child(1) { animation-delay: 0.6s; }
.feature-card:nth-child(2) { animation-delay: 0.7s; }
.feature-card:nth-child(3) { animation-delay: 0.8s; }
.feature-card:nth-child(4) { animation-delay: 0.9s; }
.feature-card:nth-child(5) { animation-delay: 1.0s; }

.feature-card:hover {
  background: rgba(255, 255, 255, 0.06);
  transform: translateY(-4px) scale(1.02);
  border-color: rgba(64, 158, 255, 0.15);
  box-shadow: 0 4px 20px rgba(64, 158, 255, 0.04);
}
.feature-card.active {
  border-color: #409eff;
  background: rgba(64, 158, 255, 0.04);
  box-shadow: 0 4px 20px rgba(64, 158, 255, 0.06);
}
.feature-card:active {
  transform: scale(0.95);
}
[data-theme="dark"] .feature-card:hover {
  background: rgba(255, 255, 255, 0.03);
}
[data-theme="dark"] .feature-card.active {
  border-color: #409eff;
  background: rgba(64, 158, 255, 0.06);
}

.feature-icon {
  color: #409eff;
  opacity: 0.4;
  margin-bottom: 4px;
  display: flex;
  justify-content: center;
}
.feature-icon svg {
  transition: all 0.4s ease;
}
.feature-card.active .feature-icon {
  opacity: 1;
}
.feature-card.active .feature-icon svg {
  filter: drop-shadow(0 0 12px rgba(64, 158, 255, 0.3));
}
.feature-card h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 2px;
}
.feature-card p {
  font-size: 12px;
  color: var(--text-muted);
  margin: 0;
  line-height: 1.5;
}

.landing-footer {
  flex-shrink: 0;
  text-align: center;
  padding: 16px 0 6px;
  font-size: 14px;
  color: var(--text-muted);
  border-top: 1px solid var(--border-color);
  letter-spacing: 0.5px;
  animation: fadeIn 0.8s ease both 0.8s;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
@keyframes fadeInDown {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes fadeInRight {
  from { opacity: 0; transform: translateX(40px); }
  to { opacity: 1; transform: translateX(0); }
}

@media (max-width: 1024px) {
  .landing-content { padding: 14px 32px 10px; }
  .landing-main { gap: 40px; padding-left: 30px; }
  .hero { margin-left: 20px; }
  .hero-logo-main { font-size: 48px; }
  .hero-logo-img { width: 76px; height: 76px; }
  .hero-title { font-size: 36px; }
  .screenshot-section { max-width: 520px; margin-right: 0; }
  .features-grid { grid-template-columns: repeat(3, 1fr); }
  .overlay-desc { max-width: 100%; font-size: 12px; }
}

@media (max-width: 768px) {
  .landing-content { padding: 12px 18px 10px; }
  .landing-main {
    flex-direction: column;
    gap: 24px;
    padding: 12px 0;
    padding-left: 0;
  }
  .hero {
    max-width: 100%;
    align-items: center;
    text-align: center;
    margin-left: 0;
  }
  .hero-logo {
    flex-direction: column;
    align-items: center;
    gap: 10px;
  }
  .hero-logo-main { font-size: 42px; }
  .hero-logo-img { width: 64px; height: 64px; }
  .hero-title { font-size: 30px; }
  .hero-actions { flex-direction: column; width: 100%; }
  .screenshot-section { max-width: 100%; width: 100%; margin-right: 0; }
  .screenshot-frame { aspect-ratio: 16 / 11; }
  .features-grid { grid-template-columns: repeat(3, 1fr); gap: 10px; }
  .feature-card { padding: 12px 14px; }
  .feature-card h3 { font-size: 13px; }
  .feature-card p { font-size: 11px; }
  .overlay-desc { max-width: 100%; font-size: 12px; }
  .overlay-title { font-size: 16px; }
  .slide-overlay { padding: 16px 18px 14px; }
  .carousel-arrow { width: 34px; height: 34px; }
  .carousel-dots .dot { width: 20px; height: 5px; }
  .carousel-dots .dot.active { width: 32px; }
}

@media (max-width: 480px) {
  .landing-content { padding: 10px 14px 8px; }
  .hero-logo-main { font-size: 34px; }
  .hero-logo-img { width: 52px; height: 52px; }
  .hero-title { font-size: 24px; }
  .hero-desc { font-size: 16px; }
  .cta-primary { font-size: 16px; padding: 14px 32px; }
  .features-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .feature-card { padding: 10px 12px; }
  .feature-card h3 { font-size: 12px; }
  .feature-card p { font-size: 10px; }
  .nav-brand { font-size: 18px; }
  .nav-logo { width: 34px; height: 34px; }
  .screenshot-frame { aspect-ratio: 16 / 12; }
  .slide-overlay { padding: 12px 14px 10px; }
  .overlay-index { font-size: 10px; }
  .overlay-title { font-size: 14px; }
  .overlay-desc { font-size: 11px; }
  .overlay-tag { font-size: 9px; }
  .carousel-dots { gap: 6px; padding: 4px 10px; }
  .carousel-dots .dot { width: 16px; height: 4px; }
  .carousel-dots .dot.active { width: 24px; }
}
</style>