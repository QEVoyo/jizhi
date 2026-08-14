<template>
  <div class="sd-page">
    <div class="sd-bg"></div>
    <div class="sd-container">
      <!-- ===== 顶栏 ===== -->
      <div class="sd-topbar">
        <button class="back-btn" @click="$router.push('/subject-plan')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
          <span>考纲列表</span>
        </button>
        <div class="sd-breadcrumb">
          <span class="crumb">学科计划</span>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
          <span class="crumb active">{{ syllabus.name }}</span>
        </div>
      </div>

      <div v-if="pageLoading" class="sd-loading">
        <div class="loading-pulse"></div>
        <span>加载考纲数据...</span>
      </div>

      <!-- ===== 诊断模式：全屏诊断页 ===== -->
      <template v-if="showDiagnosis && !plan">
        <div class="diagnosis-page">
          <!-- 诊断顶栏 -->
          <div class="diag-topbar">
            <button class="back-btn" @click="showDiagnosis = false">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
              <span>返回概览</span>
            </button>
            <div class="sd-breadcrumb">
              <span class="crumb">学科计划</span>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
              <span class="crumb">{{ syllabus.name }}</span>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
              <span class="crumb active">摸底诊断</span>
            </div>
          </div>

          <!-- Step 1: 答题 -->
          <div v-if="diagStep === 1" class="glass-panel diag-panel-full">
            <div class="diag-progress-bar"><div class="diag-bar-fill" :style="{ width: (answeredCount / diagnosisQuestions.length * 100) + '%' }"></div></div>
            <div class="diag-header"><span>摸底诊断</span><span class="diag-counter">{{ answeredCount }} / {{ diagnosisQuestions.length }}</span></div>
            <div v-if="diagnosisQuestions.length" class="diag-question-wrap">
              <div class="q-meta-row">
                <span class="q-badge" :class="'bdg-' + currentQ.category">{{ categoryLabel(currentQ.category) }}</span>
                <span class="q-type">{{ typeLabel(currentQ.question_type) }}</span>
                <span class="q-idx">{{ currentIdx + 1 }} / {{ diagnosisQuestions.length }}</span>
              </div>
              <div class="q-stem">{{ getStem(currentQ) }}</div>
              <div v-if="isChoiceType(currentQ.question_type)" class="q-options">
                <button v-for="(o, i) in getOptions(currentQ)" :key="i" class="opt-btn"
                  :class="{ selected: isMultiChoice(currentQ.question_type) ? (getMultiAnswer(currentQ.id) || []).includes(String.fromCharCode(65 + i)) : answers[currentQ.id] === String.fromCharCode(65 + i) }"
                  @click="isMultiChoice(currentQ.question_type) ? toggleMultiAnswer(currentQ.id, String.fromCharCode(65 + i)) : answers[currentQ.id] = String.fromCharCode(65 + i)">
                  <span class="opt-letter">{{ String.fromCharCode(65 + i) }}</span>
                  <span class="opt-text">{{ o.replace(/^[A-D][.、\s]+/, '') }}</span>
                </button>
                <div v-if="isMultiChoice(currentQ.question_type)" class="multi-hint">可多选，点击已选项取消</div>
              </div>
              <input v-else-if="currentQ.question_type === 'fill' || currentQ.question_type === 'calculation'" v-model="answers[currentQ.id]" class="glass-input" placeholder="输入答案..." />
              <textarea v-else-if="isLongTextType(currentQ.question_type)" v-model="answers[currentQ.id]" class="glass-input textarea" rows="5" :placeholder="longTextPlaceholder(currentQ.question_type)"></textarea>
              <div class="q-nav">
                <button class="btn-ghost" v-if="currentIdx > 0" @click="currentIdx--">上一题</button>
                <div class="q-dots"><span v-for="(_, i) in diagnosisQuestions" :key="i" class="dot" :class="{ done: answers[diagnosisQuestions[i].id], current: i === currentIdx }"></span></div>
                <button v-if="currentIdx < diagnosisQuestions.length - 1" class="btn-ghost accent" @click="currentIdx++">下一题</button>
                <button v-else class="btn-primary" :disabled="answeredCount < diagnosisQuestions.length" @click="diagStep = 2">完成答题</button>
              </div>
            </div>
          </div>

          <!-- Step 2: 设定目标 -->
          <div v-if="diagStep === 2" class="glass-panel diag-panel-full">
            <h2 class="step-title">设定学习目标</h2>
            <div class="goal-form">
              <div class="goal-row"><label>目标分数 <span class="goal-val">{{ goalScore }} 分</span></label>
                <input type="range" v-model.number="goalScore" :min="scoreMin" :max="syllabusMaxScore" :step="syllabusMaxScore <= 10 ? 0.5 : 5" class="glass-range" />
                <div class="range-labels"><span>{{ scoreMin }}</span><span>{{ syllabusPassScore }}</span><span>{{ syllabusMaxScore }}</span></div>
              </div>
              <div class="goal-row"><label>备考周期 <span class="goal-val">{{ periodDays }} 天</span></label>
                <input type="range" v-model.number="periodDays" min="7" max="90" step="1" class="glass-range" />
                <div class="range-labels"><span>7天</span><span>30天</span><span>90天</span></div>
              </div>
              <div class="goal-row"><label>每天学习 <span class="goal-val">{{ dailyMinutes }} 分钟</span></label>
                <input type="range" v-model.number="dailyMinutes" min="15" max="180" step="5" class="glass-range" />
                <div class="range-labels"><span>15m</span><span>60m</span><span>180m</span></div>
              </div>
            </div>
            <div class="goal-actions">
              <button class="btn-ghost" @click="diagStep = 1">返回修改</button>
              <button class="btn-primary" :disabled="submitting" @click="doSubmitDiagnosis">
                <span v-if="submitting" class="btn-spinner"></span>{{ submitting ? 'AI 生成计划中...' : '生成专属计划' }}
              </button>
            </div>
            <div v-if="submitError" class="error-msg">{{ submitError }}</div>
          </div>
        </div>
      </template>

      <!-- ===== 普通模式：考纲详情页 ===== -->
      <template v-else>
        <!-- ===== 考纲头部 ===== -->
        <div class="syllabus-hero glass-panel">
          <div class="hero-badge" :style="{ background: syllabus.color || '#6c8cff' }">{{ syllabus.abbr || syllabus.name?.charAt(0) }}</div>
          <div class="hero-info">
            <h1>{{ syllabus.name }}</h1>
            <p>{{ syllabus.description }}</p>
            <div class="hero-tags">
              <span class="htag">{{ syllabus.question_count }} 题</span>
              <span v-for="d in (syllabus.dimensions || [])" :key="d.name" class="htag dim">{{ d.name }}</span>
            </div>
          </div>
          <div v-if="plan" class="hero-score">
            <div class="score-ring">
              <svg viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(255,255,255,.06)" stroke-width="5"/>
                <circle cx="50" cy="50" r="42" fill="none" :stroke="scoreColor" stroke-width="5" stroke-linecap="round"
                  :stroke-dasharray="264" :stroke-dashoffset="264 - (264 * scorePct / 100)" transform="rotate(-90 50 50)" style="transition: stroke-dashoffset 1s ease"/>
              </svg>
              <span class="score-text">{{ plan.goal_score }}</span>
            </div>
            <span class="score-label">目标分</span>
          </div>
        </div>

        <!-- ===== Tab 栏 ===== -->
        <div class="tab-bar">
          <button v-for="t in tabs" :key="t.key" class="tab-btn" :class="{ active: activeTab === t.key }" @click="switchTab(t.key)">
            <svg v-if="t.key === 'overview'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
            <svg v-if="t.key === 'bank'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>
            <svg v-if="t.key === 'tasks'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>
            <svg v-if="t.key === 'mastery'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20V10M18 20V4M6 20v-4"/></svg>
            <svg v-if="t.key === 'mistakes'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
            {{ t.label }}
          </button>
        </div>

        <!-- ===== 1. 概览 Tab（默认首页）===== -->
        <div v-if="activeTab === 'overview'" class="tab-body">
          <!-- 介绍卡片 -->
          <div class="ov-intro glass-panel">
            <div class="ov-intro-text">{{ syllabus.intro || syllabus.description }}</div>
            <div class="ov-meta-grid">
              <div class="ov-meta">
                <span class="om-label">适合人群</span>
                <span class="om-value">{{ syllabus.suitable_for || '备考该科目的学习者' }}</span>
              </div>
              <div class="ov-meta">
                <span class="om-label">考试维度</span>
                <span class="om-value ov-dims">
                  <span v-for="d in (syllabus.dimensions || [])" :key="d.category" class="ov-dim-tag" :class="{ grey: d.grey }" :title="d.grey ? '该维度暂未上线，等待资源补充' : ''">{{ d.name }}{{ d.grey ? ' 🚧' : '' }}</span>
                </span>
                <span v-if="hasGreyDims" class="ov-grey-hint">🚧 标记维度尚未开放，需等待题目资源或音频文件就绪</span>
              </div>
              <div class="ov-meta">
                <span class="om-label">题库规模</span>
                <span class="om-value">
                  {{ syllabus.question_count }} 题
                  <span v-if="syllabus.target_count" class="ov-target">/ {{ syllabus.target_count }} 目标</span>
                  · {{ enabledTypes.length }} 种题型
                </span>
              </div>
              <div class="ov-meta">
                <span class="om-label">分数范围</span>
                <span class="om-value">满分 {{ syllabus.max_score || 710 }} · 过线 {{ syllabus.pass_score || 425 }}</span>
              </div>
            </div>
          </div>

          <!-- 行动按钮 -->
          <div class="ov-actions">
            <button class="ov-btn primary" @click="openPlanPicker">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3M12 17h.01"/></svg>
              <div>
                <div class="ov-btn-title">生成备考计划</div>
                <div class="ov-btn-desc">摸底诊断 / 真题答卷 → AI 生成专属计划</div>
              </div>
            </button>
            <button class="ov-btn" @click="activeTab = 'bank'; loadBank(1)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>
              <div>
                <div class="ov-btn-title">浏览题库</div>
                <div class="ov-btn-desc">{{ syllabus.question_count }} 题，支持筛选 · 收藏 · 练习</div>
              </div>
            </button>

            <!-- 真题套卷 -->
            <div v-if="(syllabus.exam_papers || []).length" class="ov-exam-section">
              <div class="ov-section-title">真题套卷</div>
              <button v-for="ep in (syllabus.exam_papers || [])" :key="ep.name"
                class="ov-btn exam-btn" :class="{ grey: ep.grey }"
                @click="goExamPaper(ep)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
                <div>
                  <div class="ov-btn-title">{{ ep.name }}</div>
                  <div class="ov-btn-desc">
                    <template v-if="ep.grey">即将上线</template>
                    <template v-else>{{ ep.question_count || 0 }}题 · {{ ep.section_count || 4 }} 卷面{{ ep.available_score ? ' · 可练' + ep.available_score + '分' : '' }}</template>
                  </div>
                </div>
                <span v-if="!ep.grey" class="exam-type-tag" :class="ep.paper_type === 'simulation' ? 'sim' : 'real'">
                  {{ ep.paper_type === 'simulation' ? '仿真' : '真题' }}
                </span>
                <span v-if="ep.grey" class="exam-coming">即将上线</span>
              </button>
            </div>

            <!-- 真题模式选择弹窗 -->
            <div v-if="showExamPicker" class="exam-picker-overlay" @click.self="showExamPicker = null">
              <div class="exam-picker glass-panel">
                <h3>{{ showExamPicker.ep.name }}</h3>
                <p class="exam-picker-meta">
                  {{ showExamPicker.ep.question_count || 0 }}题 · {{ showExamPicker.ep.section_count || 4 }}卷面
                  <span v-if="showExamPicker.ep.available_score"> · 可练{{ showExamPicker.ep.available_score }}分</span>
                </p>
                <div class="exam-picker-choices">
                  <button class="exam-pick-btn practice" @click="enterExamPaper('practice')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                    <div><strong>做题模式</strong><span>模拟考试，计时作答，交卷出分</span></div>
                  </button>
                  <button class="exam-pick-btn review" @click="enterExamPaper('review')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    <div><strong>解析模式</strong><span>查看答案、解析、历史正确率、AI 建议</span></div>
                  </button>
                </div>
                <button class="exam-picker-close" @click="showExamPicker = null">取消</button>
              </div>
            </div>

            <!-- 生成计划通道选择弹窗 -->
            <div v-if="showPlanPicker" class="exam-picker-overlay" @click.self="showPlanPicker = false">
              <div class="exam-picker plan-picker">
                <h3>生成备考计划</h3>
                <p class="exam-picker-meta">选择一种方式，AI 根据评估结果生成专属计划</p>

                <!-- 通道一：摸底生成 -->
                <div class="plan-channel">
                  <div class="plan-channel-head">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3M12 17h.01"/></svg>
                    <strong>摸底生成</strong>
                  </div>
                  <p class="plan-channel-desc">先做摸底诊断题，AI 评估水平后生成计划</p>
                  <button class="plan-channel-btn" @click="startPlanFromDiagnosis">开始摸底</button>
                </div>

                <div class="plan-divider">或</div>

                <!-- 通道二：答卷生成 -->
                <div class="plan-channel">
                  <div class="plan-channel-head">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                    <strong>答卷生成</strong>
                  </div>
                  <p class="plan-channel-desc">根据已完成的真题答卷，AI 分析错题生成计划</p>

                  <!-- 卷子列表 -->
                  <div v-if="planPapersLoading" class="plan-paper-loading">加载卷子...</div>
                  <div v-else-if="!planPapers.length" class="plan-paper-empty">该考纲暂无真题卷</div>
                  <div v-else class="plan-paper-list">
                    <button v-for="p in planPapers" :key="p.paper_id"
                      class="plan-paper-item" :class="{ done: p.completed }"
                      :disabled="!p.completed"
                      @click="p.completed ? generatePlanFromPaper(p) : null">
                      <div class="plan-paper-info">
                        <span class="plan-paper-name">{{ p.name }}</span>
                        <span v-if="p.completed" class="plan-paper-score">
                          上次 {{ p.latest_score_pct }}%（{{ p.latest_score }}/{{ p.available_score }}分）
                        </span>
                        <span v-else class="plan-paper-pending">未完成 — 先做真题</span>
                      </div>
                      <span class="plan-paper-state">
                        <span v-if="p.completed" class="state-done">可生成</span>
                        <span v-else class="state-grey">未完成</span>
                      </span>
                    </button>
                  </div>
                </div>

                <button class="exam-picker-close" @click="showPlanPicker = false">取消</button>
              </div>
            </div>

            <template v-if="plan">
              <div class="ov-plan-badge">已有备考计划 · 目标 {{ plan.goal_score }} 分</div>
              <button class="ov-btn green" @click="activeTab = 'tasks'; loadTabData('tasks')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>
                <div>
                  <div class="ov-btn-title">每日任务</div>
                  <div class="ov-btn-desc">按天解锁，逐日完成备考计划</div>
                </div>
              </button>
              <button class="ov-btn purple" @click="activeTab = 'mastery'; loadTabData('mastery')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20V10M18 20V4M6 20v-4"/></svg>
                <div>
                  <div class="ov-btn-title">知识点掌握度</div>
                  <div class="ov-btn-desc">红→绿渐变卡片，加权平均追踪</div>
                </div>
              </button>
              <button class="ov-btn red" @click="activeTab = 'mistakes'; loadTabData('mistakes')">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                <div>
                  <div class="ov-btn-title">错题本</div>
                  <div class="ov-btn-desc">回顾错题，针对薄弱点复习</div>
                </div>
              </button>
              <div class="ov-plan-footer">
                <button class="btn-ghost small" @click="reDiagnose">重新摸底</button>
                <button class="btn-ghost small danger" @click="doDeletePlan">删除计划</button>
              </div>
            </template>
          </div>
        </div>

        <!-- ===== 2. 题库 Tab ===== -->
        <div v-if="activeTab === 'bank'" class="tab-body">
          <!-- 题目状态统计（有计划时） -->
          <div v-if="plan && qStateCounts.total" class="q-state-bar">
            <span class="qst-chip weak">薄弱 {{ qStateCounts.weak }}</span>
            <span class="qst-chip consolidating">待巩固 {{ qStateCounts.consolidating }}</span>
            <span class="qst-chip strong">优势 {{ qStateCounts.strong }}</span>
            <span class="qst-chip total">共 {{ qStateCounts.total }} 题有记录</span>
          </div>

          <!-- 工具条 -->
          <div class="bank-toolbar">
            <select v-model="bankFilters.category" @change="loadBank(1)" class="glass-select">
              <option value="">全部维度</option>
              <option v-for="d in (syllabus.dimensions || [])" :key="d.category" :value="d.category">{{ d.name }}</option>
            </select>
            <select v-model="bankFilters.sub_category" @change="loadBank(1)" class="glass-select">
              <option value="">全部子分类</option>
              <option v-for="s in bankSubOptions" :key="s" :value="s">{{ s }}</option>
            </select>
            <select v-model="bankFilters.question_type" @change="loadBank(1)" class="glass-select">
              <option value="">全部题型</option>
              <option v-for="t in bankTypeOptions" :key="t" :value="t">{{ typeLabel(t) }}</option>
            </select>
            <button class="pill bank-fav-pill" :class="{ active: bankFavOnly }" @click="bankFavOnly = !bankFavOnly; loadBank(1)">
              <svg viewBox="0 0 24 24" :fill="bankFavOnly ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
              收藏{{ bankFavCount ? `(${bankFavCount})` : '' }}
            </button>
            <div class="bank-search-wrap">
              <svg class="search-icon-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
              <input v-model="bankSearch" class="glass-input small" placeholder="搜索题干..." @input="onBankSearch" />
            </div>
          </div>

          <div v-if="loadingBank" class="tab-loading"><div class="loading-pulse small"></div></div>
          <div v-else-if="bankQuestions.length" class="bank-list">
            <div v-for="q in bankQuestions" :key="q.id" class="bank-q glass-panel"
              :class="[qStateClass(q.id), { open: expandedBankQ === q.id }]">
              <div class="bq-row" @click="toggleBankQ(q.id)">
                <span class="q-badge" :class="'bdg-' + q.category">{{ categoryLabel(q.category) }}</span>
                <span class="bq-sub">{{ q.sub_category }}</span>
                <span v-if="plan && getQState(q.id)" class="bq-state-tag" :class="getQState(q.id).level">
                  {{ getQState(q.id).rate }}% ({{ getQState(q.id).total }}次)
                </span>
                <div v-if="plan && getQMastery(q) !== null" class="bq-mst-bar-wrap" title="掌握度">
                  <div class="bq-mst-bar" :style="{ width: getQMastery(q) + '%', background: masteryColor(getQMastery(q)) }"></div>
                </div>
                <span class="bq-diff">{{ '★'.repeat(q.difficulty || 1) }}</span>
                <button class="bq-practice-btn" @click.stop="goPracticeSingle(q)" title="去练习">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                </button>
                <button class="bq-fav" :class="{ favd: isQFav(q.id) }" @click.stop="toggleQFav(q.id)">
                  <svg viewBox="0 0 24 24" :fill="isQFav(q.id) ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
                </button>
                <svg class="bq-chevron" :class="{ rotated: expandedBankQ === q.id }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
              </div>
              <div class="bq-stem" @click="toggleBankQ(q.id)">{{ getStem(q).slice(0, 150) }}</div>
              <div v-if="expandedBankQ === q.id" class="bq-answer-panel">
                <div class="bq-answer-row"><span class="bq-label">答案</span><span class="bq-ans">{{ getAnswer(q) }}</span></div>
                <div v-if="q.explanation" class="bq-answer-row"><span class="bq-label">解析</span><span class="bq-expl">{{ q.explanation }}</span></div>
              </div>
            </div>
            <div class="bank-pager">
              <button class="btn-ghost small" :disabled="bankPage <= 1" @click="loadBank(bankPage - 1)">上一页</button>
              <span class="pager-info">{{ bankPage }} / {{ bankTotalPages || 1 }}</span>
              <button class="btn-ghost small" :disabled="bankPage >= bankTotalPages" @click="loadBank(bankPage + 1)">下一页</button>
            </div>
          </div>
          <div v-else class="tab-empty">{{ bankFavOnly ? '暂无收藏题目' : '没有匹配的题目' }}</div>
        </div>

        <!-- ===== 3. 每日任务 Tab ===== -->
        <div v-if="activeTab === 'tasks' && plan" class="tab-body">
          <div v-if="loadingTab" class="tab-loading">
            <div class="loading-pulse small"></div><span>加载今日任务...</span>
          </div>
          <template v-else-if="todayTasks.length">
            <div class="day-badge">Day {{ dayNumber }}</div>
            <div v-if="plan.daily_time_hint" class="day-time-hint">⏱ {{ plan.daily_time_hint }}</div>
            <div class="task-list">
              <div v-for="t in todayTasks" :key="t.id" class="task-card glass-panel" :class="{ 'lc-open': expandedTask === t.id }">
                <!-- 任务头 -->
                <div class="task-head">
                  <div class="task-info">
                    <div class="task-title-row">
                      <span v-if="t.phase" class="phase-tag" :class="'phase-' + phaseIndex(t.phase)">{{ t.phase }}</span>
                      <span class="task-title">{{ t.title }}</span>
                    </div>
                    <div class="task-meta">
                      <span>{{ typeLabel(t.question_type) }}</span><span>{{ t.question_count }} 题</span><span v-if="t.estimated_minutes">{{ t.estimated_minutes }} 分钟</span>
                    </div>
                  </div>
                  <button class="task-learn-btn" :class="{ active: expandedTask === t.id }" @click="toggleLearning(t)">
                    📖 学习讲解
                  </button>
                </div>

                <!-- 学习讲解展开区 -->
                <Transition name="learn-expand">
                  <div v-if="expandedTask === t.id" class="task-learning-area">
                    <!-- AI 生成中动画 -->
                    <div v-if="learningStates[t.id] === 'loading'" class="learn-loading">
                      <div class="ai-gen-anim">
                        <span class="ai-dot"></span><span class="ai-dot"></span><span class="ai-dot"></span>
                      </div>
                      <p>AI 正在根据本日题目生成学习讲解...</p>
                      <p class="learn-loading-sub">分析知识点 · 提炼解题方法 · 标注易错点</p>
                    </div>
                    <!-- 生成失败 -->
                    <div v-else-if="learningStates[t.id] === 'error'" class="learn-error">
                      <p>😵 生成失败，<a @click="toggleLearning(t)">点击重试</a></p>
                    </div>
                    <!-- 讲解内容 -->
                    <div v-else-if="t.learning_content || learningStates[t.id] === 'done'" class="learn-content">
                      <div class="learn-summary">
                        <span class="learn-label">🎯 学习目标</span>
                        <p>{{ getLC(t).summary }}</p>
                      </div>
                      <div v-if="getLC(t).key_points?.length" class="learn-block">
                        <span class="learn-label">📚 核心知识点</span>
                        <ul>
                          <li v-for="(kp, i) in getLC(t).key_points" :key="i">{{ kp }}</li>
                        </ul>
                      </div>
                      <div v-if="getLC(t).methods?.length" class="learn-block">
                        <span class="learn-label">🛠 解题方法</span>
                        <ul>
                          <li v-for="(m, i) in getLC(t).methods" :key="i">{{ m }}</li>
                        </ul>
                      </div>
                      <div v-if="getLC(t).common_mistakes?.length" class="learn-block">
                        <span class="learn-label">⚠️ 常见错误</span>
                        <ul>
                          <li v-for="(cm, i) in getLC(t).common_mistakes" :key="i">{{ cm }}</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </Transition>

                <!-- 题目预览 -->
                <div v-if="t.questions?.length" class="task-preview">
                  <div v-for="q in t.questions.slice(0, 3)" :key="q.id" class="preview-line">{{ getStem(q).slice(0, 60) }}{{ getStem(q).length > 60 ? '...' : '' }}</div>
                </div>

                <!-- 操作区：做题 + 视频 -->
                <div class="task-actions">
                  <button class="btn-primary small" @click="goPractice(t)">✏️ 去练习</button>
                  <button class="btn-video disabled" disabled title="视频推送即将上线">
                    🎬 视频推送
                    <span class="video-soon">即将上线</span>
                  </button>
                </div>
              </div>
            </div>
          </template>
          <div v-else class="tab-empty">暂无今日任务，明天再来！</div>
        </div>

        <!-- ===== 4. 知识点 Tab ==== -->
        <div v-if="activeTab === 'mastery' && plan" class="tab-body">
          <div v-if="loadingTab" class="tab-loading"><div class="loading-pulse small"></div></div>
          <div v-else-if="masteryCards.length" class="mastery-cards-row">
            <div v-for="m in masteryCards" :key="m.name" class="mst-card"
              :style="{ background: `linear-gradient(135deg, ${masteryColor(m.score)}, ${masteryColorDark(m.score)})`, boxShadow: `0 4px 20px ${masteryColor(m.score)}40` }">
              <span class="mst-card-topic">{{ m.name }}</span>
              <span class="mst-card-score">{{ m.score }}%</span>
              <button class="mst-card-btn" @click="goMasteryDrill(m)">🎯 攻克</button>
            </div>
          </div>
          <div v-else class="tab-empty">暂无知识点数据</div>
        </div>

        <!-- ===== 5. 错题本 Tab ==== -->
        <div v-if="activeTab === 'mistakes' && plan" class="tab-body">
          <div v-if="loadingTab" class="tab-loading"><div class="loading-pulse small"></div></div>
          <div v-else-if="mistakeList.length" class="mistake-grid">
            <div v-for="m in mistakeList" :key="m.id" class="mistake-card glass-panel">
              <div class="mstk-stem">{{ getStem(m.question)?.slice(0, 120) || 'N/A' }}</div>
              <div class="mstk-answers">
                <span class="mstk-wrong">你的: {{ m.user_answer }}</span>
                <span class="mstk-correct">正确: {{ getAnswer(m.question) }}</span>
              </div>
            </div>
          </div>
          <div v-else class="tab-empty">没有错题，太强了！</div>
        </div>

      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getSyllabusDetail, startDiagnosis, submitDiagnosis, getTodayTasks, getQuestions, getMastery, getMistakes, getQuestionStats, deletePlan, getQuestionStates, listExamPapers, submitExamPlan } from '@/api/subjectPlan'
import { useAuthStore } from '@/stores/auth'
import request from '@/utils/request'
import { typeLabel, buildCategoryMap, isChoiceType, isMultiChoice, isLongTextType, longTextPlaceholder } from '@/utils/questionLabels'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const syllabusId = computed(() => route.params.syllabusId)

const pageLoading = ref(true)
const syllabus = ref({})
const plan = ref(null)
const stats = ref(null)

const allTabs = [
  { key: 'overview', label: '概览', needPlan: false },
  { key: 'bank', label: '题库', needPlan: false },
  { key: 'tasks', label: '每日任务', needPlan: true },
  { key: 'mastery', label: '知识点', needPlan: true },
  { key: 'mistakes', label: '错题本', needPlan: true },
]
const tabs = computed(() => allTabs.filter(t => !t.needPlan || plan.value))
const activeTab = ref('overview')
const loadingTab = ref(false)

// 诊断
const showDiagnosis = ref(false)
const diagStep = ref(1)
const diagnosisQuestions = ref([])
const currentIdx = ref(0)
const answers = ref({})
const goalScore = ref(425)
const periodDays = ref(30)
const dailyMinutes = ref(60)
const submitting = ref(false)
const submitError = ref('')
const answeredCount = computed(() => Object.keys(answers.value).length)
const currentQ = computed(() => diagnosisQuestions.value[currentIdx.value] || {})

const syllabusMaxScore = computed(() => syllabus.value?.max_score || 710)
const syllabusPassScore = computed(() => syllabus.value?.pass_score || 425)
const scoreMin = computed(() => {
  const mx = syllabusMaxScore.value
  if (mx <= 10) return Math.round(mx * 0.3)
  if (mx <= 150) return Math.round(mx * 0.4)
  return Math.round(mx * 0.4)
})
const initGoalFromSyllabus = () => { goalScore.value = syllabusPassScore.value }
watch(syllabus, initGoalFromSyllabus)

const scorePct = computed(() => {
  if (!plan.value) return 0
  const mx = syllabusMaxScore.value; const min = scoreMin.value
  return Math.round(Math.max(0, (plan.value.goal_score - min) / (mx - min)) * 100)
})
const scoreColor = computed(() => {
  const s = plan.value?.goal_score || 0; const pass = syllabusPassScore.value; const mx = syllabusMaxScore.value
  if (s >= mx * 0.85) return '#22c55e'; if (s >= pass) return '#6c8cff'; return '#f59e0b'
})

// 任务
const todayTasks = ref([])
const dayNumber = ref(1)

// 题库
const bankQuestions = ref([]); const bankPage = ref(1); const bankTotal = ref(0)
const bankSearch = ref(''); const bankFavOnly = ref(false); const loadingBank = ref(false)
const expandedBankQ = ref(null)
const bankFilters = ref({ category: '', sub_category: '', question_type: '' })
const pageSize = 20
const qStates = ref({}) // 题目作答状态 map

const QFAV_KEY = 'jizhi-fav-questions'
function loadQFavs() { try { return new Set(JSON.parse(localStorage.getItem(QFAV_KEY) || '[]')) } catch { return new Set() } }
function saveQFavs() { localStorage.setItem(QFAV_KEY, JSON.stringify([...qFavorites.value])) }
const qFavorites = ref(loadQFavs())
const bankFavCount = computed(() => qFavorites.value.size)
function isQFav(id) { return qFavorites.value.has(id) }
function toggleQFav(id) { if (qFavorites.value.has(id)) { qFavorites.value.delete(id) } else { qFavorites.value.add(id) }; saveQFavs() }

const bankSubCategoryMap = computed(() => {
  const map = {}
  const diag = syllabus.value?.diagnosis_config || (syllabus.value?.diagnosisConfig || [])
  diag.forEach(d => { if (!map[d.category]) map[d.category] = []; if (!map[d.category].includes(d.sub)) map[d.category].push(d.sub) })
  return map
})
const hasGreyDims = computed(() => (syllabus.value?.dimensions || []).some(d => d.grey))
const enabledTypes = computed(() => syllabus.value?.question_types_enabled || syllabus.value?.question_types || [])
const bankTypeOptions = computed(() => syllabus.value?.question_types || [])
const bankSubOptions = computed(() => {
  if (!bankFilters.value.category) { const all = Object.values(bankSubCategoryMap.value).flat(); return [...new Set(all)] }
  return bankSubCategoryMap.value[bankFilters.value.category] || []
})
const bankTotalPages = computed(() => Math.ceil(bankTotal.value / pageSize))
let bankSearchTimer = null
function onBankSearch() { clearTimeout(bankSearchTimer); bankSearchTimer = setTimeout(() => loadBank(1), 300) }

// 题目状态
const qStateCounts = computed(() => {
  const c = { weak: 0, consolidating: 0, strong: 0, total: 0 }
  Object.values(qStates.value).forEach(s => { c[s.level]++; c.total++ })
  return c
})
function getQState(qid) { return qStates.value[qid] || null }
function qStateClass(qid) {
  const s = qStates.value[qid]
  if (!s) return ''
  if (s.level === 'weak') return 'q-weak'
  if (s.level === 'consolidating') return 'q-consolidating'
  if (s.level === 'strong') return 'q-strong'
  return ''
}

// 掌握度
const masteryList = ref([])
function masteryColor(score) {
  const s = score || 0
  if (s < 5) return '#FF0000'; if (s < 10) return '#FF1A00'; if (s < 15) return '#FF3300'; if (s < 20) return '#FF4D00'
  if (s < 25) return '#FF6600'; if (s < 30) return '#FF8000'; if (s < 35) return '#FF9900'; if (s < 40) return '#FFB300'
  if (s < 45) return '#FFCC00'; if (s < 50) return '#FFE600'; if (s < 55) return '#D4E000'; if (s < 60) return '#A8D500'
  if (s < 65) return '#7DCC00'; if (s < 70) return '#52C200'; if (s < 75) return '#26B800'; if (s < 80) return '#00AD00'
  if (s < 85) return '#00A300'; if (s < 90) return '#009900'; if (s < 95) return '#008000'; return '#006600'
}
function masteryColorDark(score) {
  const s = score || 0
  if (s < 5) return '#CC0000'; if (s < 15) return '#CC2A00'; if (s < 25) return '#CC5200'; if (s < 35) return '#CC7A00'
  if (s < 45) return '#CCA300'; if (s < 55) return '#A9B300'; if (s < 65) return '#64A100'; if (s < 75) return '#1E8F00'
  if (s < 85) return '#008200'; if (s < 95) return '#006600'; return '#005200'
}
const masteryCards = computed(() =>
  [...masteryList.value].sort((a, b) => (a.mastery_score || 0) - (b.mastery_score || 0))
    .map(m => ({ name: m.kp_name || m.sub_category || m.category || '未知', score: m.mastery_score || 0, category: m.category, sub_category: m.sub_category }))
)
const qMasteryMap = computed(() => {
  const map = {}; masteryList.value.forEach(m => { const key = m.sub_category || m.kp_name; if (key) map[key] = m.mastery_score || 0 }); return map
})
function getQMastery(q) {
  if (!plan.value) return null
  const sub = q.sub_category; if (sub && qMasteryMap.value[sub] !== undefined) return qMasteryMap.value[sub]
  const cat = q.category
  for (const [key, score] of Object.entries(qMasteryMap.value)) { if (cat && key.includes(cat)) return score }
  return null
}

// 错题
const mistakeList = ref([])

// Helpers
const dimLabelMap = computed(() => buildCategoryMap(syllabus.value?.dimensions || []))
function categoryLabel(c) { return dimLabelMap.value[c] || c }
function getStem(q) { const c = q?.content || {}; return typeof c === 'string' ? c : (c.stem || '') }
function getOptions(q) { const c = q?.content || {}; return typeof c === 'string' ? [] : (c.options || []) }
function getAnswer(q) { if (!q) return ''; if (typeof q.answer === 'string') return q.answer; if (Array.isArray(q.answer)) return q.answer.join(' / '); return String(q.answer || '') }
function getMultiAnswer(qid) { if (!answers.value[qid]) answers.value[qid] = []; return answers.value[qid] }
function toggleMultiAnswer(qid, letter) {
  if (!answers.value[qid]) answers.value[qid] = []; const arr = answers.value[qid]; const idx = arr.indexOf(letter)
  if (idx >= 0) arr.splice(idx, 1); else arr.push(letter)
}

async function switchTab(key) {
  activeTab.value = key; loadTabData(key)
  if (key === 'bank') loadBank(bankPage.value)
}

async function loadTabData(key) {
  loadingTab.value = true
  try {
    const pid = plan.value?.id; if (!pid) return
    const uid = authStore.user?.id || ''
    if (key === 'tasks') { const r = await getTodayTasks(pid, uid); todayTasks.value = r.tasks || []; dayNumber.value = r.day_number || 1 }
    else if (key === 'mastery') { const r = await getMastery(pid, uid); masteryList.value = r.mastery || [] }
    else if (key === 'mistakes') { const r = await getMistakes(pid, uid); mistakeList.value = r.mistakes || [] }
  } catch (e) { console.error(e) } finally { loadingTab.value = false }
}

async function loadQuestionStates() {
  if (!plan.value) return
  try {
    const r = await getQuestionStates(plan.value.id, authStore.user.id)
    qStates.value = r.states || {}
  } catch {}
}

async function loadBank(p) {
  bankPage.value = p; loadingBank.value = true; expandedBankQ.value = null
  if (plan.value) {
    try { const r = await getMastery(plan.value.id, authStore.user.id); masteryList.value = r.mastery || [] } catch {}
    loadQuestionStates()
  }
  try {
    const limit = bankFavOnly.value ? 1000 : pageSize; const offset = bankFavOnly.value ? 0 : (p - 1) * pageSize
    const params = { user_id: authStore.user.id, limit, offset }
    if (bankFilters.value.category) params.category = bankFilters.value.category
    if (bankFilters.value.sub_category) params.sub_category = bankFilters.value.sub_category
    if (bankFilters.value.question_type) params.question_type = bankFilters.value.question_type
    if (bankSearch.value.trim()) params.search = bankSearch.value.trim()
    const r = await getQuestions(syllabusId.value, params)
    let qs = r.questions || []
    if (bankFavOnly.value) { qs = qs.filter(q => qFavorites.value.has(q.id)); bankTotal.value = qs.length; const start = (p - 1) * pageSize; qs = qs.slice(start, start + pageSize) }
    else { bankTotal.value = r.total || 0 }
    bankQuestions.value = qs
  } catch (e) { console.error(e) } finally { loadingBank.value = false }
}

function toggleBankQ(id) { expandedBankQ.value = expandedBankQ.value === id ? null : id }

async function doDiagnosis() {
  showDiagnosis.value = true; diagStep.value = 1
  try { const r = await startDiagnosis(syllabusId.value); diagnosisQuestions.value = r.questions || [] } catch (e) { submitError.value = '获取诊断题目失败' }
}
async function doSubmitDiagnosis() {
  submitting.value = true; submitError.value = ''
  try {
    const ansArr = diagnosisQuestions.value.map(q => ({ question_id: q.id, user_answer: answers.value[q.id] || '', time_spent: 0 }))
    const res = await submitDiagnosis(syllabusId.value, { user_id: authStore.user.id, answers: ansArr, preferences: { goal_score: goalScore.value, period_days: periodDays.value, daily_minutes: dailyMinutes.value } })
    if (res.already_exists) {
      // 已有旧计划：询问是否删除重建
      const doReplace = confirm(`你已有一个计划「${res.plan_name || ''}」，是否删除旧计划并用本次结果重新生成？`)
      if (doReplace) {
        await deletePlan(res.plan_id, authStore.user.id)
        // 重新提交（现在没有活跃计划了）
        const res2 = await submitDiagnosis(syllabusId.value, { user_id: authStore.user.id, answers: ansArr, preferences: { goal_score: goalScore.value, period_days: periodDays.value, daily_minutes: dailyMinutes.value } })
        if (res2.already_exists) { alert('重建失败，请稍后再试') }
      }
    }
    await loadSyllabus(); showDiagnosis.value = false; activeTab.value = 'tasks'
    if (plan.value) { loadTabData('tasks'); loadQuestionStates() }
  } catch (e) { submitError.value = '提交失败: ' + (e.response?.data?.detail || e.message) } finally { submitting.value = false }
}
async function reDiagnose() { showDiagnosis.value = true; diagStep.value = 1; answers.value = {}; await doDiagnosis() }

// ===== 学习讲解（AI 按需生成）=====
const expandedTask = ref(null)
const learningStates = ref({})  // taskId → 'loading' | 'done' | 'error'

function phaseIndex(phase) {
  return { '基础期': 1, '强化期': 2, '冲刺期': 3 }[phase] || 1
}

function getLC(task) {
  if (task.learning_content) return task.learning_content
  return {}
}

async function toggleLearning(task) {
  // 收起
  if (expandedTask.value === task.id) {
    expandedTask.value = null
    return
  }
  expandedTask.value = task.id

  // 已有缓存讲解直接显示
  if (task.learning_content) {
    learningStates.value[task.id] = 'done'
    return
  }

  // 调 AI 生成
  learningStates.value[task.id] = 'loading'
  try {
    const res = await request.post(
      `/subject-plan/plans/${plan.value.id}/tasks/${task.id}/generate-learning`,
      { user_id: authStore.user?.id || '' }
    )
    task.learning_content = res.data?.learning_content || null
    learningStates.value[task.id] = 'done'
  } catch (e) {
    console.error('生成学习讲解失败:', e)
    learningStates.value[task.id] = 'error'
  }
}

function goPractice(task) {
  const qs = (task.questions || []).map(q => q.id).join(',')
  const dimsParam = syllabus.value?.dimensions ? encodeURIComponent(JSON.stringify(syllabus.value.dimensions)) : ''
  const pid = plan.value?.id || ''
  const langs = (syllabus.value?.languages || ['python']).join(',')
  router.push(`/subject-plan/${syllabusId.value}/practice?plan_id=${pid}&syllabus_id=${syllabusId.value}&questions=${qs}&dimensions=${dimsParam}&langs=${langs}`)
}
function goPracticeSingle(q) {
  const pid = plan.value?.id || ''
  const dimsParam = syllabus.value?.dimensions ? encodeURIComponent(JSON.stringify(syllabus.value.dimensions)) : ''
  const langs = (syllabus.value?.languages || ['python']).join(',')
  router.push(`/subject-plan/${syllabusId.value}/practice?plan_id=${pid}&syllabus_id=${syllabusId.value}&questions=${q.id}&dimensions=${dimsParam}&langs=${langs}`)
}
async function goMasteryDrill(m) {
  if (!plan.value) return
  try {
    const params = { user_id: authStore.user.id, limit: 50, random_order: true }; if (m.category) params.category = m.category; if (m.sub_category) params.sub_category = m.sub_category
    const r = await getQuestions(syllabusId.value, params); const qs = (r.questions || []).slice(0, 10)
    if (!qs.length) { alert('该知识点暂无题目'); return }
    const ids = qs.map(q => q.id).join(',')
    const dimsParam = syllabus.value?.dimensions ? encodeURIComponent(JSON.stringify(syllabus.value.dimensions)) : ''
    router.push(`/subject-plan/${syllabusId.value}/practice?plan_id=${plan.value.id}&syllabus_id=${syllabusId.value}&questions=${ids}&dimensions=${dimsParam}`)
  } catch (e) { console.error(e) }
}
const showExamPicker = ref(null)

function goExamPaper(ep) {
  if (ep.grey) return
  const paperId = ep.paper_id
  if (!paperId) return
  showExamPicker.value = { paperId, ep }
}

function enterExamPaper(mode) {
  const { paperId } = showExamPicker.value
  showExamPicker.value = null
  router.push(`/subject-plan/${syllabusId.value}/exam/${paperId}?syllabus_id=${syllabusId.value}&mode=${mode}`)
}

// ===== 生成计划双通道 =====
const showPlanPicker = ref(false)
const planPapers = ref([])
const planPapersLoading = ref(false)
const generatingFromPaper = ref(false)

async function openPlanPicker() {
  showPlanPicker.value = true
  planPapersLoading.value = true
  try {
    const userId = authStore.user?.id || ''
    const r = await listExamPapers(syllabusId.value, userId)
    planPapers.value = r.papers || []
  } catch (e) {
    console.error('加载卷子失败:', e)
    planPapers.value = []
  } finally {
    planPapersLoading.value = false
  }
}

function startPlanFromDiagnosis() {
  showPlanPicker.value = false
  doDiagnosis()
}

async function generatePlanFromPaper(p) {
  if (!p.completed || generatingFromPaper.value) return
  generatingFromPaper.value = true
  try {
    const res = await submitExamPlan(p.paper_id, {
      user_id: authStore.user?.id || '',
      period_days: 30,
      daily_minutes: 60
    })
    if (res.error) { alert(res.error); return }
    if (res.already_exists) {
      const doReplace = confirm(`你已有一个计划「${res.plan_name || ''}」，是否删除旧计划并用本次答卷重新生成？`)
      if (doReplace) {
        await deletePlan(res.plan_id, authStore.user?.id || '')
        const res2 = await submitExamPlan(p.paper_id, {
          user_id: authStore.user?.id || '',
          period_days: 30,
          daily_minutes: 60
        })
        if (res2.error || res2.already_exists) { alert('重建失败: ' + (res2.error || '请稍后再试')); return }
      } else {
        showPlanPicker.value = false
        await loadSyllabus()
        activeTab.value = 'tasks'
        return
      }
    }
    showPlanPicker.value = false
    // 回到考纲页，切换到每日任务 Tab（和诊断流程一致）
    await loadSyllabus()
    activeTab.value = 'tasks'
    if (plan.value) { loadTabData('tasks'); loadQuestionStates() }
  } catch (e) {
    alert('生成计划失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    generatingFromPaper.value = false
  }
}

async function doDeletePlan() {
  if (!plan.value) return
  if (!confirm(`确定要删除计划「${plan.value.name || ''}」吗？\n每日任务、答题记录、掌握度数据都会一并清除。`)) return
  try {
    await deletePlan(plan.value.id, authStore.user.id)
    plan.value = null
    activeTab.value = 'overview'
    showDiagnosis.value = false
    diagnosisQuestions.value = []
    todayTasks.value = []
    masteryList.value = []
    mistakeList.value = []
    stats.value = null
    qStates.value = {}
    await loadSyllabus()
  } catch (e) { alert('删除失败: ' + (e.response?.data?.detail || e.message)) }
}
async function loadSyllabus() {
  try {
    const r = await getSyllabusDetail(syllabusId.value, authStore.user?.id || '')
    syllabus.value = r.syllabus || {}; plan.value = r.plan || null
    if (r.plan) { try { stats.value = await getQuestionStats(r.plan.id, authStore.user.id) } catch {} }
  } catch (e) { console.error(e) }
}

onMounted(async () => {
  await loadSyllabus(); pageLoading.value = false
  if (plan.value) { loadTabData('tasks'); loadQuestionStates() }
})
</script>

<style scoped>
.sd-page { min-height: 100vh; position: relative; padding: 32px 24px 80px; background: linear-gradient(135deg, #0a0e17 0%, #111827 40%, #0d1520 100%); color: #e2e8f0; }
.sd-bg { position: fixed; inset: 0; background: radial-gradient(ellipse 60% 50% at 50% -10%, rgba(108,140,255,.06) 0%, transparent 70%), radial-gradient(ellipse 40% 60% at 80% 80%, rgba(139,92,246,.04) 0%, transparent 70%); pointer-events: none; }
.sd-container { width: 100%; max-width: 960px; margin: 0 auto; position: relative; z-index: 1; }
.glass-panel { background: rgba(255,255,255,.025); border: 1px solid rgba(255,255,255,.05); backdrop-filter: blur(20px); border-radius: 16px; transition: all .3s; }
.glass-panel:hover { border-color: rgba(255,255,255,.08); }
.btn-primary { display: inline-flex; align-items: center; gap: 8px; padding: 10px 22px; border-radius: 10px; border: none; background: linear-gradient(135deg, #6c8cff, #5b7bf0); color: #fff; font-size: 14px; font-weight: 600; cursor: pointer; transition: all .25s; font-family: inherit; }
.btn-primary:hover { transform: translateY(-1px); box-shadow: 0 4px 20px rgba(108,140,255,.25); }
.btn-primary:disabled { opacity: .4; cursor: not-allowed; transform: none; box-shadow: none; }
.btn-primary.small { padding: 6px 14px; font-size: 12px; border-radius: 8px; }
.btn-ghost { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 10px; border: 1px solid rgba(255,255,255,.06); background: rgba(255,255,255,.03); color: #94a3b8; font-size: 13px; cursor: pointer; backdrop-filter: blur(12px); transition: all .25s; font-family: inherit; }
.btn-ghost:hover { background: rgba(255,255,255,.06); color: #e2e8f0; }
.btn-ghost.accent { color: #6c8cff; border-color: rgba(108,140,255,.15); }
.btn-ghost.small { padding: 5px 12px; font-size: 12px; border-radius: 8px; }
.btn-ghost.danger { color: #ef4444; border-color: rgba(239,68,68,.1); }
.btn-ghost.danger:hover { background: rgba(239,68,68,.08); border-color: rgba(239,68,68,.2); color: #dc2626; }
.error-msg { margin-top: 14px; padding: 10px 16px; border-radius: 10px; background: rgba(239,68,68,.08); border: 1px solid rgba(239,68,68,.15); color: #ef4444; font-size: 13px; }
.sd-topbar { display: flex; align-items: center; gap: 12px; margin-bottom: 24px; }
.back-btn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 14px; border-radius: 10px; border: 1px solid rgba(255,255,255,.06); background: rgba(255,255,255,.03); color: #94a3b8; font-size: 13px; cursor: pointer; backdrop-filter: blur(12px); transition: all .25s; font-family: inherit; }
.back-btn:hover { background: rgba(255,255,255,.06); color: #e2e8f0; }
.back-btn svg { width: 14px; height: 14px; }
.sd-breadcrumb { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #475569; }
.sd-breadcrumb svg { width: 12px; height: 12px; }
.crumb.active { color: #94a3b8; }
.sd-loading, .tab-loading { display: flex; flex-direction: column; align-items: center; gap: 16px; padding: 80px 0; }
.loading-pulse { width: 40px; height: 40px; border-radius: 50%; background: rgba(108,140,255,.15); animation: pulse-glow 1.5s ease-in-out infinite; }
.loading-pulse.small { width: 28px; height: 28px; }
@keyframes pulse-glow { 0%, 100% { transform: scale(1); opacity: .5; } 50% { transform: scale(1.3); opacity: 1; } }
.syllabus-hero { display: flex; gap: 20px; padding: 24px 28px; margin-bottom: 20px; align-items: center; }
.hero-badge { width: 56px; height: 56px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: 700; color: #fff; flex-shrink: 0; }
.hero-info { flex: 1; }
.hero-info h1 { font-size: 22px; font-weight: 700; margin: 0 0 4px; }
.hero-info p { font-size: 13px; color: #64748b; margin: 0 0 10px; }
.hero-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.htag { font-size: 11px; padding: 3px 8px; border-radius: 6px; background: rgba(255,255,255,.05); color: #94a3b8; }
.htag.dim { background: rgba(108,140,255,.08); color: #6c8cff; }
.hero-score { display: flex; flex-direction: column; align-items: center; gap: 4px; flex-shrink: 0; }
.score-ring { width: 64px; height: 64px; position: relative; }
.score-ring svg { width: 100%; height: 100%; }
.score-text { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: 700; }
.score-label { font-size: 11px; color: #64748b; }

/* Tab */
.tab-bar { display: flex; gap: 2px; margin-bottom: 16px; padding: 4px; border-radius: 12px; background: rgba(255,255,255,.02); border: 1px solid rgba(255,255,255,.03); }
.tab-btn { flex: 1; display: flex; align-items: center; justify-content: center; gap: 6px; padding: 10px 8px; border: none; border-radius: 10px; background: transparent; color: #64748b; cursor: pointer; font-size: 13px; font-family: inherit; transition: all .25s; }
.tab-btn:hover { color: #94a3b8; background: rgba(255,255,255,.02); }
.tab-btn.active { color: #e2e8f0; background: rgba(108,140,255,.1); font-weight: 600; }
.tab-btn svg { width: 15px; height: 15px; }
.tab-body { margin-top: 8px; }
.tab-empty { text-align: center; padding: 60px 20px; color: #475569; font-size: 14px; }

/* 概览 */
.ov-intro { padding: 24px 28px; margin-bottom: 20px; }
.ov-intro-text { font-size: 14px; line-height: 1.8; color: #94a3b8; }
.ov-meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 20px; padding-top: 18px; border-top: 1px solid rgba(255,255,255,.04); }
.ov-meta { display: flex; flex-direction: column; gap: 2px; }
.om-label { font-size: 11px; color: #475569; text-transform: uppercase; letter-spacing: .05em; }
.om-value { font-size: 13px; color: #cbd5e1; font-weight: 500; }
.ov-dims { display: flex; gap: 6px; flex-wrap: wrap; }
.ov-dim-tag { font-size: 11px; padding: 2px 10px; border-radius: 6px; background: rgba(108,140,255,.1); color: #6c8cff; }
.ov-dim-tag.grey { background: rgba(255,255,255,.03); color: #475569; text-decoration: line-through; cursor: help; }
.ov-grey-hint { display: block; font-size: 10px; color: #475569; margin-top: 4px; }
.ov-target { font-size: 11px; color: #64748b; }
.ov-exams { margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,.04); }
.ov-exam-list { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 6px; }
.ov-exam-tag { font-size: 12px; padding: 4px 12px; border-radius: 8px; background: rgba(245,158,11,.08); color: #f59e0b; border: 1px solid rgba(245,158,11,.15); }
.ov-exam-tag.grey { background: rgba(255,255,255,.02); color: #475569; border-color: rgba(255,255,255,.04); }
.ov-exam-section { display: flex; flex-direction: column; gap: 8px; }
.ov-section-title { font-size: 11px; color: #475569; text-transform: uppercase; letter-spacing: .1em; padding: 8px 4px 0; }
.ov-btn.exam-btn { opacity: .7; }
.ov-btn.exam-btn:not(.grey) { opacity: 1; border-color: rgba(255,107,107,.15); }
.ov-btn.exam-btn:not(.grey):hover { opacity: 1; border-color: rgba(255,107,107,.3); }
.ov-btn.exam-btn.grey { cursor: default; opacity: .4; }
.ov-btn.exam-btn.grey:hover { transform: none; background: rgba(255,255,255,.03); }
.exam-coming { font-size: 10px; padding: 2px 8px; border-radius: 6px; background: rgba(255,255,255,.04); color: #475569; flex-shrink: 0; }
.exam-type-tag { font-size: 10px; padding: 2px 8px; border-radius: 4px; font-weight: 700; flex-shrink: 0; }
.exam-type-tag.real { background: rgba(255,107,107,.12); color: #ff6b6b; }
.exam-type-tag.sim { background: rgba(255,179,0,.12); color: #ffb300; border: 1px dashed rgba(255,179,0,.25); }

/* ===== 真题模式选择弹窗 ===== */
.exam-picker-overlay { position: fixed; inset: 0; z-index: 500; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,.55); backdrop-filter: blur(6px); }
.exam-picker { padding: 32px 36px; width: 420px; max-width: 90vw; text-align: center; }
.exam-picker h3 { font-size: 20px; margin: 0 0 6px; }
.exam-picker-meta { font-size: 13px; color: #888; margin: 0 0 24px; }
.exam-picker-choices { display: flex; flex-direction: column; gap: 12px; margin-bottom: 16px; }
.exam-pick-btn { display: flex; align-items: center; gap: 14px; padding: 18px 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,.08); background: rgba(255,255,255,.04); cursor: pointer; transition: all .2s; text-align: left; font-family: inherit; color: #e0e0e0; }
.exam-pick-btn:hover { transform: translateY(-2px); }
.exam-pick-btn.practice:hover { border-color: rgba(255,107,107,.3); background: rgba(255,107,107,.06); }
.exam-pick-btn.review:hover { border-color: rgba(64,158,255,.3); background: rgba(64,158,255,.06); }
.exam-pick-btn svg { width: 28px; height: 28px; flex-shrink: 0; }
.exam-pick-btn.practice svg { color: #ff6b6b; }
.exam-pick-btn.review svg { color: #409eff; }
.exam-pick-btn strong { display: block; font-size: 15px; margin-bottom: 3px; }
.exam-pick-btn span { display: block; font-size: 12px; color: #888; }
.exam-picker-close { padding: 8px 24px; border: none; border-radius: 8px; background: rgba(255,255,255,.06); color: #999; cursor: pointer; font-family: inherit; font-size: 14px; transition: all .2s; }
.exam-picker-close:hover { background: rgba(255,255,255,.1); color: #ccc; }

/* ===== 生成计划双通道弹窗 ===== */
.plan-picker { width: 500px; max-height: 85vh; overflow-y: auto; }
.plan-channel { padding: 16px 18px; border-radius: 12px; background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.06); margin-bottom: 12px; text-align: left; }
.plan-channel-head { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.plan-channel-head svg { width: 20px; height: 20px; color: #6c8cff; }
.plan-channel-head strong { font-size: 15px; }
.plan-channel-desc { font-size: 12px; color: #888; margin: 0 0 10px; }
.plan-channel-btn { padding: 8px 22px; border: none; border-radius: 8px; background: linear-gradient(135deg, #6c8cff, #8b5cf6); color: #fff; cursor: pointer; font-family: inherit; font-size: 13px; font-weight: 600; transition: all .2s; }
.plan-channel-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(108,140,255,.4); }
.plan-divider { display: flex; align-items: center; gap: 10px; color: #666; font-size: 12px; margin: 14px 0; }
.plan-divider::before, .plan-divider::after { content: ''; flex: 1; height: 1px; background: rgba(255,255,255,.06); }
.plan-paper-loading, .plan-paper-empty { font-size: 13px; color: #666; text-align: center; padding: 14px 0; }
.plan-paper-list { display: flex; flex-direction: column; gap: 6px; }
.plan-paper-item { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 10px 14px; border-radius: 8px; border: 1px solid rgba(255,255,255,.06); background: rgba(255,255,255,.02); cursor: pointer; font-family: inherit; text-align: left; transition: all .2s; }
.plan-paper-item.done { border-color: rgba(16,185,129,.25); background: rgba(16,185,129,.05); }
.plan-paper-item.done:hover { border-color: rgba(16,185,129,.45); transform: translateY(-1px); }
.plan-paper-item:disabled { cursor: not-allowed; opacity: .45; }
.plan-paper-item:disabled:hover { transform: none; }
.plan-paper-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.plan-paper-name { font-size: 13px; font-weight: 600; color: #e0e0e0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.plan-paper-score { font-size: 11px; color: #10b981; }
.plan-paper-pending { font-size: 11px; color: #777; }
.plan-paper-state { flex-shrink: 0; }
.state-done { font-size: 11px; padding: 3px 10px; border-radius: 10px; background: rgba(16,185,129,.15); color: #10b981; font-weight: 600; }
.state-grey { font-size: 11px; padding: 3px 10px; border-radius: 10px; background: rgba(255,255,255,.05); color: #666; }

.ov-actions { display: flex; flex-direction: column; gap: 10px; }
.ov-btn { display: flex; align-items: center; gap: 14px; padding: 16px 20px; border-radius: 14px; border: 1px solid rgba(255,255,255,.06); background: rgba(255,255,255,.03); cursor: pointer; transition: all .25s; text-align: left; font-family: inherit; color: #e2e8f0; }
.ov-btn:hover { border-color: rgba(255,255,255,.12); transform: translateX(4px); background: rgba(255,255,255,.05); }
.ov-btn svg { width: 28px; height: 28px; flex-shrink: 0; }
.ov-btn.primary svg { color: #6c8cff; }
.ov-btn.green svg { color: #22c55e; }
.ov-btn.purple svg { color: #8b5cf6; }
.ov-btn.red svg { color: #ef4444; }
.ov-btn-title { font-size: 15px; font-weight: 600; }
.ov-btn-desc { font-size: 12px; color: #64748b; margin-top: 2px; }
.ov-plan-badge { text-align: center; font-size: 12px; color: #22c55e; padding: 8px 0 2px; }
.ov-plan-footer { display: flex; justify-content: center; gap: 10px; padding-top: 4px; }

/* 题库 */
.bank-toolbar { display: flex; gap: 8px; margin-bottom: 16px; align-items: center; flex-wrap: wrap; }
.bank-fav-pill { display: inline-flex; align-items: center; gap: 5px; padding: 6px 12px; border-radius: 20px; border: 1px solid rgba(255,255,255,.05); background: rgba(255,255,255,.02); color: #64748b; font-size: 12px; cursor: pointer; font-family: inherit; backdrop-filter: blur(12px); transition: all .25s; }
.bank-fav-pill:hover { color: #ef4444; }
.bank-fav-pill.active { color: #ef4444; border-color: rgba(239,68,68,.2); background: rgba(239,68,68,.06); }
.bank-fav-pill svg { width: 13px; height: 13px; }
.bank-search-wrap { position: relative; flex: 1; min-width: 160px; }
.search-icon-sm { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); width: 14px; height: 14px; color: #475569; pointer-events: none; }
.glass-select { padding: 7px 28px 7px 12px; border-radius: 8px; font-size: 12px; color: #94a3b8; background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.06); outline: none; cursor: pointer; font-family: inherit; backdrop-filter: blur(12px); appearance: none; background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 6px center; background-size: 14px; }
.glass-input { width: 100%; padding: 12px 16px; border-radius: 10px; border: 1px solid rgba(255,255,255,.06); background: rgba(255,255,255,.02); color: #e2e8f0; font-size: 14px; font-family: inherit; outline: none; backdrop-filter: blur(12px); }
.glass-input.small { padding: 7px 12px 7px 32px; font-size: 13px; }
.glass-input:focus { border-color: rgba(108,140,255,.2); }

/* 题目状态统计 */
.q-state-bar { display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
.qst-chip { font-size: 11px; padding: 3px 10px; border-radius: 8px; font-weight: 600; }
.qst-chip.weak { background: rgba(239,68,68,.12); color: #ef4444; }
.qst-chip.consolidating { background: rgba(245,158,11,.12); color: #f59e0b; }
.qst-chip.strong { background: rgba(34,197,94,.12); color: #22c55e; }
.qst-chip.total { background: rgba(255,255,255,.04); color: #64748b; }

/* 题库列表 */
.bank-list { display: flex; flex-direction: column; gap: 6px; }
.bank-q { padding: 14px 18px; cursor: pointer; position: relative; }
.bank-q:hover { border-color: rgba(255,255,255,.08); }
.bank-q.open { border-color: rgba(108,140,255,.15); background: rgba(108,140,255,.02); }
.bank-q.q-weak { border-left: 3px solid rgba(239,68,68,.3); }
.bank-q.q-consolidating { border-left: 3px solid rgba(245,158,11,.3); }
.bank-q.q-strong { border-left: 3px solid rgba(34,197,94,.3); }
.bq-row { display: flex; gap: 8px; align-items: center; margin-bottom: 6px; }
.q-badge { font-size: 11px; padding: 3px 10px; border-radius: 6px; font-weight: 600; }
.bdg-vocabulary { background: rgba(64,158,255,.12); color: #409eff; }
.bdg-grammar { background: rgba(139,92,246,.12); color: #8b5cf6; }
.bdg-reading { background: rgba(34,197,94,.12); color: #22c55e; }
.bdg-translation { background: rgba(245,158,11,.12); color: #f59e0b; }
.bdg-writing { background: rgba(236,72,153,.12); color: #ec4899; }
.bdg-cloze { background: rgba(168,85,247,.12); color: #a855f7; }
.bq-sub { font-size: 11px; color: #64748b; }
.bq-state-tag { font-size: 10px; padding: 2px 8px; border-radius: 6px; font-weight: 600; flex-shrink: 0; }
.bq-state-tag.weak { background: rgba(239,68,68,.1); color: #ef4444; }
.bq-state-tag.consolidating { background: rgba(245,158,11,.1); color: #f59e0b; }
.bq-state-tag.strong { background: rgba(34,197,94,.1); color: #22c55e; }
.bq-mst-bar-wrap { width: 42px; height: 4px; border-radius: 2px; background: rgba(255,255,255,.06); overflow: hidden; flex-shrink: 0; }
.bq-mst-bar { height: 100%; border-radius: 2px; transition: width .5s ease; }
.bq-diff { font-size: 10px; color: #f59e0b; letter-spacing: 1px; }
.bq-practice-btn { width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; border-radius: 6px; border: 1px solid rgba(108,140,255,.15); background: rgba(108,140,255,.04); color: #6c8cff; cursor: pointer; flex-shrink: 0; transition: all .25s; }
.bq-practice-btn:hover { background: rgba(108,140,255,.15); transform: scale(1.1); }
.bq-practice-btn svg { width: 12px; height: 12px; }
.bq-fav { width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; border-radius: 6px; border: none; background: transparent; color: #475569; cursor: pointer; flex-shrink: 0; transition: all .25s; }
.bq-fav:hover { color: #ef4444; }
.bq-fav.favd { color: #ef4444; }
.bq-fav svg { width: 13px; height: 13px; }
.bq-chevron { width: 14px; height: 14px; color: #475569; transition: transform .3s; flex-shrink: 0; }
.bq-chevron.rotated { transform: rotate(180deg); }
.bq-stem { font-size: 13px; line-height: 1.6; color: #cbd5e1; }
.bq-answer-panel { margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,.04); animation: slideDown .25s ease; }
@keyframes slideDown { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: translateY(0); } }
.bq-answer-row { display: flex; gap: 10px; margin-bottom: 6px; font-size: 13px; }
.bq-label { font-weight: 600; color: #64748b; flex-shrink: 0; min-width: 36px; }
.bq-ans { color: #22c55e; font-weight: 600; }
.bq-expl { color: #94a3b8; line-height: 1.5; }
.bank-pager { display: flex; justify-content: center; align-items: center; gap: 14px; margin-top: 20px; padding-top: 16px; }
.pager-info { font-size: 12px; color: #475569; }

/* 每日任务 */
.day-badge { display: inline-block; font-size: 13px; font-weight: 600; padding: 4px 12px; border-radius: 8px; background: rgba(108,140,255,.1); color: #6c8cff; margin-bottom: 16px; }
.day-time-hint { font-size: 12px; color: #888; margin-bottom: 12px; padding: 6px 12px; background: rgba(255,255,255,.03); border-radius: 8px; display: inline-block; }
.task-list { display: flex; flex-direction: column; gap: 10px; }
.task-card { display: flex; flex-direction: column; gap: 12px; padding: 18px 22px; transition: border-color .3s; }
.task-card.lc-open { border-color: rgba(108,140,255,.25); }
.task-head { display: flex; align-items: center; gap: 16px; }
.task-info { flex: 1; }
.task-title-row { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.task-title { font-size: 14px; font-weight: 600; }
.phase-tag { font-size: 10px; padding: 2px 8px; border-radius: 4px; font-weight: 700; flex-shrink: 0; }
.phase-1 { background: rgba(16,185,129,.12); color: #10b981; }
.phase-2 { background: rgba(245,158,11,.12); color: #f59e0b; }
.phase-3 { background: rgba(255,107,107,.12); color: #ff6b6b; }
.task-meta { display: flex; gap: 10px; font-size: 11px; color: #64748b; margin-bottom: 8px; }
.task-learn-btn { padding: 8px 14px; border-radius: 8px; border: 1px solid rgba(108,140,255,.2); background: rgba(108,140,255,.06); color: #6c8cff; font-size: 12px; cursor: pointer; font-family: inherit; transition: all .25s; flex-shrink: 0; }
.task-learn-btn:hover { background: rgba(108,140,255,.15); transform: translateY(-1px); }
.task-learn-btn.active { background: rgba(108,140,255,.2); border-color: rgba(108,140,255,.4); }
.preview-line { font-size: 12px; color: #475569; padding: 2px 0; }

/* 学习讲解展开动画 */
.learn-expand-enter-active, .learn-expand-leave-active { transition: all .35s ease; overflow: hidden; }
.learn-expand-enter-from, .learn-expand-leave-to { opacity: 0; max-height: 0; transform: translateY(-8px); }
.learn-expand-enter-to, .learn-expand-leave-from { opacity: 1; max-height: 800px; transform: translateY(0); }

/* 学习讲解区 */
.task-learning-area { border-top: 1px solid rgba(255,255,255,.05); padding-top: 14px; }
.learn-loading { text-align: center; padding: 24px 0; }
.ai-gen-anim { display: flex; gap: 8px; justify-content: center; margin-bottom: 14px; }
.ai-dot { width: 10px; height: 10px; border-radius: 50%; background: #6c8cff; animation: ai-bounce 1.2s infinite ease-in-out; }
.ai-dot:nth-child(2) { animation-delay: .2s; background: #8b5cf6; }
.ai-dot:nth-child(3) { animation-delay: .4s; background: #10b981; }
@keyframes ai-bounce { 0%, 100% { transform: translateY(0); opacity: .5; } 50% { transform: translateY(-12px); opacity: 1; } }
.learn-loading p { font-size: 13px; color: #999; margin: 0; }
.learn-loading-sub { font-size: 11px !important; color: #666 !important; margin-top: 6px !important; animation: shimmer 2s infinite; }
@keyframes shimmer { 0%, 100% { opacity: .4; } 50% { opacity: 1; } }
.learn-error { text-align: center; padding: 16px 0; font-size: 13px; color: #ff6b6b; }
.learn-error a { color: #6c8cff; cursor: pointer; text-decoration: underline; }
.learn-content { display: flex; flex-direction: column; gap: 12px; animation: learn-fade-in .4s ease; }
@keyframes learn-fade-in { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
.learn-label { display: block; font-size: 12px; font-weight: 700; color: #8b5cf6; margin-bottom: 6px; }
.learn-summary p { font-size: 13px; color: #ccc; line-height: 1.6; margin: 0; }
.learn-block { background: rgba(255,255,255,.02); border-radius: 10px; padding: 12px 16px; }
.learn-block ul { margin: 0; padding-left: 18px; }
.learn-block li { font-size: 13px; color: #bbb; line-height: 1.7; }

/* 任务操作区 */
.task-actions { display: flex; gap: 10px; align-items: center; justify-content: flex-end; }
.btn-video { padding: 8px 16px; border-radius: 8px; border: 1px dashed rgba(255,255,255,.1); background: rgba(255,255,255,.02); color: #555; font-size: 12px; font-family: inherit; cursor: not-allowed; display: flex; align-items: center; gap: 6px; }
.video-soon { font-size: 10px; padding: 2px 6px; border-radius: 4px; background: rgba(255,255,255,.04); color: #666; }

/* 知识点卡片 */
.mastery-cards-row { display: flex; gap: 12px; flex-wrap: wrap; }
.mst-card { padding: 14px 18px; border-radius: 14px; color: #fff; text-align: center; min-width: 120px; flex: 1; transition: all .35s ease; position: relative; overflow: hidden; }
.mst-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(180deg, rgba(255,255,255,.12) 0%, transparent 100%); pointer-events: none; border-radius: 14px; }
.mst-card:hover { transform: translateY(-4px); }
.mst-card-topic { display: block; font-size: 12px; font-weight: 500; text-shadow: 0 1px 8px rgba(0,0,0,.15); position: relative; z-index: 1; }
.mst-card-score { display: block; font-size: 26px; font-weight: 700; margin: 4px 0; text-shadow: 0 1px 8px rgba(0,0,0,.15); position: relative; z-index: 1; }
.mst-card-btn { margin-top: 4px; padding: 4px 16px; border-radius: 8px; border: 1px solid rgba(255,255,255,.25); background: rgba(255,255,255,.08); color: #fff; font-size: 12px; cursor: pointer; transition: all .25s; font-family: inherit; position: relative; z-index: 1; }
.mst-card-btn:hover { background: rgba(255,255,255,.22); transform: translateY(-2px); }

/* 错题本 */
.mistake-grid { display: flex; flex-direction: column; gap: 8px; }
.mistake-card { padding: 14px 18px; border-color: rgba(239,68,68,.08); background: rgba(239,68,68,.02); }
.mistake-card:hover { border-color: rgba(239,68,68,.15); }
.mstk-stem { font-size: 13px; color: #cbd5e1; margin-bottom: 8px; line-height: 1.5; }
.mstk-answers { display: flex; gap: 16px; font-size: 12px; }
.mstk-wrong { color: #ef4444; }
.mstk-correct { color: #22c55e; }

	/* 诊断全屏页 */
	.diagnosis-page { max-width: 720px; margin: 0 auto; }
	.diag-topbar { display: flex; align-items: center; gap: 12px; margin-bottom: 28px; }
	.diag-panel-full { padding: 32px 36px; margin-bottom: 20px; }
	.diag-panel-full .diag-question-wrap { padding-top: 8px; }
.diag-progress-bar { height: 3px; border-radius: 2px; background: rgba(255,255,255,.05); margin-bottom: 20px; overflow: hidden; }
.diag-bar-fill { height: 100%; background: linear-gradient(90deg, #6c8cff, #8b5cf6); border-radius: 2px; transition: width .4s; }
.diag-header { display: flex; justify-content: space-between; font-size: 13px; color: #94a3b8; margin-bottom: 24px; }
.q-meta-row { display: flex; gap: 8px; align-items: center; margin-bottom: 16px; }
.q-type { font-size: 11px; color: #64748b; }
.q-idx { font-size: 11px; color: #475569; margin-left: auto; }
.q-stem { font-size: 16px; line-height: 1.8; margin-bottom: 24px; }
.q-options { display: flex; flex-direction: column; gap: 8px; margin-bottom: 24px; }
.opt-btn { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 10px; border: 1px solid rgba(255,255,255,.06); background: rgba(255,255,255,.02); color: #e2e8f0; text-align: left; cursor: pointer; font-size: 14px; font-family: inherit; transition: all .2s; backdrop-filter: blur(12px); }
.opt-btn:hover { border-color: rgba(108,140,255,.2); background: rgba(108,140,255,.04); transform: translateX(2px); }
.opt-btn.selected { border-color: #6c8cff; background: rgba(108,140,255,.1); }
.opt-letter { width: 24px; height: 24px; border-radius: 6px; background: rgba(255,255,255,.05); display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600; flex-shrink: 0; }
.opt-btn.selected .opt-letter { background: #6c8cff; }
.glass-input.textarea { resize: vertical; min-height: 80px; }
.q-nav { display: flex; align-items: center; justify-content: space-between; margin-top: 24px; }
.q-dots { display: flex; gap: 4px; }
.dot { width: 6px; height: 6px; border-radius: 50%; background: rgba(255,255,255,.06); transition: all .3s; }
.dot.done { background: #6c8cff; }
.dot.current { background: #e2e8f0; transform: scale(1.3); }
.multi-hint { font-size: 11px; color: #64748b; margin-top: 6px; }
.step-title { font-size: 18px; margin: 0 0 24px; }
.goal-form { display: flex; flex-direction: column; gap: 24px; margin-bottom: 28px; }
.goal-row label { display: flex; justify-content: space-between; font-size: 13px; color: #94a3b8; margin-bottom: 8px; }
.goal-val { color: #6c8cff; font-weight: 600; }
.glass-range { width: 100%; height: 4px; border-radius: 2px; background: rgba(255,255,255,.05); appearance: none; outline: none; cursor: pointer; }
.glass-range::-webkit-slider-thumb { appearance: none; width: 18px; height: 18px; border-radius: 50%; background: #6c8cff; cursor: pointer; box-shadow: 0 2px 8px rgba(108,140,255,.3); }
.range-labels { display: flex; justify-content: space-between; font-size: 10px; color: #475569; margin-top: 4px; }
.goal-actions { display: flex; gap: 10px; justify-content: flex-end; }
.btn-spinner { width: 14px; height: 14px; border: 2px solid rgba(255,255,255,.3); border-top-color: #fff; border-radius: 50%; animation: spin .6s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
