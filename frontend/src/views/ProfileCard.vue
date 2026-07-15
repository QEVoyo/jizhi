<template>
  <div class="profile-card-page">
    <div class="profile-container">
      <!-- ===== 顶部 ===== -->
      <div class="profile-header">
        <div class="header-left">
          <el-button text class="back-btn" @click="goBack">
            <i class="fas fa-arrow-left"></i> 返回
          </el-button>
          <h1>六维画像</h1>
          <el-tag size="small" type="info">{{ generateDate }}</el-tag>
        </div>
        <el-button size="small" type="primary" @click="refreshData" :loading="loading">
          <i class="fas fa-sync"></i> 刷新
        </el-button>
      </div>

      <el-divider />

      <div v-if="loading" class="loading-state">
        <i class="fas fa-spinner fa-spin"></i> 加载中...
      </div>

      <div v-else class="profile-content">
        <!-- ===== 1. 知识基础（星系图） ===== -->
        <div class="dimension-section">
          <div class="section-title">
            <span class="section-icon">K</span> 知识基础
          </div>
          <div class="section-body">
            <div v-if="!dimData.knowledge_base?.list?.length" class="empty-tip">
              暂无数据
            </div>
            <div v-else>
              <div ref="knowledgeGraphRef" style="width: 100%; height: 340px;"></div>
            </div>
          </div>
        </div>

        <!-- ===== 2. 认知风格（饼图） ===== -->
        <div class="dimension-section">
          <div class="section-title">
            <span class="section-icon">C</span> 认知风格
          </div>
          <div class="section-body">
            <div v-if="!Object.keys(dimData.cognitive_style?.distribution || {}).length" class="empty-tip">
              暂无数据
            </div>
            <div v-else class="pie-wrapper">
              <div ref="pieChartRef" style="width: 100%; height: 260px;"></div>
              <div class="pie-label">
                {{ dimData.cognitive_style?.label || '未分析' }}
              </div>
            </div>
          </div>
        </div>

        <!-- ===== 3. 易错偏好（气泡图） ===== -->
        <div class="dimension-section">
          <div class="section-title">
            <span class="section-icon">E</span> 易错偏好
          </div>
          <div class="section-body">
            <div v-if="dimData.mistake_pattern?.total === 0" class="empty-tip">
              暂无错题
            </div>
            <div v-else>
              <div class="bubble-stats">
                <span class="bubble-stat learning">
                  <span class="bubble-dot red"></span> 未攻克：{{ dimData.mistake_pattern.learning?.length || 0 }}
                </span>
                <span class="bubble-stat conquered">
                  <span class="bubble-dot green"></span> 已攻克：{{ dimData.mistake_pattern.conquered?.length || 0 }}
                </span>
                <span class="bubble-stat rate">
                  攻克率：{{ dimData.mistake_pattern.conquered_rate || 0 }}%
                </span>
              </div>
              <div class="bubble-cloud">
                <div
                  v-for="t in dimData.mistake_pattern.learning"
                  :key="'l-' + t"
                  class="bubble learning-bubble"
                  :style="{
                    fontSize: (14 + Math.random() * 8) + 'px',
                    padding: (6 + Math.random() * 8) + 'px ' + (12 + Math.random() * 16) + 'px',
                    animationDelay: (Math.random() * 0.5) + 's'
                  }"
                >
                  {{ t }}
                </div>
                <div
                  v-for="t in dimData.mistake_pattern.conquered"
                  :key="'c-' + t"
                  class="bubble conquered-bubble"
                  :style="{
                    fontSize: (12 + Math.random() * 6) + 'px',
                    padding: (4 + Math.random() * 6) + 'px ' + (10 + Math.random() * 12) + 'px',
                    animationDelay: (Math.random() * 0.5) + 's'
                  }"
                >
                  {{ t }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ===== 4. 学习目标（柱状图） ===== -->
        <div class="dimension-section">
          <div class="section-title">
            <span class="section-icon">G</span> 学习目标
          </div>
          <div class="section-body">
            <div v-if="!dimData.learning_goal?.sets?.length" class="empty-tip">
              暂无题集
            </div>
            <div v-else>
              <div ref="goalChartRef" style="width: 100%; height: 220px;"></div>
              <div class="goal-summary">
                共 {{ dimData.learning_goal.total_sets }} 个题集，{{ dimData.learning_goal.total_questions }} 道题目
              </div>
            </div>
          </div>
        </div>

        <!-- ===== 5. 学习人格 ===== -->
        <div class="dimension-section personality-section">
          <div class="section-title">
            <span class="section-icon">P</span> 学习人格
          </div>
          <div class="section-body">
            <div v-if="!dimData.personality" class="empty-tip">
              暂无数据
            </div>
            <div v-else class="personality-hero">
              <div class="personality-glow"></div>
              <div class="personality-type-hero">{{ dimData.personality.type }}</div>
              <div class="personality-tags-hero">
                <span
                  v-for="tag in dimData.personality.tags"
                  :key="tag"
                  class="personality-tag-hero"
                >
                  {{ tag }}
                </span>
              </div>
              <div class="personality-desc-hero">
                {{ dimData.personality.description }}
              </div>
            </div>
          </div>
        </div>

        <!-- ===== 6. 兴趣领域（3D 球体） ===== -->
        <div class="dimension-section">
          <div class="section-title">
            <span class="section-icon">I</span> 兴趣领域
          </div>
          <div class="section-body">
            <div v-if="!dimData.interest_field?.list?.length" class="empty-tip">
              暂无数据
            </div>
            <div v-else ref="sphereContainerRef" class="sphere-container">
              <div ref="threeContainerRef" class="three-container"></div>
              <div class="sphere-hint">🖱 拖拽旋转 · 滚轮缩放</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { CSS3DRenderer, CSS3DObject } from 'three/addons/renderers/CSS3DRenderer.js'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const generateDate = ref('')
const knowledgeGraphRef = ref(null)
const pieChartRef = ref(null)
const goalChartRef = ref(null)
const threeContainerRef = ref(null)
const sphereContainerRef = ref(null)
let knowledgeGraph = null
let pieChart = null
let goalChart = null
let scene, camera, renderer, labelRenderer, controls
let labelObjects = []
let animationId = null

const dimData = ref({
  knowledge_base: { list: [] },
  cognitive_style: { distribution: {} },
  mistake_pattern: { total: 0, learning: [], conquered: [], conquered_rate: 0 },
  learning_goal: { sets: [], total_sets: 0, total_questions: 0 },
  personality: null,
  interest_field: { list: [] }
})

// 20种颜色（红→黄→绿渐变）
const masteryColors = [
  '#FF0000', '#FF1A00', '#FF3300', '#FF4D00', '#FF6600',
  '#FF8000', '#FF9900', '#FFB300', '#FFCC00', '#FFE600',
  '#D4E000', '#A8D500', '#7DCC00', '#52C200', '#26B800',
  '#00AD00', '#00A300', '#009900', '#008000', '#006600'
]

const colorPalette = [
  '#409EFF', '#8B5CF6', '#F59E0B', '#22C55E', '#EC4899',
  '#06B6D4', '#F472B6', '#34D399', '#FB923C', '#A78BFA',
  '#60A5FA', '#F87171', '#2DD4BF', '#F97316', '#818CF8',
  '#34D399', '#F472B6', '#E879F9'
]

function getColor(score) {
  const index = Math.min(Math.floor(score / 5), 19)
  return masteryColors[index] || '#888'
}

// ===== 知识基础星系图 =====
function loadKnowledgeGraph() {
  if (!knowledgeGraphRef.value) return
  if (knowledgeGraph) { knowledgeGraph.dispose(); knowledgeGraph = null }

  const list = dimData.value.knowledge_base?.list || []
  if (!list.length) return

  const nodes = list.map((item, index) => {
    const color = getColor(item.score)
    return {
      name: item.name,
      value: item.score,
      symbolSize: 16 + item.score * 0.4,
      itemStyle: {
        color: color,
        shadowBlur: 25,
        shadowColor: color + '88',
        borderColor: color + '44',
        borderWidth: 2,
        color: new echarts.graphic.RadialGradient(0.3, 0.3, 0.5, [
          { offset: 0, color: '#ffffff' },
          { offset: 0.3, color: color },
          { offset: 1, color: color + '88' }
        ])
      },
      label: {
        show: true,
        fontSize: 12,
        color: 'rgba(255,255,255,0.9)',
        fontWeight: '500',
        formatter: (params) => params.name,
        textShadowBlur: 6,
        textShadowColor: 'rgba(0,0,0,0.6)'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 16,
          fontWeight: 'bold',
          color: '#fff',
          textShadowBlur: 12,
          textShadowColor: 'rgba(0,0,0,0.8)'
        },
        itemStyle: {
          shadowBlur: 40,
          shadowColor: color + 'cc',
          borderColor: '#fff',
          borderWidth: 3
        }
      }
    }
  })

  const edges = []
  const connectedPairs = new Set()
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const diff = Math.abs(nodes[i].value - nodes[j].value)
      const connectChance = Math.max(0, 0.5 - diff / 200)
      if (Math.random() < connectChance * 0.6 + 0.1) {
        const key = `${Math.min(i,j)}-${Math.max(i,j)}`
        if (!connectedPairs.has(key)) {
          connectedPairs.add(key)
          edges.push({
            source: i,
            target: j,
            lineStyle: {
              color: 'rgba(255,255,255,0.06)',
              width: 0.8 + Math.random() * 0.5,
              curveness: 0.2 + Math.random() * 0.3
            }
          })
        }
      }
    }
  }

  knowledgeGraph = echarts.init(knowledgeGraphRef.value)
  knowledgeGraph.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(0,0,0,0.75)',
      borderColor: 'rgba(255,255,255,0.06)',
      borderWidth: 1,
      textStyle: { color: '#fff', fontSize: 13 },
      formatter: (params) => {
        if (params.dataType === 'node') {
          const score = params.value
          const color = getColor(score)
          const level = score >= 80 ? '优秀' : score >= 60 ? '良好' : score >= 40 ? '一般' : '待提升'
          return `
            <div style="font-weight:600;font-size:15px;margin-bottom:4px;">${params.name}</div>
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:2px;">
              <span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:${color};"></span>
              <span>掌握度：<strong style="color:${color};">${score}%</strong></span>
            </div>
            <div style="color:rgba(255,255,255,0.5);font-size:12px;">评级：${level}</div>
          `
        }
        return ''
      }
    },
    series: [{
      type: 'graph',
      layout: 'force',
      force: {
        repulsion: 350,
        edgeLength: [120, 220],
        gravity: 0.08,
        friction: 0.12
      },
      roam: true,
      draggable: true,
      data: nodes,
      edges: edges,
      focusNodeAdjacency: true,
      edgeSymbol: ['none', 'none'],
      lineStyle: {
        color: 'rgba(255,255,255,0.04)',
        width: 1,
        curveness: 0.2
      },
      label: {
        show: true,
        position: 'bottom',
        fontSize: 12,
        color: 'rgba(255,255,255,0.8)',
        distance: 6
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: {
          width: 2,
          color: 'rgba(255,255,255,0.15)'
        }
      }
    }],
    backgroundColor: 'transparent'
  })
  knowledgeGraph.resize()
}

// ===== 3D 球体（兴趣领域） =====
function initThreeSphere() {
  const container = threeContainerRef.value
  if (!container) return

  if (renderer) {
    renderer.dispose()
    labelRenderer.dispose()
  }
  if (animationId) {
    cancelAnimationFrame(animationId)
    animationId = null
  }

  const width = container.clientWidth || 400
  const height = container.clientHeight || 300

  scene = new THREE.Scene()

  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000)
  camera.position.set(0, 0, 300)

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setClearColor(0x000000, 0)
  container.appendChild(renderer.domElement)

  // CSS3DRenderer - 标签固定在3D空间
  labelRenderer = new CSS3DRenderer()
  labelRenderer.setSize(width, height)
  labelRenderer.domElement.style.position = 'absolute'
  labelRenderer.domElement.style.top = '0'
  labelRenderer.domElement.style.left = '0'
  labelRenderer.domElement.style.pointerEvents = 'none'
  labelRenderer.domElement.style.background = 'transparent'
  container.appendChild(labelRenderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controls.autoRotate = true
  controls.autoRotateSpeed = 1.5
  controls.minDistance = 150
  controls.maxDistance = 500
  controls.enablePan = false
  controls.target.set(0, 0, 0)

  const starsGeometry = new THREE.BufferGeometry()
  const starsCount = 500
  const starPositions = new Float32Array(starsCount * 3)
  for (let i = 0; i < starsCount * 3; i++) {
    starPositions[i] = (Math.random() - 0.5) * 600
  }
  starsGeometry.setAttribute('position', new THREE.BufferAttribute(starPositions, 3))
  const starsMaterial = new THREE.PointsMaterial({
    color: 0x444466,
    size: 1.5,
    transparent: true,
    opacity: 0.6
  })
  const stars = new THREE.Points(starsGeometry, starsMaterial)
  scene.add(stars)

  const list = dimData.value.interest_field?.list || []
  if (list.length === 0) return

  const maxCount = Math.max(...list.map(t => t.count), 1)
  const radius = 120
  const total = list.length

  list.forEach((item, index) => {
    const phi = Math.acos(1 - 2 * (index + 0.5) / total)
    const theta = Math.PI * (1 + Math.sqrt(5)) * (index + 0.5)
    const x = radius * Math.sin(phi) * Math.cos(theta)
    const y = radius * Math.cos(phi)
    const z = radius * Math.sin(phi) * Math.sin(theta)

    const color = colorPalette[index % colorPalette.length]
    const countRatio = item.count / maxCount
    const baseSize = 16 + countRatio * 12

    const div = document.createElement('div')
    div.textContent = item.name
    div.style.color = color
    div.style.fontSize = baseSize + 'px'
    div.style.fontWeight = '600'
    div.style.padding = '4px 14px'
    div.style.borderRadius = '20px'
    div.style.border = `1px solid ${color}44`
    div.style.background = `${color}0a`
    div.style.backdropFilter = 'blur(4px)'
    div.style.boxShadow = '0 2px 12px rgba(0,0,0,0.04)'
    div.style.transition = 'all 0.3s ease'
    div.style.pointerEvents = 'auto'
    div.style.cursor = 'default'
    div.style.whiteSpace = 'nowrap'

    const countSpan = document.createElement('span')
    countSpan.textContent = item.count
    countSpan.style.fontSize = '10px'
    countSpan.style.opacity = '0.5'
    countSpan.style.marginLeft = '4px'
    countSpan.style.fontWeight = '400'
    div.appendChild(countSpan)

    // CSS3DObject - 固定在3D空间
    const label = new CSS3DObject(div)
    label.position.set(x, y, z)
    // 朝向球外（法线方向）
    const direction = new THREE.Vector3(x, y, z).normalize()
    label.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), direction)
    scene.add(label)
    labelObjects.push(label)
  })

  const wireframeGeometry = new THREE.SphereGeometry(radius * 0.98, 24, 16)
  const wireframeMaterial = new THREE.MeshBasicMaterial({
    color: 0x409EFF,
    wireframe: true,
    transparent: true,
    opacity: 0.06
  })
  const wireframe = new THREE.Mesh(wireframeGeometry, wireframeMaterial)
  scene.add(wireframe)

  const glowGeometry = new THREE.SphereGeometry(radius * 0.02, 8, 8)
  const glowMaterial = new THREE.MeshBasicMaterial({
    color: 0x409EFF,
    transparent: true,
    opacity: 0.08
  })
  const glow = new THREE.Mesh(glowGeometry, glowMaterial)
  scene.add(glow)

  function animate() {
    animationId = requestAnimationFrame(animate)
    controls.update()
    renderer.render(scene, camera)
    labelRenderer.render(scene, camera)
  }
  animate()

  const resizeObserver = new ResizeObserver(() => {
    const w = container.clientWidth
    const h = container.clientHeight
    if (w > 0 && h > 0) {
      camera.aspect = w / h
      camera.updateProjectionMatrix()
      renderer.setSize(w, h)
      labelRenderer.setSize(w, h)
    }
  })
  resizeObserver.observe(container)
  container._resizeObserver = resizeObserver
}

function destroyThreeSphere() {
  if (animationId) {
    cancelAnimationFrame(animationId)
    animationId = null
  }

  // ✅ 加判空，防止报错
  if (renderer && typeof renderer.dispose === 'function') {
    renderer.dispose()
    renderer = null
  }

  // ✅ 核心修复：加判空
  if (labelRenderer && typeof labelRenderer.dispose === 'function') {
    labelRenderer.dispose()
    labelRenderer = null
  }

  if (controls && typeof controls.dispose === 'function') {
    controls.dispose()
    controls = null
  }

  scene = null
  labelObjects = []

  if (threeContainerRef.value) {
    threeContainerRef.value.innerHTML = ''
  }
}

// ===== 饼图 =====
function loadPieChart() {
  if (!pieChartRef.value) return
  if (pieChart) { pieChart.dispose(); pieChart = null }

  const dist = dimData.value.cognitive_style?.distribution || {}
  const data = Object.entries(dist).map(([name, value]) => ({ name, value }))
  if (!data.length) return

  pieChart = echarts.init(pieChartRef.value)
  const colors = ['#409EFF', '#8B5CF6', '#F59E0B', '#22C55E', '#EC4899', '#06B6D4']

  pieChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} 道 ({d}%)',
      backgroundColor: 'rgba(0,0,0,0.7)',
      borderColor: 'rgba(255,255,255,0.1)',
      textStyle: { color: '#fff' }
    },
    color: colors,
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      avoidLabelOverlap: true,
      itemStyle: {
        borderRadius: 8,
        borderColor: 'rgba(255,255,255,0.08)',
        borderWidth: 2
      },
      label: {
        color: 'rgba(255,255,255,0.8)',
        fontSize: 13,
        formatter: '{b}\n{d}%'
      },
      labelLine: {
        lineStyle: { color: 'rgba(255,255,255,0.12)' }
      },
      data: data,
      animationDuration: 800
    }]
  })
  pieChart.resize()
}

// ===== 学习目标柱状图 =====
function loadGoalChart() {
  if (!goalChartRef.value) return
  if (goalChart) { goalChart.dispose(); goalChart = null }

  const sets = dimData.value.learning_goal?.sets || []
  if (!sets.length) return

  goalChart = echarts.init(goalChartRef.value)
  const names = sets.map(s => s.name.length > 8 ? s.name.slice(0, 8) + '..' : s.name)
  const counts = sets.map(s => s.question_count)

  goalChart.setOption({
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        const p = params[0]
        const fullName = sets[p.dataIndex].name
        return `<strong>${fullName}</strong><br/>题目数：${p.value} 道`
      },
      backgroundColor: 'rgba(0,0,0,0.7)',
      borderColor: 'rgba(255,255,255,0.1)',
      textStyle: { color: '#fff' }
    },
    grid: {
      left: '8%',
      right: '8%',
      bottom: '18%',
      top: '8%'
    },
    xAxis: {
      type: 'category',
      data: names,
      axisLabel: {
        color: 'rgba(255,255,255,0.5)',
        fontSize: 11,
        rotate: 20,
        interval: 0
      },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      name: '题目数',
      nameTextStyle: { color: 'rgba(255,255,255,0.3)', fontSize: 11 },
      axisLabel: { color: 'rgba(255,255,255,0.3)', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } },
      axisLine: { show: false },
      axisTick: { show: false }
    },
    series: [{
      type: 'bar',
      data: counts.map((v, i) => ({
        value: v,
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: colorPalette[i % colorPalette.length] },
            { offset: 1, color: colorPalette[(i + 3) % colorPalette.length] + '44' }
          ])
        }
      })),
      barWidth: '35%',
      label: {
        show: true,
        position: 'top',
        color: 'rgba(255,255,255,0.5)',
        fontSize: 11
      }
    }]
  })
  goalChart.resize()
}

// ===== 加载数据 =====
async function loadData() {
  loading.value = true
  try {
    const res = await fetch(
      `${import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'}/evaluation/profile-data?user_id=${authStore.user.id}`,
      { headers: { Authorization: `Bearer ${authStore.token}` } }
    )
    const data = await res.json()
    dimData.value = data
    generateDate.value = new Date().toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit'
    })
    await nextTick()
    setTimeout(() => {
      loadKnowledgeGraph()
      loadPieChart()
      loadGoalChart()
      destroyThreeSphere()
      setTimeout(() => initThreeSphere(), 100)
    }, 300)
  } catch (error) {
    console.error('加载失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

async function refreshData() {
  await loadData()
  ElMessage.success('已刷新')
}

function goBack() {
  router.push('/evaluation-center')
}

function handleResize() {
  if (knowledgeGraphRef.value && knowledgeGraph) {
    knowledgeGraph.resize()
  }
  if (threeContainerRef.value && renderer) {
    const w = threeContainerRef.value.clientWidth
    const h = threeContainerRef.value.clientHeight
    if (w > 0 && h > 0) {
      camera.aspect = w / h
      camera.updateProjectionMatrix()
      renderer.setSize(w, h)
      labelRenderer.setSize(w, h)
    }
  }
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  destroyThreeSphere()
  if (knowledgeGraph) { knowledgeGraph.dispose() }
  if (pieChart) { pieChart.dispose() }
  if (goalChart) { goalChart.dispose() }
})

watch(() => dimData.value.interest_field?.list, (newVal) => {
  if (newVal && newVal.length > 0 && threeContainerRef.value) {
    destroyThreeSphere()
    setTimeout(() => initThreeSphere(), 50)
  }
}, { deep: true })
</script>

<style scoped>
.profile-card-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 30px 20px;
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  background-repeat: no-repeat;
}
[data-theme="light"] .profile-card-page {
  background-image: url('/assets/bg/resource_lib_bg.jpg');
}
[data-theme="dark"] .profile-card-page {
  background-image: url('/assets/bg/resource_lib_bl.jpg');
}

.profile-container {
  max-width: 860px;
  width: 100%;
  margin: 0 auto;
  padding: 28px 36px;
  border-radius: 18px;
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: 0 8px 32px rgba(0,0,0,0.06);
}
[data-theme="dark"] .profile-container {
  background: rgba(0,0,0,0.30);
}

.profile-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
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
  background: rgba(255,255,255,0.06);
}
.profile-header h1 {
  font-size: 22px;
  color: var(--text-primary);
  margin: 0;
}

.el-divider { margin: 12px 0; }
.loading-state { text-align: center; padding: 60px 20px; color: var(--text-muted); }

.dimension-section {
  margin-bottom: 20px;
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255,255,255,0.02);
}
.section-title {
  padding: 12px 18px;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.3px;
  color: var(--text-primary);
  background: rgba(255,255,255,0.02);
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.section-icon {
  display: inline-block;
  width: 24px;
  height: 24px;
  line-height: 24px;
  text-align: center;
  font-size: 12px;
  font-weight: 700;
  border-radius: 6px;
  background: rgba(64,158,255,0.08);
  color: #409EFF;
  margin-right: 10px;
}
.section-body { padding: 14px 18px; }
.empty-tip { color: var(--text-muted); font-size: 13px; text-align: center; padding: 8px 0; }

/* ===== 知识基础星系图 ===== */
.knowledge-graph-wrapper {
  width: 100%;
  height: 340px;
}

/* ===== 认知风格 ===== */
.pie-wrapper { position: relative; }
.pie-label {
  text-align: center;
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 6px;
  letter-spacing: 0.5px;
}

/* ===== 易错偏好气泡图 ===== */
.bubble-stats {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.bubble-stat {
  display: flex;
  align-items: center;
  gap: 6px;
}
.bubble-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}
.bubble-dot.red { background: #EF4444; }
.bubble-dot.green { background: #22C55E; }

.bubble-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  min-height: 80px;
  align-items: center;
  justify-content: center;
  padding: 8px;
}
.bubble {
  border-radius: 24px;
  font-weight: 600;
  transition: all 0.3s ease;
  cursor: default;
  animation: bubbleFloat 0.6s ease both;
  border: 1px solid transparent;
}
.bubble:hover {
  transform: scale(1.1) !important;
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  z-index: 2;
}
.learning-bubble {
  background: rgba(239,68,68,0.10);
  color: #EF4444;
  border-color: rgba(239,68,68,0.15);
}
.conquered-bubble {
  background: rgba(34,197,94,0.10);
  color: #22C55E;
  border-color: rgba(34,197,94,0.15);
}
@keyframes bubbleFloat {
  0% { opacity: 0; transform: scale(0.5) translateY(10px); }
  100% { opacity: 1; transform: scale(1) translateY(0); }
}

/* ===== 学习目标 ===== */
.goal-summary {
  text-align: center;
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(255,255,255,0.03);
}

/* ===== 学习人格 ===== */
.personality-hero {
  position: relative;
  padding: 28px 24px 24px;
  border-radius: 16px;
  text-align: center;
  overflow: hidden;
  background: linear-gradient(135deg, rgba(64,158,255,0.06), rgba(139,92,246,0.06));
  border: 1px solid rgba(64,158,255,0.10);
}
.personality-glow {
  position: absolute;
  top: -40%;
  left: -20%;
  width: 140%;
  height: 140%;
  background: radial-gradient(ellipse at center, rgba(64,158,255,0.08), transparent 70%);
  animation: glowPulse 3s ease-in-out infinite;
  pointer-events: none;
}
@keyframes glowPulse {
  0%, 100% { transform: scale(1); opacity: 0.6; }
  50% { transform: scale(1.1); opacity: 1; }
}
.personality-type-hero {
  position: relative;
  font-size: 32px;
  font-weight: 800;
  letter-spacing: 1px;
  margin-bottom: 12px;
  background: linear-gradient(135deg, #409EFF, #8B5CF6, #F59E0B);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: shimmerText 4s ease-in-out infinite;
}
@keyframes shimmerText {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}
.personality-tags-hero {
  position: relative;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
  margin-bottom: 14px;
}
.personality-tag-hero {
  padding: 6px 18px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  background: rgba(64,158,255,0.12);
  color: #409EFF;
  border: 1px solid rgba(64,158,255,0.15);
  box-shadow: 0 0 20px rgba(64,158,255,0.05);
  backdrop-filter: blur(4px);
  transition: all 0.3s ease;
}
.personality-tag-hero:hover {
  transform: scale(1.05);
  box-shadow: 0 0 30px rgba(64,158,255,0.15);
}
.personality-desc-hero {
  position: relative;
  font-size: 15px;
  line-height: 1.8;
  color: var(--text-secondary);
  max-width: 560px;
  margin: 0 auto;
}

/* ===== 3D 球体 ===== */
.sphere-container {
  position: relative;
  width: 100%;
  height: 340px;
  overflow: hidden;
  border-radius: 12px;
  background: radial-gradient(ellipse at center, rgba(64,158,255,0.03), transparent 70%);
}
.three-container {
  width: 100%;
  height: 100%;
  position: relative;
}
.three-container :deep(.css3d-renderer) {
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  pointer-events: none !important;
}
.three-container :deep(.css3d-renderer) div {
  pointer-events: auto !important;
}
.sphere-hint {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 12px;
  color: var(--text-muted);
  opacity: 0.4;
  pointer-events: none;
}

@media (max-width: 640px) {
  .profile-container { padding: 16px 14px; }
  .profile-header { flex-direction: column; align-items: stretch; }
  .knowledge-graph-wrapper { height: 260px; }
  .mistake-stats { gap: 12px; font-size: 12px; }
  .personality-type-hero { font-size: 24px; }
  .personality-hero { padding: 20px 16px; }
  .sphere-container { height: 260px; }
  .bubble { font-size: 12px !important; padding: 4px 10px !important; }
}
</style>