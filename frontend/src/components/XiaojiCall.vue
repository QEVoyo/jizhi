<template>
  <div class="xiaoji-call-page">
    <!-- ===== 顶部导航 ===== -->
    <div class="call-nav">
      <span class="nav-back-spacer"></span>
      <div class="nav-center">
        <div class="nav-avatar-wrapper">
          <img :src="avatarUrl" alt="小基" class="nav-avatar" />
        </div>
        <div>
          <div class="nav-name">{{ xiaojiName }}</div>
          <!-- 顶部状态 = 当前角色身份（2026-09-02 用户拍板：替代「在线」） -->
          <div class="nav-status" :style="{ color: modeMeta.color }">{{ callStatusLabel }}</div>
        </div>
      </div>
      <div class="nav-actions">
        <el-button
          text
          class="nav-action"
          @click="toggleChatMode"
          :title="chatMode === 'bubble' ? '切换到列表模式' : '切换到气泡模式'"
        >
          <i :class="chatMode === 'bubble' ? 'fas fa-comments' : 'fas fa-list-ul'"></i>
        </el-button>
        <el-button
          text
          class="nav-action"
          @click="toggleCleanMode"
          :title="cleanMode ? '退出纯净模式（显示两侧）' : '纯净模式（隐藏两侧）'"
        >
          <i :class="cleanMode ? 'fas fa-compress' : 'fas fa-expand'"></i>
        </el-button>
        <el-button text class="nav-action" @click="goSearch" title="搜索记录">
          <i class="fas fa-search"></i>
        </el-button>
        <el-button text class="nav-action" @click="clearHistory" title="清空记录">
          <i class="fas fa-trash-alt"></i>
        </el-button>
        <el-button text class="nav-action" @click="goSettings">
          <i class="fas fa-cog"></i>
        </el-button>
      </div>
    </div>

    <!-- ===== 边缘半椭圆中枢轮盘（2026-08-25：撤侧边栏，导航嵌入屏幕左缘；纯净模式隐藏，只留中间聊天区） ===== -->
    <EdgeNavDock v-show="!cleanMode" :hidden="cleanMode" />

    <div class="call-body" :class="{ clean: cleanMode }">

      <div class="call-main">
    <!-- ===== 小基形象 ===== -->
    <div class="xiaoji-area" :class="{ 'bubble-mode': chatMode === 'bubble' }">
      <div class="xiaoji-glow-ring"></div>
      <div class="xiaoji-glow-ring-2"></div>
      <div
        class="xiaoji-click-area"
        @click="onAvatarClick"
        @dblclick="onAvatarDoubleClick"
        @mouseenter="onAvatarHover(true)"
        @mouseleave="onAvatarHover(false)"
      >
        <div class="xiaoji-shadow"></div>
        <img :src="avatarUrl" alt="小基" class="xiaoji-image" :class="{ hover: isHover }" />
        <div class="xiaoji-status-area">
          <el-tag :type="statusTagType" size="default" effect="plain" class="status-tag">
            {{ statusText }}
          </el-tag>
          <!-- 真实阶段（2026-09-10）：文案由实际动作设置；进度百分比已知才显示进度条 -->
          <div v-if="isProcessing && stage" class="agent-progress">
            <el-progress
              v-if="stagePercent != null"
              :percentage="stagePercent"
              :stroke-width="3"
              :show-text="false"
              class="agent-progress-bar"
            />
            <div class="agent-info">
              <span class="agent-desc">{{ stage }}</span>
            </div>
          </div>
        </div>
        <!-- 小基气泡：列表模式 = 点击/问候短语定时弹出；气泡模式 = 最新回复常驻 -->
        <div
          v-if="dialogDisplayText"
          class="xiaoji-dialog"
          :style="showDialog ? dialogStyle : null"
          :class="{ pop: showDialog, persistent: !showDialog }"
        >
          <!-- 气泡署名（2026-08-27）：队员呼叫后，气泡里亮出是谁在回答 -->
          <div
            v-if="chatMode === 'bubble' && !showDialog && lastAssistantAgent"
            class="bubble-agent-badge"
            :style="{ '--fc': fellowMeta(lastAssistantAgent)?.color || '#888' }"
          >
            <img :src="fellowMeta(lastAssistantAgent)?.img" alt="" />
            <span>{{ fellowMeta(lastAssistantAgent)?.name }}</span>
          </div>
          {{ dialogDisplayText }}
          <div class="dialog-tail"></div>
        </div>
      </div>
      <!-- 气泡模式：我的最新一条 -->
      <div v-if="chatMode === 'bubble' && lastUserText" class="xiaoji-user-bubble">
        {{ lastUserText }}
      </div>
    </div>

    <!-- ===== 聊天区域（列表模式） ===== -->
    <div v-if="chatMode === 'list'" class="chat-area-wrapper">
      <div class="chat-cylinder-wrapper">
        <div class="chat-cylinder-glow"></div>
        <div class="chat-roll" ref="chatRollRef" @scroll="onScroll">
          <div v-if="loading" class="roll-loading">
            <i class="fas fa-spinner fa-spin"></i>
            <span>加载中...</span>
          </div>
          <div v-else-if="!messages.length" class="roll-empty">
            <span>💬 开始和小基聊天吧</span>
          </div>
          <div v-else class="roll-messages">
            <!-- 分页加载指示（可点击，滚动到顶也会自动触发） -->
            <div v-if="loadingMore" class="roll-load-more"><i class="fas fa-spinner fa-spin"></i> 加载更早消息...</div>
            <div v-else-if="hasMoreMessages" class="roll-load-more clickable" @click="loadMoreMessages">↑ 加载更早消息</div>
            <template v-for="(msg, index) in messages" :key="index">
              <!-- 日期分隔线 -->
              <div v-if="showDateDivider(index)" class="roll-date-divider">{{ formatDate(msg.created_at) }}</div>
              <div
                class="roll-item"
                :data-msg-id="msg.id"
                :class="{
                  user: msg.role === 'user',
                  assistant: msg.role === 'assistant',
                  isQuestion: msg.is_question,
                  isSet: msg.is_set,
                  isEvaluation: msg.is_evaluation,
                  highlight: msg.id && msg.id === highlightId
                }"
              >
              <div class="roll-avatar">
                <img
                  v-if="msg.role === 'user'"
                  :src="authStore.user?.avatar_url || '/default-avatar.png'"
                  class="user-avatar-img"
                />
                <img v-else :src="avatarUrl" class="xiaoji-avatar-img" />
              </div>
              <div class="roll-content">
                <!-- 队员署名徽章（2026-08-27）：是谁的产出，一眼可见 -->
                <div v-if="msg.agent" class="agent-badge" :style="{ '--fc': fellowMeta(msg.agent)?.color || '#888' }">
                  <img :src="fellowMeta(msg.agent)?.img" alt="" class="agent-badge-img" />
                  <span class="agent-badge-name">{{ fellowMeta(msg.agent)?.name || '智能体' }}</span>
                  <span class="agent-badge-tag">{{ fellowMeta(msg.agent)?.tagline || '' }}</span>
                </div>

                <!-- ===== 图片显示 ===== -->
                <div v-if="msg.image_url" class="message-image" @click="previewImage(msg.image_url)">
                  <img :src="msg.image_url" alt="图片" />
                </div>

                <!-- 题目卡片 -->
                <div v-if="msg.is_question" class="message-card question-card" @click="previewQuestion(msg.questionData)">
                  <div class="card-header">
                    <span class="card-icon">📝</span>
                    <span class="card-title">{{ msg.questionData?.title || '题目' }}</span>
                    <span class="card-badge">{{ getTypeName(msg.questionData?.question_type) }}</span>
                    <span class="card-difficulty-badge">难度 {{ msg.questionData?.difficulty_score || 5 }}</span>
                  </div>
                  <div class="card-body">
                    <div class="card-question">{{ msg.questionData?.question_content || msg.questionData?.title }}</div>
                    <div v-if="msg.questionData?.question_type === 'choice' && msg.questionData?.options" class="card-options">
                      <div v-for="(val, key) in msg.questionData.options" :key="key" class="card-option">
                        {{ key }}. {{ val }}
                      </div>
                    </div>
                  </div>
                  <div class="card-footer">
                    <span class="card-hint">点击卡片查看详情</span>
                    <span class="card-actions" @click.stop>
                      <button class="card-act" @click="saveToResourceLib(msg.questionData)">
                        <i class="fas fa-box-archive"></i> 存到资源库
                      </button>
                      <button class="card-act" @click="toggleBankSearch(String(index), msg.questionData)">
                        <i class="fas fa-search"></i> 题库检索
                      </button>
                    </span>
                  </div>
                  <!-- 选题依据（2026-09-02 生成 Agent 真实出题：薄弱点/错题定向，让用户知道为什么出这道） -->
                  <div v-if="msg.picked_from" class="picked-note">🎯 {{ msg.picked_from }}</div>
                  <!-- 题库检索结果（同类题折叠列表，2026-08-27） -->
                  <div v-if="bankMatch[String(index)]" class="bank-match" @click.stop>
                    <div v-if="bankMatch[String(index)].loading" class="bank-match-tip"><i class="fas fa-spinner fa-spin"></i> 检索题库中...</div>
                    <template v-else>
                      <div v-if="!bankMatch[String(index)].items.length" class="bank-match-tip">题库里没找到同类题</div>
                      <div
                        v-for="m in bankMatch[String(index)].items"
                        :key="m.id"
                        class="bank-match-item"
                        title="点击发给小基评价"
                        @click="evaluateBankQuestion(m)"
                      >
                        <span class="bm-badge">{{ m.syllabus_name || '题库' }}</span>
                        <span class="bm-title">{{ (m.question_content || m.title || '').slice(0, 46) }}</span>
                        <span class="bm-type">{{ getTypeName(m.question_type) }} · 难度{{ m.difficulty_score ?? 5 }}</span>
                      </div>
                    </template>
                  </div>
                </div>

                <!-- 题集卡片 -->
                <div v-else-if="msg.is_set" class="message-card set-card" @click="previewSet(msg.setData)">
                  <div class="card-header">
                    <span class="card-icon">📚</span>
                    <span class="card-title">{{ msg.setData?.name || '题集' }}</span>
                    <span class="card-badge">{{ msg.setData?.question_ids?.length || 0 }} 道题</span>
                  </div>
                  <div class="card-body">
                    <span class="card-preview">{{ msg.setData?.description || '点击查看题集详情' }}</span>
                  </div>
                  <div class="card-footer">
                    <span class="card-hint">点击查看题集详情</span>
                  </div>
                </div>

                <!-- 计划卡（2026-09-10 自动分流：规划不再只输出一大段话，而是可执行的计划） -->
                <div v-else-if="msg.is_plan_card" class="message-card plan-card" @click.stop>
                  <div class="card-header">
                    <span class="card-icon">📋</span>
                    <span class="card-title">{{ msg.planCard.goal || '学习计划' }}</span>
                    <span class="card-badge">{{ msg.planCard.days }} 天</span>
                  </div>
                  <div class="card-body">
                    <div class="plan-fields">
                      <input v-model="msg.planCard.goal" class="pf-input grow" :disabled="!!msg.planCard.draft" placeholder="想学什么（如：四级核心词汇）" />
                      <input v-model.number="msg.planCard.days" type="number" class="pf-input num" :disabled="!!msg.planCard.draft" min="3" max="180" />
                      <span class="pf-unit">天</span>
                      <input v-model.number="msg.planCard.minutes" type="number" class="pf-input num" :disabled="!!msg.planCard.draft" min="5" max="240" />
                      <span class="pf-unit">分/天</span>
                    </div>
                    <div v-if="msg.planCard.loading" class="plan-tip"><i class="fas fa-spinner fa-spin"></i> 正在排计划…</div>
                    <div v-else-if="msg.planCard.error" class="plan-tip err">生成失败，可以再试一次</div>
                    <template v-else-if="msg.planCard.draft">
                      <div v-for="d in msg.planCard.draft.slice(0, 4)" :key="d.day" class="plan-day">
                        <span class="pd-day">D{{ d.day || 1 }}</span>
                        <span class="pd-topic">{{ d.topic }}</span>
                      </div>
                      <div v-if="msg.planCard.draft.length > 4" class="plan-tip">…共 {{ msg.planCard.draft.length }} 天</div>
                    </template>
                  </div>
                  <div class="card-footer">
                    <span class="card-hint">{{ msg.planCard.draft ? '确认后就能开始执行' : '填好点生成，我来排' }}</span>
                    <span class="card-actions">
                      <button v-if="!msg.planCard.draft" class="card-act" :disabled="msg.planCard.loading" @click="runPlanDraft(msg.planCard)">
                        <i class="fas fa-wand-magic-sparkles"></i> 生成计划
                      </button>
                      <button v-else class="card-act" :disabled="msg.planCard.creating" @click="confirmPlanDraft(msg.planCard)">
                        <i class="fas fa-play"></i> 开始执行
                      </button>
                    </span>
                  </div>
                </div>

                <!-- 评估卡（2026-09-10 自动分流：识别到评估意图 → 直接出结论） -->
                <div v-else-if="msg.is_eval_card" class="message-card eval-card" @click.stop>
                  <div class="card-header">
                    <span class="card-icon">📊</span>
                    <span class="card-title">学习评估</span>
                    <span v-if="msg.evalCard.data?.rating" class="card-badge">{{ msg.evalCard.data.rating }}</span>
                  </div>
                  <div class="card-body">
                    <div v-if="msg.evalCard.loading" class="plan-tip"><i class="fas fa-spinner fa-spin"></i> 正在分析你的学习数据…</div>
                    <div v-else-if="msg.evalCard.error" class="plan-tip err">分析失败，稍后再试一次</div>
                    <template v-else-if="msg.evalCard.data">
                      <div v-if="msg.evalCard.data.summary" class="ev-summary">{{ msg.evalCard.data.summary }}</div>
                      <div v-if="msg.evalCard.data.core_issue" class="ev-row"><span class="ev-k">核心问题</span><span>{{ msg.evalCard.data.core_issue }}</span></div>
                      <div v-if="msg.evalCard.data.cause" class="ev-row"><span class="ev-k">归因</span><span>{{ msg.evalCard.data.cause }}</span></div>
                      <div v-if="msg.evalCard.data.advice_actions?.length" class="ev-actions">
                        <div v-for="(a, i) in msg.evalCard.data.advice_actions" :key="i" class="ev-act">
                          <span class="ev-i">{{ i + 1 }}</span>{{ a }}
                        </div>
                      </div>
                    </template>
                  </div>
                  <div class="card-footer">
                    <span class="card-hint">数据来自你近 30 天的真实学习记录</span>
                    <span class="card-actions">
                      <button class="card-act" @click="router.push('/evaluation-center')">
                        <i class="fas fa-arrow-right"></i> 去评估中心
                      </button>
                    </span>
                  </div>
                </div>

                <!-- 评价结果 -->
                <div v-else-if="msg.is_evaluation" class="evaluation-content">
                  <div class="eval-badge">📊 小基评价</div>
                  <div class="eval-text" v-html="formatEvalText(msg.content)"></div>
                </div>

                <!-- 普通文本（代码围栏切成代码卡，带沙箱运行，2026-08-27） -->
                <template v-else>
                  <template v-for="(seg, si) in segmentsOf(msg.content)" :key="si">
                    <span v-if="seg.type === 'text'" class="msg-text-seg">{{ seg.text }}</span>
                    <div v-else class="code-card">
                      <div class="code-card-head">
                        <span class="code-lang"><i class="fas fa-code"></i> {{ langLabel(seg.lang) }}</span>
                        <button
                          v-if="isRunnable(seg.lang)"
                          class="code-run-btn"
                          :disabled="codeRun[`${index}-${si}`]?.running"
                          @click="runMsgCode(`${index}-${si}`, seg.code, seg.lang)"
                        >
                          <i class="fas" :class="codeRun[`${index}-${si}`]?.running ? 'fa-spinner fa-spin' : 'fa-play'"></i>
                          {{ codeRun[`${index}-${si}`]?.running ? '运行中...' : '沙箱运行' }}
                        </button>
                      </div>
                      <pre class="code-block">{{ seg.code }}</pre>
                      <div v-if="codeRun[`${index}-${si}`] && !codeRun[`${index}-${si}`].running" class="code-run-box">
                        <div class="code-run-input-row">
                          <input
                            v-model="codeRun[`${index}-${si}`].input"
                            class="code-run-input"
                            placeholder="标准输入（可选，回车再跑一次）"
                            @keyup.enter="runMsgCode(`${index}-${si}`, seg.code, seg.lang)"
                          />
                          <button class="code-act" @click="runMsgCode(`${index}-${si}`, seg.code, seg.lang)">再次运行</button>
                        </div>
                        <pre class="code-run-output">{{ codeRun[`${index}-${si}`].output }}</pre>
                      </div>
                    </div>
                  </template>
                </template>

                <!-- 队员行动条（2026-09-02）：计划/评估 Agent 的回复带真实跳转入口 -->
                <div v-if="msg.agent === 'plan'" class="agent-actions">
                  <router-link to="/learning-plan">📋 查看我的学习计划</router-link>
                </div>
                <div v-else-if="msg.agent === 'evaluate'" class="agent-actions">
                  <router-link to="/evaluation-center">📊 查看评估报告</router-link>
                </div>
              </div>
              <span class="roll-time">{{ formatTime(msg.created_at) }}</span>
              </div>
            </template>

            <!-- 正在输入 -->
            <div v-if="sending" class="roll-item assistant">
              <div class="roll-avatar">
                <img :src="avatarUrl" class="xiaoji-avatar-img" />
              </div>
              <div class="roll-content">
                <span class="typing-dots-inline">
                  <span></span><span></span><span></span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 输入框 ===== -->
    <div class="call-input-area">
      <!-- 工具行：自动判别状态 + 功能按键同一行（2026-09-10 起不再手动选角色） -->
      <div class="input-tools">
        <span
          class="mode-chip"
          :class="{ 'is-active': liveRoute.intent !== 'chat' }"
          :style="{ '--mc': modeMeta.color }"
          :title="liveRoute.intent === 'chat' ? '说「帮我出几道题 / 做个计划 / 看看我学得怎么样」可以直达对应模式' : `识别到「${modeMeta.label}」，发送后直接出卡片`"
        >
          <i class="fas" :class="modeMeta.icon"></i>
          <span class="mc-text">{{ liveRoute.intent === 'chat' ? '自动识别' : modeMeta.label }}</span>
        </span>
        <button class="tool-btn" @click="triggerImageUpload" title="上传图片">
          <i class="fas fa-image"></i>
        </button>
        <button class="tool-btn" :class="{ active: videoFrames.length }" @click="triggerVideoUpload" title="分析视频（本地抽帧识图）">
          <i class="fas fa-video"></i>
        </button>
        <button class="tool-btn" @click="openSendQuestion" title="发送题目">
          <i class="fas fa-paper-plane"></i>
        </button>
        <button class="tool-btn" :class="{ active: isRecording, recording: isRecording }" @click="toggleRecording" :title="isRecording ? '结束录音' : '语音输入'">
          <i :class="isRecording ? 'fas fa-stop' : 'fas fa-microphone'"></i>
        </button>
        <button class="tool-btn" @click="goVoiceCall" title="语音通话（实时语音对话）">
          <i class="fas fa-phone"></i>
        </button>
        <button class="tool-btn" @click="toggleVoice" :class="{ active: voiceEnabled }" title="语音播报开关">
          <i :class="voiceEnabled ? 'fas fa-volume-up' : 'fas fa-volume-mute'"></i>
        </button>
        <button v-if="isSpeaking" class="tool-btn stop-reading" @click="stopReading" title="停止朗读">
          <i class="fas fa-circle-stop"></i>
        </button>
        <span v-for="q in quickQuestions" :key="q" class="quick-chip" @click="quickAsk(q)">{{ q }}</span>
      </div>
      <input ref="fileInputRef" type="file" accept="image/*" style="display:none" @change="handleImageSelect" />
      <input ref="videoInputRef" type="file" accept="video/*" style="display:none" @change="handleVideoSelect" />

      <!-- 词条卡（问词义 / 识图提词，2026-08-25 从 ChatArea 移植） -->
      <div v-if="vocabCards.length" class="vocab-cards">
        <VocabCard
          v-for="c in vocabCards"
          :key="c.word"
          :word="c.word"
          :user-id="authStore.user?.id"
          :touchpoint="c.touchpoint"
          @close="vocabCards = vocabCards.filter(x => x.word !== c.word)"
        />
      </div>

      <div class="input-row">
        <el-input
          v-model="inputText"
          :placeholder="inputPlaceholder"
          size="large"
          @keyup.enter="sendMessage()"
          class="chat-input"
        >
          <template #append>
            <el-button :loading="sending" @click="sendMessage">
              <i class="fas fa-paper-plane"></i>
            </el-button>
          </template>
        </el-input>
      </div>

      <div v-if="uploadedImage" class="image-preview">
        <img :src="uploadedImage" alt="待发送图片" />
        <button class="remove-image" @click="removeImage">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <div v-if="videoFrames.length" class="image-preview video-preview">
        <span class="video-preview-tag">
          <i class="fas fa-video"></i> {{ videoFileName }} · {{ videoFrames.length }} 帧已就绪
        </span>
        <button class="remove-image" @click="removeVideo">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </div>
      </div><!-- /call-main -->

      <!-- ===== 右侧栏：问候 + 推荐 + 关心 + 使用日志 + 寄语（2026-08-26 玻璃卡片分区改版） ===== -->
      <aside class="call-side side-right">
        <!-- 问候头（小基头像 + 时段问候） -->
        <div class="side-greeting">
          <img :src="avatarUrl" alt="小基" class="side-greeting-avatar" />
          <div class="side-greeting-text">
            <div class="side-greeting-title">{{ greetingText() }}<span class="side-greeting-name">，{{ authStore.user?.nickname || '同学' }}</span></div>
            <div class="side-greeting-sub">{{ greetingSub() }}</div>
          </div>
        </div>

        <!-- 小基推荐 -->
        <section class="side-card">
          <div class="side-card-head"><span class="side-card-ic amber"><i class="fas fa-lightbulb"></i></span>小基推荐</div>
          <div v-if="daily.recommendation" class="rec-card">
            <div class="rec-title">{{ daily.recommendation.title }}</div>
            <div class="rec-content">{{ daily.recommendation.content }}</div>
            <el-button size="small" type="primary" @click="goRecLink">
              {{ daily.recommendation.action_label || '立即学习' }}
            </el-button>
          </div>
          <div v-else class="rec-empty">
            <span>今天还没有学习推荐～<br />去做几道题，小基明天给你定制</span>
          </div>
          </section>

        <!-- 小基关心 -->
        <section class="side-card">
          <div class="side-card-head"><span class="side-card-ic violet"><i class="fas fa-heart"></i></span>小基关心</div>
          <div class="care-grid">
            <div class="care-item c-violet">
              <strong>{{ daily.stats.study_days_7d }}</strong>
              <span>近7天学习(天)</span>
            </div>
            <div class="care-item c-blue">
              <strong>{{ daily.stats.week_questions }}</strong>
              <span>本周做题</span>
            </div>
            <div class="care-item c-green">
              <strong>{{ daily.stats.vocab_mastered }}</strong>
              <span>已掌握词条</span>
            </div>
            <div class="care-item c-amber">
              <strong>{{ daily.stats.vocab_weak }}</strong>
              <span>薄弱词条</span>
            </div>
          </div>
        </section>

        <!-- 使用日志 -->
        <section class="side-card log-card">
          <div class="side-card-head"><span class="side-card-ic cyan"><i class="fas fa-history"></i></span>使用日志</div>
          <!-- 摘要单行（2026-08-26 压缩：4 格磁贴改单行文字，省 ~38px 高度） -->
          <div class="log-summary">
            <span class="ls-item"><strong>{{ daily.logs?.call_count || 0 }}</strong> 通话</span>
            <i class="ls-dot">·</i>
            <span class="ls-item"><strong>{{ fmtMinutes(daily.logs?.call_total_seconds || 0) }}</strong></span>
            <i class="ls-dot">·</i>
            <span class="ls-item"><strong>{{ daily.logs?.chat_count || 0 }}</strong> 聊天</span>
            <i class="ls-dot">·</i>
            <span class="ls-item"><strong>{{ daily.logs?.tool_usage_7d || 0 }}</strong> 工具</span>
          </div>
          <!-- 通话记录：只有它会一直增加，单独内部滚动（2026-08-26 用户定稿） -->
          <div class="call-history">
            <div v-for="c in (daily.logs?.recent_calls || [])" :key="c.id" class="call-row">
              <i class="fas fa-phone-alt"></i>
              <span class="call-time">{{ fmtCallTime(c.started_at) }}</span>
              <span class="call-dur">{{ fmtMinutes(c.duration_seconds) }} · {{ c.turns }} 轮</span>
            </div>
            <div v-if="!daily.logs || daily.logs.call_count === 0" class="call-empty">
              还没有通话记录，点输入框的 <i class="fas fa-phone"></i> 试试～
            </div>
          </div>
          <!-- 时段分布：固定不滚，永远可见 -->
          <div class="time-buckets">
            <div v-for="b in (daily.logs?.time_buckets || [])" :key="b.label" class="bucket-row">
              <span class="bucket-label">{{ b.label }}</span>
              <div class="bucket-bar"><div class="bucket-fill" :style="{ width: Math.max(b.pct, b.value > 0 ? 6 : 0) + '%' }"></div></div>
              <span class="bucket-num">{{ b.value }}</span>
            </div>
          </div>
        </section>

        <!-- 每日寄语（小基气泡） -->
        <div class="side-quote">
          <img :src="avatarUrl" alt="小基" class="quote-avatar" />
          <div class="quote-bubble">
            「{{ dailyQuote }}」
            <div class="quote-by">—— 小基</div>
          </div>
        </div>
      </aside>
    </div><!-- /call-body -->

    <!-- ===== 自定义出题弹窗（2026-08-27：聊天内出题卡——自己填需求，生成 Agent 生成后回聊） ===== -->
    <el-dialog
      v-model="showGenDialog"
      title="✍️ 自定义出题 · 生成 Agent"
      width="480px"
      destroy-on-close
      class="custom-glass-dialog"
    >
      <div class="gen-form">
        <div class="gen-row">
          <label>题型</label>
          <el-select v-model="genForm.qtype" size="small" style="flex:1">
            <el-option v-for="t in genTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </div>
        <div class="gen-row">
          <label>学科</label>
          <el-select v-model="genForm.category" size="small" style="flex:1" placeholder="通用（自动判定学科）">
            <el-option v-for="c in genCategories" :key="c" :label="c === '通用' ? '通用（自动判定）' : c" :value="c" />
          </el-select>
        </div>
        <div class="gen-row">
          <label>知识点</label>
          <el-input v-model="genForm.knowledge" size="small" placeholder="如：定语从句 / 极限与连续" style="flex:1" @keyup.enter="submitGenForm" />
        </div>
        <div class="gen-row">
          <label>难度</label>
          <el-select v-model="genForm.difficulty" size="small" style="flex:1">
            <el-option v-for="t in genDifficulties" :key="t" :label="t" :value="t" />
          </el-select>
        </div>
        <div class="gen-row">
          <label>数量</label>
          <el-select v-model="genForm.count" size="small" style="flex:1">
            <el-option v-for="n in [1, 2, 3]" :key="n" :label="`${n} 道`" :value="n" />
          </el-select>
        </div>
        <div class="gen-actions">
          <el-button size="small" @click="showGenDialog = false">取消</el-button>
          <el-button size="small" type="primary" :loading="genLoading" @click="submitGenForm">
            生成 → AI 判定
          </el-button>
        </div>
      </div>
    </el-dialog>

    <!-- ===== 发送题目弹窗 ===== -->
    <el-dialog
      v-model="showQuestionDialog"
      title="📤 发送给小基"
      width="640px"
      destroy-on-close
      class="custom-glass-dialog"
    >
      <div class="question-dialog">
        <el-tabs v-model="questionTab" class="custom-glass-tabs">
          <!-- ===== 题库（学科计划 19,000+ 题，模糊搜索） ===== -->
          <el-tab-pane label="题库" name="bank">
            <div class="bank-search-row">
              <el-select
                v-model="bankSyllabus"
                size="small"
                style="width: 170px"
                placeholder="全部考纲"
                clearable
                @change="doBankSearch"
              >
                <el-option
                  v-for="(name, id) in bankSyllabusNames"
                  :key="id"
                  :label="name"
                  :value="id"
                />
              </el-select>
              <el-input
                v-model="bankKeyword"
                size="small"
                placeholder="模糊搜索题目：知识点 / 题干关键词 / 标题"
                clearable
                @input="onBankSearchInput"
                class="bank-search-input"
              >
                <template #prefix><i class="fas fa-search"></i></template>
              </el-input>
            </div>
            <div v-loading="bankSearching" class="bank-results">
              <div v-if="!bankKeyword.trim()" class="empty-tip">
                输入关键词模糊搜索题库（如「细胞」「函数」「四级词汇」），或先选考纲再搜
              </div>
              <div v-else-if="!bankResults.length" class="empty-tip">
                没有找到相关题目，换个关键词试试
              </div>
              <div
                v-for="q in bankResults"
                :key="q.id"
                class="question-item"
                @click="sendBankQuestion(q)"
              >
                <div class="q-main">
                  <span class="q-title">{{ bankQuestionTitle(q) }}</span>
                  <span class="q-meta">
                    {{ q.syllabus_name }} · {{ getTypeName(q.question_type) }} · 难度 {{ q.difficulty || q.difficulty_score || 5 }}
                  </span>
                </div>
                <el-button size="small" type="primary">发送</el-button>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="生成历史" name="history">
            <div v-if="historyQuestions.length === 0" class="empty-tip">
              暂无生成历史
            </div>
            <div
              v-for="q in historyQuestions"
              :key="q.id"
              class="question-item"
              @click="sendSingleQuestion(q)"
            >
              <span class="q-title">{{ q.title || q.question_content || '未命名题目' }}</span>
              <span class="q-type">{{ getTypeName(q.question_type) }}</span>
              <el-button size="small" type="primary">发送</el-button>
            </div>
          </el-tab-pane>

          <el-tab-pane label="题集" name="sets">
            <div v-if="questionSets.length === 0" class="empty-tip">
              暂无题集
            </div>
            <div
              v-for="s in questionSets"
              :key="s.id"
              class="set-item-wrapper"
            >
              <div class="set-item" @click="toggleSetExpand(s.id)">
                <div class="set-info">
                  <span class="set-name">{{ s.name }}</span>
                  <span class="set-count">{{ s.question_ids?.length || 0 }} 道题</span>
                  <el-icon :class="{ expanded: expandedSetId === s.id }" class="set-expand-icon">
                    <i class="fas fa-chevron-down"></i>
                  </el-icon>
                </div>
              </div>
              <div v-if="expandedSetId === s.id" class="set-questions-list">
                <div v-if="setQuestionsMap[s.id] === null" class="loading-tip">
                  <i class="fas fa-spinner fa-spin"></i> 加载中...
                </div>
                <div v-else-if="setQuestionsMap[s.id]?.length === 0" class="empty-tip">
                  该题集暂无题目
                </div>
                <div
                  v-for="q in setQuestionsMap[s.id] || []"
                  :key="q.id"
                  class="set-question-item"
                  @click="sendSingleQuestion(q)"
                >
                  <div class="sq-info">
                    <span class="sq-title">{{ q.title || q.question_content || '未命名题目' }}</span>
                    <span v-if="q.question_content && q.question_content !== q.title" class="sq-preview">
                      {{ q.question_content.slice(0, 40) }}{{ q.question_content.length > 40 ? '...' : '' }}
                    </span>
                  </div>
                  <span class="sq-type">{{ getTypeName(q.question_type) }}</span>
                  <el-button size="small" type="primary">发送</el-button>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>

    <!-- ===== 预览弹窗 ===== -->
    <el-dialog
      v-model="showPreviewDialog"
      :title="previewTitle"
      width="600px"
      destroy-on-close
      class="custom-glass-dialog"
    >
      <div class="preview-content">
        <div v-if="previewType === 'question'">
          <div class="preview-question">
            <h4>{{ previewData?.title }}</h4>
            <p><strong>题型：</strong>{{ getTypeName(previewData?.question_type) }}</p>
            <p><strong>难度：</strong>{{ previewData?.difficulty_score || 5 }}</p>
            <p><strong>内容：</strong>{{ previewData?.question_content || previewData?.title }}</p>

            <div v-if="previewData?.question_type === 'choice' && previewData?.options">
              <p><strong>选项：</strong></p>
              <div v-for="(val, key) in previewData.options" :key="key" class="option-item">
                {{ key }}. {{ val }}
              </div>
            </div>

            <div v-if="(previewData?.question_type === 'coding' || previewData?.question_type === 'programming') && previewData?.starter_code">
              <p><strong>代码模板：</strong></p>
              <pre class="code-block">{{ previewData.starter_code }}</pre>
            </div>
          </div>
        </div>
        <div v-else-if="previewType === 'set'">
          <div class="preview-set">
            <p><strong>题集名称：</strong>{{ previewData?.name }}</p>
            <p><strong>描述：</strong>{{ previewData?.description || '无描述' }}</p>
            <p><strong>题目数量：</strong>{{ previewData?.question_ids?.length || 0 }}</p>
            <div v-if="previewQuestions.length > 0" class="set-questions-list">
              <p><strong>包含题目：</strong></p>
              <div v-for="(q, idx) in previewQuestions" :key="idx" class="set-question-item">
                <span class="sq-index">{{ idx + 1 }}.</span>
                <span class="sq-title">{{ q.title || q.question_content || '未命名题目' }}</span>
                <span class="sq-type">{{ getTypeName(q.question_type) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- ===== 图片预览 ===== -->
    <el-dialog v-model="imagePreviewVisible" width="80%" class="image-preview-dialog" destroy-on-close>
      <img :src="previewImageUrl" alt="预览" class="preview-image" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, nextTick, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getXiaojiMessages,
  xiaojiVision,
  xiaojiVideoAnalyze,
  clearXiaojiMessages,
  evaluateQuestion,
  evaluateSet,
  getXiaojiConfig,
  updateXiaojiConfig,
  xiaojiTts,
  getXiaojiDaily,
  agentGenerate,
  routeIntent
} from '@/api/xiaoji'
import { getGenerationHistory, getQuestionSets, getQuestionDetail, generateQuestion, saveGenerationHistory } from '@/api/questions'
import { searchBankQuestions as searchBankQuestionsApi, runCode } from '@/api/subjectPlan'
import { recordAction } from '@/api/career'
import { createPlan } from '@/api/learningPlan'
import { agents as agentMetaList } from '@/utils/mockAgents'
import VocabCard from '@/components/VocabCard.vue'
import EdgeNavDock from '@/components/EdgeNavDock.vue'
import { useXiaojiAvatar } from '@/composables/useXiaojiAvatar'
import { BACKEND_URL } from '@/utils/constants'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const {
  avatarUrl,
  statusText,
  statusTagType,
  stage,
  stagePercent,
  isProcessing,
  setThinking,
  setStage,
  setSpeaking,
  setHappy,
  setIdle,
  setSleeping
} = useXiaojiAvatar()

// ===== 状态 =====
const messages = ref([])
const inputText = ref('')
const sending = ref(false)
const loading = ref(false)
const voiceEnabled = ref(true)

// ===== 小基配置（语音/问候，来自设置页） =====
const voiceConfig = ref({
  name: '小基',
  voice_enabled: true,
  voice_speed: 5,
  voice_volume: 5,
  voice_name: 'longanqian',
  proactive_enabled: true
})

// 自定义名称（设置页可改，页面标题与聊天人设同步使用）
const xiaojiName = computed(() => voiceConfig.value.name || '小基')

let voiceConfigLoaded = false
async function loadVoiceConfig() {
  try {
    const data = await getXiaojiConfig(authStore.user.id)
    if (data) {
      voiceConfig.value = { ...voiceConfig.value, ...data }
      voiceEnabled.value = data.voice_enabled !== false
    }
  } catch { /* 用默认值 */ }
  voiceConfigLoaded = true
}

// ===== 搜索跳转高亮 =====
const highlightId = ref('')
const chatRollRef = ref(null)

// ===== 显示模式：气泡为主 / 列表为主（2026-08-25 分解两种展示方式，按用户记忆） =====
const chatMode = ref('bubble')
try {
  chatMode.value = localStorage.getItem(`xiaoji_chat_mode_${authStore.user?.id || 'guest'}`) || 'bubble'
} catch {}
function toggleChatMode() {
  chatMode.value = chatMode.value === 'bubble' ? 'list' : 'bubble'
  try { localStorage.setItem(`xiaoji_chat_mode_${authStore.user?.id || 'guest'}`, chatMode.value) } catch {}
  if (chatMode.value === 'list') {
    nextTick(() => {
      forceScrollToBottom(true)
      setTimeout(updateScale, 50)
    })
  } else {
    ElMessage.info('气泡模式：最新对话显示在小基头像旁')
  }
}

// ===== 纯净模式（2026-08-25，08-26 修订）：隐藏左侧轮盘 + 右侧栏，只留中间聊天区，顶部按钮切换 =====
const cleanMode = ref(false)
try {
  cleanMode.value = localStorage.getItem(`xiaoji_clean_mode_${authStore.user?.id || 'guest'}`) === '1'
} catch {}
function toggleCleanMode() {
  cleanMode.value = !cleanMode.value
  try { localStorage.setItem(`xiaoji_clean_mode_${authStore.user?.id || 'guest'}`, cleanMode.value ? '1' : '0') } catch {}
  ElMessage.info(cleanMode.value ? '纯净模式：两侧已隐藏' : '已退出纯净模式')
}
const greetingBubble = ref('')
const lastUserText = computed(() => {
  for (let i = messages.value.length - 1; i >= 0; i--) {
    if (messages.value[i].role === 'user') return messages.value[i].content
  }
  return ''
})
const lastAssistantText = computed(() => {
  for (let i = messages.value.length - 1; i >= 0; i--) {
    if (messages.value[i].role === 'assistant') return messages.value[i].content
  }
  return ''
})
// 气泡模式常驻内容：最新一条小基回复（无回复时显示问候语）
const assistantBubbleText = computed(() => lastAssistantText.value || greetingBubble.value)
// 最新一条助手消息的署名智能体（队友栏呼叫后，气泡里亮徽章）
const lastAssistantAgent = computed(() => {
  for (let i = messages.value.length - 1; i >= 0; i--) {
    if (messages.value[i].role === 'assistant' && messages.value[i].agent) return messages.value[i].agent
  }
  return null
})
const dialogDisplayText = computed(() => {
  if (showDialog.value) return dialogText.value       // 定时弹出（点击/悬停短语）优先
  if (chatMode.value === 'bubble') return assistantBubbleText.value
  return ''                                           // 列表模式：回复只看列表
})

// ===== 左右侧栏：每日推荐 + 小基关心（2026-08-25 新增，两种模式都显示） =====
const daily = ref({
  recommendation: null,
  stats: { study_days_7d: 0, week_questions: 0, vocab_total: 0, vocab_mastered: 0, vocab_weak: 0 },
  logs: { call_count: 0, call_total_seconds: 0, recent_calls: [], time_buckets: [], chat_count: 0 }
})

// 时长格式化：<60s 显示秒，否则 X 分 Y 秒
function fmtMinutes(seconds) {
  const s = Math.max(0, Math.round(seconds || 0))
  if (s < 60) return `${s}秒`
  const m = Math.floor(s / 60)
  return `${m}分${s % 60}秒`
}

// 通话时间：今天显示 HH:mm，其他显示 M月D日 HH:mm
function fmtCallTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  const now = new Date()
  const hm = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  const sameDay = d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth() && d.getDate() === now.getDate()
  return sameDay ? `今天 ${hm}` : `${d.getMonth() + 1}月${d.getDate()}日 ${hm}`
}
const quickQuestions = ['背个单词', '求安慰']   // 陪伴类快捷提问

// ===== 意图自动判别（2026-09-10：删掉手动「呼叫对象」下拉框，改为按用户说的内容自动分流）
// 浅层判别（只跑规则层，零成本零延迟）在输入时实时跑，用于状态提示与按键联动；
// 权威判别在后端同一个请求里做——chat-stream 判出「派活」时直接回路由指令，省一次往返。
const MODE_META = {
  chat:     { label: '陪聊', color: '#5b8def', icon: 'fa-comment-dots' },
  generate: { label: '出题', color: '#e8842c', icon: 'fa-pen-field' },
  plan:     { label: '规划', color: '#4d8dff', icon: 'fa-calendar-check' },
  evaluate: { label: '评估', color: '#26d0ce', icon: 'fa-chart-simple' },
}
const liveRoute = ref({ intent: 'chat', matched: '', hit: '' })
const modeMeta = computed(() => MODE_META[liveRoute.value.intent] || MODE_META.chat)
// 顶部状态：默认「队长 · 陪聊」，识别到派活时如实显示识别结果
const callStatusLabel = computed(() => {
  const it = liveRoute.value.intent
  return it === 'chat' ? '队长 · 陪聊' : `已识别 · ${MODE_META[it].label}`
})

let routeProbeTimer = null
/** 输入时浅层预判：只走规则层，不花模型钱（判别失败静默，不影响输入） */
function probeRoute() {
  clearTimeout(routeProbeTimer)
  routeProbeTimer = setTimeout(async () => {
    const text = inputText.value.trim()
    if (text.length < 2) { liveRoute.value = { intent: 'chat', matched: 'short', hit: '' }; return }
    try {
      liveRoute.value = await routeIntent(text, false)
    } catch { /* 静默 */ }
  }, 220)
}
watch(inputText, probeRoute)

const inputPlaceholder = computed(() => {
  if (uploadedImage.value) return '输入图片描述...'
  if (videoFrames.value.length) return '想问这段视频的什么？'
  const it = liveRoute.value.intent
  if (it === 'generate') return '说说想练什么，我来出题...'
  if (it === 'plan') return '说说你的目标，我来排计划...'
  if (it === 'evaluate') return '想让我看看哪方面？'
  return '输入消息...'
})

// 生成 Agent 的「随便出一题」口头禅 → 走自动选题，不当知识点
const GEN_INTENT_PHRASES = ['出一题', '考我一道题', '出道题', '再来一题', '来一题', '出题', '考考我', '帮我出一题']

function fellowMeta(key) {
  return agentMetaList.find(a => a.key === key) || {}
}
const dailyQuotes = [
  '今天也要加油哦，我会一直陪着你的。',
  '学习就像爬山，慢一点没关系，别停就好。',
  '累了就歇一会儿，回来我还在。',
  '你昨天很棒，今天继续一点点就很好。',
  '不会的题先放着，我们一起把它拆开看看。',
  '你不需要和任何人比，只要比昨天的自己好。',
  '小基一直都在，随时可以来找我说话。',
]
const dailyQuote = computed(() => dailyQuotes[new Date().getDate() % dailyQuotes.length])

// ===== 右栏问候（2026-08-26 玻璃卡片分区改版）：按时段问候，函数式保证随渲染刷新 =====
function greetingText() {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 9) return '早上好'
  if (h < 12) return '上午好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
}
function greetingSub() {
  const h = new Date().getHours()
  if (h < 9) return '新的一天也要加油呀'
  if (h < 18) return '学累了就来找我聊聊天'
  return '今天也辛苦啦，早点休息'
}

async function loadDaily() {
  try {
    const res = await getXiaojiDaily(authStore.user.id)
    if (res) {
      daily.value = {
        ...daily.value,
        ...res,
        stats: { ...daily.value.stats, ...(res.stats || {}) }
      }
    }
  } catch { /* 侧栏数据失败不影响主功能 */ }
}

function goRecLink() {
  const link = daily.value.recommendation?.action_link
  if (link) router.push(link)
}

// 当前轮到哪个队员署名（发消息前置位，流式回复创建消息时固化）
let pendingAgent = null

// 生成 Agent 出题（2026-09-02）：指定知识点 or 自动选题（薄弱优先）→ 真实生成 → 题目卡回聊
async function generateFellowQuestion(text = '') {
  sending.value = true
  pendingAgent = 'generate'
  const topic = GEN_INTENT_PHRASES.includes(text) || text.length < 2 ? '' : text
  messages.value.push({
    role: 'user',
    content: text || '帮我出一题吧～',
    created_at: new Date().toISOString()
  })
  await nextTick()
  forceScrollToBottom()
  setStage('正在出题…')
  try {
    const res = await agentGenerate(authStore.user.id, topic)
    const q = res.question
    if (q && q.title) {
      setSpeaking()
      messages.value.push({
        role: 'assistant',
        content: '',
        agent: 'generate',
        is_question: true,
        questionData: q,
        picked_from: res.picked_from || '',
        created_at: new Date().toISOString()
      })
    } else {
      messages.value.push({
        role: 'assistant',
        content: '这次没能生成出来，再试一次～',
        agent: 'generate',
        created_at: new Date().toISOString()
      })
    }
  } catch (e) {
    console.error('生成 Agent 出题失败:', e)
    ElMessage.error('出题失败，请重试')
    messages.value.push({
      role: 'assistant',
      content: '生成出错了，稍后再试一次吧～',
      agent: 'generate',
      created_at: new Date().toISOString()
    })
  } finally {
    pendingAgent = null
    sending.value = false
    setHappy()
  }
  await nextTick()
  forceScrollToBottom()
}

async function quickAsk(text) {
  if (sending.value) return
  // 陪伴 chips 固定走队长闲聊，跳过自动判别（forceChat）
  inputText.value = text
  await sendMessage({ forceChat: true })
}

// ===== 分页加载 =====
const MESSAGE_PAGE_SIZE = 30
const hasMoreMessages = ref(false)
const loadingMore = ref(false)
let skipScrollWatch = false
const fileInputRef = ref(null)
const uploadedImage = ref(null)
const imagePreviewVisible = ref(false)
const previewImageUrl = ref('')
const videoInputRef = ref(null)
const videoFrames = ref([])
const videoFileName = ref('')

const isHover = ref(false)
const showDialog = ref(false)
const dialogText = ref('')
const dialogPop = ref(false)
const dialogTimer = ref(null)
const dialogStyle = ref({})

const showQuestionDialog = ref(false)
const questionTab = ref('bank')
const historyQuestions = ref([])
const questionSets = ref([])

const showPreviewDialog = ref(false)
const previewTitle = ref('')
const previewType = ref('')
const previewData = ref(null)
const previewQuestions = ref([])

// ===== 题集展开 =====
const expandedSetId = ref(null)
const setQuestionsMap = ref({})

// ===== 话语库 =====
const greetPhrases = [
  '你好呀~ 😊 今天想学点什么？',
  '嘿嘿，你来啦！ 🎉 我正等着你呢！',
  '嗨！好久不见~ 最近学习怎么样？ 📚',
  '欢迎回来！ 🤗 小基随时准备帮你！',
  '哟！你来啦！ 💪 今天也要加油哦！',
  '哈喽~ 有什么我可以帮你的吗？ ✨',
  '嘿嘿，看到你来我特别开心！ 😄',
  '今天状态怎么样？ 🌟 想聊点什么？'
]

const clickPhrases = [
  '嘿嘿，干嘛~ 😄 想跟我聊天吗？',
  '我在听呢 👂 继续说，我认真的！',
  '继续继续！ 💬 我超喜欢听你说话！',
  '你戳到我啦！ 😆 好痒！',
  '哈哈哈，别闹！ 🤣 我快笑死了！',
  '嗯嗯？ 👀 你叫我干嘛？',
  '我在我在！ 🙋 有什么吩咐？',
  '嘿嘿，被你发现了！ 😏 我正想找你呢！'
]

const doubleClickPhrases = [
  '哈哈，别戳啦！ 🤣 我快受不了了！',
  '好痒！ 😆 你再戳我也要戳你了！',
  '你手不累吗？ 😏 要不要休息一下？',
  '哎呀！ 😂 你是不是太无聊了！',
  '救命！ 🆘 我被戳到不行了！',
  '嘿嘿，这么喜欢戳我吗？ 😊 那就多聊聊天吧！',
  '别戳了别戳了！ 🙈 我投降！'
]

const hoverPhrases = [
  '你好呀~ 😊 有什么想聊的？',
  '我在听呢 👂 随时都在！',
  '今天想学什么？ 📚 我来帮你！',
  '这个问题有意思！ 🤔 让我想想！',
  '哈哈，继续继续！ 😄 我喜欢听你说话！',
  '嗯嗯，然后呢？ 💬 我在认真听！',
  '好棒！继续加油！ 💪 你是最棒的！',
  '我来帮你！ ✨ 有什么问题尽管说！',
  '嘿嘿，你看起来心情不错呀！ 🌟',
  '今天有什么新收获？ 🎯 跟我分享分享！'
]

const thinkingPhrases = [
  '让我想想... 🤔 这个问题有点意思！',
  '嗯... 我在认真思考！ 💭 等等我！',
  '稍等哦~ 🧠 我在整理思路！',
  '哈哈，这个问题问得好！ 🤔 让我好好想想！',
  '嗯嗯，我在想！ 💡 马上回答你！',
  '等一下哦~ ⏳ 我在组织语言！'
]

// ===== 工具函数 =====
function getTypeName(type) {
  const map = { choice: '选择题', fill: '填空题', judge: '判断题', essay: '简答题', calculation: '计算题', coding: '编程题', programming: '编程题' }
  return map[type] || type || '题目'
}

function getQuestionPreview(q) {
  const content = q?.question_content || q?.title || ''
  return content.length > 50 ? content.slice(0, 50) + '...' : content
}

function formatEvalText(text) {
  if (!text) return ''
  return text.replace(/\n/g, '<br/>')
}

function scrollToBottom() {
  if (chatRollRef.value) {
    chatRollRef.value.scrollTop = chatRollRef.value.scrollHeight
  }
}

function forceScrollToBottom(instant = false) {
  const el = chatRollRef.value
  if (!el) return
  if (instant) {
    // 首次加载时禁用平滑滚动，直接跳到底部，避免从顶部滚动的动画
    el.style.scrollBehavior = 'auto'
    el.scrollTop = el.scrollHeight
    el.style.scrollBehavior = 'smooth'
  } else {
    el.scrollTop = el.scrollHeight
  }
}

// ===== 半球体效果 =====
function updateScale() {
  const container = chatRollRef.value
  if (!container) return
  const items = container.querySelectorAll('.roll-item')
  const containerHeight = container.clientHeight

  items.forEach((el) => {
    const rect = el.getBoundingClientRect()
    const containerRect = container.getBoundingClientRect()
    const itemBottom = rect.bottom - containerRect.top
    const distanceFromBottom = containerHeight - itemBottom

    const maxDistance = containerHeight
    const factor = Math.max(0.1, 1 - (distanceFromBottom / maxDistance) * 0.9)
    const opacity = 0.1 + factor * 0.9

    el.style.opacity = opacity
    el.style.transition = 'transform 0.1s ease, opacity 0.1s ease'
    el.style.transformOrigin = 'center center'
    el.style.filter = `brightness(${0.15 + factor * 0.85})`
  })
}

function onScroll() {
  updateScale()
  // 滚到顶部附近自动加载更早消息
  const el = chatRollRef.value
  if (el && el.scrollTop <= 40) loadMoreMessages()
}

// ===== 加载更早消息（前置拼接 + 滚动锚定，防止视口跳动） =====
async function loadMoreMessages() {
  if (!hasMoreMessages.value || loadingMore.value || loading.value) return
  loadingMore.value = true
  try {
    const res = await getXiaojiMessages(authStore.user.id, '', MESSAGE_PAGE_SIZE, messages.value.length)
    const older = res.messages || []
    hasMoreMessages.value = res.has_more ?? false
    console.log('[小基分页] 加载更早:', '请求 offset=', messages.value.length, '| 返回', older.length, '条 | total=', res.total, '| has_more=', hasMoreMessages.value)
    if (older.length) {
      const el = chatRollRef.value
      const prevHeight = el ? el.scrollHeight : 0
      const prevTop = el ? el.scrollTop : 0
      skipScrollWatch = true
      messages.value = [...older, ...messages.value]
      await nextTick()
      skipScrollWatch = false
      if (el) {
        el.scrollTop = prevTop + (el.scrollHeight - prevHeight)
      }
      setTimeout(updateScale, 50)
      ElMessage.success(`已加载更早 ${older.length} 条消息`)
    }
  } catch (e) {
    console.error('加载更早消息失败:', e)
    ElMessage.error('加载更早消息失败')
  } finally {
    loadingMore.value = false
  }
}

// ===== 语音 =====
// 播报走千问 TTS（音色/语速/音量读设置页配置），失败降级浏览器语音
// 长文本按句子切分排队合成：流式回复时首句声音随文字同步出来，大幅降低延迟
const ttsCache = new Map()
const ttsQueue = []
let ttsPumping = false
let pendingSpeak = ''
let ttsHalted = false      // 停止朗读标记：本段播报终止，后续句子不再入队
let ttsBroken = false      // TTS 服务不可用标记：会话内统一走浏览器朗读（避免两种音色混着出现）
let currentAudio = null
const isSpeaking = ref(false)

function stopAudio() {
  if (currentAudio) {
    currentAudio.pause()
    currentAudio = null
  }
}

function speakTextBrowser(text) {
  if (!window.speechSynthesis) return
  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = 'zh-CN'
  utterance.rate = Math.min(2, Math.max(0.5, voiceConfig.value.voice_speed / 5))
  utterance.pitch = 1.0
  window.speechSynthesis.speak(utterance)
}

// 单句合成（带缓存），失败返回 null
async function synthSentence(text) {
  const cfg = voiceConfig.value
  // TTS 服务已判死：本会话全部走浏览器朗读，避免两种音色混着出现
  if (ttsBroken) return null
  const cacheKey = `${cfg.voice_name}|${cfg.voice_speed}|${cfg.voice_volume}|${text.slice(0, 120)}`
  try {
    let audioBase64 = ttsCache.get(cacheKey)
    if (!audioBase64) {
      const res = await xiaojiTts(text, {
        speed: cfg.voice_speed,
        volume: cfg.voice_volume,
        voice_name: cfg.voice_name
      })
      audioBase64 = res?.audio_base64
      if (!audioBase64) throw new Error('TTS 无音频返回')
      if (ttsCache.size > 80) ttsCache.clear()
      ttsCache.set(cacheKey, audioBase64)
    }
    ttsBroken = false
    return audioBase64
  } catch (e) {
    console.error('千问 TTS 失败:', e)
    if (!ttsBroken) {
      // 第一次失败重试一次（偶发抖动）；再失败则本会话统一浏览器朗读
      try {
        const res = await xiaojiTts(text, {
          speed: cfg.voice_speed,
          volume: cfg.voice_volume,
          voice_name: cfg.voice_name
        })
        if (res?.audio_base64) {
          ttsCache.set(cacheKey, res.audio_base64)
          return res.audio_base64
        }
      } catch {}
      ttsBroken = true
      ElMessage.warning('语音服务暂不可用，本次会话已切换浏览器朗读')
    }
    return null
  }
}

function playMp3(base64) {
  return new Promise((resolve) => {
    stopAudio()
    currentAudio = new Audio(`data:audio/mp3;base64,${base64}`)
    currentAudio.volume = Math.min(1, Math.max(0, voiceConfig.value.voice_volume / 9))
    currentAudio.onended = resolve
    currentAudio.onerror = resolve
    currentAudio.play().catch(resolve)
  })
}

// 句子队列播放：合成一句播一句（合成与播放串行，流式下句子短、延迟低）
async function pumpTtsQueue() {
  if (ttsPumping) return
  ttsPumping = true
  isSpeaking.value = true
  while (ttsQueue.length && voiceEnabled.value && !ttsHalted) {
    const text = ttsQueue.shift()
    const b64 = await synthSentence(text)
    if (ttsHalted) break
    if (b64) {
      console.log(`[小基语音] 千问 TTS 播放（${voiceConfig.value.voice_name}）：${text.slice(0, 20)}`)
      await playMp3(b64)
    } else {
      speakTextBrowser(text)
    }
  }
  ttsPumping = false
  isSpeaking.value = false
}

// emoji 不朗读（后端 TTS 也会剥，这里兜底浏览器降级路径）
function stripEmoji(text) {
  return (text || '')
    .replace(/[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}\u{2190}-\u{21FF}\u{2300}-\u{23FF}\u{FE0F}\u{200D}\u{20E3}]/gu, ' ')
    .replace(/\s{2,}/g, ' ')
    .trim()
}

function enqueueSpeak(text) {
  if (ttsHalted) return
  const t = stripEmoji(text)
  if (!t) return
  ttsQueue.push(t)
  pumpTtsQueue()
}

// 停止朗读（豆包式）：停当前播放 + 清空队列，语音播报开关不受影响
function stopReading() {
  ttsHalted = true
  ttsQueue.length = 0
  pendingSpeak = ''
  stopAudio()
  if (window.speechSynthesis) window.speechSynthesis.cancel()
  isSpeaking.value = false
  ElMessage.info('已停止朗读')
}

function lastSentenceEnd(text) {
  const m = text.match(/[。！？；!?;\n]/)
  return m ? m.index + 1 : -1
}

// 流式文本投喂：按句子边界切分，成句即入队合成
function feedSpeakStream(chunk) {
  if (!voiceEnabled.value) return
  pendingSpeak += chunk
  let idx
  while ((idx = lastSentenceEnd(pendingSpeak)) > 0) {
    enqueueSpeak(pendingSpeak.slice(0, idx))
    pendingSpeak = pendingSpeak.slice(idx)
  }
}

function flushSpeakStream() {
  if (pendingSpeak.trim()) enqueueSpeak(pendingSpeak)
  pendingSpeak = ''
}

// 整段文本播报入口（问候/评价/戳一戳等非流式场景，同样走句子队列）
function speakText(text) {
  if (!voiceEnabled.value) return
  ttsHalted = false   // 新一段播报开始，解除上一段的停止标记
  pendingSpeak = ''
  feedSpeakStream(text)
  flushSpeakStream()
}

// ===== 语音输入（实时听写：麦克风 PCM 流 → 后端 WS → 讯飞 iat 逐字回传） =====
const isRecording = ref(false)
let audioCtx = null
let scriptNode = null
let mediaStream = null
let asrWs = null
let liveBaseText = ''
let liveText = ''
let closeTimer = null

function asrWsUrl() {
  const base = import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'
  return base.replace(/^http/, 'ws') + '/xiaoji/asr-ws'
}

async function toggleRecording() {
  if (isRecording.value) { stopRecording(); return }
  const Ctx = window.AudioContext || window.webkitAudioContext
  if (!navigator.mediaDevices || !Ctx) {
    ElMessage.warning('当前浏览器不支持录音，请使用 Chrome / Edge')
    return
  }
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    audioCtx = new Ctx({ sampleRate: 16000 })
    scriptNode = audioCtx.createScriptProcessor(1024, 1, 1)
    const source = audioCtx.createMediaStreamSource(mediaStream)
    source.connect(scriptNode)
    scriptNode.connect(audioCtx.destination)

    liveBaseText = inputText.value
    liveText = ''
    isRecording.value = true

    asrWs = new WebSocket(asrWsUrl())

    // 麦克风 PCM 持续发往后端 + 静音检测自动结束
    let silenceChunks = 0
    const SILENCE_CHUNKS_MAX = 40   // 1024 samples @16k ≈ 64ms/帧 × 40 ≈ 2.5s
    scriptNode.onaudioprocess = (e) => {
      if (!asrWs || asrWs.readyState !== WebSocket.OPEN) return
      let floats = e.inputBuffer.getChannelData(0)
      if (audioCtx.sampleRate !== 16000) {
        floats = resampleTo16k(floats, audioCtx.sampleRate)
      }
      // RMS 静音检测：连续 ~2.5s 低于阈值 → 自动收尾
      let sum = 0
      for (let i = 0; i < floats.length; i++) sum += floats[i] * floats[i]
      const rms = Math.sqrt(sum / floats.length)
      silenceChunks = rms < 0.006 ? silenceChunks + 1 : 0
      if (silenceChunks >= SILENCE_CHUNKS_MAX) {
        silenceChunks = 0
        stopRecording()
        return
      }
      const b64 = pcm16ToBase64(floatToPcm16(floats))
      asrWs.send(JSON.stringify({ status: 0, audio: b64 }))
    }

    // 识别结果实时回填输入框
    asrWs.onmessage = (e) => {
      try {
        const d = JSON.parse(e.data)
        if (d.error) {
          ElMessage.error('识别失败：' + d.error)
          return
        }
        if (typeof d.text === 'string') {
          liveText = d.text
          inputText.value = liveBaseText ? liveBaseText + liveText : liveText
        }
        if (d.done) stopRecording()
      } catch { /* 忽略坏帧 */ }
    }
    asrWs.onerror = () => {
      if (isRecording.value) ElMessage.error('语音识别连接失败，请重试')
    }
    ElMessage.info('正在听写，说完自动结束（点击可提前结束）')
  } catch (e) {
    console.error('录音失败:', e)
    releaseMedia()
    isRecording.value = false
    ElMessage.error('无法访问麦克风，请检查浏览器权限')
  }
}

function stopRecording() {
  if (asrWs && asrWs.readyState === WebSocket.OPEN) {
    asrWs.send(JSON.stringify({ status: 2, audio: '' }))
  }
  isRecording.value = false
  releaseMedia()
  // 后端会在最终结果后关闭连接；兜底 4s 后强制关闭
  clearTimeout(closeTimer)
  closeTimer = setTimeout(() => {
    if (asrWs && asrWs.readyState !== WebSocket.CLOSED) {
      try { asrWs.close() } catch {}
    }
    asrWs = null
  }, 4000)
}

function releaseMedia() {
  if (scriptNode) { try { scriptNode.disconnect() } catch {} ; scriptNode = null }
  if (audioCtx) { audioCtx.close().catch(() => {}); audioCtx = null }
  if (mediaStream) { mediaStream.getTracks().forEach(t => t.stop()); mediaStream = null }
}

// Float32（16k）→ Int16 PCM
function floatToPcm16(floats) {
  const pcm = new Int16Array(floats.length)
  for (let i = 0; i < floats.length; i++) {
    const s = Math.max(-1, Math.min(1, floats[i]))
    pcm[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
  }
  return pcm
}

// Int16 PCM → 小端字节流 base64（Uint8Array 值域 0-255，btoa 安全）
function pcm16ToBase64(pcm) {
  const bytes = new Uint8Array(pcm.buffer)
  let binary = ''
  const CHUNK = 0x8000
  for (let i = 0; i < bytes.length; i += CHUNK) {
    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + CHUNK))
  }
  return btoa(binary)
}

// 浏览器未按 16k 建上下文时线性降采样（分块近似，对 ASR 足够）
function resampleTo16k(floats, srcRate) {
  const ratio = srcRate / 16000
  const out = new Float32Array(Math.floor(floats.length / ratio))
  for (let i = 0; i < out.length; i++) {
    const pos = i * ratio
    const i0 = Math.floor(pos)
    const i1 = Math.min(i0 + 1, floats.length - 1)
    const frac = pos - i0
    out[i] = floats[i0] * (1 - frac) + floats[i1] * frac
  }
  return out
}

function randomPick(arr) {
  return arr[Math.floor(Math.random() * arr.length)]
}

// ===== 对话框 =====
async function pushAssistantMessage(content) {
  const assistantMsg = {
    role: 'assistant',
    content,
    image_url: null,
    created_at: new Date().toISOString()
  }
  messages.value.push(assistantMsg)
  await nextTick()
  forceScrollToBottom()
  setTimeout(updateScale, 50)
}

async function showDialogBubble(text, addToChat = true) {
  const offsetX = (Math.random() - 0.5) * 80
  const offsetY = (Math.random() - 0.5) * 60 - 20
  dialogStyle.value = {
    transform: `translate(calc(-50% + ${offsetX}px), calc(-100% + ${offsetY}px))`
  }
  dialogText.value = text
  showDialog.value = true
  dialogPop.value = false

  await nextTick()
  setTimeout(() => {
    dialogPop.value = true
  }, 50)

  if (addToChat) {
    await pushAssistantMessage(text)
  }

  if (dialogTimer.value) clearTimeout(dialogTimer.value)
  // 展示时长按文本长度自适应（3s 起步，最长 15s），长回复能看完
  const duration = Math.min(15000, Math.max(3000, (text || '').length * 150))
  dialogTimer.value = setTimeout(() => {
    showDialog.value = false
  }, duration)
}

// ===== 交互 =====
async function onAvatarClick() {
  // 配置未加载完时先等配置：避免默认音色与你设置的音色不一致
  if (!voiceConfigLoaded) await loadVoiceConfig()
  const msg = randomPick(clickPhrases)
  showDialogBubble(msg, true)
  speakText(msg)
  setHappy()
  setTimeout(() => setIdle(), 1500)
}

async function onAvatarDoubleClick() {
  if (!voiceConfigLoaded) await loadVoiceConfig()
  const msg = randomPick(doubleClickPhrases)
  showDialogBubble(msg, true)
  speakText(msg)
  setHappy()
  setTimeout(() => setIdle(), 1500)
}

function onAvatarHover(val) {
  isHover.value = val
  if (val) {
    const phrase = randomPick(hoverPhrases)
    showDialogBubble(phrase, false)
  }
}

// ===== 加载消息（首屏只取最近 30 条） =====
async function loadMessages() {
  loading.value = true
  try {
    const res = await getXiaojiMessages(authStore.user.id, '', MESSAGE_PAGE_SIZE, 0)
    messages.value = res.messages || []
    hasMoreMessages.value = res.has_more ?? false
    console.log('[小基分页] 首页加载:', messages.value.length, '条 | total=', res.total, '| has_more=', hasMoreMessages.value)
  } catch (error) {
    console.error('加载消息失败:', error)
    messages.value = []
    hasMoreMessages.value = false
  }
  // 注意：先关 loading 让消息渲染出来，再滚动，否则 scrollHeight 是加载态的高度
  loading.value = false
  await nextTick()
  forceScrollToBottom(true)
  setTimeout(() => {
    updateScale()
  }, 100)
  setIdle()
  setTimeout(() => {
    // 主动问候按设置开关（默认开启）
    if (voiceConfig.value.proactive_enabled === false) return
    const phrase = randomPick(greetPhrases)
    greetingBubble.value = phrase   // 气泡模式下作为常驻问候（有真实回复后自动让位）
    showDialogBubble(phrase, false)
  }, 600)
}

// ===== 跳转到搜索页 =====
function goSearch() {
  router.push('/xiaoji/search')
}

// ===== 跳转到语音通话页（独立通话界面） =====
function goVoiceCall() {
  router.push('/xiaoji/voice-call')
}

// ===== 搜索跳转定位 + 高亮 =====
function handleHighlight() {
  const id = route.query.highlight
  if (!id) return
  chatMode.value = 'list'   // 高亮定位只在列表模式可见，强制切列表
  highlightId.value = String(id)
  nextTick(() => scrollToMessage(String(id)))
  setTimeout(() => {
    highlightId.value = ''
  }, 2600)
}

function scrollToMessage(id) {
  const container = chatRollRef.value
  if (!container) return
  const el = container.querySelector(`[data-msg-id="${id}"]`)
  if (!el) return
  const cRect = container.getBoundingClientRect()
  const eRect = el.getBoundingClientRect()
  // 目标消息尽量居中显示
  container.scrollTop += eRect.top - cRect.top - cRect.height / 2 + eRect.height / 2
}

function formatTime(time) {
  if (!time) return ''
  const t = new Date(time)
  return t.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// ===== 日期分隔 =====
function dateKey(iso) {
  const d = iso ? new Date(iso) : null
  if (!d || isNaN(d.getTime())) return ''
  return `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`
}

function showDateDivider(index) {
  if (index === 0) return true
  return dateKey(messages.value[index]?.created_at) !== dateKey(messages.value[index - 1]?.created_at)
}

function formatDate(iso) {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  const now = new Date()
  const isSameDay = (a, b) =>
    a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()
  if (isSameDay(d, now)) return '今天'
  const yesterday = new Date(now)
  yesterday.setDate(now.getDate() - 1)
  if (isSameDay(d, yesterday)) return '昨天'
  const week = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][d.getDay()]
  if (d.getFullYear() === now.getFullYear()) {
    return `${d.getMonth() + 1}月${d.getDate()}日 ${week}`
  }
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
}

// ===== 词条提取（2026-08-25 从 ChatArea 移植：小基成为词条唯一收集入口）
// 问词义 → chat_ask；识图提词 → xiaoji_vision
const vocabCards = ref([])
const VOCAB_STOPWORDS = new Set([
  'the','and','for','you','your','this','that','with','are','was','were','will','have','has','not','but','can','from',
  'what','when','where','which','who','how','about','than','then','them','they','their','there','into','these','those',
  'some','other','being','been','more','most','much','many','such','only','also','very','just','like','would','should',
  'could','must','might','shall','every','both','between','after','before','because','over','under','again','once',
  'here','hello','thanks','thank','please','image','images',
])

function detectVocabCards(userText, replyText, hadImages) {
  const words = []
  // 1. 问词义模式："abandon 是什么意思"
  const ask = userText.match(/([A-Za-z]{2,20})\s*(?:是什么意思|什么意思|怎么读|怎么用|如何用)/)
  if (ask) words.push(ask[1].toLowerCase())
  // 2. 整句就是一个单词
  const single = userText.trim().match(/^([A-Za-z]{2,20})$/)
  if (single) words.push(single[1].toLowerCase())
  // 3. 识图模式：从 AI 回复里提取英文生词
  if (hadImages) {
    const found = (replyText.match(/[A-Za-z]{3,}/g) || [])
      .map(w => w.toLowerCase())
      .filter(w => !VOCAB_STOPWORDS.has(w))
    words.push(...found.slice(0, 5))
  }
  const touchpoint = hadImages && !ask && !single ? 'xiaoji_vision' : 'chat_ask'
  return [...new Set(words)].map(w => ({ word: w, touchpoint }))
}

// ===== 自动分流落地：判为派活后出对应卡片（2026-09-10）=====
// 三张卡片全部复用既有链路，不另起一套：
//   出题 → 出题表单（用户填）→ 真实出题 → 跳做题界面（与资源库同款链路）
//   规划 → 计划草稿（AI 排）→ 确认 → 建计划 → 跳计划详情
//   评估 → /evaluation/deep-analysis 的真实结论 → 评估卡 → 可跳评估中心
async function handleRoutedIntent(intent, text) {
  if (intent === 'generate') return openGenerateCard(text)
  if (intent === 'plan') return openPlanCard(text)
  if (intent === 'evaluate') return openEvaluateCard()
}

/** 从指令里剥出知识点/目标（预填用，不准用户可改——只做保守清洗，不过度猜测） */
function cleanTopicHint(text) {
  let t = (text || '').trim()
  // 长短语优先剥（否则「学习计划」会先被「计划」切碎，剩个「学习」）
  const words = [
    '帮我做个', '帮我制定', '帮我生成', '帮我安排', '帮我出', '帮我做', '帮我', '麻烦', '请你', '请', '给我', '我要', '我想',
    '学习计划', '备考计划', '复习计划', '制定计划', '生成计划', '做个计划', '学习规划', '学习路线',
    '学习方案', '备考方案', '安排一下', '怎么学', '怎么安排', '怎么规划', '计划', '规划', '安排',
    '出题', '出道题', '出个题', '出一道', '出几道', '来一道', '来几道', '生成题', '生成一道', '生成几道',
    '做几道题', '练几道', '练习题', '刷题', '考考我', '测测我', '的题', '的卷', '题目', '试卷', '题',
    '出套卷子', '出套卷', '出份卷', '出个卷', '套卷子', '卷子', '几道', '一道',
    '怎么走', '怎么', '一下', '一个', '吧',
  ].sort((a, b) => b.length - a.length)
  for (const w of words) t = t.split(w).join(' ')
  t = t.replace(/[，。！？、,.!?\s]+/g, ' ').trim()
  t = t.replace(/[的了吧呀]+$/, '').trim()
  return t.length >= 2 ? t.slice(0, 20) : ''
}

/** 出题卡：复用现有出题表单 */
function openGenerateCard(text) {
  genForm.knowledge = cleanTopicHint(text)
  genForm.count = 1
  showGenDialog.value = true
}

/** 规划卡：先排草稿，确认后落库 */
async function openPlanCard(text) {
  const goal = cleanTopicHint(text) || (text || '').replace(/^(帮我|请|麻烦|给我)/, '').trim().slice(0, 20)
  const card = reactive({ goal, days: 30, minutes: 30, loading: false, error: false, draft: null, creating: false })
  messages.value.push({
    role: 'assistant', content: '', is_plan_card: true, planCard: card,
    created_at: new Date().toISOString()
  })
  await nextTick()
  forceScrollToBottom()
  if (card.goal) runPlanDraft(card)   // 说清了目标就直接排，不让用户再点一次
}

async function runPlanDraft(card) {
  if (!card.goal?.trim()) { ElMessage.warning('先说说想学什么～'); return }
  card.loading = true
  card.error = false
  try {
    const res = await fetch(`${BACKEND_URL}/learning-plan/generate-tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authStore.token}` },
      body: JSON.stringify({
        keywords: card.goal.trim(), difficulty: '中等',
        daily_minutes: card.minutes, total_days: card.days
      })
    })
    const out = await res.json()
    let days = out?.data || []
    if (!Array.isArray(days) && days.tasks) days = days.tasks
    if (!res.ok || !out?.success || !days.length) throw new Error(out?.detail || '生成失败')
    card.draft = days
  } catch (e) {
    card.error = true
    ElMessage.error('计划生成失败：' + (e?.message || '请重试'))
  } finally {
    card.loading = false
  }
}

async function confirmPlanDraft(card) {
  card.creating = true
  try {
    const start = new Date()
    const end = new Date(start.getTime() + card.days * 86400000)
    const iso = d => d.toISOString().slice(0, 10)
    const res = await createPlan({
      user_id: authStore.user.id, name: card.goal, stage: '', grade: '', major: '',
      difficulty: '中等', daily_minutes: card.minutes,
      start_date: iso(start), end_date: iso(end),
      keywords: card.goal, tasks: card.draft
    })
    if (res?.success) {
      ElMessage.success('计划建好了，开始吧！')
      router.push(`/plan-detail/${res.plan_id}`)
    } else {
      ElMessage.error(typeof res?.detail === 'string' ? res.detail : '保存失败，请重试')
    }
  } catch (e) {
    ElMessage.error('保存失败：' + (e?.response?.data?.detail || e?.message || '请重试'))
  } finally {
    card.creating = false
  }
}

/** 评估卡：复用评估中心的深度分析（带 15 分钟缓存） */
async function openEvaluateCard() {
  const card = reactive({ loading: true, error: false, data: null })
  messages.value.push({
    role: 'assistant', content: '', is_eval_card: true, evalCard: card,
    created_at: new Date().toISOString()
  })
  await nextTick()
  forceScrollToBottom()
  try {
    const res = await fetch(
      `${BACKEND_URL}/evaluation/deep-analysis?user_id=${encodeURIComponent(authStore.user.id)}`,
      { headers: { 'Authorization': `Bearer ${authStore.token}` } }
    )
    const out = await res.json()
    if (!res.ok) throw new Error(out?.detail || 'failed')
    card.data = out?.data || out
  } catch {
    card.error = true
  } finally {
    card.loading = false
  }
}

// ===== 发送消息 =====
async function sendMessage(opts = {}) {
  const text = inputText.value.trim()
  const image = uploadedImage.value
  const video = videoFrames.value.length ? [...videoFrames.value] : null

  if (!text && !image && !video) {
    ElMessage.warning('请输入内容、上传图片或视频')
    return
  }

  inputText.value = ''
  vocabCards.value = []
  liveRoute.value = { intent: 'chat', matched: '', hit: '' }   // 复位识别显示

  const userMsg = {
    role: 'user',
    content: text || (video ? '[视频]' : '图片'),
    image_url: image || null,
    is_question: false,
    is_set: false,
    is_video: !!video,
    created_at: new Date().toISOString()
  }
  messages.value.push(userMsg)
  const currentImage = image
  const currentVideo = video
  if (image) {
    removeImage()
  }
  if (video) {
    removeVideo()
  }
  await nextTick()
  forceScrollToBottom()
  setTimeout(updateScale, 50)

  sending.value = true
  setThinking('思考中...')

  try {
    let reply = ''
    // 图片/视频走独立识图链路、不经过队员人设，此处不消费 pendingAgent → 显式清掉防串台
    pendingAgent = null
    if (currentImage) {
      const res = await xiaojiVision({
        user_id: authStore.user.id,
        image_url: currentImage,
        question: text || '这张图片里有什么？'
      })
      reply = res.reply || '图片理解失败，请重试'
      setSpeaking()
      // 回复只进消息列表：列表模式看列表，气泡模式由常驻气泡显示
      await pushAssistantMessage(reply)
      speakText(reply)
    } else if (currentVideo) {
      const res = await xiaojiVideoAnalyze({
        user_id: authStore.user.id,
        frames: currentVideo,
        question: text || '分析这个视频讲了什么'
      })
      reply = res.reply || '视频分析失败，请重试'
      setSpeaking()
      await pushAssistantMessage(reply)
      speakText(reply)
    } else {
      // 自动判别（2026-09-10）：闲聊走流式；判为派活则后端直接回路由指令，改出卡片
      setSpeaking()
      const out = await streamXiaojiChat(text, opts)
      if (out.route) {
        await handleRoutedIntent(out.route, text)
        return
      }
      reply = out.text || ''
    }
    // 词条提取：问词义 / 整句单词 / 识图提词 → 输入框上方渲染词条卡
    vocabCards.value = detectVocabCards(text, reply, !!currentImage)
    setHappy()

  } catch (error) {
    console.error('发送失败:', error)
    ElMessage.error('发送失败，请重试')
    setIdle()
  } finally {
    sending.value = false
  }
}

// ===== 小基对话请求：闲聊流式逐字 / 派活直接返回路由指令 =====
// 返回 { text } 或 { route }；自动判别在后端同一请求内完成，不多一次往返
async function streamXiaojiChat(text, opts = {}) {
  const response = await fetch(
    `${BACKEND_URL}/community/xiaoji/chat-stream?user_id=${encodeURIComponent(authStore.user.id)}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`
      },
      body: JSON.stringify({ content: text, force_chat: !!opts.forceChat })
    }
  )
  if (!response.ok) {
    const err = await response.json().catch(() => null)
    throw new Error(err?.detail || `HTTP ${response.status}`)
  }

  // 判为派活：后端不回答，回一条 JSON 路由指令，由前端出对应卡片
  const ctype = response.headers.get('content-type') || ''
  if (ctype.includes('application/json')) {
    const routed = await response.json()
    return { route: routed.route, matched: routed.matched }
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let full = ''
  ttsHalted = false   // 新回复开始，解除停止标记

  // 助手消息占位，随流更新（队员署名：呼叫对象置位的 agent 固化进消息）
  const assistantMsg = {
    role: 'assistant',
    content: '',
    image_url: null,
    agent: pendingAgent || undefined,
    created_at: new Date().toISOString()
  }
  messages.value.push(assistantMsg)
  await nextTick()
  forceScrollToBottom()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    const chunk = decoder.decode(value, { stream: true })
    full += chunk
    assistantMsg.content = full
    feedSpeakStream(chunk)
    forceScrollToBottom()
    setTimeout(updateScale, 50)
  }
  flushSpeakStream()

  if (!full) {
    messages.value.pop()
    throw new Error('空回复')
  }
  return { text: full }
}

// ===== 切换题集展开 =====
async function toggleSetExpand(setId) {
  if (expandedSetId.value === setId) {
    expandedSetId.value = null
    return
  }
  expandedSetId.value = setId

  if (setQuestionsMap.value[setId] !== undefined) {
    return
  }

  setQuestionsMap.value[setId] = null
  const s = questionSets.value.find(item => item.id === setId)
  if (s) {
    const ids = s.question_ids || []
    const qs = []
    for (const id of ids) {
      try {
        const q = await getQuestionDetail(id)
        if (q) qs.push(q)
      } catch (e) {}
    }
    setQuestionsMap.value[setId] = qs
  } else {
    setQuestionsMap.value[setId] = []
  }
}

// ===== 聊天行动卡（2026-08-27）：出题表单 + 题目卡行动 + 代码沙箱 =====
const genTypes = ['选择题', '填空题', '判断题', '简答题', '计算题', '编程题']
const genDifficulties = ['简单', '中等', '困难']
// 学科锚定（2026-09-02「出题卡质量差」修复：不指定时模型默认偏向 Python/编程）
const genCategories = ['通用', '数学', '语文', '英语', '物理', '化学', '生物', '历史', '政治', '地理', '计算机']
const showGenDialog = ref(false)
const genLoading = ref(false)
const genForm = reactive({ qtype: '选择题', knowledge: '', difficulty: '中等', count: 1, category: '通用' })
const bankMatch = reactive({})     // msgIndex -> { loading, items }
const codeRun = reactive({})       // `${index}-${si}` -> { running, input, output }

// 代码围栏解析：```lang\ncode``` → 文本/代码段（代码段渲染成可运行卡片）
function segmentsOf(content) {
  if (!content) return []
  const re = /```(\w*)\s*\n?([\s\S]*?)```/g
  const segs = []
  let last = 0
  let m
  while ((m = re.exec(content))) {
    if (m.index > last) segs.push({ type: 'text', text: content.slice(last, m.index) })
    segs.push({ type: 'code', lang: (m[1] || 'python').toLowerCase(), code: m[2].trim() })
    last = m.index + m[0].length
  }
  if (last < content.length) segs.push({ type: 'text', text: content.slice(last) })
  return segs
}
const CODE_LANGS = { python: 'Python 3', c: 'C', cpp: 'C++', java: 'Java' }
function langLabel(l) { return CODE_LANGS[l] || l.toUpperCase() }
function isRunnable(l) { return l in CODE_LANGS }

async function runMsgCode(key, code, lang) {
  const slot = codeRun[key] || { running: false, input: '', output: '' }
  codeRun[key] = { ...slot, running: true }
  try {
    const res = await runCode(code, lang, slot.input || '')
    codeRun[key] = { running: false, input: slot.input || '', output: res?.output ?? '（无输出）' }
  } catch (e) {
    codeRun[key] = {
      running: false,
      input: slot.input || '',
      output: `运行失败：${e?.response?.data?.detail || e?.message || '网络错误'}`
    }
  }
}

// 题目卡·存到资源库（写生成历史）
async function saveToResourceLib(q) {
  try {
    await saveGenerationHistory({
      user_id: authStore.user.id,
      question_id: q.id || '',
      title: q.title || '对话题目',
      question_type: q.question_type || 'choice',
      category: '通用',
      topic: q.topic || q.knowledge_point || (q.title || '').slice(0, 40)
    })
    ElMessage.success('已存入资源库 · 生成历史')
  } catch {
    ElMessage.error('保存失败，请重试')
  }
}

// 题目卡·题库检索同类题（学科计划题库模糊搜索）
async function toggleBankSearch(idx, q) {
  if (bankMatch[idx]?.items?.length || bankMatch[idx]?.loading) return
  bankMatch[idx] = { loading: true, items: [] }
  const kw = (q.question_content || q.title || '').slice(0, 24)
  try {
    const res = await searchBankQuestionsApi(kw, '', 6)
    bankMatch[idx] = { loading: false, items: (res?.questions || []).slice(0, 6) }
  } catch {
    bankMatch[idx] = { loading: false, items: [] }
  }
}

function evaluateBankQuestion(q) {
  ElMessage.info('已发送给小基评价')
  setTimeout(() => sendSingleQuestion(q), 150)
}

// 自定义出题：填需求 → 生成 Agent 逐道生成 → 题目卡回聊（署名 generate）
async function submitGenForm() {
  const f = genForm
  if (!f.knowledge.trim()) {
    ElMessage.warning('填一下知识点～')
    return
  }
  showGenDialog.value = false
  genLoading.value = true
  pendingAgent = 'generate'
  recordAction(authStore.user.id, 'use_generate_agent', { touchpoint: 'xiaoji_gen_card' }).catch(() => {})
  const catText = f.category && f.category !== '通用' ? `${f.category}·` : ''
  messages.value.push({
    role: 'user',
    content: `✍️ 帮我出 ${f.count} 道${f.difficulty}难度的${f.qtype}，${catText}知识点：${f.knowledge.trim()}`,
    created_at: new Date().toISOString()
  })
  await nextTick()
  forceScrollToBottom()

  const qs = []
  try {
    for (let i = 0; i < f.count; i++) {
      // 真实进度：出题是逐道生成的，这里显示的就是真实第几道
      setStage(f.count > 1 ? `正在出第 ${i + 1}/${f.count} 道题…` : '正在出题…', Math.round(i / f.count * 100))
      const q = await generateQuestion({
        user_id: authStore.user.id,
        category: f.category || '通用',
        topic: f.knowledge.trim(),
        question_type: f.qtype,
        difficulty: f.difficulty
      })
      if (q) qs.push(q)
    }
    setSpeaking()
    if (qs.length) {
      for (const q of qs) {
        messages.value.push({
          role: 'assistant',
          content: '',
          agent: 'generate',
          is_question: true,
          questionData: q,
          created_at: new Date().toISOString()
        })
      }
      // 与资源库生成题目同款链路：带第一道题直接跳做题界面（其余留在聊天里可点）
      sessionStorage.setItem('current_question', JSON.stringify(qs[0]))
      setTimeout(() => router.push('/do-question'), 400)
    } else {
      messages.value.push({
        role: 'assistant',
        content: '抱歉，这次没能生成出来，你换个知识点或题型再试一次～',
        agent: 'generate',
        created_at: new Date().toISOString()
      })
    }
  } catch (e) {
    console.error('生成失败:', e)
    ElMessage.error('生成失败，请重试')
    messages.value.push({
      role: 'assistant',
      content: '生成出错了，稍后再试一次吧～',
      agent: 'generate',
      created_at: new Date().toISOString()
    })
  } finally {
    genLoading.value = false
    setHappy()
  }
  await nextTick()
  forceScrollToBottom()
}

// ===== 发送题目 =====
async function sendSingleQuestion(q) {
  showQuestionDialog.value = false
  expandedSetId.value = null

  const userMsg = {
    role: 'user',
    content: `📝 ${q.title || q.question_content || '未命名题目'}`,
    is_question: true,
    questionData: q,
    created_at: new Date().toISOString()
  }
  messages.value.push(userMsg)
  await nextTick()
  forceScrollToBottom()
  setTimeout(updateScale, 50)

  sending.value = true

  setStage('正在批改这道题…')

  try {
    const res = await evaluateQuestion(authStore.user.id, q)
    const reply = res.reply || '好的，我来看看这道题~'

    setSpeaking()

    const assistantMsg = {
      role: 'assistant',
      content: reply,
      is_evaluation: true,
      created_at: new Date().toISOString()
    }
    messages.value.push(assistantMsg)
    await nextTick()
    forceScrollToBottom()
    setTimeout(updateScale, 50)
    speakText(reply)
    setHappy()

  } catch (error) {
    console.error('评价失败:', error)
    ElMessage.error('评价失败，请重试')
    setIdle()
  } finally {
    sending.value = false
  }
}

// ===== 发送题集 =====
async function sendWholeSet(s) {
  showQuestionDialog.value = false

  let questions = []
  const ids = s.question_ids || []
  for (const id of ids) {
    try {
      const q = await getQuestionDetail(id)
      if (q) questions.push(q)
    } catch (e) {}
  }

  const userMsg = {
    role: 'user',
    content: `📚 题集：${s.name}（${questions.length} 道题）`,
    is_set: true,
    setData: s,
    created_at: new Date().toISOString()
  }
  messages.value.push(userMsg)
  await nextTick()
  forceScrollToBottom()
  setTimeout(updateScale, 50)

  sending.value = true
  setThinking('分析题集中...')

  try {
    const res = await evaluateSet(authStore.user.id, s, questions)
    const reply = res.reply || '好的，我来看看这个题集~'

    setSpeaking()

    const assistantMsg = {
      role: 'assistant',
      content: reply,
      is_evaluation: true,
      created_at: new Date().toISOString()
    }
    messages.value.push(assistantMsg)
    await nextTick()
    forceScrollToBottom()
    setTimeout(updateScale, 50)
    speakText(reply)
    setHappy()

  } catch (error) {
    console.error('评价题集失败:', error)
    ElMessage.error('评价失败，请重试')
    setIdle()
  } finally {
    sending.value = false
  }
}

// ===== 预览 =====
function previewQuestion(q) {
  previewType.value = 'question'
  previewTitle.value = '📝 题目详情'
  previewData.value = q
  showPreviewDialog.value = true
}

async function previewSet(s) {
  previewType.value = 'set'
  previewData.value = s
  previewTitle.value = '📚 题集详情'

  const ids = s.question_ids || []
  const qs = []
  for (const id of ids) {
    try {
      const q = await getQuestionDetail(id)
      if (q) qs.push(q)
    } catch (e) {}
  }
  previewQuestions.value = qs
  showPreviewDialog.value = true
}

async function openSendQuestion() {
  showQuestionDialog.value = true
  expandedSetId.value = null
  setQuestionsMap.value = {}
  try {
    const res = await getGenerationHistory(authStore.user.id)
    historyQuestions.value = res || []
  } catch {
    historyQuestions.value = []
  }
  try {
    const res = await getQuestionSets(authStore.user.id)
    questionSets.value = res || []
  } catch {
    questionSets.value = []
  }
}

// ===== 题库搜索（学科计划 19,000+ 题，模糊搜索，2026-08-25 纳入发送题目） =====
const bankKeyword = ref('')
const bankSyllabus = ref('')
const bankResults = ref([])
const bankSyllabusNames = ref({})
const bankSearching = ref(false)
let bankSearchTimer = null

async function doBankSearch() {
  const kw = bankKeyword.value.trim()
  if (!kw) {
    bankResults.value = []
    return
  }
  bankSearching.value = true
  try {
    const res = await searchBankQuestionsApi(kw, bankSyllabus.value, 20)
    bankResults.value = res.questions || []
    if (res.syllabus_names) bankSyllabusNames.value = res.syllabus_names
  } catch {
    bankResults.value = []
  } finally {
    bankSearching.value = false
  }
}

function onBankSearchInput() {
  clearTimeout(bankSearchTimer)
  bankSearchTimer = setTimeout(doBankSearch, 300)
}

function bankQuestionTitle(q) {
  const stem = q.content?.stem || q.title || q.question_content || ''
  return stem.length > 46 ? stem.slice(0, 46) + '…' : stem
}

function sendBankQuestion(q) {
  // 题库题目字段与评价接口对齐：title/question_content/difficulty_score
  sendSingleQuestion({
    ...q,
    title: bankQuestionTitle(q),
    question_content: q.content?.stem || q.title || '',
    difficulty_score: q.difficulty || q.difficulty_score || 5,
  })
}

// ===== 图片 =====
function triggerImageUpload() {
  fileInputRef.value?.click()
}

function handleImageSelect(event) {
  const file = event.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (e) => {
    uploadedImage.value = e.target.result
  }
  reader.readAsDataURL(file)
  event.target.value = ''
}

function removeImage() {
  uploadedImage.value = null
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

// ===== 视频分析（2026-09-05 用户定调：小基读视频内容并分析）=====
function triggerVideoUpload() {
  videoInputRef.value?.click()
}

function pickVideoFrames(file, count = 4) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const v = document.createElement('video')
    v.muted = true; v.playsInline = true; v.preload = 'auto'
    const done = () => URL.revokeObjectURL(url)
    v.onerror = () => { done(); reject(new Error('视频读取失败')) }
    v.onloadedmetadata = async () => {
      try {
        const dur = v.duration || 1
        const n = Math.max(2, Math.min(count, Math.floor(dur * 2)))
        const frames = []
        for (let i = 0; i < n; i++) {
          const t = (dur * (i + 0.6)) / n
          await new Promise(res => { v.onseeked = res; v.currentTime = t })
          const canvas = document.createElement('canvas')
          const w = Math.min(480, v.videoWidth || 640)
          canvas.width = w
          canvas.height = Math.round(w * (v.videoHeight / (v.videoWidth || 1)))
          canvas.getContext('2d').drawImage(v, 0, 0, canvas.width, canvas.height)
          frames.push(canvas.toDataURL('image/jpeg', 0.62))
        }
        resolve(frames)
      } catch (e) {
        reject(e)
      } finally {
        done()
      }
    }
    v.src = url
  })
}

async function handleVideoSelect(event) {
  const file = event.target.files[0]
  event.target.value = ''
  if (!file) return
  const loadingMsg = ElMessage({ message: '正在抽取视频画面…', duration: 0 })
  try {
    videoFrames.value = await pickVideoFrames(file, 4)
    videoFileName.value = file.name
    ElMessage.success(`已抽取 ${videoFrames.value.length} 帧，输入想了解的问题后发送`)
  } catch (e) {
    console.error('抽帧失败:', e)
    ElMessage.error('视频读取失败，请换一个视频试试')
    videoFrames.value = []
  } finally {
    loadingMsg.close()
  }
}

function removeVideo() {
  videoFrames.value = []
  videoFileName.value = ''
  if (videoInputRef.value) videoInputRef.value.value = ''
}

function toggleVoice() {
  voiceEnabled.value = !voiceEnabled.value
  voiceConfig.value.voice_enabled = voiceEnabled.value
  // 同步到小基设置
  updateXiaojiConfig(authStore.user.id, { voice_enabled: voiceEnabled.value }).catch(() => {})
  if (!voiceEnabled.value) {
    if (window.speechSynthesis) window.speechSynthesis.cancel()
    ttsHalted = true
    stopAudio()
    ttsQueue.length = 0
  }
  ElMessage.info(voiceEnabled.value ? '语音播报已开启' : '语音播报已关闭')
}

async function clearHistory() {
  try {
    await ElMessageBox.confirm('确定要清空所有聊天记录吗？', '确认清空', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await clearXiaojiMessages(authStore.user.id)
    messages.value = []
    greetingBubble.value = ''
    ElMessage.success('已清空')
  } catch {}
}

function goSettings() {
  router.push('/xiaoji/settings')
}

function handleResize() {
  updateScale()
}

watch(messages, () => {
  nextTick(() => {
    // 加载更早消息的前置拼接不触发滚底（滚动锚定在 loadMoreMessages 里处理）
    if (skipScrollWatch) return
    forceScrollToBottom()
    setTimeout(updateScale, 50)
  })
})

onMounted(() => {
  loadVoiceConfig().then(() => loadMessages()).then(() => handleHighlight())
  loadDaily()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (isRecording.value) stopRecording()
  clearTimeout(closeTimer)
  if (asrWs && asrWs.readyState !== WebSocket.CLOSED) {
    try { asrWs.close() } catch {}
  }
  stopAudio()
  ttsQueue.length = 0
  if (window.speechSynthesis) window.speechSynthesis.cancel()
})
</script>

<style scoped>
.xiaoji-call-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-color);
  color: var(--text-primary);
  overflow: hidden;
}

/* ===== 左右侧栏布局（小基推荐 / 小基关心，两种模式都显示） ===== */
.call-body {
  flex: 1;
  display: flex;
  min-height: 0;
  position: relative;   /* 右栏悬浮定位基准 */
}
.call-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
}
.call-side {
  width: 264px;
  /* 整体固定不可滚（2026-09-02 用户重申）：只有日志卡内的通话记录区内部滚动；
     整栏溢出宁可裁剪也不出滚动条（此前 overflow-y:auto 会在记录多时让整栏滚起来） */
  overflow: hidden;
  /* 2026-08-26 压缩：配合日志区局部滚动，尽量整栏不滚 */
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  /* 悬浮右缘（2026-08-26）：不参与 flex 布局，不再挤压中间列，小基保持屏幕居中 */
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  z-index: 50;
  background: var(--bg-overlay);
  backdrop-filter: blur(24px) saturate(1.2);
  -webkit-backdrop-filter: blur(24px) saturate(1.2);
  box-shadow: -16px 0 40px rgba(0, 0, 0, 0.18);
}
.call-side::-webkit-scrollbar { width: 3px; }
.call-side::-webkit-scrollbar-thumb {
  background: rgba(128,128,128,0.12);
  border-radius: 2px;
}
.side-right {
  border-left: 1px solid var(--border-color);
}
/* 纯净模式：右栏隐藏 */
.call-body.clean .call-side {
  display: none;
}
/* 边缘中枢轮盘占位：中宽屏幕给聊天区左侧留出空间，避免与轮盘重叠 */
@media (max-width: 1500px) {
  .call-main { padding-left: 420px; }
}
@media (max-width: 1100px) {
  .call-main { padding-left: 280px; }
}
/* 纯净模式：左缘轮盘隐藏（v-show），去掉左留白，小基在屏幕正中 */
.call-body.clean .call-main {
  padding-left: 0;
}
/* ===== 右栏玻璃卡片分区（2026-08-26 改版） ===== */
/* 问候头 */
.side-greeting {
  display: flex; align-items: center; gap: 10px;
  padding: 2px 4px 10px; border-bottom: 1px solid var(--border-color);
}
.side-greeting-avatar {
  width: 32px; height: 32px; border-radius: 50%; object-fit: contain;
  background: rgba(139,92,246,.10);
  box-shadow: 0 0 14px rgba(139,92,246,.35);
  flex-shrink: 0;
}
.side-greeting-text { min-width: 0; }
.side-greeting-title {
  font-size: 14px; font-weight: 700; color: var(--text-primary);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.side-greeting-name { color: color-mix(in srgb, #c4b5fd 60%, var(--text-primary)); }
.side-greeting-sub { font-size: 11px; color: var(--text-muted); margin-top: 1px; }

/* 分区卡片 */
.side-card {
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: 10px;
  display: flex; flex-direction: column; gap: 8px;
}
.side-card-head {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; font-weight: 600; color: var(--text-secondary);
}
.side-card-ic {
  width: 22px; height: 22px; border-radius: 7px;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; color: #fff; flex-shrink: 0;
}
.side-card-ic.amber  { background: linear-gradient(135deg, #f59e0b, #d97706); box-shadow: 0 0 10px rgba(245,158,11,.35); }
.side-card-ic.violet { background: linear-gradient(135deg, #8b5cf6, #6d28d9); box-shadow: 0 0 10px rgba(139,92,246,.35); }
.side-card-ic.cyan   { background: linear-gradient(135deg, #06b6d4, #0284c7); box-shadow: 0 0 10px rgba(6,182,212,.35); }

/* 推荐卡 */
.rec-card {
  background: rgba(245,158,11,.06);
  border: 1px solid rgba(245,158,11,.15);
  border-left: 3px solid rgba(245,158,11,.6);
  border-radius: 12px;
  padding: 10px;
  display: flex; flex-direction: column; gap: 8px;
}
.rec-title { font-size: 13px; font-weight: 600; color: color-mix(in srgb, #f59e0b 70%, var(--text-primary)); }
.rec-content { font-size: 12px; line-height: 1.7; color: var(--text-secondary); }
.rec-empty {
  text-align: center; font-size: 12px; color: var(--text-muted);
  background: rgba(128,128,128,.04); border-radius: 12px;
  padding: 10px 8px; line-height: 1.6;
}
.quick-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.quick-chip {
  font-size: 11px; padding: 3px 8px; border-radius: 20px;
  background: color-mix(in srgb, var(--brand) 8%, transparent); border: 1px solid color-mix(in srgb, var(--brand) 15%, transparent);
  color: var(--brand-bright); cursor: pointer; transition: all .2s ease;
}
.quick-chip:hover {
  background: color-mix(in srgb, var(--brand) 16%, transparent);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px color-mix(in srgb, var(--brand) 20%, transparent);
}

/* 关心磁贴（2×2 渐变，每格主题色） */
.care-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.care-item {
  border-radius: 12px; padding: 6px 4px;
  display: flex; flex-direction: column; align-items: center; gap: 1px;
  border: 1px solid transparent; transition: transform .2s, box-shadow .2s;
}
.care-item:hover { transform: translateY(-1px); }
.care-item strong { font-size: 17px; font-weight: 700; }
.care-item span { font-size: 10px; color: var(--text-muted); }
.care-item.c-violet { background: linear-gradient(160deg, rgba(139,92,246,.16), rgba(139,92,246,.04)); border-color: rgba(139,92,246,.22); }
.care-item.c-violet strong { color: color-mix(in srgb, #a78bfa 60%, var(--text-primary)); }
.care-item.c-violet:hover { box-shadow: 0 0 16px rgba(139,92,246,.25); }
.care-item.c-blue { background: linear-gradient(160deg, rgba(59,130,246,.15), rgba(59,130,246,.04)); border-color: rgba(59,130,246,.22); }
.care-item.c-blue strong { color: color-mix(in srgb, #60a5fa 60%, var(--text-primary)); }
.care-item.c-blue:hover { box-shadow: 0 0 16px rgba(59,130,246,.25); }
.care-item.c-green { background: linear-gradient(160deg, rgba(16,185,129,.15), rgba(16,185,129,.04)); border-color: rgba(16,185,129,.22); }
.care-item.c-green strong { color: color-mix(in srgb, #34d399 65%, var(--text-primary)); }
.care-item.c-green:hover { box-shadow: 0 0 16px rgba(16,185,129,.25); }
.care-item.c-amber { background: linear-gradient(160deg, rgba(245,158,11,.15), rgba(245,158,11,.04)); border-color: rgba(245,158,11,.22); }
.care-item.c-amber strong { color: color-mix(in srgb, #fbbf24 70%, var(--text-primary)); }
.care-item.c-amber:hover { box-shadow: 0 0 16px rgba(245,158,11,.25); }

/* 使用日志 */
.log-summary {
  display: flex; flex-wrap: wrap; align-items: center; gap: 2px 6px;
  font-size: 11px; color: var(--text-muted);
}
.ls-item strong { color: color-mix(in srgb, #22d3ee 65%, var(--text-primary)); font-weight: 600; margin-right: 2px; }
.ls-dot { font-style: normal; color: var(--text-muted); opacity: .6; }
/* 通话记录内部滚动（2026-08-26 用户定稿：只有记录会增长，记录区滚、时段分布固定可见）
   弹性撑满：日志卡吸收右栏剩余空间，记录区随视口高低自适应多显示几条 */
/* 弹性撑满 + 可收缩（min-height:0 解除 flex 默认 min-height:auto，否则内容长时
   日志卡缩不下去、整栏溢出滚动 —— 2026-09-02 修复） */
.side-card.log-card { flex: 1 1 auto; min-height: 0; }
.call-history {
  display: flex; flex-direction: column; gap: 2px;
  flex: 1; min-height: 66px; overflow-y: auto;
}
.call-history::-webkit-scrollbar { width: 3px; }
.call-history::-webkit-scrollbar-thumb { background: rgba(128,128,128,.15); border-radius: 2px; }
.call-row {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 8px; border-radius: 8px; font-size: 11px;
  color: var(--text-secondary); transition: background .2s;
}
.call-row:hover { background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent); }
.call-row .fa-phone-alt { font-size: 9px; color: var(--text-muted); }
.call-dur { margin-left: auto; color: var(--text-muted); font-variant-numeric: tabular-nums; }
.call-empty {
  font-size: 11px; color: var(--text-muted); text-align: center;
  padding: 10px 8px; line-height: 1.8;
}
.time-buckets { display: flex; flex-direction: column; gap: 3px; }
.bucket-row { display: grid; grid-template-columns: 88px 1fr 22px; align-items: center; gap: 6px; }
.bucket-label { font-size: 10px; color: var(--text-muted); text-align: right; }
.bucket-bar { height: 4px; border-radius: 2px; background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent); overflow: hidden; }
.bucket-fill {
  height: 100%; border-radius: 3px;
  background: linear-gradient(90deg, #8b5cf6, #ec4899);
  box-shadow: 0 0 8px rgba(139,92,246,.5);
  transition: width .4s ease;
}
.bucket-num { font-size: 10px; color: var(--text-secondary); text-align: right; font-variant-numeric: tabular-nums; }

/* 寄语（小基气泡） */
.side-quote {
  margin-top: auto;
  display: flex; gap: 8px; align-items: flex-start;
}
.quote-avatar {
  width: 24px; height: 24px; border-radius: 50%; object-fit: contain;
  flex-shrink: 0; background: rgba(236,72,153,.10);
  box-shadow: 0 0 10px rgba(236,72,153,.3);
}
.quote-bubble {
  flex: 1; font-size: 12px; line-height: 1.6; color: var(--text-secondary);
  background: rgba(236,72,153,.05); border: 1px solid rgba(236,72,153,.12);
  border-radius: 4px 12px 12px 12px; padding: 6px 8px;
}
.quote-by { text-align: right; color: var(--text-muted); font-size: 9px; margin-top: 2px; }

@media (max-width: 1200px) {
  /* 窄屏只隐藏右栏（推荐/关心/日志），左栏导航必须保留（主页唯一导航） */
  .call-side.side-right { display: none; }
}

.call-nav {
  display: grid;
  grid-template-columns: 1fr auto 1fr;   /* 左右等宽：中间（名字+状态）真正居中 */
  align-items: center;
  padding: 10px 20px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  backdrop-filter: blur(12px);
}
.nav-back {
  font-size: 18px;
  color: var(--text-secondary) !important;
}
.nav-back:hover {
  color: var(--text-primary) !important;
}
.nav-center {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-self: center;
}
.nav-avatar-wrapper {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
}
.nav-avatar {
  width: 40px;
  height: 40px;
  border-radius: 0;
  object-fit: contain;
  display: block;
}
.nav-name {
  font-size: 15px;
  font-weight: 600;
}
.nav-status {
  font-size: 12px;
  color: var(--text-muted);
}
.nav-actions {
  display: flex;
  gap: 4px;
  justify-self: end;
}
.nav-action {
  font-size: 16px;
  color: var(--text-secondary) !important;
}
.nav-action:hover {
  color: var(--text-primary) !important;
}

/* ===== 搜索跳转高亮 ===== */
.roll-item.highlight {
  animation: msgHighlight 2.4s ease;
}
@keyframes msgHighlight {
  0%, 55% {
    background: rgba(255,193,7,0.22);
    box-shadow: 0 0 24px rgba(255,193,7,0.25);
  }
  100% {
    background: initial;
    box-shadow: initial;
  }
}

.xiaoji-area {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8px 0 2px;
  flex-shrink: 0;
}
.xiaoji-glow-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 160px;
  height: 160px;
  border-radius: 50%;
  background: radial-gradient(circle, color-mix(in srgb, var(--brand) 8%, transparent) 0%, transparent 70%);
  pointer-events: none;
  animation: glowPulse 3s ease-in-out infinite;
}
.xiaoji-glow-ring-2 {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 200px;
  height: 200px;
  border-radius: 50%;
  border: 1px solid color-mix(in srgb, var(--brand) 4%, transparent);
  pointer-events: none;
  animation: ringRotate 20s linear infinite;
}
@keyframes glowPulse {
  0%, 100% { opacity: 0.4; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 1; transform: translate(-50%, -50%) scale(1.05); }
}
@keyframes ringRotate {
  0% { transform: translate(-50%, -50%) rotate(0deg); }
  100% { transform: translate(-50%, -50%) rotate(360deg); }
}

.xiaoji-click-area {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  padding: 8px;
  border-radius: 20px;
  transition: all 0.3s ease;
  z-index: 2;
}
.xiaoji-click-area:hover .xiaoji-image {
  transform: scale(1.04) rotate(2deg);
  filter: drop-shadow(0 0 40px color-mix(in srgb, var(--brand) 25%, transparent));
}

.xiaoji-shadow {
  position: absolute;
  bottom: 4px;
  left: 50%;
  transform: translateX(-50%);
  width: 50%;
  height: 12px;
  border-radius: 50%;
  background: radial-gradient(ellipse, rgba(0,0,0,0.12) 0%, transparent 70%);
  pointer-events: none;
}
.xiaoji-image {
  width: 130px;
  height: 130px;
  object-fit: contain;
  display: block;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  filter: drop-shadow(0 4px 30px color-mix(in srgb, var(--brand) 8%, transparent));
}
.xiaoji-image.hover {
  transform: scale(1.04);
  filter: drop-shadow(0 0 50px color-mix(in srgb, var(--brand) 20%, transparent));
}

.xiaoji-status-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  margin-top: 2px;
}
.status-tag {
  font-size: 12px !important;
  font-weight: 500 !important;
}
.agent-progress {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  width: 100%;
  max-width: 200px;
}
.agent-progress-bar {
  width: 100%;
}
.agent-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}
.agent-desc {
  font-size: 11px;
  color: var(--text-muted);
}

.xiaoji-status-badge {
  font-size: 12px;
  color: var(--text-muted);
  background: rgba(128,128,128,0.06);
  padding: 2px 14px;
  border-radius: 10px;
  margin-top: 2px;
  backdrop-filter: blur(4px);
}

.xiaoji-dialog {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translate(-50%, -100%);
  background: color-mix(in srgb, var(--surface, #ffffff) 8%, transparent);
  backdrop-filter: blur(20px);
  border: 1px solid var(--line-soft);
  border-radius: 16px;
  padding: 8px 18px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  /* 多行换行 + 限宽：长回复能完整看完，不再被压成一行
     min-width 防止绝对定位在头像容器内收缩过窄（保证 ≥20 字/行） */
  white-space: normal;
  word-break: break-word;
  min-width: min(300px, 84vw);
  max-width: min(420px, 70vw);
  box-shadow: 0 8px 40px rgba(0,0,0,0.12);
  opacity: 0;
  transform-origin: bottom center;
  pointer-events: none;
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 10;
}
.xiaoji-dialog.pop {
  opacity: 1;
  transform: translate(-50%, calc(-100% - 12px));
}
/* 气泡模式：最新回复常驻（无弹跳动画，过长限高滚动） */
.xiaoji-dialog.persistent {
  opacity: 1;
  transform: translate(-50%, calc(-100% - 12px));
  max-height: 40vh;
  overflow-y: auto;
}

/* ===== 气泡模式：形象区放大占满（小基放大一倍）+ 我的最新一条 ===== */
.xiaoji-area.bubble-mode {
  flex: 1;
}
.xiaoji-area.bubble-mode .xiaoji-image {
  width: 260px;
  height: 260px;
}
.xiaoji-area.bubble-mode .xiaoji-glow-ring {
  width: 300px;
  height: 300px;
}
.xiaoji-area.bubble-mode .xiaoji-glow-ring-2 {
  width: 410px;
  height: 410px;
}
.xiaoji-user-bubble {
  max-width: min(420px, 70vw);
  margin-top: 14px;
  padding: 10px 16px;
  border-radius: 16px;
  background: color-mix(in srgb, var(--brand) 8%, transparent);
  border: 1px solid color-mix(in srgb, var(--brand) 12%, transparent);
  color: var(--text-primary);
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
  white-space: pre-wrap;
  z-index: 2;
}
.dialog-tail {
  position: absolute;
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%) rotate(45deg);
  width: 12px;
  height: 12px;
  background: color-mix(in srgb, var(--surface, #ffffff) 8%, transparent);
  border-right: 1px solid var(--line-soft);
  border-bottom: 1px solid var(--line-soft);
  backdrop-filter: blur(20px);
}

.chat-area-wrapper {
  flex: 1;
  display: flex;
  justify-content: center;
  padding: 0 24px;
  min-height: 0;
}

.chat-cylinder-wrapper {
  flex: 1;
  max-width: 800px;
  position: relative;
  padding: 4px 0;
  border-radius: 24px;
  background: radial-gradient(ellipse at center, color-mix(in srgb, var(--brand) 2%, transparent) 0%, transparent 80%);
  overflow: hidden;
}
.chat-cylinder-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80%;
  height: 60%;
  border-radius: 50%;
  background: radial-gradient(ellipse, color-mix(in srgb, var(--brand) 3%, transparent) 0%, transparent 70%);
  pointer-events: none;
}

.chat-roll {
  height: 100%;
  padding: 8px 16px 4px;
  overflow-y: auto;
  scroll-behavior: smooth;
}
.chat-roll::-webkit-scrollbar {
  width: 3px;
}
.chat-roll::-webkit-scrollbar-thumb {
  background: rgba(128,128,128,0.12);
  border-radius: 2px;
}

.roll-loading,
.roll-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-muted);
  font-size: 15px;
}
.roll-empty {
  opacity: 0.4;
}

.roll-messages {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 4px 0 8px;
  align-items: center;
  justify-content: flex-end;
  min-height: 100%;
}

.roll-load-more {
  align-self: center;
  font-size: 11px;
  color: var(--text-muted);
  padding: 2px 0 8px;
  opacity: 0.7;
}
.roll-load-more.clickable {
  cursor: pointer;
  color: var(--brand);
  opacity: 0.9;
  transition: opacity 0.2s;
}
.roll-load-more.clickable:hover {
  opacity: 1;
}

.roll-date-divider {
  align-self: center;
  font-size: 11px;
  color: var(--text-muted);
  background: rgba(128,128,128,0.08);
  padding: 2px 12px;
  border-radius: 10px;
  margin: 4px 0 2px;
  opacity: 0.8;
}

.roll-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 20px;
  border-radius: 16px;
  max-width: 70%;
  width: auto;
  transition: transform 0.1s ease, opacity 0.1s ease, filter 0.1s ease;
  transform-origin: center center;
  will-change: transform, opacity, filter;
  box-shadow: 0 2px 16px rgba(0,0,0,0.02);
}
.roll-item.user {
  align-self: flex-end;
  flex-direction: row-reverse;
  background: color-mix(in srgb, var(--brand) 8%, transparent);
  border: 1px solid color-mix(in srgb, var(--brand) 6%, transparent);
}
.roll-item.assistant {
  align-self: flex-start;
  background: rgba(128,128,128,0.03);
  border: 1px solid rgba(128,128,128,0.04);
}

.roll-avatar {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border-radius: 50%;
  overflow: hidden;
}
.user-avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}
.xiaoji-avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 0;
  object-fit: contain;
  display: block;
}

.roll-content {
  font-size: 17px;
  line-height: 1.7;
  word-break: break-word;
  flex: 1;
}
.roll-time {
  font-size: 11px;
  color: var(--text-muted);
  flex-shrink: 0;
  margin-top: 2px;
  align-self: flex-end;
}

/* ===== 图片样式 ===== */
.message-image {
  max-width: 200px;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  margin-bottom: 6px;
}
.message-image img {
  width: 100%;
  height: auto;
  display: block;
  max-height: 180px;
  object-fit: cover;
}

.message-card {
  padding: 12px 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255,255,255,0.06);
  min-width: 220px;
}
.message-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  border-color: color-mix(in srgb, var(--brand) 15%, transparent);
}

.question-card .card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.question-card .card-icon { font-size: 18px; }
.question-card .card-title { font-weight: 600; font-size: 15px; flex: 1; }
.question-card .card-badge {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--brand) 8%, transparent);
  color: var(--brand);
}
.question-card .card-difficulty-badge {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 10px;
  background: rgba(128,128,128,0.06);
  color: var(--text-muted);
}
.question-card .card-body {
  margin: 4px 0;
}
.question-card .card-question {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.6;
  margin-bottom: 4px;
}
.question-card .card-options {
  margin: 2px 0 4px;
  padding-left: 8px;
}
.question-card .card-option {
  font-size: 13px;
  color: var(--text-secondary);
  padding: 2px 0;
}
.question-card .card-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 4px;
}
.question-card .card-hint {
  font-size: 11px;
  color: var(--brand);
  opacity: 0.6;
}

.set-card .card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.set-card .card-icon { font-size: 18px; }
.set-card .card-title { font-weight: 600; font-size: 15px; flex: 1; }
.set-card .card-badge {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 10px;
  background: rgba(139,92,246,0.08);
  color: color-mix(in srgb, #8b5cf6 60%, var(--text-primary));
}
.set-card .card-body {
  margin: 6px 0 4px;
  color: var(--text-primary);
  font-size: 14px;
}
.set-card .card-footer {
  display: flex;
  justify-content: flex-end;
  font-size: 12px;
  color: var(--text-muted);
}
.set-card .card-hint {
  color: color-mix(in srgb, #8b5cf6 60%, var(--text-primary));
  opacity: 0.6;
}

/* ===== 计划卡 / 评估卡（2026-09-10 自动分流新增） ===== */
.plan-card .card-header,
.eval-card .card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.plan-card .card-icon,
.eval-card .card-icon { font-size: 18px; }
.plan-card .card-title,
.eval-card .card-title { font-weight: 600; font-size: 15px; flex: 1; }
.plan-card .card-badge,
.eval-card .card-badge {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--brand) 8%, transparent);
  color: var(--brand);
}
.plan-card .card-body,
.eval-card .card-body {
  margin: 8px 0 6px;
  color: var(--text-primary);
  font-size: 13px;
}
.plan-card .card-footer,
.eval-card .card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 4px;
}
.plan-card .card-hint,
.eval-card .card-hint {
  font-size: 11px;
  color: var(--text-muted);
}
.card-actions { display: flex; gap: 6px; }

/* 计划卡：参数行 + 草稿预览 */
.plan-fields { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.pf-input {
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
  padding: 5px 8px;
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
}
.pf-input:focus { border-color: color-mix(in srgb, var(--brand) 40%, transparent); }
.pf-input:disabled { opacity: 0.6; }
.pf-input.grow { flex: 1; min-width: 120px; }
.pf-input.num { width: 56px; text-align: center; }
.pf-unit { font-size: 12px; color: var(--text-muted); }
.plan-tip { margin-top: 6px; font-size: 12px; color: var(--text-muted); }
.plan-tip.err { color: #e8842c; }
.plan-day {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 0;
  font-size: 12.5px;
}
.pd-day {
  flex-shrink: 0;
  font-size: 11px;
  padding: 1px 7px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--brand) 10%, transparent);
  color: var(--brand);
}
.pd-topic {
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 评估卡：结论 + 归因 + 行动 */
.ev-summary { font-size: 13.5px; line-height: 1.6; color: var(--text-primary); }
.ev-row {
  display: flex;
  gap: 8px;
  margin-top: 6px;
  font-size: 12.5px;
  color: var(--text-secondary);
  line-height: 1.5;
}
.ev-k {
  flex-shrink: 0;
  height: fit-content;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 6px;
  color: var(--brand);
  background: color-mix(in srgb, var(--brand) 8%, transparent);
}
.ev-actions { margin-top: 8px; display: flex; flex-direction: column; gap: 4px; }
.ev-act { display: flex; gap: 7px; font-size: 12.5px; color: var(--text-secondary); }
.ev-i {
  flex-shrink: 0;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  font-size: 10px;
  color: var(--brand);
  background: color-mix(in srgb, var(--brand) 14%, transparent);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 输入区：自动识别状态 chip（2026-09-10，取代原「呼叫对象」下拉框） */
.mode-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  white-space: nowrap;
  color: var(--text-muted);
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent);
  border: 1px solid rgba(255,255,255,0.07);
  transition: all 0.25s ease;
}
.mode-chip.is-active {
  color: var(--mc);
  border-color: color-mix(in srgb, var(--mc) 45%, transparent);
  background: color-mix(in srgb, var(--mc) 12%, transparent);
}
.mode-chip .mc-text { font-weight: 600; }

.evaluation-content {
  width: 100%;
}
.eval-badge {
  font-size: 12px;
  font-weight: 600;
  color: color-mix(in srgb, #f59e0b 70%, var(--text-primary));
  background: rgba(245,158,11,0.08);
  padding: 2px 12px;
  border-radius: 10px;
  display: inline-block;
  margin-bottom: 6px;
}
.eval-text {
  font-size: 15px;
  line-height: 1.8;
  white-space: pre-wrap;
}

.typing-dots-inline {
  display: inline-flex;
  gap: 4px;
  align-items: center;
  padding: 0 4px;
}
.typing-dots-inline span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
  animation: typingBounce 1.4s infinite both;
}
.typing-dots-inline span:nth-child(1) { animation-delay: -0.32s; }
.typing-dots-inline span:nth-child(2) { animation-delay: -0.16s; }
.typing-dots-inline span:nth-child(3) { animation-delay: 0s; }
@keyframes typingBounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* 2026-09-03 用户拍板：输入区不做直线分割，改为独立圆角矩形框住；长度收缩、居中 */
.call-input-area {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 4px auto 12px;
  width: calc(100% - 40px);
  max-width: 820px;   /* 收缩：只比工具行 780px 略宽 */
  padding: 10px 14px 12px;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  backdrop-filter: blur(12px);
}
.input-tools {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 4px;
  width: 100%;
  max-width: 780px;
}
.tool-btn {
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 15px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}
.tool-btn:hover:not(.disabled) {
  background: rgba(128,128,128,0.06);
  color: var(--text-primary);
}
.tool-btn.active {
  color: var(--brand);
}
.tool-btn.disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
.tool-btn.recording {
  color: #f56c6c;
  animation: recordPulse 1.2s ease-in-out infinite;
}
@keyframes recordPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(245,108,108,0.35); }
  50% { box-shadow: 0 0 0 8px rgba(245,108,108,0); }
}
.tool-btn.stop-reading {
  color: #f56c6c;
  animation: recordPulse 1.5s ease-in-out infinite;
}

.input-row {
  display: flex;
  gap: 8px;
  width: 100%;
  max-width: 600px;
}
/* 词条卡（问词义 / 识图提词） */
.vocab-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  width: 100%;
  max-width: 600px;
  margin-bottom: 6px;
}
.chat-input {
  flex: 1;
}
.chat-input :deep(.el-input__wrapper) {
  background: rgba(128,128,128,0.03);
  border-color: var(--border-color);
  border-radius: 12px;
}
.chat-input :deep(.el-input-group__append) {
  background: color-mix(in srgb, var(--brand) 6%, transparent);
  border-color: var(--border-color);
  border-radius: 0 12px 12px 0;
}

.image-preview {
  position: relative;
  display: inline-block;
  margin-top: 4px;
  width: 100%;
  max-width: 600px;
}
.video-preview { display: flex; align-items: center; }
.video-preview-tag {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 12px; border-radius: 999px;
  font-size: 12px; color: var(--brand-bright, #7db8ff);
  background: color-mix(in srgb, var(--brand, #4d8dff) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--brand, #4d8dff) 30%, transparent);
}
.image-preview img {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  object-fit: cover;
}
.remove-image {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: none;
  background: rgba(239,68,68,0.9);
  color: #fff;
  cursor: pointer;
  font-size: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ===== 弹窗 ===== */
.custom-glass-dialog :deep(.el-dialog) {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent) !important;
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
  border-radius: 20px !important;
  box-shadow: 0 8px 40px rgba(0,0,0,0.08) !important;
}
[data-theme="dark"] .custom-glass-dialog :deep(.el-dialog) {
  background: var(--well) !important;
  border-color: rgba(255,255,255,0.04) !important;
}
.custom-glass-dialog :deep(.el-dialog__title) {
  color: var(--text-primary) !important;
  font-weight: 600 !important;
}
.custom-glass-dialog :deep(.el-dialog__body) {
  padding: 16px 24px 24px !important;
}
.custom-glass-dialog :deep(.el-dialog__header) {
  padding: 16px 24px 8px !important;
  border-bottom: 1px solid rgba(255,255,255,0.04) !important;
}
.custom-glass-dialog :deep(.el-dialog__headerbtn) {
  color: var(--text-secondary) !important;
}
.custom-glass-dialog :deep(.el-dialog__headerbtn:hover) {
  color: var(--text-primary) !important;
}

.custom-glass-tabs :deep(.el-tabs__header) {
  border-bottom: 1px solid rgba(255,255,255,0.04) !important;
}
.custom-glass-tabs :deep(.el-tabs__item) {
  color: var(--text-secondary) !important;
  font-size: 14px !important;
}
.custom-glass-tabs :deep(.el-tabs__item.is-active) {
  color: var(--text-primary) !important;
}
.custom-glass-tabs :deep(.el-tabs__item:hover) {
  color: var(--text-primary) !important;
}
.custom-glass-tabs :deep(.el-tabs__active-bar) {
  background: var(--brand) !important;
}

.preview-content {
  max-height: 400px;
  overflow-y: auto;
}

/* ===== 预览弹窗（蓝色） ===== */
.preview-question h4 {
  margin: 0 0 12px;
  color: var(--brand);
  font-size: 17px;
}
.preview-question p {
  margin: 6px 0;
  font-size: 14px;
  color: var(--brand);
  line-height: 1.7;
}
.preview-question p strong {
  color: var(--brand);
  font-weight: 600;
}
.option-item {
  padding: 4px 12px;
  margin: 2px 0;
  border-radius: 6px;
  background: color-mix(in srgb, var(--brand) 6%, transparent);
  font-size: 14px;
  color: var(--brand);
}
.code-block {
  background: rgba(0,0,0,0.06);
  padding: 12px;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  white-space: pre-wrap;
  overflow-x: auto;
  margin: 4px 0;
  color: var(--brand);
}

.preview-set p {
  margin: 6px 0;
  font-size: 14px;
  color: var(--text-secondary);
}
.preview-set p strong {
  color: var(--text-primary);
}

.set-questions-list {
  margin-top: 4px;
  padding: 6px 8px;
  border-radius: 8px;
  background: rgba(128,128,128,0.02);
  border: 1px solid var(--border-color);
  max-height: 200px;
  overflow-y: auto;
}

.loading-tip {
  text-align: center;
  padding: 12px 0;
  color: var(--text-muted);
  font-size: 13px;
}

.set-question-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 1px solid rgba(128,128,128,0.04);
}
.set-question-item:hover {
  background: color-mix(in srgb, var(--brand) 4%, transparent);
}
.set-question-item:last-child {
  border-bottom: none;
}
.sq-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.sq-title {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 500;
}
.sq-preview {
  font-size: 12px;
  color: var(--text-muted);
  opacity: 0.7;
}
.sq-type {
  font-size: 11px;
  color: var(--text-muted);
  padding: 0 8px;
  border-radius: 4px;
  background: rgba(128,128,128,0.04);
}

.question-dialog {
  max-height: 420px;
  overflow-y: auto;
}
/* ===== 题库搜索（发送题目） ===== */
.bank-search-row {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}
.bank-search-input {
  flex: 1;
}
.bank-results {
  min-height: 120px;
  max-height: 300px;
  overflow-y: auto;
}
.bank-results::-webkit-scrollbar { width: 3px; }
.bank-results::-webkit-scrollbar-thumb {
  background: rgba(128,128,128,0.12);
  border-radius: 2px;
}
.q-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.q-meta {
  font-size: 11px;
  color: var(--text-muted);
}
.question-dialog::-webkit-scrollbar {
  width: 3px;
}
.question-dialog::-webkit-scrollbar-thumb {
  background: rgba(128,128,128,0.12);
  border-radius: 2px;
}

.question-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid var(--border-color);
  margin-bottom: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
}
.question-item:hover {
  background: color-mix(in srgb, var(--brand) 4%, transparent);
  border-color: color-mix(in srgb, var(--brand) 12%, transparent);
}
.q-title {
  flex: 1;
  font-size: 14px;
  color: var(--brand);
}
.q-type {
  font-size: 12px;
  color: var(--text-muted);
  margin: 0 12px;
}

/* ===== 题集弹窗（蓝色） ===== */
.set-item-wrapper {
  margin-bottom: 6px;
}
.set-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.3s ease;
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
}
.set-item:hover {
  background: rgba(139,92,246,0.04);
  border-color: rgba(139,92,246,0.12);
}
.set-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}
.set-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--brand);
}
.set-count {
  font-size: 12px;
  color: var(--text-muted);
}
.set-expand-icon {
  transition: transform 0.3s ease;
  color: var(--text-muted);
  font-size: 14px;
}
.set-expand-icon.expanded {
  transform: rotate(180deg);
}

.empty-tip {
  text-align: center;
  color: var(--text-muted);
  padding: 30px 0;
}

.image-preview-dialog :deep(.el-dialog) {
  background: rgba(0,0,0,0.8) !important;
  border: none !important;
}
.image-preview-dialog :deep(.el-dialog__body) {
  padding: 0 !important;
}
.preview-image {
  width: 100%;
  max-height: 80vh;
  object-fit: contain;
}

[data-theme="dark"] .xiaoji-call-page {
  background: rgba(0,0,0,0.06);
}
[data-theme="dark"] .roll-item.user {
  background: color-mix(in srgb, var(--brand) 6%, transparent);
}
[data-theme="dark"] .xiaoji-dialog {
  background: var(--well);
}
[data-theme="dark"] .chat-cylinder-wrapper {
  background: radial-gradient(ellipse at center, color-mix(in srgb, var(--brand) 2%, transparent) 0%, transparent 80%);
}
[data-theme="dark"] .message-card {
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
  border-color: rgba(255,255,255,0.04);
}
[data-theme="dark"] .call-nav {
  background: var(--well);
}
[data-theme="dark"] .call-input-area {
  background: rgba(0,0,0,0.15);
}
[data-theme="dark"] .question-item {
  border-color: rgba(255,255,255,0.04);
}
[data-theme="dark"] .question-item:hover {
  background: color-mix(in srgb, var(--brand) 4%, transparent);
}
[data-theme="dark"] .set-item {
  border-color: rgba(255,255,255,0.04);
}
[data-theme="dark"] .set-item:hover {
  background: rgba(139,92,246,0.04);
}
[data-theme="dark"] .set-questions-list {
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
  border-color: rgba(255,255,255,0.04);
}
[data-theme="dark"] .set-name {
  color: var(--brand-bright);
}
[data-theme="dark"] .q-title {
  color: var(--brand-bright);
}
[data-theme="dark"] .preview-question h4 {
  color: var(--brand-bright);
}
[data-theme="dark"] .preview-question p {
  color: var(--brand-bright);
}
[data-theme="dark"] .preview-question p strong {
  color: var(--brand-bright);
}
[data-theme="dark"] .option-item {
  color: var(--brand-bright);
  background: color-mix(in srgb, var(--brand) 8%, transparent);
}
[data-theme="dark"] .code-block {
  color: var(--brand-bright);
}
[data-theme="dark"] .sq-title {
  color: rgba(255,255,255,0.8);
}

@media (max-width: 640px) {
  .call-nav {
    padding: 8px 14px;
  }
  .xiaoji-image {
    width: 96px;
    height: 96px;
  }
  .xiaoji-area.bubble-mode .xiaoji-image {
    width: 170px;
    height: 170px;
  }
  .xiaoji-area.bubble-mode .xiaoji-glow-ring {
    width: 210px;
    height: 210px;
  }
  .xiaoji-area.bubble-mode .xiaoji-glow-ring-2 {
    width: 290px;
    height: 290px;
  }
  .xiaoji-glow-ring {
    width: 120px;
    height: 120px;
  }
  .xiaoji-glow-ring-2 {
    width: 150px;
    height: 150px;
  }
  .chat-area-wrapper {
    padding: 0 12px;
  }
  .chat-cylinder-wrapper {
    border-radius: 16px;
  }
  .chat-roll {
    padding: 6px 10px 2px;
  }
  .roll-item {
    max-width: 82%;
    padding: 8px 14px;
    gap: 8px;
  }
  .roll-content {
    font-size: 15px;
  }
  .roll-avatar {
    width: 32px;
    height: 32px;
  }
  .call-input-area {
    padding: 6px 14px 10px;
  }
  .input-tools {
    max-width: 100%;
  }
  .input-row {
    max-width: 100%;
  }
  .xiaoji-dialog {
    font-size: 12px;
    padding: 4px 12px;
  }
  .message-card {
    min-width: 160px;
    padding: 8px 12px;
  }
  .question-dialog {
    max-height: 320px;
  }
  .custom-glass-dialog :deep(.el-dialog) {
    width: 92% !important;
    margin: 0 auto !important;
  }
  .message-image {
    max-width: 140px;
  }
}

/* 原「呼叫对象」下拉样式已随手动选角色一并移除（2026-09-10 改自动判别，见 .mode-chip） */

/* 列表消息署名徽章：是谁的产出，一眼可见 */
.agent-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px 3px 5px;
  margin-bottom: 7px;
  border-radius: 14px;
  font-size: 11px;
  color: var(--text-secondary);
  background: color-mix(in srgb, var(--fc) 13%, transparent);
  border: 1px solid color-mix(in srgb, var(--fc) 40%, transparent);
}
.agent-badge-img { width: 18px; height: 18px; border-radius: 50%; object-fit: cover; }
.agent-badge-name { font-weight: 700; color: var(--fc); }
.agent-badge-tag { opacity: .75; }

/* 气泡模式下的队员徽章 */
.bubble-agent-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 6px;
  padding: 2px 9px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 700;
  color: var(--fc);
  background: color-mix(in srgb, var(--fc) 14%, transparent);
  border: 1px solid color-mix(in srgb, var(--fc) 45%, transparent);
}
.bubble-agent-badge img { width: 16px; height: 16px; border-radius: 50%; object-fit: cover; }

/* ===== 聊天行动卡（2026-08-27）：题目卡行动条 / 题库检索 / 代码沙箱卡 / 出题表单 ===== */
.card-actions {
  display: inline-flex;
  gap: 6px;
}
.card-act {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 8px;
  border: 1px solid var(--line-soft);
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent);
  color: var(--text-secondary);
  font-size: 11px;
  cursor: pointer;
  font-family: inherit;
  transition: all .2s ease;
}
.card-act:hover {
  color: var(--text-primary);
  background: color-mix(in srgb, var(--surface, #ffffff) 12%, transparent);
  border-color: var(--line);
}
[data-theme='light'] .card-act {
  border-color: rgba(0,0,0,.10);
  background: rgba(0,0,0,.04);
  color: var(--text-secondary);
}
/* 选题依据（2026-09-02 生成 Agent 出题卡） */
.picked-note {
  margin: 8px 12px 0;
  font-size: 11px;
  color: var(--text-muted);
  text-align: left;
}
/* 队员行动条（2026-09-02 计划/评估 Agent 回复跳转入口） */
.agent-actions {
  margin-top: 6px;
  display: flex;
  gap: 8px;
}
.agent-actions a {
  font-size: 11px;
  color: var(--text-secondary);
  text-decoration: none;
  padding: 4px 10px;
  border-radius: 10px;
  border: 1px solid var(--line-soft);
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  transition: all .25s ease;
}
.agent-actions a:hover {
  color: var(--brand);
  border-color: color-mix(in srgb, var(--brand) 35%, transparent);
  background: color-mix(in srgb, var(--brand) 8%, transparent);
}

.bank-match {
  margin-top: 6px;
  border-top: 1px dashed var(--line-soft);
  padding-top: 6px;
}
.bank-match-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background .2s ease;
  font-size: 12px;
}
.bank-match-item:hover { background: color-mix(in srgb, var(--surface, #ffffff) 8%, transparent); }
.bm-badge {
  flex-shrink: 0;
  padding: 2px 7px;
  border-radius: 6px;
  font-size: 10px;
  color: color-mix(in srgb, #7cc9ff 60%, var(--text-primary));
  background: color-mix(in srgb, var(--brand) 16%, transparent);
  border: 1px solid color-mix(in srgb, var(--brand) 30%, transparent);
}
.bm-title {
  flex: 1;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.bm-type { flex-shrink: 0; font-size: 10px; color: var(--text-muted); }
.bank-match-tip { font-size: 11px; color: var(--text-muted); padding: 4px 2px; }

.msg-text-seg { white-space: pre-wrap; }
.code-card {
  margin: 8px 0;
  border: 1px solid rgba(255,255,255,.10);
  border-radius: 10px;
  background: rgba(0,0,0,.28);
  overflow: hidden;
}
[data-theme='light'] .code-card {
  background: rgba(0,0,0,.045);
  border-color: rgba(0,0,0,.10);
}
.code-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  border-bottom: 1px solid rgba(255,255,255,.08);
}
.code-lang { font-size: 11px; color: var(--text-secondary); }
.code-lang i { margin-right: 4px; color: #6bcb77; }
.code-run-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: 7px;
  border: 1px solid rgba(107,203,119,.45);
  background: rgba(107,203,119,.12);
  color: #6bcb77;
  font-size: 11px;
  cursor: pointer;
  font-family: inherit;
  transition: all .2s ease;
}
.code-run-btn:hover:not(:disabled) { background: rgba(107,203,119,.22); }
.code-run-btn:disabled { opacity: .6; cursor: not-allowed; }
.code-block {
  margin: 0;
  padding: 10px 12px;
  font-family: 'Cascadia Code', 'Fira Code', 'JetBrains Mono', Consolas, monospace;
  font-size: 12px;
  line-height: 1.55;
  color: #d7e3f4;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 320px;
  overflow: auto;
}
[data-theme='light'] .code-block { color: #33415c; }
.code-run-box {
  border-top: 1px solid rgba(255,255,255,.08);
  background: rgba(0,0,0,.2);
  padding: 8px 10px;
}
.code-run-input-row { display: flex; gap: 6px; margin-bottom: 6px; }
.code-run-input {
  flex: 1;
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px solid rgba(255,255,255,.12);
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent);
  color: var(--text-primary);
  font-size: 11px;
  font-family: monospace;
  outline: none;
}
.code-act {
  padding: 3px 10px;
  border-radius: 6px;
  border: 1px solid rgba(255,255,255,.14);
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent);
  color: var(--text-secondary);
  font-size: 11px;
  cursor: pointer;
  font-family: inherit;
}
.code-run-output {
  margin: 0;
  padding: 7px 9px;
  border-radius: 6px;
  background: #0e1420;
  border: 1px solid rgba(255,255,255,.06);
  color: #8fd6a0;
  font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace;
  font-size: 11px;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 180px;
  overflow: auto;
}
[data-theme='light'] .code-run-output {
  background: #f2f4f8;
  border-color: rgba(0,0,0,.08);
  color: #2e7d4f;
}

.gen-form { display: flex; flex-direction: column; gap: 12px; }
.gen-row { display: flex; align-items: center; gap: 10px; }
.gen-row label { width: 56px; font-size: 13px; color: var(--text-secondary); flex-shrink: 0; }
.gen-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 4px; }
</style>