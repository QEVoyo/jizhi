<template>
  <div class="admin-questions">
    <div class="page-header">
      <h2 class="page-title">题库管理</h2>
      <div class="header-actions">
        <el-button size="default" @click="showCreateDialog" :disabled="!selectedSyllabus">
          <i class="fas fa-plus"></i> 新增题目
        </el-button>
        <el-upload :auto-upload="false" :show-file-list="false" accept=".json" @change="handleImport" :disabled="!selectedSyllabus">
          <el-button size="default" :disabled="!selectedSyllabus">
            <i class="fas fa-upload"></i> 批量导入
          </el-button>
        </el-upload>
      </div>
    </div>

    <!-- 考纲选择 -->
    <div class="filter-row">
      <el-select v-model="selectedSyllabus" placeholder="选择考纲" size="default" @change="onSyllabusChange" style="min-width:200px">
        <el-option v-for="s in syllabi" :key="s.id" :label="s.name" :value="s.id" />
      </el-select>
      <span v-if="syllabi.length && !selectedSyllabus" class="hint">请先选择考纲</span>
      <span v-else-if="selectedSyllabus" class="stat-chip">共 <strong>{{ total }}</strong> 题</span>
    </div>

    <!-- 统计 + 筛选 -->
    <template v-if="selectedSyllabus">
      <div class="filter-row">
        <el-select v-model="filters.category" placeholder="维度" size="small" clearable @change="loadQuestions">
          <el-option v-for="d in currentDimensions" :key="d.category" :label="d.name" :value="d.category" />
        </el-select>
        <el-select v-model="filters.question_type" placeholder="题型" size="small" clearable @change="loadQuestions">
          <el-option v-for="t in currentTypes" :key="t" :label="typeLabel(t)" :value="t" />
        </el-select>
        <el-input v-model="filters.search" placeholder="搜索题干..." size="small" clearable @input="onSearch" class="search-inline" />
      </div>

      <!-- 题目列表 -->
      <div class="table-wrap">
        <AdminLoading :visible="loading" text="加载题库..." />
        <div class="question-list" v-if="!loading">
          <div v-for="q in questions" :key="q.id" class="q-item">
            <div class="q-header">
              <span class="q-id">{{ q.id.slice(0, 8) }}...</span>
              <span class="q-tag">{{ q.category }}</span>
              <span class="q-tag sub">{{ q.sub_category }}</span>
              <span class="q-tag type-tag">{{ typeLabel(q.question_type) }}</span>
              <span class="q-difficulty" :class="diffClass(q.difficulty)">★ {{ q.difficulty || 3 }}</span>
            </div>
            <div class="q-stem" @click="toggleExpand(q)" :class="{ expanded: expandedId === q.id }">
              {{ getStem(q) }}
            </div>
            <div class="q-expanded" v-if="expandedId === q.id">
              <div v-if="getOptions(q).length" class="q-options">
                <div v-for="(opt, i) in getOptions(q)" :key="i" class="q-option" :class="{ correct: isCorrectAnswer(q, i) }">{{ opt }}</div>
              </div>
              <div class="q-answer"><strong>答案：</strong>{{ formatAnswer(q) }}</div>
              <div class="q-explanation" v-if="q.explanation"><strong>解析：</strong>{{ q.explanation }}</div>
              <div class="q-actions">
                <el-button size="small" text @click="editQuestion(q)">编辑</el-button>
                <el-button size="small" text type="danger" @click="deleteQuestionItem(q)">删除</el-button>
              </div>
            </div>
          </div>
        </div>
        <div class="empty" v-if="!loading && questions.length === 0">暂无题目</div>
        <div class="pagination" v-if="total > pageSize">
          <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="prev, pager, next" @current-change="loadQuestions" />
        </div>
      </div>
    </template>

    <!-- 弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑题目' : '新增题目'" width="660px" class="admin-dialog" @closed="resetForm">
      <el-form :model="form" label-position="top" class="q-form">
        <el-row :gutter="14">
          <el-col :span="8">
            <el-form-item label="维度">
              <el-select v-model="form.category">
                <el-option v-for="d in currentDimensions" :key="d.category" :label="d.name" :value="d.category" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="7">
            <el-form-item label="子分类">
              <el-input v-model="form.sub_category" placeholder="如：近义词辨析" />
            </el-form-item>
          </el-col>
          <el-col :span="9">
            <el-form-item label="题型">
              <el-select v-model="form.question_type">
                <el-option v-for="t in currentTypes" :key="t" :label="typeLabel(t)" :value="t" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="14">
          <el-col :span="6">
            <el-form-item label="难度 (1-10)">
              <el-input-number v-model="form.difficulty" :min="1" :max="10" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="知识点">
              <el-input v-model="form.kp_name" placeholder="如：时态语态" />
            </el-form-item>
          </el-col>
          <el-col :span="10">
            <el-form-item label="考纲">
              <el-input :model-value="selectedSyllabusLabel" disabled />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="题干">
          <el-input v-model="form.stem" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="选项（每行一个，仅选择/完形类题型需要）">
          <el-input v-model="form.optionsText" type="textarea" :rows="4" placeholder="A. London&#10;B. Paris&#10;C. Berlin&#10;D. Madrid" />
        </el-form-item>
        <el-form-item label="正确答案">
          <el-input v-model="form.answerText" placeholder="选择题填字母如 A，翻译题填标准翻译，数组类用逗号分隔..." />
        </el-form-item>
        <el-form-item label="解析">
          <el-input v-model="form.explanation" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveQuestion" :loading="saving">{{ editingId ? '保存' : '创建' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { getQuestions, createQuestion, updateQuestion, deleteQuestion, importQuestions } from '@/api/admin'
import { ElMessage, ElMessageBox } from 'element-plus'
import AdminLoading from '@/components/admin/AdminLoading.vue'
import request from '@/utils/request'

const loading = ref(false)
const questions = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const expandedId = ref(null)

// 考纲列表
const syllabi = ref([])
const selectedSyllabus = ref('')
const selectedSyllabusLabel = computed(() => {
  const s = syllabi.value.find(s => s.id === selectedSyllabus.value)
  return s ? s.name : ''
})

// 当前考纲的维度和题型
const currentDimensions = computed(() => {
  const s = syllabi.value.find(s => s.id === selectedSyllabus.value)
  return s?.dimensions || []
})
const currentTypes = computed(() => {
  const s = syllabi.value.find(s => s.id === selectedSyllabus.value)
  return s?.question_types || []
})

const filters = reactive({ category: '', question_type: '', search: '' })

const typeLabels = {
  choice: '选择题', choice_single: '单选题', choice_multi: '多选题', choice_indefinite: '不定项选择',
  fill: '填空题', cloze: '完形填空', translation: '翻译', essay: '作文', short_answer: '简答',
  case_analysis: '案例分析', teaching_design: '教学设计', programming: '编程', calculation: '计算',
  analysis: '论述分析',
}
function typeLabel(t) { return typeLabels[t] || t || '未知' }

let searchTimer = null
function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; loadQuestions() }, 400)
}

async function loadSyllabi() {
  try {
    const res = await request.get('/subject-plan/syllabi', { params: { user_id: 'admin' } })
    syllabi.value = (res.data?.syllabi || []).filter(s => s.question_bank !== false)
  } catch (e) { console.error('加载考纲失败', e) }
}

function onSyllabusChange() {
  filters.category = ''
  filters.question_type = ''
  filters.search = ''
  page.value = 1
  loadQuestions()
}

async function loadQuestions() {
  if (!selectedSyllabus.value) return
  loading.value = true
  try {
    const params = {
      syllabus_id: selectedSyllabus.value,
      page: page.value,
      page_size: pageSize.value,
    }
    if (filters.category) params.category = filters.category
    if (filters.question_type) params.question_type = filters.question_type
    if (filters.search) params.search = filters.search
    const data = await getQuestions(params)
    questions.value = data.items || []
    total.value = data.total || 0
  } catch (e) { ElMessage.error('加载题库失败') }
  finally { loading.value = false }
}

function getStem(q) {
  const c = typeof q.content === 'string' ? tryParse(q.content) : (q.content || {})
  const s = c.stem || ''
  return s.length > 100 ? s.slice(0, 100) + '...' : s
}
function getOptions(q) {
  const c = typeof q.content === 'string' ? tryParse(q.content) : (q.content || {})
  return c.options || []
}
function formatAnswer(q) {
  if (Array.isArray(q.answer)) return q.answer.join(' / ')
  return String(q.answer || '')
}
function isCorrectAnswer(q, idx) {
  const letters = 'ABCDEFGH'
  return q.answer === letters[idx]
}
function diffClass(d) {
  if (!d || d <= 3) return 'd1'
  if (d <= 6) return 'd5'
  return 'd7'
}
function tryParse(v) { try { return JSON.parse(v) } catch { return {} } }

function toggleExpand(q) {
  expandedId.value = expandedId.value === q.id ? null : q.id
}

// 弹窗
const dialogVisible = ref(false)
const editingId = ref(null)
const saving = ref(false)
const form = reactive({
  category: '', sub_category: '', question_type: 'choice',
  difficulty: 3, kp_name: '', stem: '', optionsText: '', answerText: '', explanation: ''
})

function resetForm() {
  editingId.value = null
  const defCat = currentDimensions.value[0]?.category || ''
  const defType = currentTypes.value[0] || 'choice'
  Object.assign(form, {
    category: defCat, sub_category: '', question_type: defType,
    difficulty: 3, kp_name: '', stem: '', optionsText: '', answerText: '', explanation: ''
  })
}

function showCreateDialog() {
  if (!selectedSyllabus.value) { ElMessage.warning('请先选择考纲'); return }
  resetForm()
  dialogVisible.value = true
}

async function editQuestion(q) {
  editingId.value = q.id
  const c = typeof q.content === 'string' ? tryParse(q.content) : (q.content || {})
  form.category = q.category || ''
  form.sub_category = q.sub_category || ''
  form.question_type = q.question_type || 'choice'
  form.difficulty = q.difficulty || 3
  form.kp_name = q.kp_name || ''
  form.stem = c.stem || ''
  form.optionsText = (c.options || []).join('\n')
  form.answerText = typeof q.answer === 'string' ? q.answer : (Array.isArray(q.answer) ? q.answer.join(', ') : String(q.answer || ''))
  form.explanation = q.explanation || ''
  dialogVisible.value = true
}

async function saveQuestion() {
  saving.value = true
  try {
    const options = form.optionsText.split('\n').filter(o => o.trim())
    const content = { stem: form.stem }
    if (options.length > 0) content.options = options

    // 智能解析 answer：数组格式 "word1, word2" → 数组
    let answer = form.answerText.trim()
    const commas = answer.split(',').filter(s => s.trim())
    if (commas.length > 1 && !/^[A-D]$/.test(answer)) {
      answer = commas.map(s => s.trim())
    }

    const payload = {
      category: form.category,
      sub_category: form.sub_category,
      question_type: form.question_type,
      difficulty: form.difficulty,
      kp_name: form.kp_name,
      content,
      answer,
      explanation: form.explanation,
    }

    if (editingId.value) {
      await updateQuestion(editingId.value, payload)
      ElMessage.success('题目已更新')
    } else {
      await createQuestion(payload, selectedSyllabus.value)
      ElMessage.success('题目已创建')
    }
    dialogVisible.value = false
    loadQuestions()
  } catch (e) { ElMessage.error('保存失败: ' + (e.response?.data?.detail || e.message)) }
  finally { saving.value = false }
}

async function deleteQuestionItem(q) {
  try {
    await ElMessageBox.confirm('确定要删除这道题吗？', '删除确认', { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' })
    await deleteQuestion(q.id)
    ElMessage.success('已删除')
    loadQuestions()
  } catch (e) { /* cancelled */ }
}

async function handleImport(file) {
  if (!selectedSyllabus.value) { ElMessage.warning('请先选择考纲'); return }
  try {
    const text = await file.raw.text()
    const qs = JSON.parse(text)
    if (!Array.isArray(qs)) { ElMessage.error('JSON 格式错误：需要题目数组'); return }
    await importQuestions(qs, selectedSyllabus.value)
    ElMessage.success(`已导入 ${qs.length} 道题目`)
    loadQuestions()
  } catch (e) { ElMessage.error('导入失败：' + (e.message || '格式错误')) }
}

onMounted(async () => { await loadSyllabi() })
</script>

<style scoped>
.admin-questions { max-width: 1100px; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; flex-wrap: wrap; gap: 12px; }
.page-title { font-size: 20px; font-weight: 600; color: #e0e0e0; margin: 0; }
.header-actions { display: flex; gap: 10px; }
.filter-row { display: flex; gap: 10px; margin-bottom: 14px; align-items: center; flex-wrap: wrap; }
.search-inline { width: 200px; }
.hint { font-size: 13px; color: rgba(255,255,255,.3); }
.stat-chip { font-size: 13px; color: rgba(255,255,255,.4); }
.stat-chip strong { color: #e0e0e0; }

.table-wrap {
  background: rgba(255,255,255,.03); backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,.06); border-radius: 14px; overflow: hidden;
}
.question-list { padding: 4px 0; }
.q-item { padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,.03); transition: background .2s; }
.q-item:hover { background: rgba(255,255,255,.02); }
.q-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; flex-wrap: wrap; }
.q-id { font-size: 11px; color: rgba(255,255,255,.2); font-family: monospace; }
.q-tag { padding: 1px 8px; border-radius: 6px; font-size: 11px; background: rgba(64,158,255,.1); color: #409eff; }
.q-tag.sub { background: rgba(20,184,166,.1); color: #14b8a6; }
.q-tag.type-tag { background: rgba(139,92,246,.1); color: #a78bfa; }
.q-difficulty { font-size: 11px; color: rgba(255,255,255,.3); margin-left: auto; }
.q-difficulty.d1 { color: #67c23a; }
.q-difficulty.d5 { color: #e6a23c; }
.q-difficulty.d7 { color: #f56c6c; }
.q-stem { font-size: 13px; color: rgba(255,255,255,.7); cursor: pointer; line-height: 1.5; transition: color .2s; }
.q-stem:hover { color: #409eff; }
.q-expanded { margin-top: 12px; padding: 14px; background: rgba(255,255,255,.03); border-radius: 10px; }
.q-options { display: flex; flex-direction: column; gap: 4px; margin-bottom: 10px; }
.q-option { font-size: 13px; color: rgba(255,255,255,.5); padding: 4px 10px; border-radius: 6px; background: rgba(255,255,255,.02); }
.q-option.correct { background: rgba(103,194,58,.1); color: #67c23a; font-weight: 500; }
.q-answer { font-size: 13px; color: #67c23a; margin-bottom: 4px; }
.q-explanation { font-size: 13px; color: rgba(255,255,255,.5); line-height: 1.5; margin-bottom: 8px; }
.q-actions { display: flex; gap: 6px; }
.empty { padding: 48px; text-align: center; color: rgba(255,255,255,.2); font-size: 14px; }
.pagination { display: flex; justify-content: center; padding: 16px; }

.q-form :deep(.el-form-item__label) { color: rgba(255,255,255,.5) !important; font-size: 12px !important; }
:deep(.el-select .el-input__wrapper), :deep(.el-input__wrapper) {
  background: rgba(255,255,255,.05) !important; border: 1px solid rgba(255,255,255,.08) !important;
  border-radius: 10px !important; box-shadow: none !important;
}
:deep(.el-input__inner), :deep(.el-textarea__inner) { color: #e0e0e0 !important; }
:deep(.el-textarea__inner) {
  background: rgba(255,255,255,.05) !important; border: 1px solid rgba(255,255,255,.08) !important; border-radius: 10px !important;
}
:deep(.admin-dialog) { background: #111827 !important; border: 1px solid rgba(255,255,255,.08) !important; border-radius: 16px !important; }
:deep(.admin-dialog .el-dialog__header) { border-bottom: 1px solid rgba(255,255,255,.06); padding: 18px 24px; }
:deep(.admin-dialog .el-dialog__title) { color: #e0e0e0 !important; }
:deep(.admin-dialog .el-dialog__body) { padding: 24px; }
:deep(.admin-dialog .el-dialog__close) { color: rgba(255,255,255,.4) !important; }
</style>
