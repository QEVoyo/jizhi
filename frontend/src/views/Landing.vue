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
          </p >
          <div class="hero-actions">
            <button class="cta-primary" @click="goLogin">开始学习</button>
            <button class="cta-ghost" @click="goLogin">已有账号？登录 →</button>
          </div>
        </div>

        <div class="screenshot-section">
          <div class="screenshot-frame">
            <div class="screenshot-carousel">
              <div class="slide-placeholder">
                <span class="slide-icon">◈</span>
                <p>产品截图</p >
                <span class="slide-hint">即将上线</span>
              </div>
              <div class="carousel-dots">
                <span class="dot active"></span>
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 功能卡片 ===== -->
      <div class="features-section">
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon">◈</div>
            <h3>多智能体协作</h3>
            <p>规划、生成、评估三位一体，AI 驱动学习全流程</p >
          </div>
          <div class="feature-card">
            <div class="feature-icon">◈</div>
            <h3>智能资源库</h3>
            <p>生成题目、管理题集、错题本自动收录</p >
          </div>
          <div class="feature-card">
            <div class="feature-icon">◈</div>
            <h3>学程追踪</h3>
            <p>打卡、计时、学习日志，可视化每一步成长</p >
          </div>
          <div class="feature-card">
            <div class="feature-icon">◈</div>
            <h3>社区互动</h3>
            <p>分享、交流、共同进步，让学习不再孤单</p >
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
import { useRouter } from 'vue-router'
import WaterBackground from '@/components/WaterBackground.vue'

const router = useRouter()

function goLogin() {
  router.push('/login')
}

function goRegister() {
  router.push('/login?tab=register')
}
</script>

<style scoped>
.landing-content {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 16px 32px 12px;
  animation: fadeIn 0.8s ease both;
}

/* ===== 导航 ===== */
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

/* ===== 主体 ===== */
.landing-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 40px;
  padding: 16px 0 12px;
  padding-left: 60px;
}

/* ===== 左侧 ===== */
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

/* ===== 右侧截图 ===== */
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
}
[data-theme="dark"] .screenshot-frame {
  background: rgba(0, 0, 0, 0.2);
  border-color: rgba(255, 255, 255, 0.04);
}

.screenshot-carousel {
  width: 100%;
  height: 100%;
  border-radius: 12px;
  background: rgba(128, 128, 128, 0.04);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}
.slide-placeholder {
  text-align: center;
  color: var(--text-muted);
}
.slide-icon {
  font-size: 56px;
  display: block;
  margin-bottom: 8px;
  opacity: 0.3;
}
.slide-placeholder p {
  font-size: 18px;
  margin: 0;
}
.slide-hint {
  font-size: 14px;
  opacity: 0.5;
  margin-top: 4px;
}

.carousel-dots {
  position: absolute;
  bottom: 18px;
  display: flex;
  gap: 10px;
}
.carousel-dots .dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--border-color);
  transition: all 0.3s ease;
}
.carousel-dots .dot.active {
  width: 32px;
  border-radius: 5px;
  background: #409eff;
}

/* ===== 功能卡片 ===== */
.features-section {
  flex-shrink: 0;
  padding: 18px 0 12px;
  border-top: 1px solid var(--border-color);
}
.features-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}
.feature-card {
  padding: 20px 22px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
  opacity: 0;
  animation: fadeInUp 0.6s ease forwards;
}
.feature-card:nth-child(1) { animation-delay: 0.6s; }
.feature-card:nth-child(2) { animation-delay: 0.7s; }
.feature-card:nth-child(3) { animation-delay: 0.8s; }
.feature-card:nth-child(4) { animation-delay: 0.9s; }

.feature-card:hover {
  background: rgba(255, 255, 255, 0.05);
  transform: translateY(-3px);
  border-color: rgba(64, 158, 255, 0.15);
}
[data-theme="dark"] .feature-card:hover {
  background: rgba(255, 255, 255, 0.03);
}
.feature-icon {
  font-size: 22px;
  color: #409eff;
  opacity: 0.5;
  margin-bottom: 4px;
}
.feature-card h3 {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 4px;
}
.feature-card p {
  font-size: 14px;
  color: var(--text-muted);
  margin: 0;
  line-height: 1.6;
}

/* ===== 底部 ===== */
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

/* ===== 入场动画 ===== */
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

/* ===== 响应式 ===== */
@media (max-width: 1024px) {
  .landing-content {
    padding: 14px 32px 10px;
  }
  .landing-main {
    gap: 40px;
    padding-left: 30px;
  }
  .hero {
    margin-left: 20px;
  }
  .hero-logo-main {
    font-size: 48px;
  }
  .hero-logo-img {
    width: 76px;
    height: 76px;
  }
  .hero-title {
    font-size: 36px;
  }
  .screenshot-section {
    max-width: 520px;
    margin-right: 0;
  }
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .landing-content {
    padding: 12px 18px 10px;
  }
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
  .hero-logo-main {
    font-size: 42px;
  }
  .hero-logo-img {
    width: 64px;
    height: 64px;
  }
  .hero-title {
    font-size: 30px;
  }
  .hero-actions {
    flex-direction: column;
    width: 100%;
  }
  .screenshot-section {
    max-width: 100%;
    width: 100%;
    margin-right: 0;
  }
  .screenshot-frame {
    aspect-ratio: 16 / 11;
  }
  .features-grid {
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
  .feature-card {
    padding: 14px 16px;
  }
}

@media (max-width: 480px) {
  .landing-content {
    padding: 10px 14px 8px;
  }
  .hero-logo-main {
    font-size: 34px;
  }
  .hero-logo-img {
    width: 52px;
    height: 52px;
  }
  .hero-title {
    font-size: 24px;
  }
  .hero-desc {
    font-size: 16px;
  }
  .cta-primary {
    font-size: 16px;
    padding: 14px 32px;
  }
  .features-grid {
    grid-template-columns: 1fr;
  }
  .nav-brand {
    font-size: 18px;
  }
  .nav-logo {
    width: 34px;
    height: 34px;
  }
}
</style>