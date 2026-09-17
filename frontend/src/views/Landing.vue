<template>
  <WaterBackground>
    <div class="landing-content">
      <!-- ===== 顶部导航 ===== -->
      <div class="landing-nav">
        <div class="nav-left" @click="onLogoClick">
          <img src="/logo.png" alt="基智" class="nav-logo" />
          <span class="nav-brand">基智</span>
        </div>
        <div class="nav-actions">
          <button class="nav-link" @click="scrollTo('features')">功能</button>
          <button class="nav-link" @click="scrollTo('faq')">常见问题</button>
          <button class="nav-link" @click="goLogin">登录</button>
          <button class="nav-btn-primary magnet" @click="goRegister">免费注册</button>
        </div>
      </div>

      <!-- ===== 主体 ===== -->
      <div class="landing-main">
        <Starfield ref="starfieldRef" />
        <div class="hero">
          <div class="hero-logo">
            <img src="/logo.png" alt="基智" class="hero-logo-img" @click="onLogoClick" />
            <div class="hero-logo-text">
              <span class="hero-logo-main">基智</span>
              <span class="hero-logo-sub">学习助手</span>
            </div>
          </div>
          <div class="hero-badge">AI 备考平台 · 17 考纲 · 12 套真题</div>
          <h1 class="hero-title">选一门考试<br />AI 陪你学到上岸</h1>
          <p class="hero-desc">
            摸底诊断 → 三阶段备考计划 → 每日任务 → 真题冲刺<br />
            19,000+ 题库 · 全程免费
          </p>
          <div class="hero-actions">
            <button class="cta-ghost explore-btn magnet" @click="scrollTo('features')">了解功能 ↓</button>
          </div>

          <!-- 打字机 + 考试倒计时 HUD -->
          <div class="hero-hud-line">
            <span class="hud-prompt">LOADING SYLLABUS</span>
            <span class="hud-typed">{{ typedText }}</span><span class="hud-caret">▍</span>
          </div>
          <div class="hero-countdown">
            <span class="cd-label">NEXT EXAMS</span>
            <span v-for="c in countdowns" :key="c" class="cd-item">{{ c }}</span>
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
                  <!-- ===== 学科计划：考纲芯片 + 三阶段计划 ===== -->
                  <div v-if="slide.type === 'plan'" class="mockup mockup-plan">
                    <div class="mu-hud-row">
                      <span class="mu-hud">SYLLABUS // 17 ONLINE</span>
                      <span class="mu-hud mu-hud-accent">MODE: AI DIAGNOSIS</span>
                    </div>
                    <div class="mu-chip-grid">
                      <span v-for="(c, i) in ['CET-4', '考研英', '法考', '公务员', '教资', 'CPA', '二级Py', '雅思']" :key="i" class="mu-chip" :class="'c' + (i % 4)">{{ c }}</span>
                    </div>
                    <div class="mu-phases">
                      <div class="mu-phase done"><i>✓</i>基础期</div>
                      <div class="mu-phase-line done"></div>
                      <div class="mu-phase active"><i>◆</i>强化期</div>
                      <div class="mu-phase-line"></div>
                      <div class="mu-phase"><i>○</i>冲刺期</div>
                    </div>
                    <div class="mu-plan-footer">
                      <span class="mu-hud">AI 正在分析你的摸底答卷…</span>
                      <div class="mu-bar"><div class="mu-bar-fill"></div></div>
                    </div>
                  </div>

                  <!-- ===== 真题套卷：试卷卡 + 计时 + 分数环 ===== -->
                  <div v-else-if="slide.type === 'exam'" class="mockup mockup-exam">
                    <div class="mu-exam-paper">
                      <div class="mu-paper-title"></div>
                      <div class="mu-paper-line" v-for="n in 5" :key="'l' + n"></div>
                      <div class="mu-paper-line short"></div>
                      <div class="mu-paper-bracket">2024 年 6 月真题</div>
                    </div>
                    <div class="mu-exam-side">
                      <div class="mu-timer"><span class="mu-timer-dot"></span>00:37:52</div>
                      <div class="mu-score-ring">
                        <div class="mu-score-inner">
                          <b>85</b>
                          <span>分</span>
                        </div>
                      </div>
                      <div class="mu-verdict"><i>✓</i> AI 已分析 3 处错因</div>
                    </div>
                  </div>

                  <!-- ===== 每日任务：任务清单 + 掌握度 ===== -->
                  <div v-else-if="slide.type === 'daily'" class="mockup mockup-daily">
                    <div class="mu-hud-row">
                      <span class="mu-hud">DAY 7 / 14 · 基础期</span>
                      <span class="mu-hud mu-hud-accent">今日任务</span>
                    </div>
                    <div class="mu-task-card">
                      <div class="mu-task-row done">
                        <span class="mu-check">✓</span>
                        <div class="mu-task-text w1"></div>
                        <span class="mu-tag green">掌握度 92%</span>
                      </div>
                      <div class="mu-task-row doing">
                        <span class="mu-check pulse"></span>
                        <div class="mu-task-text w2"></div>
                        <span class="mu-tag blue">进行中</span>
                      </div>
                      <div class="mu-task-row">
                        <span class="mu-check"></span>
                        <div class="mu-task-text w3"></div>
                        <span class="mu-tag grey">待学</span>
                      </div>
                    </div>
                    <div class="mu-daily-actions">
                      <span class="mu-btn">📖 学习讲解</span>
                      <span class="mu-btn primary">✏️ 去练习</span>
                      <span class="mu-btn">🎬 视频推送</span>
                    </div>
                  </div>

                  <!-- ===== 小基：形象 + 聊天气泡 ===== -->
                  <div v-else-if="slide.type === 'xiaoji'" class="mockup mockup-xiaoji">
                    <div class="mu-xiaoji-wrap">
                      <img src="/images/xiaoji/xiaoji_idle.png" alt="小基" class="mu-xiaoji-img" />
                      <div class="mu-xiaoji-ring"></div>
                    </div>
                    <div class="mu-bubble-stack">
                      <div class="mu-bubble user">这道题的考点是什么？</div>
                      <div class="mu-bubble ai">这是虚拟语气的常见考法，先看时态标记…</div>
                      <div class="mu-bubble ai typing"><span></span><span></span><span></span></div>
                    </div>
                  </div>

                  <!-- ===== 社区与学程：动态卡 + 排行榜 + 段位 ===== -->
                  <div v-else-if="slide.type === 'community'" class="mockup mockup-community">
                    <div class="mu-post-card">
                      <div class="mu-post-head">
                        <span class="mu-avatar"></span>
                        <span class="mu-post-name"></span>
                        <span class="mu-like">♥ 128</span>
                      </div>
                      <div class="mu-post-body"></div>
                    </div>
                    <div class="mu-podium">
                      <div class="mu-podium-item p2"><b>2</b><span class="mu-bar-podium h2"></span></div>
                      <div class="mu-podium-item p1"><b>1</b><span class="mu-bar-podium h1"></span><i class="mu-crown">♛</i></div>
                      <div class="mu-podium-item p3"><b>3</b><span class="mu-bar-podium h3"></span></div>
                    </div>
                    <div class="mu-rank-badge">段位 · 破晓 Lv.6</div>
                  </div>

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
            @click="scrollToFeature(slide.type)"
          >
            <div class="feature-icon" v-html="slide.iconSvg"></div>
            <h3>{{ slide.featureTitle }}</h3>
            <p>{{ slide.featureDesc }}</p>
          </div>
        </div>
      </div>

      <!-- ===== 数字条 ===== -->
      <div class="stats-section reveal">
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-num"><span data-count="17">0</span></div>
            <div class="stat-label">考试考纲</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-num"><span data-count="19338">0</span></div>
            <div class="stat-label">题库题目</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-num"><span data-count="12">0</span></div>
            <div class="stat-label">国家考试真题卷</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-num"><span data-count="11">0</span></div>
            <div class="stat-label">支持题型</div>
          </div>
        </div>
      </div>

      <!-- ===== 三步流程 ===== -->
      <div class="how-section reveal" id="how">
        <h2 class="section-title">三步开始你的备考</h2>
        <p class="section-sub">从选考纲到真题冲刺，全程 AI 陪伴</p>
        <div class="how-grid">
          <div class="how-step reveal d1">
            <div class="how-num">01</div>
            <h3>选考纲</h3>
            <p>17 个高频考试任选一门：四六级、考研、法考、公务员、教资、CPA……都有覆盖</p>
          </div>
          <div class="how-arrow">→</div>
          <div class="how-step reveal d2">
            <div class="how-num">02</div>
            <h3>AI 摸底诊断</h3>
            <p>答一轮诊断题，设定目标分数和周期，AI 生成「基础 → 强化 → 冲刺」三阶段计划</p>
          </div>
          <div class="how-arrow">→</div>
          <div class="how-step reveal d3">
            <div class="how-num">03</div>
            <h3>每日任务 + 真题冲刺</h3>
            <p>每天跟着任务学讲解、做练习，最后用真题卷检验，交卷即出 AI 错因分析</p>
          </div>
        </div>
      </div>

      <!-- ===== 功能深展区 ===== -->
      <div class="features-deep" id="features">
        <div
          v-for="(slide, idx) in slides"
          :key="'feat-' + slide.type"
          class="feat-block reveal"
          :class="idx % 2 === 0 ? 'left-text' : 'right-text'"
          :id="'feat-' + slide.type"
        >
          <div class="feat-text">
            <span class="feat-hud">{{ String(idx + 1).padStart(2, '0') }} / {{ slide.label }}</span>
            <h3>{{ slide.featureTitle }}</h3>
            <p class="feat-desc">{{ slide.deepDesc }}</p>
            <ul class="feat-points">
              <li v-for="(p, pi) in slide.points" :key="pi"><i>✓</i>{{ p }}</li>
            </ul>
            <router-link :to="slide.cta.to" class="feat-cta magnet">{{ slide.cta.label }} <span>→</span></router-link>
          </div>
          <div class="feat-visual">
            <!-- 学科计划 -->
            <div v-if="slide.type === 'plan'" class="fv-inner">
              <div class="mu-chip-grid fv-chips">
                <span v-for="(c, i) in ['CET-4', '考研', '法考', '公务员']" :key="i" class="mu-chip" :class="'c' + i">{{ c }}</span>
              </div>
              <div class="mu-phases">
                <div class="mu-phase done"><i>✓</i>基础期</div>
                <div class="mu-phase-line done"></div>
                <div class="mu-phase active"><i>◆</i>强化期</div>
                <div class="mu-phase-line"></div>
                <div class="mu-phase"><i>○</i>冲刺期</div>
              </div>
              <div class="mu-plan-footer fv-bar">
                <span class="mu-hud">AI 正在生成你的专属计划…</span>
                <div class="mu-bar"><div class="mu-bar-fill"></div></div>
              </div>
            </div>
            <!-- 真题套卷 -->
            <div v-else-if="slide.type === 'exam'" class="fv-inner fv-row">
              <div class="mu-exam-paper fv-paper">
                <div class="mu-paper-title"></div>
                <div class="mu-paper-line" v-for="n in 3" :key="'pl' + n"></div>
                <div class="mu-paper-line short"></div>
                <div class="mu-paper-bracket">2024 年 6 月真题</div>
              </div>
              <div class="mu-exam-side">
                <div class="mu-score-ring">
                  <div class="mu-score-inner"><b>85</b><span>分</span></div>
                </div>
                <div class="mu-verdict"><i>✓</i> AI 已分析错因</div>
              </div>
            </div>
            <!-- 每日任务 -->
            <div v-else-if="slide.type === 'daily'" class="fv-inner">
              <div class="mu-task-card fv-task">
                <div class="mu-task-row done">
                  <span class="mu-check">✓</span>
                  <div class="mu-task-text w1"></div>
                  <span class="mu-tag green">92%</span>
                </div>
                <div class="mu-task-row doing">
                  <span class="mu-check pulse"></span>
                  <div class="mu-task-text w2"></div>
                  <span class="mu-tag blue">进行中</span>
                </div>
                <div class="mu-task-row">
                  <span class="mu-check"></span>
                  <div class="mu-task-text w3"></div>
                  <span class="mu-tag grey">待学</span>
                </div>
              </div>
              <div class="mu-daily-actions fv-actions">
                <span class="mu-btn">📖 学习讲解</span>
                <span class="mu-btn primary">✏️ 去练习</span>
              </div>
            </div>
            <!-- 小基 -->
            <div v-else-if="slide.type === 'xiaoji'" class="fv-inner fv-row">
              <div class="mu-xiaoji-wrap fv-xiaoji">
                <img src="/images/xiaoji/xiaoji_idle.png" alt="小基" class="mu-xiaoji-img" />
                <div class="mu-xiaoji-ring"></div>
              </div>
              <div class="mu-bubble-stack fv-bubbles">
                <div class="mu-bubble user">这道题怎么做？</div>
                <div class="mu-bubble ai">先看考点：虚拟语气，时态要往前提一格…</div>
              </div>
            </div>
            <!-- 社区与学程 -->
            <div v-else-if="slide.type === 'community'" class="fv-inner">
              <div class="mu-podium">
                <div class="mu-podium-item p2"><b>2</b><span class="mu-bar-podium h2"></span></div>
                <div class="mu-podium-item p1"><i class="mu-crown">♛</i><b>1</b><span class="mu-bar-podium h1"></span></div>
                <div class="mu-podium-item p3"><b>3</b><span class="mu-bar-podium h3"></span></div>
              </div>
              <div class="mu-rank-badge">段位 · 破晓 Lv.6 · 排行榜</div>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== FAQ ===== -->
      <div class="faq-section reveal" id="faq">
        <h2 class="section-title">常见问题</h2>
        <p class="section-sub">还有疑问？注册后随时问小基</p>
        <div class="faq-list">
          <div
            v-for="(f, fi) in faqList"
            :key="fi"
            class="faq-item"
            :class="{ open: openFaq === fi }"
            @click="toggleFaq(fi)"
          >
            <div class="faq-q">
              <span>{{ f.q }}</span>
              <i class="faq-toggle" :class="{ open: openFaq === fi }">+</i>
            </div>
            <div class="faq-a-wrap">
              <div class="faq-a-inner">
                <p class="faq-a">{{ f.a }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 旅程轨道线（滚动进度） ===== -->
      <svg class="journey-rail" viewBox="0 0 24 1000" preserveAspectRatio="none" aria-hidden="true">
        <line class="rail-track" x1="12" y1="0" x2="12" y2="1000" />
        <line class="rail-fill" x1="12" y1="0" x2="12" y2="0" />
        <circle class="rail-dot" cx="12" cy="60" r="5" />
        <circle class="rail-dot" cx="12" cy="340" r="5" />
        <circle class="rail-dot" cx="12" cy="640" r="5" />
        <circle class="rail-dot" cx="12" cy="940" r="5" />
      </svg>

      <!-- ===== 小基伴游 ===== -->
      <button class="xiaoji-companion" @click="goRegister" aria-label="小基">
        <img src="/images/xiaoji/xiaoji_happy.png" alt="" />
        <span class="xiaoji-bubble">注册后就能和我聊天啦</span>
      </button>

      <!-- ===== 光标光效 ===== -->
      <div class="cursor-glow" ref="glowEl"></div>

      <!-- ===== 底部 ===== -->
      <div class="landing-footer">
        <div class="footer-top">
          <div class="footer-brand">
            <img src="/logo.png" alt="基智" class="footer-logo" />
            <div>
              <b>基智学习助手</b>
              <p>选一门考试，AI 陪你学到上岸</p>
            </div>
          </div>
          <div class="footer-links">
            <router-link to="/qa">帮助中心</router-link>
            <router-link to="/open-source">开源文档</router-link>
            <a href="#" @click.prevent="scrollTo('faq')">常见问题</a>
          </div>
        </div>
        <div class="footer-bottom">
          <span>© 2026 基智学习助手 · 17 考纲 · 19,000+ 题库 · 12 套真题 · 全程免费</span>
          <a class="icp" href="https://beian.miit.gov.cn/" target="_blank" rel="noopener">粤ICP备2026109012号-2</a>
        </div>
      </div>
    </div>
  </WaterBackground>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import WaterBackground from '@/components/WaterBackground.vue'
import Starfield from '@/components/Starfield.vue'
import { useThemeStore } from '@/stores/theme'

const router = useRouter()
const themeStore = useThemeStore()

// 落地页专属（2026-09-03 用户拍板）：仅落地页跟随系统明暗，摘下四轴定制变量，无任何可改入口；
// setup 阶段即切换（先于子组件渲染，避免 Starfield 首帧闪错明暗），离开时恢复应用主题
themeStore.enterLanding()

// ===== 5 个轮播 + 数据 =====
const slides = [
  {
    type: 'plan',
    label: '学科计划',
    desc: '17 个考试考纲全覆盖：四六级、考研、雅思托福、法考、公务员、教资、CPA、计算机二级……选一门开始，AI 摸底诊断，生成「基础 → 强化 → 冲刺」三阶段专属备考计划。',
    tags: ['17 考纲', 'AI 摸底诊断', '三阶段计划'],
    iconSvg: `<svg viewBox="0 0 24 24" width="28" height="28"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.8" fill="none"/><path d="M15.5 8.5l-2.1 4.9-4.9 2.1 2.1-4.9 4.9-2.1z" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linejoin="round"/></svg>`,
    featureTitle: '学科计划',
    featureDesc: '17 考纲 · AI 诊断 · 三阶段计划',
    deepDesc: '覆盖四六级、考研、法考、公务员等 17 个高频考试。摸底诊断后 AI 生成「基础 → 强化 → 冲刺」三阶段计划，每个任务带真实题目，可查可练。',
    points: ['17 个考纲任选，题库 19,000+ 随时练', '摸底诊断 → AI 生成三阶段专属计划', '知识点掌握度实时更新，薄弱点一目了然'],
    cta: { label: '看看考纲', to: '/subject-plan' },
  },
  {
    type: 'exam',
    label: '真题套卷',
    desc: '12 套国家考试真题：CET-4/6、考研英数政、法考、教资、CPA、计算机二级、公务员行测。做题模式计时交卷，客观自动判分、主观 AI 批改，交卷后 AI 逐题分析错因。',
    tags: ['12 套真题', '计时交卷', 'AI 错因分析'],
    iconSvg: `<svg viewBox="0 0 24 24" width="28" height="28"><path d="M6 2h8l4 4v16H6z" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linejoin="round"/><path d="M14 2v4h4" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linejoin="round"/><path d="M9 14l2 2 4-4" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
    featureTitle: '真题套卷',
    featureDesc: '12 套真题 · 自动判分 · AI 错因分析',
    deepDesc: '12 套国家考试真题：做题模式计时交卷、客观自动判分、主观 AI 批改；解析模式回看你的答案、正确率和 AI 错因分析。',
    points: ['CET-4/6、考研英数政、法考、教资、CPA 全覆盖', '交卷即出分，含分区得分明细', '错题 AI 逐题分析，解析模式秒开'],
    cta: { label: '浏览真题', to: '/subject-plan' },
  },
  {
    type: 'daily',
    label: '每日任务',
    desc: '计划生成后每天都有安排：AI 按当日题目生成学习讲解，练习带真实题目，完成即更新知识点掌握度。学一天是一天，进步看得见。',
    tags: ['每日讲解', '真实题目', '掌握度'],
    iconSvg: `<svg viewBox="0 0 24 24" width="28" height="28"><rect x="3" y="5" width="18" height="16" rx="2" stroke="currentColor" stroke-width="1.8" fill="none"/><path d="M3 9h18" stroke="currentColor" stroke-width="1.8"/><path d="M9 13l2 2 4-4" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
    featureTitle: '每日任务',
    featureDesc: '每日讲解 · 去练习 · 掌握度看板',
    deepDesc: '计划生成后每天自动解锁任务：AI 按当日题目生成学习讲解并缓存，练习带真实题目，做完即更新掌握度，每天进步看得见。',
    points: ['AI 学习讲解：目标 / 知识点 / 方法 / 易错点', '练习带真实题目，不重复不遗漏', '阶段标签：基础期绿 · 强化期橙 · 冲刺期红'],
    cta: { label: '了解每日任务', to: '/subject-plan' },
  },
  {
    type: 'xiaoji',
    label: 'AI伙伴小基',
    desc: '专属 AI 学习伙伴，支持文字聊天、语音、图片理解、聊天记录搜索。学习中遇到任何问题，随时呼叫小基。',
    tags: ['AI 伙伴', '语音 · 图片', '记录搜索'],
    iconSvg: `<svg viewBox="0 0 24 24" width="28" height="28"><rect x="2" y="4" width="20" height="16" rx="2" stroke="currentColor" stroke-width="1.8" fill="none"/><circle cx="9" cy="12" r="1.5" fill="currentColor"/><circle cx="15" cy="12" r="1.5" fill="currentColor"/><path d="M8 16s1.5 1.5 4 1.5 4-1.5 4-1.5" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round"/></svg>`,
    featureTitle: 'AI伙伴小基',
    featureDesc: '聊天 / 语音 / 图片理解 / 记录搜索',
    deepDesc: '专属 AI 学习伙伴：文字聊天、语音、图片理解、聊天记录搜索。学习中卡壳了，随时呼叫小基，它记得你问过的一切。',
    points: ['语音通话 + 文字聊天，随时答疑', '图片理解：拍下题目直接问', '聊天记录实时搜索，问过的都能找回'],
    cta: { label: '认识小基', to: '/home' },
  },
  {
    type: 'community',
    label: '社区与学程',
    desc: '学习社区发布动态、点赞评论、好友私聊、排行榜；学程系统记录学习数据，段位、成就、任务一路升级。和考友一起，学习不再孤单。',
    tags: ['学习社区', '好友排行', '段位成就'],
    iconSvg: `<svg viewBox="0 0 24 24" width="28" height="28"><circle cx="9" cy="8" r="3" stroke="currentColor" stroke-width="1.8" fill="none"/><path d="M3.5 19c.7-3 2.8-4.5 5.5-4.5s4.8 1.5 5.5 4.5" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round"/><circle cx="17" cy="9" r="2.2" stroke="currentColor" stroke-width="1.8" fill="none"/><path d="M15.5 14.6c2.4.2 4 1.6 4.7 4.4" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round"/></svg>`,
    featureTitle: '社区与学程',
    featureDesc: '分享 · 排行 · 成就，学习不孤单',
    deepDesc: '发布学习动态、和考友互相关注私聊、查看排行榜；学程系统记录你的做题数据，段位、成就、任务一路升级。',
    points: ['动态广场 + 好友私聊 + 排行榜', '段位 / 等级 / 成就 / 任务四大成长线', '学习打卡、倒计时、计时器工具箱'],
    cta: { label: '了解学程', to: '/community' },
  },
]

// ===== 访客向 FAQ =====
const faqList = [
  { q: '基智学习助手是什么？收费吗？', a: '基智学习助手是一个 AI 备考平台：覆盖 17 个高频考试考纲、19,000+ 题库、12 套国家考试真题。选考纲 → AI 摸底诊断生成三阶段备考计划 → 每日任务 → 真题冲刺，全程免费。' },
  { q: '支持哪些考试？', a: 'CET-4/6、考研英语/数学/政治、雅思、托福、计算机二级（Python/C/Office）、教师资格证、法律职业资格、公务员行测、CPA、普通话、ACM/算法等 17 个考纲，均可直接开始。' },
  { q: '备考计划是怎么生成的？', a: '先做一轮摸底诊断（按考纲维度抽题），再设定目标分数、备考周期和每日学习时长，AI 结合你的答卷生成「基础期 → 强化期 → 冲刺期」三阶段计划，每个任务都带真实题目。' },
  { q: '每日任务是什么？', a: '计划生成后每天自动解锁任务：AI 按当天题目实时生成学习讲解（目标/知识点/方法/易错点），「去练习」带真实题目，做完即更新知识点掌握度。' },
  { q: '真题卷是真的吗？怎么批改？', a: '12 套真题来自教育部等国家部委组织的公开考试（CET-4/6、考研、法考、教资、CPA、计算机二级、公务员行测）。做题模式计时交卷：客观题自动判分、主观题 AI 批改，交卷后 AI 逐题分析错因。' },
  { q: '怎么登录？', a: '邮箱注册/登录，也可以微信扫码登录；小程序端支持微信登录并绑定网页账号，两端数据互通。' },
  { q: '遇到问题找谁？', a: '站内帮助中心有 29 条常见问题；也可以随时在对话里问小基 AI；意见反馈入口在侧边栏底部，我们会认真看每一条。' },
]

// ===== FAQ 手风琴 =====
const openFaq = ref(-1)
function toggleFaq(i) {
  openFaq.value = openFaq.value === i ? -1 : i
}

// ===== 锚点滚动 =====
function scrollTo(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
function scrollToFeature(type) {
  scrollTo('feat-' + type)
}

const currentSlide = ref(0)
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

function goLogin() {
  router.push('/login')
}

function goRegister() {
  router.push('/login?tab=register')
}

// ===== 滚动入场 + 数字滚动 =====
let revealObserver = null
function animateCount(el, target) {
  const dur = 1000
  const start = performance.now()
  const step = (now) => {
    const p = Math.min((now - start) / dur, 1)
    const eased = 1 - Math.pow(1 - p, 3)
    el.textContent = Math.round(target * eased).toLocaleString()
    if (p < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}

// ===== 科幻交互 =====
const starfieldRef = ref(null)
const glowEl = ref(null)
const finePointer = typeof window !== 'undefined' && window.matchMedia('(hover: hover) and (pointer: fine)').matches
const reducedMotion = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

// --- 打字机：轮播考试名 ---
const typeList = ['CET-4', '考研', '法考', '公务员', '教资', 'CPA']
const typedText = ref('')
let typeTimer = null
function startTypewriter() {
  let li = 0, ci = 0, deleting = false
  const tick = () => {
    const word = typeList[li]
    if (!deleting) {
      ci++
      typedText.value = word.slice(0, ci)
      if (ci >= word.length) { deleting = true; typeTimer = setTimeout(tick, 1500); return }
      typeTimer = setTimeout(tick, 90 + Math.random() * 100)
    } else {
      ci--
      typedText.value = word.slice(0, ci)
      if (ci <= 0) { deleting = false; li = (li + 1) % typeList.length; typeTimer = setTimeout(tick, 350); return }
      typeTimer = setTimeout(tick, 45)
    }
  }
  tick()
}

// --- 考试倒计时 ---
const examDeadlines = [
  { name: '四六级', date: '2026-12-19' },
  { name: '考研初试', date: '2026-12-26' },
]
const countdowns = computed(() => examDeadlines.map((e) => {
  const days = Math.ceil((new Date(e.date) - Date.now()) / 86400000)
  return `${e.name} ${e.date} · 还有 ${days} 天`
}))

// --- 光标光效（rAF 平滑跟随） ---
let glowX = -9999, glowY = -9999, glowTx = -9999, glowTy = -9999
let glowRaf = null
function onGlowMove(e) { glowTx = e.clientX; glowTy = e.clientY }
function glowLoop() {
  glowX += (glowTx - glowX) * 0.09
  glowY += (glowTy - glowY) * 0.09
  if (glowEl.value) glowEl.value.style.transform = `translate3d(${glowX - 210}px, ${glowY - 210}px, 0)`
  glowRaf = requestAnimationFrame(glowLoop)
}

// --- 磁性按钮 ---
function onMagnetMove(e) {
  document.querySelectorAll('.magnet').forEach((el) => {
    const r = el.getBoundingClientRect()
    const cx = r.left + r.width / 2
    const cy = r.top + r.height / 2
    const dx = e.clientX - cx
    const dy = e.clientY - cy
    const dist = Math.hypot(dx, dy)
    if (dist < 120 && dist > 0) {
      const f = (1 - dist / 120) * 10
      el.style.transform = `translate(${(dx / dist) * f}px, ${(dy / dist) * f}px)`
    } else {
      el.style.transform = ''
    }
  })
}

// --- 旅程轨道线（滚动进度） ---
let railFillEl = null
let railDots = []
let scrollRaf = null
function updateRail() {
  const max = document.documentElement.scrollHeight - window.innerHeight
  const p = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0
  if (railFillEl) railFillEl.setAttribute('y2', String(p * 1000))
  const ats = [0.02, 0.32, 0.62, 0.95]
  railDots.forEach((d, i) => d.classList.toggle('lit', p >= ats[i]))
}
function onScrollRail() {
  if (scrollRaf) return
  scrollRaf = requestAnimationFrame(() => { scrollRaf = null; updateRail() })
}

// --- 彩蛋：连点 logo 5 次 → 流星雨 ---
let logoTaps = 0
let logoTimer = null
function onLogoClick() {
  logoTaps++
  clearTimeout(logoTimer)
  logoTimer = setTimeout(() => { logoTaps = 0 }, 1500)
  if (logoTaps >= 5) {
    logoTaps = 0
    starfieldRef.value?.meteorShower()
  }
}

function initSciFi() {
  if (!reducedMotion) {
    if (finePointer) {
      window.addEventListener('mousemove', onGlowMove, { passive: true })
      window.addEventListener('mousemove', onMagnetMove, { passive: true })
      glowRaf = requestAnimationFrame(glowLoop)
    }
    startTypewriter()
  }
  railFillEl = document.querySelector('.rail-fill')
  railDots = Array.from(document.querySelectorAll('.rail-dot'))
  window.addEventListener('scroll', onScrollRail, { passive: true })
  updateRail()
}

function cleanupSciFi() {
  if (typeTimer) clearTimeout(typeTimer)
  if (glowRaf) cancelAnimationFrame(glowRaf)
  if (scrollRaf) cancelAnimationFrame(scrollRaf)
  window.removeEventListener('mousemove', onGlowMove)
  window.removeEventListener('mousemove', onMagnetMove)
  window.removeEventListener('scroll', onScrollRail)
}

onMounted(() => {
  resetAutoPlay()

  revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (!e.isIntersecting) return
      e.target.classList.add('revealed')
      // 数字统计滚动
      e.target.querySelectorAll('[data-count]').forEach((el) => {
        if (el.dataset.done) return
        el.dataset.done = '1'
        animateCount(el, Number(el.dataset.count))
      })
      revealObserver.unobserve(e.target)
    })
  }, { threshold: 0.2 })
  document.querySelectorAll('.reveal').forEach((el) => revealObserver.observe(el))

  initSciFi()
})

onUnmounted(() => {
  if (autoPlayTimer) {
    clearInterval(autoPlayTimer)
    autoPlayTimer = null
  }
  if (revealObserver) revealObserver.disconnect()
  cleanupSciFi()
  themeStore.exitLanding()
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
  background: color-mix(in srgb, var(--brand) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--brand) 20%, transparent);
  color: var(--brand);
  font-size: 17px;
  padding: 10px 34px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.nav-btn-primary:hover {
  background: color-mix(in srgb, var(--brand) 20%, transparent);
}

.landing-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 40px;
  padding: 16px 0 12px;
  padding-left: 60px;
  position: relative;
}

.hero {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 560px;
  margin-left: 40px;
  position: relative;
  z-index: 1;
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
  background: linear-gradient(135deg, var(--brand), #7c6df0);
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
  background: linear-gradient(135deg, var(--brand), #7c6df0);
  border: none;
  color: #fff;
  font-size: 20px;
  font-weight: 500;
  padding: 18px 56px;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 24px color-mix(in srgb, var(--brand) 35%, transparent);
}
.cta-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 36px color-mix(in srgb, var(--brand) 45%, transparent);
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
.explore-btn {
  border: 1px solid rgba(96,165,250,.25);
  padding: 10px 26px;
  border-radius: 24px;
  background: rgba(96,165,250,.06);
}
.explore-btn:hover {
  color: var(--text-primary);
  border-color: rgba(96,165,250,.5);
  background: rgba(96,165,250,.1);
}

.screenshot-section {
  flex: 1.2;
  max-width: 780px;
  margin-right: -20px;
  animation: fadeInRight 0.9s ease both 0.2s;
  position: relative;
  z-index: 1;
}
.screenshot-frame {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
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
  border-color: color-mix(in srgb, var(--brand) 15%, transparent);
  box-shadow: 0 12px 60px color-mix(in srgb, var(--brand) 6%, transparent);
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
  background: radial-gradient(ellipse, color-mix(in srgb, var(--brand) 6%, transparent) 0%, transparent 70%);
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

/* ===== 轮播 mockup（纯 CSS 科幻面板） ===== */
.mockup {
  width: 100%;
  height: 100%;
  border-radius: 12px;
  position: relative;
  padding: 26px 28px 112px; /* 底部让位给字幕渐变 */
  display: flex;
  flex-direction: column;
  gap: 14px;
  background:
    radial-gradient(ellipse 80% 60% at 70% 15%, color-mix(in srgb, var(--brand) 12%, transparent) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 15% 90%, rgba(124, 109, 240, 0.12) 0%, transparent 60%),
    linear-gradient(160deg, #0e1728 0%, #0a1120 100%);
  border: 1px solid rgba(255,255,255,0.05);
  overflow: hidden;
}

/* HUD 文字 */
.mu-hud-row { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.mu-hud {
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 11px;
  letter-spacing: 2px;
  color: rgba(125, 211, 252, 0.75);
  white-space: nowrap;
}
.mu-hud-accent { color: rgba(167, 139, 250, 0.9); }

/* ---- 学科计划 ---- */
.mu-chip-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-top: 4px;
}
.mu-chip {
  display: flex; align-items: center; justify-content: center;
  height: 40px; border-radius: 10px;
  font-size: 13px; font-weight: 600;
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border: 1px solid rgba(255,255,255,0.08);
  animation: muFloat 5s ease-in-out infinite;
}
.mu-chip.c0 { color: #60a5fa; border-color: rgba(96,165,250,.25); animation-delay: 0s; }
.mu-chip.c1 { color: #a78bfa; border-color: rgba(167,139,250,.25); animation-delay: .6s; }
.mu-chip.c2 { color: #34d399; border-color: rgba(52,211,153,.25); animation-delay: 1.2s; }
.mu-chip.c3 { color: #fbbf24; border-color: rgba(251,191,36,.25); animation-delay: 1.8s; }

.mu-phases { display: flex; align-items: center; justify-content: center; gap: 10px; margin-top: auto; }
.mu-phase {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; color: rgba(148,163,184,.7);
  padding: 6px 14px; border-radius: 20px;
  border: 1px solid rgba(255,255,255,.08);
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  white-space: nowrap;
}
.mu-phase i { font-style: normal; font-size: 11px; }
.mu-phase.done { color: #34d399; border-color: rgba(52,211,153,.3); }
.mu-phase.active {
  color: #60a5fa;
  border-color: rgba(96,165,250,.4);
  animation: muGlow 2.2s ease-in-out infinite;
}
.mu-phase-line { width: 26px; height: 1px; background: color-mix(in srgb, var(--surface, #ffffff) 15%, transparent); }
.mu-phase-line.done { background: rgba(52,211,153,.5); }

.mu-plan-footer { display: flex; align-items: center; gap: 12px; margin-top: 6px; }
.mu-bar { flex: 1; height: 6px; border-radius: 3px; background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent); overflow: hidden; }
.mu-bar-fill {
  width: 100%; height: 100%; border-radius: 3px;
  background: linear-gradient(90deg, var(--brand), #7c6df0);
  transform-origin: left center;
  animation: muFill 3.2s cubic-bezier(0.4, 0, 0.2, 1) infinite alternate;
  box-shadow: 0 0 12px rgba(96,165,250,.5);
}

/* ---- 真题套卷 ---- */
.mockup-exam { flex-direction: row; align-items: stretch; gap: 18px; }
.mu-exam-paper {
  flex: 1.25;
  border-radius: 10px;
  background: color-mix(in srgb, var(--surface, #ffffff) 5.5%, transparent);
  border: 1px solid rgba(255,255,255,.1);
  padding: 20px 22px;
  display: flex; flex-direction: column; gap: 10px;
  animation: muFloat 6s ease-in-out infinite;
}
.mu-paper-title { width: 46%; height: 14px; border-radius: 4px; background: color-mix(in srgb, var(--surface, #ffffff) 16%, transparent); }
.mu-paper-line { width: 100%; height: 8px; border-radius: 4px; background: color-mix(in srgb, var(--surface, #ffffff) 7%, transparent); }
.mu-paper-line.short { width: 62%; }
.mu-paper-bracket {
  margin-top: auto; font-size: 12px; letter-spacing: 3px;
  color: rgba(148,163,184,.85); white-space: nowrap;
}
.mu-paper-bracket::before { content: '【 '; color: rgba(96,165,250,.7); }
.mu-paper-bracket::after { content: ' 】'; color: rgba(96,165,250,.7); }

.mu-exam-side {
  flex: 1;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 14px;
}
.mu-timer {
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 17px; letter-spacing: 3px;
  color: #7dd3fc;
  display: flex; align-items: center; gap: 8px;
}
.mu-timer-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: #f87171;
  box-shadow: 0 0 10px rgba(248,113,113,.8);
  animation: muBlink 1.4s ease-in-out infinite;
}
.mu-score-ring {
  width: 92px; height: 92px; border-radius: 50%;
  background: conic-gradient(#34d399 0 85%, rgba(255,255,255,.07) 85% 100%);
  display: flex; align-items: center; justify-content: center;
  animation: muGlow 2.4s ease-in-out infinite;
}
.mu-score-inner {
  width: 72px; height: 72px; border-radius: 50%;
  background: rgba(10,16,28,.9);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.mu-score-inner b { font-size: 24px; color: #34d399; font-family: 'Consolas', monospace; line-height: 1; }
.mu-score-inner span { font-size: 10px; color: rgba(148,163,184,.8); margin-top: 2px; }
.mu-verdict {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; color: rgba(52,211,153,.9);
  padding: 5px 12px; border-radius: 14px;
  background: rgba(52,211,153,.08); border: 1px solid rgba(52,211,153,.2);
  white-space: nowrap;
}
.mu-verdict i { font-style: normal; }

/* ---- 每日任务 ---- */
.mu-task-card {
  border-radius: 12px;
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  border: 1px solid rgba(255,255,255,.07);
  padding: 6px 14px;
  display: flex; flex-direction: column;
}
.mu-task-row { display: flex; align-items: center; gap: 12px; padding: 11px 2px; }
.mu-task-row + .mu-task-row { border-top: 1px solid rgba(255,255,255,.05); }
.mu-check {
  width: 20px; height: 20px; border-radius: 50%; flex-shrink: 0;
  border: 1.5px solid rgba(255,255,255,.2);
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; color: transparent;
}
.mu-task-row.done .mu-check { background: rgba(52,211,153,.15); border-color: #34d399; color: #34d399; }
.mu-check.pulse { border-color: rgba(96,165,250,.6); animation: muPulse 1.8s ease-in-out infinite; }
.mu-task-text { height: 9px; border-radius: 4px; background: color-mix(in srgb, var(--surface, #ffffff) 8%, transparent); }
.mu-task-text.w1 { width: 42%; }
.mu-task-text.w2 { width: 58%; }
.mu-task-text.w3 { width: 34%; }
.mu-tag { margin-left: auto; font-size: 10px; padding: 3px 10px; border-radius: 10px; flex-shrink: 0; }
.mu-tag.green { color: #34d399; background: rgba(52,211,153,.1); }
.mu-tag.blue { color: #60a5fa; background: rgba(96,165,250,.1); }
.mu-tag.grey { color: #94a3b8; background: rgba(148,163,184,.1); }
.mu-daily-actions { display: flex; gap: 10px; margin-top: auto; }
.mu-btn {
  flex: 1; text-align: center;
  font-size: 12px; padding: 10px 0; border-radius: 10px;
  color: #cbd5e1;
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border: 1px solid rgba(255,255,255,.09);
  white-space: nowrap;
}
.mu-btn.primary {
  color: #fff;
  background: linear-gradient(135deg, color-mix(in srgb, var(--brand) 35%, transparent), rgba(124,109,240,.35));
  border-color: rgba(124,109,240,.45);
  animation: muGlow 2.4s ease-in-out infinite;
}

/* ---- 小基 ---- */
.mockup-xiaoji { flex-direction: row; align-items: center; justify-content: center; gap: 26px; }
.mu-xiaoji-wrap { position: relative; width: 130px; height: 130px; flex-shrink: 0; }
.mu-xiaoji-img {
  width: 100%; height: 100%; object-fit: contain;
  animation: muFloat 4.5s ease-in-out infinite;
}
.mu-xiaoji-ring {
  position: absolute; inset: -8px; border-radius: 50%;
  border: 1.5px dashed rgba(96,165,250,.35);
  animation: muSpin 14s linear infinite;
}
.mu-bubble-stack { display: flex; flex-direction: column; gap: 10px; max-width: 60%; }
.mu-bubble {
  font-size: 13px; line-height: 1.5;
  padding: 9px 14px; border-radius: 14px;
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent);
  border: 1px solid rgba(255,255,255,.08);
  color: #cbd5e1;
}
.mu-bubble.user {
  align-self: flex-start;
  background: color-mix(in srgb, var(--brand) 16%, transparent);
  border-color: color-mix(in srgb, var(--brand) 30%, transparent);
  color: #dbeafe;
  border-bottom-left-radius: 4px;
}
.mu-bubble.ai { align-self: stretch; border-bottom-right-radius: 4px; }
.mu-bubble.typing { display: flex; gap: 5px; padding: 12px 14px; align-self: flex-start; }
.mu-bubble.typing span {
  width: 6px; height: 6px; border-radius: 50%;
  background: rgba(148,163,184,.8);
  animation: muBounce 1.2s ease-in-out infinite;
}
.mu-bubble.typing span:nth-child(2) { animation-delay: .15s; }
.mu-bubble.typing span:nth-child(3) { animation-delay: .3s; }

/* ---- 社区与学程 ---- */
.mockup-community { justify-content: flex-start; }
.mu-post-card {
  border-radius: 12px;
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border: 1px solid rgba(255,255,255,.08);
  padding: 12px 16px;
  animation: muFloat 6s ease-in-out infinite;
}
.mu-post-head { display: flex; align-items: center; gap: 10px; }
.mu-avatar {
  width: 26px; height: 26px; border-radius: 50%;
  background: linear-gradient(135deg, #f472b6, #fbbf24);
  flex-shrink: 0;
}
.mu-post-name { width: 70px; height: 9px; border-radius: 4px; background: color-mix(in srgb, var(--surface, #ffffff) 12%, transparent); }
.mu-like { margin-left: auto; font-size: 12px; color: #f87171; }
.mu-post-body { margin-top: 10px; height: 34px; border-radius: 8px; background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent); }
.mu-podium { display: flex; align-items: flex-end; justify-content: center; gap: 10px; margin-top: auto; }
.mu-podium-item { position: relative; display: flex; flex-direction: column; align-items: center; gap: 6px; padding-top: 16px; }
.mu-podium-item b {
  width: 24px; height: 24px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; color: #cbd5e1;
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent);
  border: 1px solid rgba(255,255,255,.12);
}
.mu-podium-item.p1 b { background: rgba(251,191,36,.15); border-color: rgba(251,191,36,.5); color: #fbbf24; }
.mu-bar-podium { width: 34px; border-radius: 6px 6px 0 0; background: color-mix(in srgb, var(--surface, #ffffff) 7%, transparent); }
.mu-bar-podium.h1 { height: 52px; background: linear-gradient(180deg, rgba(251,191,36,.35), rgba(251,191,36,.08)); }
.mu-bar-podium.h2 { height: 36px; }
.mu-bar-podium.h3 { height: 24px; }
.mu-crown {
  position: absolute; top: -2px; left: 50%; transform: translateX(-50%);
  font-style: normal; color: #fbbf24; font-size: 14px;
  text-shadow: 0 0 10px rgba(251,191,36,.6);
}
.mu-rank-badge {
  align-self: center;
  font-size: 12px; letter-spacing: 2px;
  color: #c4b5fd;
  padding: 6px 16px; border-radius: 16px;
  background: rgba(167,139,250,.1);
  border: 1px solid rgba(167,139,250,.3);
  animation: muGlow 2.8s ease-in-out infinite;
}

/* ---- mockup 动画 ---- */
@keyframes muFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-7px); }
}
@keyframes muGlow {
  0%, 100% { box-shadow: 0 0 8px rgba(96,165,250,.18); }
  50% { box-shadow: 0 0 22px rgba(96,165,250,.45); }
}
@keyframes muBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: .25; }
}
@keyframes muFill {
  from { transform: scaleX(.15); }
  to { transform: scaleX(1); }
}
@keyframes muPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(96,165,250,.35); }
  50% { box-shadow: 0 0 0 6px rgba(96,165,250,0); }
}
@keyframes muBounce {
  0%, 100% { transform: translateY(0); opacity: .5; }
  50% { transform: translateY(-4px); opacity: 1; }
}
@keyframes muSpin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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
  color: var(--brand);
  letter-spacing: 1px;
  background: color-mix(in srgb, var(--brand) 12%, transparent);
  padding: 2px 12px;
  border-radius: 20px;
  border: 1px solid color-mix(in srgb, var(--brand) 15%, transparent);
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
  background: linear-gradient(90deg, var(--brand), transparent);
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
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent);
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
    color-mix(in srgb, var(--brand) 1%, transparent) 2px,
    color-mix(in srgb, var(--brand) 1%, transparent) 4px
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
  background: color-mix(in srgb, var(--brand) 50%, transparent);
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
  background: color-mix(in srgb, var(--surface, #ffffff) 20%, transparent);
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
.carousel-dots .dot.active {
  background: var(--brand);
  width: 44px;
  box-shadow: 0 0 20px color-mix(in srgb, var(--brand) 30%, transparent);
}
.carousel-dots .dot:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 50%, transparent);
  transform: scaleY(1.8);
}
.carousel-dots .dot.active:hover {
  background: var(--brand);
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
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
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
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent);
  transform: translateY(-4px) scale(1.02);
  border-color: color-mix(in srgb, var(--brand) 15%, transparent);
  box-shadow: 0 4px 20px color-mix(in srgb, var(--brand) 4%, transparent);
}
.feature-card.active {
  border-color: var(--brand);
  background: color-mix(in srgb, var(--brand) 4%, transparent);
  box-shadow: 0 4px 20px color-mix(in srgb, var(--brand) 6%, transparent);
}
.feature-card:active {
  transform: scale(0.95);
}
[data-theme="dark"] .feature-card:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
}
[data-theme="dark"] .feature-card.active {
  border-color: var(--brand);
  background: color-mix(in srgb, var(--brand) 6%, transparent);
}

.feature-icon {
  color: var(--brand);
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
  filter: drop-shadow(0 0 12px color-mix(in srgb, var(--brand) 30%, transparent));
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

/* ===== 数字条 ===== */
.stats-section {
  flex-shrink: 0;
  padding: 22px 0;
  border-bottom: 1px solid var(--border-color);
}
.stats-grid { display: flex; align-items: center; justify-content: center; gap: 40px; flex-wrap: wrap; }
.stat-item { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.stat-num {
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 40px; font-weight: 700; line-height: 1.1;
  background: linear-gradient(135deg, #60a5fa, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.stat-label { font-size: 13px; color: var(--text-muted); letter-spacing: 1px; }
.stat-divider { width: 1px; height: 40px; background: color-mix(in srgb, var(--surface, #ffffff) 8%, transparent); }

/* ===== 三步流程 ===== */
.how-section { flex-shrink: 0; padding: 56px 0 20px; text-align: center; }
.section-title { font-size: 30px; font-weight: 700; color: var(--text-primary); margin: 0; }
.section-sub { font-size: 15px; color: var(--text-muted); margin: 10px 0 0; }
.how-grid { display: flex; align-items: stretch; justify-content: center; gap: 22px; margin-top: 36px; flex-wrap: wrap; }
.how-step {
  flex: 1; max-width: 300px; min-width: 220px;
  padding: 26px 22px; border-radius: 16px;
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  border: 1px solid rgba(255,255,255,.07);
  transition: transform .3s ease, border-color .3s ease, box-shadow .3s ease;
}
.how-step:hover { transform: translateY(-4px); border-color: rgba(96,165,250,.3); box-shadow: 0 8px 32px rgba(96,165,250,.1); }
.how-num {
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 26px; font-weight: 700;
  color: rgba(96,165,250,.9);
  letter-spacing: 2px;
}
.how-step h3 { font-size: 17px; color: var(--text-primary); margin: 12px 0 8px; }
.how-step p { font-size: 13px; line-height: 1.7; color: var(--text-secondary); margin: 0; }
.how-arrow { align-self: center; font-size: 22px; color: rgba(96,165,250,.5); }

/* ===== 功能深展区 ===== */
.features-deep { flex-shrink: 0; display: flex; flex-direction: column; gap: 44px; padding: 56px 0 24px; }
.feat-block { display: flex; align-items: center; gap: 48px; }
.feat-block.right-text { flex-direction: row-reverse; }
.feat-text { flex: 1; min-width: 0; }
.feat-hud {
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 12px; letter-spacing: 3px;
  color: rgba(96,165,250,.8);
}
.feat-text h3 { font-size: 24px; font-weight: 700; color: var(--text-primary); margin: 10px 0 12px; }
.feat-desc { font-size: 15px; line-height: 1.8; color: var(--text-secondary); margin: 0; }
.feat-points { list-style: none; margin: 18px 0 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.feat-points li { display: flex; align-items: center; gap: 10px; font-size: 14px; color: var(--text-secondary); }
.feat-points i {
  font-style: normal; font-size: 11px;
  width: 20px; height: 20px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  color: #34d399; background: rgba(52,211,153,.12);
  border: 1px solid rgba(52,211,153,.25);
}
.feat-cta {
  display: inline-flex; align-items: center; gap: 8px;
  margin-top: 22px; padding: 11px 26px;
  border-radius: 12px; font-size: 14px; font-weight: 500;
  color: #fff; text-decoration: none;
  background: linear-gradient(135deg, color-mix(in srgb, var(--brand) 25%, transparent), rgba(124,109,240,.25));
  border: 1px solid rgba(96,165,250,.35);
  transition: all .3s ease;
}
.feat-cta:hover { transform: translateY(-2px); box-shadow: 0 6px 24px rgba(96,165,250,.25); border-color: rgba(96,165,250,.6); }
.feat-cta span { transition: transform .3s ease; }
.feat-cta:hover span { transform: translateX(4px); }

.feat-visual {
  flex: 1; min-height: 300px;
  border-radius: 18px;
  padding: 26px;
  display: flex; align-items: center; justify-content: center;
  background:
    radial-gradient(ellipse 90% 70% at 70% 10%, color-mix(in srgb, var(--brand) 10%, transparent) 0%, transparent 60%),
    radial-gradient(ellipse 60% 60% at 15% 95%, rgba(124,109,240,.10) 0%, transparent 60%),
    linear-gradient(160deg, #0e1728 0%, #0a1120 100%);
  border: 1px solid rgba(255,255,255,.07);
  transition: transform .3s ease, border-color .3s ease, box-shadow .3s ease;
}
.feat-block:hover .feat-visual {
  transform: translateY(-4px);
  border-color: rgba(96,165,250,.25);
  box-shadow: 0 12px 44px color-mix(in srgb, var(--brand) 8%, transparent);
}
.fv-inner { width: 100%; display: flex; flex-direction: column; align-items: center; gap: 20px; }
.fv-row { flex-direction: row; }
.fv-chips { width: 100%; max-width: 340px; }
.fv-bar { width: 100%; max-width: 340px; }
.fv-paper { max-width: 230px; }
.fv-task { width: 100%; max-width: 340px; }
.fv-actions { width: 100%; max-width: 340px; }
.fv-xiaoji { width: 110px; height: 110px; }
.fv-bubbles { max-width: 70%; }

/* ===== FAQ ===== */
.faq-section { flex-shrink: 0; padding: 56px 0 24px; text-align: center; }
.faq-list { max-width: 760px; margin: 32px auto 0; display: flex; flex-direction: column; gap: 12px; text-align: left; }
.faq-item {
  border-radius: 14px;
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  border: 1px solid rgba(255,255,255,.07);
  cursor: pointer;
  transition: border-color .3s ease, background .3s ease;
}
.faq-item:hover { border-color: rgba(96,165,250,.25); }
.faq-item.open { border-color: rgba(96,165,250,.35); background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent); }
.faq-q {
  display: flex; align-items: center; justify-content: space-between; gap: 14px;
  padding: 16px 20px; font-size: 15px; font-weight: 600; color: var(--text-primary);
}
.faq-toggle {
  font-style: normal; font-size: 18px; color: var(--text-muted);
  transition: transform .3s ease; flex-shrink: 0;
}
.faq-toggle.open { transform: rotate(45deg); color: #60a5fa; }
.faq-a-wrap { display: grid; grid-template-rows: 0fr; transition: grid-template-rows .35s cubic-bezier(.22, 1, .36, 1); }
.faq-item.open .faq-a-wrap { grid-template-rows: 1fr; }
.faq-a-inner { overflow: hidden; }
.faq-a { margin: 0; padding: 0 20px 16px; font-size: 14px; line-height: 1.8; color: var(--text-secondary); }

/* ===== 页脚 ===== */
.landing-footer {
  flex-shrink: 0;
  padding: 26px 0 10px;
  border-top: 1px solid var(--border-color);
}
.footer-top { display: flex; align-items: center; justify-content: space-between; gap: 20px; flex-wrap: wrap; }
.footer-brand { display: flex; align-items: center; gap: 12px; }
.footer-logo { width: 40px; height: 40px; object-fit: contain; }
.footer-brand b { font-size: 15px; color: var(--text-primary); }
.footer-brand p { margin: 3px 0 0; font-size: 12px; color: var(--text-muted); }
.footer-links { display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
.footer-links a {
  font-size: 13px; color: var(--text-secondary);
  cursor: pointer; text-decoration: none;
  transition: color .3s ease;
}
.footer-links a:hover { color: var(--text-primary); }
.footer-bottom {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  flex-wrap: wrap;
  margin-top: 18px; padding-top: 14px;
  border-top: 1px solid rgba(255,255,255,.05);
  font-size: 12px; color: var(--text-muted);
}
.footer-bottom .icp {
  opacity: .8;
  color: inherit;
  text-decoration: none;
  transition: opacity .3s ease;
}
.footer-bottom .icp:hover { opacity: 1; }

/* ===== 科幻交互 ===== */
/* 打字机 HUD */
.hero-hud-line {
  display: flex; align-items: center; gap: 10px;
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 13px; letter-spacing: 1px;
  color: var(--text-muted);
  animation: fadeInUp 0.8s ease both 0.45s;
}
.hud-prompt { color: #4a90d9; }
.hud-typed { color: var(--text-primary); min-width: 3ch; }
.hud-caret { color: #60a5fa; animation: muBlink 1.4s ease-in-out infinite; }

/* 考试倒计时 */
.hero-countdown {
  display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
  margin-top: 2px;
  font-family: 'Consolas', 'Courier New', monospace;
  font-size: 12px; letter-spacing: 1px;
  animation: fadeInUp 0.8s ease both 0.55s;
}
.cd-label { color: var(--text-muted); letter-spacing: 3px; }
.cd-item {
  color: #4a90d9;
  background: rgba(96,165,250,.06);
  border: 1px solid rgba(96,165,250,.18);
  padding: 3px 12px; border-radius: 12px;
  white-space: nowrap;
}

/* 磁性按钮 */
.magnet { transition: transform .25s cubic-bezier(.22, 1, .36, 1); }

/* 光标光效 */
.cursor-glow {
  position: fixed; top: 0; left: 0;
  width: 420px; height: 420px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(96,165,250,.10) 0%, rgba(124,109,240,.05) 40%, transparent 68%);
  pointer-events: none; z-index: 30;
  will-change: transform;
  transform: translate3d(-9999px, -9999px, 0);
}

/* 旅程轨道线 */
.journey-rail {
  position: fixed;
  left: 20px;
  top: 50%;
  transform: translateY(-50%);
  height: 55vh;
  width: 22px;
  z-index: 40;
  pointer-events: none;
  opacity: .9;
}
.rail-track { stroke: rgba(120,140,180,.18); stroke-width: 2; }
.rail-fill {
  stroke: #60a5fa; stroke-width: 2;
  filter: drop-shadow(0 0 4px rgba(96,165,250,.8));
}
.rail-dot { fill: rgba(10,16,28,.9); stroke: rgba(120,140,180,.4); stroke-width: 1.5; transition: fill .3s ease, stroke .3s ease; }
.rail-dot.lit { fill: #60a5fa; stroke: #60a5fa; filter: drop-shadow(0 0 6px rgba(96,165,250,.9)); }

/* 小基伴游 */
.xiaoji-companion {
  position: fixed; right: 26px; bottom: 26px;
  width: 66px; height: 66px; border-radius: 50%;
  border: 1px solid rgba(96,165,250,.35);
  background: radial-gradient(circle at 30% 25%, rgba(96,165,250,.2), rgba(10,17,32,.88));
  box-shadow: 0 6px 30px rgba(96,165,250,.25);
  cursor: pointer; z-index: 60;
  display: flex; align-items: center; justify-content: center;
  padding: 7px;
  animation: xjFloat 3.5s ease-in-out infinite;
  transition: box-shadow .3s ease;
}
.xiaoji-companion:hover { box-shadow: 0 8px 44px rgba(96,165,250,.45); }
.xiaoji-companion img { width: 100%; height: 100%; object-fit: contain; }
.xiaoji-bubble {
  position: absolute; right: 74px; bottom: 12px;
  background: rgba(14,23,40,.92);
  border: 1px solid rgba(96,165,250,.3);
  color: #cbd5e1; font-size: 13px;
  padding: 9px 14px; border-radius: 12px 12px 4px 12px;
  white-space: nowrap;
  opacity: 0; pointer-events: none;
  transform: translateY(6px);
  transition: opacity .3s ease, transform .3s ease;
  animation: xjBubbleIn .4s cubic-bezier(.34, 1.56, .64, 1) 4s forwards;
}
.xiaoji-companion:hover .xiaoji-bubble { opacity: 1; transform: translateY(0); }
@keyframes xjFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-7px); }
}
@keyframes xjBubbleIn {
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 1200px) { .journey-rail { display: none; } }
@media (hover: none) {
  .cursor-glow { display: none; }
  .xiaoji-bubble { display: none; }
}

/* ===== 滚动入场 ===== */
.reveal {
  opacity: 0;
  transform: translateY(26px);
  transition: opacity .7s ease, transform .7s cubic-bezier(.22, 1, .36, 1);
}
.reveal.revealed { opacity: 1; transform: none; }
.reveal.d1 { transition-delay: .12s; }
.reveal.d2 { transition-delay: .24s; }
.reveal.d3 { transition-delay: .36s; }
@media (prefers-reduced-motion: reduce) {
  .reveal { opacity: 1; transform: none; transition: none; }
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
  .mockup { padding: 18px 18px 92px; }
  .mu-xiaoji-wrap { width: 96px; height: 96px; }
  .mu-bubble-stack { max-width: 100%; }
  .mu-chip { height: 32px; font-size: 11px; }
  .mu-chip-grid { gap: 6px; }
  .feat-block, .feat-block.right-text { flex-direction: column; gap: 22px; }
  .feat-visual { width: 100%; min-height: 240px; }
  .how-arrow { transform: rotate(90deg); }
  .stat-num { font-size: 30px; }
  .stats-grid { gap: 20px; }
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
  .mockup { padding: 14px 14px 84px; gap: 10px; }
  .mu-hud { font-size: 9px; letter-spacing: 1px; }
  .mu-chip-grid { grid-template-columns: repeat(2, 1fr); }
  .mockup-exam { gap: 10px; }
  .mu-exam-paper { padding: 14px 16px; }
  .mu-exam-side { gap: 8px; }
  .mu-score-ring { width: 68px; height: 68px; }
  .mu-score-inner { width: 54px; height: 54px; }
  .mu-score-inner b { font-size: 18px; }
  .mu-timer { font-size: 13px; letter-spacing: 1px; }
  .mu-xiaoji-wrap { width: 72px; height: 72px; }
  .mockup-xiaoji { gap: 14px; }
  .mu-bubble { font-size: 11px; padding: 7px 10px; }
  .mu-daily-actions { gap: 6px; }
  .mu-btn { font-size: 10px; padding: 8px 0; }
  .mu-phases { gap: 4px; }
  .mu-phase { font-size: 11px; padding: 5px 8px; }
  .mu-phase-line { width: 12px; }
  .section-title { font-size: 24px; }
  .stat-num { font-size: 24px; }
  .stat-divider { display: none; }
  .feat-text h3 { font-size: 20px; }
  .fv-xiaoji { width: 84px; height: 84px; }
  .fv-row { flex-direction: column; }
  .footer-top, .footer-bottom { flex-direction: column; align-items: flex-start; }
}
</style>