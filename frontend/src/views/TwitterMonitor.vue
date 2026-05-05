<template>
  <div>
    <div class="page-header">
      <h2>博主监控</h2>
      <div style="display:flex;gap:8px;align-items:center">
        <el-tag v-if="barkCount > 0" type="success" size="small">
          <el-icon><Bell /></el-icon> {{ barkCount }} 个 Bark 设备
        </el-tag>
        <el-tag v-else type="warning" size="small">
          <el-icon><Bell /></el-icon> Bark 未配置
        </el-tag>
        <el-button size="small" type="primary" :loading="collecting" @click="triggerCollect">
          立即采集
        </el-button>
      </div>
    </div>

    <!-- 采集状态条 -->
    <el-alert
      v-if="lastResult"
      :title="lastResultText"
      type="info"
      show-icon
      :closable="false"
      style="margin-bottom:16px"
    />

    <div class="monitor-layout">
      <!-- 左列：博主列表 -->
      <div class="left-col">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span class="card-title">监控博主</span>
              <el-button type="primary" size="small" :icon="Plus" @click="showAddDialog = true">添加</el-button>
            </div>
          </template>

          <div v-if="users.length === 0" class="empty-tip">
            <el-empty description="还没有监控任何博主" :image-size="80" />
          </div>

          <div v-else class="user-list">
            <div
              v-for="user in users"
              :key="user"
              class="user-item"
              :class="{ active: filterUser === user }"
              @click="setFilter(user)"
            >
              <div class="user-info">
                <el-avatar :size="34" style="background:#1d9bf0;flex-shrink:0">
                  {{ user[0].toUpperCase() }}
                </el-avatar>
                <div class="user-text">
                  <span class="username">@{{ user }}</span>
                  <span class="tweet-count">{{ tweetCounts[user] || 0 }} 条</span>
                </div>
              </div>
              <div class="user-actions">
                <a :href="`https://x.com/${user}`" target="_blank" class="ext-link" @click.stop>
                  <el-icon><TopRight /></el-icon>
                </a>
                <el-button type="danger" size="small" plain :icon="Delete" @click.stop="removeUser(user)" />
              </div>
            </div>
          </div>
        </el-card>

        <!-- 采集日志 -->
        <el-card shadow="never">
          <template #header><span class="card-title">采集记录</span></template>
          <div v-if="history.length === 0" style="color:#909399;font-size:13px">暂无记录</div>
          <div v-else class="history-list">
            <div v-for="h in history.slice(0, 5)" :key="h.id" class="history-item">
              <el-tag :type="h.status === 'success' ? 'success' : 'danger'" size="small">
                {{ h.status === 'success' ? '成功' : '失败' }}
              </el-tag>
              <span class="history-time">{{ formatTime(h.started_at) }}</span>
              <span v-if="h.result && !h.result.error" class="history-detail">
                +{{ h.result.saved }} 条
              </span>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 右列：推文列表 -->
      <div class="right-col">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                {{ filterUser ? `@${filterUser} 的推文` : '全部推文' }}
              </span>
              <div style="display:flex;gap:8px;align-items:center">
                <el-button v-if="filterUser" size="small" @click="filterUser = ''; loadTweets()">
                  显示全部
                </el-button>
                <el-button size="small" :icon="Refresh" :loading="loadingTweets" @click="loadTweets" />
              </div>
            </div>
          </template>

          <div v-if="loadingTweets" style="padding:24px">
            <el-skeleton :rows="5" animated />
          </div>

          <div v-else-if="tweets.length === 0" class="empty-tip">
            <el-empty description="暂无推文，配置好 API Key 后点击「立即采集」" :image-size="80" />
          </div>

          <div v-else class="tweet-list">
            <div v-for="t in tweets" :key="t.id" class="tweet-item">
              <div class="tweet-meta">
                <span class="tweet-author" @click="setFilter(t.author)">@{{ t.author }}</span>
                <span class="tweet-time">{{ formatTime(t.tweeted_at || t.saved_at) }}</span>
                <a v-if="t.url" :href="t.url" target="_blank" class="tweet-link">
                  <el-icon><TopRight /></el-icon> 查看原文
                </a>
              </div>
              <div class="tweet-content">{{ t.content }}</div>
              <div v-if="t.content_zh" class="tweet-content-zh">{{ t.content_zh }}</div>
            </div>
          </div>

          <div v-if="total > pageSize" class="pagination">
            <el-pagination
              v-model:current-page="page"
              :page-size="pageSize"
              :total="total"
              layout="total, prev, pager, next"
              small
              @current-change="loadTweets"
            />
          </div>
        </el-card>
      </div>
    </div>

    <!-- 添加博主 dialog -->
    <el-dialog v-model="showAddDialog" title="添加监控博主" width="380px" :close-on-click-modal="false">
      <el-form @submit.prevent="handleAddUser">
        <el-form-item label="用户名">
          <el-input
            v-model="newUsername"
            placeholder="输入用户名，不含 @"
            clearable
            autofocus
            @keyup.enter="handleAddUser"
          >
            <template #prepend>@</template>
          </el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" :loading="addingUser" @click="handleAddUser">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Refresh, TopRight, Bell } from '@element-plus/icons-vue'
import {
  getTwitterSettings, saveTwitterSettings,
  listBarkDevices, getTweets,
  triggerCollect as apiTrigger, getCollectStatus, getCollectHistory,
} from '../api'
import { formatTime } from '../lib/timezone'

// ── 博主列表 ──────────────────────────────────────────────────────────────────
const users = ref([])
const showAddDialog = ref(false)
const newUsername = ref('')
const addingUser = ref(false)
const tweetCounts = ref({})

const loadUsers = async () => {
  try {
    const { data } = await getTwitterSettings()
    users.value = (data.watch_users || '').split(',').map(u => u.trim()).filter(Boolean)
    loadTweetCounts()
  } catch { ElMessage.error('加载博主列表失败') }
}

const loadTweetCounts = async () => {
  for (const u of users.value) {
    try {
      const { data } = await getTweets({ author: u, page: 1, size: 1 })
      tweetCounts.value[u] = data.total
    } catch {}
  }
}

const saveUsers = async () => {
  await saveTwitterSettings({ watch_users: users.value.join(',') })
}

const handleAddUser = async () => {
  const name = newUsername.value.trim().replace(/^@/, '')
  if (!name) return
  if (users.value.includes(name)) { ElMessage.warning('已在监控列表中'); return }
  addingUser.value = true
  try {
    users.value = [...users.value, name]
    await saveUsers()
    ElMessage.success(`已添加 @${name}`)
    showAddDialog.value = false
    newUsername.value = ''
    loadTweets()
  } catch {
    users.value = users.value.filter(u => u !== name)
    ElMessage.error('添加失败')
  } finally { addingUser.value = false }
}

const removeUser = async (user) => {
  try {
    await ElMessageBox.confirm(`确认移除对 @${user} 的监控？`, '确认', {
      type: 'warning', confirmButtonText: '移除', cancelButtonText: '取消',
    })
  } catch { return }
  users.value = users.value.filter(u => u !== user)
  if (filterUser.value === user) filterUser.value = ''
  try {
    await saveUsers()
    ElMessage.success(`已移除 @${user}`)
    loadTweets()
  } catch { ElMessage.error('保存失败') }
}

// ── Bark 状态 ─────────────────────────────────────────────────────────────────
const barkCount = ref(0)
const loadBark = async () => {
  try {
    const { data } = await listBarkDevices()
    barkCount.value = data.items.filter(d => d.enabled).length
  } catch {}
}

// ── 推文列表 ──────────────────────────────────────────────────────────────────
const tweets = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loadingTweets = ref(false)
const filterUser = ref('')

const loadTweets = async () => {
  loadingTweets.value = true
  try {
    const params = { page: page.value, size: pageSize }
    if (filterUser.value) params.author = filterUser.value
    const { data } = await getTweets(params)
    tweets.value = data.items
    total.value = data.total
  } catch { ElMessage.error('加载推文失败') }
  finally { loadingTweets.value = false }
}

const setFilter = (user) => {
  filterUser.value = filterUser.value === user ? '' : user
  page.value = 1
  loadTweets()
}

// ── 立即采集 ──────────────────────────────────────────────────────────────────
const collecting = ref(false)
const lastResult = ref(null)
const history = ref([])

const lastResultText = computed(() => {
  if (!lastResult.value) return ''
  const r = lastResult.value
  if (r.error) return `上次采集失败: ${r.error}`
  return `上次采集：新增 ${r.saved} 条，跳过 ${r.skipped} 条，推送 ${r.pushed || 0} 条`
})

const loadStatus = async () => {
  try {
    const [s, h] = await Promise.all([getCollectStatus(), getCollectHistory()])
    lastResult.value = s.data.last_result
    history.value = h.data.items
  } catch {}
}

const triggerCollect = async () => {
  collecting.value = true
  try {
    await apiTrigger()
    ElMessage.success('采集已启动')
    // 等待完成后刷新
    setTimeout(async () => {
      await loadStatus()
      await loadTweets()
      await loadTweetCounts()
      collecting.value = false
    }, 8000)
  } catch {
    ElMessage.error('启动失败')
    collecting.value = false
  }
}


onMounted(() => {
  loadUsers()
  loadBark()
  loadTweets()
  loadStatus()
})
</script>

<style scoped>
.monitor-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 16px;
  align-items: start;
}
@media (max-width: 768px) {
  .monitor-layout { grid-template-columns: 1fr; }
}

.left-col, .right-col { display: flex; flex-direction: column; gap: 16px; }

.card-header { display: flex; align-items: center; justify-content: space-between; }
.card-title { font-weight: 600; }

.user-list { display: flex; flex-direction: column; gap: 6px; }
.user-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 10px; border-radius: 6px;
  background: var(--el-fill-color-lighter);
  cursor: pointer; transition: background 0.15s;
}
.user-item:hover, .user-item.active { background: var(--el-color-primary-light-9); }
.user-info { display: flex; align-items: center; gap: 8px; }
.user-text { display: flex; flex-direction: column; gap: 2px; }
.username { font-weight: 500; font-size: 14px; }
.tweet-count { font-size: 11px; color: #909399; }
.user-actions { display: flex; align-items: center; gap: 6px; }
.ext-link { color: #409eff; display: flex; align-items: center; }

.history-list { display: flex; flex-direction: column; gap: 6px; }
.history-item { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.history-time { color: #909399; font-size: 12px; }
.history-detail { color: #67c23a; }

.empty-tip { padding: 24px 0; text-align: center; }

.tweet-list { display: flex; flex-direction: column; }
.tweet-item {
  padding: 14px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.tweet-item:last-child { border-bottom: none; }
.tweet-meta { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; flex-wrap: wrap; }
.tweet-author {
  font-weight: 600; color: #1d9bf0; font-size: 13px;
  cursor: pointer;
}
.tweet-author:hover { text-decoration: underline; }
.tweet-time { font-size: 12px; color: #909399; }
.tweet-link {
  font-size: 12px; color: #409eff;
  display: flex; align-items: center; gap: 2px; text-decoration: none;
}
.tweet-content {
  font-size: 14px; line-height: 1.7;
  white-space: pre-wrap; word-break: break-word;
}
.tweet-content-zh {
  font-size: 13px; line-height: 1.6; color: #606266;
  margin-top: 6px; padding-left: 10px;
  border-left: 3px solid var(--el-color-primary-light-5);
  white-space: pre-wrap; word-break: break-word;
}
.pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
