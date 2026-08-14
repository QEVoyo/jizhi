<template>
  <div class="du-root">
    <!-- 3D 太阳系背景画布 -->
    <div ref="hub3dRef" class="hub-3d"></div>

    <!-- 顶栏 -->
    <div class="du-topbar">
      <button class="g-btn" @click="goBack"><el-icon><ArrowLeft /></el-icon> 返回</button>
      <h1>维度宇宙</h1>
      <button class="g-btn" @click="loadData" :disabled="loading">
        <el-icon :class="{ spin: loading }"><Refresh /></el-icon>
      </button>
    </div>

    <!-- 底栏提示 -->
    <div class="du-bottombar" v-if="!activeDim">
      <span><el-icon><Mouse /></el-icon> 拖拽旋转</span>
      <span><el-icon><ZoomIn /></el-icon> 滚轮缩放</span>
      <span>点击星球进入维度</span>
    </div>

    <!-- 维度信息浮层 -->
    <Transition name="fade">
      <div v-if="hoveredPlanet && !activeDim" class="planet-tooltip" :style="tooltipStyle">
        <div class="tt-name">{{ hoveredPlanet.label }}</div>
        <div class="tt-sub">{{ hoveredPlanet.sub }}</div>
      </div>
    </Transition>

    <!-- ====== 详情面板 ====== -->
    <Transition name="detail">
      <div v-if="activeDim" class="detail-panel">
        <div class="dp-header">
          <button class="g-btn" @click="closeDetail"><el-icon><ArrowLeft /></el-icon> 返回宇宙</button>
          <h2 :style="{ color: currentDim?.color || '#fff' }">{{ currentDim?.label || '' }}</h2>
        </div>
        <div class="dp-body">
          <div v-if="activeDim === 'knowledge'">
            <div v-if="hasKnowledge" ref="knowledgeRef" class="chart-box"></div>
            <div v-else class="empty-dim">完成一些题目后，知识星系将为你点亮，展示各知识点的掌握度分布</div>
          </div>
          <div v-else-if="activeDim === 'ability'">
            <div v-if="hasAbility" ref="radarRef" class="chart-box"></div>
            <div v-else class="empty-dim">完成题目后，能力雷达将从六个维度分析你的学习能力</div>
          </div>
          <div v-else-if="activeDim === 'rhythm'" class="rhythm-wrap">
            <div v-if="hasRhythm" ref="calendarRef" class="chart-box"></div>
            <div v-else class="empty-dim">开始学习后，这里会展示你的学习热力日历和活跃分析</div>
            <div class="rhythm-stats" v-if="hasRhythm">
              <div class="rs"><span class="rs-v">{{ data.learning_rhythm?.current_streak || 0 }}</span><span>连续(天)</span></div>
              <div class="rs"><span class="rs-v">{{ data.learning_rhythm?.max_streak || 0 }}</span><span>最长连续</span></div>
              <div class="rs"><span class="rs-v">{{ data.learning_rhythm?.total_active_days || 0 }}</span><span>活跃天数</span></div>
            </div>
          </div>
          <div v-else-if="activeDim === 'cognitive'">
            <div v-if="hasCognitive" ref="cognitiveBarRef" class="chart-box" style="height:280px"></div>
            <div v-else class="empty-dim">使用 AI 生成题目后，这里会展示你的题型偏好和知识点兴趣分布</div>
          </div>
          <div v-else-if="activeDim === 'mistake'">
            <div v-if="hasMistakes" ref="treemapRef" class="chart-box"></div>
            <div v-else class="empty-dim">做题后如果产生了错题，这里会用树图展示你的易错知识点分布</div>
          </div>
          <div v-else-if="activeDim === 'growth'">
            <div v-if="hasGrowth" ref="growthRef" class="chart-box"></div>
            <div v-else class="empty-dim">持续学习后，这里会展示你掌握度的变化轨迹</div>
          </div>
          <div v-else-if="activeDim === 'personality'" class="personality-card">
            <div class="pc-glow"></div>
            <div class="pc-type">{{ data.personality?.type || '探索型学习者' }}</div>
            <div class="pc-tags"><span v-for="t in data.personality?.tags||['数据采集中']" :key="t" class="pc-tag">{{ t }}</span></div>
            <p class="pc-desc">{{ data.personality?.description || '完成更多学习任务后，AI 将为你生成详细的个性化学习人格画像。' }}</p>
          </div>
          <div v-else-if="activeDim === 'interest'">
            <div v-if="hasInterest" ref="interest3dRef" class="int-3d"></div>
            <div v-else class="empty-dim">生成题目后，兴趣星云将展示你的知识探索领域分布，可拖拽旋转的 3D 球体</div>
          </div>
          <div v-else-if="activeDim === 'summary'" class="summary-box">
            <p class="sb-text">{{ displaySummary }}<span v-if="typing" class="sb-cursor">|</span></p>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 加载层 -->
    <Transition name="fade">
      <div v-if="loading && !activeDim" class="load-overlay">
        <div class="lo-ring"></div>
        <span>扫描维度中...</span>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ArrowLeft, Refresh, Mouse, ZoomIn } from '@element-plus/icons-vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { CSS3DRenderer, CSS3DObject } from 'three/addons/renderers/CSS3DRenderer.js'
import * as echarts from 'echarts'
import 'echarts-gl'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const activeDim = ref(null)
const hoveredPlanet = ref(null)
const tooltipStyle = ref({})
const data = ref({ knowledge_base:{}, ability_radar:{}, learning_rhythm:{}, cognitive_preference:{}, mistake_map:{}, growth_trajectory:{}, personality:{}, interest_field:{}, ai_summary:'' })
const displaySummary = ref('')
const typing = ref(false)

const dimensions = [
  { key:'knowledge',  label:'知识星系', sub:'掌握度 · 力导向图', color:'#409eff', orbit:2.8, speed:0.15, size:1.4 },
  { key:'ability',    label:'能力雷达', sub:'六维 · 雷达图',     color:'#8b5cf6', orbit:3.6, speed:0.12, size:1.1 },
  { key:'rhythm',     label:'学习节奏', sub:'活跃度 · 热力日历', color:'#10b981', orbit:4.4, speed:0.10, size:1.0 },
  { key:'cognitive',  label:'认知偏好', sub:'题型分布 · 条形图', color:'#f59e0b', orbit:5.2, speed:0.09, size:1.0 },
  { key:'mistake',    label:'易错地图', sub:'错题分析 · 树图',   color:'#ef4444', orbit:6.0, speed:0.08, size:1.2 },
  { key:'growth',     label:'成长轨迹', sub:'趋势 · 渐近线',     color:'#06b6d4', orbit:6.8, speed:0.07, size:1.0 },
  { key:'personality',label:'学习人格', sub:'AI 画像 · 深度洞察',color:'#ec4899', orbit:7.6, speed:0.06, size:1.3 },
  { key:'interest',   label:'兴趣星云', sub:'知识领域 · 3D 球体',color:'#f97316', orbit:8.4, speed:0.05, size:1.1 },
  { key:'summary',    label:'AI 洞见',  sub:'智能总结 · 打字机', color:'#a78bfa', orbit:9.2, speed:0.04, size:1.0 },
]
const currentDim = computed(() => dimensions.find(d => d.key === activeDim.value))

// 数据存在性检查
const hasKnowledge = computed(() => (data.value.knowledge_base?.list || []).length > 0)
const hasAbility = computed(() => Object.keys(data.value.ability_radar || {}).length > 0 && data.value.knowledge_base?.list?.length > 0)
const hasRhythm = computed(() => (data.value.learning_rhythm?.total_active_days || 0) > 0)
const hasCognitive = computed(() => (data.value.cognitive_preference?.types || []).length > 0)
const hasMistakes = computed(() => (data.value.mistake_map?.list || []).length > 0)
const hasGrowth = computed(() => (data.value.growth_trajectory?.points || []).length > 1)
const hasInterest = computed(() => (data.value.interest_field?.list || []).length > 0)

// ===== Three.js 太阳系 =====
const hub3dRef = ref(null)
function createGlowTexture() {
  const c = document.createElement('canvas'); c.width = 64; c.height = 64
  const ctx = c.getContext('2d')
  const g = ctx.createRadialGradient(32, 32, 0, 32, 32, 32)
  g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.05, 'rgba(255,255,255,0.8)')
  g.addColorStop(0.3, 'rgba(180,200,255,0.3)'); g.addColorStop(0.7, 'rgba(100,130,200,0.03)')
  g.addColorStop(1, 'rgba(0,0,0,0)')
  ctx.fillStyle = g; ctx.fillRect(0, 0, 64, 64)
  return new THREE.CanvasTexture(c)
}

let scene, camera, renderer, controls, flyAnimId
let planets = [], planetMeshes = [], animationId
const raycaster = new THREE.Raycaster()
const mouse = new THREE.Vector2()

function initSolarSystem() {
  const el = hub3dRef.value; if (!el) return
  const W = el.clientWidth, H = el.clientHeight

  scene = new THREE.Scene()
  // 电影级深空背景 — 极暗，微偏蓝
  scene.background = new THREE.Color(0x020210)
  scene.fog = new THREE.FogExp2(0x020210, 0.00008)

  camera = new THREE.PerspectiveCamera(55, W / H, 1, 60)
  camera.position.set(0, 12, 18)
  camera.lookAt(0, 0, 0)

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false })
  renderer.setSize(W, H); renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.shadowMap.enabled = true
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.2
  el.appendChild(renderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true; controls.dampingFactor = 0.08
  controls.minDistance = 6; controls.maxDistance = 35
  controls.target.set(0, 0, 0)
  controls.autoRotate = true; controls.autoRotateSpeed = 0.3

  // 远层微星 — 5000颗极暗，模拟真实星空密度
  const bgStarsGeo = new THREE.BufferGeometry()
  const bgp = new Float32Array(5000 * 3)
  for (let i = 0; i < 5000 * 3; i++) bgp[i] = (Math.random() - 0.5) * 100
  bgStarsGeo.setAttribute('position', new THREE.BufferAttribute(bgp, 3))
  scene.add(new THREE.Points(bgStarsGeo, new THREE.PointsMaterial({ color: 0xccddff, size: 0.028, transparent: true, opacity: 0.65 })))

  // 填充层 — 3000颗散布全空间，消除空洞感
  const fillGeo = new THREE.BufferGeometry()
  const fp2 = new Float32Array(3000 * 3)
  for (let i = 0; i < 3000 * 3; i++) fp2[i] = (Math.random() - 0.5) * 85
  fillGeo.setAttribute('position', new THREE.BufferAttribute(fp2, 3))
  scene.add(new THREE.Points(fillGeo, new THREE.PointsMaterial({ color: 0x8899bb, size: 0.035, transparent: true, opacity: 0.5 })))

  // 中层银河带 — 2000颗，集中在水平面
  const midStarsGeo = new THREE.BufferGeometry()
  const mp = new Float32Array(2000 * 3)
  for (let i = 0; i < 2000; i++) {
    const a = Math.random() * Math.PI * 2
    const r = 8 + Math.random() * 38
    mp[i*3] = Math.cos(a) * r + (Math.random()-0.5)*8
    mp[i*3+1] = (Math.random()-0.5) * 3.5
    mp[i*3+2] = Math.sin(a) * r + (Math.random()-0.5)*8
  }
  midStarsGeo.setAttribute('position', new THREE.BufferAttribute(mp, 3))
  scene.add(new THREE.Points(midStarsGeo, new THREE.PointsMaterial({ color: 0xeeeeff, size: 0.05, transparent: true, opacity: 0.45, blending: THREE.AdditiveBlending, depthWrite: false })))

  // 近层亮星 — 300颗，白/蓝白
  const nearStarsGeo = new THREE.BufferGeometry()
  const nsp = new Float32Array(300 * 3); const ncol = new Float32Array(300 * 3)
  for (let i = 0; i < 300; i++) {
    nsp[i*3] = (Math.random()-0.5) * 55; nsp[i*3+1] = (Math.random()-0.5) * 30; nsp[i*3+2] = (Math.random()-0.5) * 55
    const temp = 0.7 + Math.random() * 0.3
    ncol[i*3] = temp; ncol[i*3+1] = temp * (0.85 + Math.random() * 0.1); ncol[i*3+2] = 0.9 + Math.random() * 0.1
  }
  nearStarsGeo.setAttribute('position', new THREE.BufferAttribute(nsp, 3))
  nearStarsGeo.setAttribute('color', new THREE.BufferAttribute(ncol, 3))
  scene.add(new THREE.Points(nearStarsGeo, new THREE.PointsMaterial({ size: 0.13, vertexColors: true, transparent: true, opacity: 0.55, blending: THREE.AdditiveBlending, depthWrite: false, map: createGlowTexture() })))

  // 暗尘带 — 极淡的深灰粒子，在银河面附近
  for (let l = 0; l < 2; l++) {
    const dustGeo = new THREE.BufferGeometry()
    const dp = []; const r = 16 + l * 8
    for (let i = 0; i < 3000; i++) {
      const a = Math.random() * Math.PI * 2; const rr = r - 2 + Math.random() * 4
      dp.push(Math.cos(a) * rr, (Math.random()-0.5) * 1.2, Math.sin(a) * rr)
    }
    dustGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(dp), 3))
    scene.add(new THREE.Points(dustGeo, new THREE.PointsMaterial({ color: 0x1a1a2e, size: 0.06, transparent: true, opacity: 0.25 - l * 0.08, depthWrite: false })))
  }

  // 远处微星云 — just 2 subtle blobs
  for (let n = 0; n < 2; n++) {
    const nebGeo = new THREE.BufferGeometry()
    const np2 = []
    const cx = (n === 0 ? -12 : 10); const cz = (n === 0 ? -8 : 12)
    for (let i = 0; i < 150; i++) {
      np2.push(cx + (Math.random()-0.5)*10, (Math.random()-0.5)*3, cz + (Math.random()-0.5)*10)
    }
    nebGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(np2), 3))
    scene.add(new THREE.Points(nebGeo, new THREE.PointsMaterial({ color: 0x1a1a3a, size: 0.2, transparent: true, opacity: 0.06, blending: THREE.AdditiveBlending, depthWrite: false })))
  }

  // 中央恒星 — 体感白热核心（径向渐变）
  const sunCore = new THREE.Mesh(
    new THREE.SphereGeometry(0.55, 64, 64),
    new THREE.ShaderMaterial({
      uniforms: {},
      vertexShader: `varying vec3 vP;void main(){vP=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
      fragmentShader: `varying vec3 vP;void main(){float d=length(vP)/0.55;vec3 c=mix(vec3(1.0,0.98,0.92),vec3(1.0,0.82,0.45),d*0.65);gl_FragColor=vec4(c,1.0);}`
    })
  )
  scene.add(sunCore)
  // 内日冕：白→淡金渐变
  const innerCorona = new THREE.Mesh(
    new THREE.SphereGeometry(0.85, 32, 32),
    new THREE.ShaderMaterial({
      uniforms: {},
      vertexShader: `varying vec3 vN;void main(){vN=normalize(normalMatrix*normal);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
      fragmentShader: `varying vec3 vN;void main(){float f=1.0-abs(dot(vN,vec3(0,0,1)));gl_FragColor=vec4(1.0,0.95,0.8,f*0.3);}`,
      transparent: true, depthWrite: false
    })
  )
  scene.add(innerCorona)
  // 外日冕：淡白→透明，大范围
  const outerCorona = new THREE.Mesh(
    new THREE.SphereGeometry(1.5, 32, 32),
    new THREE.ShaderMaterial({
      uniforms: {},
      vertexShader: `varying vec3 vN;void main(){vN=normalize(normalMatrix*normal);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
      fragmentShader: `varying vec3 vN;void main(){float f=pow(1.0-abs(dot(vN,vec3(0,0,1))),2.5);gl_FragColor=vec4(0.9,0.85,0.75,f*0.12);}`,
      transparent: true, depthWrite: false
    })
  )
  scene.add(outerCorona)
  // 极远光晕
  const farGlow = new THREE.Mesh(
    new THREE.SphereGeometry(2.2, 16, 16),
    new THREE.ShaderMaterial({
      uniforms: {},
      vertexShader: `varying vec3 vN;void main(){vN=normalize(normalMatrix*normal);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
      fragmentShader: `varying vec3 vN;void main(){float f=pow(1.0-abs(dot(vN,vec3(0,0,1))),4.0);gl_FragColor=vec4(0.7,0.7,0.8,f*0.04);}`,
      transparent: true, depthWrite: false
    })
  )
  scene.add(farGlow)
  // 光晕sprite — 镜头光晕感
  const flareTex = createGlowTexture()
  const flareSprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: flareTex, color: 0xffeedd, transparent: true, opacity: 0.15, blending: THREE.AdditiveBlending, depthWrite: false }))
  flareSprite.scale.set(6, 6, 1)
  scene.add(flareSprite)

  // 轨道环
  dimensions.forEach(d => {
    const orbitPts = []; for (let i = 0; i <= 128; i++) { const a = (i / 128) * Math.PI * 2; orbitPts.push(Math.cos(a) * d.orbit, 0, Math.sin(a) * d.orbit) }
    const orbitGeo = new THREE.BufferGeometry()
    orbitGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(orbitPts), 3))
    scene.add(new THREE.Line(orbitGeo, new THREE.LineBasicMaterial({ color: new THREE.Color(d.color), transparent: true, opacity: 0.05, depthWrite: false })))
  })

  // 创建行星
  planetMeshes = []
  planets = dimensions.map((d, i) => {
    const group = new THREE.Group()
    // 球体
    const pGeo = new THREE.SphereGeometry(d.size * 0.5, 32, 32)
    const pMat = new THREE.MeshStandardMaterial({ color: new THREE.Color(d.color), roughness: 0.5, metalness: 0.15 })
    const mesh = new THREE.Mesh(pGeo, pMat)
    mesh.userData = { dimKey: d.key, dimIndex: i }
    group.add(mesh)
    // 大气层
    const atmoGeo = new THREE.SphereGeometry(d.size * 0.58, 16, 16)
    const atmoMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(d.color), transparent: true, opacity: 0.06, depthWrite: false })
    group.add(new THREE.Mesh(atmoGeo, atmoMat))
    // 光环（某些行星）
    if (i % 3 === 0) {
      const ringG = new THREE.TorusGeometry(d.size * 0.75, 0.03, 8, 48)
      ringG.rotateX(Math.PI / 2.5)
      group.add(new THREE.Mesh(ringG, new THREE.MeshBasicMaterial({ color: new THREE.Color(d.color), transparent: true, opacity: 0.15, depthWrite: false })))
    }
    // Sprite 标签（随距离缩放）
    const canvas = document.createElement('canvas')
    canvas.width = 256; canvas.height = 64
    const ctx = canvas.getContext('2d')
    ctx.font = 'bold 28px -apple-system, sans-serif'
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
    ctx.fillStyle = 'rgba(255,255,255,0.7)'; ctx.fillText(d.label, 128, 32)
    const tex = new THREE.CanvasTexture(canvas); tex.minFilter = THREE.LinearFilter
    const spriteMat = new THREE.SpriteMaterial({ map: tex, transparent: true, opacity: 0.6, depthTest: false })
    const sprite = new THREE.Sprite(spriteMat)
    sprite.scale.set(d.size * 1.6, d.size * 0.4, 1)
    sprite.position.y = d.size * 0.9
    group.add(sprite)

    scene.add(group)
    planetMeshes.push(mesh)
    return { group, mesh, data: d, angle: Math.random() * Math.PI * 2 }
  })

  // 灯光 — 模拟恒星照明
  scene.add(new THREE.AmbientLight(0x1a1a33, 0.45))
  const sunLight = new THREE.PointLight(0xfff8ee, 3.5, 45, 1.5)
  sunLight.position.set(0, 0, 0)
  scene.add(sunLight)
  const fillLight = new THREE.PointLight(0x445577, 1.0, 55, 2)
  fillLight.position.set(0, 18, 0)
  scene.add(fillLight)

  // 动画循环
  function anim() {
    animationId = requestAnimationFrame(anim)
    planets.forEach((p, i) => {
      p.angle += dimensions[i].speed * 0.02
      const a = p.angle; const r = dimensions[i].orbit
      p.group.position.set(Math.cos(a) * r, Math.sin(a * 0.3) * 0.8, Math.sin(a) * r)
      p.mesh.rotation.y += 0.01
    })
    controls.update()
    renderer.render(scene, camera)
  }
  anim()

  // 点击检测
  el.addEventListener('click', onHubClick)
  el.addEventListener('mousemove', onHubMove)
  // 响应式
  new ResizeObserver(() => {
    const w = el.clientWidth, h = el.clientHeight
    if (w > 0 && h > 0) { camera.aspect = w / h; camera.updateProjectionMatrix(); renderer.setSize(w, h) }
  }).observe(el)
}

function onHubMove(e) {
  mouse.x = (e.clientX / window.innerWidth) * 2 - 1
  mouse.y = -(e.clientY / window.innerHeight) * 2 + 1
  raycaster.setFromCamera(mouse, camera)
  const hits = raycaster.intersectObjects(planetMeshes)
  if (hits.length) {
    const d = dimensions[hits[0].object.userData.dimIndex]
    hoveredPlanet.value = d
    document.body.style.cursor = 'pointer'
  } else {
    hoveredPlanet.value = null
    document.body.style.cursor = ''
  }
}

function onHubClick(e) {
  if (!hoveredPlanet.value) return
  const d = hoveredPlanet.value
  // 飞行动画：相机靠近行星
  const planet = planets.find(p => p.data.key === d.key)
  if (!planet) { activeDim.value = d.key; return }
  const target = planet.group.position.clone()
  const start = { x: camera.position.x, y: camera.position.y, z: camera.position.z, tx: controls.target.x, ty: controls.target.y, tz: controls.target.z }
  const end = { x: target.x + 3, y: target.y + 1.5, z: target.z + 3, tx: target.x, ty: target.y, tz: target.z }
  const dur = 600; const st = performance.now()
  function fly(now) {
    const p = Math.min(1, (now - st) / dur)
    const e = 1 - Math.pow(1 - p, 3)
    camera.position.set(start.x + (end.x - start.x) * e, start.y + (end.y - start.y) * e, start.z + (end.z - start.z) * e)
    controls.target.set(start.tx + (end.tx - start.tx) * e, start.ty + (end.ty - start.ty) * e, start.tz + (end.tz - start.tz) * e)
    if (p < 1) flyAnimId = requestAnimationFrame(fly)
    else { activeDim.value = d.key; setTimeout(() => renderDetail(d.key), 300) }
  }
  flyAnimId = requestAnimationFrame(fly)
}

function closeDetail() {
  activeDim.value = null
  controls.target.set(0, 0, 0)
  camera.position.set(0, 12, 18)
  camera.lookAt(0, 0, 0)
}

function destroySolar() {
  if (animationId) cancelAnimationFrame(animationId)
  if (flyAnimId) cancelAnimationFrame(flyAnimId)
  if (renderer) { renderer.dispose(); renderer = null }
  if (hub3dRef.value) hub3dRef.value.innerHTML = ''
}

// ===== 数据 =====
async function loadData() {
  loading.value = true
  try {
    const res = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'}/evaluation/profile-data?user_id=${authStore.user.id}`,
      { headers: { Authorization: `Bearer ${authStore.token}` } })
    data.value = await res.json()
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

// ===== 详情图表 =====
const charts = {}
function getChart(k, ref, opts) {
  if (charts[k]) { charts[k].dispose(); charts[k] = null }
  if (!ref.value) return
  charts[k] = echarts.init(ref.value)
  charts[k].setOption({ backgroundColor: 'transparent', ...opts })
}

function renderDetail(key) {
  const d = data.value
  // 仅当数据存在时才渲染图表
  if (key === 'knowledge' && !hasKnowledge.value) return
  if (key === 'ability' && !hasAbility.value) return
  if (key === 'rhythm' && !hasRhythm.value) return
  if (key === 'cognitive' && !hasCognitive.value) return
  if (key === 'mistake' && !hasMistakes.value) return
  if (key === 'growth' && !hasGrowth.value) return
  if (key === 'interest' && !hasInterest.value) return
  switch (key) {
    case 'knowledge': {
      const list = d.knowledge_base?.list || []
      if (!list.length) return
      const nodes = list.map((it, i) => ({ name: it.name, value: it.score, symbolSize: 10 + it.score * 0.25,
        itemStyle: { color: scoreColor(it.score), shadowBlur: 15, shadowColor: scoreColor(it.score) + '66' },
        label: { show: true, fontSize: 10, color: '#bbb', formatter: p => p.name.length > 6 ? p.name.slice(0, 6) + '..' : p.name }
      }))
      let ed = []; for (let i = 0; i < nodes.length; i++) for (let j = i + 1; j < nodes.length; j++) if (Math.random() < 0.08) ed.push({ source: i, target: j, lineStyle: { color: 'rgba(255,255,255,0.03)', width: 0.5 } })
      getChart('knowledge', knowledgeRef, { series: [{ type: 'graph', layout: 'force', roam: true, draggable: true, force: { repulsion: 250, edgeLength: [60, 160], gravity: 0.05 }, data: nodes, edges: ed, emphasis: { focus: 'adjacency' }, edgeSymbol: ['none', 'none'] }] })
      break
    }
    case 'ability': {
      const rd = d.ability_radar || {}; const ks = Object.keys(rd)
      if (!ks.length) return
      getChart('radar', radarRef, {
        radar: { indicator: ks.map(k => ({ name: k, max: 100 })), center: ['50%','55%'], radius: '60%', axisName: { color: '#aaa', fontSize: 11 }, splitArea: { areaStyle: { color: ['rgba(64,158,255,0.01)','rgba(64,158,255,0.03)'] } }, axisLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } } },
        series: [{ type: 'radar', data: [{ value: ks.map(k => rd[k]?.score || 0), name: '能力', areaStyle: { color: 'rgba(139,92,246,0.12)' }, lineStyle: { color: '#8b5cf6', width: 2 }, itemStyle: { color: '#8b5cf6' } }] }]
      })
      break
    }
    case 'rhythm': {
      const cal = d.learning_rhythm?.calendar || []
      if (!cal.length) return
      getChart('calendar', calendarRef, {
        tooltip: { formatter: p => `${p.value[0]}<br/>${p.value[1]} 次活动` },
        visualMap: { min: 0, max: Math.max(...cal.map(c => c.count), 3), orient: 'horizontal', left: 'center', bottom: 0, inRange: { color: ['rgba(255,255,255,0.01)','#10b98133','#10b981'] }, textStyle: { color: '#888' } },
        calendar: { range: cal.length > 30 ? [cal[0].date, cal[cal.length-1].date] : undefined, cellSize: ['auto', 13], itemStyle: { borderColor: 'rgba(255,255,255,0.02)' }, dayLabel: { color: '#777' }, monthLabel: { color: '#999' } },
        series: [{ type: 'heatmap', coordinateSystem: 'calendar', data: cal.map(c => [c.date, c.count]) }]
      })
      break
    }
    case 'cognitive': {
      const ts = d.cognitive_preference?.types || []
      if (!ts.length) return
      getChart('cogBar', cognitiveBarRef, {
        grid: { left: '22%', right: '8%', top: 10, bottom: 10 },
        xAxis: { type: 'value', axisLabel: { color: '#888' }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.03)' } } },
        yAxis: { type: 'category', data: ts.map(t => t.name).reverse(), axisLabel: { color: '#aaa', fontSize: 12 }, axisLine: { show: false } },
        series: [{ type: 'bar', data: ts.map(t => t.value).reverse(), barWidth: '45%', itemStyle: { borderRadius: [0,4,4,0], color: new echarts.graphic.LinearGradient(0,0,1,0, [{offset:0,color:'#f59e0b33'},{offset:1,color:'#f59e0b'}]) }, label: { show: true, position: 'right', color: '#aaa', fontSize: 11 } }]
      })
      break
    }
    case 'mistake': {
      const ml = d.mistake_map?.list || []
      if (!ml.length) return
      getChart('treemap', treemapRef, { tooltip: { formatter: p => `${p.name}<br/>错题：${p.value}` },
        series: [{ type: 'treemap', data: ml.map(m => ({ name: m.name, value: m.total })), roam: false, label: { show: true, color: '#ccc', fontSize: 12, formatter: p => `${p.name}\n${p.value}` }, itemStyle: { borderColor: 'rgba(255,255,255,0.04)', gapWidth: 2 }, levels: [{ colorMapping: 'value', color: ['rgba(34,197,94,0.2)','rgba(239,68,68,0.5)'] }] }]
      })
      break
    }
    case 'growth': {
      const pts = d.growth_trajectory?.points || []
      if (!pts.length) return
      getChart('growth', growthRef, {
        grid: { left: '8%', right: '6%', top: 20, bottom: 30 },
        xAxis: { type: 'category', data: pts.map(p => p.date.slice(5)), axisLabel: { color: '#888', fontSize: 10, rotate: 30 }, axisLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } } },
        yAxis: { type: 'value', min: 0, max: 100, axisLabel: { color: '#888' }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.02)' } } },
        series: [{ type: 'line', data: pts.map(p => p.score), smooth: true, lineStyle: { color: '#06b6d4', width: 2 }, areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1, [{offset:0,color:'rgba(6,182,212,0.25)'},{offset:1,color:'rgba(6,182,212,0.01)'}]) }, itemStyle: { color: '#06b6d4' }, symbol: 'circle', symbolSize: 3 }]
      })
      break
    }
    case 'interest': initInterest3D(); break
    case 'summary': typeSummary(); break
  }
}

// 兴趣 3D 球体
let intrScene, intrCam, intrRenderer, intrLabel, intrCtrl, intrAnim
function initInterest3D() {
  destroyIntr3D()
  const el = interest3dRef.value; if (!el) return
  const W = el.clientWidth || 400, H = el.clientHeight || 340
  intrScene = new THREE.Scene(); intrScene.background = new THREE.Color(0x020210)
  intrCam = new THREE.PerspectiveCamera(45, W/H, 1, 600); intrCam.position.z = 260
  intrRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true }); intrRenderer.setSize(W, H); intrRenderer.setPixelRatio(1.5)
  el.appendChild(intrRenderer.domElement)
  intrLabel = new CSS3DRenderer(); intrLabel.setSize(W, H); intrLabel.domElement.style.cssText = 'position:absolute;top:0;left:0;pointer-events:none'
  el.appendChild(intrLabel.domElement)
  intrCtrl = new OrbitControls(intrCam, intrRenderer.domElement); intrCtrl.enableDamping = true; intrCtrl.autoRotate = true; intrCtrl.autoRotateSpeed = 1

  const bgGeo = new THREE.BufferGeometry(); const bp = new Float32Array(800 * 3)
  for (let i = 0; i < 800 * 3; i++) bp[i] = (Math.random() - 0.5) * 400
  bgGeo.setAttribute('position', new THREE.BufferAttribute(bp, 3))
  intrScene.add(new THREE.Points(bgGeo, new THREE.PointsMaterial({ color: 0x445588, size: 0.8, transparent: true, opacity: 0.5 })))

  const list = data.value.interest_field?.list || []
  if (!list.length) return
  const maxC = Math.max(...list.map(t => t.count), 1); const R = 100
  const clrs = ['#409eff','#8b5cf6','#f59e0b','#22c55e','#ec4899','#06b6d4','#f97316','#a78bfa','#60a5fa','#f472b6','#2dd4bf','#818cf8']
  list.forEach((item, i) => {
    const phi = Math.acos(1 - 2 * (i + 0.5) / list.length)
    const theta = Math.PI * (1 + Math.sqrt(5)) * i
    const x = R * Math.sin(phi) * Math.cos(theta), y = R * Math.cos(phi), z = R * Math.sin(phi) * Math.sin(theta)
    const div = document.createElement('div')
    div.textContent = item.name
    const sz = 13 + (item.count / maxC) * 12
    div.style.cssText = `color:#fff;font-size:${sz}px;font-weight:600;padding:3px 14px;border-radius:16px;border:1px solid ${clrs[i%clrs.length]}44;background:rgba(0,0,0,0.4);white-space:nowrap;text-shadow:0 0 6px ${clrs[i%clrs.length]}44`
    const lbl = new CSS3DObject(div); lbl.position.set(x, y, z); lbl.quaternion.setFromUnitVectors(new THREE.Vector3(0,0,1), new THREE.Vector3(x,y,z).normalize())
    intrScene.add(lbl)
  })
  intrScene.add(new THREE.Mesh(new THREE.SphereGeometry(R*0.96, 20, 14), new THREE.MeshBasicMaterial({ color: 0x334466, wireframe: true, transparent: true, opacity: 0.02 })))
  function anim() { intrAnim = requestAnimationFrame(anim); intrCtrl.update(); intrRenderer.render(intrScene, intrCam); intrLabel.render(intrScene, intrCam) }
  anim()
}
function destroyIntr3D() {
  if (intrAnim) { cancelAnimationFrame(intrAnim); intrAnim = null }
  if (intrRenderer && typeof intrRenderer.dispose === 'function') { intrRenderer.dispose(); intrRenderer = null }
  if (intrLabel && typeof intrLabel.dispose === 'function') { intrLabel.dispose(); intrLabel = null }
  if (interest3dRef.value) interest3dRef.value.innerHTML = ''
}

function typeSummary() {
  typing.value = true; displaySummary.value = ''
  const text = data.value.ai_summary || '完成更多题目后，AI 将为你生成深度画像总结。'
  let i = 0; const t = setInterval(() => { displaySummary.value += text[i]; i++; if (i >= text.length) { clearInterval(t); typing.value = false } }, 40)
}

function scoreColor(s) { if (s >= 80) return '#22c55e'; if (s >= 60) return '#eab308'; if (s >= 40) return '#f97316'; return '#ef4444' }
function goBack() { router.push('/evaluation-center') }

const knowledgeRef=ref(null),radarRef=ref(null),calendarRef=ref(null),cognitiveBarRef=ref(null),treemapRef=ref(null),growthRef=ref(null),interest3dRef=ref(null)

onMounted(() => { loadData(); setTimeout(initSolarSystem, 200) })
onBeforeUnmount(() => { destroySolar(); destroyIntr3D(); Object.values(charts).forEach(c => c?.dispose()) })
</script>

<style scoped>
.du-root { width: 100vw; height: 100vh; overflow: hidden; position: relative; background: #060610; }
.hub-3d { width: 100%; height: 100%; position: absolute; inset: 0; }

.du-topbar { position: absolute; top: 0; left: 0; right: 0; z-index: 10; display: flex; justify-content: space-between; align-items: center; padding: 14px 22px; pointer-events: none; }
.du-topbar > * { pointer-events: auto; }
.du-topbar h1 { font-size: 18px; font-weight: 600; color: rgba(255,255,255,0.7); margin: 0; letter-spacing: 2px; }
.du-bottombar { position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%); z-index: 10; display: flex; gap: 24px; font-size: 10px; color: rgba(255,255,255,0.2); letter-spacing: 0.5px; }
.du-bottombar span { display: flex; align-items: center; gap: 5px; }

.g-btn { display: inline-flex; align-items: center; gap: 5px; padding: 5px 12px; font-size: 11px; font-weight: 500; color: rgba(255,255,255,0.4); background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.04); border-radius: 6px; cursor: pointer; transition: all 0.3s; font-family: inherit; }
.g-btn:hover { background: rgba(255,255,255,0.06); color: rgba(255,255,255,0.7); border-color: rgba(255,255,255,0.1); }

/* 行星提示 */
.planet-tooltip { position: fixed; z-index: 15; pointer-events: none; text-align: center; }
.tt-name { font-size: 12px; font-weight: 600; color: rgba(255,255,255,0.8); letter-spacing: 0.5px; }
.tt-sub { font-size: 9px; color: rgba(255,255,255,0.35); margin-top: 3px; }

/* 详情面板 — 3D 立体 */
.detail-panel {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%) perspective(1200px) rotateX(2deg);
  z-index: 20; max-width: 700px; width: 90%; max-height: 80vh; overflow-y: auto;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(20,20,50,0.9) 0%, rgba(8,8,25,0.94) 100%);
  backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow:
    0 2px 0 rgba(255,255,255,0.03) inset,
    0 8px 40px rgba(0,0,0,0.5),
    0 24px 80px rgba(0,0,0,0.4),
    0 0 0 1px rgba(255,255,255,0.03);
  transition: transform 0.4s cubic-bezier(0.4,0,0.2,1);
}
.detail-panel:hover {
  transform: translate(-50%,-50%) perspective(1200px) rotateX(1deg) translateY(-4px);
  box-shadow:
    0 2px 0 rgba(255,255,255,0.04) inset,
    0 12px 48px rgba(0,0,0,0.6),
    0 32px 96px rgba(0,0,0,0.5),
    0 0 0 1px rgba(255,255,255,0.05);
}
.detail-panel::-webkit-scrollbar { width: 3px; }
.detail-panel::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.06); border-radius: 2px; }

.dp-header {
  display: flex; align-items: center; gap: 16px; padding: 18px 24px;
  position: sticky; top: 0; z-index: 2;
  background: linear-gradient(180deg, rgba(15,15,40,0.85) 0%, rgba(10,10,30,0.4) 100%);
  backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
  border-radius: 20px 20px 0 0;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  box-shadow: 0 1px 0 rgba(255,255,255,0.02) inset;
}
.dp-header h2 { font-size: 18px; margin: 0; text-shadow: 0 0 12px currentColor; }
.dp-body { padding: 20px 28px 32px; }
.chart-box { width: 100%; height: 340px; border-radius: 12px; overflow: hidden; }
.int-3d {
  width: 100%; height: 340px; position: relative; overflow: hidden; border-radius: 12px;
  background: radial-gradient(ellipse at center, rgba(64,158,255,0.03), transparent 70%);
  box-shadow: 0 0 0 1px rgba(255,255,255,0.03) inset;
}

.rhythm-stats { display: flex; gap: 32px; justify-content: center; margin-top: 16px; }
.rs { text-align: center; } .rs-v { display: block; font-size: 26px; font-weight: 700; color: #10b981; font-family: monospace; } .rs span:last-child { font-size: 11px; color: rgba(255,255,255,0.4); }

.personality-card { position: relative; text-align: center; padding: 48px 32px; border-radius: 20px; background: linear-gradient(135deg, rgba(236,72,153,0.04), rgba(139,92,246,0.04)); border: 1px solid rgba(236,72,153,0.08); overflow: hidden; }
.pc-glow { position: absolute; inset: 0; background: radial-gradient(ellipse at center, rgba(236,72,153,0.04), transparent 60%); animation: gp 3s infinite; }
@keyframes gp { 0%,100% { transform: scale(1); opacity: 0.5; } 50% { transform: scale(1.1); opacity: 1; } }
.pc-type { position: relative; font-size: 38px; font-weight: 800; background: linear-gradient(135deg, #ec4899, #8b5cf6, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-size: 200% 200%; animation: st 3s infinite; margin-bottom: 16px; }
@keyframes st { 0%,100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }
.pc-tags { position: relative; display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin-bottom: 20px; }
.pc-tag { padding: 6px 20px; border-radius: 20px; font-size: 14px; font-weight: 600; background: rgba(236,72,153,0.08); color: #ec4899; border: 1px solid rgba(236,72,153,0.12); }
.pc-desc { position: relative; font-size: 15px; line-height: 1.8; color: rgba(255,255,255,0.6); max-width: 560px; margin: 0 auto; }

.summary-box { padding: 40px 20px; text-align: center; }
.sb-text { font-size: 20px; line-height: 2; color: rgba(255,255,255,0.75); display: inline; }
.sb-cursor { font-size: 20px; color: #a78bfa; animation: blink 0.8s step-end infinite; }
@keyframes blink { 50% { opacity: 0; } }

.load-overlay { position: fixed; inset: 0; z-index: 30; display: flex; flex-direction: column; align-items: center; justify-content: center; background: rgba(0,0,0,0.6); backdrop-filter: blur(6px); gap: 14px; color: rgba(255,255,255,0.5); font-size: 13px; }
.lo-ring { width: 36px; height: 36px; border: 2px solid rgba(64,158,255,0.12); border-top-color: #409eff; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.empty-dim { text-align: center; padding: 60px 30px; color: rgba(255,255,255,0.3); font-size: 13px; line-height: 1.8; }

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.detail-enter-active { transition: all 0.5s cubic-bezier(0.4,0,0.2,1); }
.detail-leave-active { transition: all 0.3s ease; }
.detail-enter-from { opacity: 0; transform: scale(1.05); }
.detail-leave-to { opacity: 0; }
</style>
