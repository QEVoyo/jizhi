// 2D 校园（2026-11-15）：地图取自《龙之城堡》当前的超大地图
// （纯地图世界，424320×256320 连续地形；不是 11-10 那张 9 房间 legacy 图）。
// 网页端只放 4 个传送点：回书桌 + 今日任务 / 薄弱点 / 资源库。
// x / y 是地图容器内的百分比坐标（底图 1280×720）。
export const CAMPUS_HOTSPOTS = [
  {
    id: 'home',
    title: '回书桌',
    subtitle: '传送点',
    desc: '回到基智主界面，看看今天的安排。',
    path: '/home',
    color: '#ffd98a',
    x: 50,
    y: 27,
  },
  {
    id: 'today',
    title: '今日任务',
    subtitle: '传送点',
    desc: '今天还有几道题没做完。小基建议先从最短的一组开始，做完再去逛。',
    path: '/learning-plan',
    color: '#ffcf7a',
    x: 23,
    y: 47,
  },
  {
    id: 'weakness',
    title: '薄弱点',
    subtitle: '传送点',
    desc: '昨天有一道题错了两次。去掌握度看板看一眼，再决定要不要重练。',
    path: '/mastery-board',
    color: '#9d8cff',
    x: 50,
    y: 63,
  },
  {
    id: 'resource',
    title: '资源库',
    subtitle: '传送点',
    desc: '最近生成的题集都在这里。挑一套顺手的，别从最难的那套开始。',
    path: '/resource-lib',
    color: '#6ee7ff',
    x: 77,
    y: 42,
  },
]

export const CAMPUS_LINES = {
  home: '回书桌看看今天的安排？',
  today: '今天先把这几道题收个尾，我陪你。',
  weakness: '昨天那道错的，我今天还记着。跟我来。',
  resource: '你攒的题集该翻一翻了，走。',
  guest: '第一次来？先看看今天的任务，别急着逛。',
}
