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
            placeholder="输入你的问题，我们将通过邮件回复你..."
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
          <span>问题将发送到管理员邮箱，我们会尽快回复你（支持图片上传）</span>
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
              {{ item.status === '已回复' ? '✅ 已回复' : '⏳ 待回复' }}
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
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

// ===== 搜索 =====
const searchKeyword = ref('')

// ===== Tab =====
const tabs = [
  { key: 'all', icon: '📋', label: '全部' },
  { key: 'guide', icon: '📚', label: '学习指南' },
  { key: 'feature', icon: '🛠️', label: '功能使用' },
  { key: 'career', icon: '🏆', label: '学程' },
  { key: 'community', icon: '🌐', label: '社区' },
  { key: 'account', icon: '👤', label: '账号管理' },
  { key: 'api', icon: '🔑', label: 'API配置' }
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
  // ========================================================
  // ✅ 修改：重写了六维学情画像，删掉旧的错误版本
  // ========================================================
  {
    id: 2,
    tag: '学习指南',
    tagColor: '#4CAF50',
    question: '六维学情画像各维度代表什么？',
    answer: [
      '六维学情画像从 6 个维度全面评估你的学习状态，运作流程如下：',
      '',
      '📊 K 知识基础：根据你在「资源库」做过的所有题目计算掌握度，分数越高代表基础越牢固。',
      '🧠 C 认知风格：分析你习惯的做题方式，综合型、探索型等不同风格影响你的学习效率。',
      '🎯 E 易错偏好：根据错题本中「未攻克」和「已攻克」的比例，找到你需要专门刷题的方向。',
      '🚀 G 学习目标：统计你在题集中创建和管理的目标，衡量长期学习的规划能力。',
      '📈 I 兴趣领域：扫描你生成历史中的高频知识点，找出你最感兴趣的方向。',
      '❤️ P 学习人格：综合前五项数据，为你生成一个专属的学习者标签（如稳健型/创新型）。',
      '',
      '👉 你可以在「评估中心」点击「六维画像」查看具体图表和数据。'
    ],
    expanded: false,
    actions: [
      { icon: '🧠', label: '去查看六维画像', route: '/profile-card' }
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
    expanded: false,
    actions: [
      { icon: '📊', label: '查看学情报告', route: '/evaluation-report' }
    ]
  },
  // ========================================================
  // ✅ 新增：学情报告运作说明
  // ========================================================
  {
    id: 4,
    tag: '学习指南',
    tagColor: '#4CAF50',
    question: '学情报告能看到什么数据？',
    answer: [
      '学情报告是你学习进度的数据仪表盘，运作方式如下：',
      '',
      '📊 统计概览：自动汇总你的知识点总数、已掌握（≥80%）、待巩固（<60%）以及平均掌握度。',
      '📈 掌握度分布：三段式进度条直观显示薄弱、待巩固、已掌握的占比，一目了然。',
      '🔍 知识点详情：支持按「全部/薄弱/待巩固/已掌握」筛选，也支持直接搜索具体知识点。',
      '📖 学习动态：按时间线显示近期的学习行为记录（如打卡、做题、解锁成就等）。',
      '💾 导出功能：点击右上角的「导出PDF」按钮，一键保存当前报告为 PDF 文件。',
      '',
      '👉 你可以在「评估中心」点击「学情报告」查看完整面板。'
    ],
    expanded: false,
    actions: [
      { icon: '📊', label: '去查看学情报告', route: '/evaluation-report' }
    ]
  },
  // ========================================================
  // ✅ 新增：评估表运作说明 + 生成规划入口
  // ========================================================
  {
    id: 5,
    tag: '学习指南',
    tagColor: '#4CAF50',
    question: '评估表怎么用？如何一键生成学习规划？',
    answer: [
      '评估表是系统对你综合能力的深度诊断工具，运作流程非常直接：',
      '',
      '📈 综合评分：自动计算六维维度分数的加权平均值，得出你的综合能力评分。',
      '🏆 评级体系：根据分数分为「开拓期、筑基期、精进期、卓越期、巅峰期」五个阶段。',
      '🧩 六维雷达图：用图形展示六个维度的相对强弱，让你一眼看出自己的优劣势。',
      '📋 智能诊断：系统会为你生成四项核心内容——核心优势、待提升维度、成长潜力、学习建议。',
      '🚀 生成规划：在诊断卡片下方点击「生成规划」，系统会立刻提取薄弱点/优势，自动生成一个针对性的「规划名称」并跳转到预览页，确认后即可生成带日期解锁的每日任务。',
      '',
      '👉 你可以在「评估中心」点击「评估表」体验完整流程。'
    ],
    expanded: false,
    actions: [
      { icon: '📋', label: '去使用评估表', route: '/evaluation-table' }
    ]
  },
  // ========================================================
  // ✅ 新增：学习规划运作说明
  // ========================================================
  {
    id: 6,
    tag: '学习指南',
    tagColor: '#4CAF50',
    question: '学习规划是怎么生成和运作的？',
    answer: [
      '学习规划是系统为你量身定制的长期学习路线图，运作逻辑如下：',
      '',
      '📝 创建入口：在「学习规划」列表页点击「新建规划」，或从「评估表」一键生成跳转。',
      '🤖 AI 生成任务：输入关键词、难度基数、周期后，AI 会拆分为多个子知识点，自动生成每天的学习内容与题目。',
      '📅 日期解锁机制：第一天默认解锁，此后每天必须完成前一天所有任务，才能解锁下一天的内容。',
      '✅ 任务三态：任务分为「待开始、进行中、已完成」，状态会自动更新并影响整体进度。',
      '📚 任务类型：每天的学习任务包括「学习内容、做题、学习视频（预留）」三大板块。',
      '',
      '👉 在「评估中心」点击「学习规划」即可管理和查看你的所有规划。'
    ],
    expanded: false,
    actions: [
      { icon: '🚀', label: '去管理学习规划', route: '/learning-plan' }
    ]
  },
  {
    id: 7,
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
    id: 8,
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
    expanded: false,
    actions: [
      { icon: '👤', label: '去个人中心', route: '/profile' }
    ]
  },

  // ===== 功能使用 =====
  {
    id: 9,
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
    id: 10,
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
    id: 11,
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
    id: 12,
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
    id: 13,
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
    expanded: false,
    actions: [
      { icon: '⏱️', label: '去工作台', route: '/home' }
    ]
  },
  {
    id: 14,
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
    expanded: false,
    actions: [
      { icon: '📊', label: '去工作台', route: '/home' }
    ]
  },
  {
    id: 15,
    tag: '功能使用',
    tagColor: '#42A5F5',
    question: '如何查看生成历史和题型筛选？',
    answer: [
      '1. 进入「资源库」→「生成历史」',
      '2. 默认按时间倒序显示所有生成记录',
      '3. 使用「题型筛选」下拉框按题型过滤',
      '4. 支持搜索和分页浏览'
    ],
    expanded: false,
    actions: [
      { icon: '📝', label: '去资源库', route: '/resource-lib' }
    ]
  },

  // ===== 学程 =====
  {
    id: 16,
    tag: '学程',
    tagColor: '#F44336',
    question: '学程是什么？',
    answer: [
      '学程是基智学习助手的游戏化激励体系，通过段位、等级、任务、成就四个维度，将学习行为转化为可视化的成长路径。',
      '',
      '📌 四大模块：',
      '',
      '🏆 段位：7 大段位 + 每段 5 小级',
      '  启程 → 求索 → 明理 → 致知 → 笃行 → 臻境 → 传说',
      '',
      '📈 等级：等差数列升级，第 1 级 2 分，第 n 级 n+1 分',
      '',
      '📋 任务：播种任务（新手引导）→ 施肥任务（每日5个）→ 发芽任务（长期阶梯）',
      '',
      '🎖️ 成就：25 个一次性成就，涵盖学习全场景，解锁获得积分'
    ],
    expanded: false,
    actions: [
      { icon: '🏆', label: '去学程', route: '/career' }
    ]
  },
  {
    id: 17,
    tag: '学程',
    tagColor: '#F44336',
    question: '段位系统是如何计算的？',
    answer: [
      '段位系统由「段位积分」驱动，积分累计自动晋升：',
      '',
      '📌 7 大段位（从低到高）：',
      '  启程 → 求索 → 明理 → 致知 → 笃行 → 臻境 → 传说',
      '',
      '📌 每个大段位含 5 个小段（I → V）：',
      '  每小段 100 分，满 500 分晋升下一大段',
      '',
      '📌 积分来源：',
      '  • 完成每日任务：10-70 分/个',
      '  • 解锁成就：15-500 分/个',
      '  • 段位晋升：50-500 分/次',
      '  • 等级升级：自动累计',
      '',
      '📌 查看位置：学程 → 登攀'
    ],
    expanded: false,
    actions: [
      { icon: '🏆', label: '查看段位', route: '/career/rank' }
    ]
  },
  {
    id: 18,
    tag: '学程',
    tagColor: '#F44336',
    question: '等级系统是如何计算的？',
    answer: [
      '等级系统采用等差数列升级规则：',
      '',
      '📌 升级规则：',
      '  第 1 级：需要 2 分',
      '  第 2 级：需要 3 分',
      '  第 n 级：需要 n+1 分',
      '',
      '📌 积分来源：',
      '  与段位积分共享，学习行为同时累积段位积分和等级积分',
      '',
      '📌 进度显示：',
      '  蓝色进度条实时展示当前等级进度',
      '',
      '📌 查看位置：学程 → 登攀'
    ],
    expanded: false,
    actions: [
      { icon: '📈', label: '查看等级', route: '/career/rank' }
    ]
  },
  {
    id: 19,
    tag: '学程',
    tagColor: '#F44336',
    question: '三种任务有什么区别？',
    answer: [
      '任务系统分为三个阶段，循序渐进：',
      '',
      '🌱 播种任务（新手引导）：',
      '  • 首次使用各项功能，如：首次打卡、首次生成题目、首次添加好友',
      '  • 完成后解锁施肥任务',
      '',
      '💧 施肥任务（每日任务）：',
      '  • 每天 5 个任务，如：完成 3 道题、学习 15 分钟',
      '  • 可「换一批」更换任务（每日限 1 次）',
      '  • 完成后解锁发芽任务',
      '',
      '🌿 发芽任务（长期阶梯任务）：',
      '  • 长期目标，如：累计完成 100 道题、连续打卡 7 天',
      '  • 阶梯式奖励，越往后奖励越高',
      '',
      '📌 查看位置：学程 → 勤耕'
    ],
    expanded: false,
    actions: [
      { icon: '📋', label: '去任务', route: '/career/tasks' }
    ]
  },
  {
    id: 20,
    tag: '学程',
    tagColor: '#F44336',
    question: '成就有哪些？如何解锁？',
    answer: [
      '共有 25 个一次性成就，涵盖学习全场景：',
      '',
      '📌 成就分类：',
      '  🎯 学习类：完成题目、掌握度提升、连续学习',
      '  🤝 社交类：添加好友、分享题集、发布动态',
      '  🏅 成长类：段位晋升、等级提升、完成任务',
      '  📚 资源类：创建题集、收藏动态、错题攻克',
      '',
      '📌 成就状态：',
      '  🔒 未解锁 → 条件未达成',
      '  🔓 可领取 → 条件已达成，点击领取积分',
      '  ✅ 已领取 → 已获得积分奖励',
      '',
      '📌 查看位置：学程 → 拾贝'
    ],
    expanded: false,
    actions: [
      { icon: '🎖️', label: '查看成就', route: '/career/achievements' }
    ]
  },
  {
    id: 21,
    tag: '学程',
    tagColor: '#F44336',
    question: '如何查看攀登足迹？',
    answer: [
      '攀登足迹记录你学习成长的每一个重要时刻：',
      '',
      '📌 记录内容：',
      '  • 段位晋升：从启程 → 传说，每次晋升都有记录',
      '  • 等级提升：每升 1 级记录一次',
      '  • 成就解锁：获得特殊成就时记录',
      '',
      '📌 查看位置：学程 → 登攀 → 攀登足迹',
      '',
      '📌 用途：',
      '  回顾自己的学习历程，看到从零到现在的成长轨迹，增强学习动力。'
    ],
    expanded: false,
    actions: [
      { icon: '📜', label: '查看足迹', route: '/career/rank' }
    ]
  },
  {
    id: 22,
    tag: '学程',
    tagColor: '#F44336',
    question: '积分可以从哪些行为获得？',
    answer: [
      '积分是段位、等级、成就的通用货币，以下行为均可获得：',
      '',
      '┌───────────────┬─────────────┐',
      '│ 行为           │ 积分范围     │',
      '├───────────────┼─────────────┤',
      '│ 完成每日任务   │ 10-70 分    │',
      '│ 解锁成就       │ 15-500 分   │',
      '│ 段位晋升       │ 50-500 分   │',
      '│ 等级升级       │ 自动累计    │',
      '│ 完成题目       │ 按正确率评估 │',
      '│ 打卡           │ 10 分       │',
      '│ 发布动态       │ 15 分       │',
      '│ 分享题集       │ 20 分       │',
      '└───────────────┴─────────────┘',
      '',
      '📌 价值星星：不同价值的行为显示不同颜色星星，一目了然。'
    ],
    expanded: false,
    actions: [
      { icon: '⭐', label: '去赚积分', route: '/career' }
    ]
  },
  {
    id: 23,
    tag: '学程',
    tagColor: '#F44336',
    question: '学程三个子页面分别是什么？',
    answer: [
      '学程包含三个子页面，各司其职：',
      '',
      '🏔️ 登攀（/career/rank）：',
      '  • 当前段位显示、段位进度条',
      '  • 攀登足迹（历史记录）',
      '  • 全部段位预览（从启程到传说）',
      '',
      '📋 勤耕（/career/tasks）：',
      '  • 播种任务（新手引导）',
      '  • 施肥任务（每日5个，可换一批）',
      '  • 发芽任务（长期阶梯式）',
      '',
      '🐚 拾贝（/career/achievements）：',
      '  • 25 个成就卡片展示',
      '  • 成就进度、状态（未解锁/可领取/已领取）',
      '  • 成就详情弹窗（毛玻璃效果）'
    ],
    expanded: false,
    actions: [
      { icon: '🏆', label: '去学程', route: '/career' }
    ]
  },

  // ===== 社区 =====
  {
    id: 24,
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
    expanded: false,
    actions: [
      { icon: '🌐', label: '去社区', route: '/community' }
    ]
  },
  {
    id: 25,
    tag: '社区',
    tagColor: '#9C27B0',
    question: '如何添加好友？',
    answer: [
      '添加好友流程：',
      '',
      '1. 进入「社区」→「好友」→ 搜索用户（按账号搜索）',
      '2. 点击用户卡片上的「添加好友」按钮',
      '3. 等待对方确认好友申请',
      '4. 成为好友后，可以互相查看资料卡和分享题集',
      '5. 好友排行榜数据互通'
    ],
    expanded: false,
    actions: [
      { icon: '👥', label: '去添加好友', route: '/community/friends' }
    ]
  },
  {
    id: 26,
    tag: '社区',
    tagColor: '#9C27B0',
    question: '如何分享和接收题集？',
    answer: [
      '题集分享功能：',
      '',
      '1. 在「资源库」→ 题集管理 → 选择要分享的题集',
      '2. 点击「分享」按钮，发送给好友',
      '3. 好友在消息中心收到通知，点击接收即可',
      '4. 接收后自动保存到自己的题集列表中',
      '5. 支持一键收纳好友分享的题目/套餐题集'
    ],
    expanded: false,
    actions: [
      { icon: '📂', label: '去题集管理', route: '/resource-lib' }
    ]
  },
  {
    id: 27,
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
    expanded: false,
    actions: [
      { icon: '👤', label: '查看好友资料卡', route: '/community/friends' }
    ]
  },
  {
    id: 28,
    tag: '社区',
    tagColor: '#9C27B0',
    question: '动态广场是什么？',
    answer: [
      '动态广场是社区的信息流页面，展示：',
      '',
      '📌 全部动态 / 好友动态（可切换筛选）',
      '📌 发布学习笔记和心得',
      '📌 点赞、评论、收藏互动',
      '📌 举报违规内容'
    ],
    expanded: false,
    actions: [
      { icon: '🏠', label: '去动态广场', route: '/community' }
    ]
  },

  // ===== 账号管理 =====
  {
    id: 29,
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
    id: 30,
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
    id: 31,
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
    expanded: false,
    actions: [
      { icon: '👤', label: '去个人中心', route: '/profile' }
    ]
  },
  {
    id: 32,
    tag: '账号管理',
    tagColor: '#FF9800',
    question: '如何修改个人简介？',
    answer: [
      '1. 进入「个人中心」→ 简介区域',
      '2. 点击编辑按钮，输入新的个人简介',
      '3. 点击保存，简介会自动更新'
    ],
    expanded: false,
    actions: [
      { icon: '👤', label: '去个人中心', route: '/profile' }
    ]
  },
  {
    id: 33,
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

  // ===== API配置 =====
  {
    id: 34,
    tag: 'API配置',
    tagColor: '#FF5722',
    question: 'API 管理是做什么的？',
    answer: [
      'API 管理让你可以为每个 AI 功能选择不同的模型平台，并填入自己的 API 凭证。',
      '',
      '📌 可配置的功能：',
      '',
      '  💬 AI 对话（小基聊天 / 学习问答）',
      '    可选平台：火山引擎（豆包）、DeepSeek、智谱 GLM',
      '',
      '  🖼️ 图片理解（识别图片内容）',
      '    可选平台：火山引擎（豆包）',
      '',
      '  📝 题目生成（AI 出题 / 换题型）',
      '    可选平台：DeepSeek、智谱 GLM',
      '',
      '  📊 学习评估（掌握度评分 / 学情报告 / 画像生成）',
      '    可选平台：DeepSeek',
      '',
      '  🎥 视频推荐（知识点相关视频推送）',
      '    可选平台：腾讯云',
      '',
      '  📞 视频通话（讯飞数字人）',
      '    可选平台：讯飞',
      '',
      '💡 配置后功能将优先使用你自己的 API 额度，无调用限制。'
    ],
    expanded: false,
    actions: [
      { icon: '🔑', label: '去配置 API', route: '/api-center' }
    ]
  },
  {
    id: 35,
    tag: 'API配置',
    tagColor: '#FF5722',
    question: '各功能需要什么平台的 API？',
    answer: [
      '各功能和推荐平台的对应关系：',
      '',
      '┌─────────────┬──────────────────┬─────────────────────┐',
      '│ 功能        │ 推荐平台         │ 凭证要求            │',
      '├─────────────┼──────────────────┼─────────────────────┤',
      '│ 💬 AI 对话  │ 火山引擎（豆包）  │ API Key + Endpoint ID│',
      '│             │ DeepSeek         │ API Key             │',
      '│             │ 智谱 GLM         │ API Key             │',
      '├─────────────┼──────────────────┼─────────────────────┤',
      '│ 🖼️ 图片理解  │ 火山引擎（豆包）  │ API Key + Endpoint ID│',
      '├─────────────┼──────────────────┼─────────────────────┤',
      '│ 📝 题目生成  │ DeepSeek         │ API Key             │',
      '│             │ 智谱 GLM         │ API Key             │',
      '├─────────────┼──────────────────┼─────────────────────┤',
      '│ 📊 学习评估  │ DeepSeek         │ API Key             │',
      '├─────────────┼──────────────────┼─────────────────────┤',
      '│ 🎥 视频推荐  │ 腾讯云           │ SecretId + SecretKey│',
      '├─────────────┼──────────────────┼─────────────────────┤',
      '│ 📞 视频通话  │ 讯飞             │ APPID + API Key     │',
      '│             │                  │ + API Secret        │',
      '└─────────────┴──────────────────┴─────────────────────┘'
    ],
    expanded: false,
    actions: [
      { icon: '🔑', label: '去配置 API', route: '/api-center' }
    ]
  },
  {
    id: 36,
    tag: 'API配置',
    tagColor: '#FF5722',
    question: '如何获取 DeepSeek API Key？',
    answer: [
      '🔹 步骤：',
      '  1. 访问 platform.deepseek.com 注册账号',
      '  2. 完成实名认证（需要手机号+身份证）',
      '  3. 进入控制台 → 「API Keys」→ 「创建 API Key」',
      '  4. 输入名称（如「基智学习」），点击「创建」',
      '  5. 复制生成的 Key（格式：sk-xxxxxxxxxxxxxxxx）',
      '  6. 回到基智 API 管理页面，粘贴保存',
      '',
      '⚠️ 常见坑：',
      '  • DeepSeek 新用户送 500 万 tokens 额度，够用很久',
      '  • Key 只显示一次，务必复制保存，关闭后无法再查看',
      '  • 如果提示余额不足，去控制台充值即可',
      '',
      '🔗 直达链接：',
      '  • 注册/登录：https://platform.deepseek.com',
      '  • API Keys 管理：https://platform.deepseek.com/api_keys'
    ],
    expanded: false,
    actions: [
      { icon: '🔑', label: '去配置 API', route: '/api-center' }
    ]
  },
  {
    id: 37,
    tag: 'API配置',
    tagColor: '#FF5722',
    question: '如何获取火山引擎（豆包）API Key？',
    answer: [
      '🔹 步骤：',
      '  1. 访问 console.volcengine.com 注册账号',
      '  2. 完成实名认证（个人/企业均可）',
      '  3. 开通「火山方舟 ARK」服务（控制台搜索「ARK」）',
      '  4. 进入「推理接入」→ 「创建接入点」',
      '  5. 选择模型（如 Doubao-pro-32k、Doubao-vision）',
      '  6. 接入点创建成功后，点击「API 调用」获取 Key',
      '  7. 复制 API Key（格式：VxCgNvLTE.xxxxxxxxxxxxxxxx）和 Endpoint ID',
      '  8. 回到基智 API 管理页面，填入对应字段',
      '',
      '⚠️ 常见坑：',
      '  • 火山引擎的 API Key 不是 Access Key/Secret Key，而是 ARK API Key',
      '  • 开通 ARK 服务可能需要 0 元开通，无需付费',
      '  • 每个接入点有独立的 API Key，不要搞混',
      '  • Vision（图片理解）和 Chat（对话）是不同接入点，需分别创建',
      '  • 新用户通常有免费额度，够测试使用',
      '',
      '🔗 直达链接：',
      '  • 注册/登录：https://console.volcengine.com',
      '  • ARK 控制台：https://console.volcengine.com/ark/',
      '  • 推理接入点管理：https://console.volcengine.com/ark/region:ark+cn-beijing/endpoint'
    ],
    expanded: false,
    actions: [
      { icon: '🔑', label: '去配置 API', route: '/api-center' }
    ]
  },
  {
    id: 38,
    tag: 'API配置',
    tagColor: '#FF5722',
    question: '如何获取智谱 GLM / 百川 API Key？',
    answer: [
      '🔹 智谱 GLM（用于对话、生成题目）：',
      '  1. 访问 open.bigmodel.cn 注册账号',
      '  2. 完成实名认证',
      '  3. 进入控制台 → 「API Keys」→ 「创建 API Key」',
      '  4. 复制 Key（格式：xxxxxxxx.xxxxxxxxxxxxxxxx）',
      '  5. 新用户送免费额度',
      '  🔗 https://open.bigmodel.cn',
      '',
      '🔹 百川（用于联网搜索）：',
      '  1. 访问 platform.baichuan-ai.com 注册账号',
      '  2. 完成实名认证',
      '  3. 进入「API Keys」页面创建密钥',
      '  4. 复制 Key 并保存',
      '  🔗 https://platform.baichuan-ai.com',
      '',
      '⚠️ 通用坑：',
      '  • 所有平台的 Key 都只显示一次，请立即保存',
      '  • 如果验证失败，检查 Key 是否有前后空格',
      '  • 大部分平台新用户都有免费额度，不用先充值'
    ],
    expanded: false,
    actions: [
      { icon: '🔑', label: '去配置 API', route: '/api-center' }
    ]
  },
  {
    id: 39,
    tag: 'API配置',
    tagColor: '#FF5722',
    question: '如何获取腾讯云 API 密钥？',
    answer: [
      '🔹 步骤（用于视频推荐）：',
      '  1. 访问 console.cloud.tencent.com 注册账号',
      '  2. 完成实名认证',
      '  3. 开通「云点播 VOD」服务',
      '  4. 进入「访问管理」→ 「API密钥管理」',
      '  5. 创建密钥，获取 SecretId 和 SecretKey',
      '  6. 选择地域（推荐上海 ap-shanghai）',
      '  7. 回到基智 API 管理页面，填入对应字段',
      '',
      '⚠️ 常见坑：',
      '  • SecretId 和 SecretKey 是腾讯云所有服务的通用密钥',
      '  • 需开通云点播服务后才能使用视频相关功能',
      '  • 部分接口需要指定地域，与密钥权限相关',
      '',
      '🔗 直达链接：',
      '  • 注册/登录：https://console.cloud.tencent.com',
      '  • API密钥管理：https://console.cloud.tencent.com/cam/capi',
      '  • 云点播控制台：https://console.cloud.tencent.com/vod'
    ],
    expanded: false,
    actions: [
      { icon: '🔑', label: '去配置 API', route: '/api-center' }
    ]
  },
  {
    id: 40,
    tag: 'API配置',
    tagColor: '#FF5722',
    question: '如何获取讯飞 API 凭证？',
    answer: [
      '🔹 步骤（用于视频通话/数字人）：',
      '  1. 访问 console.xfyun.cn 注册账号',
      '  2. 完成实名认证',
      '  3. 进入控制台 → 创建应用',
      '  4. 获取 APPID、API Key、API Secret',
      '  5. 开通对应的数字人服务（如讯飞数字人）',
      '  6. 回到基智 API 管理页面，填入对应字段',
      '',
      '⚠️ 常见坑：',
      '  • 讯飞的三个凭证（APPID、API Key、API Secret）都需要填写',
      '  • 不同应用有不同的凭证，不要搞混',
      '  • 数字人服务需要单独开通，可能有免费试用额度',
      '',
      '🔗 直达链接：',
      '  • 注册/登录：https://console.xfyun.cn',
      '  • 应用管理：https://console.xfyun.cn/app'
    ],
    expanded: false,
    actions: [
      { icon: '🔑', label: '去配置 API', route: '/api-center' }
    ]
  },
  {
    id: 41,
    tag: 'API配置',
    tagColor: '#FF5722',
    question: 'API Key 配置后如何验证是否有效？',
    answer: [
      '在「API 管理」页面填入凭证后：',
      '',
      '1. 点击对应平台的「验证」按钮',
      '2. 系统会发送一条测试请求到该平台',
      '3. 验证结果会显示在按钮旁边：',
      '   ✅ 验证通过 → 凭证有效，功能可正常使用',
      '   ❌ 验证失败 → 请检查以下问题：',
      '',
      '🔍 验证失败排查：',
      '  • 凭证是否完整复制（没有遗漏字符）',
      '  • 是否有多余空格（复制时容易带入）',
      '  • 平台账户是否有余额/免费额度',
      '  • 火山引擎：是否填写了正确的 Endpoint ID',
      '  • 腾讯云：是否开通了对应的云服务',
      '  • 讯飞：是否开通了对应的数字人服务',
      '  • 网络是否正常（需要能访问外网）',
      '',
      '💡 验证通过后，对应功能会优先使用你的凭证进行调用。'
    ],
    expanded: false,
    actions: [
      { icon: '🔑', label: '去验证 API', route: '/api-center' }
    ]
  },
  {
    id: 42,
    tag: 'API配置',
    tagColor: '#FF5722',
    question: '未配置 API 或 API 失效时会怎样？',
    answer: [
      '系统有完整的降级方案，保证功能可用：',
      '',
      '📌 情况1：未配置任何 API',
      '  → 自动使用系统公共 API（有限额，适合体验）',
      '  → 页面会提示「建议配置专属 Key」',
      '',
      '📌 情况2：已配置但凭证失效',
      '  → 自动降级到系统公共 API',
      '  → 页面提示「你的 API 凭证已失效，已切换为公共资源」',
      '',
      '📌 情况3：公共 API 也超限',
      '  → 显示「服务繁忙，请稍后重试或配置自己的 API Key」',
      '',
      '💡 建议尽早配置自己的凭证，避免公共额度耗尽影响学习。'
    ],
    expanded: false,
    actions: [
      { icon: '🔑', label: '去配置 API', route: '/api-center' }
    ]
  }
])

// ===== 提问 =====
const askContent = ref('')
const askSubmitting = ref(false)
const uploadedImage = ref(null)
const uploadRef = ref(null)
const showAskHistory = ref(false)
const askHistory = ref([
  { id: 1, question: '如何配置 API Key？', status: '已回复', time: '2026-07-08' },
  { id: 2, question: '为什么我的 API Key 验证失败？', status: '已回复', time: '2026-07-08' },
  { id: 3, question: '社区好友排行榜怎么看不到自己？', status: '已回复', time: '2026-07-07' }
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
      career: '学程',
      community: '社区',
      account: '账号管理',
      api: 'API配置'
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
    const response = await fetch('/api/qa/submit', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: authStore.user?.id || '',
        user_email: authStore.user?.email || '',
        user_nickname: authStore.user?.nickname || '用户',
        question: askContent.value.trim() || '（图片提问）',
        has_image: !!uploadedImage.value,
        image_data: uploadedImage.value || null
      })
    })

    const result = await response.json()

    if (response.ok) {
      const newHistory = {
        id: askHistory.value.length + 1,
        question: askContent.value.trim() || '（含图片提问）',
        status: '待回复',
        time: new Date().toISOString().slice(0, 10)
      }
      askHistory.value.unshift(newHistory)
      ElMessage.success('✅ 问题已发送，我们会通过邮件回复你')
      askContent.value = ''
      removeImage()
    } else {
      ElMessage.error(result.message || '发送失败，请稍后重试')
    }
  } catch (error) {
    console.error('提交问题失败:', error)
    ElMessage.error('网络错误，请稍后重试')
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