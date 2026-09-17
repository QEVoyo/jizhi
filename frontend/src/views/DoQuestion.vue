<template>
  <div class="question-page">
    <div class="question-container">
      <!-- 返回 -->
      <div class="question-topbar">
        <el-button text @click="goBack" class="back-btn">
          <i class="fas fa-arrow-left"></i> 返回
        </el-button>
        <h2>📝 练习</h2>
      </div>

      <LoadingSpinner v-if="loading" variant="typewriter" :flow-steps="['正在分析题目考点...', '正在匹配难度等级...', '正在组织题目结构...']" />

      <div v-else>
        <!-- 题目信息 -->
        <div class="question-meta">
          <div class="difficulty-ring">
            <svg viewBox="0 0 60 60" class="ring-svg">
              <circle cx="30" cy="30" r="25" fill="none" stroke="rgba(128,128,128,0.12)" stroke-width="5"/>
              <circle
                cx="30"
                cy="30"
                r="25"
                fill="none"
                :stroke="diffColor"
                stroke-width="5"
                stroke-linecap="round"
                :stroke-dasharray="157.08"
                :stroke-dashoffset="157.08 * (1 - difficultyScore / 10)"
                transform="rotate(-90 30 30)"
              />
            </svg>
            <div class="ring-label">
              <span class="ring-score">{{ difficultyScore.toFixed(1) }}</span>
              <span class="ring-text">难度</span>
            </div>
          </div>

          <div class="meta-right">
            <div class="meta-item">
              <span class="meta-label">分类</span>
              <span class="meta-value">{{ question.category || '未分类' }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">知识点</span>
              <span class="meta-value">{{ question.topic || '未知' }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">题型</span>
              <span class="meta-value">{{ getTypeDisplay(question.question_type) }}</span>
            </div>
          </div>
        </div>

        <el-divider />

        <div class="question-content">
          <h3>{{ question.title || question.question_content || '题目' }}</h3>
        </div>

        <div class="answer-area">
          <!-- 提交评估中：友好加载态（2026-08-30：AI 批改需数秒，不让用户空等） -->
          <LoadingSpinner
            v-if="submitting"
            variant="orbit"
            :flow-steps="['正在阅读你的答案…', 'AI 正在逐项批改…', '正在分析知识点掌握度…', '正在寻找相关讲解视频…']"
          />
          <template v-else>
          <el-radio-group v-if="question.question_type === 'choice'" v-model="userAnswer" class="choice-group">
            <el-radio
              v-for="(opt, key) in question.options"
              :key="key"
              :label="key"
              class="choice-item"
            >
              {{ key }}. {{ opt }}
            </el-radio>
          </el-radio-group>

          <el-radio-group v-else-if="question.question_type === 'judge'" v-model="userAnswer" class="judge-group">
            <el-radio label="正确" class="judge-item">正确</el-radio>
            <el-radio label="错误" class="judge-item">错误</el-radio>
          </el-radio-group>

          <el-input
            v-else-if="question.question_type === 'fill'"
            v-model="userAnswer"
            placeholder="请输入答案..."
            size="large"
          />

          <el-input
            v-else-if="question.question_type === 'essay'"
            v-model="userAnswer"
            type="textarea"
            :rows="5"
            placeholder="请输入你的回答..."
          />

          <div
            v-else-if="question.question_type === 'coding' || question.question_type === 'programming'"
            class="code-editor"
          >
            <div class="ce-bar">
              <span class="ce-lang"><i class="fas fa-code"></i> Python 3</span>
              <button class="ce-run" :disabled="codeRunning || !userAnswer" @click="runUserCode">
                <i class="fas" :class="codeRunning ? 'fa-spinner fa-spin' : 'fa-play'"></i>
                {{ codeRunning ? '运行中…' : '运行' }}
              </button>
            </div>

            <el-input
              v-model="userAnswer"
              type="textarea"
              :rows="10"
              class="ce-input"
              :placeholder="question.starter_code || '# 请在这里编写代码'"
            />

            <div class="ce-stdin">
              <span class="ce-lbl">运行输入（stdin）</span>
              <el-input v-model="codeStdin" size="small" placeholder="程序需要读入时填这里，可留空" />
            </div>

            <div v-if="codeRunResult" class="ce-out">
              <div class="ce-out-head">
                运行结果
                <span class="ce-exit">exit {{ codeRunResult.exit_code }}</span>
              </div>
              <pre class="ce-out-body">{{ codeRunResult.output || '（无输出）' }}</pre>
            </div>

            <div v-if="sampleCases.length" class="ce-samples">
              <div class="ce-samples-title">样例（共 {{ sampleCases.length }} 组）</div>
              <div v-for="(tc, i) in sampleCases" :key="i" class="ce-sample">
                <div class="ce-sample-col">
                  <span class="ce-lbl">输入</span>
                  <pre>{{ tc.input || '(无)' }}</pre>
                </div>
                <div class="ce-sample-col">
                  <span class="ce-lbl">输出</span>
                  <pre>{{ tc.output || tc.expected_output || '' }}</pre>
                </div>
              </div>
            </div>

            <div v-if="codeTestResults && codeTestResults.length" class="ce-results">
              <div class="ce-samples-title">判分结果</div>
              <div
                v-for="t in codeTestResults"
                :key="t.index"
                class="ce-res"
                :class="'ce-res-' + String(t.status).toLowerCase()"
              >
                <span class="ce-res-badge">{{ t.status }}</span>
                <span class="ce-res-desc">{{ t.description }}</span>
                <span v-if="!t.passed" class="ce-res-note">
                  期望 {{ t.expected || '(空)' }} · 实得 {{ (t.stdout || '').trim() || '(空)' }}
                </span>
              </div>
            </div>
          </div>

          <el-input
            v-else-if="question.question_type === 'calculation'"
            v-model="userAnswer"
            type="textarea"
            :rows="4"
            placeholder="请写出计算过程和答案..."
          />

          <el-input v-else v-model="userAnswer" placeholder="请输入答案..." size="large" />

        <el-divider />

        <div v-if="evaluated && evaluationResult" class="evaluation">
          <div v-if="evaluationResult.is_correct" class="correct">
            <i class="fas fa-check-circle"></i> 回答正确！
          </div>
          <div v-else class="incorrect">
            <i class="fas fa-times-circle"></i> 回答错误
          </div>

          <div class="correct-answer">
            <span class="label">✅ 正确答案：</span>
            <span class="answer">{{ evaluationResult.correct_answer || '无' }}</span>
          </div>

          <div class="user-answer-display">
            <span class="label">📝 你的答案：</span>
            <span class="answer">{{ userAnswer || '未作答' }}</span>
          </div>

          <div class="mastery-section">
            <span class="mastery-label">掌握程度</span>
            <div class="mastery-bar">
              <div
                class="mastery-fill"
                :style="{
                  width: (evaluationResult.mastery_score || 50) + '%',
                  background: getColor(evaluationResult.mastery_score || 50)
                }"
              />
            </div>
            <span class="mastery-score">{{ evaluationResult.mastery_score || 50 }}%</span>
          </div>

          <div v-if="evaluationResult.detailed_analysis" class="detail-analysis">
            <div class="analysis-title">📖 详细解析</div>
            <div class="analysis-content">{{ evaluationResult.detailed_analysis }}</div>
          </div>

          <div class="eval-text">
            <strong>📝 评估：</strong>{{ evaluationResult.evaluation }}
          </div>
          <div class="eval-text">
            <strong>💡 建议：</strong>{{ evaluationResult.suggestion }}
          </div>

          <!-- 自营视频库（2026-09-04）：知识点讲解 · 强相关排行 + 用户自选 -->
          <div v-if="libVideos.length || libGenerating" class="video-section lib-section">
            <div class="video-header">
              <span class="video-title">
                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 4L2 9l10 5 10-5-10-5z"/>
                  <path d="M6 11.5V16c0 1.5 2.7 3 6 3s6-1.5 6-3v-4.5"/>
                  <path d="M22 9v5"/>
                </svg>
                「{{ libKpName }}」知识点讲解
              </span>
              <span class="lib-badge">基智自营视频库</span>
            </div>
            <div class="lib-grid">
              <div
                v-for="v in libVideos"
                :key="v.id"
                class="lib-card"
                @click="openLibVideo(v)"
              >
                <div class="lib-poster">
                  <VideoPoster :video="v" />
                  <div v-if="!v.script" class="lib-name-fallback">{{ v.title || v.knowledge_name }}</div>
                  <span class="lib-poster-play">
                    <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
                  </span>
                  <span class="lib-poster-mark">{{ ANGLE_LABELS[v.angle] || '讲解' }}</span>
                  <span class="lib-score" :class="{ exact: v.match_score >= 100 }">{{ scoreLabel(v.match_score) }}</span>
                </div>
                <div class="lib-info">
                  <div class="lib-name">{{ v.title || v.knowledge_name }}</div>
                  <div class="lib-meta">
                    <span class="lib-author">
                      <img v-if="v.author_avatar" :src="v.author_avatar" alt="" />
                      {{ v.author_name || '基智' }}
                    </span>
                    <span class="lib-dur">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <circle cx="12" cy="12" r="9"/>
                      <path d="M12 7v5l3 3"/>
                    </svg>
                    {{ Math.round(v.audio_duration || 90) }}s
                  </span>
                  </div>
                </div>
              </div>
              <div v-if="libGenerating" class="lib-card generating">
                <div class="lib-poster generating">
                  <svg class="lib-pen" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 20h9"/>
                    <path d="M16.5 3.5a2.12 2.12 0 013 3L7 19l-4 1 1-4 12.5-12.5z"/>
                  </svg>
                </div>
                <div class="lib-info">
                  <div class="lib-name">讲解师正在写讲稿…</div>
                  <div class="lib-meta">十几秒后刷新一下试试</div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="videos.length > 0" class="video-section">
            <div class="video-header">
              <span class="video-title">
                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="2" y="7" width="20" height="14" rx="2"/>
                  <path d="M17 2l-5 5h6l-5 5"/>
                </svg>
                更多参考视频
              </span>
              <a
                :href="`https://search.bilibili.com/all?keyword=${encodeURIComponent(searchKeyword)}`"
                target="_blank"
                class="more-link"
              >
                查看更多 →
              </a>
            </div>
            <div class="video-grid">
              <div
                v-for="video in videos"
                :key="video.bvid"
                class="video-card"
                @click="openVideo(video)"
              >
                <img
                  :src="video.pic"
                  :alt="video.title"
                  loading="lazy"
                  referrerpolicy="no-referrer"
                  @error="handleImageError(video)"
                />
                <div class="video-info">
                  <div class="video-title-text">{{ video.title }}</div>
                  <div class="video-meta">
                    <span>{{ video.author }}</span>
                    <span>👁 {{ formatNumber(video.play) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else-if="videoSearched && !videoLoading && !videos.length" class="video-empty">
            暂无更多参考视频
          </div>

          <el-button type="primary" @click="resetEvaluation">继续练习 →</el-button>
        </div>

        <div v-else class="action-buttons">
          <el-button type="primary" :loading="submitting" @click="handleSubmit">
            <i class="fas fa-paper-plane"></i> 提交
          </el-button>
          <el-button :loading="regenerating" @click="handleRegenerate">
            <i class="fas fa-sync"></i> 重新生成
          </el-button>
          <el-button @click="handleAddToSet">
            <i class="fas fa-folder-plus"></i> 加入题集
          </el-button>
          <el-button @click="showChangeType = true">
            <i class="fas fa-arrows-rotate"></i> 换题型
          </el-button>
          <el-button @click="showHint">
            <i class="fas fa-lightbulb"></i> 提示
          </el-button>
        </div>
          </template>
        </div>
      </div>
    </div>

    <!-- ===== 换题型弹窗 ===== -->
    <el-dialog v-model="showChangeType" title="🔄 换题型" width="420px" destroy-on-close>
      <div class="change-type-dialog">
        <p class="dialog-tip">选择换题方式</p>
        <el-radio-group v-model="changeMode" class="change-mode-group">
          <el-radio label="random">🎲 从选中的题型中随机</el-radio>
          <el-radio label="specify">📋 指定一个题型</el-radio>
        </el-radio-group>

        <div v-if="changeMode === 'random'" class="random-types">
          <p class="sub-tip">勾选要参与随机的题型（至少选一个）</p>
          <div class="type-checkboxes">
            <el-checkbox
              v-for="t in availableTypes"
              :key="t"
              v-model="selectedTypes"
              :label="t"
            />
          </div>
          <p v-if="!selectedTypes.length" class="warning-tip">⚠️ 请至少选择一个题型</p>
        </div>

        <div v-else class="specify-type">
          <el-select v-model="targetType" placeholder="选择题型" style="width:100%">
            <el-option
              v-for="t in availableTypes"
              :key="t"
              :label="t"
              :value="t"
            />
          </el-select>
        </div>
      </div>
      <template #footer>
        <el-button @click="showChangeType = false">取消</el-button>
        <el-button type="primary" :loading="changingType" @click="handleChangeType">
          确认换题
        </el-button>
      </template>
    </el-dialog>

    <!-- ===== 加入题集弹窗 ===== -->
    <el-dialog v-model="showAddToSet" title="📁 加入题集" width="440px" destroy-on-close>
      <div class="add-to-set-dialog">
        <p class="dialog-tip">将当前题目加入以下题集</p>
        <div v-if="!questionSets.length" class="empty-state">
          <p>📭 你还没有创建题集</p>
          <el-button type="primary" size="small" @click="goCreateSet">前往创建题集</el-button>
        </div>
        <div v-else>
          <div
            v-for="s in questionSets"
            :key="s.id"
            class="set-item"
            :class="{ already: s.question_ids?.includes(question.id) }"
          >
            <div class="set-info">
              <span class="set-name">{{ s.name }}</span>
              <span class="set-count">{{ s.question_ids?.length || 0 }} 道题</span>
            </div>
            <el-button
              v-if="s.question_ids?.includes(question.id)"
              size="small"
              disabled
            >
              ✅ 已加入
            </el-button>
            <el-button
              v-else
              size="small"
              type="primary"
              :loading="addingSetId === s.id"
              @click="handleAddToSetConfirm(s.id)"
            >
              加入
            </el-button>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showAddToSet = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- ===== 视频播放弹窗 ===== -->
    <el-dialog
      v-model="videoDialogVisible"
      :title="currentVideo?.title || '视频播放'"
      width="800px"
      class="video-dialog"
      destroy-on-close
      :close-on-click-modal="true"
    >
      <div v-if="currentVideo" class="video-player-container">
        <div class="video-wrapper" v-loading="iframeLoading" element-loading-text="正在加载视频…" element-loading-background="rgba(10, 14, 24, 0.88)">
          <iframe
            :src="`https://player.bilibili.com/player.html?bvid=${currentVideo.bvid}&page=1&autoplay=0&high_quality=1`"
            frameborder="0"
            allowfullscreen
            class="video-iframe"
            @load="iframeLoading = false"
          />
        </div>
        <div class="video-detail-info">
          <div class="video-detail-title">{{ currentVideo.title }}</div>
          <div class="video-detail-meta">
            <span>👤 {{ currentVideo.author }}</span>
            <span>👁 {{ formatNumber(currentVideo.play) }}</span>
            <span>❤️ {{ formatNumber(currentVideo.like) }}</span>
          </div>
          <a
            :href="currentVideo.url"
            target="_blank"
            class="goto-bilibili-btn"
          >
            去B站观看 ↗
          </a>
        </div>
      </div>
    </el-dialog>

    <!-- ===== 自营视频库播放弹窗 ===== -->
    <el-dialog
      v-model="libDialogVisible"
      :title="libCurrent?.title || libCurrent?.knowledge_name || '知识点讲解'"
      width="760px"
      class="video-dialog lib-dialog"
      :close-on-click-modal="true"
    >
      <VideoLessonPlayer ref="libPlayer" v-if="libCurrent" :video="libCurrent" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  evaluateAnswer,
  generateQuestion,
  getQuestionSets,
  addQuestionToSet
} from '@/api/questions'
import { searchBilibili } from '@/api/video'
import { ensureVideoLib, getVideoRelated, recordVideoPlay } from '@/api/video'
import { knowledgeKey, questionFingerprint, ANGLE_LABELS } from '@/utils/videoLib'
import VideoLessonPlayer from '@/components/VideoLessonPlayer.vue'
import VideoPoster from '@/components/VideoPoster.vue'
import { ElMessage } from 'element-plus'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const loading = ref(true)
const question = ref({})
const userAnswer = ref('')
const evaluated = ref(false)
const evaluationResult = ref(null)
const submitting = ref(false)

// ===== 编程题：沙箱运行 + 逐测试点判分（2026-09-11）=====
const codeRunning = ref(false)
const codeStdin = ref('')
const codeRunResult = ref(null)
const codeTestResults = ref(null)
const isProgramming = computed(() =>
  ['coding', 'programming'].includes(question.value?.question_type))
// 测试用例可能在顶层（生成题）或 content 内（题库题）
const sampleCases = computed(() => {
  const q = question.value || {}
  if (Array.isArray(q.test_cases) && q.test_cases.length) return q.test_cases
  const c = q.content
  if (c && Array.isArray(c.test_cases) && c.test_cases.length) return c.test_cases
  return []
})
const hasTestCases = computed(() => sampleCases.value.length > 0)

async function runUserCode() {
  if (codeRunning.value) return
  codeRunning.value = true
  codeRunResult.value = null
  try {
    const baseUrl = import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'
    const res = await fetch(`${baseUrl}/subject-plan/code/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: userAnswer.value || '', language: 'python', input: codeStdin.value || '' })
    })
    const d = await res.json()
    codeRunResult.value = { output: d.output, exit_code: d.exit_code }
  } catch (e) {
    codeRunResult.value = { output: '运行失败：' + (e?.message || '网络错误'), exit_code: -1 }
  } finally {
    codeRunning.value = false
  }
}

/** 编程题提交：有测试用例 → 沙箱逐点判分；没有 → 仍走 AI 批改 */
async function submitProgramming() {
  const baseUrl = import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'
  const res = await fetch(`${baseUrl}/subject-plan/code/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: authStore.user?.id || '',
      question_id: question.value.id,
      syllabus_id: question.value.syllabus_id || '',
      language: 'python',
      code: userAnswer.value,
      source: 'generated'
    })
  })
  const d = await res.json()
  if (!res.ok) throw new Error(d?.detail || '判分失败')
  codeTestResults.value = d.test_results || []
  evaluationResult.value = {
    is_correct: !!d.is_correct,
    correct_answer: question.value.answer || '',
    detailed_analysis: `沙箱判分：${d.passed_count}/${d.total_count} 个测试点通过，得分 ${d.score}`
  }
  evaluated.value = true
}
const regenerating = ref(false)
const changingType = ref(false)
const addingSetId = ref(null)

const showChangeType = ref(false)
const changeMode = ref('random')
const selectedTypes = ref([])
const targetType = ref('')
const availableTypes = ref([])

const showAddToSet = ref(false)
const questionSets = ref([])

const videos = ref([])
const videoLoading = ref(false)
const videoSearched = ref(false)
const searchKeyword = ref('')
const videoDialogVisible = ref(false)
const currentVideo = ref(null)
const iframeLoading = ref(false)

// ===== 自营视频库（2026-09-04）=====
const libVideos = ref([])
const libGenerating = ref(false)
const libTriggered = ref(false)
const libDialogVisible = ref(false)
const libCurrent = ref(null)
const libPlayer = ref(null)
let libPollTimer = null
let libPollTries = 0
// 弹窗不再销毁，组件常驻保秒开：关窗停音轨，二次打开从头自动开播
// 播放量（2026-09-05 用户定调：进入满 10 秒才 +1 次）
let libViewTimer = null
watch(libDialogVisible, (v) => {
  if (!v) {
    if (libViewTimer) { clearTimeout(libViewTimer); libViewTimer = null }
    if (libPlayer.value) libPlayer.value.stop()
  } else {
    if (libPlayer.value) libPlayer.value.start()
    const vid = libCurrent.value && libCurrent.value.id
    if (libViewTimer) clearTimeout(libViewTimer)
    libViewTimer = setTimeout(() => {
      if (libDialogVisible.value && vid) recordVideoPlay(vid)
    }, 10000)
  }
})

const libKpName = computed(() => question.value.normalized_topic || question.value.topic || '本题')

function scoreLabel(score) {
  if (score >= 100) return '精准匹配'
  if (score >= 70) return '同学科'
  return '热门讲解'
}

function openLibVideo(v) {
  // 播放量改为弹窗停留满 10 秒才计（watch libDialogVisible）
  libCurrent.value = v
  libDialogVisible.value = true
}

const difficultyScore = computed(() => {
  return question.value.difficulty_score || 5
})

const diffColor = computed(() => {
  const s = difficultyScore.value / 10
  if (s < 0.2) return '#00CC66'
  if (s < 0.4) return '#6BCB77'
  if (s < 0.6) return '#FFD93D'
  if (s < 0.8) return '#FFB74D'
  return '#FF6B6B'
})

const typeDisplayMap = {
  choice: '选择题',
  fill: '填空题',
  judge: '判断题',
  essay: '简答题/论述题',
  calculation: '计算题',
  coding: '编程题',
  programming: '编程题'
}

const allTypes = ['选择题', '填空题', '判断题', '简答题', '计算题', '编程题']

function getTypeDisplay(type) {
  return typeDisplayMap[type] || type || '未知'
}

function getColor(score) {
  if (score < 5) return '#FF0000'
  if (score < 10) return '#FF1A00'
  if (score < 15) return '#FF3300'
  if (score < 20) return '#FF4D00'
  if (score < 25) return '#FF6600'
  if (score < 30) return '#FF8000'
  if (score < 35) return '#FF9900'
  if (score < 40) return '#FFB300'
  if (score < 45) return '#FFCC00'
  if (score < 50) return '#FFE600'
  if (score < 55) return '#D4E000'
  if (score < 60) return '#A8D500'
  if (score < 65) return '#7DCC00'
  if (score < 70) return '#52C200'
  if (score < 75) return '#26B800'
  if (score < 80) return '#00AD00'
  if (score < 85) return '#00A300'
  if (score < 90) return '#009900'
  if (score < 95) return '#008000'
  return '#006600'
}

function formatNumber(num) {
  if (!num) return '0'
  if (num >= 10000) return (num / 10000).toFixed(1) + '万'
  return num.toString()
}

function handleImageError(video) {
  video.pic = ''
}

async function loadQuestionSets() {
  try {
    const token = authStore.token
    const userId = authStore.user.id
    const baseUrl = import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'

    const res = await fetch(`${baseUrl}/questions/set/list/${userId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })
    const data = await res.json()

    questionSets.value = (data || []).map(s => ({
      ...s,
      question_ids: Array.isArray(s.question_ids) ? s.question_ids : []
    }))
  } catch (e) {
    console.error('加载题集失败:', e)
    questionSets.value = []
  }
}

async function searchVideos(keyword) {
  if (!keyword) return
  videoLoading.value = true
  videoSearched.value = false
  try {
    const res = await searchBilibili(keyword, 1, 4)
    if (res.success) {
      videos.value = res.videos || []
    } else {
      videos.value = []
    }
  } catch (error) {
    console.error('搜索视频失败:', error)
    videos.value = []
  } finally {
    videoLoading.value = false
    videoSearched.value = true
  }
}

function openVideo(video) {
  // 换了视频才重新亮起加载遮罩；同一条复用不重复等待
  if (!currentVideo.value || currentVideo.value.bvid !== video.bvid) iframeLoading.value = true
  currentVideo.value = video
  videoDialogVisible.value = true
}

// ===== 自营视频库加载：ensure（触发懒生成）+ related（排行自选）+ 未就绪轮询 =====
async function fetchLibVideos(key, subject, fp) {
  try {
    const res = await getVideoRelated({ knowledge_key: key, subject, question_fingerprint: fp, limit: 6 })
    libVideos.value = res.items || []
    return libVideos.value.length
  } catch (e) {
    console.error('视频库检索失败:', e)
    return 0
  }
}

async function loadLibraryVideos() {
  const q = question.value || {}
  const subject = q.category || '通用'
  const kp = q.normalized_topic || q.topic || ''
  if (!kp) return
  const key = knowledgeKey(subject, kp)
  const fp = questionFingerprint(q.title || '')
  libPollTries = 0

  try {
    const ensured = await ensureVideoLib({ knowledge_key: key, knowledge_name: kp, subject })
    libTriggered.value = !!ensured.triggered
  } catch (e) {
    console.error('视频库 ensure 失败:', e)
  }

  const count = await fetchLibVideos(key, subject, fp)
  // 还没生成完 → 显示「写讲稿」卡 + 轮询（最多 5 次 × 8s）
  libGenerating.value = count === 0
  if (count === 0) scheduleLibPoll(key, subject, fp)
}

function scheduleLibPoll(key, subject, fp) {
  clearLibPoll()
  libPollTimer = setTimeout(async () => {
    if (libPollTries >= 5) { libGenerating.value = false; return }
    libPollTries++
    const count = await fetchLibVideos(key, subject, fp)
    if (count === 0 && libPollTries < 5) {
      scheduleLibPoll(key, subject, fp)
    } else {
      libGenerating.value = count === 0
    }
  }, 8000)
}

function clearLibPoll() {
  if (libPollTimer) { clearTimeout(libPollTimer); libPollTimer = null }
}

// ============================================================
// ✅ 核心加载逻辑：绝不重新生成旧题
// ============================================================
async function loadQuestion() {
   loading.value = true

  // ✅ 0. 最优先：从 URL 参数获取完整题目数据（来自好友分享）
  const dataParam = route.query.data
  if (dataParam) {
    try {
      const parsed = JSON.parse(decodeURIComponent(dataParam))
      question.value = parsed
      evaluated.value = false
      evaluationResult.value = null
      userAnswer.value = ''
      initUI(question.value)
      loading.value = false
      return
    } catch (error) {
      console.error('解析题目数据失败:', error)
      // 解析失败就继续走下面的逻辑
    }
  }

  // 1. 从路由取 taskId（错题本/历史/规划详情）
  const taskId = route.params.taskId
  if (taskId) {
    try {
      const res = await fetch(`${import.meta.env.VITE_BACKEND_URL}/questions/${taskId}`, {
        headers: { 'Authorization': `Bearer ${authStore.token}` }
      })
      if (!res.ok) throw new Error('获取题目失败')
      const data = await res.json()

      question.value = data
      evaluated.value = false
      evaluationResult.value = null
      userAnswer.value = ''
      initUI(question.value)
      loading.value = false
      return
    } catch (error) {
      console.error('加载题目失败:', error)
      ElMessage.error('加载题目失败')
      router.back()
      loading.value = false
      return
    }
  }

  // 2. 如果没 ID，读缓存（规划详情跳转）
  const stored = sessionStorage.getItem('current_question')
  if (stored) {
    try {
      const parsed = JSON.parse(stored)
      question.value = parsed
      initUI(question.value)
      loading.value = false
      return
    } catch {}
  }

  // 3. 什么都没有，才生成（资源库直接点生成）
  const query = route.query
  try {
    const newQuestion = await generateQuestion({
      user_id: authStore.user.id,
      category: query.category || '通用',
      topic: query.topic || '',
      question_type: query.questionType || '选择题',
      difficulty: '中等',
      extra: ''
    })
    question.value = newQuestion
    initUI(question.value)
  } catch (error) {
    ElMessage.error('生成题目失败')
    router.back()
  } finally {
    loading.value = false
  }
}

function initUI(q) {
  const currentType = q.question_type || 'choice'
  const displayType = typeDisplayMap[currentType] || '选择题'
  availableTypes.value = allTypes.filter(t => t !== displayType)
  selectedTypes.value = [...availableTypes.value]
  if (availableTypes.value.length) {
    targetType.value = availableTypes.value[0]
  }

  if (q.question_type === 'choice' &&
      (!q.options || Object.keys(q.options).length === 0)) {
    q.options = { 'A': '选项 A', 'B': '选项 B', 'C': '选项 C', 'D': '选项 D' }
  }
}

// ============================================================
// ✅ 核心提交逻辑：更新掌握度 + 错题状态
// ============================================================
async function handleSubmit() {
  if (!userAnswer.value) {
    ElMessage.warning('请先作答')
    return
  }

  // 编程题且有测试用例 → 沙箱逐点判分，不再交给 AI 批改
  if (isProgramming.value && hasTestCases.value) {
    submitting.value = true
    try {
      await submitProgramming()
      if (evaluationResult.value?.is_correct) ElMessage.success('全部测试点通过 🎉')
      else ElMessage.warning('还有测试点没通过，再改改')
    } catch (e) {
      ElMessage.error('判分失败：' + (e?.message || '请重试'))
    } finally {
      submitting.value = false
    }
    return
  }

  submitting.value = true
  try {
    const result = await evaluateAnswer({
      question: question.value,
      user_answer: userAnswer.value,
      user_id: authStore.user.id
    })

    // 如果是错题本进来的，且掌握度 >= 60，自动更新为“已攻克”
    const fromMistake = sessionStorage.getItem('from_mistake_book')
    if (fromMistake === 'true' && result.mastery_score >= 60) {
      try {
        await fetch(`${import.meta.env.VITE_BACKEND_URL}/questions/${question.value.id}/mistake-status`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authStore.token}`
          },
          body: JSON.stringify({ status: 'conquered' })
        })
        sessionStorage.removeItem('from_mistake_book')
        ElMessage.success('🎉 错题已攻克！')
      } catch (err) {
        console.error('更新错题状态失败:', err)
      }
    }

    evaluationResult.value = result
    evaluated.value = true

    const searchTerms = []
    const topic = question.value.topic || ''
    if (topic) searchTerms.push(topic)
    const typeName = getTypeDisplay(question.value.question_type)
    const keyword = searchTerms.length > 0
      ? searchTerms[0] + (typeName ? ' ' + typeName : '')
      : topic || '学习'

    searchKeyword.value = keyword
    await searchVideos(keyword)
    await loadLibraryVideos()

  } catch (error) {
    ElMessage.error('评估失败: ' + error.message)
  } finally {
    submitting.value = false
  }
}

function resetEvaluation() {
  evaluated.value = false
  evaluationResult.value = null
  userAnswer.value = ''
  videos.value = []
  videoSearched.value = false
  videoLoading.value = false
  // 视频库状态一并重置
  clearLibPoll()
  libVideos.value = []
  libGenerating.value = false
  libTriggered.value = false
}

async function handleRegenerate() {
  const { category, topic, question_type, difficulty_score } = question.value
  regenerating.value = true
  try {
    const s = Number(difficulty_score) || 6
    // 三档区间映射（与后端一致：简单 1-3 / 中等 4-6 / 困难 7-10）
    const diff = s <= 3 ? '简单' : s < 7 ? '中等' : '困难'
    const typeMap = {
      choice: '选择题', fill: '填空题', judge: '判断题',
      essay: '简答题', calculation: '计算题', coding: '编程题', programming: '编程题'
    }
    const newQuestion = await generateQuestion({
      user_id: authStore.user.id,
      category: category || '通用',
      topic: topic || '',
      question_type: typeMap[question_type] || '选择题',
      difficulty: diff,
      extra: ''
    })
    question.value = newQuestion
    resetEvaluation()
    const currentType = newQuestion.question_type || 'choice'
    const displayType = typeDisplayMap[currentType] || '选择题'
    availableTypes.value = allTypes.filter(t => t !== displayType)
    selectedTypes.value = [...availableTypes.value]
    if (availableTypes.value.length) {
      targetType.value = availableTypes.value[0]
    }
    ElMessage.success('已重新生成')
  } catch (error) {
    ElMessage.error('重新生成失败: ' + error.message)
  } finally {
    regenerating.value = false
  }
}

async function handleChangeType() {
  if (changeMode.value === 'random' && !selectedTypes.value.length) {
    ElMessage.warning('请至少选择一个题型')
    return
  }
  if (changeMode.value === 'specify' && !targetType.value) {
    ElMessage.warning('请选择题型')
    return
  }

  const newType = changeMode.value === 'random'
    ? selectedTypes.value[Math.floor(Math.random() * selectedTypes.value.length)]
    : targetType.value

  changingType.value = true
  try {
    const { category, topic, difficulty_score } = question.value
    const s = Number(difficulty_score) || 6
    // 三档区间映射（与后端一致：简单 1-3 / 中等 4-6 / 困难 7-10）
    const diff = s <= 3 ? '简单' : s < 7 ? '中等' : '困难'

    const newQuestion = await generateQuestion({
      user_id: authStore.user.id,
      category: category || '通用',
      topic: topic || '',
      question_type: newType,
      difficulty: diff,
      extra: ''
    })

    question.value = newQuestion
    resetEvaluation()

    const currentType = newQuestion.question_type || 'choice'
    const displayType = typeDisplayMap[currentType] || '选择题'
    availableTypes.value = allTypes.filter(t => t !== displayType)
    selectedTypes.value = [...availableTypes.value]
    if (availableTypes.value.length) {
      targetType.value = availableTypes.value[0]
    }

    showChangeType.value = false
    ElMessage.success(`已切换为 ${newType}`)
  } catch (error) {
    ElMessage.error('换题型失败: ' + error.message)
  } finally {
    changingType.value = false
  }
}

function handleAddToSet() {
  console.log('🔵 打开弹窗, 加载题集')
  showAddToSet.value = true
  loadQuestionSets()
}

async function handleAddToSetConfirm(setId) {
  addingSetId.value = setId
  try {
    const baseUrl = import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'
    const res = await fetch(`${baseUrl}/questions/set/${setId}/add/${question.value.id}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authStore.token}`,
        'Content-Type': 'application/json'
      }
    })
    if (!res.ok) throw new Error('加入失败')

    ElMessage.success('已加入题集')
    await loadQuestionSets()
  } catch (error) {
    ElMessage.error('加入失败')
  } finally {
    addingSetId.value = null
  }
}

function goCreateSet() {
  showAddToSet.value = false
  router.push('/resource-lib')
}

function showHint() {
  if (question.value.hint) {
    ElMessage.info('💡 ' + question.value.hint)
  } else {
    ElMessage.info('暂无提示')
  }
}

function goBack() {
  const fromMistake = sessionStorage.getItem('from_mistake_book')
  if (fromMistake === 'true') {
    sessionStorage.removeItem('from_mistake_book')
    router.push('/resource-lib')
  } else {
    router.back()
  }
}

onMounted(loadQuestion)
onUnmounted(() => {
  clearLibPoll()
  if (libViewTimer) clearTimeout(libViewTimer)
})
</script>

<style scoped>
.question-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px 32px;
}

.question-container {
  max-width: 1000px;
  width: 100%;
  padding: 40px 48px;
  border-radius: 18px;
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--line-soft);
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
}

.question-container:hover {
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.06);
}

[data-theme="dark"] .question-container {
  background: var(--well);
  border-color: rgba(255, 255, 255, 0.04);
}
[data-theme="dark"] .question-container:hover {
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.2);
}

.question-topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}
.question-topbar h2 {
  margin: 0;
  font-size: 22px;
  color: var(--text-primary);
}
.back-btn {
  color: var(--text-secondary) !important;
  transition: all 0.3s ease !important;
}
.back-btn:hover {
  color: var(--text-primary) !important;
  transform: translateX(-2px);
}

/* ===== 加载状态 ===== */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  gap: 16px;
  color: var(--text-muted);
}
.loader {
  width: 40px;
  height: 40px;
  border: 3px solid color-mix(in srgb, var(--brand) 10%, transparent);
  border-top-color: var(--brand);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ===== 难度圆环 + 信息 ===== */
.question-meta {
  display: flex;
  align-items: center;
  gap: 32px;
  flex-wrap: wrap;
  padding: 8px 0;
}

.difficulty-ring {
  position: relative;
  width: 72px;
  height: 72px;
  flex-shrink: 0;
  transition: transform 0.3s ease;
}
.difficulty-ring:hover {
  transform: scale(1.05);
}
.ring-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}
.ring-label {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  line-height: 1.2;
}
.ring-score {
  display: block;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}
.ring-text {
  display: block;
  font-size: 9px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.meta-right {
  display: flex;
  flex-wrap: wrap;
  gap: 20px 40px;
  flex: 1;
}
.meta-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.meta-label {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.meta-value {
  font-size: 15px;
  color: var(--text-primary);
  font-weight: 500;
}

.question-content h3 {
  font-size: 20px;
  line-height: 1.8;
  color: var(--text-primary);
  font-weight: 500;
}

.answer-area {
  margin: 20px 0;
}

.choice-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: flex-start;
  width: 100%;
}
.choice-item {
  padding: 12px 18px;
  border-radius: 10px;
  border: 1px solid var(--border-color);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  width: 100%;
  cursor: pointer;
  font-size: 15px;
}
.choice-item:hover {
  background: rgba(128, 128, 128, 0.06);
  border-color: rgba(128, 128, 128, 0.2);
  transform: translateX(4px);
}
.choice-item.is-checked {
  border-color: var(--brand);
  background: color-mix(in srgb, var(--brand) 6%, transparent);
  transform: translateX(4px);
}

.judge-group {
  display: flex;
  gap: 20px;
  align-items: flex-start;
  flex-wrap: wrap;
}
.judge-item {
  padding: 12px 28px;
  border-radius: 10px;
  border: 1px solid var(--border-color);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  cursor: pointer;
  font-size: 15px;
}
.judge-item:hover {
  background: rgba(128, 128, 128, 0.06);
  border-color: rgba(128, 128, 128, 0.2);
  transform: translateY(-2px) scale(1.02);
}
.judge-item.is-checked {
  border-color: var(--brand);
  background: color-mix(in srgb, var(--brand) 6%, transparent);
}

.evaluation {
  padding: 24px 28px;
  border-radius: 14px;
  background: rgba(128, 128, 128, 0.04);
  transition: all 0.3s ease;
}
.evaluation:hover {
  background: rgba(128, 128, 128, 0.06);
}

.correct {
  color: color-mix(in srgb, #6BCB77 65%, var(--text-primary));
  font-weight: 600;
  font-size: 20px;
}
.incorrect {
  color: #FF6B6B;
  font-weight: 600;
  font-size: 20px;
}

.correct-answer,
.user-answer-display {
  margin: 8px 0;
  padding: 10px 14px;
  border-radius: 8px;
  background: rgba(128, 128, 128, 0.04);
}
.correct-answer .label,
.user-answer-display .label {
  font-weight: 500;
  color: var(--text-secondary);
}
.correct-answer .answer {
  color: color-mix(in srgb, #6BCB77 65%, var(--text-primary));
  font-weight: 600;
}
.user-answer-display .answer {
  color: var(--text-primary);
  font-weight: 600;
}

.mastery-section {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 16px 0;
}
.mastery-label {
  font-size: 14px;
  color: var(--text-secondary);
  white-space: nowrap;
}
.mastery-bar {
  flex: 1;
  height: 10px;
  border-radius: 5px;
  background: rgba(128, 128, 128, 0.15);
  overflow: hidden;
}
.mastery-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 0.8s ease;
}
.mastery-score {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  min-width: 48px;
  text-align: right;
}

.detail-analysis {
  margin: 12px 0;
  padding: 14px 16px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--brand) 4%, transparent);
  border-left: 3px solid var(--brand);
}
.analysis-title {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
  font-size: 14px;
}
.analysis-content {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
}

.eval-text {
  margin: 8px 0;
  color: var(--text-secondary);
  font-size: 15px;
  line-height: 1.7;
}
.eval-text strong {
  color: var(--text-primary);
}

.video-section {
  margin: 16px 0;
  padding: 14px 16px;
  border-radius: 12px;
  background: rgba(128, 128, 128, 0.03);
}
.video-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.video-title {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-weight: 600;
  font-size: 15px;
  color: var(--text-primary);
}
.video-title .icon {
  width: 17px;
  height: 17px;
  color: var(--brand-bright);
  flex: none;
}
.more-link {
  font-size: 13px;
  color: var(--brand);
  text-decoration: none;
  cursor: pointer;
  transition: all 0.3s ease;
}
.more-link:hover {
  color: var(--brand-bright);
  transform: translateX(2px);
}

.video-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
@media (max-width: 768px) {
  .video-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 480px) {
  .video-grid {
    grid-template-columns: 1fr;
  }
}

.video-card {
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

/* ====== 自营视频库（2026-09-04）====== */
.lib-badge {
  font-size: 11px;
  color: var(--brand-bright);
  padding: 2px 9px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--brand) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--brand) 30%, transparent);
}
.lib-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}
.lib-card {
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent);
  border: 1px solid rgba(255, 255, 255, 0.07);
}
.lib-card:hover {
  transform: translateY(-4px) scale(1.01);
  border-color: color-mix(in srgb, var(--brand) 35%, transparent);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.14);
}
.lib-poster {
  position: relative;
  aspect-ratio: 16/9;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
}
.lib-name-fallback {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 12px;
  text-align: center;
  font-size: 14px;
  font-weight: 700;
  color: #e8edf7;
}
.lib-poster.tpl-chalkboard {
  background: linear-gradient(160deg, #0f1722 0%, #142030 60%, #101a28 100%);
  border-bottom: 1px solid rgba(160, 200, 255, .12);
}
.lib-poster.tpl-cards {
  background: linear-gradient(160deg, #f4f6fb 0%, #e9eef7 100%);
  border-bottom: 1px solid rgba(120, 140, 180, .14);
}
.lib-poster.generating { background: rgba(128, 128, 128, .08); }
.lib-poster .lib-pen { width: 30px; height: 30px; color: var(--text-secondary); }
.lib-poster-body { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; padding: 0 30px 0 12px; text-align: center; width: 100%; height: 100%; }
.lib-poster-t { font-size: 13px; font-weight: 700; color: #e8edf7; }
.lib-poster-l { font-size: 10px; color: rgba(201, 214, 234, .7); max-width: 92%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tpl-cards .lib-poster-t { color: #1c2b45; }
.tpl-cards .lib-poster-l { color: rgba(69, 83, 110, .75); }
.lib-poster-play { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,.16); color: #5ed0ff; }
.lib-poster-play svg { width: 12px; height: 12px; margin-left: 1px; }
.lib-card:hover .lib-poster-play { background: rgba(255,255,255,.25); }
.lib-dur { display: inline-flex; align-items: center; gap: 4px; }
.lib-dur svg { width: 12px; height: 12px; }
.lib-poster-mark {
  position: absolute;
  left: 10px;
  top: 10px;
  font-size: 11px;
  padding: 2px 9px;
  border-radius: 999px;
  background: rgba(10, 14, 24, .55);
  color: #dfe7f5;
  border: 1px solid rgba(255, 255, 255, .14);
}
.lib-score {
  position: absolute;
  right: 10px;
  top: 10px;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(10, 14, 24, .55);
  color: #ffd97a;
  border: 1px solid rgba(255, 217, 122, .25);
}
.lib-score.exact {
  color: #7af0b0;
  border-color: rgba(122, 240, 176, .3);
}
.lib-info { padding: 9px 11px 10px; }
.lib-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.lib-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-top: 5px;
  font-size: 11px;
  color: var(--text-muted);
}
.lib-author {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-secondary);
}
.lib-author img {
  width: 15px;
  height: 15px;
  border-radius: 50%;
  object-fit: cover;
  background: #fff;
  flex: none;
}
.lib-card.generating { cursor: default; opacity: .85; }
.lib-card.generating .lib-poster { animation: lib-pulse 1.6s ease-in-out infinite; }
.lib-card.generating .lib-poster::after {
  content: "";
  position: absolute; inset: 0;
  background: linear-gradient(105deg, transparent 38%, rgba(255, 255, 255, .13) 50%, transparent 62%);
  background-size: 220% 100%;
  animation: lib-shimmer 1.8s ease-in-out infinite;
  pointer-events: none;
}
@keyframes lib-pulse {
  0%, 100% { opacity: .55; }
  50% { opacity: 1; }
}
@keyframes lib-shimmer {
  from { background-position: 130% 0; }
  to { background-position: -130% 0; }
}
.video-card:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  border-color: var(--line-soft);
}
.video-card img {
  width: 100%;
  aspect-ratio: 16/9;
  object-fit: cover;
  display: block;
}
.video-info {
  padding: 8px 10px;
}
.video-title-text {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.4;
}
.video-meta {
  font-size: 11px;
  color: var(--text-muted);
  display: flex;
  gap: 10px;
  margin-top: 4px;
}
.video-empty {
  padding: 12px 0;
  color: var(--text-muted);
  font-size: 14px;
  text-align: center;
}

.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.action-buttons .el-button {
  border-radius: 10px;
  padding: 10px 20px;
  font-size: 14px;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
}
.action-buttons .el-button:hover {
  transform: translateY(-2px) scale(1.02);
}
.action-buttons .el-button:active {
  transform: translateY(0px) scale(0.98);
}
.action-buttons .el-button--primary {
  background: color-mix(in srgb, var(--brand) 12%, transparent) !important;
  border-color: color-mix(in srgb, var(--brand) 20%, transparent) !important;
  color: var(--brand) !important;
}
.action-buttons .el-button--primary:hover {
  background: color-mix(in srgb, var(--brand) 20%, transparent) !important;
}

.change-type-dialog {
  padding: 4px 0;
}
.dialog-tip {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 12px;
}
.sub-tip {
  color: var(--text-muted);
  font-size: 13px;
  margin: 8px 0;
}
.change-mode-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.random-types {
  margin-top: 12px;
}
.type-checkboxes {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  margin: 8px 0;
}
.warning-tip {
  color: #f56c6c;
  font-size: 13px;
  margin: 4px 0;
}
.specify-type {
  margin-top: 12px;
}

.set-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  margin-bottom: 8px;
  transition: all 0.3s ease;
}
.set-item:hover {
  background: rgba(128, 128, 128, 0.04);
}
.set-item.already {
  opacity: 0.6;
}
.set-info {
  display: flex;
  gap: 12px;
  align-items: center;
}
.set-name {
  font-weight: 500;
  color: #ff0000;
}
.set-count {
  font-size: 12px;
  color: var(--text-muted);
}
.empty-state {
  text-align: center;
  padding: 20px 0;
  color: var(--text-muted);
}
.empty-state p {
  margin-bottom: 12px;
}

.video-dialog :deep(.el-dialog) {
  max-width: 94vw;   /* 手机上 760px 会溢出屏幕 */
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent) !important;
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  border: 1px solid var(--line-soft) !important;
  border-radius: 16px !important;
}
[data-theme="dark"] .video-dialog :deep(.el-dialog) {
  background: var(--well) !important;
}
.video-dialog :deep(.el-dialog__title) {
  color: var(--text-primary) !important;
  font-weight: 600;
}
.video-dialog :deep(.el-dialog__body) {
  padding: 12px 20px 20px;
}
.video-dialog :deep(.el-dialog__header) {
  padding: 16px 20px 0;
}

.video-player-container {
  width: 100%;
}
.video-wrapper {
  position: relative;
  width: 100%;
  padding-bottom: 56.25%;
  background: #000;
  border-radius: 10px;
  overflow: hidden;
}
.video-iframe {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: none;
}
.video-detail-info {
  padding: 12px 4px 4px;
}
.video-detail-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}
.video-detail-meta {
  font-size: 13px;
  color: var(--text-muted);
  display: flex;
  gap: 16px;
  margin: 4px 0 10px;
}
.goto-bilibili-btn {
  display: inline-block;
  padding: 6px 18px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--brand) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--brand) 20%, transparent);
  color: var(--brand);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.3s ease;
}
.goto-bilibili-btn:hover {
  background: color-mix(in srgb, var(--brand) 20%, transparent);
  transform: translateY(-2px);
}

[data-theme="dark"] :deep(.el-input__wrapper) {
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent) !important;
  border-color: var(--line-soft) !important;
}
[data-theme="dark"] :deep(.el-input__wrapper:hover) {
  border-color: var(--line-soft) !important;
}
[data-theme="dark"] :deep(.el-textarea__inner) {
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent) !important;
  border-color: var(--line-soft) !important;
  color: var(--text-primary) !important;
}
[data-theme="dark"] :deep(.el-textarea__inner:hover) {
  border-color: var(--line-soft) !important;
}
[data-theme="dark"] :deep(.el-textarea__inner:focus) {
  border-color: var(--line) !important;
}

[data-theme="dark"] .choice-item {
  border-color: var(--line-soft);
}
[data-theme="dark"] .choice-item:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border-color: var(--line);
}
[data-theme="dark"] .judge-item {
  border-color: var(--line-soft);
}
[data-theme="dark"] .judge-item:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border-color: var(--line);
}
[data-theme="dark"] .evaluation {
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
}
[data-theme="dark"] .evaluation:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent);
}
[data-theme="dark"] .set-item {
  border-color: rgba(255, 255, 255, 0.06);
}
[data-theme="dark"] .set-item:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
}

@media (max-width: 640px) {
  .question-page {
    padding: 12px 10px;
    align-items: flex-start;
  }
  .question-container {
    padding: 20px 16px;
    margin-top: 4px;
  }
  .question-meta {
    gap: 16px;
  }
  .meta-right {
    gap: 12px 20px;
  }
  .action-buttons .el-button {
    flex: 1;
    min-width: 56px;
    font-size: 12px;
    padding: 8px 10px;
  }
  .difficulty-ring {
    width: 56px;
    height: 56px;
  }
  .ring-score {
    font-size: 14px;
  }
  .choice-group {
    gap: 6px;
  }
  .judge-group {
    gap: 10px;
  }
  .evaluation {
    padding: 14px;
  }
  .question-content h3 {
    font-size: 16px;
  }
  .question-topbar h2 {
    font-size: 18px;
  }
  .choice-item {
    font-size: 14px;
    padding: 10px 14px;
  }
  .judge-item {
    font-size: 14px;
    padding: 10px 18px;
  }
  .video-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 400px) {
  .video-grid {
    grid-template-columns: 1fr;
  }
}

/* ===== 编程题：代码编辑器 + 沙箱判分 ===== */
.code-editor {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 8px;
}
.ce-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--surface, #ffffff) 70%, transparent);
  border: 1px solid var(--line-soft, rgba(128, 128, 128, .14));
}
.ce-lang {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary, #666);
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.ce-run {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 14px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  color: var(--brand-on, #fff);
  background: var(--brand, #4a6cf7);
  transition: opacity .2s;
}
.ce-run:disabled { opacity: .5; cursor: not-allowed; }
.ce-input :deep(textarea) {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
}
.ce-stdin { display: flex; align-items: center; gap: 10px; }
.ce-lbl {
  flex: none;
  font-size: 12px;
  color: var(--text-tertiary, #999);
}
.ce-out {
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--line-soft, rgba(128, 128, 128, .14));
}
.ce-out-head {
  display: flex;
  justify-content: space-between;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary, #666);
  background: color-mix(in srgb, var(--surface, #ffffff) 60%, transparent);
}
.ce-exit { font-weight: 400; color: var(--text-tertiary, #999); }
.ce-out-body {
  margin: 0;
  padding: 10px 12px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  white-space: pre-wrap;
  word-break: break-all;
  color: var(--text-primary, #222);
}
.ce-samples-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-tertiary, #999);
  margin-bottom: 6px;
}
.ce-sample {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 8px;
}
.ce-sample pre {
  margin: 4px 0 0;
  padding: 8px 10px;
  border-radius: 8px;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
  background: color-mix(in srgb, var(--surface, #ffffff) 55%, transparent);
  border: 1px solid var(--line-soft, rgba(128, 128, 128, .14));
  color: var(--text-primary, #222);
}
.ce-results { margin-top: 4px; }
.ce-res {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 12px;
  border-radius: 8px;
  margin-bottom: 6px;
  font-size: 13px;
  background: color-mix(in srgb, var(--surface, #ffffff) 55%, transparent);
  border: 1px solid var(--line-soft, rgba(128, 128, 128, .14));
}
.ce-res-badge {
  flex: none;
  font-weight: 700;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 6px;
  color: #fff;
  background: var(--text-tertiary, #999);
}
.ce-res-ac .ce-res-badge { background: #2e9e5b; }
.ce-res-wa .ce-res-badge { background: #d98b1e; }
.ce-res-re .ce-res-badge,
.ce-res-tle .ce-res-badge { background: #cf4a4a; }
.ce-res-desc { color: var(--text-secondary, #666); }
.ce-res-note {
  margin-left: auto;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  color: var(--text-tertiary, #999);
}
@media (max-width: 560px) {
  .ce-sample { grid-template-columns: 1fr; }
  .ce-res-note { display: none; }
}
</style>