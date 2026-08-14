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
        <div class="ask-hint">问题将发送到管理员邮箱，我们会尽快回复你（支持图片上传）</div>
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
  { key: 'career', icon: '', label: '学程' },
  { key: 'community', icon: '', label: '社区' },
  { key: 'account', icon: '', label: '账号管理' },
  { key: 'api', icon: '', label: 'API配置' },
]
const activeTab = ref('all')

const faqs = ref([
  // ==================== 入门指南 ====================
  { id: 1, tag: '入门指南', tagColor: '#4CAF50', question: '如何开始学习？', answer: [
    '1. 注册登录后，进入「主界面」开始与 AI 对话',
    '2. 前往「学科计划」选择一个考纲，完成诊断摸底生成专属备考计划',
    '3. 按每日任务练习，系统会记录答题数据并更新知识点掌握度',
    '4. 在「资源库」可以自由生成题目、管理题集、复习错题',
    '5. 在「学程」中查看段位成长和任务进度',
  ], expanded: false, actions: [
    { icon: '', label: '去学科计划', route: '/subject-plan' },
    { icon: '', label: '去资源库', route: '/resource-lib' },
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
    '前往「评估中心 → 维度宇宙」查看完整雷达图和 AI 深度画像',
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
    '个人中心 → 查看维度宇宙学情画像各维度掌握度',
    '学科计划 → 考纲详情页 → 知识点 Tab 查看每个知识点的掌握度卡片（红→绿渐变）',
    '学程 → 查看段位等级和任务完成进度',
  ], expanded: false, actions: [
    { icon: '', label: '去学科计划', route: '/subject-plan' },
    { icon: '', label: '去学程', route: '/career' },
  ]},

  // ==================== 学科计划 ====================
  { id: 10, tag: '学科计划', tagColor: '#06b6d4', question: '学科计划是什么？怎么开始？', answer: [
    '学科计划是本平台的核心备考系统，覆盖 15 个大学生高频考试（CET-4/6、考研、雅思、托福、教资、CPA 等）。',
    '',
    '使用流程：',
    '1. 进入「学科计划」→ 浏览考纲列表，点击感兴趣的考纲卡片',
    '2. 在考纲详情页浏览题库，或点击「摸底诊断」开始评估',
    '3. 完成诊断题目后，设定目标分数、备考周期、每日学习时长',
    '4. AI 根据你的诊断结果生成专属备考计划',
    '5. 按「每日任务」Tab 逐天完成学习，查看「知识点」掌握度变化',
  ], expanded: false, actions: [
    { icon: '', label: '去学科计划', route: '/subject-plan' },
  ]},
  { id: 11, tag: '学科计划', tagColor: '#06b6d4', question: '考纲是什么？题库怎么用？', answer: [
    '15 个考纲覆盖四六级、考研、雅思托福、计算机二级、教资、CPA 等，每个考纲自带完整的题库（总计 1252 题）。',
    '',
    '题库功能：',
    '维度筛选 — 按词汇/语法/阅读等维度过滤题目',
    '子分类 + 题型筛选 — 精确定位你想练的题目类型',
    '收藏 — 点击心形按钮收藏，支持收藏筛选',
    '展开看答案 — 点击题目展开查看正确答案和解析',
    '已完成标记 — 做过的题目左侧显示绿色 ✓',
    '练习按钮 — 每道题右侧的 ▶ 按钮，点击直接跳转做题页',
  ], expanded: false, actions: [
    { icon: '', label: '去学科计划', route: '/subject-plan' },
  ]},
  { id: 12, tag: '学科计划', tagColor: '#06b6d4', question: '诊断摸底怎么操作？', answer: [
    '诊断摸底是生成专属备考计划的前置步骤：',
    '',
    'Step 1 — 答题：系统根据考纲维度配置，从题库随机抽取题目。支持 11 种题型（选择/多选/填空/完形/翻译/作文/编程/计算等），底部进度条显示完成情况',
    'Step 2 — 设定目标：答完所有题目后，设置目标分数、备考周期（7-90天）、每日学习时长（15-180分钟）',
    'Step 3 — 生成计划：点击「生成专属计划」，AI 立即创建带日期解锁的每日任务',
  ], expanded: false, actions: [
    { icon: '', label: '去学科计划', route: '/subject-plan' },
  ]},
  { id: 13, tag: '学科计划', tagColor: '#06b6d4', question: '每日任务怎么完成？', answer: [
    '生成计划后，在考纲详情页的「每日任务」Tab 查看当天学习内容：',
    '',
    '每个任务卡片包含标题、题型、题目数量、预估时间',
    '点击「去练习」→ 跳转做题页，逐题提交答案（选择题/填空/翻译/编程等全部题型支持）',
    '做完一题点「下一题」，全部完成后显示完成状态',
    '第二天自动解锁新任务，任务题目不会与已做/已分配题目重复',
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
  { id: 21, tag: '资源库', tagColor: '#42A5F5', question: '错题本是如何自动收录的？', answer: [
    '错题本自动收录规则：',
    '',
    '掌握度 < 40% → 自动加入「学习中」错题本',
    '掌握度 40%-60% → 保持学习中，定期复习',
    '掌握度 ≥ 60% → 自动移至「已攻克」错题本',
    '',
    '查看位置：资源库 → 错题本 Tab',
    '支持手动标记错题状态，每道错题配「复习」按钮跳转做题',
  ], expanded: false, actions: [
    { icon: '', label: '去错题本', route: '/resource-lib' },
  ]},
  { id: 22, tag: '资源库', tagColor: '#42A5F5', question: '如何创建和加入题集？', answer: [
    '创建题集：资源库 → 我的题集 Tab → 新建题集 → 输入名称和描述',
    '加入题集：做题页面点击「加入题集」→ 选择目标题集',
    '题集功能：',
    '  支持加权平均掌握度自动计算（进度条颜色从红到绿）',
    '  支持整卷练习和逐题练习',
    '  题集可分享给好友（社区功能）',
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
    { icon: '', label: '去主界面', route: '/home' },
  ]},
  { id: 25, tag: '资源库', tagColor: '#42A5F5', question: '如何查看生成历史？', answer: [
    '1. 进入「资源库」→「生成历史」Tab',
    '2. 默认按时间倒序显示所有生成记录',
    '3. 使用题型筛选下拉框按题型过滤',
    '4. 支持搜索和分页浏览',
  ], expanded: false, actions: [
    { icon: '', label: '去资源库', route: '/resource-lib' },
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
  { id: 42, tag: '社区', tagColor: '#9C27B0', question: '如何分享和接收题集？', answer: [
    '1. 在「资源库」题集管理中选择要分享的题集',
    '2. 点击「分享」发送给好友',
    '3. 好友在消息中心收到通知，点击接收即可',
    '4. 接收后自动保存到自己的题集列表',
  ], expanded: false, actions: [
    { icon: '', label: '去题集管理', route: '/resource-lib' },
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
  { id: 50, tag: '账号管理', tagColor: '#FF9800', question: '如何修改昵称和头像？', answer: [
    '1. 点击侧边栏「个人中心」进入个人资料页',
    '2. 头像：点击头像区域 → 上传新图片',
    '3. 昵称：点击昵称旁编辑按钮 → 输入新昵称 → 保存',
  ], expanded: false, actions: [
    { icon: '', label: '去个人中心', route: '/profile' },
  ]},
  { id: 51, tag: '账号管理', tagColor: '#FF9800', question: '如何修改密码？', answer: [
    '1. 进入「个人中心」→ 安全设置',
    '2. 输入当前密码验证 → 设置新密码（至少8位）→ 确认',
    '3. 修改成功后自动退出，需重新登录',
  ], expanded: false, actions: [
    { icon: '', label: '去个人中心', route: '/profile' },
  ]},
  { id: 52, tag: '账号管理', tagColor: '#FF9800', question: '如何修改邮箱和简介？', answer: [
    '邮箱：个人中心 → 账号设置 → 修改邮箱 → 输入新邮箱 → 验证码确认',
    '简介：个人中心 → 简介区域 → 编辑 → 保存',
  ], expanded: false, actions: [
    { icon: '', label: '去个人中心', route: '/profile' },
  ]},
  { id: 53, tag: '账号管理', tagColor: '#FF9800', question: '如何退出登录？', answer: [
    '点击侧边栏底部「退出登录」→ 弹窗确认 → 清除登录态跳转登录页',
  ], expanded: false },

  // ==================== API 配置 ====================
  { id: 60, tag: 'API配置', tagColor: '#FF5722', question: 'API 管理是做什么的？', answer: [
    'API 管理让你为每个 AI 功能选择不同模型平台并填入自己的 API 凭证：',
    '',
    'AI 对话（小基）— 火山引擎(豆包) / DeepSeek / 智谱 GLM',
    '图片理解 — 火山引擎(豆包)',
    '题目生成 — DeepSeek / 智谱 GLM',
    '学习评估 — DeepSeek',
    '视频推荐 — 腾讯云',
    '视频通话 — 讯飞',
    '',
    '配置后优先使用你自己的额度，无调用限制。',
  ], expanded: false, actions: [
    { icon: '', label: '去配置 API', route: '/api-center' },
  ]},
  { id: 61, tag: 'API配置', tagColor: '#FF5722', question: '如何获取各平台 API Key？', answer: [
    'DeepSeek：platform.deepseek.com → API Keys → 创建 Key（格式 sk-xxx）',
    '火山引擎(豆包)：console.volcengine.com → 开通 ARK → 创建接入点 → 获取 Key + Endpoint ID',
    '智谱 GLM：open.bigmodel.cn → API Keys → 创建 Key',
    '腾讯云：console.cloud.tencent.com → 访问管理 → API密钥管理 → SecretId + SecretKey',
    '讯飞：console.xfyun.cn → 创建应用 → APPID + API Key + API Secret',
    '',
    '所有平台的 Key 只显示一次，请立即保存！',
  ], expanded: false, actions: [
    { icon: '', label: '去配置 API', route: '/api-center' },
  ]},
  { id: 62, tag: 'API配置', tagColor: '#FF5722', question: 'API Key 如何验证是否有效？', answer: [
    '在 API 管理页面填入凭证后点击「验证」按钮，系统发送测试请求：',
    '  验证通过 → 凭证有效，功能可正常使用',
    '  验证失败 → 检查凭证是否完整、有无多余空格、账户是否有余额',
  ], expanded: false, actions: [
    { icon: '', label: '去验证 API', route: '/api-center' },
  ]},
  { id: 63, tag: 'API配置', tagColor: '#FF5722', question: '未配置 API 或凭证失效会怎样？', answer: [
    '系统有完整降级方案：',
    '',
    '未配置 → 自动使用系统公共 API（有限额）',
    '已配置但失效 → 自动降级到系统公共 API，页面提示切换',
    '公共 API 也超限 → 显示「服务繁忙，请配置自己的 Key」',
    '',
    '建议尽早配置专属凭证，避免公共额度耗尽。',
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

function goBack() { router.push('/home') }
function switchTab(tab) { activeTab.value = tab }
function toggleFAQ(id) { const item = faqs.value.find(f => f.id === id); if (item) item.expanded = !item.expanded }
function filterFAQs() {}

const filteredFAQs = computed(() => {
  let result = faqs.value

  const tagMap = {
    guide: '入门指南',
    subject: '学科计划',
    resource: '资源库',
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
.qa-container { max-width: 820px; width: 100%; padding: 28px 36px; border-radius: 18px; background: rgba(255,255,255,.04); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,.08); box-shadow: 0 8px 32px rgba(0,0,0,.06); height: fit-content; max-height: 90vh; overflow-y: auto; }
.qa-container::-webkit-scrollbar { width: 4px; }
.qa-container::-webkit-scrollbar-thumb { background: rgba(128,128,128,.2); border-radius: 2px; }
.qa-header { display: flex; align-items: center; justify-content: space-between; }
.qa-header h1 { font-size: 26px; color: var(--text-primary); margin: 0; }
.back-btn { color: var(--text-secondary) !important; transition: all .3s ease !important; font-size: 15px; padding: 8px 12px; border-radius: 10px; }
.back-btn:hover { color: var(--text-primary) !important; transform: translateX(-4px); background: rgba(255,255,255,.08); }
.el-divider { margin: 14px 0; }
.search-section { margin: 4px 0 14px; }
.search-wrapper { position: relative; }
.search-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); color: var(--text-muted); font-size: 14px; z-index: 1; }
.search-wrapper :deep(.el-input__wrapper) { padding-left: 38px; background: rgba(255,255,255,.04) !important; border: 1px solid rgba(255,255,255,.08) !important; border-radius: 12px !important; }
.search-wrapper :deep(.el-input__wrapper:hover) { border-color: rgba(255,255,255,.15) !important; }
.search-wrapper :deep(.el-input__wrapper.is-focus) { border-color: rgba(64,158,255,.4) !important; box-shadow: 0 0 0 4px rgba(64,158,255,.08) !important; }
.search-wrapper :deep(.el-input__inner) { color: var(--text-primary) !important; font-size: 14px; }
.tab-section { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
.tab-item { padding: 8px 18px; border-radius: 10px; border: 1px solid rgba(255,255,255,.06); background: rgba(255,255,255,.02); color: var(--text-secondary); font-size: 14px; cursor: pointer; transition: all .3s cubic-bezier(.4,0,.2,1); font-family: inherit; }
.tab-item:hover { background: rgba(255,255,255,.06); transform: translateY(-2px); border-color: rgba(255,255,255,.12); }
.tab-item.active { background: rgba(64,158,255,.10); border-color: rgba(64,158,255,.2); color: #409eff; }
.faq-list { display: flex; flex-direction: column; gap: 6px; margin-bottom: 16px; }
.faq-item { padding: 12px 16px; border-radius: 12px; border: 1px solid rgba(255,255,255,.04); background: rgba(255,255,255,.02); cursor: pointer; transition: all .3s ease; }
.faq-item:hover { background: rgba(255,255,255,.05); border-color: rgba(255,255,255,.08); transform: translateX(4px); }
.faq-question { display: flex; align-items: center; gap: 10px; }
.faq-icon { font-size: 12px; color: var(--text-muted); flex-shrink: 0; }
.faq-title { font-size: 15px; font-weight: 500; color: var(--text-primary); flex: 1; }
.faq-tag { font-size: 11px; padding: 2px 10px; border-radius: 12px; flex-shrink: 0; }
.faq-answer { margin-top: 10px; padding: 12px 16px; border-radius: 10px; background: rgba(255,255,255,.03); border-left: 3px solid rgba(64,158,255,.3); animation: slideDown .3s ease; }
@keyframes slideDown { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
.faq-step { font-size: 14px; color: var(--text-secondary); line-height: 1.8; padding: 2px 0; white-space: pre-wrap; }
.faq-actions { display: flex; gap: 10px; margin-top: 12px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,.06); flex-wrap: wrap; }
.faq-action-btn { padding: 4px 14px; border-radius: 8px; border: 1px solid rgba(255,255,255,.08); background: rgba(255,255,255,.03); color: var(--text-secondary); font-size: 13px; cursor: pointer; transition: all .3s ease; font-family: inherit; }
.faq-action-btn:hover { background: rgba(64,158,255,.10); border-color: rgba(64,158,255,.2); color: #409eff; transform: translateY(-2px); }
.empty-state { text-align: center; padding: 40px 20px; color: var(--text-muted); }
.empty-state p { margin: 6px 0; }
.qa-divider { display: flex; align-items: center; justify-content: space-between; font-size: 15px; color: var(--text-secondary); padding: 8px 0 12px; }
.qa-divider .el-button { color: var(--text-muted) !important; font-size: 13px; }
.qa-divider .el-button:hover { color: var(--text-primary) !important; }
.ask-section { margin-top: 4px; }
.ask-wrapper { display: flex; gap: 10px; align-items: center; }
.ask-wrapper :deep(.el-input__wrapper) { background: rgba(255,255,255,.04) !important; border: 1px solid rgba(255,255,255,.08) !important; border-radius: 12px !important; }
.ask-wrapper :deep(.el-input__wrapper:hover) { border-color: rgba(255,255,255,.15) !important; }
.ask-wrapper :deep(.el-input__wrapper.is-focus) { border-color: rgba(64,158,255,.4) !important; box-shadow: 0 0 0 4px rgba(64,158,255,.08) !important; }
.ask-wrapper :deep(.el-input__inner) { color: var(--text-primary) !important; }
.upload-btn { flex-shrink: 0; }
.upload-trigger { width: 40px; height: 40px; padding: 0 !important; border-radius: 12px !important; border: 1px solid rgba(255,255,255,.08) !important; background: rgba(255,255,255,.04) !important; color: var(--text-secondary) !important; display: flex !important; align-items: center !important; justify-content: center !important; font-size: 16px; transition: all .3s ease !important; }
.upload-trigger:hover { background: rgba(255,255,255,.1) !important; transform: translateY(-2px); border-color: rgba(255,255,255,.15) !important; }
.ask-wrapper .el-button--primary { border-radius: 12px !important; padding: 12px 24px !important; background: rgba(64,158,255,.1) !important; border: 1px solid rgba(64,158,255,.15) !important; color: #409eff !important; }
.ask-wrapper .el-button--primary:hover { background: rgba(64,158,255,.2) !important; transform: translateY(-2px); }
.upload-preview { display: flex; align-items: center; gap: 10px; margin-top: 10px; padding: 8px 12px; border-radius: 10px; background: rgba(255,255,255,.04); }
.upload-preview img { width: 60px; height: 60px; object-fit: cover; border-radius: 8px; }
.upload-preview .el-button { margin-left: auto; color: var(--text-muted); }
.upload-preview .el-button:hover { color: #f56c6c; }
.ask-hint { margin-top: 6px; font-size: 12px; color: var(--text-muted); opacity: .6; }
.ask-history { margin-top: 14px; padding: 12px 16px; border-radius: 12px; background: rgba(255,255,255,.02); border: 1px solid rgba(255,255,255,.04); }
.history-title { font-size: 14px; font-weight: 500; color: var(--text-secondary); margin-bottom: 10px; }
.history-item { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,.03); }
.history-item:last-child { border-bottom: none; }
.history-question { font-size: 14px; color: var(--text-primary); }
.history-meta { display: flex; gap: 12px; align-items: center; flex-shrink: 0; margin-left: 12px; }
.history-status { font-size: 12px; }
.history-status.resolved { color: #67c23a; }
.history-status.pending { color: #e6a23c; }
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
