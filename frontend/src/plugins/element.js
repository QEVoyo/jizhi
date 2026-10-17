// ============================================================
// Element Plus 按需加载
//
// 落地页（/、/agreement、/privacy）一个 el-* 组件都不用，但原来 main.js
// 在入口静态 import 了整个 Element Plus + 293 个图标 —— 首屏 1.2MB 的入口 JS
// 里约 90% 是它。现在改成：
//   · 落地页/协议页：完全不加载 Element Plus；
//   · 其它路由：由 main.js 的全局前置守卫 await ensureElementPlus(app) 后再渲染。
//
// 这样首次进入落地页的主包能砍掉约 340KB gzip；登录/应用页多一次动态加载，
// 但那时用户已经在交互了，感知上比首屏白屏好得多。
//
// ⚠️ 只能加载一次。app.use() 重复调用会重复注册组件。
// ============================================================

let elementPromise = null

export function ensureElementPlus(app) {
  if (!elementPromise) {
    elementPromise = Promise.all([
      import('element-plus'),
      import('element-plus/dist/index.css'),
      import('@element-plus/icons-vue'),
    ]).then(([mod, , icons]) => {
      app.use(mod.default)
      // 与改造前保持完全一致：全量注册（prefix-icon="User" 这类字符串要靠它解析）
      for (const [key, component] of Object.entries(icons)) {
        app.component(key, component)
      }
    })
  }
  return elementPromise
}
