<template>
  <div class="api-center-page">
    <div class="api-container">
      <!-- ===== 顶部 ===== -->
      <div class="api-header">
        <div class="header-left">
          <el-button text class="back-btn" @click="goBack">
            <i class="fas fa-arrow-left"></i> 返回
          </el-button>
          <h1>🔑 API 管理</h1>
        </div>
        <el-tag type="info" size="small">配置后功能使用你自己的额度</el-tag>
      </div>

      <el-divider />

      <!-- ===== 说明 ===== -->
      <div class="api-desc">
        <p>为每个 AI 功能选择模型平台，填入对应的 API 凭证。不知道怎么获取？<span @click="goQA">查看 Q&A 指南 →</span></p>
      </div>

      <!-- ===== 功能列表 ===== -->
      <div class="api-list">
        <!-- ===== 1. AI 对话 ===== -->
        <div class="api-card">
          <div class="api-card-header">
            <div class="api-card-left">
              <span class="api-icon">💬</span>
              <div>
                <div class="api-name">AI 对话</div>
                <div class="api-desc-text">主界面 / 小基 / 语音对话</div>
              </div>
            </div>
            <div class="api-card-right">
              <span class="api-status" :class="getStatusClass('chat')">
                {{ getStatusText('chat') }}
              </span>
              <el-select v-model="chatPlatform" size="small" class="api-select">
                <el-option
                  v-for="p in chatOptions"
                  :key="p.value"
                  :label="p.label"
                  :value="p.value"
                />
              </el-select>
            </div>
          </div>

          <!-- DeepSeek 配置 -->
          <div v-if="chatPlatform === 'deepseek'" class="api-config">
            <div class="config-row">
              <span class="config-label">API Key</span>
              <el-input
                v-model="chatDeepseekKey"
                type="password"
                placeholder="sk-xxxxxxxxxxxxxxxx"
                size="small"
                class="config-input"
                show-password
              />
              <el-button size="small" type="primary" plain @click="validateKey('chat', 'deepseek')">
                验证
              </el-button>
            </div>
            <div class="config-hint">🔗 platform.deepseek.com</div>
          </div>

          <!-- 火山引擎配置 -->
          <div v-if="chatPlatform === 'volc'" class="api-config">
            <div class="config-row">
              <span class="config-label">API Key</span>
              <el-input
                v-model="chatVolcKey"
                type="password"
                placeholder="VxCgNvLTE.xxxxxxxxxxxxxxxx"
                size="small"
                class="config-input"
                show-password
              />
              <el-button size="small" type="primary" plain @click="validateKey('chat', 'volc')">
                验证
              </el-button>
            </div>
            <div class="config-row">
              <span class="config-label">Endpoint ID</span>
              <el-input
                v-model="chatVolcEndpoint"
                placeholder="ep-202607xxxxxxxx"
                size="small"
                class="config-input"
              />
            </div>
            <div class="config-hint">🔗 console.volcengine.com/ark</div>
          </div>

          <!-- 智谱配置 -->
          <div v-if="chatPlatform === 'zhipu'" class="api-config">
            <div class="config-row">
              <span class="config-label">API Key</span>
              <el-input
                v-model="chatZhipuKey"
                type="password"
                placeholder="xxxxxxxx.xxxxxxxxxxxxxxxx"
                size="small"
                class="config-input"
                show-password
              />
              <el-button size="small" type="primary" plain @click="validateKey('chat', 'zhipu')">
                验证
              </el-button>
            </div>
            <div class="config-hint">🔗 open.bigmodel.cn</div>
          </div>
        </div>

        <!-- ===== 2. 图片理解 ===== -->
        <div class="api-card">
          <div class="api-card-header">
            <div class="api-card-left">
              <span class="api-icon">🖼️</span>
              <div>
                <div class="api-name">图片理解</div>
                <div class="api-desc-text">识别图片内容</div>
              </div>
            </div>
            <div class="api-card-right">
              <span class="api-status" :class="getStatusClass('vision')">
                {{ getStatusText('vision') }}
              </span>
              <el-select v-model="visionPlatform" size="small" class="api-select">
                <el-option
                  v-for="p in visionOptions"
                  :key="p.value"
                  :label="p.label"
                  :value="p.value"
                />
              </el-select>
            </div>
          </div>

          <!-- 火山引擎配置 -->
          <div v-if="visionPlatform === 'volc'" class="api-config">
            <div class="config-row">
              <span class="config-label">API Key</span>
              <el-input
                v-model="visionVolcKey"
                type="password"
                placeholder="VxCgNvLTE.xxxxxxxxxxxxxxxx"
                size="small"
                class="config-input"
                show-password
              />
              <el-button size="small" type="primary" plain @click="validateKey('vision', 'volc')">
                验证
              </el-button>
            </div>
            <div class="config-row">
              <span class="config-label">Endpoint ID</span>
              <el-input
                v-model="visionVolcEndpoint"
                placeholder="ep-202607xxxxxxxx"
                size="small"
                class="config-input"
              />
            </div>
            <div class="config-hint">🔗 console.volcengine.com/ark</div>
          </div>
        </div>

        <!-- ===== 3. 题目生成 ===== -->
        <div class="api-card">
          <div class="api-card-header">
            <div class="api-card-left">
              <span class="api-icon">📝</span>
              <div>
                <div class="api-name">题目生成</div>
                <div class="api-desc-text">AI 出题 / 换题型</div>
              </div>
            </div>
            <div class="api-card-right">
              <span class="api-status" :class="getStatusClass('generate')">
                {{ getStatusText('generate') }}
              </span>
              <el-select v-model="generatePlatform" size="small" class="api-select">
                <el-option
                  v-for="p in generateOptions"
                  :key="p.value"
                  :label="p.label"
                  :value="p.value"
                />
              </el-select>
            </div>
          </div>

          <!-- DeepSeek 配置 -->
          <div v-if="generatePlatform === 'deepseek'" class="api-config">
            <div class="config-row">
              <span class="config-label">API Key</span>
              <el-input
                v-model="generateDeepseekKey"
                type="password"
                placeholder="sk-xxxxxxxxxxxxxxxx"
                size="small"
                class="config-input"
                show-password
              />
              <el-button size="small" type="primary" plain @click="validateKey('generate', 'deepseek')">
                验证
              </el-button>
            </div>
            <div class="config-hint">🔗 platform.deepseek.com</div>
          </div>

          <!-- 智谱配置 -->
          <div v-if="generatePlatform === 'zhipu'" class="api-config">
            <div class="config-row">
              <span class="config-label">API Key</span>
              <el-input
                v-model="generateZhipuKey"
                type="password"
                placeholder="xxxxxxxx.xxxxxxxxxxxxxxxx"
                size="small"
                class="config-input"
                show-password
              />
              <el-button size="small" type="primary" plain @click="validateKey('generate', 'zhipu')">
                验证
              </el-button>
            </div>
            <div class="config-hint">🔗 open.bigmodel.cn</div>
          </div>
        </div>

        <!-- ===== 4. 学习评估 / 学情报告 ===== -->
        <div class="api-card">
          <div class="api-card-header">
            <div class="api-card-left">
              <span class="api-icon">📊</span>
              <div>
                <div class="api-name">学习评估 / 学情报告</div>
                <div class="api-desc-text">掌握度评分 / 画像 / 建议</div>
              </div>
            </div>
            <div class="api-card-right">
              <span class="api-status" :class="getStatusClass('evaluate')">
                {{ getStatusText('evaluate') }}
              </span>
              <el-select v-model="evaluatePlatform" size="small" class="api-select">
                <el-option
                  v-for="p in evaluateOptions"
                  :key="p.value"
                  :label="p.label"
                  :value="p.value"
                />
              </el-select>
            </div>
          </div>

          <!-- DeepSeek 配置 -->
          <div v-if="evaluatePlatform === 'deepseek'" class="api-config">
            <div class="config-row">
              <span class="config-label">API Key</span>
              <el-input
                v-model="evaluateDeepseekKey"
                type="password"
                placeholder="sk-xxxxxxxxxxxxxxxx"
                size="small"
                class="config-input"
                show-password
              />
              <el-button size="small" type="primary" plain @click="validateKey('evaluate', 'deepseek')">
                验证
              </el-button>
            </div>
            <div class="config-hint">🔗 platform.deepseek.com</div>
          </div>
        </div>

        <!-- ===== 5. 视频推荐 ===== -->
        <div class="api-card">
          <div class="api-card-header">
            <div class="api-card-left">
              <span class="api-icon">🎥</span>
              <div>
                <div class="api-name">视频推荐</div>
                <div class="api-desc-text">知识点相关视频推送</div>
              </div>
            </div>
            <div class="api-card-right">
              <span class="api-status" :class="getStatusClass('video')">
                {{ getStatusText('video') }}
              </span>
              <el-select v-model="videoPlatform" size="small" class="api-select">
                <el-option
                  v-for="p in videoOptions"
                  :key="p.value"
                  :label="p.label"
                  :value="p.value"
                />
              </el-select>
            </div>
          </div>

          <!-- 腾讯云配置 -->
          <div v-if="videoPlatform === 'tencent'" class="api-config">
            <div class="config-row">
              <span class="config-label">SecretId</span>
              <el-input
                v-model="videoTencentId"
                placeholder="AKIDxxxxxxxxxxxxxxxx"
                size="small"
                class="config-input"
              />
            </div>
            <div class="config-row">
              <span class="config-label">SecretKey</span>
              <el-input
                v-model="videoTencentKey"
                type="password"
                placeholder="xxxxxxxxxxxxxxxx"
                size="small"
                class="config-input"
                show-password
              />
            </div>
            <div class="config-row">
              <span class="config-label">地域</span>
              <el-select v-model="videoTencentRegion" size="small" class="config-input">
                <el-option label="上海 (ap-shanghai)" value="ap-shanghai" />
                <el-option label="广州 (ap-guangzhou)" value="ap-guangzhou" />
                <el-option label="北京 (ap-beijing)" value="ap-beijing" />
              </el-select>
              <el-button size="small" type="primary" plain @click="validateKey('video', 'tencent')">
                验证
              </el-button>
            </div>
            <div class="config-hint">🔗 console.cloud.tencent.com</div>
          </div>
        </div>

        <!-- ===== 6. 视频通话 ===== -->
        <div class="api-card">
          <div class="api-card-header">
            <div class="api-card-left">
              <span class="api-icon">📞</span>
              <div>
                <div class="api-name">视频通话</div>
                <div class="api-desc-text">讯飞数字人</div>
              </div>
            </div>
            <div class="api-card-right">
              <span class="api-status" :class="getStatusClass('call')">
                {{ getStatusText('call') }}
              </span>
              <el-select v-model="callPlatform" size="small" class="api-select">
                <el-option
                  v-for="p in callOptions"
                  :key="p.value"
                  :label="p.label"
                  :value="p.value"
                />
              </el-select>
            </div>
          </div>

          <!-- 讯飞配置 -->
          <div v-if="callPlatform === 'iflytek'" class="api-config">
            <div class="config-row">
              <span class="config-label">APPID</span>
              <el-input
                v-model="callIflytekAppId"
                placeholder="xxxxxxxx"
                size="small"
                class="config-input"
              />
            </div>
            <div class="config-row">
              <span class="config-label">API Key</span>
              <el-input
                v-model="callIflytekKey"
                type="password"
                placeholder="xxxxxxxxxxxxxxxx"
                size="small"
                class="config-input"
                show-password
              />
            </div>
            <div class="config-row">
              <span class="config-label">API Secret</span>
              <el-input
                v-model="callIflytekSecret"
                type="password"
                placeholder="xxxxxxxxxxxxxxxx"
                size="small"
                class="config-input"
                show-password
              />
              <el-button size="small" type="primary" plain @click="validateKey('call', 'iflytek')">
                验证
              </el-button>
            </div>
            <div class="config-hint">🔗 console.xfyun.cn</div>
          </div>
        </div>
      </div>

      <!-- ===== 底部提示 ===== -->
      <div class="api-footer">
        <el-divider />
        <p>💡 语音输入转文字使用浏览器内置功能，无需配置</p>
        <p class="api-footer-link">不知道怎么获取 Key？<span @click="goQA">查看 Q&A 指南 →</span></p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()

// ===== 各功能当前选择的平台 =====
const chatPlatform = ref('volc')
const visionPlatform = ref('volc')
const generatePlatform = ref('deepseek')
const evaluatePlatform = ref('deepseek')
const videoPlatform = ref('tencent')
const callPlatform = ref('iflytek')

// ===== 各功能可选平台 =====
const chatOptions = [
  { value: 'volc', label: '火山引擎（豆包）' },
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'zhipu', label: '智谱 GLM' }
]
const visionOptions = [
  { value: 'volc', label: '火山引擎（豆包）' }
]
const generateOptions = [
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'zhipu', label: '智谱 GLM' }
]
const evaluateOptions = [
  { value: 'deepseek', label: 'DeepSeek' }
]
const videoOptions = [
  { value: 'tencent', label: '腾讯云' }
]
const callOptions = [
  { value: 'iflytek', label: '讯飞' }
]

// ===== 各功能平台凭证 =====
// AI 对话
const chatDeepseekKey = ref('')
const chatVolcKey = ref('')
const chatVolcEndpoint = ref('')
const chatZhipuKey = ref('')

// 图片理解
const visionVolcKey = ref('')
const visionVolcEndpoint = ref('')

// 题目生成
const generateDeepseekKey = ref('')
const generateZhipuKey = ref('')

// 学习评估
const evaluateDeepseekKey = ref('')

// 视频推荐
const videoTencentId = ref('')
const videoTencentKey = ref('')
const videoTencentRegion = ref('ap-shanghai')

// 视频通话
const callIflytekAppId = ref('')
const callIflytekKey = ref('')
const callIflytekSecret = ref('')

// ===== 模拟状态（演示用） =====
const statusMap = ref({
  chat: false,
  vision: false,
  generate: false,
  evaluate: false,
  video: false,
  call: false
})

function getStatusClass(key) {
  return statusMap.value[key] ? 'verified' : 'pending'
}

function getStatusText(key) {
  return statusMap.value[key] ? '✅ 已配置' : '⏳ 未配置'
}

function validateKey(category, platform) {
  ElMessage.info(`正在验证 ${category} - ${platform} ...`)
  setTimeout(() => {
    statusMap.value[category] = true
    ElMessage.success(`${category} 验证通过 ✅`)
  }, 1000)
}

function goBack() {
  router.push('/home')
}

function goQA() {
  router.push('/qa')
}
</script>

<style scoped>
.api-center-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 30px 20px;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

[data-theme="light"] .api-center-page {
  background-image: url('/assets/bg/api_bg.jpg');
}
[data-theme="dark"] .api-center-page {
  background-image: url('/assets/bg/api_bl.jpg');
}

.api-container {
  max-width: 860px;
  width: 100%;
  padding: 28px 36px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
  max-height: 90vh;
  overflow-y: auto;
}

[data-theme="dark"] .api-container {
  background: rgba(0, 0, 0, 0.30);
}

.api-container::-webkit-scrollbar {
  width: 4px;
}
.api-container::-webkit-scrollbar-thumb {
  background: rgba(128, 128, 128, 0.2);
  border-radius: 2px;
}

.api-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.back-btn {
  color: var(--text-secondary) !important;
  font-size: 15px;
  padding: 4px 8px;
  transition: all 0.3s ease !important;
}
.back-btn:hover {
  color: var(--text-primary) !important;
  transform: translateX(-2px);
  background: rgba(255, 255, 255, 0.06);
}
.api-header h1 {
  font-size: 22px;
  color: var(--text-primary);
  margin: 0;
}

.el-divider {
  margin: 12px 0;
}

.api-desc {
  padding: 4px 0 8px;
}
.api-desc p {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}
.api-desc span {
  color: #409eff;
  cursor: pointer;
}
.api-desc span:hover {
  text-decoration: underline;
}

.api-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px 0;
}

.api-card {
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.02);
  padding: 14px 18px;
  transition: all 0.3s ease;
}
.api-card:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.10);
}

.api-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}
.api-card-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.api-icon {
  font-size: 22px;
}
.api-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}
.api-desc-text {
  font-size: 12px;
  color: var(--text-muted);
}
.api-card-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.api-status {
  font-size: 13px;
  font-weight: 500;
}
.api-status.verified {
  color: #67c23a;
}
.api-status.pending {
  color: var(--text-muted);
}

.api-select {
  width: 150px;
}
.api-select :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 8px !important;
}

.api-config {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.config-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.config-label {
  font-size: 13px;
  color: var(--text-secondary);
  min-width: 80px;
  flex-shrink: 0;
}
.config-input {
  flex: 1;
}
.config-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 8px !important;
}
.config-hint {
  font-size: 12px;
  color: var(--text-muted);
  padding-left: 88px;
}
.config-hint a {
  color: #409eff;
  text-decoration: none;
}
.config-hint a:hover {
  text-decoration: underline;
}

.api-footer {
  padding: 8px 0;
}
.api-footer p {
  font-size: 13px;
  color: var(--text-muted);
  text-align: center;
  margin: 4px 0;
}
.api-footer-link span {
  color: #409eff;
  cursor: pointer;
}
.api-footer-link span:hover {
  text-decoration: underline;
}

@media (max-width: 640px) {
  .api-container {
    padding: 16px 14px;
    max-height: 95vh;
  }
  .api-header h1 {
    font-size: 18px;
  }
  .api-card-header {
    flex-direction: column;
    align-items: stretch;
  }
  .api-card-right {
    flex-wrap: wrap;
  }
  .api-select {
    width: 100%;
  }
  .config-row {
    flex-wrap: wrap;
  }
  .config-label {
    min-width: 60px;
  }
  .config-hint {
    padding-left: 0;
  }
}
</style>