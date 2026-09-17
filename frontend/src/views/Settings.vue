<template>
  <div class="settings-page">
    <!-- Toast -->
    <Teleport to="body">
      <TransitionGroup name="toast" tag="div" class="toast-stack">
        <div v-for="t in toasts" :key="t.id" :class="['toast-item', 'toast-' + t.type]">
          <span class="toast-icon">{{ t.type === 'success' ? '✓' : t.type === 'error' ? '✕' : '!' }}</span>
          <span class="toast-msg">{{ t.msg }}</span>
        </div>
      </TransitionGroup>
    </Teleport>

    <!-- 顶部 -->
    <div class="settings-topbar">
      <button class="glass-btn back-btn" @click="$router.push('/')">
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        返回主界面
      </button>
      <h1>⚙ 设置</h1>
    </div>

    <div class="settings-container">
      <!-- ====== 1. 个人信息 ====== -->
      <div class="settings-card">
        <div class="card-header">
          <span class="card-icon">👤</span>
          <span class="card-title">个人信息</span>
        </div>
        <div class="card-body">
          <div class="field">
            <label class="field-label">昵称</label>
            <div class="field-row">
              <input class="glass-input" v-model="form.nickname" placeholder="请输入昵称" />
              <button class="glass-btn primary" @click="saveNickname">保存</button>
            </div>
          </div>
          <div class="field">
            <label class="field-label">个人简介</label>
            <textarea class="glass-input textarea" v-model="form.bio" rows="2" placeholder="介绍一下自己..."></textarea>
            <button class="glass-btn primary" style="margin-top:8px" @click="saveBio">保存简介</button>
          </div>
          <div class="field">
            <label class="field-label">头像</label>
            <div class="avatar-row">
              <div class="avatar-ring">
                <img v-if="user?.avatar_url" :src="user.avatar_url" class="avatar-img" />
                <span v-else class="avatar-placeholder">{{ user?.nickname?.[0] || 'U' }}</span>
              </div>
              <label class="glass-btn primary small">
                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/>
                  <path d="M12 11v6M9 14l3-3 3 3"/>
                </svg>
                更换头像
                <input type="file" accept="image/*" @change="handleAvatarUpload" style="display:none" />
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- ====== 2. 学习偏好 ====== -->
      <div class="settings-card">
        <div class="card-header">
          <span class="card-icon">🎯</span>
          <span class="card-title">学习偏好</span>
          <span class="card-hint">帮助基智提供更精准的学习建议</span>
        </div>
        <div class="card-body prefs-grid">
          <div class="pref-field">
            <label class="field-label">学习阶段</label>
            <select class="glass-input" v-model="form.learning_stage" @change="onStageChange">
              <option value="">未设置</option>
              <option v-for="o in stageOptions" :key="o" :value="o">{{ o }}</option>
            </select>
          </div>
          <div class="pref-field">
            <label class="field-label">年级</label>
            <select class="glass-input" v-model="form.grade">
              <option value="">未设置</option>
              <option v-for="o in gradeOptions" :key="o" :value="o">{{ o }}</option>
            </select>
          </div>
          <div class="pref-field">
            <label class="field-label">专业/方向</label>
            <input class="glass-input" v-model="form.major" placeholder="如：计算机科学" list="major-list" />
            <datalist id="major-list">
              <option v-for="m in majorOptions" :key="m" :value="m" />
            </datalist>
          </div>
          <div class="pref-field">
            <label class="field-label">学习目标</label>
            <select class="glass-input" v-model="form.learning_goal">
              <option value="">未设置</option>
              <option v-for="o in goalOptions" :key="o" :value="o">{{ o }}</option>
            </select>
          </div>
          <div class="pref-field">
            <label class="field-label">题目难度</label>
            <select class="glass-input" v-model="form.difficulty_preference">
              <option value="">未设置</option>
              <option v-for="o in difficultyOptions" :key="o" :value="o">{{ o }}</option>
            </select>
          </div>
          <div class="pref-field">
            <label class="field-label">讲解方式</label>
            <select class="glass-input" v-model="form.learning_style">
              <option value="">未设置</option>
              <option v-for="o in styleOptions" :key="o" :value="o">{{ o }}</option>
            </select>
          </div>
          <div class="pref-field">
            <label class="field-label">每日学习时长</label>
            <select class="glass-input" v-model="form.daily_study_time">
              <option value="">未设置</option>
              <option v-for="o in timeOptions" :key="o" :value="o">{{ o }}</option>
            </select>
          </div>
        </div>
        <div class="card-footer">
          <button class="glass-btn primary" :disabled="savingPrefs" @click="savePreferences">
            {{ savingPrefs ? '保存中...' : '保存学习偏好' }}
          </button>
        </div>
      </div>

      <!-- ====== 3. 外观 ====== -->
      <div class="settings-card">
        <div class="card-header">
          <span class="card-icon">🎨</span>
          <span class="card-title">外观</span>
        </div>
        <div class="card-body">
          <!-- 主题定制（09-03 用户拍板：去掉浅/深/跟随系统开关，外观只有四轴定制——
               背景色 + 组件色 + 主题色 + 字体色，默认方案 = 深空蓝四轴，全站生效 + 账号同步） -->
          <div class="theme-custom">
            <!-- 整套方案 -->
            <div class="tc-section">
              <div class="tc-title">预设一套（背景 + 组件 + 主题 + 字体一键换好）</div>
              <div class="tc-sets">
                <span
                  v-for="t in themeSets" :key="t.key"
                  class="tc-set"
                  :class="{ active: isSetActive(t) }"
                  @click="applySet(t)"
                  :title="`${t.name}：背景 ${t.bg} / 组件 ${t.surface} / 主题 ${t.brand} / 字体 ${t.scheme}`"
                >
                  <span class="tc-set-tile" :style="{ background: t.bg }">
                    <i class="tc-set-surface" :style="{ background: t.surface }"></i>
                    <i class="tc-set-brand" :style="{ background: t.brand }"></i>
                    <i class="tc-set-ink" :style="{ background: (FONT_SCHEMES[t.scheme] || {}).primary || '#e8e8f0' }"></i>
                  </span>
                  <small>{{ t.name }}</small>
                </span>
              </div>
            </div>

            <!-- 背景色 -->
            <div class="tc-section">
              <div class="tc-title">背景色（页面底色，氛围自动派生）</div>
              <div class="tc-colors">
                <template v-for="c in bgPresets.light" :key="'l' + c">
                  <span class="tc-swatch" :class="{ active: isBg(c) }" :style="{ background: c }" @click="chooseBg(c)" :title="c"></span>
                </template>
                <template v-for="c in bgPresets.dark" :key="'d' + c">
                  <span class="tc-swatch" :class="{ active: isBg(c) }" :style="{ background: c }" @click="chooseBg(c)" :title="c"></span>
                </template>
                <el-color-picker v-model="bgPick" size="small" @change="chooseBg" title="高级选色（自由取色）" />
              </div>
            </div>

            <!-- 组件色 -->
            <div class="tc-section">
              <div class="tc-title">组件色（毛玻璃卡片 / 输入框 / 浮层）</div>
              <div class="tc-colors">
                <template v-for="c in surfacePresets.light" :key="'sl' + c">
                  <span class="tc-swatch" :class="{ active: isSurface(c) }" :style="{ background: c }" @click="chooseSurface(c)" :title="c"></span>
                </template>
                <template v-for="c in surfacePresets.dark" :key="'sd' + c">
                  <span class="tc-swatch" :class="{ active: isSurface(c) }" :style="{ background: c }" @click="chooseSurface(c)" :title="c"></span>
                </template>
                <el-color-picker v-model="surfacePick" size="small" @change="chooseSurface" title="高级选色（自由取色）" />
              </div>
            </div>

            <!-- 主题色 -->
            <div class="tc-section">
              <div class="tc-title">主题色（按钮 / 链接 / 选中态 / 发光）</div>
              <div class="tc-colors">
                <span
                  v-for="c in brandPresets" :key="c"
                  class="tc-swatch"
                  :class="{ active: themeStore.brandColor.toLowerCase() === c.toLowerCase() }"
                  :style="{ background: c }"
                  @click="chooseBrand(c)"
                  :title="c"
                ></span>
                <el-color-picker v-model="brandPick" size="small" @change="chooseBrand" title="高级选色（自由取色）" />
              </div>
            </div>

            <!-- 字体色 -->
            <div class="tc-section">
              <div class="tc-title">字体色（主 / 次 / 弱三档文字）</div>
              <div class="tc-schemes">
                <span
                  v-for="s in schemeOptions" :key="s.key"
                  class="tc-scheme"
                  :class="{ active: themeStore.textScheme === s.key }"
                  @click="chooseScheme(s.key)"
                >
                  <span v-if="s.colors" class="tc-dots">
                    <i :style="{ background: s.colors.primary }"></i>
                    <i :style="{ background: s.colors.secondary }"></i>
                    <i :style="{ background: s.colors.muted }"></i>
                  </span>
                  <i v-else class="tc-dot-def"></i>
                  {{ s.label }}
                </span>
                <span class="tc-scheme" :class="{ active: isCustomText }" @click="chooseScheme('custom')">自定义（高级）</span>
              </div>

              <div v-if="isCustomText" class="tc-custom">
                <div v-for="k in [['primary','主文字'],['secondary','次文字'],['muted','弱文字']]" :key="k[0]" class="tc-pick-row">
                  <span class="tc-pick-label">{{ k[1] }}</span>
                  <el-color-picker v-model="textPick[k[0]]" size="small" @change="applyCustomText" title="高级选色（自由取色）" />
                </div>
              </div>
            </div>

            <!-- 实时预览 + 适配度 -->
            <div class="tc-section tc-fit">
              <div class="tc-fit-head">
                <span class="tc-title">实时预览（嵌入小页面 · 四色联动）</span>
                <span class="tc-pv-score-wrap">适配度 <b :class="fit.cls">{{ fit.pct }}%</b></span>
              </div>

              <!-- 小页面预览窗（2026-09-03 升级 / 2026-09-04 抽成组件供外观码复用） -->
              <ThemePreviewWindow :bg="effectiveBg" :surface="effectiveSurface" :brand="themeStore.brandColor" :text="effectiveText" />

              <div class="tc-fit-bar"><i :class="fit.cls" :style="{ width: fit.pct + '%' }"></i></div>
              <div class="tc-fit-checks">
                <div v-for="c in fit.checks" :key="c.key" class="tc-fit-row" :class="c.cls">
                  <i class="tc-fit-dot" :class="c.cls"></i>
                  <span class="tc-fit-label">{{ c.label }}</span>
                  <span class="tc-fit-val">{{ c.ratio }}:1</span>
                  <span v-if="c.advice" class="tc-fit-advice">{{ c.advice }}</span>
                </div>
              </div>
              <div class="tc-fit-summary" :class="fit.cls">{{ fit.summary }}</div>
              <div v-if="fit.canAutoFix" class="tc-fit-fix">
                <el-button size="small" @click="autoFixText">✨ 自动调整字体色</el-button>
              </div>
            </div>

            <div class="tc-actions">
              <el-button size="small" type="primary" :loading="savingTheme" @click="saveTheme">保存到账号</el-button>
              <el-button size="small" @click="resetTheme">恢复默认</el-button>
            </div>

            <!-- 外观码（2026-09-04：四轴打包成可分享码——码本身就是色值，可读可手改） -->
            <div class="tc-section tc-share">
              <div class="tc-title">📤 分享外观 · 外观码</div>
              <div class="tc-share-desc">
                把背景 / 组件 / 主题 / 字体整套打包成「外观码」，好友粘贴就能一键复刻你的外观；
                当前外观{{ appearanceCode.setName ? ` = 「${appearanceCode.setName}」套装` : '' }}
              </div>
              <div class="tc-share-code" @click="copyCode" :title="'点击复制\n' + appearanceCode.code">
                <span class="tc-share-dots">
                  <i :style="{ background: themeStore.bgColor }"></i>
                  <i :style="{ background: themeStore.surfaceColor }"></i>
                  <i :style="{ background: themeStore.brandColor }"></i>
                  <i :style="{ background: effectiveText.primary }"></i>
                </span>
                <code>{{ appearanceCode.code }}</code>
              </div>
              <div class="tc-actions">
                <el-button size="small" @click="copyCode">📋 复制外观码</el-button>
                <el-button size="small" @click="copyLink">🔗 复制分享链接</el-button>
                <el-button size="small" @click="openImport">📥 粘贴导入</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 导入外观码弹窗 -->
      <el-dialog v-model="importVisible" title="📥 导入外观码" width="560px" class="tc-import-dialog" destroy-on-close>
        <div class="tc-import">
          <textarea
            v-model="importText"
            class="tc-import-input"
            rows="2"
            placeholder="粘贴好友发来的外观码，例如：JZ1-space 或 JZ1-0d1220-16233c-409eff-paper-CK2F8"></textarea>
          <div v-if="importText.trim() && importResult && !importResult.ok" class="tc-import-err">
            ⚠️ {{ importResult.error }}
          </div>
          <template v-if="importOk">
            <div class="tc-import-head">
              <span v-if="importResult.setName" class="tc-import-tag">「{{ importResult.setName }}」套装</span>
              <span class="tc-import-score" :class="importFit.cls">适配度 {{ importFit.pct }}%</span>
            </div>
            <ThemePreviewWindow
              :bg="importResult.payload.bg"
              :surface="importResult.payload.surface"
              :brand="importResult.payload.brand"
              :text="importTextResolved" />
            <div v-if="importFit.cls === 'bad'" class="tc-import-warn">
              ⚠️ 这份外观对比度不足，应用后文字可能看不清，建议确认后再应用
            </div>
          </template>
        </div>
        <template #footer>
          <el-button size="small" @click="importVisible = false">取消</el-button>
          <el-button size="small" type="primary" :disabled="!importOk" @click="applyImport">应用外观</el-button>
        </template>
      </el-dialog>

      <!-- ====== 4. 隐私 ====== -->
      <div class="settings-card">
        <div class="card-header">
          <span class="card-icon">🔒</span>
          <span class="card-title">隐私</span>
        </div>
        <div class="card-body">
          <div class="toggle-group">
            <div
              v-for="opt in statusOptions" :key="opt.value"
              class="toggle-card"
              :class="{ active: userStatus === opt.value }"
              @click="changeStatus(opt.value)"
            >
              <span class="toggle-icon">{{ opt.icon }}</span>
              <span class="toggle-label">{{ opt.label }}</span>
              <span class="toggle-desc">{{ opt.desc }}</span>
              <span class="toggle-check" v-if="userStatus === opt.value">✓</span>
            </div>
          </div>
        </div>
      </div>

      <!-- ====== 5. 通知设置 ====== -->
      <div class="settings-card">
        <div class="card-header">
          <span class="card-icon">🔔</span>
          <span class="card-title">通知设置</span>
        </div>
        <div class="card-body">
          <div class="notif-grid">
            <div v-for="item in notifItems" :key="item.key" class="notif-row">
              <div class="notif-info">
                <span class="notif-label">{{ item.label }}</span>
                <span class="notif-desc">{{ item.desc }}</span>
              </div>
              <label class="switch">
                <input type="checkbox" v-model="notifSettings[item.key]" @change="saveNotifSettings" />
                <span class="switch-slider"></span>
              </label>
            </div>
          </div>
          <div class="notif-time-row">
            <div class="notif-time-field">
              <label class="field-label">每日推荐时间</label>
              <input type="time" class="glass-input" v-model="notifSettings.daily_rec_time" @change="saveNotifSettings" style="width:160px" />
            </div>
            <div class="notif-time-field">
              <label class="field-label">每日总结时间</label>
              <input type="time" class="glass-input" v-model="notifSettings.daily_summary_time" @change="saveNotifSettings" style="width:160px" />
            </div>
          </div>
        </div>
      </div>

      <!-- ====== 6. 账号安全 ====== -->
      <div class="settings-card">
        <div class="card-header">
          <span class="card-icon">🔐</span>
          <span class="card-title">账号安全</span>
        </div>
        <div class="card-body">
          <!-- 修改密码 -->
          <div class="field">
            <label class="field-label">修改密码</label>
            <div class="pw-fields">
              <input class="glass-input" v-model="pw.old" type="password" placeholder="当前密码" />
              <input class="glass-input" v-model="pw.new1" type="password" placeholder="新密码（至少6位）" />
              <input class="glass-input" v-model="pw.new2" type="password" placeholder="确认新密码" />
            </div>
            <button class="glass-btn warning" style="margin-top:10px" :disabled="changingPw" @click="changePassword">
              {{ changingPw ? '修改中...' : '修改密码' }}
            </button>
          </div>

          <div class="divider"></div>

          <!-- 微信绑定 -->
          <div class="field">
            <label class="field-label">微信绑定</label>
            <div v-if="user?.wechat_openid" class="wechat-bound">
              <i class="fab fa-weixin" style="color:#07c160;font-size:20px"></i>
              <span>已绑定微信</span>
            </div>
            <template v-else>
              <button v-if="!wechat.qrcode" class="glass-btn wechat-btn" :disabled="wechat.loading" @click="startWechatBind">
                <i class="fab fa-weixin"></i> {{ wechat.loading ? '获取中...' : '绑定微信' }}
              </button>
              <div v-if="wechat.qrcode" class="wechat-panel">
                <img :src="wechat.qrcode" class="wechat-qr" alt="微信扫码" />
                <p class="wechat-tip">{{ wechat.status }}</p>
                <button class="glass-btn small" @click="cancelWechatBind">取消</button>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- ====== 7. AI 与 API ====== -->
      <div class="settings-card">
        <div class="card-header">
          <img src="/images/xiaoji/xiaoji_idle.png" alt="小基" class="xiaoji-section-icon" />
          <span class="card-title">AI 与 API</span>
        </div>
        <div class="card-body">
          <div class="link-grid">
            <router-link to="/xiaoji/settings" class="link-card">
              <img src="/images/xiaoji/xiaoji_idle.png" alt="小基" class="link-icon-img" />
              <span class="link-label">小基 AI 设置</span>
              <span class="link-desc">AI 助手名称、语音、性格</span>
              <svg class="link-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
            </router-link>
            <router-link to="/api-center" class="link-card">
              <span class="link-icon">🔑</span>
              <span class="link-label">API 管理中心</span>
              <span class="link-desc">管理第三方 API 密钥</span>
              <svg class="link-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
            </router-link>
          </div>
        </div>
      </div>

      <!-- ====== 8. 关于 ====== -->
      <div class="settings-card">
        <div class="card-header">
          <span class="card-icon">ℹ️</span>
          <span class="card-title">关于</span>
          <span class="card-hint">基智学习助手</span>
        </div>
        <div class="card-body">
          <div class="about-version">
            <span class="about-label">当前版本</span>
            <span class="about-ver">v{{ appVersion }} <em class="about-tag">Beta</em></span>
          </div>
          <div class="about-version">
            <span class="about-label">ICP 备案</span>
            <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener" class="about-ver about-icp-link">粤ICP备2026109012号-2</a>
          </div>
          <div class="link-grid about-links">
            <router-link to="/guide" class="link-card">
              <span class="link-icon">📖</span>
              <span class="link-label">使用指引</span>
              <span class="link-desc">产品使用说明书</span>
              <svg class="link-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
            </router-link>
            <router-link to="/qa" class="link-card">
              <span class="link-icon">❓</span>
              <span class="link-label">帮助中心</span>
              <span class="link-desc">常见问题与提问</span>
              <svg class="link-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
            </router-link>
            <router-link to="/open-source" class="link-card">
              <span class="link-icon">📚</span>
              <span class="link-label">开源文档</span>
              <span class="link-desc">技术架构与开源说明</span>
              <svg class="link-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
            </router-link>
          </div>
        </div>
      </div>

      <!-- 底部间距 -->
      <div style="height:40px"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore, BRAND_PRESETS, BG_PRESETS, SURFACE_PRESETS, FONT_SCHEMES, THEME_SETS, luminance, resolveText, computeFit } from '@/stores/theme'
import { encodeAppearance, decodeAppearance, appearanceLink } from '@/utils/appearanceCode'
import ThemePreviewWindow from '@/components/ThemePreviewWindow.vue'
import { setUser } from '@/utils/storage'
import { updateNickname, updateBio, uploadAvatar, updateUserTheme } from '@/api/auth'
import { getNotificationSettings, updateNotificationSettings } from '@/api/community'
import { recordAction } from '@/api/career'
import pkg from '../../package.json'

const authStore = useAuthStore()
const themeStore = useThemeStore()

const appVersion = pkg.version

const user = computed(() => authStore.user)
const userStatus = ref(authStore.user?.status || 'online')
const savingPrefs = ref(false)
const changingPw = ref(false)

// ===== Form =====
const form = reactive({
  nickname: '',
  bio: '',
  learning_stage: '',
  grade: '',
  major: '',
  learning_goal: '',
  difficulty_preference: '',
  learning_style: '',
  daily_study_time: '',
})

// ===== Password =====
const pw = reactive({ old: '', new1: '', new2: '' })

// ===== Toast =====
const toasts = ref([])
let toastId = 0
function toast(msg, type = 'success') {
  const id = ++toastId
  toasts.value.push({ id, msg, type })
  setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id) }, 2800)
}

// ===== 选项 =====
const stageOptions = ['初中', '高中', '大学', '考研', '在职', '其他']
const gradeMap = {
  '初中': ['初一', '初二', '初三'],
  '高中': ['高一', '高二', '高三'],
  '大学': ['大一', '大二', '大三', '大四', '大五'],
  '考研': ['备考中', '已上岸'],
  '在职': ['初级', '中级', '高级'],
  '其他': []
}
const gradeOptions = computed(() => gradeMap[form.learning_stage] || [])
function onStageChange() { form.grade = '' }
const majorOptions = ['计算机科学与技术', '软件工程', '人工智能', '数据科学', '电子信息工程', '通信工程', '自动化', '数学', '物理', '化学', '生物', '医学', '法学', '经济学', '管理学', '会计学', '金融学', '英语', '日语', '汉语言文学', '历史', '哲学', '教育学', '心理学', '机械工程', '土木工程', '建筑学', '环境工程', '材料科学', '其他']
const goalOptions = ['考试备考', '兴趣学习', '补课提升', '考研复习', '工作提升', '其他']
const difficultyOptions = ['基础巩固', '适中练习', '挑战难题']
const styleOptions = ['详细讲解', '精简要点', '举例说明']
const timeOptions = ['30分钟内', '1小时左右', '2小时左右', '2小时以上']

// ===== 主题定制（2026-09-02/03：背景色 + 组件色 + 品牌色 + 字体色，存账号跨设备同步）=====
const brandPresets = BRAND_PRESETS
const bgPresets = BG_PRESETS
const surfacePresets = SURFACE_PRESETS
const themeSets = THEME_SETS
const brandPick = ref(themeStore.brandColor)
const bgPick = ref(themeStore.bgColor || '')
const surfacePick = ref(themeStore.surfaceColor || '')
const schemeOptions = [
  { key: 'default', label: '默认（随明暗）', colors: null },
  { key: 'paper', label: '纯净白纸', colors: FONT_SCHEMES.paper },
  { key: 'warmink', label: '暖墨', colors: FONT_SCHEMES.warmink },
  { key: 'cyanink', label: '青灰', colors: FONT_SCHEMES.cyanink },
  { key: 'ink', label: '曜黑', colors: FONT_SCHEMES.ink },
]
const savingTheme = ref(false)
const textPick = reactive({
  primary: themeStore.textOverrides?.primary || '#e8e8f0',
  secondary: themeStore.textOverrides?.secondary || '#a8a8c0',
  muted: themeStore.textOverrides?.muted || '#8888aa',
})
const isCustomText = computed(() => themeStore.textScheme === 'custom')

// 有效背景色 / 组件色（四轴恒有具体值：默认方案或用户定制）；有效三档字色（自定义/预设档/派生明暗默认）
const effectiveBg = computed(() => themeStore.bgColor)
const effectiveSurface = computed(() => themeStore.surfaceColor)
const effectiveText = computed(() => resolveText(themeStore.textScheme, themeStore.textOverrides, themeStore.bgColor))

// 适配度：五组对比度按标杆折算成百分比加权（文字落在组件上，以组件色为基准；逻辑在 theme.js 供导入预览复用）
const fit = computed(() => computeFit(effectiveBg.value, effectiveSurface.value, themeStore.brandColor, effectiveText.value))

// ===== 外观码（2026-09-04：四轴打包成可分享码）=====
const appearanceCode = computed(() => encodeAppearance(themeStore.currentAppearance()))
// 链接域名跟随当前站点：上线后自动是正式域名；开发期可用 VITE_SHARE_BASE_URL 覆盖
const shareLink = computed(() => appearanceLink(appearanceCode.value.code))

async function copyText(t, okMsg) {
  try {
    await navigator.clipboard.writeText(t)
    toast(okMsg)
  } catch {
    toast('复制失败，请长按手动复制', 'error')
  }
}
const copyCode = () => copyText(appearanceCode.value.code, '外观码已复制，粘贴给好友即可')
const copyLink = () => copyText(shareLink.value, '分享链接已复制，好友点开即可预览')

// 导入弹窗：粘贴 → 实时校验 → 复用预览窗 + 适配度
const importVisible = ref(false)
const importText = ref('')
const openImport = () => { importVisible.value = true }
const importResult = computed(() => {
  const t = importText.value.trim()
  if (!t) return null
  return decodeAppearance(t)
})
const importOk = computed(() => !!importResult.value?.ok)
const importTextResolved = computed(() => {
  const p = importResult.value?.payload
  return p ? resolveText(p.textScheme, p.textOverrides, p.bg) : null
})
const importFit = computed(() => {
  const p = importResult.value?.payload
  if (!p || !importTextResolved.value) return { pct: 0, cls: '' }
  return computeFit(p.bg, p.surface, p.brand, importTextResolved.value)
})

async function applyImport() {
  const p = importResult.value?.payload
  if (!p) return
  themeStore.applyAppearance(p)
  // 回显设置页各控件
  brandPick.value = p.brand
  bgPick.value = p.bg
  surfacePick.value = p.surface
  if (p.textScheme === 'custom' && p.textOverrides) Object.assign(textPick, p.textOverrides)
  importVisible.value = false
  importText.value = ''
  if (!authStore.user?.id) {
    toast('已应用新外观（登录后保存到账号可跨设备同步）')
    return
  }
  try {
    await updateUserTheme(authStore.user.id, {
      brand_color: p.brand, text_scheme: p.textScheme, text_overrides: p.textOverrides,
      bg_color: p.bg, surface_color: p.surface,
    })
    toast('已应用并同步到账号，跨设备一致')
  } catch (e) {
    toast('已应用，但账号同步失败（' + (e?.response?.data?.detail || '网络异常') + '）', 'error')
  }
}

function chooseBrand(c) {
  if (!c) return
  themeStore.setBrand(c)
  brandPick.value = c
}

function isBg(c) {
  return (themeStore.bgColor || '').toLowerCase() === c.toLowerCase()
}

function chooseBg(c) {
  themeStore.setBg(c || null)
  bgPick.value = themeStore.bgColor || ''
}

function isSurface(c) {
  return (themeStore.surfaceColor || '').toLowerCase() === c.toLowerCase()
}

function chooseSurface(c) {
  themeStore.setSurface(c || null)
  surfacePick.value = themeStore.surfaceColor || ''
}

function applySet(t) {
  themeStore.setBg(t.bg)
  themeStore.setSurface(t.surface)
  themeStore.setBrand(t.brand)
  themeStore.setTextScheme(t.scheme)
  brandPick.value = t.brand
  bgPick.value = t.bg
  surfacePick.value = t.surface
}

function isSetActive(t) {
  return themeStore.brandColor.toLowerCase() === t.brand.toLowerCase()
    && themeStore.textScheme === t.scheme
    && (themeStore.bgColor || '').toLowerCase() === t.bg.toLowerCase()
    && (themeStore.surfaceColor || '').toLowerCase() === t.surface.toLowerCase()
}

function chooseScheme(k) {
  if (k === 'custom') {
    if (!isCustomText.value) {
      const base = FONT_SCHEMES[themeStore.textScheme] || { primary: '#e8e8f0', secondary: '#a8a8c0', muted: '#8888aa' }
      Object.assign(textPick, base)
    }
    applyCustomText()
    return
  }
  themeStore.setTextScheme(k)
}

function applyCustomText() {
  themeStore.setTextOverrides({ primary: textPick.primary, secondary: textPick.secondary, muted: textPick.muted })
}

// 按当前组件深浅自动选字体档：深底 → 纯净白纸（浅字），浅底 → 曜黑（深字）
function autoFixText() {
  themeStore.setTextScheme(luminance(effectiveSurface.value) < 0.45 ? 'paper' : 'ink')
}

async function saveTheme() {
  savingTheme.value = true
  try {
    await updateUserTheme(authStore.user.id, {
      brand_color: themeStore.brandColor,
      text_scheme: themeStore.textScheme,
      text_overrides: themeStore.textOverrides,
      bg_color: themeStore.bgColor,
      surface_color: themeStore.surfaceColor,
    })
    themeStore.cachePersist()
    toast('主题已保存，跨设备同步')
  } catch (e) {
    const detail = e?.response?.data?.detail
    toast(detail || '保存失败（若未执行 fix_user_theme.sql，先在 Supabase 执行）', 'error')
  } finally {
    savingTheme.value = false
  }
}

async function resetTheme() {
  themeStore.resetCustom()
  brandPick.value = themeStore.brandColor
  bgPick.value = themeStore.bgColor
  surfacePick.value = themeStore.surfaceColor
  Object.assign(textPick, { primary: '#e8e8f0', secondary: '#a8a8c0', muted: '#8888aa' })
  await saveTheme()
}

// ===== 在线状态 =====
const statusOptions = [
  { value: 'online', label: '在线', icon: '🟢', desc: '对其他用户可见' },
  { value: 'invisible', label: '隐身', icon: '🟣', desc: '不显示在线状态' },
]

async function changeStatus(status) {
  userStatus.value = status
  await authStore.setUserStatus(status)
  recordAction(authStore.user.id, 'change_status')
  toast('状态已更新')
}

// ===== 个人信息保存 =====
async function saveNickname() {
  if (!form.nickname) { toast('请输入昵称', 'error'); return }
  try {
    await updateNickname(authStore.user.id, form.nickname)
    authStore.user.nickname = form.nickname
    setUser(authStore.user)
    recordAction(authStore.user.id, 'update_nickname')
    toast('昵称已更新')
  } catch { toast('更新失败', 'error') }
}

async function saveBio() {
  try {
    await updateBio(authStore.user.id, form.bio)
    authStore.user.bio = form.bio
    setUser(authStore.user)
    recordAction(authStore.user.id, 'update_bio')
    toast('简介已更新')
  } catch { toast('更新失败', 'error') }
}

async function handleAvatarUpload(e) {
  const file = e.target.files[0]
  if (!file) return
  try {
    const result = await uploadAvatar(authStore.user.id, file)
    if (result.success) {
      authStore.user.avatar_url = result.avatar_url
      setUser(authStore.user)
      recordAction(authStore.user.id, 'update_avatar')
      toast('头像已更新')
    }
  } catch { toast('上传失败', 'error') }
  e.target.value = ''
}

// ===== 学习偏好保存 =====
async function savePreferences() {
  savingPrefs.value = true
  try {
    const prefs = {
      learning_stage: form.learning_stage,
      grade: form.grade,
      major: form.major,
      learning_goal: form.learning_goal,
      difficulty_preference: form.difficulty_preference,
      learning_style: form.learning_style,
      daily_study_time: form.daily_study_time,
    }
    const res = await authStore.updatePreferences(prefs)
    if (res.success) {
      recordAction(authStore.user.id, 'update_preferences')
      toast('学习偏好已保存')
    } else {
      toast(res.detail || '保存失败', 'error')
    }
  } catch { toast('保存失败，请检查网络', 'error') }
  finally { savingPrefs.value = false }
}

// ===== 修改密码 =====
async function changePassword() {
  if (!pw.old) { toast('请输入当前密码', 'error'); return }
  if (!pw.new1 || pw.new1.length < 6) { toast('新密码至少6位', 'error'); return }
  if (pw.new1 !== pw.new2) { toast('两次密码不一致', 'error'); return }
  changingPw.value = true
  try {
    const res = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'}/auth/update-password?user_id=${authStore.user.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authStore.token}` },
      body: JSON.stringify({ old_password: pw.old, new_password: pw.new1 })
    })
    const data = await res.json()
    if (data.success) {
      toast('密码修改成功')
      pw.old = ''; pw.new1 = ''; pw.new2 = ''
      recordAction(authStore.user.id, 'change_password')
    } else {
      toast(data.detail || '修改失败', 'error')
    }
  } catch { toast('修改失败，请检查网络', 'error') }
  finally { changingPw.value = false }
}

// ===== 微信绑定 =====
const wechat = reactive({ qrcode: '', status: '', loading: false })
let wechatTimer = null

async function startWechatBind() {
  wechat.loading = true
  const result = await authStore.bindWechat()
  wechat.loading = false
  if (result.success) {
    wechat.qrcode = result.qrcode
    wechat.status = '请用微信扫描二维码'
    let attempts = 0
    wechatTimer = setInterval(async () => {
      attempts++
      if (attempts > 150) {
        clearInterval(wechatTimer); wechatTimer = null
        wechat.status = '已过期，请重新获取'
        setTimeout(() => { wechat.qrcode = '' }, 2000)
        return
      }
      const pr = await authStore.bindWechatPoll(result.pollToken)
      if (pr.success) {
        clearInterval(wechatTimer); wechatTimer = null
        wechat.status = '绑定成功！'
        if (authStore.user) authStore.user.wechat_openid = 'bound'
        toast('微信绑定成功！')
        recordAction(authStore.user.id, 'bind_wechat')
        setTimeout(() => { wechat.qrcode = '' }, 1500)
      } else if (pr.message) {
        clearInterval(wechatTimer); wechatTimer = null
        wechat.status = pr.message
        setTimeout(() => { wechat.qrcode = '' }, 2000)
      }
    }, 2000)
  } else {
    toast(result.message || '获取绑定二维码失败', 'error')
  }
}

function cancelWechatBind() {
  if (wechatTimer) { clearInterval(wechatTimer); wechatTimer = null }
  wechat.qrcode = ''
  wechat.status = ''
}

// ===== 通知设置 =====
const notifSettings = reactive({
  chat_enabled: true,
  social_enabled: true,
  learning_enabled: true,
  plan_reminder_enabled: true,
  evaluation_enabled: true,
  daily_rec_enabled: true,
  daily_summary_enabled: true,
  system_enabled: true,
  daily_rec_time: '08:00',
  daily_summary_time: '07:00',
})

const notifItems = [
  { key: 'chat_enabled', label: '对话通知', desc: 'AI 对话完成、新消息提醒' },
  { key: 'social_enabled', label: '社交通知', desc: '好友请求、评论、点赞' },
  { key: 'learning_enabled', label: '学习提醒', desc: '每日任务、学习进度提醒' },
  { key: 'plan_reminder_enabled', label: '计划提醒', desc: '学习计划到期提醒' },
  { key: 'evaluation_enabled', label: '评估通知', desc: '诊断结果、学情报告生成' },
  { key: 'daily_rec_enabled', label: '每日推荐', desc: '每日个性化题目推荐' },
  { key: 'daily_summary_enabled', label: '每日总结', desc: '学习数据日报' },
  { key: 'system_enabled', label: '系统通知', desc: '公告、维护、活动通知' },
]

async function loadNotifSettings() {
  if (!authStore.user?.id) return
  try {
    const data = await getNotificationSettings(authStore.user.id)
    // 后端返回平铺对象 {chat_enabled, ...}，只取已知键避免脏字段
    if (data && typeof data.chat_enabled === 'boolean') {
      const KEYS = [
        'chat_enabled', 'social_enabled', 'learning_enabled', 'plan_reminder_enabled',
        'evaluation_enabled', 'daily_rec_enabled', 'daily_summary_enabled', 'system_enabled',
        'daily_rec_time', 'daily_summary_time'
      ]
      KEYS.forEach(k => { if (data[k] !== undefined) notifSettings[k] = data[k] })
    }
  } catch { /* 使用默认值 */ }
}

let notifSaveTimer = null
function saveNotifSettings() {
  clearTimeout(notifSaveTimer)
  notifSaveTimer = setTimeout(async () => {
    try {
      await updateNotificationSettings({ data: { ...notifSettings }, user_id: authStore.user.id })
    } catch { /* 静默失败 */ }
  }, 400)
}

// ===== 初始化 =====
onMounted(() => {
  const u = authStore.user
  if (u) {
    form.nickname = u.nickname || ''
    form.bio = u.bio || ''
    form.learning_stage = u.learning_stage || ''
    form.grade = u.grade || ''
    form.major = u.major || ''
    form.learning_goal = u.learning_goal || ''
    form.difficulty_preference = u.difficulty_preference || ''
    form.learning_style = u.learning_style || ''
    form.daily_study_time = u.daily_study_time || ''
    userStatus.value = u.status || 'online'
  }
  loadNotifSettings()
})

onUnmounted(() => {
  if (wechatTimer) clearInterval(wechatTimer)
  if (notifSaveTimer) clearTimeout(notifSaveTimer)
})
</script>

<style scoped>
.settings-page {
  min-height: 100vh;
  padding: 20px 28px;
  }

.settings-topbar {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
}
.settings-topbar h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.settings-container {
  max-width: 760px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ====== 卡片 ====== */
.settings-card {
  border-radius: 16px;
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.06);
  transition: all 0.3s ease;
  overflow: hidden;
}
.settings-card:hover {
  border-color: var(--line-soft);
}
[data-theme="dark"] .settings-card {
  background: var(--well);
  border-color: rgba(255,255,255,0.04);
}
[data-theme="dark"] .settings-card:hover {
  border-color: var(--line-soft);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 24px 0;
}
.card-icon { font-size: 18px; }
.card-title { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.card-hint { font-size: 12px; color: var(--text-muted); margin-left: auto; }
.card-body { padding: 16px 24px 20px; }
.card-footer { padding: 0 24px 18px; }

/* ====== 按钮 ====== */
.glass-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border: 1px solid rgba(255,255,255,0.04);
  cursor: pointer;
  transition: all 0.25s ease;
  font-family: inherit;
}
.glass-btn:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 8%, transparent);
  border-color: var(--line-soft);
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.06);
}
.glass-btn:active { transform: scale(0.97); }
.glass-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none !important; box-shadow: none !important; }
.glass-btn .icon { width: 18px; height: 18px; }
.glass-btn.small { padding: 4px 14px; font-size: 13px; }
.back-btn .icon { width: 20px; height: 20px; }

.glass-btn.primary {
  color: var(--brand);
  background: color-mix(in srgb, var(--brand) 8%, transparent);
  border-color: color-mix(in srgb, var(--brand) 10%, transparent);
}
.glass-btn.primary:hover {
  background: color-mix(in srgb, var(--brand) 15%, transparent);
  border-color: color-mix(in srgb, var(--brand) 22%, transparent);
  box-shadow: 0 4px 20px color-mix(in srgb, var(--brand) 12%, transparent);
}
.glass-btn.warning {
  color: color-mix(in srgb, #F59E0B 70%, var(--text-primary));
  background: rgba(245,158,11,0.08);
  border-color: rgba(245,158,11,0.10);
}
.glass-btn.warning:hover {
  background: rgba(245,158,11,0.14);
  border-color: rgba(245,158,11,0.20);
}

/* ====== 表单 ====== */
.field { margin-bottom: 16px; }
.field:last-child { margin-bottom: 0; }
.field-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.field-row { display: flex; gap: 10px; }
.field-row .glass-input { flex: 1; }

.glass-input {
  width: 100%;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 14px;
  color: var(--text-primary);
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
  border: 1px solid rgba(255,255,255,0.04);
  transition: all 0.25s ease;
  outline: none;
  font-family: inherit;
  box-sizing: border-box;
}
.glass-input::placeholder { color: var(--text-muted); opacity: 0.4; }
.glass-input:focus {
  border-color: color-mix(in srgb, var(--brand) 20%, transparent);
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--brand) 4%, transparent);
}
.glass-input.textarea { resize: vertical; min-height: 60px; }
select.glass-input { cursor: pointer; appearance: none; }

.pw-fields { display: flex; flex-direction: column; gap: 10px; }

/* ====== 头像 ====== */
.avatar-row { display: flex; align-items: center; gap: 16px; }
.avatar-ring {
  width: 64px; height: 64px;
  border-radius: 50%;
  border: 2px solid var(--border-color);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  flex-shrink: 0;
}
.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.avatar-placeholder { font-size: 24px; font-weight: 700; color: var(--text-primary); }

/* ====== 学习偏好 ====== */
.prefs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}
.pref-field { display: flex; flex-direction: column; gap: 6px; }

/* ====== 外观 & 隐私 ====== */
.toggle-group {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 10px;
}
.toggle-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 16px 12px;
  border-radius: 12px;
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
  border: 2px solid rgba(255,255,255,0.04);
  cursor: pointer;
  transition: all 0.25s ease;
  position: relative;
}
.toggle-card:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent);
  border-color: var(--line-soft);
  transform: translateY(-2px);
}
.toggle-card.active {
  background: color-mix(in srgb, var(--brand) 8%, transparent);
  border-color: color-mix(in srgb, var(--brand) 25%, transparent);
}
.toggle-icon { font-size: 24px; }
.toggle-label { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.toggle-desc { font-size: 11px; color: var(--text-muted); text-align: center; }
.toggle-check {
  position: absolute; top: 8px; right: 10px;
  width: 20px; height: 20px; border-radius: 50%;
  background: var(--brand, var(--brand)); color: var(--brand-on);
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700;
}

/* ====== 主题定制（2026-09-02：品牌色 / 字体色） ====== */
.theme-custom {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(255,255,255,0.05);
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.tc-section { display: flex; flex-direction: column; gap: 8px; }
.tc-title { font-size: 12px; color: var(--text-muted); }
.tc-colors {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.tc-swatch {
  width: 24px; height: 24px; border-radius: 50%;
  cursor: pointer;
  border: 2px solid transparent;
  transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease;
}
.tc-swatch:hover { transform: scale(1.15); }
.tc-swatch.active {
  border-color: #fff;
  box-shadow: 0 0 0 2px rgba(255,255,255,.25), 0 0 10px rgba(0,0,0,.3);
}
.tc-schemes {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.tc-scheme {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
  padding: 5px 11px;
  border-radius: 16px;
  border: 1px solid var(--line-soft);
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  cursor: pointer;
  transition: all .2s ease;
}
.tc-scheme:hover { background: color-mix(in srgb, var(--surface, #ffffff) 7%, transparent); }
.tc-scheme.active {
  color: var(--brand, var(--brand));
  border-color: color-mix(in srgb, var(--brand, var(--brand)) 55%, transparent);
  background: color-mix(in srgb, var(--brand, var(--brand)) 10%, transparent);
}
.tc-dots { display: inline-flex; gap: 3px; }
.tc-dots i {
  width: 12px; height: 12px; border-radius: 50%;
  border: 1px solid rgba(0,0,0,.15);
}
.tc-dot-def {
  width: 12px; height: 12px; border-radius: 50%;
  background: conic-gradient(#ddd 0 25%, #999 0 50%, #555 0 75%, #222 0);
  border: 1px solid rgba(0,0,0,.2);
}
.tc-custom {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  border: 1px dashed var(--line-soft);
}
.tc-pick-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-secondary);
}
.tc-pick-label { min-width: 58px; }
.tc-actions { display: flex; gap: 10px; }

/* ====== 主题定制：整套方案 / 背景色 / 适配度（2026-09-03）====== */
.tc-sets { display: flex; gap: 10px; flex-wrap: wrap; }
.tc-set {
  display: inline-flex; flex-direction: column; align-items: center; gap: 4px;
  padding: 6px 8px; border-radius: 8px; cursor: pointer;
  border: 1px solid rgba(128,128,128,.18); font-size: 12px; color: var(--text-secondary);
  transition: border-color .2s ease, background .2s ease;
}
.tc-set:hover { background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent); }
.tc-set.active {
  border-color: color-mix(in srgb, var(--brand) 55%, transparent);
  color: var(--brand-bright);
}
.tc-set-tile {
  position: relative; display: block; width: 34px; height: 24px;
  border-radius: 4px; overflow: hidden; border: 1px solid rgba(0,0,0,.2);
}
.tc-set-surface { position: absolute; left: 5px; top: 4px; width: 8px; height: 6px; border-radius: 2px; border: 1px solid rgba(128,128,128,.25); }
.tc-set-brand { position: absolute; right: 4px; top: 4px; width: 9px; height: 9px; border-radius: 50%; }
.tc-set-ink { position: absolute; left: 5px; bottom: 4px; width: 12px; height: 3px; border-radius: 1px; }

.tc-fit {
  padding: 10px 12px; border-radius: 10px;
  border: 1px solid rgba(128,128,128,.16);
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
}
.tc-fit-head { display: flex; align-items: center; justify-content: space-between; }
.tc-fit-head b { font-size: 20px; font-weight: 700; }
.tc-fit-head b.good, .tc-fit-summary.good { color: color-mix(in srgb, #67c23a 65%, var(--text-primary)); }
.tc-fit-head b.warn, .tc-fit-summary.warn { color: color-mix(in srgb, #e6a23c 70%, var(--text-primary)); }
.tc-fit-head b.bad, .tc-fit-summary.bad { color: #f56c6c; }
.tc-fit-bar {
  height: 6px; border-radius: 3px; margin: 8px 0 2px;
  background: rgba(128,128,128,.18); overflow: hidden;
}
.tc-fit-bar i {
  display: block; height: 100%; border-radius: 3px;
  transition: width .3s ease;
}
.tc-fit-bar i.good { background: #67c23a; }
.tc-fit-bar i.warn { background: #e6a23c; }
.tc-fit-bar i.bad { background: #f56c6c; }
.tc-fit-checks { display: flex; flex-direction: column; gap: 3px; margin-top: 8px; }
.tc-fit-row { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; font-size: 12px; }
.tc-fit-dot { width: 8px; height: 8px; border-radius: 50%; flex: none; }
.tc-fit-dot.good { background: #67c23a; }
.tc-fit-dot.warn { background: #e6a23c; }
.tc-fit-dot.bad { background: #f56c6c; }
.tc-fit-label { color: var(--text-secondary); }
.tc-fit-val { color: var(--text-muted); font-size: 11px; }
.tc-fit-advice { font-size: 11px; flex-basis: 100%; color: var(--text-muted); }
.tc-fit-row.bad .tc-fit-advice { color: #f56c6c; }
.tc-fit-row.warn .tc-fit-advice { color: #e6a23c; }
.tc-fit-summary { margin-top: 8px; font-size: 12px; }
.tc-fit-fix { margin-top: 8px; }

/* ====== 实时预览：嵌入小页面（2026-09-03 / 2026-09-04 抽为 ThemePreviewWindow 组件，样式随组件走）====== */
.tc-pv-score-wrap { font-size: 12px; color: var(--text-secondary); }
.tc-pv-score-wrap b { font-size: 18px; font-weight: 700; margin-left: 2px; }
.tc-pv-score-wrap b.good { color: #67c23a; }
.tc-pv-score-wrap b.warn { color: #e6a23c; }
.tc-pv-score-wrap b.bad { color: #f56c6c; }

/* ====== 外观码（2026-09-04）====== */
.tc-share {
  padding: 12px;
  border-radius: 10px;
  border: 1px dashed var(--line-soft);
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
}
.tc-share-desc { font-size: 12px; color: var(--text-muted); line-height: 1.6; }
.tc-share-code {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 12px; border-radius: 10px;
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent);
  border: 1px solid var(--line-soft);
  cursor: pointer;
  transition: border-color .2s ease, background .2s ease;
}
.tc-share-code:hover {
  border-color: color-mix(in srgb, var(--brand) 35%, transparent);
  background: color-mix(in srgb, var(--surface, #ffffff) 9%, transparent);
}
.tc-share-code code {
  flex: 1; min-width: 0;
  font-size: 12px; font-family: 'Consolas', 'Menlo', monospace;
  color: var(--text-primary);
  word-break: break-all;
  user-select: all;
}
.tc-share-dots { display: inline-flex; gap: 4px; flex: none; }
.tc-share-dots i {
  width: 11px; height: 11px; border-radius: 50%;
  border: 1px solid rgba(0,0,0,.25);
}

/* ====== 导入外观码弹窗（el-dialog 挂在 body，按 .settings-dialog 同款 :deep 模式）====== */
.tc-import-dialog :deep(.el-dialog) {
  background: var(--well) !important;
  backdrop-filter: blur(24px) !important;
  border: 1px solid var(--line-soft) !important;
  border-radius: 16px !important;
}
.tc-import-dialog :deep(.el-dialog__title) {
  color: var(--text-primary) !important;
  font-weight: 600;
}
.tc-import-dialog :deep(.el-dialog__body) { padding: 18px 24px 8px; }
.tc-import-dialog :deep(.el-dialog__footer) { padding: 8px 24px 18px; }
.tc-import-dialog :deep(.el-button) {
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent) !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
  color: var(--text-secondary) !important;
  border-radius: 8px !important;
}
.tc-import-dialog :deep(.el-button--primary) {
  background: color-mix(in srgb, var(--brand) 15%, transparent) !important;
  border-color: color-mix(in srgb, var(--brand) 20%, transparent) !important;
  color: var(--brand-bright) !important;
}

.tc-import { display: flex; flex-direction: column; gap: 10px; }
.tc-import-input {
  width: 100%;
  padding: 10px 12px;
  border-radius: 10px;
  font-size: 13px;
  font-family: 'Consolas', 'Menlo', monospace;
  line-height: 1.5;
  resize: vertical;
  min-height: 52px;
  color: var(--text-primary);
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border: 1px solid var(--line-soft);
  outline: none;
  box-sizing: border-box;
}
.tc-import-input::placeholder { color: var(--text-muted); opacity: 0.45; font-family: inherit; }
.tc-import-input:focus {
  border-color: color-mix(in srgb, var(--brand) 30%, transparent);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--brand) 5%, transparent);
}
.tc-import-err {
  font-size: 12px; color: #f56c6c;
  padding: 8px 12px; border-radius: 8px;
  background: rgba(245,108,108,.08);
  border: 1px solid rgba(245,108,108,.2);
}
.tc-import-head { display: flex; align-items: center; justify-content: space-between; margin-top: 2px; }
.tc-import-tag {
  font-size: 12px; font-weight: 600; color: var(--brand-bright);
  padding: 2px 10px; border-radius: 999px;
  background: color-mix(in srgb, var(--brand) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--brand) 30%, transparent);
}
.tc-import-score { font-size: 13px; font-weight: 700; }
.tc-import-score.good { color: #67c23a; }
.tc-import-score.warn { color: #e6a23c; }
.tc-import-score.bad { color: #f56c6c; }
.tc-import-warn {
  font-size: 12px; color: #e6a23c;
  padding: 8px 12px; border-radius: 8px;
  background: rgba(230,162,60,.08);
  border: 1px solid rgba(230,162,60,.2);
}

/* ====== 通知设置 ====== */
.notif-grid { display: flex; flex-direction: column; gap: 4px; }
.notif-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-radius: 10px;
  transition: background 0.2s;
}
.notif-row:hover { background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent); }
.notif-info { display: flex; flex-direction: column; gap: 2px; }
.notif-label { font-size: 14px; color: var(--text-primary); font-weight: 500; }
.notif-desc { font-size: 12px; color: var(--text-muted); }
.notif-time-row { display: flex; gap: 24px; margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.04); }
.notif-time-field { display: flex; flex-direction: column; gap: 6px; }

/* Switch */
.switch { position: relative; display: inline-block; width: 44px; height: 24px; flex-shrink: 0; }
.switch input { opacity: 0; width: 0; height: 0; }
.switch-slider {
  position: absolute; cursor: pointer;
  top: 0; left: 0; right: 0; bottom: 0;
  background: color-mix(in srgb, var(--surface, #ffffff) 10%, transparent);
  border-radius: 24px;
  transition: all 0.3s ease;
}
.switch-slider::before {
  content: ""; position: absolute;
  height: 18px; width: 18px;
  left: 3px; bottom: 3px;
  background: #fff;
  border-radius: 50%;
  transition: all 0.3s ease;
}
.switch input:checked + .switch-slider { background: var(--brand); }
.switch input:checked + .switch-slider::before { transform: translateX(20px); }

/* ====== 关于 ====== */
.about-version {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
  border: 1px solid rgba(255,255,255,0.04);
  margin-bottom: 12px;
}
.about-label { font-size: 13px; color: var(--text-secondary); }
.about-ver {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  font-family: 'Consolas', 'Menlo', monospace;
}
.about-tag {
  font-style: normal;
  font-size: 11px;
  font-weight: 600;
  color: var(--brand);
  background: color-mix(in srgb, var(--brand) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--brand) 20%, transparent);
  padding: 1px 7px;
  border-radius: 8px;
  margin-left: 6px;
  vertical-align: middle;
}
.about-icp-link { text-decoration: none; transition: color .25s ease; }
.about-icp-link:hover { color: var(--brand); }
.about-links { margin-top: 4px; }

/* ====== 分隔线 ====== */
.divider { height: 1px; background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent); margin: 18px 0; }

/* ====== 微信 ====== */
.wechat-bound { display: flex; align-items: center; gap: 10px; padding: 10px 0; font-size: 15px; color: var(--text-primary); }
.wechat-btn {
  display: inline-flex; align-items: center; gap: 8px;
  background: linear-gradient(135deg, #07c160, #06ad56) !important;
  color: #fff !important; border: none !important;
}
.wechat-btn:hover { box-shadow: 0 4px 16px rgba(7,193,96,0.3); }
.wechat-panel {
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  padding: 16px; background: #fff; border-radius: 14px; border: 2px solid #07c160;
}
.wechat-qr { width: 180px; height: 180px; border-radius: 8px; }
.wechat-tip { font-size: 14px; color: #333; margin: 0; font-weight: 500; }

/* ====== AI 链接 ====== */
.link-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 10px; }
.link-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 12px;
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  border: 1px solid rgba(255,255,255,0.04);
  text-decoration: none;
  cursor: pointer;
  transition: all 0.25s ease;
}
.link-card:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent);
  border-color: color-mix(in srgb, var(--brand) 15%, transparent);
  transform: translateY(-2px);
}
.link-icon { font-size: 22px; flex-shrink: 0; }
.link-label { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.link-desc { font-size: 12px; color: var(--text-muted); flex: 1; }
.link-arrow { width: 18px; height: 18px; color: var(--text-muted); flex-shrink: 0; }

/* 小基图标 */
.xiaoji-section-icon {
  width: 24px;
  height: 24px;
  object-fit: contain;
  border-radius: 6px;
}
.link-icon-img {
  width: 28px;
  height: 28px;
  object-fit: contain;
  border-radius: 7px;
  flex-shrink: 0;
}

/* ====== Toast ====== */
.toast-stack {
  position: fixed; top: 24px; right: 24px; z-index: 9999;
  display: flex; flex-direction: column; gap: 8px;
  pointer-events: none;
}
.toast-item {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 18px; border-radius: 12px;
  background: var(--well);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid var(--line-soft);
  box-shadow: 0 8px 32px rgba(0,0,0,0.2);
  pointer-events: auto;
  font-size: 14px;
  color: var(--text-primary);
}
.toast-success .toast-icon { color: color-mix(in srgb, #67c23a 65%, var(--text-primary)); font-weight: 700; }
.toast-error .toast-icon { color: #f56c6c; font-weight: 700; }
.toast-warning .toast-icon { color: color-mix(in srgb, #e6a23c 70%, var(--text-primary)); font-weight: 700; }
.toast-enter-active { transition: all 0.3s ease-out; }
.toast-leave-active { transition: all 0.2s ease-in; }
.toast-enter-from { opacity: 0; transform: translateX(40px); }
.toast-leave-to { opacity: 0; transform: translateX(40px); }

@media (max-width: 600px) {
  .settings-page { padding: 12px 16px; }
  .prefs-grid { grid-template-columns: 1fr; }
  .toggle-group { grid-template-columns: repeat(2, 1fr); }
  .notif-time-row { flex-direction: column; }
  .link-grid { grid-template-columns: 1fr; }
}
</style>
