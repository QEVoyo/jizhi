<template>
  <div class="qa-page">
    <div class="qa-container">
      <!-- ===== 顶部 ===== -->
      <div class="qa-header">
        <el-button text class="back-btn" @click="goBack">
          <i class="fas fa-arrow-left"></i> 返回
        </el-button>
        <h1>❓ 帮助中心</h1>
        <div></div>
      </div>

      <el-divider />

      <!-- ===== 搜索 ===== -->
      <div class="search-section">
        <div class="search-wrapper">
          <i class="fas fa-search search-icon"></i>
          <el-input
            v-model="searchKeyword"
            placeholder="输入关键词搜索问题..."
            size="large"
            clearable
            @input="filterFAQs"
          />
        </div>
      </div>

      <!-- ===== Tab ===== -->
      <div class="tab-section">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-item"
          :class="{ active: activeTab === tab.key }"
          @click="switchTab(tab.key)"
        >
          {{ tab.icon }} {{ tab.label }}
        </button>
      </div>

      <!-- ===== FAQ 列表 ===== -->
      <div class="faq-list">
        <div
          v-for="item in filteredFAQs"
          :key="item.id"
          class="faq-item"
          @click="toggleFAQ(item.id)"
        >
          <div class="faq-question">
            <span class="faq-icon">{{ item.expanded ? '▼' : '▶' }}</span>
            <span class="faq-title">{{ item.question }}</span>
            <span class="faq-tag" :style="{ background: item.tagColor + '20', color: item.tagColor }">
              {{ item.tag }}
            </span>
          </div>
          <div v-show="item.expanded" class="faq-answer">
            <div v-for="(step, idx) in item.answer" :key="idx" class="faq-step">
              {{ step }}
            </div>
            <div v-if="item.actions && item.actions.length" class="faq-actions">
              <button
                v-for="action in item.actions"
                :key="action.label"
                class="faq-action-btn"
                @click.stop="handleAction(action)"
              >
                {{ action.icon }} {{ action.label }}
              </button>
            </div>
          </div>
        </div>

        <div v-if="!filteredFAQs.length" class="empty-state">
          <i class="fas fa-search" style="font-size: 48px; opacity: 0.3;"></i>
          <p>没有找到相关问题</p>
          <p style="font-size: 13px; opacity: 0.6;">试试其他关键词，或者使用下方即时答疑</p>
        </div>
      </div>

      <!-- ===== 即时答疑 ===== -->
      <div class="qa-divider">
        <span>💬 还有问题？</span>
        <el-button text size="small" @click="showAskHistory = !showAskHistory">
          {{ showAskHistory ? '收起历史' : '查看历史提问' }}
        </el-button>
      </div>

      <div class="ask-section">
        <div class="ask-wrapper">
          <el-input
            v-model="askContent"
            placeholder="输入你的问题，AI 将为你解答..."
            size="large"
            @keyup.enter="submitAsk"
          />
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept="image/*"
            :on-change="handleImageUpload"
            :on-remove="handleImageRemove"
            class="upload-btn"
          >
            <el-button class="upload-trigger">
              <i class="fas fa-image"></i>
            </el-button>
          </el-upload>
          <el-button type="primary" :loading="askSubmitting" @click="submitAsk">
            <i class="fas fa-paper-plane"></i> 发送
          </el-button>
        </div>
        <div v-if="uploadedImage" class="upload-preview">
          <img :src="uploadedImage" alt="上传图片预览" />
          <el-button size="small" circle @click="removeImage">
            <i class="fas fa-times"></i>
          </el-button>
        </div>
        <div class="ask-hint">
          <span>支持文字提问和图片上传（JPG/PNG，最大 5MB）</span>
        </div>
      </div>

      <!-- ===== 提问历史 ===== -->
      <div v-if="showAskHistory" class="ask-history">
        <div class="history-title">📋 提问历史</div>
        <div
          v-for="item in askHistory"
          :key="item.id"
          class="history-item"
        >
          <div class="history-question">{{ item.question }}</div>
          <div class="history-meta">
            <span class="history-status" :class="item.status === '已回复' ? 'resolved' : 'pending'">
              {{ item.status === '已回复' ? '✅ 已回复' : '⏳ 处理中' }}
            </span>
            <span class="history-time">{{ item.time }}</span>
          </div>
        </div>
        <div v-if="!askHistory.length" class="history-empty">
          暂无提问记录
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()

// ===== 搜索 =====
const searchKeyword = ref('')

// ===== Tab =====
const tabs = [
  { key: 'all', icon: '📋', label: '全部' },
  { key: 'guide', icon: '📚', label: '学习指南' },
  { key: 'feature', icon: '🛠️', label: '功能使用' },
  { key: 'account', icon: '👤', label: '账号管理' },
  { key: 'community', icon: '🌐', label: '社区' }
]
const activeTab = ref('all')

// ===== FAQ 数据 =====
const faqs = ref([
  // ===== 学习指南 =====
  {
    id: 1,
    tag: '学习指南',
    tagColor: '#4CAF50',
    question: '如何开始学习？',
    answer: [
      '1. 注册登录后，进入「主界面」开始与 AI 对话',
      '2. 在「资源库」生成题目进行练习，系统会记录答题数据',
      '3. 系统根据你的答题情况自动生成「六维学情画像」',
      '4. 规划 Agent 会根据画像推荐适合你的学习路径',
      '5. 在「学程」中查看段位成长和任务进度'
    ],
    expanded: false,
    actions: [
      { icon: '📝', label: '去练习', route: '/resource-lib' }
    ]
  },
  {
    id: 2,
    tag: '学习指南',
    tagColor: '#4CAF50',
    question: '什么是六维学情画像？',
    answer: [
      '六维学情画像从 6 个维度全面评估你的学习状态：',
      '',
      '📊 知识基础 —— 各知识点的掌握程度和薄弱项',
      '🧠 认知风格 —— 适合视觉/听觉/动觉哪种学习方式',
      '🎯 易错点偏好 —— 常错的题型和知识板块分析',
      '🚀 学习目标 —— 短期目标和长期目标的完成进度',
      '📈 学习进度 —— 学习时长、完成度、效率评估',
      '❤️ 兴趣领域 —— 擅长的学科方向和兴趣偏好'
    ],
    expanded: false,
    actions: [
      { icon: '📊', label: '查看画像', route: '/profile' }
    ]
  },
  {
    id: 3,
    tag: '学习指南',
    tagColor: '#4CAF50',
    question: '学习路径如何动态调整？',
    answer: [
      '规划 Agent 会根据你的实时学习数据动态调整：',
      '',
      '✅ 掌握度 ≥ 80% 的知识点 → 自动减少练习，进入下一阶段',
      '⚠️ 掌握度 40%-60% 的知识点 → 保持常规练习，推送补充材料',
      '❌ 掌握度 < 40% 的知识点 → 增加练习频次，推送相关视频讲解',
      '📊 每周自动生成学习报告，优化下一周学习路径'
    ],
    expanded: false
  },
  {
    id: 4,
    tag: '学习指南',
    tagColor: '#4CAF50',
    question: '如何查看学习进度和报告？',
    answer: [
      '学习进度查看方式：',
      '',
      '📊 个人中心 → 查看六维学情画像各维度掌握度',
      '📈 工作台 → 学情报告 → 选择时间范围生成周报/月报',
      '🏆 学程 → 查看段位等级和任务完成进度'
    ],
    expanded: false,
    actions: [
      { icon: '📊', label: '去个人中心', route: '/profile' }
    ]
  },
  {
    id: 5,
    tag: '学习指南',
    tagColor: '#4CAF50',
    question: '如何设置学习目标？',
    answer: [
      '学习目标设置方法：',
      '',
      '1. 进入「个人中心」→ 学习目标板块',
      '2. 设置短期目标（如：本周完成 20 道题）',
      '3. 设置长期目标（如：一个月提升掌握度 20%）',
      '4. 系统会根据目标自动调整学习路径和题目难度'
    ],
    expanded: false
  },

  // ===== 功能使用 =====
  {
    id: 6,
    tag: '功能使用',
    tagColor: '#42A5F5',
    question: '如何生成题目？',
    answer: [
      '1. 进入「资源库」→ 点击「生成题目」',
      '2. 选择学科、知识点、题型和难度等级',
      '3. 点击「生成」，AI 会为你生成一道全新题目',
      '4. 题目会自动进入「练习」页面，开始作答',
      '5. 支持「换题型」和「重新生成」功能'
    ],
    expanded: false,
    actions: [
      { icon: '📝', label: '去生成题目', route: '/resource-lib' }
    ]
  },
  {
    id: 7,
    tag: '功能使用',
    tagColor: '#42A5F5',
    question: '错题本是如何自动收录的？',
    answer: [
      '错题本自动收录规则：',
      '',
      '📌 掌握度 < 40% → 自动加入「学习中」错题本，需要重点复习',
      '📌 掌握度 40%-60% → 保持学习中，定期复习巩固',
      '📌 掌握度 ≥ 60% → 自动移至「已攻克」错题本',
      '',
      '查看位置：资源库 → 错题本',
      '支持手动标记错题状态，支持导出复习'
    ],
    expanded: false,
    actions: [
      { icon: '📖', label: '去错题本', route: '/resource-lib' }
    ]
  },
  {
    id: 8,
    tag: '功能使用',
    tagColor: '#42A5F5',
    question: '如何创建和加入题集？',
    answer: [
      '创建题集：资源库 → 题集管理 → 新建题集 → 输入名称和描述',
      '',
      '加入题集：做题页面点击「加入题集」→ 选择目标题集',
      '',
      '题集功能：',
      '✅ 支持加权平均掌握度自动计算',
      '✅ 支持整卷练习和逐题练习',
      '✅ 题集可分享给好友（社区功能）'
    ],
    expanded: false,
    actions: [
      { icon: '📂', label: '去题集管理', route: '/resource-lib' }
    ]
  },
  {
    id: 9,
    tag: '功能使用',
    tagColor: '#42A5F5',
    question: '掌握度是如何计算的？',
    answer: [
      '每题作答后，评估 Agent 会给出 0-100% 的掌握度评分',
      '',
      '同知识点下所有题目的掌握度取加权平均（最近答题权重更高）',
      '',
      '掌握度含义：',
      '🔴 < 40% → 需要重点复习，加入错题本',
      '🟡 40%-60% → 需要巩固练习',
      '🟢 ≥ 80% → 建议进入下一阶段'
    ],
    expanded: false
  },
  {
    id: 10,
    tag: '功能使用',
    tagColor: '#42A5F5',
    question: '如何使用学习计时器和打卡功能？',
    answer: [
      '学习计时器：工作台 → 计时器 → 支持正向计时和倒计时',
      '',
      '打卡功能：',
      '1. 工作台 → 打卡 → 添加自定义打卡项目',
      '2. 每日点击打卡按钮完成打卡',
      '3. 打卡数据会自动记录到学习日志中'
    ],
    expanded: false
  },
  {
    id: 11,
    tag: '功能使用',
    tagColor: '#42A5F5',
    question: '如何查看学情报告？',
    answer: [
      '学情报告查看方式：',
      '',
      '1. 进入「工作台」→「学情报告」',
      '2. 选择报告时间范围（周/月/自定义）',
      '3. 点击「生成报告」，AI 自动生成详细报告',
      '4. 报告包含：掌握度变化趋势、薄弱项分析、学习建议',
      '5. 支持导出 PDF 和图片'
    ],
    expanded: false
  },
  {
    id: 12,
    tag: '功能使用',
    tagColor: '#42A5F5',
    question: '如何查看生成历史和题型筛选？',
    answer: [
      '1. 进入「资源库」→「生成历史」',
      '2. 默认按时间倒序显示所有生成记录',
      '3. 使用「题型筛选」下拉框按题型过滤',
      '4. 支持搜索和分页浏览'
    ],
    expanded: false
  },

  // ===== 账号管理 =====
  {
    id: 13,
    tag: '账号管理',
    tagColor: '#FF9800',
    question: '如何修改昵称和头像？',
    answer: [
      '1. 点击侧边栏「个人中心」进入个人资料页',
      '2. 头像：点击头像区域 → 上传新图片，自动裁剪压缩',
      '3. 昵称：点击昵称旁边的编辑按钮 → 输入新昵称 → 保存',
      '4. 修改后自动保存，刷新页面即时生效'
    ],
    expanded: false,
    actions: [
      { icon: '👤', label: '去个人中心', route: '/profile' }
    ]
  },
  {
    id: 14,
    tag: '账号管理',
    tagColor: '#FF9800',
    question: '如何修改密码？',
    answer: [
      '1. 进入「个人中心」→ 安全设置',
      '2. 输入当前密码验证身份',
      '3. 设置新密码（至少 8 位，含字母和数字）',
      '4. 确认新密码后点击提交',
      '5. 修改成功后自动退出，需重新登录'
    ],
    expanded: false,
    actions: [
      { icon: '👤', label: '去个人中心', route: '/profile' }
    ]
  },
  {
    id: 15,
    tag: '账号管理',
    tagColor: '#FF9800',
    question: '如何绑定和修改邮箱？',
    answer: [
      '1. 进入「个人中心」→ 账号设置',
      '2. 点击「修改邮箱」按钮',
      '3. 输入新邮箱地址，点击获取验证码',
      '4. 登录邮箱查看验证码并填写',
      '5. 点击确认完成邮箱绑定'
    ],
    expanded: false
  },
  {
    id: 16,
    tag: '账号管理',
    tagColor: '#FF9800',
    question: '如何修改个人简介？',
    answer: [
      '1. 进入「个人中心」→ 简介区域',
      '2. 点击编辑按钮，输入新的个人简介',
      '3. 点击保存，简介会自动更新'
    ],
    expanded: false
  },
  {
    id: 17,
    tag: '账号管理',
    tagColor: '#FF9800',
    question: '如何退出登录？',
    answer: [
      '1. 点击侧边栏底部「退出登录」按钮',
      '2. 弹窗确认是否退出',
      '3. 确认后清除登录态，跳转到登录页'
    ],
    expanded: false
  },

  // ===== 社区 =====
  {
    id: 18,
    tag: '社区',
    tagColor: '#9C27B0',
    question: '什么是社区？',
    answer: [
      '社区是一个轻量化的学习社交空间，你可以在这里：',
      '',
      '🌐 发布学习笔记和动态，与同学分享学习心得',
      '👥 添加好友，查看好友的学习资料和动态',
      '📚 分享题集和资源，一键收纳好友分享的题目',
      '📊 查看好友排行榜数据，互相激励进步',
      '💬 在动态广场互动，点赞评论学习内容'
    ],
    expanded: false
  },
  {
    id: 19,
    tag: '社区',
    tagColor: '#9C27B0',
    question: '如何添加好友？',
    answer: [
      '添加好友流程：',
      '',
      '1. 进入「社区」→ 搜索用户（按昵称或账号）',
      '2. 点击用户卡片上的「添加好友」按钮',
      '3. 等待对方确认好友申请',
      '4. 成为好友后，可以互相查看资料卡和分享题集',
      '5. 好友排行榜数据互通'
    ],
    expanded: false
  },
  {
    id: 20,
    tag: '社区',
    tagColor: '#9C27B0',
    question: '如何分享和接收题集？',
    answer: [
      '题集分享功能：',
      '',
      '1. 在「资源库」→ 题集管理 → 选择要分享的题集',
      '2. 点击「分享」按钮，生成分享链接',
      '3. 发送给好友，好友点击链接即可接收题集',
      '4. 接收后自动保存到自己的题集列表中',
      '5. 支持一键收纳好友分享的题目/套餐题集'
    ],
    expanded: false
  },
  {
    id: 21,
    tag: '社区',
    tagColor: '#9C27B0',
    question: '好友之间可以查看哪些数据？',
    answer: [
      '好友互通权限说明：',
      '',
      '✅ 查看好友资料卡（昵称、头像、简介、段位等级）',
      '✅ 查看好友排行榜数据',
      '✅ 接收好友分享的题库和题集',
      '✅ 查看好友的学习动态（打卡、完成题目、解锁成就）',
      '❌ 无法查看好友的错题本和隐私设置内容'
    ],
    expanded: false
  },
  {
    id: 22,
    tag: '社区',
    tagColor: '#9C27B0',
    question: '动态广场是什么？',
    answer: [
      '动态广场是社区的信息流页面，展示：',
      '',
      '📌 自己的学习动态（打卡、完成题目、解锁成就等）',
      '📌 好友的学习动态（系统自动聚合）',
      '📌 发布的笔记和题集分享',
      '',
      '支持点赞、评论、收藏等互动功能'
    ],
    expanded: false
  }
])

// ===== 提问 =====
const askContent = ref('')
const askSubmitting = ref(false)
const uploadedImage = ref(null)
const uploadRef = ref(null)
const showAskHistory = ref(false)
const askHistory = ref([
  { id: 1, question: '什么是导数？', status: '已回复', time: '2024-01-15' },
  { id: 2, question: '如何理解偏微分？', status: '处理中', time: '2024-01-16' },
  { id: 3, question: '微积分有什么应用？', status: '已回复', time: '2024-01-14' }
])

// ===== 方法 =====
function goBack() {
  router.push('/home')
}

function switchTab(tab) {
  activeTab.value = tab
}

function toggleFAQ(id) {
  const item = faqs.value.find(f => f.id === id)
  if (item) {
    item.expanded = !item.expanded
  }
}

function filterFAQs() {
  // 由 computed 自动处理
}

const filteredFAQs = computed(() => {
  let result = faqs.value

  if (activeTab.value !== 'all') {
    const tabMap = {
      guide: '学习指南',
      feature: '功能使用',
      account: '账号管理',
      community: '社区'
    }
    const tag = tabMap[activeTab.value]
    if (tag) {
      result = result.filter(f => f.tag === tag)
    }
  }

  if (searchKeyword.value.trim()) {
    const keyword = searchKeyword.value.trim().toLowerCase()
    result = result.filter(f =>
      f.question.toLowerCase().includes(keyword) ||
      f.answer.join('').toLowerCase().includes(keyword)
    )
  }

  return result
})

function handleAction(action) {
  if (action.route) {
    router.push(action.route)
  }
}

function handleImageUpload(file) {
  const reader = new FileReader()
  reader.onload = (e) => {
    uploadedImage.value = e.target.result
  }
  reader.readAsDataURL(file.raw)
}

function handleImageRemove() {
  removeImage()
}

function removeImage() {
  uploadedImage.value = null
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

async function submitAsk() {
  if (!askContent.value.trim() && !uploadedImage.value) {
    ElMessage.warning('请先输入问题或上传图片')
    return
  }

  askSubmitting.value = true
  try {
    // 模拟提交
    await new Promise(resolve => setTimeout(resolve, 1000))
    const newHistory = {
      id: askHistory.value.length + 1,
      question: askContent.value || '（含图片提问）',
      status: '处理中',
      time: new Date().toISOString().slice(0, 10)
    }
    askHistory.value.unshift(newHistory)
    ElMessage.success('✅ 问题已提交，AI 正在处理...')
    askContent.value = ''
    removeImage()
  } catch (error) {
    ElMessage.error('提交失败，请稍后重试')
  } finally {
    askSubmitting.value = false
  }
}
</script>

<style scoped>
.qa-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  padding: 30px 20px;
  background: transparent;
}

.qa-container {
  max-width: 820px;
  width: 100%;
  padding: 28px 36px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
  height: fit-content;
  max-height: 90vh;
  overflow-y: auto;
}

.qa-container::-webkit-scrollbar {
  width: 4px;
}
.qa-container::-webkit-scrollbar-thumb {
  background: rgba(128, 128, 128, 0.2);
  border-radius: 2px;
}

.qa-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.qa-header h1 {
  font-size: 26px;
  color: var(--text-primary);
  margin: 0;
}

.back-btn {
  color: var(--text-secondary) !important;
  transition: all 0.3s ease !important;
  font-size: 15px;
  padding: 8px 12px;
  border-radius: 10px;
}
.back-btn:hover {
  color: var(--text-primary) !important;
  transform: translateX(-4px);
  background: rgba(255, 255, 255, 0.08);
}
.back-btn:active {
  transform: translateX(-2px) scale(0.97);
}

.el-divider {
  margin: 14px 0;
}

/* ===== 搜索 ===== */
.search-section {
  margin: 4px 0 14px;
}
.search-wrapper {
  position: relative;
}
.search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  font-size: 14px;
  z-index: 1;
}
.search-wrapper :deep(.el-input__wrapper) {
  padding-left: 38px;
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 12px !important;
  transition: all 0.3s ease !important;
}
.search-wrapper :deep(.el-input__wrapper:hover) {
  border-color: rgba(255, 255, 255, 0.15) !important;
}
.search-wrapper :deep(.el-input__wrapper.is-focus) {
  border-color: rgba(64, 158, 255, 0.4) !important;
  box-shadow: 0 0 0 4px rgba(64, 158, 255, 0.08) !important;
}
.search-wrapper :deep(.el-input__inner) {
  color: var(--text-primary) !important;
  font-size: 14px;
}

/* ===== Tab ===== */
.tab-section {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
.tab-item {
  padding: 8px 18px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.02);
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.tab-item:hover {
  background: rgba(255, 255, 255, 0.06);
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.12);
}
.tab-item.active {
  background: rgba(64, 158, 255, 0.10);
  border-color: rgba(64, 158, 255, 0.2);
  color: #409eff;
}

/* ===== FAQ ===== */
.faq-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}
.faq-item {
  padding: 12px 16px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.04);
  background: rgba(255, 255, 255, 0.02);
  cursor: pointer;
  transition: all 0.3s ease;
}
.faq-item:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.08);
  transform: translateX(4px);
}
.faq-item:active {
  transform: translateX(2px) scale(0.99);
}
.faq-question {
  display: flex;
  align-items: center;
  gap: 10px;
}
.faq-icon {
  font-size: 12px;
  color: var(--text-muted);
  transition: transform 0.3s ease;
  flex-shrink: 0;
}
.faq-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
  flex: 1;
}
.faq-tag {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 12px;
  flex-shrink: 0;
}
.faq-answer {
  margin-top: 10px;
  padding: 12px 16px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  border-left: 3px solid rgba(64, 158, 255, 0.3);
  animation: slideDown 0.3s ease;
}
@keyframes slideDown {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}
.faq-step {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.8;
  padding: 2px 0;
}
.faq-actions {
  display: flex;
  gap: 10px;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}
.faq-action-btn {
  padding: 4px 14px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.faq-action-btn:hover {
  background: rgba(64, 158, 255, 0.10);
  border-color: rgba(64, 158, 255, 0.2);
  color: #409eff;
  transform: translateY(-2px);
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-muted);
}
.empty-state p {
  margin: 6px 0;
}

/* ===== 即时答疑 ===== */
.qa-divider {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 15px;
  color: var(--text-secondary);
  padding: 8px 0 12px;
}
.qa-divider .el-button {
  color: var(--text-muted) !important;
  font-size: 13px;
}
.qa-divider .el-button:hover {
  color: var(--text-primary) !important;
}

.ask-section {
  margin-top: 4px;
}
.ask-wrapper {
  display: flex;
  gap: 10px;
  align-items: center;
}
.ask-wrapper :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 12px !important;
  transition: all 0.3s ease !important;
}
.ask-wrapper :deep(.el-input__wrapper:hover) {
  border-color: rgba(255, 255, 255, 0.15) !important;
}
.ask-wrapper :deep(.el-input__wrapper.is-focus) {
  border-color: rgba(64, 158, 255, 0.4) !important;
  box-shadow: 0 0 0 4px rgba(64, 158, 255, 0.08) !important;
}
.ask-wrapper :deep(.el-input__inner) {
  color: var(--text-primary) !important;
}

.upload-btn {
  flex-shrink: 0;
}
.upload-trigger {
  width: 40px;
  height: 40px;
  padding: 0 !important;
  border-radius: 12px !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  background: rgba(255, 255, 255, 0.04) !important;
  color: var(--text-secondary) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  font-size: 16px;
  transition: all 0.3s ease !important;
}
.upload-trigger:hover {
  background: rgba(255, 255, 255, 0.10) !important;
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.15) !important;
}

.ask-wrapper .el-button--primary {
  border-radius: 12px !important;
  padding: 12px 24px !important;
  background: rgba(64, 158, 255, 0.10) !important;
  border: 1px solid rgba(64, 158, 255, 0.15) !important;
  color: #409eff !important;
  transition: all 0.3s ease !important;
}
.ask-wrapper .el-button--primary:hover {
  background: rgba(64, 158, 255, 0.20) !important;
  transform: translateY(-2px);
}
.ask-wrapper .el-button--primary:active {
  transform: translateY(0px) scale(0.97);
}

.upload-preview {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
  padding: 8px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.04);
}
.upload-preview img {
  width: 60px;
  height: 60px;
  object-fit: cover;
  border-radius: 8px;
}
.upload-preview .el-button {
  margin-left: auto;
  color: var(--text-muted);
}
.upload-preview .el-button:hover {
  color: #f56c6c;
}

.ask-hint {
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-muted);
  opacity: 0.6;
}

/* ===== 提问历史 ===== */
.ask-history {
  margin-top: 14px;
  padding: 12px 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
}
.history-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 10px;
}
.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}
.history-item:last-child {
  border-bottom: none;
}
.history-question {
  font-size: 14px;
  color: var(--text-primary);
}
.history-meta {
  display: flex;
  gap: 12px;
  align-items: center;
}
.history-status {
  font-size: 12px;
}
.history-status.resolved {
  color: #67c23a;
}
.history-status.pending {
  color: #e6a23c;
}
.history-time {
  font-size: 12px;
  color: var(--text-muted);
}
.history-empty {
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
  padding: 12px 0;
}

/* ===== 响应式 ===== */
@media (max-width: 640px) {
  .qa-page {
    padding: 12px 10px;
  }
  .qa-container {
    padding: 16px 14px;
    max-height: 95vh;
  }
  .qa-header h1 {
    font-size: 20px;
  }
  .tab-section {
    gap: 4px;
  }
  .tab-item {
    font-size: 12px;
    padding: 6px 12px;
  }
  .faq-item {
    padding: 10px 12px;
  }
  .faq-title {
    font-size: 13px;
  }
  .ask-wrapper {
    flex-direction: row;
    flex-wrap: wrap;
  }
  .ask-wrapper :deep(.el-input) {
    flex: 1;
    min-width: 120px;
  }
  .ask-wrapper .el-button--primary {
    padding: 10px 16px !important;
    font-size: 13px;
  }
  .faq-actions {
    flex-wrap: wrap;
  }
  .faq-action-btn {
    font-size: 12px;
    padding: 3px 10px;
  }
}
</style>