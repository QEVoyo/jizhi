<template>
  <div class="qa-page">
    <div class="qa-container">
      <div class="qa-header">
        <el-button text class="back-btn" @click="goBack">
          <i class="fas fa-arrow-left"></i> 返回
        </el-button>
        <h1>帮助中心</h1>
        <div></div>
      </div>

      <el-divider />

      <div class="search-section">
        <div class="search-wrapper">
          <i class="fas fa-search search-icon"></i>
          <el-input v-model="searchKeyword" placeholder="输入关键词搜索问题..." size="large" clearable @input="filterFAQs" />
        </div>
      </div>

      <div class="tab-section">
        <button v-for="tab in tabs" :key="tab.key" class="tab-item" :class="{ active: activeTab === tab.key }" @click="switchTab(tab.key)">
          {{ tab.icon }} {{ tab.label }}
        </button>
      </div>

      <div class="faq-list">
        <div v-for="item in filteredFAQs" :key="item.id" class="faq-item" @click="toggleFAQ(item.id)">
          <div class="faq-question">
            <span class="faq-icon">{{ item.expanded ? '▼' : '▶' }}</span>
            <span class="faq-title">{{ item.question }}</span>
            <span class="faq-tag" :style="{ background: item.tagColor + '20', color: item.tagColor }">{{ item.tag }}</span>
          </div>
          <div v-show="item.expanded" class="faq-answer">
            <div v-for="(step, idx) in item.answer" :key="idx" class="faq-step">{{ step }}</div>
            <div v-if="item.actions && item.actions.length" class="faq-actions">
              <button v-for="action in item.actions" :key="action.label" class="faq-action-btn" @click.stop="handleAction(action)">
                {{ action.icon }} {{ action.label }}
              </button>
            </div>
          </div>
        </div>
        <div v-if="!filteredFAQs.length" class="empty-state">
          <i class="fas fa-search" style="font-size:48px;opacity:.3"></i>
          <p>没有找到相关问题</p>
          <p style="font-size:13px;opacity:.6">试试其他关键词，或者使用下方即时答疑</p>
        </div>
      </div>

      <div class="qa-divider">
        <span>还有问题？</span>
        <el-button text size="small" @click="showAskHistory = !showAskHistory">{{ showAskHistory ? '收起历史' : '查看历史提问' }}</el-button>
      </div>

      <div class="ask-section">
        <div class="ask-wrapper">
          <el-input v-model="askContent" placeholder="输入你的问题，我们将通过邮件回复你..." size="large" @keyup.enter="submitAsk" />
          <el-upload ref="uploadRef" :auto-upload="false" :limit="1" accept="image/*" :on-change="handleImageUpload" :on-remove="handleImageRemove" class="upload-btn">
            <el-button class="upload-trigger"><i class="fas fa-image"></i></el-button>
          </el-upload>
          <el-button type="primary" :loading="askSubmitting" @click="submitAsk"><i class="fas fa-paper-plane"></i> 发送</el-button>
        </div>
        <div v-if="uploadedImage" class="upload-preview">
          <img :src="uploadedImage" alt="上传图片预览" />
          <el-button size="small" circle @click="removeImage"><i class="fas fa-times"></i></el-button>
        </div>
        <div class="ask-hint">{{ authStore.isLoggedIn ? '问题将发送到管理员邮箱，我们会尽快回复你（支持图片上传）' : '登录后提问可收到邮件回复，当前将以访客身份提交' }}</div>
      </div>

      <div v-if="showAskHistory" class="ask-history">
        <div class="history-title">提问历史</div>
        <div v-for="item in askHistory" :key="item.id" class="history-item">
          <div class="history-question">{{ item.question }}</div>
          <div class="history-meta">
            <span class="history-status" :class="item.status === '已回复' ? 'resolved' : 'pending'">{{ item.status === '已回复' ? '已回复' : '待回复' }}</span>
            <span class="history-time">{{ item.time }}</span>
          </div>
        </div>
        <div v-if="!askHistory.length" class="history-empty">暂无提问记录</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const searchKeyword = ref('')

const tabs = [
  { key: 'all', icon: '', label: '全部' },
  { key: 'guide', icon: '', label: '入门指南' },
  { key: 'subject', icon: '', label: '学科计划' },
  { key: 'resource', icon: '', label: '资源库' },
  { key: 'vocab', icon: '', label: '词条本' },
  { key: 'agent', icon: '', label: '智能体中心' },
  { key: 'career', icon: '', label: '学程' },
  { key: 'community', icon: '', label: '社区' },
  { key: 'account', icon: '', label: '账号管理' },
  { key: 'api', icon: '', label: 'API配置' },
]
const activeTab = ref('all')

const faqs = ref([
  // ==================== 入门指南 ====================
  { id: 1, tag: '入门指南', tagColor: '#4CAF50', question: '如何开始学习？', answer: [
    '1. 注册登录后，直接进入「小基」主界面与 AI 学习伙伴聊天（任何页面按 Ctrl+K 可全局搜索跳转）',
    '2. 前往「学科计划」选一个考纲：完成「摸底诊断」，或先做一套「真题套卷」交卷后按答卷生成计划',
    '3. 按「每日任务」学习：AI 实时讲解 + 做题练习 + 错题复习，系统自动更新知识点掌握度',
    '4. 对话里问的单词自动收进「词条本」；「资源库」可自由生成题目、管理题集',
    '5. 在「智能体中心」查看 5 个智能体的使用统计并磨合参数；「学程」查看段位成长',
  ], expanded: false, actions: [
    { icon: '', label: '去学科计划', route: '/subject-plan' },
    { icon: '', label: '去资源库', route: '/resource-lib' },
  ]},
  { id: 5, tag: '入门指南', tagColor: '#4CAF50', question: '全局搜索怎么用？', answer: [
    '全局搜索让你在任何页面快速跳到任何页面：',
    '',
    '入口：侧边栏顶部搜索框，或任意页面按 Ctrl+K 唤起',
    '范围：全站页面 + 17 个考纲 + 12 套真题卷 + 5 个智能体 + 你词条本里的词，支持中文/英文缩写/拼音首字母模糊匹配',
    '快捷键：↑↓ 选择、Enter 跳转、Esc 关闭',
    '空态管理：最近访问和搜索历史可单条删除或一键清空',
    '自定义钉选：点「＋ 添加自定义项」→ 从全部页面里点选收录常用入口（再点一次移除，✎ 可重命名）',
  ], expanded: false, actions: [
    { icon: '', label: '去小基主页', route: '/home' },
  ]},
  { id: 2, tag: '入门指南', tagColor: '#4CAF50', question: '维度宇宙学情画像各维度代表什么？', answer: [
    '维度宇宙学情画像从多个维度全面评估你的学习状态：',
    '',
    'K 知识基础：根据你做过的所有题目计算掌握度，分数越高基础越牢固',
    'C 认知风格：分析你习惯的做题方式，综合型、探索型等不同风格',
    'E 易错偏好：根据错题本比例，找到需要重点刷题的方向',
    'G 学习目标：统计你创建的题集和目标，衡量长期规划能力',
    'I 兴趣领域：扫描高频知识点，找出你最感兴趣的方向',
    'P 学习人格：综合各项数据，生成专属学习者标签（如稳健型/创新型）',
    '',
    '前往侧边栏「个人画像」查看完整雷达图和 AI 深度画像',
  ], expanded: false, actions: [
    { icon: '', label: '去查看维度宇宙', route: '/profile-card' },
  ]},
  { id: 3, tag: '入门指南', tagColor: '#4CAF50', question: '学习路径如何动态调整？', answer: [
    '系统会根据你的实时答题数据动态调整学习计划：',
    '',
    '掌握度 ≥ 80% → 自动减少该知识点练习，进入下一阶段',
    '掌握度 40%-60% → 保持常规练习，推送补充材料',
    '掌握度 < 40% → 增加练习频次，加入错题本重点复习',
    '每次答题后通过 EWMA 加权平均更新掌握度（新分数 = 旧×0.7 + 本次×0.3）',
  ], expanded: false, actions: [
    { icon: '', label: '去个人中心', route: '/profile' },
  ]},
  { id: 4, tag: '入门指南', tagColor: '#4CAF50', question: '如何查看学习进度？', answer: [
    '学习进度可以从以下入口查看：',
    '',
    '侧边栏「个人画像」→ 查看维度宇宙学情画像各维度掌握度',
    '学科计划 → 考纲详情页 → 知识点 Tab 查看每个知识点的掌握度卡片（红→绿渐变）',
    '学程 → 查看段位等级和任务完成进度',
  ], expanded: false, actions: [
    { icon: '', label: '去学科计划', route: '/subject-plan' },
    { icon: '', label: '去学程', route: '/career' },
  ]},

  // ==================== 学科计划 ====================
  { id: 10, tag: '学科计划', tagColor: '#06b6d4', question: '学科计划是什么？怎么开始？', answer: [
    '学科计划是本平台的核心备考系统，覆盖 17 个考纲（CET-4/6、考研、雅思、托福、教资、CPA、法考、计算机二级、算法等）。',
    '',
    '使用流程：',
    '1. 进入「学科计划」→ 浏览考纲列表，点击感兴趣的考纲卡片',
    '2. 生成计划有两条通道（见「诊断摸底和答卷生成怎么操作」）：摸底诊断，或先做真题交卷后按答卷生成',
    '3. 设定目标分数、备考周期、每日学习时长后，AI 生成三阶段备考计划（基础期补弱项 → 强化期全覆盖 → 冲刺期实战）',
    '4. 按「每日任务」Tab 逐天学习，查看「知识点」掌握度变化，用「真题套卷」检验水平',
  ], expanded: false, actions: [
    { icon: '', label: '去学科计划', route: '/subject-plan' },
  ]},
  { id: 11, tag: '学科计划', tagColor: '#06b6d4', question: '考纲是什么？题库怎么用？', answer: [
    '17 个考纲覆盖四六级、考研、雅思托福、计算机二级、教资、CPA、法考、算法等，题库共 19,000+ 道题、11 种题型。',
    '',
    '题库功能：',
    '维度筛选 — 按词汇/语法/阅读等维度过滤题目',
    '子分类 + 题型筛选 — 精确定位你想练的题目类型',
    '作答状态 — 每题左侧颜色条（红=薄弱/黄=待巩固/绿=优势）+ 作答次数标签',
    '收藏 — 点击心形按钮收藏，支持收藏筛选',
    '展开看答案 — 点击题目展开查看正确答案和解析',
    '练习按钮 — 每道题右侧的 ▶ 按钮，点击直接跳转做题页',
  ], expanded: false, actions: [
    { icon: '', label: '去学科计划', route: '/subject-plan' },
  ]},
  { id: 12, tag: '学科计划', tagColor: '#06b6d4', question: '诊断摸底和答卷生成怎么操作？', answer: [
    '生成备考计划有两条通道（考纲详情页「生成备考计划」弹窗选择）：',
    '',
    '通道一 · 摸底生成：',
    '  Step 1 答题 — 系统按考纲维度抽取诊断题（11 种题型，底部进度条显示进度）',
    '  Step 2 设目标 — 目标分数、备考周期（7-90天）、每日学习时长（15-180分钟）',
    '  Step 3 生成 — AI 创建带日期解锁的三阶段每日任务',
    '',
    '通道二 · 答卷生成：',
    '  先完成一套真题卷交卷 → 弹窗里该卷显示 ✅ 和上次分数，可直接选择 → AI 按答卷错题薄弱点生成计划（没做过的卷子灰色禁用）',
  ], expanded: false, actions: [
    { icon: '', label: '去学科计划', route: '/subject-plan' },
  ]},
  { id: 17, tag: '学科计划', tagColor: '#06b6d4', question: '真题套卷怎么用？', answer: [
    '学科计划内置 12 套真实真题卷（四六级/考研/法考/教资/CPA/计算机二级/行测等）：',
    '',
    '入口：考纲详情页「真题套卷」区，或全局搜索直接搜卷名',
    '做题模式 — 隐藏答案 + 计时器 + 分区导航，交卷即出分（客观题自动判 + 主观题 AI 批改）',
    '解析模式 — 你的答案/正确率/解析/AI 错因分析（交卷后自动生成并缓存，二次打开秒开不重复烧 AI）',
    '生成计划 — 交卷后点「生成备考计划」，AI 按答卷薄弱点生成三阶段备考计划',
    '注意：听力/上机操作等无法模拟的卷面会标注「不可练习」，分数按可练部分计算',
  ], expanded: false, actions: [
    { icon: '', label: '去学科计划', route: '/subject-plan' },
  ]},
  { id: 13, tag: '学科计划', tagColor: '#06b6d4', question: '每日任务怎么完成？', answer: [
    '生成计划后，在考纲详情页「每日任务」Tab 查看当天学习内容，任务按三阶段（基础→强化→冲刺）排布：',
    '',
    '📖 学习讲解 — 点击后 AI 按本日题目实时生成讲解（学习目标/核心知识点/解题方法/常见错误），生成一次后缓存，二次打开秒现',
    '✏️ 去练习 — 带真实题目跳做题页，逐题提交（11 种题型全支持）',
    '🎬 视频推送 — 即将上线（占位）',
    '',
    '第二天自动解锁新任务，题目不会与已做/已分配题目重复',
  ], expanded: false, actions: [
    { icon: '', label: '去学科计划', route: '/subject-plan' },
  ]},
  { id: 14, tag: '学科计划', tagColor: '#06b6d4', question: '知识点掌握度卡片怎么看？', answer: [
    '考纲详情页顶部有一排彩色掌握度卡片，展示每个知识点的当前掌握程度：',
    '',
    '卡片颜色 20 级渐变：红（薄弱 <60%）→ 黄绿（待巩固 60-80%）→ 绿（优势 ≥80%）',
    '掌握度采用 EWMA 加权平均：每次答题后 新分数 = 旧分数×0.7 + 本次结果×0.3',
    '点击卡片上的「攻克」按钮 → 自动筛选该知识点的题目 → 跳转集中练习',
    '题库列表每道题也有迷你掌握度条，颜色同上',
  ], expanded: false, actions: [
    { icon: '', label: '去学科计划', route: '/subject-plan' },
  ]},
  { id: 15, tag: '学科计划', tagColor: '#06b6d4', question: '错题本和知识点 Tab 有什么用？', answer: [
    '在考纲详情页（需先生成计划）有两个专属 Tab：',
    '',
    '错题本 Tab：显示你做错的题目，包含你的答案和正确答案对比，方便针对性复习',
    '知识点 Tab：以进度条展示每个知识点的掌握度、正确次数/总次数，直观看到薄弱环节',
  ], expanded: false, actions: [
    { icon: '', label: '去学科计划', route: '/subject-plan' },
  ]},
  { id: 16, tag: '学科计划', tagColor: '#06b6d4', question: '如何删除或重新生成计划？', answer: [
    '在考纲详情页的顶部计划摘要栏（显示目标分数、周期、每日时长、正确率的横条）：',
    '',
    '点击「删除计划」→ 确认弹窗 → 删除当前计划（做题记录保留）',
    '点击「重新摸底」→ 重新进入诊断流程，生成新计划',
  ], expanded: false, actions: [
    { icon: '', label: '去学科计划', route: '/subject-plan' },
  ]},

  // ==================== 资源库 ====================
  { id: 20, tag: '资源库', tagColor: '#42A5F5', question: '如何生成题目？', answer: [
    '1. 进入「资源库」→ 点击「生成题目」Tab',
    '2. 选择学科、知识点、题型和难度等级',
    '3. 点击「生成」，AI 为你创建一道全新题目',
    '4. 题目自动进入做题页面，支持「换题型」和「重新生成」',
  ], expanded: false, actions: [
    { icon: '', label: '去资源库', route: '/resource-lib' },
  ]},
  { id: 21, tag: '资源库', tagColor: '#42A5F5', question: '错题本是如何收录的？', answer: [
    '答错的题目自动收录到错题本，记录错题次数，方便针对性复习。',
    '',
    '查看位置：资源库 → 错题本 Tab（按考纲分组），或考纲详情页「错题本」Tab（需先生成计划）',
    '题库里每道题有作答状态标记：薄弱（红）/ 待巩固（黄）/ 优势（绿）',
    '每道错题可点击直接跳转做题页重新练习',
  ], expanded: false, actions: [
    { icon: '', label: '去错题本', route: '/resource-lib' },
  ]},
  { id: 22, tag: '资源库', tagColor: '#42A5F5', question: '如何创建和使用题集？', answer: [
    '创建题集：资源库 → 我的题集 Tab → 新建题集 → 输入名称和描述',
    '加入题集：做题页面点击「加入题集」→ 选择目标题集；AI 生成的题目也可以直接收入题集',
    '题集功能：',
    '  自动计算加权平均掌握度（进度条颜色红→绿）',
    '  支持整卷练习和逐题练习',
  ], expanded: false, actions: [
    { icon: '', label: '去题集管理', route: '/resource-lib' },
  ]},
  { id: 23, tag: '资源库', tagColor: '#42A5F5', question: '掌握度是如何计算的？', answer: [
    '每次作答后，系统通过 AI 或规则判题，采用 EWMA 加权平均更新掌握度：',
    '',
    '已有记录 → 新分数 = 旧分数 × 0.7 + 本次(100或0) × 0.3',
    '首次做题 → 初始值 = 70（正确）或 30（错误）',
    '',
    '掌握度含义：',
    '  < 60%  薄弱（需重点复习）',
    '  60-80% 待巩固',
    '  ≥ 80%  优势（可进入下一阶段）',
  ], expanded: false },
  { id: 24, tag: '资源库', tagColor: '#42A5F5', question: '侧边栏工具箱怎么用？', answer: [
    '侧边栏下方工具区有 4 个工具图标，点击右侧滑出毛玻璃面板：',
    '',
    ' 打卡 — 创建打卡项目（如"每日背单词"），每天点一下完成打卡，进度条跟踪',
    ' 倒计时 — 设置目标日期和事件名（如"CET-6 考试"），显示剩余天数',
    ' 计时器 — 支持正向计时和倒计时，完成后自动记录到学习日志',
    ' 学习日志 — 按日期分组展示学习记录（打卡记录、计时器完成记录等）',
    '',
    '所有工具数据保存在服务端，不会丢失。',
  ], expanded: false, actions: [
    { icon: '', label: '去小基主页', route: '/home' },
  ]},
  { id: 25, tag: '资源库', tagColor: '#42A5F5', question: '如何查看生成历史？', answer: [
    '1. 进入「资源库」→「生成历史」Tab',
    '2. 默认按时间倒序显示所有生成记录',
    '3. 使用题型筛选下拉框按题型过滤',
    '4. 支持搜索和分页浏览（词条本的薄弱词出题也生成在这里）',
  ], expanded: false, actions: [
    { icon: '', label: '去资源库', route: '/resource-lib' },
  ]},

  // ==================== 词条本 ====================
  { id: 70, tag: '词条本', tagColor: '#14b8a6', question: '词条本是什么？词条怎么收进来？', answer: [
    '词条本自动收集你在学习过程中遇到的生词，支持复习和定向出题。',
    '',
    '收录方式（自动，无需手动添加）：',
    '1. 在小基聊天里问词义（如发「abandon 什么意思」）→ 输入框上方出现词条卡并自动收录',
    '2. 对话/识图回复中的英文生词会被自动提取为词条卡',
    '3. 在词条卡上点「认识 ✓ / 不认识 ✗」打分，实时更新熟练度',
    '',
    '同一个词全站共享一份 AI 释义（全局缓存，不重复生成）',
  ], expanded: false, actions: [
    { icon: '', label: '去词条本', route: '/wordbook' },
  ]},
  { id: 71, tag: '词条本', tagColor: '#14b8a6', question: '词条熟练度是怎么计算的？', answer: [
    '熟练度与知识点掌握度同构，采用 EWMA 平滑：',
    '',
    '新分数 = 旧分数 × 0.7 + 本次目标 × 0.3',
    '点「认识」目标 100，点「不认识」目标 20',
    '',
    '熟练度含义：≥80 已掌握（绿）/ 60-80 巩固中 / <60 薄弱（红，进入复习队列）',
    '词条本列表按熟练度升序排列，薄弱词排在最前',
  ], expanded: false, actions: [
    { icon: '', label: '去词条本', route: '/wordbook' },
  ]},
  { id: 72, tag: '词条本', tagColor: '#14b8a6', question: '复习模式怎么用？', answer: [
    '词条本页点「复习薄弱词」进入复习模式：',
    '',
    '逐卡过关 — 薄弱词一张张展示（词 + 音标 + 释义 + 例句），点「认识/不认识」打分',
    '顶部进度显示 N/M，全部完成后自动返回列表',
    '打分会实时更新熟练度，熟练度 ≥80 的词不再出现在复习队列',
  ], expanded: false, actions: [
    { icon: '', label: '去复习', route: '/wordbook' },
  ]},
  { id: 73, tag: '词条本', tagColor: '#14b8a6', question: '薄弱词怎么出题练习？', answer: [
    '词条本页点「薄弱词出题」：',
    '',
    'AI 按你的薄弱词逐词生成单选题（每次最多 10 个词）',
    '生成的题写入资源库「生成历史」，点提示跳转后即可练习',
  ], expanded: false, actions: [
    { icon: '', label: '去词条本', route: '/wordbook' },
  ]},

  // ==================== 智能体中心 ====================
  { id: 80, tag: '智能体中心', tagColor: '#8b5cf6', question: '智能体中心是什么？', answer: [
    '智能体中心展示你身边 5 个 AI 智能体（对话/规划/生成/评估/小基）的真实使用情况：',
    '',
    '总览页 — 总调用/活跃智能体/计划完成率等 KPI + 协作闭环 + 协同增益对照（如陪伴日 vs 非陪伴日做题量）+ 路由转化',
    '详情页 — 每个智能体的 30 天趋势、触点计数（调用发生在哪些场景）、特点面板',
    '核心价值是「磨合」：系统根据你的行为数据自动微调智能体参数，越用越贴合你',
  ], expanded: false, actions: [
    { icon: '', label: '去智能体中心', route: '/agent-center' },
  ]},
  { id: 81, tag: '智能体中心', tagColor: '#8b5cf6', question: '参数调节和自动托管怎么用？', answer: [
    '进入任一智能体详情页的「参数调节」区：',
    '',
    '每个参数有对应控件（分段选择/滑块/开关），手动调整后点「保存」立即生效，下次调用实时拼装',
    '每个参数可独立开启「自动托管」：开启后控件禁用，由磨合规则自动调整（规则文案写在参数卡上）',
    '详情页的「可行动建议」可以「一键应用」直接写入参数',
    '也可以「重置出厂」恢复默认值',
  ], expanded: false, actions: [
    { icon: '', label: '去调节参数', route: '/agent-center' },
  ]},
  { id: 82, tag: '智能体中心', tagColor: '#8b5cf6', question: '磨合引擎是怎么工作的？', answer: [
    '磨合引擎不做模型微调，做「参数自适应」：你的行为数据 → 规则引擎 → 自动微调参数 → 下次调用生效。',
    '',
    '示例规则：',
    '  计划完成率 <50% → 每日任务量自动 -2；>85% → +1',
    '  题集收录率 <60% → 出题难度自动 -2',
    '  错题本 ≥10 题且未开启 → 自动开启错题针对性出题',
    '  连续 3 天没学习 → 小基主动关心频率 +1 档（新用户不打扰）',
    '',
    '保护机制：关闭自动托管的参数绝不碰；同一参数 7-14 天冷却期；详情页「立即评估」手动触发 + 系统每日后台自动评估',
  ], expanded: false, actions: [
    { icon: '', label: '去智能体中心', route: '/agent-center' },
  ]},
  { id: 83, tag: '智能体中心', tagColor: '#8b5cf6', question: '统计数据从哪里来？', answer: [
    '智能体中心的每个数字都来自你的真实行为记录（19 个触点）：',
    '',
    '对话答疑/规划分流/生成分流/评估分流 → 小基快捷提问与对话分流打点',
    '批改题量 → 做题提交批改；真题分析 → 交卷记录',
    '每日讲解 → 每日任务学习讲解记录；词条讲解 → 词条抓取记录',
    '',
    '每个数字要么解释学习效果、要么导向下一步动作，不展示无意义的计数',
  ], expanded: false, actions: [
    { icon: '', label: '去智能体中心', route: '/agent-center' },
  ]},

  // ==================== 学程 ====================
  { id: 30, tag: '学程', tagColor: '#F44336', question: '学程是什么？', answer: [
    '学程是基智的游戏化激励体系，通过段位、等级、任务、成就四个维度，将学习行为转化为可视化的成长路径。',
    '',
    '四大模块：',
    '  段位 — 7 大段位（启程→求索→明理→致知→笃行→臻境→传说），每段 5 小级',
    '  等级 — 等差数列升级，第 n 级需要 n+1 分',
    '  任务 — 播种（新手）→ 施肥（每日5个）→ 发芽（长期阶梯）',
    '  成就 — 25 个一次性成就，涵盖学习全场景',
  ], expanded: false, actions: [
    { icon: '', label: '去学程', route: '/career' },
  ]},
  { id: 31, tag: '学程', tagColor: '#F44336', question: '段位系统是如何计算的？', answer: [
    '段位由积分驱动，累计自动晋升：',
    '',
    '7 大段位：启程 → 求索 → 明理 → 致知 → 笃行 → 臻境 → 传说',
    '每大段含 5 小段（I→V），每小段 100 分，满 500 晋升下一大段',
    '积分来源：完成每日任务(10-70分)、解锁成就(15-500分)、段位晋升奖励',
    '',
    '查看位置：学程 → 登攀',
  ], expanded: false, actions: [
    { icon: '', label: '查看段位', route: '/career/rank' },
  ]},
  { id: 32, tag: '学程', tagColor: '#F44336', question: '等级系统是如何计算的？', answer: [
    '等差数列升级：第 1 级需 2 分，第 2 级需 3 分，第 n 级需 n+1 分',
    '积分与段位积分共享，蓝色进度条实时展示当前等级进度',
    '',
    '查看位置：学程 → 登攀',
  ], expanded: false, actions: [
    { icon: '', label: '查看等级', route: '/career/rank' },
  ]},
  { id: 33, tag: '学程', tagColor: '#F44336', question: '三种任务有什么区别？', answer: [
    '播种任务（新手引导）— 首次使用各项功能，完成后解锁施肥任务',
    '施肥任务（每日5个）— 如"完成3道题""学习15分钟"，可换一批（每日限1次）',
    '发芽任务（长期阶梯）— 如"累计100道题""连续打卡7天"，阶梯式奖励',
    '',
    '查看位置：学程 → 勤耕',
  ], expanded: false, actions: [
    { icon: '', label: '去任务', route: '/career/tasks' },
  ]},
  { id: 34, tag: '学程', tagColor: '#F44336', question: '成就有哪些？如何解锁？', answer: [
    '共 25 个一次性成就，涵盖学习、社交、成长、资源四大类别',
    '成就状态：未解锁 → 条件达成可领取 → 已领取',
    '解锁后获得积分奖励，同时记录到攀登足迹',
    '',
    '查看位置：学程 → 拾贝',
  ], expanded: false, actions: [
    { icon: '', label: '查看成就', route: '/career/achievements' },
  ]},
  { id: 35, tag: '学程', tagColor: '#F44336', question: '积分可以从哪些行为获得？', answer: [
    '积分是段位、等级、成就的通用货币：',
    '',
    '完成每日任务  10-70 分',
    '解锁成就      15-500 分',
    '段位晋升      50-500 分',
    '完成题目      按正确率评估',
    '打卡          10 分',
    '发布动态      15 分',
    '分享题集      20 分',
  ], expanded: false, actions: [
    { icon: '', label: '去学程', route: '/career' },
  ]},

  // ==================== 社区 ====================
  { id: 40, tag: '社区', tagColor: '#9C27B0', question: '什么是社区？', answer: [
    '社区是轻量化学习社交空间：',
    '  发布学习笔记和动态，分享学习心得',
    '  添加好友，查看好友资料和排行榜',
    '  分享题集，一键收纳好友分享的题目',
    '  在动态广场互动，点赞评论',
  ], expanded: false, actions: [
    { icon: '', label: '去社区', route: '/community' },
  ]},
  { id: 41, tag: '社区', tagColor: '#9C27B0', question: '如何添加好友？', answer: [
    '1. 进入「社区」→ 搜索用户（按账号搜索）',
    '2. 点击用户卡片上的「添加好友」',
    '3. 对方确认后，互相查看资料卡和分享题集',
  ], expanded: false, actions: [
    { icon: '', label: '去添加好友', route: '/community' },
  ]},
  { id: 42, tag: '社区', tagColor: '#9C27B0', question: '如何收藏动态？', answer: [
    '在动态广场看到喜欢的动态，点击收藏即可：',
    '',
    '收藏的动态统一在社区「收藏」页查看',
    '收藏是单向的，对方不会收到任何通知',
  ], expanded: false, actions: [
    { icon: '', label: '去社区收藏', route: '/community/collections' },
  ]},
  { id: 43, tag: '社区', tagColor: '#9C27B0', question: '好友之间可以查看哪些数据？', answer: [
    '好友互通权限：',
    '  可查看 — 资料卡（昵称、头像、段位等级）、排行榜数据',
    '  可接收 — 分享的题库和题集',
    '  不可查看 — 错题本和隐私设置内容',
  ], expanded: false, actions: [
    { icon: '', label: '查看好友', route: '/community' },
  ]},
  { id: 44, tag: '社区', tagColor: '#9C27B0', question: '动态广场是什么？', answer: [
    '动态广场是社区信息流页面：',
    '  全部动态 / 好友动态可切换筛选',
    '  发布学习笔记和心得',
    '  点赞、评论、收藏互动',
    '  举报违规内容',
  ], expanded: false, actions: [
    { icon: '', label: '去动态广场', route: '/community' },
  ]},

  // ==================== 账号管理 ====================
  { id: 50, tag: '账号管理', tagColor: '#FF9800', question: '如何修改昵称、头像和简介？', answer: [
    '个人资料的编辑统一在「设置」页完成：',
    '',
    '入口：侧边栏「个人中心」→「编辑资料与设置」按钮，或侧边栏「设置」图标',
    '头像：设置 → 个人信息 → 点击头像上传新图片',
    '昵称/简介：设置 → 个人信息 → 编辑保存',
  ], expanded: false, actions: [
    { icon: '', label: '去设置', route: '/settings' },
  ]},
  { id: 51, tag: '账号管理', tagColor: '#FF9800', question: '如何修改密码和绑定微信？', answer: [
    '在「设置 → 账号安全」完成：',
    '',
    '修改密码 — 输入当前密码验证 → 设置新密码 → 确认',
    '微信绑定 — 点击绑定 → 展示二维码 → 手机微信扫码授权完成绑定（绑定后可用微信扫码登录）',
    '',
    '邮箱用于登录和邮件回复，暂不支持自助修改',
  ], expanded: false, actions: [
    { icon: '', label: '去设置', route: '/settings' },
  ]},
  { id: 52, tag: '账号管理', tagColor: '#FF9800', question: '设置页还有哪些功能？', answer: [
    '「设置」页集中了全部个人配置（7 大模块）：',
    '',
    '个人信息 — 昵称/简介/头像',
    '学习偏好 — 7 项偏好（学习阶段/目标/风格等）',
    '外观 — 浅色/深色/跟随系统',
    '隐私 — 在线/隐身状态',
    '通知设置 — 8 个开关 + 每日推荐/总结时间',
    '账号安全 — 改密码 + 微信绑定',
    'AI 与 API — 跳转小基 AI 设置和 API 管理中心',
  ], expanded: false, actions: [
    { icon: '', label: '去设置', route: '/settings' },
  ]},
  { id: 53, tag: '账号管理', tagColor: '#FF9800', question: '如何退出登录？', answer: [
    '点击侧边栏底部「退出登录」→ 弹窗确认 → 清除登录态跳转登录页',
  ], expanded: false },

  // ==================== API 配置 ====================
  { id: 60, tag: 'API配置', tagColor: '#FF5722', question: 'API 管理是做什么的？', answer: [
    'API 管理中心展示全站 AI 能力的模型平台和调用预览：',
    '',
    'AI 对话 — DeepSeek V4.1 Flash / 智谱 GLM（气泡对话预览 + 打字机重播）',
    '图片理解 — DeepSeek V4.1 Flash（原生多模态，与文本同一模型）（题目截图 mockup + 解析气泡）',
    '语音合成 — 千问语音（真实 TTS 试听，播放缓存复用）',
    '系统状态 — 火山引擎(豆包) 主链路/待命备用',
    '视频数字人 — 腾讯云（占位中，上线后启用）',
    '',
    '当前全站 AI 调用使用平台官方 Key，无需自己配置即可使用；「用户自带 Key 优先、平台兜底」为后期规划。',
  ], expanded: false, actions: [
    { icon: '', label: '去配置 API', route: '/api-center' },
  ]},
  { id: 61, tag: 'API配置', tagColor: '#FF5722', question: '如何获取各平台 API Key？', answer: [
    'DeepSeek：platform.deepseek.com → API Keys → 创建 Key（格式 sk-xxx）',
    '阿里云百炼（千问小基）：bailian.console.aliyun.com → API-KEY → 创建 Key（格式 sk-xxx）',
    '火山引擎(豆包)：console.volcengine.com → 开通 ARK → 创建接入点 → 获取 Key + Endpoint ID',
    '智谱 GLM：open.bigmodel.cn → API Keys → 创建 Key',
    '腾讯云：console.cloud.tencent.com → 访问管理 → API密钥管理 → SecretId + SecretKey',
    '讯飞：console.xfyun.cn → 创建应用 → APPID + API Key + API Secret',
    '',
    '所有平台的 Key 只显示一次，请立即保存！',
  ], expanded: false, actions: [
    { icon: '', label: '去配置 API', route: '/api-center' },
  ]},
  { id: 62, tag: 'API配置', tagColor: '#FF5722', question: '配置区里填的 Key 会生效吗？', answer: [
    '当前配置区为本地演示（只保存在你的浏览器 localStorage），不会影响平台实际调用。',
    '',
    '后期规划：接入后端保存/验证接口（加密存储 + 掩码回显），实现「用户自带 Key 优先、平台 Key 兜底」——自带 Key 的额度自己掌控，平台 Key 保证永远可用。',
  ], expanded: false, actions: [
    { icon: '', label: '去配置 API', route: '/api-center' },
  ]},
  { id: 63, tag: 'API配置', tagColor: '#FF5722', question: '需要自己配置 API Key 吗？', answer: [
    '当前不需要：',
    '',
    '全站 AI 功能（对话/识图/语音/批改/出题）默认使用平台官方 Key，注册即可直接使用',
    'API 管理中心的预览区可以体验各模型效果（对话打字机/识图解析/TTS 试听）',
    '',
    '未来启用自带 Key 后，没有 Key 的用户自动回落到平台 Key，不影响使用',
  ], expanded: false, actions: [
    { icon: '', label: '去配置 API', route: '/api-center' },
  ]},
])

const askContent = ref('')
const askSubmitting = ref(false)
const uploadedImage = ref(null)
const uploadRef = ref(null)
const showAskHistory = ref(false)
const askHistory = ref([
  { id: 1, question: '如何配置 API Key？', status: '已回复', time: '2026-07-08' },
  { id: 2, question: '学科计划怎么生成备考方案？', status: '已回复', time: '2026-07-08' },
  { id: 3, question: '侧边栏工具箱怎么用？', status: '待回复', time: '2026-07-28' },
])

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push('/')
}
function switchTab(tab) { activeTab.value = tab }
function toggleFAQ(id) { const item = faqs.value.find(f => f.id === id); if (item) item.expanded = !item.expanded }
function filterFAQs() {}

const filteredFAQs = computed(() => {
  let result = faqs.value

  const tagMap = {
    guide: '入门指南',
    subject: '学科计划',
    resource: '资源库',
    vocab: '词条本',
    agent: '智能体中心',
    career: '学程',
    community: '社区',
    account: '账号管理',
    api: 'API配置',
  }
  if (activeTab.value !== 'all') {
    const tag = tagMap[activeTab.value]
    if (tag) result = result.filter(f => f.tag === tag)
  }

  if (searchKeyword.value.trim()) {
    const kw = searchKeyword.value.trim().toLowerCase()
    result = result.filter(f => f.question.toLowerCase().includes(kw) || f.answer.join('').toLowerCase().includes(kw))
  }

  return result
})

function handleAction(action) { if (action.route) router.push(action.route) }
function handleImageUpload(file) { const r = new FileReader(); r.onload = e => uploadedImage.value = e.target.result; r.readAsDataURL(file.raw) }
function handleImageRemove() { removeImage() }
function removeImage() { uploadedImage.value = null; if (uploadRef.value) uploadRef.value.clearFiles() }

async function submitAsk() {
  if (!askContent.value.trim() && !uploadedImage.value) { ElMessage.warning('请先输入问题或上传图片'); return }
  askSubmitting.value = true
  try {
    const res = await fetch('/api/qa/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: authStore.user?.id || '', user_email: authStore.user?.email || '', user_nickname: authStore.user?.nickname || '用户', question: askContent.value.trim() || '（图片提问）', has_image: !!uploadedImage.value, image_data: uploadedImage.value || null }),
    })
    if (res.ok) {
      askHistory.value.unshift({ id: askHistory.value.length + 1, question: askContent.value.trim() || '（含图片提问）', status: '待回复', time: new Date().toISOString().slice(0, 10) })
      ElMessage.success('问题已发送，我们会通过邮件回复你')
      askContent.value = ''; removeImage()
    } else {
      const d = await res.json(); ElMessage.error(d.message || '发送失败')
    }
  } catch { ElMessage.error('网络错误，请稍后重试') }
  finally { askSubmitting.value = false }
}
</script>

<style scoped>
.qa-page { min-height: 100vh; display: flex; justify-content: center; padding: 30px 20px; background: transparent; }
.qa-container { max-width: 820px; width: 100%; padding: 28px 36px; border-radius: 18px; background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,.08); box-shadow: 0 8px 32px rgba(0,0,0,.06); height: fit-content; max-height: 90vh; overflow-y: auto; }
.qa-container::-webkit-scrollbar { width: 4px; }
.qa-container::-webkit-scrollbar-thumb { background: rgba(128,128,128,.2); border-radius: 2px; }
.qa-header { display: flex; align-items: center; justify-content: space-between; }
.qa-header h1 { font-size: 26px; color: var(--text-primary); margin: 0; }
.back-btn { color: var(--text-secondary) !important; transition: all .3s ease !important; font-size: 15px; padding: 8px 12px; border-radius: 10px; }
.back-btn:hover { color: var(--text-primary) !important; transform: translateX(-4px); background: color-mix(in srgb, var(--surface, #ffffff) 8%, transparent); }
.el-divider { margin: 14px 0; }
.search-section { margin: 4px 0 14px; }
.search-wrapper { position: relative; }
.search-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); color: var(--text-muted); font-size: 14px; z-index: 1; }
.search-wrapper :deep(.el-input__wrapper) { padding-left: 38px; background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent) !important; border: 1px solid var(--line-soft) !important; border-radius: 12px !important; }
.search-wrapper :deep(.el-input__wrapper:hover) { border-color: var(--line) !important; }
.search-wrapper :deep(.el-input__wrapper.is-focus) { border-color: color-mix(in srgb, var(--brand) 40%, transparent) !important; box-shadow: 0 0 0 4px color-mix(in srgb, var(--brand) 8%, transparent) !important; }
.search-wrapper :deep(.el-input__inner) { color: var(--text-primary) !important; font-size: 14px; }
.tab-section { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
.tab-item { padding: 8px 18px; border-radius: 10px; border: 1px solid rgba(255,255,255,.06); background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent); color: var(--text-secondary); font-size: 14px; cursor: pointer; transition: all .3s cubic-bezier(.4,0,.2,1); font-family: inherit; }
.tab-item:hover { background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent); transform: translateY(-2px); border-color: var(--line-soft); }
.tab-item.active { background: color-mix(in srgb, var(--brand) 10%, transparent); border-color: color-mix(in srgb, var(--brand) 20%, transparent); color: var(--brand); }
.faq-list { display: flex; flex-direction: column; gap: 6px; margin-bottom: 16px; }
.faq-item { padding: 12px 16px; border-radius: 12px; border: 1px solid rgba(255,255,255,.04); background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent); cursor: pointer; transition: all .3s ease; }
.faq-item:hover { background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent); border-color: var(--line-soft); transform: translateX(4px); }
.faq-question { display: flex; align-items: center; gap: 10px; }
.faq-icon { font-size: 12px; color: var(--text-muted); flex-shrink: 0; }
.faq-title { font-size: 15px; font-weight: 500; color: var(--text-primary); flex: 1; }
.faq-tag { font-size: 11px; padding: 2px 10px; border-radius: 12px; flex-shrink: 0; }
.faq-answer { margin-top: 10px; padding: 12px 16px; border-radius: 10px; background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent); border-left: 3px solid color-mix(in srgb, var(--brand) 30%, transparent); animation: slideDown .3s ease; }
@keyframes slideDown { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
.faq-step { font-size: 14px; color: var(--text-secondary); line-height: 1.8; padding: 2px 0; white-space: pre-wrap; }
.faq-actions { display: flex; gap: 10px; margin-top: 12px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,.06); flex-wrap: wrap; }
.faq-action-btn { padding: 4px 14px; border-radius: 8px; border: 1px solid var(--line-soft); background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent); color: var(--text-secondary); font-size: 13px; cursor: pointer; transition: all .3s ease; font-family: inherit; }
.faq-action-btn:hover { background: color-mix(in srgb, var(--brand) 10%, transparent); border-color: color-mix(in srgb, var(--brand) 20%, transparent); color: var(--brand); transform: translateY(-2px); }
.empty-state { text-align: center; padding: 40px 20px; color: var(--text-muted); }
.empty-state p { margin: 6px 0; }
.qa-divider { display: flex; align-items: center; justify-content: space-between; font-size: 15px; color: var(--text-secondary); padding: 8px 0 12px; }
.qa-divider .el-button { color: var(--text-muted) !important; font-size: 13px; }
.qa-divider .el-button:hover { color: var(--text-primary) !important; }
.ask-section { margin-top: 4px; }
.ask-wrapper { display: flex; gap: 10px; align-items: center; }
.ask-wrapper :deep(.el-input__wrapper) { background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent) !important; border: 1px solid var(--line-soft) !important; border-radius: 12px !important; }
.ask-wrapper :deep(.el-input__wrapper:hover) { border-color: var(--line) !important; }
.ask-wrapper :deep(.el-input__wrapper.is-focus) { border-color: color-mix(in srgb, var(--brand) 40%, transparent) !important; box-shadow: 0 0 0 4px color-mix(in srgb, var(--brand) 8%, transparent) !important; }
.ask-wrapper :deep(.el-input__inner) { color: var(--text-primary) !important; }
.upload-btn { flex-shrink: 0; }
.upload-trigger { width: 40px; height: 40px; padding: 0 !important; border-radius: 12px !important; border: 1px solid var(--line-soft) !important; background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent) !important; color: var(--text-secondary) !important; display: flex !important; align-items: center !important; justify-content: center !important; font-size: 16px; transition: all .3s ease !important; }
.upload-trigger:hover { background: color-mix(in srgb, var(--surface, #ffffff) 10%, transparent) !important; transform: translateY(-2px); border-color: var(--line) !important; }
.ask-wrapper .el-button--primary { border-radius: 12px !important; padding: 12px 24px !important; background: color-mix(in srgb, var(--brand) 10%, transparent) !important; border: 1px solid color-mix(in srgb, var(--brand) 15%, transparent) !important; color: var(--brand) !important; }
.ask-wrapper .el-button--primary:hover { background: color-mix(in srgb, var(--brand) 20%, transparent) !important; transform: translateY(-2px); }
.upload-preview { display: flex; align-items: center; gap: 10px; margin-top: 10px; padding: 8px 12px; border-radius: 10px; background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); }
.upload-preview img { width: 60px; height: 60px; object-fit: cover; border-radius: 8px; }
.upload-preview .el-button { margin-left: auto; color: var(--text-muted); }
.upload-preview .el-button:hover { color: #f56c6c; }
.ask-hint { margin-top: 6px; font-size: 12px; color: var(--text-muted); opacity: .6; }
.ask-history { margin-top: 14px; padding: 12px 16px; border-radius: 12px; background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent); border: 1px solid rgba(255,255,255,.04); }
.history-title { font-size: 14px; font-weight: 500; color: var(--text-secondary); margin-bottom: 10px; }
.history-item { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,.03); }
.history-item:last-child { border-bottom: none; }
.history-question { font-size: 14px; color: var(--text-primary); }
.history-meta { display: flex; gap: 12px; align-items: center; flex-shrink: 0; margin-left: 12px; }
.history-status { font-size: 12px; }
.history-status.resolved { color: color-mix(in srgb, #67c23a 65%, var(--text-primary)); }
.history-status.pending { color: color-mix(in srgb, #e6a23c 70%, var(--text-primary)); }
.history-time { font-size: 12px; color: var(--text-muted); }
.history-empty { text-align: center; color: var(--text-muted); font-size: 13px; padding: 12px 0; }
@media (max-width: 640px) {
  .qa-page { padding: 12px 10px; }
  .qa-container { padding: 16px 14px; max-height: 95vh; }
  .qa-header h1 { font-size: 20px; }
  .tab-section { gap: 4px; }
  .tab-item { font-size: 12px; padding: 6px 12px; }
  .faq-item { padding: 10px 12px; }
  .faq-title { font-size: 13px; }
  .ask-wrapper { flex-wrap: wrap; }
  .faq-actions { flex-wrap: wrap; }
}
</style>
