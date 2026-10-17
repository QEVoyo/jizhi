<template>
  <!--
    渐进式图片：先渲染小图占位，等它进入视口 + 浏览器空闲后，
    再在后台加载原图；原图 onload 后把 src 换成原图。
    class/style/alt/loading/@click 等属性通过 $attrs 直接落到 <img> 上，
    所以原来的 CSS 选择器（.hero-logo-img / .mu-xiaoji-img …）不用改。
  -->
  <img ref="imgEl" :src="currentSrc" v-bind="$attrs" />
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  /** 完整原图 */
  src: { type: String, required: true },
  /** 先显示的小图 / 压缩版 */
  placeholder: { type: String, required: true },
  /** 提前多少距离开始加载，默认 240px */
  rootMargin: { type: String, default: '240px' },
})

const emit = defineEmits(['full-loaded', 'full-error'])

const imgEl = ref(null)
const currentSrc = ref(props.placeholder)
const fullLoaded = ref(false)

let observer = null
let idleHandle = null
let loadToken = 0
let destroyed = false

function cancelScheduled() {
  if (idleHandle == null) return
  if (window.cancelIdleCallback) window.cancelIdleCallback(idleHandle)
  else clearTimeout(idleHandle)
  idleHandle = null
}

function loadFull() {
  idleHandle = null
  if (destroyed || fullLoaded.value) return
  const token = ++loadToken
  const img = new Image()
  img.decoding = 'async'
  // 后台加载：不要和首屏关键资源抢带宽
  try { img.fetchPriority = 'low' } catch { /* 老浏览器忽略 */ }
  img.onload = () => {
    if (destroyed || token !== loadToken) return
    currentSrc.value = props.src
    fullLoaded.value = true
    emit('full-loaded', props.src)
  }
  img.onerror = () => {
    if (destroyed || token !== loadToken) return
    emit('full-error', props.src)
  }
  img.src = props.src
}

function scheduleFullLoad() {
  if (fullLoaded.value) return
  cancelScheduled()
  if (window.requestIdleCallback) {
    idleHandle = window.requestIdleCallback(loadFull, { timeout: 1200 })
  } else {
    idleHandle = setTimeout(loadFull, 300)
  }
}

function startObserve() {
  if (!imgEl.value) return
  if (!('IntersectionObserver' in window)) {
    scheduleFullLoad()
    return
  }
  observer = new IntersectionObserver((entries) => {
    if (!entries.some(e => e.isIntersecting)) return
    observer?.disconnect()
    observer = null
    scheduleFullLoad()
  }, { rootMargin: props.rootMargin })
  observer.observe(imgEl.value)
}

function restart() {
  fullLoaded.value = false
  loadToken++
  currentSrc.value = props.placeholder
  cancelScheduled()
  observer?.disconnect()
  observer = null
  startObserve()
}

onMounted(startObserve)
watch(() => [props.src, props.placeholder], restart)

onBeforeUnmount(() => {
  destroyed = true
  loadToken++
  cancelScheduled()
  observer?.disconnect()
  observer = null
})
</script>
