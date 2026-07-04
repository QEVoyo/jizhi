<template>
  <div class="community-profile-card">
    <!-- ===== 顶部 ===== -->
    <div class="profile-header">
      <div class="header-left">
        <h2>📋 我的资料卡</h2>
        <span class="header-subtitle">学习成果名片</span>
      </div>
      <div class="header-actions">
        <el-button size="small" @click="refreshData" :loading="refreshing">
          <i class="fas fa-sync"></i> 刷新
        </el-button>
        <el-button size="small" @click="openSettings">
          <i class="fas fa-sliders-h"></i> 自定义
        </el-button>
        <el-button size="small" @click="openPreview">
          <i class="fas fa-eye"></i> 预览
        </el-button>
        <el-button size="small" type="primary" @click="exportPDF" :loading="pdfExporting">
          <i class="fas fa-file-pdf"></i> 导出PDF
        </el-button>
        <el-button size="small" type="success" @click="exportImage" :loading="imageExporting">
          <i class="fas fa-image"></i> 导出图片
        </el-button>
      </div>
    </div>

    <el-divider />

    <!-- ===== 加载状态 ===== -->
    <div v-if="loading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i> 加载中...
    </div>

    <!-- ===== 资料卡内容 ===== -->
    <div v-else class="card-wrapper">
      <div class="card-content" ref="cardRef" id="profile-card-export">
        <!-- 强视觉几何背景 -->
        <svg class="geo-bg" viewBox="0 0 500 700" preserveAspectRatio="xMidYMid slice">
          <polygon points="0,0 160,0 80,140" fill="url(#grad1)" opacity="0.25" />
          <polygon points="500,0 340,0 420,140" fill="url(#grad2)" opacity="0.20" />
          <polygon points="0,700 160,700 80,560" fill="url(#grad3)" opacity="0.20" />
          <polygon points="500,700 340,700 420,560" fill="url(#grad4)" opacity="0.25" />
          <polygon points="250,80 290,140 250,200 210,140" fill="url(#grad5)" opacity="0.30" />
          <polygon points="120,350 150,400 120,450 90,400" fill="url(#grad1)" opacity="0.25" />
          <polygon points="380,300 410,350 380,400 350,350" fill="url(#grad2)" opacity="0.25" />
          <circle cx="250" cy="380" r="100" fill="none" stroke="url(#grad1)" stroke-width="4" opacity="0.35" />
          <circle cx="250" cy="380" r="130" fill="none" stroke="url(#grad2)" stroke-width="2" opacity="0.20" stroke-dasharray="8 12" />
          <circle cx="90" cy="200" r="50" fill="none" stroke="url(#grad3)" stroke-width="3" opacity="0.25" />
          <circle cx="410" cy="520" r="60" fill="none" stroke="url(#grad4)" stroke-width="3" opacity="0.25" />
          <rect x="30" y="30" width="80" height="80" rx="12" fill="url(#grad5)" opacity="0.15" />
          <rect x="390" y="30" width="60" height="60" rx="10" fill="url(#grad1)" opacity="0.15" />
          <rect x="30" y="550" width="60" height="60" rx="10" fill="url(#grad2)" opacity="0.15" />
          <rect x="400" y="600" width="50" height="50" rx="8" fill="url(#grad3)" opacity="0.15" />
          <line x1="0" y1="0" x2="500" y2="700" stroke="url(#grad1)" stroke-width="1.5" opacity="0.10" />
          <line x1="500" y1="0" x2="0" y2="700" stroke="url(#grad2)" stroke-width="1.5" opacity="0.10" />
          <circle cx="200" cy="100" r="3" fill="#409eff" opacity="0.20" />
          <circle cx="300" cy="160" r="3" fill="#8b5cf6" opacity="0.20" />
          <circle cx="150" cy="280" r="3" fill="#f472b6" opacity="0.20" />
          <circle cx="350" cy="240" r="3" fill="#409eff" opacity="0.20" />
          <circle cx="400" cy="440" r="3" fill="#8b5cf6" opacity="0.20" />
          <circle cx="100" cy="480" r="3" fill="#f472b6" opacity="0.20" />
          <circle cx="250" cy="560" r="3" fill="#409eff" opacity="0.20" />
          <circle cx="320" cy="620" r="3" fill="#8b5cf6" opacity="0.20" />

          <defs>
            <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:#409eff;stop-opacity:1" />
              <stop offset="100%" style="stop-color:#8b5cf6;stop-opacity:1" />
            </linearGradient>
            <linearGradient id="grad2" x1="0%" y1="100%" x2="100%" y2="0%">
              <stop offset="0%" style="stop-color:#f472b6;stop-opacity:1" />
              <stop offset="100%" style="stop-color:#409eff;stop-opacity:1" />
            </linearGradient>
            <linearGradient id="grad3" x1="100%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" style="stop-color:#34d399;stop-opacity:1" />
              <stop offset="100%" style="stop-color:#409eff;stop-opacity:1" />
            </linearGradient>
            <linearGradient id="grad4" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:#f59e0b;stop-opacity:1" />
              <stop offset="100%" style="stop-color:#ef4444;stop-opacity:1" />
            </linearGradient>
            <linearGradient id="grad5" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:#8b5cf6;stop-opacity:1" />
              <stop offset="100%" style="stop-color:#f472b6;stop-opacity:1" />
            </linearGradient>
          </defs>
        </svg>

        <!-- 光晕 -->
        <div class="glow glow-1"></div>
        <div class="glow glow-2"></div>
        <div class="glow glow-3"></div>
        <div class="glow glow-4"></div>

        <!-- 品牌头 -->
        <div class="card-brand">
          <img src="/logo.png" alt="基智" class="brand-logo" />
          <span class="brand-name">基智 · 学习成果卡</span>
          <span class="card-date">{{ generateDate }}</span>
        </div>

        <!-- 用户信息 -->
        <div class="user-section">
          <div class="user-avatar-wrapper">
            <el-avatar :size="72" :src="profile?.avatar_url || ''" class="user-avatar">
              {{ profile?.nickname?.[0] || 'U' }}
            </el-avatar>
            <div class="avatar-ring"></div>
          </div>
          <div class="user-info">
            <div class="user-name">{{ profile?.nickname || '用户' }}</div>
            <div class="user-account">{{ profile?.account || '未设置' }}</div>
            <div class="user-bio">{{ profile?.bio || '这个人很懒，什么都没写~' }}</div>
            <div class="user-meta">
              <span class="meta-badge level">Lv.{{ userLevel }}</span>
              <span class="meta-badge rank" :style="{ background: rankColor + '30', color: rankColor }">
                {{ rankIcon }} {{ rankName }} {{ rankSubSymbol }}
              </span>
              <span class="meta-badge points">⭐ {{ profile?.points || 0 }}</span>
            </div>
          </div>
        </div>

        <!-- 统计 -->
        <div class="stats-section">
          <div class="stat-item">
            <span class="stat-number">{{ profile?.points || 0 }}</span>
            <span class="stat-label">总积分</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-number">{{ totalDays }}</span>
            <span class="stat-label">学习天数</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-number">{{ achievementCount }}</span>
            <span class="stat-label">成就数</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-number">{{ checkinDays }}</span>
            <span class="stat-label">打卡天数</span>
          </div>
        </div>

        <!-- 知识点 -->
        <div class="mastery-section">
          <div class="section-header">
            <h4>📚 知识点掌握</h4>
            <span class="section-count">{{ displayedTopics.length }} / {{ allTopics.length }}</span>
          </div>
          <div v-if="!displayedTopics.length" class="empty-tip">暂无知识点</div>
          <div v-else class="topic-grid">
            <div
              v-for="item in displayedTopics"
              :key="item.topic"
              class="topic-card"
              :style="{
                background: `linear-gradient(145deg, ${getColor(item.mastery_score)}, ${getColorDark(item.mastery_score)})`,
                boxShadow: `0 4px 20px ${getColor(item.mastery_score)}60`
              }"
            >
              <span class="topic-name">{{ item.topic }}</span>
              <span class="topic-score">{{ item.mastery_score }}%</span>
              <span class="topic-badge">{{ getBadge(item.mastery_score) }}</span>
            </div>
          </div>
        </div>

        <!-- 成就 -->
        <div class="achievement-section">
          <div class="section-header">
            <h4>🏆 成就展示</h4>
            <span class="section-count">{{ displayedAchievements.length }} / {{ allAchievements.length }}</span>
          </div>
          <div v-if="!displayedAchievements.length" class="empty-tip">暂无成就</div>
          <div v-else class="achievement-grid">
            <div
              v-for="ach in displayedAchievements"
              :key="ach.id"
              class="achievement-item"
              :style="{ color: ach.themeColor || '#888' }"
            >
              <i :class="ach.icon || 'fas fa-trophy'"></i>
              <span class="ach-name">{{ ach.name }}</span>
            </div>
          </div>
        </div>

        <!-- 动态 -->
        <div class="activities-section">
          <div class="section-header">
            <h4>📈 近期动态</h4>
            <span class="section-count">{{ activities.length }} 条</span>
          </div>
          <div v-if="!activities.length" class="empty-tip">暂无动态</div>
          <div v-for="act in activities.slice(0, 5)" :key="act.id" class="activity-item">
            <span class="activity-icon">{{ getActivityIcon(act.action) }}</span>
            <span class="activity-text">{{ act.details?.text || act.action || '学习记录' }}</span>
            <span class="activity-time">{{ formatTime(act.created_at) }}</span>
          </div>
        </div>

        <!-- 底部 -->
        <div class="card-footer">
          <div class="footer-brand">
            <img src="/logo.png" alt="基智" class="footer-logo" />
            <span>基智学习助手</span>
          </div>
          <span class="footer-url">jizhi-learn.com</span>
        </div>
      </div>
    </div>

    <!-- 设置弹窗 -->
    <el-dialog
      v-model="settingsVisible"
      title="📋 自定义资料卡"
      width="600px"
      class="settings-dialog"
      destroy-on-close
    >
      <div class="settings-content">
        <div class="setting-group">
          <div class="setting-label">知识点卡片 <span class="setting-hint">最多 10 个</span></div>
          <div class="setting-items">
            <div
              v-for="item in allTopics"
              :key="item.topic"
              class="setting-item"
              :class="{ selected: tempSelectedTopics.includes(item.topic) }"
              @click="toggleTopic(item.topic)"
            >
              <span class="item-name">{{ item.topic }}</span>
              <span class="item-score" :style="{ color: getColor(item.mastery_score) }">
                {{ item.mastery_score }}%
              </span>
              <span v-if="tempSelectedTopics.includes(item.topic)" class="item-check">✓</span>
            </div>
          </div>
        </div>
        <div class="setting-group">
          <div class="setting-label">成就展示 <span class="setting-hint">最多 8 个</span></div>
          <div class="setting-items setting-achievements">
            <div
              v-for="ach in allAchievements"
              :key="ach.id"
              class="setting-item"
              :class="{ selected: tempSelectedAchievements.includes(ach.id) }"
              @click="toggleAchievement(ach.id)"
            >
              <i :class="ach.icon || 'fas fa-trophy'" :style="{ color: ach.themeColor || '#888' }"></i>
              <span class="item-name">{{ ach.name }}</span>
              <span v-if="tempSelectedAchievements.includes(ach.id)" class="item-check">✓</span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="settingsVisible = false">取消</el-button>
        <el-button type="primary" @click="saveSettings" :loading="savingSettings">确认更新</el-button>
      </template>
    </el-dialog>

    <!-- 预览弹窗 -->
    <el-dialog
      v-model="previewVisible"
      title="📷 预览资料卡"
      width="90%"
      class="preview-dialog"
      destroy-on-close
    >
      <div class="preview-content">
        <div class="preview-card" ref="previewRef">
          <div class="card-content preview-card-content" id="preview-card-export">
            <svg class="geo-bg" viewBox="0 0 500 700" preserveAspectRatio="xMidYMid slice">
              <polygon points="0,0 160,0 80,140" fill="url(#grad1)" opacity="0.25" />
              <polygon points="500,0 340,0 420,140" fill="url(#grad2)" opacity="0.20" />
              <polygon points="0,700 160,700 80,560" fill="url(#grad3)" opacity="0.20" />
              <polygon points="500,700 340,700 420,560" fill="url(#grad4)" opacity="0.25" />
              <polygon points="250,80 290,140 250,200 210,140" fill="url(#grad5)" opacity="0.30" />
              <polygon points="120,350 150,400 120,450 90,400" fill="url(#grad1)" opacity="0.25" />
              <polygon points="380,300 410,350 380,400 350,350" fill="url(#grad2)" opacity="0.25" />
              <circle cx="250" cy="380" r="100" fill="none" stroke="url(#grad1)" stroke-width="4" opacity="0.35" />
              <circle cx="250" cy="380" r="130" fill="none" stroke="url(#grad2)" stroke-width="2" opacity="0.20" stroke-dasharray="8 12" />
              <circle cx="90" cy="200" r="50" fill="none" stroke="url(#grad3)" stroke-width="3" opacity="0.25" />
              <circle cx="410" cy="520" r="60" fill="none" stroke="url(#grad4)" stroke-width="3" opacity="0.25" />
              <rect x="30" y="30" width="80" height="80" rx="12" fill="url(#grad5)" opacity="0.15" />
              <rect x="390" y="30" width="60" height="60" rx="10" fill="url(#grad1)" opacity="0.15" />
              <rect x="30" y="550" width="60" height="60" rx="10" fill="url(#grad2)" opacity="0.15" />
              <rect x="400" y="600" width="50" height="50" rx="8" fill="url(#grad3)" opacity="0.15" />
              <line x1="0" y1="0" x2="500" y2="700" stroke="url(#grad1)" stroke-width="1.5" opacity="0.10" />
              <line x1="500" y1="0" x2="0" y2="700" stroke="url(#grad2)" stroke-width="1.5" opacity="0.10" />
              <circle cx="200" cy="100" r="3" fill="#409eff" opacity="0.20" />
              <circle cx="300" cy="160" r="3" fill="#8b5cf6" opacity="0.20" />
              <circle cx="150" cy="280" r="3" fill="#f472b6" opacity="0.20" />
              <circle cx="350" cy="240" r="3" fill="#409eff" opacity="0.20" />
              <circle cx="400" cy="440" r="3" fill="#8b5cf6" opacity="0.20" />
              <circle cx="100" cy="480" r="3" fill="#f472b6" opacity="0.20" />
              <circle cx="250" cy="560" r="3" fill="#409eff" opacity="0.20" />
              <circle cx="320" cy="620" r="3" fill="#8b5cf6" opacity="0.20" />
              <defs>
                <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#409eff;stop-opacity:1" />
                  <stop offset="100%" style="stop-color:#8b5cf6;stop-opacity:1" />
                </linearGradient>
                <linearGradient id="grad2" x1="0%" y1="100%" x2="100%" y2="0%">
                  <stop offset="0%" style="stop-color:#f472b6;stop-opacity:1" />
                  <stop offset="100%" style="stop-color:#409eff;stop-opacity:1" />
                </linearGradient>
                <linearGradient id="grad3" x1="100%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" style="stop-color:#34d399;stop-opacity:1" />
                  <stop offset="100%" style="stop-color:#409eff;stop-opacity:1" />
                </linearGradient>
                <linearGradient id="grad4" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#f59e0b;stop-opacity:1" />
                  <stop offset="100%" style="stop-color:#ef4444;stop-opacity:1" />
                </linearGradient>
                <linearGradient id="grad5" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#8b5cf6;stop-opacity:1" />
                  <stop offset="100%" style="stop-color:#f472b6;stop-opacity:1" />
                </linearGradient>
              </defs>
            </svg>
            <div class="glow glow-1"></div>
            <div class="glow glow-2"></div>
            <div class="glow glow-3"></div>
            <div class="glow glow-4"></div>

            <div class="card-brand">
              <img src="/logo.png" alt="基智" class="brand-logo" />
              <span class="brand-name">基智 · 学习成果卡</span>
              <span class="card-date">{{ generateDate }}</span>
            </div>

            <div class="user-section">
              <div class="user-avatar-wrapper">
                <el-avatar :size="72" :src="profile?.avatar_url || ''" class="user-avatar">
                  {{ profile?.nickname?.[0] || 'U' }}
                </el-avatar>
                <div class="avatar-ring"></div>
              </div>
              <div class="user-info">
                <div class="user-name">{{ profile?.nickname || '用户' }}</div>
                <div class="user-account">{{ profile?.account || '未设置' }}</div>
                <div class="user-bio">{{ profile?.bio || '这个人很懒，什么都没写~' }}</div>
                <div class="user-meta">
                  <span class="meta-badge level">Lv.{{ userLevel }}</span>
                  <span class="meta-badge rank" :style="{ background: rankColor + '30', color: rankColor }">
                    {{ rankIcon }} {{ rankName }} {{ rankSubSymbol }}
                  </span>
                  <span class="meta-badge points">⭐ {{ profile?.points || 0 }}</span>
                </div>
              </div>
            </div>

            <div class="stats-section">
              <div class="stat-item"><span class="stat-number">{{ profile?.points || 0 }}</span><span class="stat-label">总积分</span></div>
              <div class="stat-divider"></div>
              <div class="stat-item"><span class="stat-number">{{ totalDays }}</span><span class="stat-label">学习天数</span></div>
              <div class="stat-divider"></div>
              <div class="stat-item"><span class="stat-number">{{ achievementCount }}</span><span class="stat-label">成就数</span></div>
              <div class="stat-divider"></div>
              <div class="stat-item"><span class="stat-number">{{ checkinDays }}</span><span class="stat-label">打卡天数</span></div>
            </div>

            <div class="mastery-section">
              <h4>📚 知识点掌握</h4>
              <div class="topic-grid">
                <div v-for="item in displayedTopics" :key="item.topic" class="topic-card" :style="{
                  background: `linear-gradient(145deg, ${getColor(item.mastery_score)}, ${getColorDark(item.mastery_score)})`,
                  boxShadow: `0 4px 20px ${getColor(item.mastery_score)}60`
                }">
                  <span class="topic-name">{{ item.topic }}</span>
                  <span class="topic-score">{{ item.mastery_score }}%</span>
                  <span class="topic-badge">{{ getBadge(item.mastery_score) }}</span>
                </div>
              </div>
            </div>

            <div class="achievement-section">
              <h4>🏆 成就展示</h4>
              <div class="achievement-grid">
                <div v-for="ach in displayedAchievements" :key="ach.id" class="achievement-item" :style="{ color: ach.themeColor || '#888' }">
                  <i :class="ach.icon || 'fas fa-trophy'"></i>
                  <span class="ach-name">{{ ach.name }}</span>
                </div>
              </div>
            </div>

            <div class="activities-section">
              <h4>📈 近期动态</h4>
              <div v-for="act in activities.slice(0, 5)" :key="act.id" class="activity-item">
                <span class="activity-icon">{{ getActivityIcon(act.action) }}</span>
                <span class="activity-text">{{ act.details?.text || act.action || '学习记录' }}</span>
                <span class="activity-time">{{ formatTime(act.created_at) }}</span>
              </div>
            </div>

            <div class="card-footer">
              <div class="footer-brand">
                <img src="/logo.png" alt="基智" class="footer-logo" />
                <span>基智学习助手</span>
              </div>
              <span class="footer-url">jizhi-learn.com</span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="previewVisible = false">关闭</el-button>
        <el-button type="primary" @click="exportFromPreview">导出PDF</el-button>
        <el-button type="success" @click="exportImageFromPreview">导出图片</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'
import { getProfileCard, updateProfileCardSettings } from '@/api/profileCard'
import { RANK_ICONS, RANK_COLORS, SUB_SYMBOLS } from '@/utils/constants'

const authStore = useAuthStore()

const loading = ref(false)
const refreshing = ref(false)
const pdfExporting = ref(false)
const imageExporting = ref(false)
const savingSettings = ref(false)
const settingsVisible = ref(false)
const previewVisible = ref(false)

const profile = ref(null)
const allTopics = ref([])
const allAchievements = ref([])
const activities = ref([])
const selectedTopics = ref([])
const selectedAchievements = ref([])
const totalDays = ref(0)
const achievementCount = ref(0)
const checkinDays = ref(0)

const tempSelectedTopics = ref([])
const tempSelectedAchievements = ref([])

const cardRef = ref(null)
const previewRef = ref(null)

const userLevel = computed(() => {
  if (!profile.value) return 1
  return Math.floor((profile.value.points || 0) / 100) + 1
})

const rankName = computed(() => profile.value?.rank || '启程')
const rankIcon = computed(() => RANK_ICONS[rankName.value] || '◈')
const rankColor = computed(() => RANK_COLORS[rankName.value] || '#888')
const rankSubSymbol = computed(() => {
  const sub = profile.value?.sub_rank || 1
  return SUB_SYMBOLS[sub] || '○'
})

const generateDate = computed(() => {
  return new Date().toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
})

const displayedTopics = computed(() => {
  return allTopics.value.filter(t => selectedTopics.value.includes(t.topic)).slice(0, 10)
})

const displayedAchievements = computed(() => {
  return allAchievements.value.filter(a => selectedAchievements.value.includes(a.id)).slice(0, 8)
})

const MASTERY_COLORS = [
  '#FF0000', '#FF1A00', '#FF3300', '#FF4D00', '#FF6600',
  '#FF8000', '#FF9900', '#FFB300', '#FFCC00', '#FFE600',
  '#D4E000', '#A8D500', '#7DCC00', '#52C200', '#26B800',
  '#00AD00', '#00A300', '#009900', '#008000', '#006600'
]

const MASTERY_COLORS_DARK = [
  '#CC0000', '#CC1500', '#CC2A00', '#CC3E00', '#CC5200',
  '#CC6600', '#CC7A00', '#CC8F00', '#CCA300', '#CCB800',
  '#A9B300', '#86AA00', '#64A100', '#419800', '#1E8F00',
  '#008A00', '#008200', '#007A00', '#006600', '#005200'
]

function getColor(score) {
  const index = Math.min(Math.floor(score / 5), 19)
  return MASTERY_COLORS[index] || '#888'
}

function getColorDark(score) {
  const index = Math.min(Math.floor(score / 5), 19)
  return MASTERY_COLORS_DARK[index] || '#666'
}

function getBadge(score) {
  if (score < 60) return '🔴 薄弱'
  if (score < 80) return '🟡 待巩固'
  return '🟢 优势'
}

function getActivityIcon(action) {
  const map = {
    checkin: '✅',
    answer_question: '📝',
    generate_question: '✏️',
    achievement_unlocked: '🏆',
    set_created: '📁',
    timer_completed: '⏱️',
    mistake_conquered: '🎯',
    level_up: '⬆️',
    rank_up: '🏅',
    chat: '💬',
    view_report: '📊',
    create_set: '📁',
    share: '📤',
    conquer_mistake: '🎯'
  }
  return map[action] || '📌'
}

function formatTime(time) {
  if (!time) return ''
  const t = new Date(time)
  const now = new Date()
  const diff = Math.floor((now - t) / 1000)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + '小时前'
  if (diff < 604800) return Math.floor(diff / 86400) + '天前'
  return t.toLocaleDateString()
}

async function loadData() {
  loading.value = true
  try {
    const res = await getProfileCard(authStore.user.id, authStore.user.id)
    profile.value = res.profile
    allTopics.value = res.mastery_data || []
    allAchievements.value = res.achievements || []
    activities.value = res.activities || []
    totalDays.value = res.total_days || 0
    achievementCount.value = res.achievement_count || 0
    checkinDays.value = res.profile?.checkin_days || 0
    selectedTopics.value = res.selected_topics || []
    selectedAchievements.value = res.selected_achievements || []
  } catch (error) {
    console.error('加载资料卡失败', error)
    ElMessage.error('加载资料卡失败')
  } finally {
    loading.value = false
  }
}

async function refreshData() {
  refreshing.value = true
  await loadData()
  refreshing.value = false
  ElMessage.success('已刷新')
}

function openSettings() {
  tempSelectedTopics.value = [...selectedTopics.value]
  tempSelectedAchievements.value = [...selectedAchievements.value]
  settingsVisible.value = true
}

function toggleTopic(topic) {
  const idx = tempSelectedTopics.value.indexOf(topic)
  if (idx > -1) {
    tempSelectedTopics.value.splice(idx, 1)
  } else if (tempSelectedTopics.value.length < 10) {
    tempSelectedTopics.value.push(topic)
  } else {
    ElMessage.warning('最多选择 10 个知识点')
  }
}

function toggleAchievement(id) {
  const idx = tempSelectedAchievements.value.indexOf(id)
  if (idx > -1) {
    tempSelectedAchievements.value.splice(idx, 1)
  } else if (tempSelectedAchievements.value.length < 8) {
    tempSelectedAchievements.value.push(id)
  } else {
    ElMessage.warning('最多选择 8 个成就')
  }
}

async function saveSettings() {
  savingSettings.value = true
  try {
    await updateProfileCardSettings(authStore.user.id, {
      selected_topics: tempSelectedTopics.value,
      selected_achievements: tempSelectedAchievements.value
    })
    selectedTopics.value = [...tempSelectedTopics.value]
    selectedAchievements.value = [...tempSelectedAchievements.value]
    settingsVisible.value = false
    ElMessage.success('设置已更新')
  } catch {
    ElMessage.error('更新失败')
  } finally {
    savingSettings.value = false
  }
}

function openPreview() {
  previewVisible.value = true
}

async function exportPDF() {
  pdfExporting.value = true
  try {
    await doExport(cardRef.value, 'pdf')
  } catch {
    ElMessage.error('导出失败')
  } finally {
    pdfExporting.value = false
  }
}

async function exportImage() {
  imageExporting.value = true
  try {
    await doExport(cardRef.value, 'image')
  } catch {
    ElMessage.error('导出失败')
  } finally {
    imageExporting.value = false
  }
}

async function exportFromPreview() {
  await doExport(previewRef.value, 'pdf')
}

async function exportImageFromPreview() {
  await doExport(previewRef.value, 'image')
}

async function doExport(element, type) {
  if (!element) {
    ElMessage.error('导出内容未找到')
    return
  }

  const isDark = document.documentElement.getAttribute('data-theme') === 'dark'
  const bgColor = isDark ? '#0d0d1a' : '#1a1a3e'

  element.style.width = '100%'
  element.style.maxWidth = '100%'
  element.style.padding = '24px 28px'
  element.style.overflow = 'visible'

  await nextTick()

  const width = element.scrollWidth
  const height = element.scrollHeight

  const canvas = await html2canvas(element, {
    scale: 4,
    useCORS: true,
    backgroundColor: bgColor,
    logging: false,
    width: width,
    height: height,
    windowWidth: width,
    windowHeight: height,
    allowTaint: true,
    onclone: (clonedDoc) => {
      const clonedEl = clonedDoc.getElementById('profile-card-export')
      if (clonedEl) {
        clonedEl.style.width = width + 'px'
        clonedEl.style.maxWidth = width + 'px'
        clonedEl.style.margin = '0'
        clonedEl.style.padding = '24px 28px'
        clonedEl.style.boxSizing = 'border-box'
        clonedEl.style.background = isDark
          ? 'linear-gradient(145deg, rgba(5,5,25,0.95), rgba(0,0,0,0.85))'
          : 'linear-gradient(145deg, rgba(20,20,60,0.90), rgba(0,0,0,0.70))'
        clonedEl.style.borderRadius = '20px'
        clonedEl.style.overflow = 'visible'
        clonedEl.style.color = '#ffffff'

        // ===== 重新创建头像 =====
        const wrapper = clonedEl.querySelector('.user-avatar-wrapper')
        if (wrapper) {
          const avatarUrl = profile.value?.avatar_url
          const name = profile.value?.nickname?.[0] || 'U'

          // 清空并重建
          wrapper.innerHTML = ''
          wrapper.style.display = 'flex'
          wrapper.style.flexShrink = '0'
          wrapper.style.alignItems = 'center'
          wrapper.style.justifyContent = 'center'
          wrapper.style.width = '72px'
          wrapper.style.height = '72px'
          wrapper.style.borderRadius = '50%'
          wrapper.style.overflow = 'hidden'
          wrapper.style.border = '3px solid rgba(255,255,255,0.2)'

          if (avatarUrl) {
            wrapper.innerHTML = `<img src="${avatarUrl}" style="width:100%;height:100%;object-fit:cover;display:block;" />`
          } else {
            wrapper.style.background = 'linear-gradient(135deg, #409eff, #8b5cf6)'
            wrapper.innerHTML = `<span style="color:#fff;font-size:28px;font-weight:600;display:flex;align-items:center;justify-content:center;width:100%;height:100%;">${name}</span>`
          }
        }

        // 所有文字强制白色
        const textEls = clonedEl.querySelectorAll('.brand-name, .user-name, .user-account, .user-bio, .meta-badge, .stat-number, .stat-label, .topic-name, .topic-score, .topic-badge, .ach-name, .activity-text, .activity-time, .footer-brand span, .footer-url, .section-header h4, .section-count, .empty-tip')
        textEls.forEach(el => {
          el.style.color = '#ffffff'
          el.style.opacity = '1'
        })
      }
    }
  })

  element.style.width = ''
  element.style.maxWidth = ''
  element.style.padding = ''
  element.style.overflow = ''

  if (type === 'image') {
    const link = document.createElement('a')
    link.download = `基智学习成果卡_${profile.value?.nickname || '用户'}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
    ElMessage.success('图片导出成功')
  } else {
    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF('p', 'mm', 'a4')
    const pdfWidth = pdf.internal.pageSize.getWidth()
    const pdfHeight = pdf.internal.pageSize.getHeight()
    const imgWidth = pdfWidth * 0.85
    const imgHeight = (canvas.height * imgWidth) / canvas.width
    const x = (pdfWidth - imgWidth) / 2
    const y = (pdfHeight - imgHeight) / 2
    pdf.addImage(imgData, 'PNG', x, y, imgWidth, imgHeight)
    pdf.save(`基智学习成果卡_${profile.value?.nickname || '用户'}.pdf`)
    ElMessage.success('PDF导出成功')
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.community-profile-card {
  padding: 0 4px;
}
.profile-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-left h2 {
  font-size: 22px;
  color: var(--text-primary);
  margin: 0;
}
.header-subtitle {
  font-size: 14px;
  color: var(--text-muted);
  opacity: 0.6;
}
.header-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.header-actions .el-button {
  border-radius: 8px !important;
  transition: all 0.3s ease !important;
}
.header-actions .el-button:hover {
  transform: translateY(-2px);
}
.el-divider {
  margin: 12px 0;
}
.card-wrapper {
  max-width: 720px;
  margin: 0 auto;
  padding: 0 !important;
  width: 100%;
}

/* ===== 主容器 ===== */
.card-content {
  position: relative;
  padding: 28px 32px;
  border-radius: 20px;
  background: linear-gradient(145deg, rgba(5,5,25,0.92), rgba(0,0,0,0.78));
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.06);
  box-shadow: 0 8px 40px rgba(0,0,0,0.4);
  overflow: hidden;
  color: #fff;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}
[data-theme="light"] .card-content {
  background: linear-gradient(145deg, rgba(20,20,60,0.88), rgba(0,0,0,0.62));
}

/* ===== 预览卡片 ===== */
.preview-card-content {
  background: linear-gradient(145deg, rgba(5,5,25,0.92), rgba(0,0,0,0.78));
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 20px;
  padding: 28px 32px;
  position: relative;
  overflow: hidden;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}
[data-theme="light"] .preview-card-content {
  background: linear-gradient(145deg, rgba(20,20,60,0.88), rgba(0,0,0,0.62));
}

/* ===== 几何背景 SVG ===== */
.geo-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}

/* ===== 光晕 ===== */
.glow {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
  z-index: 0;
  filter: blur(80px);
}
.glow-1 {
  width: 280px;
  height: 280px;
  top: -80px;
  right: -80px;
  background: rgba(64,158,255,0.12);
}
.glow-2 {
  width: 220px;
  height: 220px;
  bottom: 40px;
  left: -60px;
  background: rgba(139,92,246,0.10);
}
.glow-3 {
  width: 180px;
  height: 180px;
  bottom: 60px;
  right: 0px;
  background: rgba(244,114,182,0.08);
}
.glow-4 {
  width: 150px;
  height: 150px;
  top: 100px;
  left: -40px;
  background: rgba(52,211,153,0.06);
}

/* ===== 品牌 ===== */
.card-brand {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.brand-logo {
  width: 28px;
  height: 28px;
  object-fit: contain;
  filter: brightness(0) invert(1);
}
.brand-name {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  opacity: 0.85;
}
.card-date {
  margin-left: auto;
  font-size: 12px;
  color: rgba(255,255,255,0.3);
}

/* ===== 用户 ===== */
.user-section {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 16px 0;
}
.user-avatar-wrapper {
  position: relative;
  flex-shrink: 0;
}
.user-avatar {
  border: 3px solid rgba(255,255,255,0.10);
}
.avatar-ring {
  position: absolute;
  inset: -6px;
  border-radius: 50%;
  border: 2px solid transparent;
  background: linear-gradient(135deg, #409eff, #8b5cf6, #f472b6) border-box;
  -webkit-mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}
.user-name {
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 2px 12px rgba(0,0,0,0.3);
}
.user-account {
  font-size: 13px;
  color: rgba(255,255,255,0.4);
}
.user-bio {
  font-size: 14px;
  color: rgba(255,255,255,0.6);
  margin: 4px 0;
  padding: 4px 12px;
  border-radius: 6px;
  background: rgba(255,255,255,0.04);
  border-left: 2px solid rgba(64,158,255,0.25);
}
.user-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 4px;
}
.meta-badge {
  padding: 2px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  background: rgba(255,255,255,0.06);
  color: rgba(255,255,255,0.75);
}
.meta-badge.level {
  background: rgba(64,158,255,0.15);
  color: #66b1ff;
}
.meta-badge.rank {
  background: rgba(255,215,0,0.10);
  color: #ffd700;
}
.meta-badge.points {
  background: rgba(255,215,0,0.08);
  color: #ffd700;
}

/* ===== 统计 ===== */
.stats-section {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 1fr auto 1fr auto 1fr auto 1fr;
  align-items: center;
  gap: 4px;
  padding: 12px 0;
  border-top: 1px solid rgba(255,255,255,0.05);
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.stat-item {
  text-align: center;
}
.stat-number {
  display: block;
  font-size: 26px;
  font-weight: 700;
  color: #fff;
  text-shadow: 0 2px 12px rgba(0,0,0,0.2);
}
.stat-label {
  font-size: 12px;
  color: rgba(255,255,255,0.3);
}
.stat-divider {
  width: 1px;
  height: 28px;
  background: rgba(255,255,255,0.05);
}

/* ===== 通用 ===== */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.section-header h4 {
  font-size: 15px;
  color: #fff;
  margin: 0;
  opacity: 0.85;
}
.section-count {
  font-size: 12px;
  color: rgba(255,255,255,0.25);
}
.mastery-section, .achievement-section, .activities-section {
  position: relative;
  z-index: 1;
  padding: 12px 0;
}
.mastery-section {
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.achievement-section {
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.topic-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}
.topic-card {
  padding: 14px 12px;
  border-radius: 12px;
  color: #fff;
  text-align: center;
  transition: all 0.3s ease;
  min-height: 100px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.topic-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 28px rgba(0,0,0,0.25) !important;
}
.topic-name {
  font-size: 14px;
  font-weight: 500;
  text-shadow: 0 1px 4px rgba(0,0,0,0.15);
}
.topic-score {
  font-size: 26px;
  font-weight: 700;
  text-shadow: 0 1px 4px rgba(0,0,0,0.15);
}
.topic-badge {
  font-size: 11px;
  opacity: 0.85;
  text-shadow: 0 1px 4px rgba(0,0,0,0.15);
}

.achievement-grid {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.achievement-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px 6px 10px;
  border-radius: 10px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.05);
  font-size: 14px;
  transition: all 0.3s ease;
}
.achievement-item:hover {
  transform: translateY(-2px);
  background: rgba(255,255,255,0.07);
}
.achievement-item i {
  font-size: 20px;
}
.ach-name {
  font-size: 13px;
  color: rgba(255,255,255,0.75);
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 0;
  font-size: 14px;
  border-bottom: 1px solid rgba(255,255,255,0.03);
}
.activity-item:last-child {
  border-bottom: none;
}
.activity-icon {
  font-size: 16px;
}
.activity-text {
  color: rgba(255,255,255,0.6);
  flex: 1;
}
.activity-time {
  font-size: 12px;
  color: rgba(255,255,255,0.2);
  flex-shrink: 0;
}
.empty-tip {
  color: rgba(255,255,255,0.3);
  font-size: 13px;
  padding: 8px 0;
}

/* ===== 底部 ===== */
.card-footer {
  position: relative;
  z-index: 1;
  padding-top: 14px;
  border-top: 1px solid rgba(255,255,255,0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.footer-brand {
  display: flex;
  align-items: center;
  gap: 8px;
}
.footer-logo {
  width: 20px;
  height: 20px;
  object-fit: contain;
  filter: brightness(0) invert(1);
  opacity: 0.25;
}
.footer-brand span {
  font-size: 13px;
  color: rgba(255,255,255,0.2);
}
.footer-url {
  font-size: 11px;
  color: rgba(255,255,255,0.12);
}
.loading-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-muted);
}

/* ===== 设置弹窗 ===== */
.settings-dialog :deep(.el-dialog) {
  background: rgba(255,255,255,0.06) !important;
  backdrop-filter: blur(24px) !important;
  border: 1px solid rgba(255,255,255,0.08) !important;
  border-radius: 16px !important;
}
[data-theme="dark"] .settings-dialog :deep(.el-dialog) {
  background: rgba(0,0,0,0.3) !important;
}
.settings-dialog :deep(.el-dialog__title) {
  color: var(--text-primary) !important;
  font-weight: 600;
}
.settings-dialog :deep(.el-dialog__body) {
  padding: 16px 24px 8px;
}
.settings-dialog :deep(.el-dialog__footer) {
  padding: 8px 24px 16px;
}
.settings-dialog :deep(.el-button) {
  background: rgba(255,255,255,0.06) !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
  color: var(--text-secondary) !important;
  border-radius: 8px !important;
}
.settings-dialog :deep(.el-button--primary) {
  background: rgba(64,158,255,0.15) !important;
  border-color: rgba(64,158,255,0.2) !important;
  color: #66b1ff !important;
}
.settings-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-height: 400px;
  overflow-y: auto;
}
.setting-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.setting-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.setting-hint {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 400;
}
.setting-items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.setting-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.06);
  background: rgba(255,255,255,0.02);
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 13px;
  color: var(--text-secondary);
}
.setting-item:hover {
  background: rgba(255,255,255,0.06);
}
.setting-item.selected {
  border-color: rgba(64,158,255,0.4);
  background: rgba(64,158,255,0.08);
  color: var(--text-primary);
}
.setting-item .item-score {
  font-weight: 600;
  font-size: 12px;
}
.setting-item .item-check {
  color: #67c23a;
  font-weight: 700;
}

/* ===== 预览弹窗 ===== */
.preview-dialog :deep(.el-dialog) {
  background: rgba(255,255,255,0.06) !important;
  backdrop-filter: blur(24px) !important;
  border: 1px solid rgba(255,255,255,0.08) !important;
  border-radius: 16px !important;
}
[data-theme="dark"] .preview-dialog :deep(.el-dialog) {
  background: rgba(0,0,0,0.3) !important;
}
.preview-dialog :deep(.el-dialog__title) {
  color: var(--text-primary) !important;
  font-weight: 600;
}
.preview-dialog :deep(.el-dialog__body) {
  padding: 16px 24px 8px;
}
.preview-dialog :deep(.el-dialog__footer) {
  padding: 8px 24px 16px;
}
.preview-dialog :deep(.el-button) {
  background: rgba(255,255,255,0.06) !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
  color: var(--text-secondary) !important;
  border-radius: 8px !important;
}
.preview-dialog :deep(.el-button--primary) {
  background: rgba(64,158,255,0.15) !important;
  border-color: rgba(64,158,255,0.2) !important;
  color: #66b1ff !important;
}
.preview-dialog :deep(.el-button--success) {
  background: rgba(103,194,58,0.15) !important;
  border-color: rgba(103,194,58,0.2) !important;
  color: #67c23a !important;
}
.preview-content {
  display: flex;
  justify-content: center;
  max-height: 70vh;
  overflow-y: auto;
  padding: 8px;
}
.preview-card {
  max-width: 720px;
  width: 100%;
}
.preview-card-content {
  background: var(--card-bg) !important;
  border: 1px solid var(--border-color) !important;
}

@media (max-width: 640px) {
  .card-content { padding: 16px; }
  .profile-header { flex-direction: column; align-items: stretch; }
  .header-actions { justify-content: flex-start; }
  .stats-section { grid-template-columns: 1fr auto 1fr auto 1fr auto 1fr; gap: 4px; }
  .stat-number { font-size: 20px; }
  .user-section { flex-direction: column; text-align: center; }
  .user-meta { justify-content: center; }
  .topic-grid { grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); }
  .topic-card { min-height: 80px; padding: 10px; }
  .topic-score { font-size: 20px; }
}
</style>