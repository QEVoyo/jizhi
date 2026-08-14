<template>
  <div class="os-page">
    <!-- 顶栏 -->
    <header class="os-topbar">
      <button class="os-back" @click="$router.push('/home')">
        <i class="fas fa-arrow-left"></i>
        <span>返回</span>
      </button>
      <h1 class="os-title">📖 开源文档</h1>
      <div class="os-spacer"></div>
    </header>

    <div class="os-body">
      <p class="os-subtitle">本项目基于以下开源技术栈构建，感谢所有开源贡献者</p>

      <div class="os-grid">
        <!-- 前端 -->
        <div class="os-card">
          <div class="os-card-header frontend">
            <i class="fas fa-layer-group"></i>
            <h3>前端技术栈</h3>
          </div>
          <div class="os-card-body">
            <a href="https://vuejs.org/" target="_blank" class="os-dep">
              <span class="os-dep-name">Vue 3</span>
              <span class="os-dep-desc">渐进式 JavaScript 框架</span>
              <span class="os-dep-license">MIT</span>
            </a>
            <a href="https://router.vuejs.org/" target="_blank" class="os-dep">
              <span class="os-dep-name">Vue Router</span>
              <span class="os-dep-desc">Vue 官方路由</span>
              <span class="os-dep-license">MIT</span>
            </a>
            <a href="https://pinia.vuejs.org/" target="_blank" class="os-dep">
              <span class="os-dep-name">Pinia</span>
              <span class="os-dep-desc">Vue 状态管理</span>
              <span class="os-dep-license">MIT</span>
            </a>
            <a href="https://element-plus.org/" target="_blank" class="os-dep">
              <span class="os-dep-name">Element Plus</span>
              <span class="os-dep-desc">Vue 3 UI 组件库</span>
              <span class="os-dep-license">MIT</span>
            </a>
            <a href="https://fontawesome.com/" target="_blank" class="os-dep">
              <span class="os-dep-name">Font Awesome</span>
              <span class="os-dep-desc">图标库</span>
              <span class="os-dep-license">Free / MIT</span>
            </a>
            <a href="https://vitejs.dev/" target="_blank" class="os-dep">
              <span class="os-dep-name">Vite</span>
              <span class="os-dep-desc">前端构建工具</span>
              <span class="os-dep-license">MIT</span>
            </a>
          </div>
        </div>

        <!-- 后端 -->
        <div class="os-card">
          <div class="os-card-header backend">
            <i class="fas fa-server"></i>
            <h3>后端技术栈</h3>
          </div>
          <div class="os-card-body">
            <a href="https://fastapi.tiangolo.com/" target="_blank" class="os-dep">
              <span class="os-dep-name">FastAPI</span>
              <span class="os-dep-desc">高性能 Python Web 框架</span>
              <span class="os-dep-license">MIT</span>
            </a>
            <a href="https://www.python.org/" target="_blank" class="os-dep">
              <span class="os-dep-name">Python</span>
              <span class="os-dep-desc">编程语言</span>
              <span class="os-dep-license">PSF</span>
            </a>
            <a href="https://github.com/openai/openai-python" target="_blank" class="os-dep">
              <span class="os-dep-name">OpenAI SDK</span>
              <span class="os-dep-desc">LLM API 调用</span>
              <span class="os-dep-license">Apache 2.0</span>
            </a>
            <a href="https://supabase.com/" target="_blank" class="os-dep">
              <span class="os-dep-name">Supabase</span>
              <span class="os-dep-desc">开源 BaaS 平台</span>
              <span class="os-dep-license">Apache 2.0</span>
            </a>
            <a href="https://www.uvicorn.org/" target="_blank" class="os-dep">
              <span class="os-dep-name">Uvicorn</span>
              <span class="os-dep-desc">ASGI 服务器</span>
              <span class="os-dep-license">BSD</span>
            </a>
            <a href="https://python-dotenv.readthedocs.io/" target="_blank" class="os-dep">
              <span class="os-dep-name">python-dotenv</span>
              <span class="os-dep-desc">环境变量管理</span>
              <span class="os-dep-license">BSD</span>
            </a>
          </div>
        </div>

        <!-- AI -->
        <div class="os-card">
          <div class="os-card-header ai">
            <i class="fas fa-brain"></i>
            <h3>AI / 大模型</h3>
          </div>
          <div class="os-card-body">
            <a href="https://www.deepseek.com/" target="_blank" class="os-dep">
              <span class="os-dep-name">DeepSeek</span>
              <span class="os-dep-desc">大语言模型 API</span>
              <span class="os-dep-license">商用</span>
            </a>
            <a href="https://www.xfyun.cn/" target="_blank" class="os-dep">
              <span class="os-dep-name">讯飞星火</span>
              <span class="os-dep-desc">语音 + 大模型 API</span>
              <span class="os-dep-license">商用</span>
            </a>
            <a href="https://www.volcengine.com/" target="_blank" class="os-dep">
              <span class="os-dep-name">火山引擎</span>
              <span class="os-dep-desc">豆包大模型 API</span>
              <span class="os-dep-license">商用</span>
            </a>
          </div>
        </div>

        <!-- 工具链 & 部署 -->
        <div class="os-card">
          <div class="os-card-header tools">
            <i class="fas fa-rocket"></i>
            <h3>工具链 & 部署</h3>
          </div>
          <div class="os-card-body">
            <a href="https://git-scm.com/" target="_blank" class="os-dep">
              <span class="os-dep-name">Git</span>
              <span class="os-dep-desc">版本控制</span>
              <span class="os-dep-license">GPL v2</span>
            </a>
            <a href="https://github.com/" target="_blank" class="os-dep">
              <span class="os-dep-name">GitHub</span>
              <span class="os-dep-desc">代码托管 & CI/CD 部署</span>
              <span class="os-dep-license">SaaS</span>
            </a>
            <a href="https://www.nginx.com/" target="_blank" class="os-dep">
              <span class="os-dep-name">Nginx</span>
              <span class="os-dep-desc">Web 服务器 / 反向代理</span>
              <span class="os-dep-license">BSD</span>
            </a>
            <a href="https://www.postgresql.org/" target="_blank" class="os-dep">
              <span class="os-dep-name">PostgreSQL</span>
              <span class="os-dep-desc">关系型数据库（Supabase 底层）</span>
              <span class="os-dep-license">PostgreSQL</span>
            </a>
            <a href="https://axios-http.com/" target="_blank" class="os-dep">
              <span class="os-dep-name">Axios</span>
              <span class="os-dep-desc">HTTP 客户端</span>
              <span class="os-dep-license">MIT</span>
            </a>
          </div>
        </div>
      </div>

      <!-- 项目信息 -->
      <div class="os-footer-card">
        <h3>关于本项目</h3>
        <p>基智（Jizhi）是一个面向大学生的一站式学习平台，集学科计划、题库训练、AI 诊断、社区交流于一体。后端使用 FastAPI + Supabase（PostgreSQL），前端 Vue 3，部署于 GitHub，项目源码和文档将逐步开放。</p>
        <div class="os-meta">
          <span class="os-ver">v1.0.0-alpha</span>
          <span class="os-divider">|</span>
          <span>Built with ❤️ by Jizhi Team</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.os-page {
  min-height: 100vh;
  background: linear-gradient(180deg,
    rgba(15,23,42,.95) 0%,
    rgba(17,24,39,.95) 100%
  );
  display: flex;
  flex-direction: column;
  animation: osFadeIn 0.35s ease;
}
@keyframes osFadeIn {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 顶栏 */
.os-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  background: rgba(255,255,255,0.02);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  flex-shrink: 0;
}
.os-back {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.06);
  background: rgba(255,255,255,0.03);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
}
.os-back:hover {
  background: rgba(255,255,255,0.08);
  color: var(--text-primary);
  transform: translateX(-2px);
}
.os-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}
.os-spacer { width: 80px; }

/* 主体可滚动 */
.os-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px 40px;
  max-width: 1100px;
  margin: 0 auto;
  width: 100%;
}

.os-subtitle {
  color: var(--text-secondary);
  font-size: 14px;
  text-align: center;
  margin-bottom: 20px;
}

.os-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

@media (max-width: 768px) {
  .os-body { padding: 16px; }
  .os-grid { grid-template-columns: 1fr; }
  .os-spacer { display: none; }
}

.os-card {
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px;
  overflow: hidden;
  transition: all 0.3s ease;
}
.os-card:hover {
  border-color: rgba(255,255,255,0.10);
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
}
.os-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  font-size: 16px;
  font-weight: 600;
  color: #e2e8f0;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.os-card-header i { font-size: 18px; }
.os-card-header.frontend { background: linear-gradient(135deg, rgba(59,130,246,0.15), rgba(99,102,241,0.08)); }
.os-card-header.backend { background: linear-gradient(135deg, rgba(16,185,129,0.15), rgba(20,184,166,0.08)); }
.os-card-header.ai { background: linear-gradient(135deg, rgba(168,85,247,0.15), rgba(236,72,153,0.08)); }
.os-card-header.tools { background: linear-gradient(135deg, rgba(245,158,11,0.15), rgba(234,179,8,0.08)); }

.os-card-body {
  display: flex;
  flex-direction: column;
}
.os-dep {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 18px;
  text-decoration: none;
  color: var(--text-secondary);
  transition: all 0.2s ease;
  border-bottom: 1px solid rgba(255,255,255,0.02);
}
.os-dep:last-child { border-bottom: none; }
.os-dep:hover {
  background: rgba(255,255,255,0.04);
  color: var(--text-primary);
  transform: translateX(4px);
}
.os-dep-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
  min-width: 80px;
  flex-shrink: 0;
}
.os-dep-desc {
  font-size: 12px;
  flex: 1;
}
.os-dep-license {
  font-size: 10px;
  color: var(--text-muted);
  background: rgba(255,255,255,0.04);
  padding: 2px 8px;
  border-radius: 6px;
  flex-shrink: 0;
}

.os-footer-card {
  margin-top: 16px;
  padding: 24px 28px;
  background: rgba(255,255,255,0.03);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 14px;
  text-align: center;
}
.os-footer-card h3 {
  font-size: 18px;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.os-footer-card p {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.7;
  max-width: 640px;
  margin: 0 auto 14px;
}
.os-meta {
  font-size: 12px;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.os-ver {
  background: rgba(99,102,241,0.12);
  color: #a78bfa;
  padding: 2px 10px;
  border-radius: 6px;
  font-weight: 600;
}
</style>
