<template>
  <div class="sec-page">
    <div class="page-header">
      <h2 class="page-title">安全中心</h2>
      <div class="header-actions">
        <el-select v-model="days" size="small" class="days-select" @change="reload">
          <el-option label="近 24 小时" :value="1" />
          <el-option label="近 7 天" :value="7" />
          <el-option label="近 30 天" :value="30" />
        </el-select>
      </div>
    </div>

    <el-tabs v-model="tab" class="sec-tabs">
      <!-- ============ 总览 ============ -->
      <el-tab-pane label="总览" name="overview">
        <AdminLoading :visible="loadingOverview" text="加载总览..." />

        <template v-if="overview">
          <!-- ⚠️ 触顶提示必须显眼：数字不全比没有数字更危险 -->
          <div v-if="overview.truncated" class="warn-banner">
            <i class="fas fa-triangle-exclamation"></i>
            <span>
              窗口内共 <b>{{ overview.total_in_window }}</b> 条事件，本次只统计了最近的
              <b>{{ overview.scanned }}</b> 条 —— <b>下面的分布和 Top 榜并不完整</b>。
              事件量这么大本身就值得看：请改用更短的窗口，或去「安全事件」里查。
            </span>
          </div>

          <!-- KPI 行：单个数值用统计块，不做成只有一根柱子的柱状图 -->
          <div class="kpi-row">
            <div class="kpi-tile">
              <div class="kpi-label">今日事件</div>
              <div class="kpi-value">{{ overview.today_count }}</div>
              <div class="kpi-sub">截至现在（北京时间按 UTC 计）</div>
            </div>
            <div class="kpi-tile">
              <div class="kpi-label">高危及以上</div>
              <div class="kpi-value" :class="{ 'is-alert': overview.high_or_critical > 0 }">
                {{ overview.high_or_critical }}
              </div>
              <div class="kpi-sub">窗口 {{ overview.window_days }} 天内的 high / critical</div>
            </div>
            <div class="kpi-tile">
              <div class="kpi-label">窗口内总数</div>
              <div class="kpi-value">{{ overview.total_in_window }}</div>
              <div class="kpi-sub">所有严重级合计</div>
            </div>
            <div class="kpi-tile">
              <div class="kpi-label">涉及 IP</div>
              <div class="kpi-value">{{ overview.distinct_ips ?? 0 }}</div>
              <div class="kpi-sub">去重后的来源地址数</div>
            </div>
          </div>

          <!-- 趋势：单序列，用同一个蓝；单序列不需要图例（标题已说明画的是什么） -->
          <section class="panel">
            <h3 class="panel-title">每日事件数</h3>
            <div class="trend">
              <div v-for="d in overview.trend" :key="d.date" class="trend-col"
                   :title="`${d.date}：${d.count} 条`">
                <div class="trend-value" v-if="d.count === trendMax && d.count > 0">{{ d.count }}</div>
                <div class="trend-bar-wrap">
                  <div class="trend-bar" :style="{ height: barHeight(d.count) }"></div>
                </div>
                <div class="trend-date">{{ d.date.slice(5) }}</div>
              </div>
            </div>
          </section>

          <div class="two-col">
            <!-- 严重级：状态色，**必须**配图标+文字。
                 实测这两档在浅色底上只有 2.55:1 / 1.77:1（低于 3:1），
                 所以颜色在这里不能单独承载含义 —— 图标和中文标签是硬性配套，不是装饰。 -->
            <section class="panel">
              <h3 class="panel-title">严重级分布</h3>
              <div v-if="!overview.by_severity.length" class="empty-inline">暂无事件</div>
              <ul v-else class="sev-list">
                <li v-for="s in overview.by_severity" :key="s.key" class="sev-row">
                  <span class="sev-dot" :style="{ background: sevColor(s.key) }"></span>
                  <i class="sev-icon" :class="sevIcon(s.key)" :style="{ color: sevColor(s.key) }"></i>
                  <span class="sev-name">{{ sevLabel(s.key) }}</span>
                  <span class="sev-count">{{ s.count }}</span>
                </li>
              </ul>
            </section>

            <!-- 名义分类：所有条用**同一个**蓝，不按数值上色
                 （条长已经表达了大小，再用颜色重复编码一次是浪费识别通道） -->
            <section class="panel">
              <h3 class="panel-title">按类型</h3>
              <div v-if="!overview.by_type.length" class="empty-inline">暂无事件</div>
              <ul v-else class="rank-list">
                <li v-for="t in overview.by_type" :key="t.key" class="rank-row">
                  <span class="rank-name" :title="t.key">{{ typeLabel(t.key) }}</span>
                  <span class="rank-bar-wrap">
                    <span class="rank-bar" :style="{ width: pct(t.count, overview.by_type[0]?.count) }"></span>
                  </span>
                  <span class="rank-count">{{ t.count }}</span>
                </li>
              </ul>
            </section>
          </div>

          <div class="two-col">
            <section class="panel">
              <h3 class="panel-title">Top 来源 IP</h3>
              <div v-if="!overview.top_ips.length" class="empty-inline">暂无</div>
              <ul v-else class="rank-list">
                <li v-for="r in overview.top_ips" :key="r.key" class="rank-row">
                  <a class="rank-name mono" :title="r.key" @click="filterBy('ip', r.key)">{{ r.key }}</a>
                  <span class="rank-bar-wrap">
                    <span class="rank-bar" :style="{ width: pct(r.count, overview.top_ips[0]?.count) }"></span>
                  </span>
                  <span class="rank-count">{{ r.count }}</span>
                </li>
              </ul>
            </section>

            <section class="panel">
              <h3 class="panel-title">Top 端点</h3>
              <div v-if="!overview.by_endpoint.length" class="empty-inline">暂无</div>
              <ul v-else class="rank-list">
                <li v-for="r in overview.by_endpoint" :key="r.key" class="rank-row">
                  <a class="rank-name mono" :title="r.key" @click="filterBy('endpoint', r.key)">{{ r.key }}</a>
                  <span class="rank-bar-wrap">
                    <span class="rank-bar" :style="{ width: pct(r.count, overview.by_endpoint[0]?.count) }"></span>
                  </span>
                  <span class="rank-count">{{ r.count }}</span>
                </li>
              </ul>
            </section>
          </div>

          <section class="panel" v-if="overview.top_users.length">
            <h3 class="panel-title">Top 用户</h3>
            <ul class="rank-list">
              <li v-for="r in overview.top_users" :key="r.key" class="rank-row">
                <a class="rank-name mono" :title="r.key" @click="filterBy('user_id', r.key)">{{ r.key }}</a>
                <span class="rank-bar-wrap">
                  <span class="rank-bar" :style="{ width: pct(r.count, overview.top_users[0]?.count) }"></span>
                </span>
                <span class="rank-count">{{ r.count }}</span>
              </li>
            </ul>
          </section>
        </template>

        <div v-else-if="!loadingOverview" class="empty">暂无数据</div>
      </el-tab-pane>

      <!-- ============ 安全事件 ============ -->
      <el-tab-pane label="安全事件" name="events">
        <!-- 筛选器一行放在表格上方 -->
        <div class="filter-row">
          <el-select v-model="filters.event_type" placeholder="事件类型" size="small"
                     clearable filterable class="f-select" @change="loadEvents(1)">
            <el-option v-for="t in filterOptions.event_types" :key="t" :label="typeLabel(t)" :value="t" />
          </el-select>
          <el-select v-model="filters.severity" placeholder="严重级" size="small"
                     clearable class="f-select-sm" @change="loadEvents(1)">
            <el-option v-for="s in filterOptions.severities" :key="s" :label="sevLabel(s)" :value="s" />
          </el-select>
          <el-input v-model="filters.ip" placeholder="IP" size="small" clearable
                    class="f-input" @keyup.enter="loadEvents(1)" @clear="loadEvents(1)" />
          <el-input v-model="filters.user_id" placeholder="用户 ID" size="small" clearable
                    class="f-input" @keyup.enter="loadEvents(1)" @clear="loadEvents(1)" />
          <el-input v-model="filters.endpoint" placeholder="端点包含…" size="small" clearable
                    class="f-input" @keyup.enter="loadEvents(1)" @clear="loadEvents(1)" />
          <el-button size="small" @click="loadEvents(1)">查询</el-button>
          <el-button size="small" text @click="clearFilters">重置</el-button>
        </div>

        <div class="table-wrap">
          <AdminLoading :visible="loadingEvents" text="加载安全事件..." />
          <table class="data-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>类型</th>
                <th>严重级</th>
                <th>IP</th>
                <th>用户</th>
                <th>接口</th>
                <th>码</th>
                <th>详情</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="e in events" :key="e.id">
                <td class="date-cell">{{ formatDate(e.occurred_at) }}</td>
                <td>{{ typeLabel(e.event_type) }}</td>
                <td>
                  <span class="sev-chip">
                    <i :class="sevIcon(e.severity)" :style="{ color: sevColor(e.severity) }"></i>
                    {{ sevLabel(e.severity) }}
                  </span>
                </td>
                <td class="mono-cell">
                  <a v-if="e.ip" @click="filterBy('ip', e.ip)">{{ e.ip }}</a>
                  <span v-else>-</span>
                </td>
                <td class="mono-cell">
                  <a v-if="e.user_id" :title="e.user_id" @click="filterBy('user_id', e.user_id)">
                    {{ e.user_id.slice(0, 8) }}…
                  </a>
                  <span v-else>-</span>
                </td>
                <td class="mono-cell">
                  <span v-if="e.endpoint">{{ e.method }} {{ e.endpoint }}</span>
                  <span v-else>-</span>
                </td>
                <td class="mono-cell">{{ e.status_code || '-' }}</td>
                <td class="detail-cell">{{ detailText(e.detail) || '-' }}</td>
              </tr>
            </tbody>
          </table>
          <div class="empty" v-if="!loadingEvents && events.length === 0">暂无安全事件</div>
          <div class="pagination" v-if="total > pageSize">
            <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total"
                           layout="prev, pager, next" @current-change="loadEvents" />
          </div>
        </div>
      </el-tab-pane>

      <!-- ============ 用户信誉 ============ -->
      <el-tab-pane label="用户信誉" name="reputation">
        <!-- 查单个用户 -->
        <div class="filter-row">
          <el-input v-model="repUserId" placeholder="用户 ID（也可以从下面列表点进来）"
                    size="small" clearable class="f-input f-input-wide"
                    @keyup.enter="loadReputation" />
          <el-button size="small" type="primary" @click="loadReputation">查询</el-button>
          <el-button size="small" text @click="repUserId = ''; repDetail = null">清空</el-button>
        </div>

        <template v-if="repDetail">
          <div class="kpi-row">
            <div class="kpi-tile">
              <div class="kpi-label">信誉分</div>
              <div class="kpi-value" :class="{ 'is-alert': (repDetail.score ?? 100) < 70 }">
                {{ repDetail.score }}
              </div>
              <div class="kpi-sub">
                <!-- 档位：颜色只是辅助，图标 + 中文名必须同时在 -->
                <span class="tier-chip">
                  <i :class="tierIcon(repDetail.tier)"
                     :style="{ color: tierColor(repDetail.tier) }"></i>
                  {{ repDetail.tier_label || repDetail.tier }}
                </span>
              </div>
            </div>
            <div class="kpi-tile">
              <div class="kpi-label">连续清白</div>
              <div class="kpi-value">{{ repDetail.streak_days >= 3650 ? '从未违规' : repDetail.streak_days + ' 天' }}</div>
              <div class="kpi-sub">
                <template v-if="repDetail.days_to_next_tier > 0">
                  再坚持 {{ repDetail.days_to_next_tier }} 天恢复加速
                </template>
                <template v-else>已是最快恢复档</template>
              </div>
            </div>
            <div class="kpi-tile">
              <div class="kpi-label">AI 每日配额</div>
              <div class="kpi-value">{{ repDetail.ai_daily_quota < 0 ? '不限' : repDetail.ai_daily_quota }}</div>
              <div class="kpi-sub">-1 = 不限，0 = 禁止</div>
            </div>
            <div class="kpi-tile">
              <div class="kpi-label">内容权限</div>
              <div class="kpi-value">{{ repDetail.can_publish ? '可发布' : '禁发' }}</div>
              <div class="kpi-sub">{{ repDetail.content_needs_review ? '新内容先审后发' : '免审直发' }}</div>
            </div>
          </div>

          <!-- 手动改分 -->
          <div class="panel">
            <div class="panel-title">手动改分</div>
            <p class="panel-note">
              理由必填 —— 不写理由的手动改分，三个月后没人说得清为什么。
              改动会写一条 <code>admin.manual</code> 流水（含操作人），并进审计日志。
              手动改分**不受**每日上限约束（那是自动规则的节流阀）。
            </p>
            <div class="filter-row">
              <el-input-number v-model="repNewScore" :min="0" :max="100" size="small" />
              <el-input v-model="repReason" placeholder="修改理由（必填）" size="small"
                        class="f-input f-input-wide" maxlength="200" show-word-limit />
              <el-button size="small" type="primary" :loading="savingRep"
                         :disabled="!repReason.trim()" @click="submitReputation">提交</el-button>
            </div>
          </div>

          <!-- 变更历史 -->
          <div class="panel">
            <div class="panel-title">变更历史（最近 {{ repDetail.history?.length || 0 }} 条）</div>
            <div class="table-wrap">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>时间</th><th>变动</th><th>之后</th><th>规则</th>
                    <th>说明</th><th>来源</th><th>操作人</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="h in repDetail.history" :key="h.id">
                    <td class="date-cell">{{ formatDate(h.created_at) }}</td>
                    <td class="mono-cell" :class="h.delta > 0 ? 'delta-up' : (h.delta < 0 ? 'delta-down' : '')">
                      {{ h.delta > 0 ? '+' + h.delta : h.delta }}
                    </td>
                    <td class="mono-cell">{{ h.score_after }}</td>
                    <td class="mono-cell">{{ ruleLabel(h.reason_code) }}</td>
                    <td class="detail-cell">{{ h.reason_text || detailText(h.detail) || '-' }}</td>
                    <td class="mono-cell">{{ h.source_type || '-' }}</td>
                    <td class="mono-cell">
                      <span :title="h.operator_id">{{ h.operator_id ? h.operator_id.slice(0, 8) + '…' : '系统' }}</span>
                    </td>
                  </tr>
                  <tr v-if="!repDetail.history?.length">
                    <td colspan="7" class="empty-inline">
                      没有变更记录 —— 从没被扣过分的人不写流水（没行即满分）
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>

        <!-- 列表：只列有过记录的人 -->
        <div class="panel">
          <div class="panel-title">全站用户信誉（低分在前）</div>
          <!-- ⚠️ 2026-10-16 改：这张表以前只列 user_reputation 里有行的人，于是
               全站 23 个用户只显示 1 个、还是个满分的 —— 看着就是坏的。
               现在以 profiles 全表为准，「没行 = 从未变动 = 满分」，与引擎同口径。
               说明必须写清楚：那 22 个满分是**算出来的默认值**，不是库里的记录。 -->
          <p class="panel-note">
            以 <strong>profiles 全表</strong>为准 —— 每个注册用户都在这张表里。
            信誉分是<strong>懒创建</strong>的：分数从没变动过的人，
            <code>user_reputation</code> 里没有行，<strong>没行即满分</strong>
            （见 <code>utils/reputation.py</code> 的 <code>get_score</code>）。
            所以「最近变动」为空的人，分数是默认值算出来的，不是库里存着的。
          </p>
          <p class="panel-note">
            当前筛选下共 <strong>{{ repTotal }}</strong> 人，其中
            <strong>{{ repWithRecord }}</strong> 人的分数被动过。
          </p>
          <p v-if="repTruncated" class="panel-note">
            ⚠️ 用户数超过单次取数上限，上面的总数只统计了其中一部分，不是全量。
          </p>
          <div class="filter-row">
            <el-input v-model="repSearch" placeholder="按昵称 / 邮箱 / 账号搜"
                      size="small" clearable class="f-input f-input-wide"
                      @keyup.enter="loadRepList(1)" @clear="loadRepList(1)" />
            <el-button size="small" type="primary" @click="loadRepList(1)">搜索</el-button>
            <el-select v-model="repTier" placeholder="全部档位" size="small" clearable
                       class="f-select" @change="loadRepList(1)">
              <el-option v-for="t in repTiers" :key="t.code"
                         :label="`${tierLabel(t.code)}（${t.min_score}-${t.max_score}）`"
                         :value="t.code" />
            </el-select>
            <el-button size="small" @click="loadRepList(1)">刷新</el-button>
          </div>
          <div class="table-wrap">
            <AdminLoading :visible="loadingRepList" text="加载信誉列表..." />
            <table class="data-table">
              <thead>
                <tr><th>用户</th><th>分数</th><th>档位</th><th>最近变动</th></tr>
              </thead>
              <tbody>
                <tr v-for="u in repList" :key="u.user_id">
                  <td>
                    <a :title="u.user_id" @click="pickUser(u.user_id)">
                      {{ u.nickname || u.user_id.slice(0, 8) + '…' }}
                    </a>
                    <div class="date-cell">{{ u.user_account || u.email || '—' }}</div>
                  </td>
                  <td class="mono-cell">{{ u.score }}</td>
                  <td>
                    <span class="tier-chip">
                      <i :class="tierIcon(u.tier)" :style="{ color: tierColor(u.tier) }"></i>
                      {{ u.tier_label || u.tier || '-' }}
                    </span>
                  </td>
                  <!-- 没行的人没有变动时间 —— 显示 — 而不是空白，
                       否则会被读成"加载失败"。 -->
                  <td class="date-cell">
                    {{ u.has_record ? formatDate(u.updated_at) : '—（从未变动）' }}
                  </td>
                </tr>
                <tr v-if="!repList.length && !loadingRepList">
                  <td colspan="4" class="empty-inline">
                    {{ repSearch ? '没有匹配的用户' : '还没有用户' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="pagination">
            <el-pagination small layout="prev, pager, next, total"
                           :total="repTotal" :page-size="repPageSize"
                           :current-page="repPage" @current-change="loadRepList" />
          </div>
        </div>

        <!-- 规则与档位（只读） -->
        <div class="panel">
          <div class="panel-title">规则与档位配置（只读）</div>
          <p class="panel-note">
            改阈值和分值**不用改代码**，直接 UPDATE <code>reputation_rules</code> /
            <code>reputation_tiers</code> 两张表即可，引擎每次读表（缓存 5 分钟）。
          </p>
          <div class="table-wrap">
            <table class="data-table">
              <thead>
                <tr><th>规则</th><th>类型</th><th>分值</th><th>日上限</th><th>每日一次</th><th>说明</th></tr>
              </thead>
              <tbody>
                <tr v-for="r in repRules" :key="r.code">
                  <td class="mono-cell">{{ r.code }}</td>
                  <td>{{ KIND_LABEL[r.kind] || r.kind }}</td>
                  <td class="mono-cell" :class="r.delta > 0 ? 'delta-up' : 'delta-down'">
                    {{ r.delta > 0 ? '+' + r.delta : r.delta }}
                  </td>
                  <td class="mono-cell">{{ r.daily_cap ?? '不限' }}</td>
                  <td class="mono-cell">{{ r.once_per_day ? '是' : '否' }}</td>
                  <td class="detail-cell">{{ r.label || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </el-tab-pane>

      <!-- ============ 生成审计 ============ -->
      <el-tab-pane label="生成审计" name="genaudit">
        <AdminLoading :visible="loadingAudit" text="加载生成审计..." />

        <template v-if="audit">
          <!-- ⚠️ 覆盖率提示。这条**必须**在，而且要在最上面：
               数字只代表走网关的那部分调用点，不说清楚就会被当成全站用量。 -->
          <div class="warn-banner">
            <i class="fas fa-circle-info"></i>
            <span>
              这里只统计**已经迁到安全包网关的调用点** —— 当前
              <b>{{ audit.coverage.migrated }} / {{ audit.coverage.total }}</b>。
              其余 <b>{{ audit.coverage.total - audit.coverage.migrated }}</b> 处 AI 调用
              各写各的、不走网关，因此<b>不在这张表里</b>。
              下面的数字不是全站用量，别当总量看。
            </span>
          </div>

          <div v-if="audit.truncated" class="warn-banner">
            <i class="fas fa-triangle-exclamation"></i>
            <span>
              窗口内共 <b>{{ audit.total_in_window }}</b> 条，本次只统计了最近的
              <b>{{ audit.scanned }}</b> 条 —— 分布和 Top 榜并不完整。
            </span>
          </div>

          <div class="kpi-row">
            <div class="kpi-tile">
              <div class="kpi-label">窗口内生成</div>
              <div class="kpi-value">{{ audit.total_in_window }}</div>
              <div class="kpi-sub">近 {{ audit.window_days }} 天（走网关的部分）</div>
            </div>
            <div class="kpi-tile">
              <div class="kpi-label">今日生成</div>
              <div class="kpi-value">{{ audit.today_count }}</div>
              <div class="kpi-sub">去重用户 {{ audit.distinct_users }} 人</div>
            </div>
            <div class="kpi-tile">
              <div class="kpi-label">失败率</div>
              <div class="kpi-value" :class="{ 'is-alert': (audit.fail_rate ?? 0) > 0.05 }">
                {{ audit.fail_rate === null ? '-' : (audit.fail_rate * 100).toFixed(1) + '%' }}
              </div>
              <div class="kpi-sub">{{ audit.failed }} / {{ audit.scanned }} 条失败</div>
            </div>
            <div class="kpi-tile">
              <div class="kpi-label">耗时 p95</div>
              <div class="kpi-value">{{ audit.latency.p95 === null ? '-' : (audit.latency.p95 / 1000).toFixed(1) + 's' }}</div>
              <div class="kpi-sub">
                中位 {{ audit.latency.p50 === null ? '-' : (audit.latency.p50 / 1000).toFixed(1) + 's' }}
                · 样本 {{ audit.latency.samples }}
              </div>
            </div>
          </div>

          <section class="panel">
            <h3 class="panel-title">每日生成数</h3>
            <div class="trend">
              <div v-for="d in audit.trend" :key="d.date" class="trend-col"
                   :title="`${d.date}：${d.count} 次`">
                <div class="trend-value" v-if="d.count === auditTrendMax && d.count > 0">{{ d.count }}</div>
                <div class="trend-bar-wrap">
                  <div class="trend-bar" :style="{ height: auditBarHeight(d.count) }"></div>
                </div>
                <div class="trend-date">{{ d.date.slice(5) }}</div>
              </div>
            </div>
          </section>

          <div class="two-col">
            <!-- 结局分布：状态色 + 图标 + 中文标签，同严重级那条规矩 -->
            <section class="panel">
              <h3 class="panel-title">结局分布</h3>
              <div v-if="!audit.by_status.length" class="empty-inline">窗口内没有生成记录</div>
              <ul v-else class="sev-list">
                <li v-for="s in audit.by_status" :key="s.key" class="sev-row">
                  <span class="sev-dot" :style="{ background: statusColor(s.key) }"></span>
                  <i class="sev-icon" :class="statusIcon(s.key)" :style="{ color: statusColor(s.key) }"></i>
                  <span class="sev-name">{{ statusLabel(s.key) }}</span>
                  <span class="sev-count">{{ s.count }}</span>
                </li>
              </ul>
            </section>

            <!-- 用途：名义分类，条全用同一个蓝（条长已表达大小） -->
            <section class="panel">
              <h3 class="panel-title">按用途</h3>
              <div v-if="!audit.by_purpose.length" class="empty-inline">暂无数据</div>
              <ul v-else class="rank-list">
                <li v-for="p in audit.by_purpose" :key="p.key" class="rank-row">
                  <span class="rank-name mono" :title="p.key">{{ p.key }}</span>
                  <span class="rank-bar-wrap">
                    <span class="rank-bar" :style="{ width: pct(p.count, auditPurposeMax) }"></span>
                  </span>
                  <span class="rank-count">{{ p.count }}</span>
                </li>
              </ul>
            </section>
          </div>

          <section class="panel">
            <h3 class="panel-title">按模型</h3>
            <div v-if="!audit.by_model.length" class="empty-inline">暂无数据</div>
            <ul v-else class="rank-list">
              <li v-for="m in audit.by_model" :key="m.key" class="rank-row">
                <span class="rank-name mono" :title="m.key">{{ m.key }}</span>
                <span class="rank-bar-wrap">
                  <span class="rank-bar" :style="{ width: pct(m.count, auditModelMax) }"></span>
                </span>
                <span class="rank-count">{{ m.count }}</span>
              </li>
            </ul>
          </section>

          <!-- 明细 -->
          <section class="panel">
            <h3 class="panel-title">生成明细</h3>
            <div class="filter-row">
              <el-select v-model="auditFilters.purpose" placeholder="用途" size="small"
                         clearable filterable class="f-select" @change="loadAuditList(1)">
                <el-option v-for="p in audit.by_purpose" :key="p.key" :label="p.key" :value="p.key" />
              </el-select>
              <el-select v-model="auditFilters.status" placeholder="只看失败的" size="small"
                         clearable class="f-select" @change="loadAuditList(1)">
                <el-option v-for="s in ALL_STATUSES" :key="s" :label="statusLabel(s)" :value="s" />
              </el-select>
              <el-input v-model="auditFilters.model" placeholder="模型" size="small" clearable
                        class="f-input" @keyup.enter="loadAuditList(1)" @clear="loadAuditList(1)" />
              <el-input v-model="auditFilters.user_id" placeholder="用户 ID" size="small" clearable
                        class="f-input" @keyup.enter="loadAuditList(1)" @clear="loadAuditList(1)" />
              <el-button size="small" @click="loadAuditList(1)">查询</el-button>
              <el-button size="small" text @click="clearAuditFilters">重置</el-button>
            </div>
            <div class="table-wrap">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>时间</th><th>用途</th><th>结局</th><th>模型</th>
                    <th>用户</th><th>耗时</th><th>入/出</th><th>详情</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="g in auditList" :key="g.id">
                    <td class="date-cell">{{ formatDate(g.created_at) }}</td>
                    <td class="mono-cell">{{ g.purpose }}</td>
                    <td>
                      <span class="sev-chip">
                        <i :class="statusIcon(g.status)" :style="{ color: statusColor(g.status) }"></i>
                        {{ statusLabel(g.status) }}
                      </span>
                    </td>
                    <td class="mono-cell">{{ g.model || '-' }}</td>
                    <td class="mono-cell">
                      <a v-if="g.user_id" :title="g.user_id"
                         @click="auditFilters.user_id = g.user_id; loadAuditList(1)">
                        {{ g.user_id.slice(0, 8) }}…
                      </a>
                      <span v-else>系统</span>
                    </td>
                    <td class="mono-cell">{{ g.latency_ms === null || g.latency_ms === undefined ? '-' : (g.latency_ms / 1000).toFixed(1) + 's' }}</td>
                    <td class="mono-cell">{{ g.input_chars ?? '-' }} / {{ g.output_chars ?? '-' }}</td>
                    <td class="detail-cell">{{ detailText(g.detail) || '-' }}</td>
                  </tr>
                  <tr v-if="!auditList.length && !loadingAuditList">
                    <td colspan="8" class="empty-inline">
                      没有记录 —— 表建了吗？网关跑过生成吗？
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="pagination">
              <el-pagination small layout="prev, pager, next, total"
                             :total="auditTotal" :page-size="auditPageSize"
                             :current-page="auditPage" @current-change="loadAuditList" />
            </div>
          </section>
        </template>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getSecurityEvents, getSecurityOverview, getSecurityFilters,
  getUserReputation, setUserReputation, listReputations, getReputationRules,
  getGenAuditOverview, getGenAuditList,
} from '@/api/admin'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import AdminLoading from '@/components/admin/AdminLoading.vue'

const route = useRoute()
const router = useRouter()

// tab 与地址栏同步。两个理由：
//   1. 主面板的 AI 卡片要能直接落到「生成审计」(?tab=genaudit)；
//   2. 刷新/分享链接能回到同一个 Tab —— 以前切到哪全靠内存，一刷新就回总览。
// 写法参考 AdminReports.vue（那边同一个组件按 path 分三个入口，这里是 query）。
const TAB_NAMES = ['overview', 'events', 'reputation', 'genaudit']
const tab = computed({
  get: () => {
    const t = String(route.query.tab || '')
    return TAB_NAMES.includes(t) ? t : 'overview'
  },
  set: (v) => {
    const q = { ...route.query }
    if (v && v !== 'overview') q.tab = v
    else delete q.tab          // 总览是默认值，不往地址栏里塞
    router.replace({ query: q })
  },
})

const days = ref(7)

const overview = ref(null)
const loadingOverview = ref(false)
const events = ref([])
const loadingEvents = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(30)
const filterOptions = ref({ event_types: [], severities: [] })
const filters = ref({ event_type: '', severity: '', ip: '', user_id: '', endpoint: '' })

// ── 严重级：颜色 **必须** 配图标 + 文字 ──
// 用固定的状态色板（不是分类色板 —— 状态色是保留语义，不能被当成"第几个系列"）。
// ⚠️ 实测这两档在浅色卡片底上只有 2.55:1 / 1.77:1，**低于 3:1**。
//    所以颜色在这里绝不能单独承载含义，图标和中文标签是硬性配套。
const SEV_META = {
  critical: { label: '需立刻处理', icon: 'fas fa-bolt', color: '#d03b3b' },
  high:     { label: '高危',       icon: 'fas fa-triangle-exclamation', color: '#ec835a' },
  warn:     { label: '可疑',       icon: 'fas fa-circle-info', color: '#fab219' },
  info:     { label: '记录',       icon: 'fas fa-circle-dot', color: '#898781' },
}
function sevLabel(s) { return SEV_META[s]?.label || s || '-' }
function sevIcon(s) { return SEV_META[s]?.icon || 'fas fa-circle-dot' }
function sevColor(s) { return SEV_META[s]?.color || '#898781' }

// 事件类型的中文名。与后端 utils/security_log.py 的常量逐条对齐 ——
// 改了那边记得改这里。查不到就回落到原始键（不显示空白，也不假装认识它）。
const TYPE_LABEL = {
  'auth.login_failed': '登录失败',
  'auth.login_throttled': '登录被限流',
  'auth.token_invalid': '凭证无效',
  'auth.banned_access': '封禁账号访问',
  'auth.register_throttled': '注册被限流',
  'auth.sendcode_throttled': '验证码被限流',
  'rate_limit.hit': '触发限流',
  'access.forbidden': '越权访问',
  'access.impersonation': '冒充他人身份',
  'access.pii_probe': '探测他人资料',
  'content.banned_word': '命中违禁词',
  'content.blocked': '内容被拦',
  'reputation.changed': '信誉变动',
  'reputation.blocked': '信誉不足被拒',
  'suspicious.generic': '可疑行为',
}
function typeLabel(t) { return TYPE_LABEL[t] || t || '-' }

const DETAIL_LABEL = {
  rule: '规则', limit: '额度', window: '窗口', dimension: '维度',
  claimed_user_id: '自报身份', token_user_id: '实际身份', action: '动作',
  suppressed_since_last: '期间被压缩', via_proxy: '经代理', peer_ip: '直连对端',
  hit: '命中词', field: '字段', delta: '变动', reason: '原因',
}

function detailText(d) {
  if (!d || typeof d !== 'object') return ''
  const parts = []
  for (const [k, v] of Object.entries(d)) {
    if (v === null || v === undefined || v === '') continue
    const val = typeof v === 'boolean' ? (v ? '是' : '否') : String(v)
    parts.push(`${DETAIL_LABEL[k] || k}: ${val}`)
  }
  return parts.join(' · ')
}

function formatDate(d) { return d ? dayjs(d).format('MM-DD HH:mm:ss') : '-' }

const trendMax = computed(() => {
  const t = overview.value?.trend || []
  return t.reduce((m, d) => Math.max(m, d.count), 0)
})
function barHeight(c) {
  const max = trendMax.value
  if (!max || !c) return '2px'   // 0 也留一条细基线，否则那一天像是缺失
  return Math.max(4, Math.round((c / max) * 92)) + 'px'
}
function pct(v, max) { return max ? Math.max(2, Math.round((v / max) * 100)) + '%' : '2%' }

async function loadOverview() {
  loadingOverview.value = true
  try {
    overview.value = await getSecurityOverview({ days: days.value, top_n: 10 })
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '加载安全总览失败')
    overview.value = null
  } finally { loadingOverview.value = false }
}

async function loadEvents(p) {
  if (typeof p === 'number') page.value = p
  loadingEvents.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value, days: days.value }
    for (const [k, v] of Object.entries(filters.value)) if (v) params[k] = v
    const data = await getSecurityEvents(params)
    events.value = data.items || []
    total.value = data.total || 0
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '加载安全事件失败')
    events.value = []
  } finally { loadingEvents.value = false }
}

// ── 用户信誉（第二期）──
// 与「安全事件」是两回事：事件是客观流水（谁触发了什么），信誉是主观结论
// （这个人整体可不可信）。所以这里能改分，但每一步都要留痕。
//
// 档位配色同样遵守「颜色不单独承载含义」：图标 + 中文名是硬性配套。
// label 与后端 _TIER_LABEL 是同一套词。档位筛选的下拉要用中文名 ——
// reputation_tiers 表里只有 badge（"守信"），没有能当档位名用的列。
const TIER_META = {
  excellent: { icon: 'fas fa-shield-heart', color: '#3f9c5a', label: '优良' },
  normal:    { icon: 'fas fa-circle-check', color: '#2a78d6', label: '正常' },
  restricted:{ icon: 'fas fa-triangle-exclamation', color: '#ec835a', label: '受限' },
  high_risk: { icon: 'fas fa-ban',          color: '#d03b3b', label: '高危' },
}
function tierIcon(t) { return TIER_META[t]?.icon || 'fas fa-circle-dot' }
function tierColor(t) { return TIER_META[t]?.color || '#898781' }
function tierLabel(t) { return TIER_META[t]?.label || t }

const KIND_LABEL = { deduct: '扣分', award: '加分', recovery: '恢复' }

const repUserId = ref('')
const repDetail = ref(null)
const repNewScore = ref(100)
const repReason = ref('')
const savingRep = ref(false)

const repList = ref([])
const repTotal = ref(0)
const repPage = ref(1)
const repPageSize = ref(30)
const repTier = ref('')
const repSearch = ref('')
// 有几个人的分数真的被动过。与 repTotal（全站人数）要分开说 ——
// 全站 23 人都是满分时，说"23 条信誉记录"是错的，那 22 条是默认值。
const repWithRecord = ref(0)
const repTruncated = ref(false)
const loadingRepList = ref(false)

const repRules = ref([])
const repTiers = ref([])
// code → 可读名。规则表里改了 label 这里不用动（直接从 rules 里取）
const repRuleLabel = computed(() => {
  const m = {}
  for (const r of repRules.value) m[r.code] = r.label || r.code
  m['admin.manual'] = '管理员手动改分'
  return m
})
function ruleLabel(code) { return repRuleLabel.value[code] || code || '-' }

async function loadReputation() {
  const id = repUserId.value.trim()
  if (!id) { ElMessage.warning('请先填用户 ID'); return }
  try {
    const d = await getUserReputation(id, { history_limit: 50 })
    repDetail.value = d
    repNewScore.value = d.score ?? 100
    repReason.value = ''
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '查询信誉分失败')
    repDetail.value = null
  }
}

async function submitReputation() {
  const reason = repReason.value.trim()
  if (!reason) { ElMessage.warning('必须填写修改理由'); return }
  savingRep.value = true
  try {
    const r = await setUserReputation(repUserId.value.trim(), repNewScore.value, reason)
    ElMessage.success(`已改分：${r.score_before} → ${r.score_after}`)
    repReason.value = ''
    await loadReputation()
    await loadRepList(repPage.value)
  } catch (e) {
    // 409 = 并发冲突（引擎的 CAS 没抢到），提示刷新而不是假装成功
    const msg = e?.response?.data?.detail || '改分失败'
    ElMessage.error(e?.response?.status === 409 ? `${msg}（请刷新后重试）` : msg)
  } finally { savingRep.value = false }
}

async function loadRepList(p) {
  if (typeof p === 'number') repPage.value = p
  loadingRepList.value = true
  try {
    const params = { page: repPage.value, page_size: repPageSize.value }
    if (repTier.value) params.tier = repTier.value
    if (repSearch.value.trim()) params.search = repSearch.value.trim()
    const d = await listReputations(params)
    repList.value = d.items || []
    repTotal.value = d.total || 0
    repWithRecord.value = d.with_record || 0
    repTruncated.value = !!d.truncated
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '加载信誉列表失败')
    repList.value = []
    repTotal.value = 0
    repWithRecord.value = 0
  } finally { loadingRepList.value = false }
}

function pickUser(id) {
  repUserId.value = id
  loadReputation()
}

async function loadRepConfig() {
  try {
    const d = await getReputationRules()
    repRules.value = d.rules || []
    repTiers.value = d.tiers || []
  } catch { /* 配置拉不到不影响改分 */ }
}

// ── 生成审计（第三期）──
// 数据来自 ai_generation_audit，网关每次生成写一行（成功也写）。
// 与「安全事件」的区别：那边只记失败和拦截、问的是「谁在攻击」。
//
// ⚠️ 结局的配色同样遵守「颜色不单独承载含义」：图标 + 中文名是硬性配套。
const STATUS_META = {
  ok:                { label: '正常',        icon: 'fas fa-circle-check',        color: '#3f9c5a' },
  blocked_input:     { label: '入闸拦下',    icon: 'fas fa-shield-halved',       color: '#fab219' },
  quota_denied:      { label: '配额用尽',    icon: 'fas fa-user-slash',          color: '#fab219' },
  provider_error:    { label: '模型调用失败', icon: 'fas fa-plug-circle-xmark',   color: '#d03b3b' },
  empty_output:      { label: '返回空',      icon: 'fas fa-file-circle-xmark',   color: '#d03b3b' },
  too_short:         { label: '输出过短',    icon: 'fas fa-ruler-horizontal',    color: '#ec835a' },
  json_parse_failed: { label: 'JSON 解析失败', icon: 'fas fa-code',              color: '#ec835a' },
}
// 与后端 utils/gen_audit.py 的 KNOWN_STATUSES 逐条对齐。查不到就回落到原始键
// （不显示空白，也不假装认识它）。
const ALL_STATUSES = Object.keys(STATUS_META)
function statusLabel(s) { return STATUS_META[s]?.label || s || '-' }
function statusIcon(s) { return STATUS_META[s]?.icon || 'fas fa-circle-dot' }
function statusColor(s) { return STATUS_META[s]?.color || '#898781' }

const audit = ref(null)
const loadingAudit = ref(false)
const auditList = ref([])
const auditTotal = ref(0)
const auditPage = ref(1)
const auditPageSize = ref(30)
const auditFilters = ref({ purpose: '', status: '', model: '', user_id: '' })
const loadingAuditList = ref(false)

const auditTrendMax = computed(() =>
  (audit.value?.trend || []).reduce((m, d) => Math.max(m, d.count), 0))
function auditBarHeight(c) {
  const max = auditTrendMax.value
  if (!max || !c) return '2px'
  return Math.max(4, Math.round((c / max) * 92)) + 'px'
}
const auditPurposeMax = computed(() =>
  (audit.value?.by_purpose || []).reduce((m, x) => Math.max(m, x.count), 0))
const auditModelMax = computed(() =>
  (audit.value?.by_model || []).reduce((m, x) => Math.max(m, x.count), 0))

async function loadAudit() {
  loadingAudit.value = true
  try {
    audit.value = await getGenAuditOverview({ days: days.value, top_n: 10 })
  } catch (e) {
    // 表还没建时后端回 502 并说明要跑哪份 SQL —— 原样透出来，别吞成"暂无数据"
    ElMessage.error(e?.response?.data?.detail || '加载生成审计失败')
    audit.value = null
  } finally { loadingAudit.value = false }
}

async function loadAuditList(p) {
  if (typeof p === 'number') auditPage.value = p
  loadingAuditList.value = true
  try {
    const params = { page: auditPage.value, page_size: auditPageSize.value }
    for (const [k, v] of Object.entries(auditFilters.value)) if (v) params[k] = v
    const d = await getGenAuditList(params)
    auditList.value = d.items || []
    auditTotal.value = d.total || 0
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '加载生成明细失败')
    auditList.value = []
  } finally { loadingAuditList.value = false }
}

function clearAuditFilters() {
  auditFilters.value = { purpose: '', status: '', model: '', user_id: '' }
  loadAuditList(1)
}

function filterBy(key, val) {
  filters.value[key] = val
  tab.value = 'events'
  loadEvents(1)
}
function clearFilters() {
  filters.value = { event_type: '', severity: '', ip: '', user_id: '', endpoint: '' }
  loadEvents(1)
}
function reload() {
  loadOverview()
  if (tab.value === 'events') loadEvents(1)
  if (tab.value === 'genaudit') loadAudit()
}

// 三个 Tab 各自查不同的表，切过去才拉 —— 没必要一进页面就把四张表全查一遍。
//
// ⚠️ 用 watch 而不是 el-tabs 的 @tab-change，两个原因：
//   1. **深链进来时**（?tab=genaudit）初始 tab 不是"用户点出来的"，
//      @tab-change 不会触发，那个 Tab 会一直是空的。
//   2. 顺带修一个既有 bug：原来 events 这一支根本没写进 onTabChange，
//      点「安全事件」标签页什么都不加载，得再点一次「查询」才出数据。
//
// 三个判断里都带了 loading 标志：`filterBy()` 会先 `tab.value='events'` 再自己
// 调 loadEvents(1)，不加这个的话 watch 醒来时列表还是空的，会再发一次同样的请求。
watch(tab, (name) => {
  if (name === 'events' && !events.value.length && !loadingEvents.value) loadEvents(1)
  if (name === 'reputation' && !repRules.value.length) {
    loadRepConfig()
    loadRepList(1)
  }
  if (name === 'genaudit' && !audit.value) {
    loadAudit()
    loadAuditList(1)
  }
}, { immediate: true })

onMounted(async () => {
  try { filterOptions.value = await getSecurityFilters() } catch { /* 筛选器拉不到不影响主流程 */ }
  loadOverview()
})
</script>

<style scoped>
/* 状态色板：固定语义、不随主题换（good→critical 是一套保留色）。
   顺序蓝是单序列趋势条用的，浅/深各一档。 */
.sec-page {
  --series-blue: #2a78d6;
  max-width: 1100px;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) .sec-page { --series-blue: #3987e5; }
}
:root[data-theme="dark"] .sec-page { --series-blue: #3987e5; }

.page-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 14px;
}
.page-title { font-size: 20px; font-weight: 600; color: var(--text-primary); margin: 0; }
.days-select { width: 130px; }

.warn-banner {
  display: flex; gap: 10px; align-items: flex-start;
  padding: 11px 14px; margin-bottom: 14px;
  border-radius: 10px;
  background: color-mix(in srgb, #fab219 12%, transparent);
  border: 1px solid color-mix(in srgb, #fab219 38%, transparent);
  color: var(--text-secondary); font-size: 12.5px; line-height: 1.6;
}
.warn-banner i { color: #fab219; margin-top: 2px; }

/* ── KPI 行：单个数值用统计块，不做成只有一根柱子的柱状图 ── */
.kpi-row {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 12px; margin-bottom: 14px;
}
.kpi-tile {
  padding: 14px 16px; border-radius: 14px;
  background: color-mix(in srgb, var(--surface, #fff) 3%, transparent);
  backdrop-filter: blur(12px);
  border: 1px solid color-mix(in srgb, var(--text-primary) 6%, transparent);
}
.kpi-label { font-size: 12px; color: var(--text-muted); margin-bottom: 6px; }
/* 大号独立数字用默认比例数字 —— tabular-nums 会让 121 这种看起来松松垮垮 */
.kpi-value { font-size: 26px; font-weight: 600; color: var(--text-primary); line-height: 1.1; }
.kpi-value.is-alert { color: #d03b3b; }
.kpi-sub { font-size: 11px; color: var(--text-muted); margin-top: 5px; }

.panel {
  padding: 14px 16px 16px; border-radius: 14px; margin-bottom: 14px;
  background: color-mix(in srgb, var(--surface, #fff) 3%, transparent);
  backdrop-filter: blur(12px);
  border: 1px solid color-mix(in srgb, var(--text-primary) 6%, transparent);
}
.panel-title {
  font-size: 13px; font-weight: 600; color: var(--text-secondary);
  margin: 0 0 12px;
}
/* 面板下面那句解释。写「为什么是这样」而不是「这里有什么」——
   阈值和分值为什么定成这样、哪些改动要留痕，都是接手的人需要知道的。 */
.panel-note {
  margin: -6px 0 12px; font-size: 12px; line-height: 1.65;
  color: var(--text-muted);
}
.panel-note code {
  font-family: monospace; font-size: 11.5px;
  padding: 1px 4px; border-radius: 4px;
  background: color-mix(in srgb, var(--text-primary) 7%, transparent);
}

/* 档位徽章：颜色只是辅助，图标 + 中文名是硬性配套（同严重级那条规矩）。 */
.tier-chip {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 12px; color: var(--text-secondary);
}

/* 分数变动：正负各自一个颜色，但符号本身也在（+/-），不靠颜色单独表意。 */
.delta-up { color: #3f9c5a; }
.delta-down { color: #d03b3b; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.two-col .panel { margin-bottom: 0; }
.two-col + .two-col, .two-col + .panel { margin-top: 12px; }

/* ── 趋势：单序列柱。柱宽封顶、顶端 4px 圆角、底端贴基线 ── */
.trend { display: flex; align-items: flex-end; gap: 10px; height: 130px; }
.trend-col { flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; }
.trend-value { font-size: 11px; color: var(--text-secondary); margin-bottom: 3px; height: 14px; }
.trend-bar-wrap { flex: 1; width: 100%; display: flex; align-items: flex-end; justify-content: center; }
.trend-bar {
  width: 100%; max-width: 24px;
  background: var(--series-blue);
  border-radius: 4px 4px 0 0;      /* 数据端圆角，基线端保持方角 */
}
.trend-date { font-size: 11px; color: var(--text-muted); margin-top: 6px; }

/* ── 严重级：色点 + 图标 + 标签 + 数 ── */
.sev-list { list-style: none; margin: 0; padding: 0; }
.sev-row {
  display: flex; align-items: center; gap: 8px;
  padding: 7px 0; font-size: 13px; color: var(--text-secondary);
}
.sev-dot { width: 3px; height: 16px; border-radius: 2px; flex: none; }
.sev-icon { width: 14px; font-size: 12px; text-align: center; flex: none; }
.sev-name { flex: 1; }
.sev-count { font-variant-numeric: tabular-nums; color: var(--text-primary); }
.sev-chip { display: inline-flex; align-items: center; gap: 5px; font-size: 12px; white-space: nowrap; }

/* ── 名义分类排行：所有条同一个蓝，不按数值上色 ── */
.rank-list { list-style: none; margin: 0; padding: 0; }
.rank-row { display: flex; align-items: center; gap: 10px; padding: 5px 0; font-size: 12.5px; }
.rank-name {
  flex: none; width: 46%; color: var(--text-secondary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.rank-name.mono { font-family: monospace; font-size: 11.5px; }
.rank-name[title] { cursor: pointer; }
a.rank-name:hover { color: var(--brand, #409EFF); text-decoration: underline; }
.rank-bar-wrap {
  flex: 1; height: 6px; border-radius: 3px;
  background: color-mix(in srgb, var(--text-primary) 6%, transparent);
  overflow: hidden;
}
.rank-bar { display: block; height: 100%; background: var(--series-blue); border-radius: 3px; }
.rank-count {
  flex: none; width: 40px; text-align: right;
  font-variant-numeric: tabular-nums; color: var(--text-muted);
}

/* ── 事件表 ── */
.filter-row { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; align-items: center; }
.f-select { width: 170px; }
.f-select-sm { width: 110px; }
.f-input { width: 150px; }
.f-input-wide { width: 320px; }

.table-wrap {
  background: color-mix(in srgb, var(--surface, #fff) 3%, transparent);
  backdrop-filter: blur(12px);
  border: 1px solid color-mix(in srgb, var(--text-primary) 6%, transparent);
  border-radius: 14px; overflow: hidden;
}
.data-table { width: 100%; border-collapse: collapse; }
.data-table th {
  text-align: left; padding: 11px 14px; font-size: 11px; font-weight: 500;
  color: var(--text-muted); text-transform: uppercase;
  border-bottom: 1px solid color-mix(in srgb, var(--text-primary) 4%, transparent);
}
.data-table td {
  padding: 10px 14px; font-size: 12.5px; color: var(--text-secondary);
  border-bottom: 1px solid color-mix(in srgb, var(--text-primary) 2%, transparent);
}
.mono-cell { font-family: monospace; font-size: 11.5px; color: var(--text-muted); }
.mono-cell a { cursor: pointer; }
.mono-cell a:hover { color: var(--brand, #409EFF); text-decoration: underline; }
.date-cell { font-size: 11.5px; color: var(--text-muted); white-space: nowrap; }
.detail-cell { max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.empty, .empty-inline { text-align: center; color: var(--text-muted); font-size: 13px; padding: 28px 0; }
.empty-inline { padding: 14px 0; }
.pagination { display: flex; justify-content: center; padding: 14px; }

/* ── 未建的空态：明确说"还没做"，不做成看起来完整的空壳 ── */
.not-built { text-align: center; padding: 56px 24px; color: var(--text-muted); }
.not-built i { font-size: 26px; margin-bottom: 14px; opacity: .55; }
.nb-title { font-size: 15px; color: var(--text-secondary); margin: 0 0 8px; }
.nb-body { font-size: 13px; line-height: 1.75; max-width: 560px; margin: 0 auto 12px; }
.nb-hint { font-size: 12px; line-height: 1.7; max-width: 560px; margin: 0 auto; opacity: .8; }
.nb-hint code {
  font-family: monospace; font-size: 11.5px; padding: 1px 4px; border-radius: 4px;
  background: color-mix(in srgb, var(--text-primary) 7%, transparent);
}
</style>
