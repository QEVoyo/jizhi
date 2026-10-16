<template>
  <div class="tree-page">
    <!-- ===== 顶栏 ===== -->
    <div class="tree-nav">
      <el-button text class="nav-back" @click="router.back()">
        <i class="fas fa-arrow-left"></i>
      </el-button>
      <div class="nav-title">
        <span class="t-main">小基 · 能带你去的地方</span>
        <span class="t-sub">{{ hint }}</span>
      </div>
      <el-button text class="nav-reset" @click="resetView" title="回到初始视图">
        <i class="fas fa-compress"></i>
      </el-button>
    </div>

    <!-- ===== 树 =====
         没有加载遮罩：根节点是**立刻**画出来的，数据回来再长出分支。
         用一个盖住整块的 loading 反而会把已经能看的东西挡掉。 -->
    <div class="tree-wrap">
      <div ref="chartEl" class="tree-chart"></div>
    </div>

    <!-- ===== 图例 ===== -->
    <div class="tree-legend">
      <span class="lg"><i class="dot root"></i>小基</span>
      <span class="lg"><i class="dot branch"></i>分区（点击展开或收起）</span>
      <span class="lg"><i class="dot leaf"></i>页面（点击跳转）</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { useAuthStore } from '@/stores/auth'
import { useNavStore } from '@/stores/nav'
import { STATIC_PAGES, ADMIN_PAGES, AGENT_PAGES } from '@/utils/pageMeta'

const router = useRouter()
const authStore = useAuthStore()
const navStore = useNavStore()

const chartEl = ref(null)
const syllabusCount = ref(0)
let chart = null
let themeObserver = null

const hint = computed(() =>
  syllabusCount.value
    ? `按功能分区展开，到底就是可以进的页面（${syllabusCount.value} 个考纲都在这）`
    : '按功能分区展开，到底就是可以进的页面')

/** 读主题变量。与 AgentDetail.vue 同一套做法 —— 图表不吃 CSS 变量，得自己取。 */
function cssVar(name, fallback) {
  const el = document.querySelector('.tree-page')
  const v = el ? getComputedStyle(el).getPropertyValue(name).trim() : ''
  return v || fallback
}

// ── 树的形状 ────────────────────────────────────────────────
//
// ⚠️ **数据不在这里手写。** 页面清单的唯一来源是 `utils/pageMeta.js`
//    （静态页 + 后台页）和 `navStore.syllabi`（考纲，全局搜索也用它）。
//    第一版把页面清单在组件里抄了一遍 —— 立刻就和搜索对不上：
//    漏了「我的题集」「小基设置」这些，还编了几个不存在的。
//    **手抄的清单一定会漂，而且漂的时候没有任何报错。**
//
//    这里只做一件事：按 `pageMeta` 里的 `group` 字段归拢成树。
//    加页面的人改 `pageMeta.js` 一处，搜索和树同时生效。
//
// 设计约定（改之前先看）：
//   · **只有叶子能跳转**，分区节点点了是展开／收起 ——
//     否则点「学习」会直接跳走，根本展不开。
//   · 分区自己也有页面的，就把它作为该分区下的第一个叶子
//     （如「学科计划」既是分区标题也是 /subject-plan 这一页）。
//   · **到页面为止，不再往下钻**：题目、单条帖子、某个视频这类
//     详情页不做节点 —— 它们是列表点进去的，不是"能到的地方"。

// 版式意象表 —— 悬浮预览照着**这一页真实的版式**画，不是所有页面一个样。
// 取值来自 utils/pageMeta.js 的 wire 字段（那边定义，这边画）。
const WIRE = {
  // 指标卡 + 大图表
  dashboard: '<b class="w-kpis"><i></i><i></i><i></i></b><b class="w-chart"></b>',
  // 左窄栏 + 右侧列表行
  list: '<b class="w-split"><i class="w-side"></i><i class="w-rows"><u></u><u></u><u></u><u></u></i></b>',
  // 表头 + 若干横条
  table: '<b class="w-thead"></b><b class="w-tr"></b><b class="w-tr"></b><b class="w-tr"></b><b class="w-tr"></b>',
  // 左右交替的对话气泡
  chat: '<b class="w-bub left"></b><b class="w-bub right"></b><b class="w-bub left short"></b><b class="w-bub right short"></b>',
  // 竖向时间线
  timeline: '<b class="w-tl"><i></i><u></u><i></i><u></u><i></i><u></u></b>',
  // 输入框 + 按钮
  form: '<b class="w-field"></b><b class="w-field"></b><b class="w-field short"></b><b class="w-btn"></b>',
  // 卡片网格
  board: '<b class="w-grid"><i></i><i></i><i></i><i></i></b>',
  // 语音通话：头像 + 声波
  call: '<b class="w-avatar"></b><b class="w-wave"><i></i><i></i><i></i><i></i><i></i></b>',
  // 大标题 + 正文段落
  detail: '<b class="w-h1"></b><b class="w-p"></b><b class="w-p"></b><b class="w-p short"></b>',
  // 这一页自己：放射状
  tree: '<b class="w-radial"><i class="c"></i><i class="a"></i><i class="b"></i><i class="d"></i><i class="e"></i></b>',
}

const BRANCH = { type: 'branch' }
const LEAF = (path) => ({ type: 'leaf', path })

// 分区的展示顺序。没列到的分区排在最后 —— 万一有人加了新 group 又忘了登记，
// 它会照样出现在树上（而不是被静默丢掉）。
const GROUP_ORDER = ['学习', '评估', '学程', '社区', '小基', '智能体', '我的', '帮助', '管理后台']

function buildTree() {
  const pages = [...STATIC_PAGES]
  const isAdmin = authStore.user?.is_admin || authStore.user?.role !== 'user'
  if (isAdmin) pages.push(...ADMIN_PAGES)
  // ⚠️ AGENT_PAGES 是**单独一份**导出、没有 group 字段 —— 直接 push 进 pages
  //    的话它们会全掉进「其他」兜底分组，还会带出 `agent-center` 这种
  //    原始路径段当标签（截图里左上角那支就是）。给它们补上 group。
  for (const a of AGENT_PAGES) pages.push({ ...a, group: '智能体' })
  for (const s of (navStore.syllabi || [])) {
    pages.push({ title: s.name || s.id, path: `/subject-plan/${s.id}`, group: '学习' })
  }

  // ⚠️ **层级按路径段长，不是硬编两层。** 第一版把每个分区都拍平成
  //    「分区 → 页面」两级，结果整棵树长得像一张导图而不是树 ——
  //    而 /community/friends 本来就住在 /community 底下，
  //    /subject-plan/cet4 本来就住在 /subject-plan 底下。
  //    路径本身就是这棵树的形状，照着它长，深浅自然就错落开了。
  // 根节点就是 /home 这一页 —— 直接取 pageMeta 那条，别手写一份。
  // 手写的那份没有 desc/wire，悬浮出来是个兜底版式，和它作为叶子的身份对不上。
  const home = pages.find(x => x.path === '/home') || {}
  const root = {
    name: '小基', type: 'root', path: '/home',
    desc: home.desc || '', group: home.group || '', wire: home.wire || 'chat',
    children: [],
  }
  const groups = new Map()   // 分区名 → 节点

  for (const p of pages) {
    const g = p.group || '其他'
    if (!groups.has(g)) {
      const node = { name: g, type: 'branch', children: [] }
      groups.set(g, node)
      root.children.push(node)
    }
    const walk = groups.get(g)
    // 按 `/` 切段逐级往下挂；每一段都可能既是"页面"又是"父节点"
    const segs = p.path.split('/').filter(Boolean)
    let cur = walk
    let acc = ''
    for (let i = 0; i < segs.length; i++) {
      acc += '/' + segs[i]
      const isLeaf = i === segs.length - 1
      let next = (cur.children || []).find(c => c.__seg === acc)
      if (!next) {
        next = { name: segs[i], __seg: acc, type: isLeaf ? 'leaf' : 'branch', children: [] }
        cur.children.push(next)
      }
      if (isLeaf) {
        // 用注册表里的中文名，而不是 URL 段
        next.name = p.title
        next.type = 'leaf'
        next.path = p.path
        next.desc = p.desc || ''      // 悬浮预览要用
        next.group = p.group || ''
        next.wire = p.wire || 'detail'
      }
      cur = next
    }
  }

  // 收拾干净：把只为了建树而留的 __seg 去掉；
  // 空 children 也去掉（否则 ECharts 会把叶子画成可展开的分支）。
  const clean = (n) => {
    delete n.__seg
    if (n.children) {
      n.children.forEach(clean)
      n.children = n.children.filter(c => c.name)
      if (!n.children.length) delete n.children
    }
    if (n.children && !n.path && n.type !== 'branch') n.type = 'branch'
    return n
  }
  clean(root)

  // ── 收拾两层冗余（不然每个分区名会连着出现两次）──
  //
  // 分区分组和路径行走各建了一层，于是长出来两种别扭：
  //   · 「学程」分区下面又套一个叫「学程」的页节点（/career）→ 同名两层
  //   · 「小基」分区下面套一个叫 `xiaoji` 的容器（/xiaoji/* 的中间段）→ 原始段名露出来
  // 都是同一件事：**中间容器和它唯一的孩子说的是同一件事**。
  for (const g of root.children) {
    if (!g.children?.length) continue
    const first = g.children[0]
    // 规则一：分区第一个孩子跟分区同名 → 把那个孩子并上来（分区自己变成那一页）
    if (first.name === g.name && first.path && !first.__hasOwnChildren) {
      g.path = first.path || g.path
      g.type = 'leaf'
      g.children = (first.children || []).concat(g.children.slice(1))
    }
    // 规则二：分区只有一个孩子，而那孩子是个纯容器（没挂页面）→ 直接收养它的孩子
    if (g.children.length === 1 && !g.children[0].path) {
      g.children = g.children[0].children || []
    }
  }

  // 分区排序
  root.children.sort((a, b) => {
    const ia = GROUP_ORDER.indexOf(a.name), ib = GROUP_ORDER.indexOf(b.name)
    return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib)
  })
  return root
}

/**
 * 估一个节点框要多宽 —— 汉字按字号算，西文按 0.58 个字号算。
 *
 * ⚠️ 为什么要自己估：ECharts 的树节点**不做文字自适应**。
 *    `symbol` 是圆圈就得把标签甩到外面（于是几十个标签互相压），
 *    想「字装在框里」就必须自己算 symbolSize。
 *    宁可估宽一点 —— 框大一点只是丑，字被裁掉就是不能用。
 */
function boxWidth(name, fontSize) {
  let w = 0
  for (const ch of String(name)) {
    w += /[一-鿿＀-￯]/.test(ch) ? fontSize : fontSize * 0.58
  }
  return Math.ceil(w) + 14      // 左右各留 7px 内边距
}

/** 节点 → ECharts 数据项。 */
function toEcharts(node, depth = 0) {
  const leaf = node.type === 'leaf'
  const isRoot = depth === 0
  // 60+ 个节点挤在一个圆上，叶子越小越不容易糊在一起
  const fs = isRoot ? 13 : leaf ? 10 : 11.5
  const h = isRoot ? 30 : leaf ? 19 : 24

  const item = {
    name: node.name,
    // ⚠️ **节点本身就是个圆角框，字装在里面**（用户 2026-10-16 提的）。
    //    原来是「小圆点 + 甩在外面的标签」—— 那在径向布局下几十个标签
    //    会挤成一团（截图里顶部几个 Agent 就叠在一起了）。
    //    框自带底色，天然互相遮挡，可读性反而好。
    symbol: 'roundRect',
    symbolSize: [boxWidth(node.name, fs), h],
    // ⚠️ **摆正**。径向布局默认把节点和标签**按枝条方向旋转** ——
    //    圆圈上看不出问题，一换成方框就「歪七扭八」：外圈的框全 tilted，
    //    里面的字也跟着斜，整页没法看。方框必须始终水平。
    symbolRotate: 0,
    // 跳转目标挂在自定义字段上 —— ECharts 会原样保留，click 时取得到
    jzPath: node.path || '',
    jzLeaf: leaf,
    jzDesc: node.desc || '',
    jzWire: node.wire || '',
    jzGroup: node.group || (isRoot ? '' : node.name),
    itemStyle: {
      color: isRoot ? cssVar('--brand', '#409eff')
        : leaf ? 'transparent' : cssVar('--viz-muted', '#898781'),
      borderColor: leaf ? cssVar('--viz-s1', '#2a78d6') : 'transparent',
      borderWidth: leaf ? 1 : 0,
      borderRadius: 6,
    },
    label: {
      show: true,
      position: 'inside',
      rotate: 0,
      fontSize: fs,
      // 实心框用白字、空心框用主题色字 —— 否则浅色主题下白字看不见
      color: isRoot || !leaf ? '#fff' : cssVar('--text-primary', '#1f2328'),
      fontWeight: isRoot ? 700 : leaf ? 400 : 600,
    },
  }
  if (node.children) {
    item.children = node.children.map(c => toEcharts(c, depth + 1))
  }
  return item
}

function option() {
  const text = cssVar('--text-primary', '#1f2328')
  const muted = cssVar('--text-secondary', '#4b5563')
  return {
    tooltip: {
      trigger: 'item',
      // ⚠️ 悬浮预览**不用真截图**，用 CSS 画的窗口框。
      //    真截图要给 60 个页面各存一张图（jpeg 压到最小也有 1.5MB 进仓库），
      //    而这一页要的只是"这一页大概长什么样 + 它是干什么的" ——
      //    画个框就能说清，还不用维护那堆图（改了页面还得重拍）。
      //    落地页的 mockup 就是这个路子。
      appendToBody: false,        // 挂在本组件里，scoped 样式才吃得到
      backgroundColor: 'transparent',
      borderWidth: 0,
      padding: 0,
      extraCssText: 'box-shadow:none;',
      formatter: (p) => {
        const d = p.data || {}
        if (!d.jzPath && !d.jzDesc && !d.jzGroup) return `<b>${d.name || ''}</b>`
        const group = d.jzGroup || ''
        return `
          <div class="tp">
            <div class="tp-bar">
              <span class="tp-dots"><i></i><i></i><i></i></span>
              <span class="tp-bar-title">${d.name || ''}</span>
            </div>
            <div class="tp-body">
              <div class="tp-wire">${WIRE[d.jzWire] || WIRE.detail}</div>
              <div class="tp-meta">
                ${group ? `<span class="tp-group">${group}</span>` : ''}
                ${d.jzPath ? `<code class="tp-path">${d.jzPath}</code>` : ''}
              </div>
              ${d.jzDesc ? `<p class="tp-desc">${d.jzDesc}</p>` : ''}
              ${d.jzLeaf ? `<div class="tp-go">点击跳转 →</div>` : `<div class="tp-go muted">点击展开或收起</div>`}
            </div>
          </div>`
      },
    },
    series: [{
      type: 'tree',
      data: [nodes.value],
      // ⚠️ **径向布局**：根在中心、枝条向外发散。
      //    第一版用的 orient:'LR'（从左到右），那画出来是**思维导图/组织架构图**，
      //    不是树 —— 用户一眼就看出来了：「这不是树吧，只是一个导图」。
      //    径向是这页唯一正确的布局：它要的就是"从小基长出整个产品"那个意象。
      layout: 'radial',
      // 根放在偏左的位置而不是正中心：产品名在左、叶子往右上铺，
      // 正中心会让最外圈的标签集体撞到画布边缘。
      center: ['46%', '52%'],
      symbol: 'circle',
      // ⚠️ **全展开**（-1 = 不限制）。设成 1 时整页只看到 9 个分区名、
      //    一片叶子都没有 —— 用户第一反应是「这才一点点页面」。
      //    这一页存在的意义就是**一眼看全**，默认折叠等于把内容藏起来。
      //    层级深了以后枝干会更密，靠 roam 拖动缩放来看。
      initialTreeDepth: -1,
      expandAndCollapse: true,
      roam: true,
      // ⚠️ **必须限幅。** `roam: true` 默认是**无限**缩放 —— 滚轮一直往外滚
      //    能把整棵树缩成一个点，用户找不回来（也没有"重置"的直觉）。
      //    下限 0.4 够小到在小屏上看全，上限 5 够大到读清挤在一起的标签。
      //    树系列支持这个字段是因为 TreeSeriesOption 继承了 RoamOptionMixin。
      scaleLimit: { min: 0.4, max: 5 },
      edgeShape: 'curve',
      // 文字已经在框里了，这里不再单独配 label/leaves.label ——
      // 顶层配了会被每个节点的 label 覆盖，留着只会让人以为它生效。
      // 框之间实测仍会局部相碰，靠 roam 放大看；用 hideOverlap 会留下空框，更怪。
      lineStyle: { color: cssVar('--viz-grid', '#d8d8d2'), width: 1, curveness: 0.5 },
      emphasis: { focus: 'descendant' },
      // 径向 + 60 多个节点，动画太慢会显得卡
      animationDuration: 400,
      animationDurationUpdate: 500,
    }],
  }
}

const nodes = ref(null)

function render() {
  if (!chart || !nodes.value) return
  chart.setOption(option(), true)
}

function resetView() {
  render()
}

async function load() {
  try {
    // 复用 navStore 的缓存：全局搜索打开时已经拉过一次了，这里不会重复请求。
    // ⚠️ 别再自己 listSyllabi() —— 两处各拉一次，缓存就白做了，
    //    而且两边可能拿到不同时刻的数据。
    await navStore.loadSyllabi()
    syllabusCount.value = (navStore.syllabi || []).length
    nodes.value = toEcharts(buildTree())
  } catch (e) {
    console.error('[tree] 考纲拉取失败，按空列表铺树:', e)
    nodes.value = toEcharts(buildTree())
  } finally {
    render()
  }
}

onMounted(async () => {
  await nextTick()
  if (!chartEl.value) return
  // ⚠️ **先把图建起来、再拉数据。** 反过来写的话（先 await load 再 init），
  //    画布要等考纲接口回来才存在 —— 后端慢的时候就是好几秒的白板。
  //    2026-10-16 被端到端检查抓到过：单独跑通过、连着跑 66 条路由后失败，
  //    因为那时后端已经被打热，这一次请求刚好超了等待窗口。
  //    先渲染一个只有根节点的树，数据回来再补分支，观感也更好。
  chart = echarts.init(chartEl.value)
  nodes.value = toEcharts({ name: '小基', type: 'root', path: '/home', children: [] })
  render()
  await load()

  chart.on('click', (p) => {
    const path = p.data?.jzPath
    // 只有叶子跳转；分区交给 expandAndCollapse 自己展开/收起。
    // （根节点例外：它挂的是 /home，点一下回主界面）
    if (path && (p.data.jzLeaf || p.data.name === '小基')) {
      router.push(path)
    }
  })

  // 换主题时重画 —— 图表的颜色是从 CSS 变量读的，不重画就还是旧主题的色
  themeObserver = new MutationObserver(() => render())
  themeObserver.observe(document.documentElement,
    { attributes: true, attributeFilter: ['data-theme'] })

  window.addEventListener('resize', onResize)
})

function onResize() { chart?.resize() }

onBeforeUnmount(() => {
  themeObserver?.disconnect()
  window.removeEventListener('resize', onResize)
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.tree-page {
  display: flex; flex-direction: column;
  height: 100vh; padding: 0 0 10px;
}

.tree-nav {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px; flex: none;
  border-bottom: 1px solid color-mix(in srgb, var(--text-primary) 6%, transparent);
}
.nav-back, .nav-reset { color: var(--text-secondary); }
.nav-title { flex: 1; min-width: 0; }
.t-main { display: block; font-size: 15px; font-weight: 600; color: var(--text-primary); }
.t-sub {
  display: block; font-size: 11.5px; color: var(--text-muted);
  margin-top: 1px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

.tree-wrap { position: relative; flex: 1; min-height: 0; }
.tree-chart { width: 100%; height: 100%; }

/* ===== 悬浮预览框 =====
   画出来的一扇"窗口"，不是截图。用 :deep() 是因为这段 DOM 由 ECharts
   生成，拿不到 scoped 的 data 属性，普通 scoped 选择器选不中。 */
:deep(.tp) {
  width: 320px;
  border-radius: 10px;
  overflow: hidden;
  background: color-mix(in srgb, var(--surface, #1c1c28) 92%, #000 8%);
  border: 1px solid color-mix(in srgb, var(--text-primary) 14%, transparent);
  box-shadow: 0 8px 24px rgba(0, 0, 0, .28);
  font-family: inherit;
}
:deep(.tp-bar) {
  display: flex; align-items: center; gap: 8px;
  padding: 7px 10px;
  background: color-mix(in srgb, var(--text-primary) 7%, transparent);
}
:deep(.tp-dots) { display: inline-flex; gap: 4px; flex: none; }
:deep(.tp-dots i) {
  width: 7px; height: 7px; border-radius: 50%; display: block;
  background: color-mix(in srgb, var(--text-primary) 22%, transparent);
}
:deep(.tp-bar-title) {
  font-size: 11px; color: var(--text-secondary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
:deep(.tp-body) { padding: 10px 11px 11px; }

/* ===== 版式意象 =====
   每种页面画一个**不一样的**框（用户提的：框架要按真实页面来画）。
   不求画得像，求一眼看出"这页是列表 / 是表格 / 是对话 / 是看板"。
   灰块用 --w 统一给色，下面各版式只摆位置。 */
:deep(.tp-wire) {
  display: block; margin-bottom: 10px; height: 118px;
  padding: 9px; border-radius: 7px; overflow: hidden;
  background: color-mix(in srgb, var(--text-primary) 4%, transparent);
  /* ⚠️ 透明度别调太低。第一版用了 13% / 30%，在深色主题下几乎看不见 ——
     版式画了等于没画。实测要 26% / 55% 才看得出"这是个列表/表格/看板"。 */
  --w: color-mix(in srgb, var(--text-primary) 26%, transparent);
  --wa: color-mix(in srgb, var(--brand) 55%, transparent);
}
/* ⚠️ 这条是兜底（大部分版式的根是 <b>，默认 inline 撑不开高度），
   但它特异性是 0,1,1，**会压过后面的 .w-split{display:flex}（0,1,0）** ——
   结果列表版式被拍成 block、里面的行只有间隙高（实测 278×18）。
   所以下面凡是自己要 display 的版式，选择器都得带上 `.tp-wire >`。 */
:deep(.tp-wire > b) { display: block; }

/* 指标卡 + 大图表 */
:deep(.w-kpis) { display: flex; gap: 5px; margin-bottom: 7px; }
:deep(.w-kpis i) { flex: 1; height: 26px; border-radius: 4px; background: var(--wa); }
:deep(.w-chart) { height: 62px; border-radius: 5px; background: var(--w); }

/* 左窄栏 + 右侧行 */
:deep(.tp-wire > b.w-split) { display: flex; gap: 7px; height: 100%; }
/* <i> 默认 inline —— 不写 display:block 的话 width 完全不生效（实测 0×0） */
:deep(.w-side) { display: block; width: 46px; border-radius: 5px; background: var(--wa); }
:deep(.w-rows) { flex: 1; display: flex; flex-direction: column; gap: 6px; }
:deep(.w-rows u) { flex: 1; border-radius: 4px; background: var(--w); }

/* 表格 */
:deep(.w-thead) { height: 14px; border-radius: 4px; margin-bottom: 6px; background: var(--wa); }
:deep(.w-tr) { height: 16px; border-radius: 4px; margin-bottom: 5px; background: var(--w); }

/* 对话气泡 */
:deep(.w-bub) { height: 22px; border-radius: 11px; margin-bottom: 7px; width: 66%; background: var(--w); }
:deep(.w-bub.right) { margin-left: auto; background: var(--wa); }
:deep(.w-bub.short) { width: 46%; }

/* 时间线 */
:deep(.tp-wire > b.w-tl) { display: flex; flex-direction: column; gap: 6px; padding-left: 4px; }
:deep(.w-tl i) { width: 9px; height: 9px; border-radius: 50%; background: var(--wa); }
:deep(.w-tl u) { height: 12px; margin-left: 15px; margin-top: -13px; border-radius: 4px; background: var(--w); }

/* 表单 */
:deep(.w-field) { height: 22px; border-radius: 5px; margin-bottom: 8px; background: var(--w); }
:deep(.w-field.short) { width: 58%; }
:deep(.w-btn) { width: 46%; height: 22px; border-radius: 5px; margin-top: 4px; background: var(--wa); }

/* 卡片网格 */
:deep(.tp-wire > b.w-grid) { display: grid; grid-template-columns: 1fr 1fr; gap: 7px; height: 100%; }
:deep(.w-grid i) { border-radius: 5px; background: var(--w); }

/* 语音通话 */
:deep(.tp-wire > b.w-avatar) { width: 54px; height: 54px; border-radius: 50%; margin: 4px auto 10px; background: var(--wa); }
:deep(.tp-wire > b.w-wave) { display: flex; gap: 4px; align-items: flex-end; justify-content: center; height: 34px; }
:deep(.w-wave i) { width: 6px; border-radius: 3px; background: var(--w); }
:deep(.w-wave i:nth-child(1)) { height: 14px; }
:deep(.w-wave i:nth-child(2)) { height: 26px; }
:deep(.w-wave i:nth-child(3)) { height: 34px; }
:deep(.w-wave i:nth-child(4)) { height: 22px; }
:deep(.w-wave i:nth-child(5)) { height: 12px; }

/* 正文详情 */
:deep(.w-h1) { height: 18px; width: 52%; border-radius: 4px; margin-bottom: 10px; background: var(--wa); }
:deep(.w-p) { height: 10px; border-radius: 4px; margin-bottom: 7px; background: var(--w); }
:deep(.w-p.short) { width: 64%; }

/* 这一页自己：放射状 */
:deep(.tp-wire > b.w-radial) { position: relative; height: 100%; }
:deep(.w-radial i) { position: absolute; border-radius: 50%; background: var(--w); }
:deep(.w-radial .c) { width: 26px; height: 26px; left: 50%; top: 50%; margin: -13px 0 0 -13px; background: var(--wa); }
:deep(.w-radial .a) { width: 13px; height: 13px; left: 12%; top: 14%; }
:deep(.w-radial .b) { width: 13px; height: 13px; left: 74%; top: 12%; }
:deep(.w-radial .d) { width: 13px; height: 13px; left: 8%; top: 68%; }
:deep(.w-radial .e) { width: 13px; height: 13px; left: 78%; top: 70%; }
:deep(.tp-meta) { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; flex-wrap: wrap; }
:deep(.tp-group) {
  font-size: 10px; padding: 1px 7px; border-radius: 9px;
  background: color-mix(in srgb, var(--brand) 16%, transparent);
  color: var(--brand);
}
:deep(.tp-path) {
  font-family: ui-monospace, monospace; font-size: 10px;
  color: var(--text-muted); word-break: break-all;
}
:deep(.tp-desc) {
  margin: 0 0 7px; font-size: 12px; line-height: 1.6; color: var(--text-primary);
}
:deep(.tp-go) { font-size: 11px; color: var(--brand); }
:deep(.tp-go.muted) { color: var(--text-muted); }

.tree-legend {
  flex: none; display: flex; gap: 16px; justify-content: center; flex-wrap: wrap;
  padding: 6px 14px 2px; font-size: 11.5px; color: var(--text-muted);
}
.lg { display: inline-flex; align-items: center; gap: 5px; }
.dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
.dot.root { background: var(--brand); width: 11px; height: 11px; }
.dot.branch { background: var(--viz-muted, #898781); }
.dot.leaf { background: var(--viz-s1, #2a78d6); }
</style>
