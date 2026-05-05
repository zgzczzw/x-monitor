<template>
  <div>
    <div class="page-header"><h2>系统设置</h2></div>

    <div class="settings-layout">

      <!-- Twitter API Key -->
      <el-card shadow="never">
        <template #header>
          <div style="display:flex;align-items:center;gap:8px">
            <el-icon style="font-size:18px;color:#1d9bf0"><Platform /></el-icon>
            <span style="font-weight:600">Twitter / X（twitterapi.io）</span>
            <el-tag v-if="twitter.api_key_configured" type="success" size="small">已配置</el-tag>
            <el-tag v-else type="info" size="small">未配置</el-tag>
          </div>
        </template>

        <el-form label-position="top" @submit.prevent>
          <el-form-item>
            <template #label>
              <span>API Key</span>
              <span v-if="twitter.api_key_configured" style="margin-left:8px;font-size:12px;color:#909399">
                当前：{{ twitter.api_key_masked }}
              </span>
            </template>
            <el-input
              v-model="twitterForm.api_key"
              type="password"
              show-password
              :placeholder="twitter.api_key_configured ? '留空则保持不变，填写新值则覆盖' : '请输入 twitterapi.io API Key'"
              clearable
            />
            <div class="hint">申请地址：twitterapi.io &nbsp;·&nbsp; 计费约 $0.15 / 1k 条推文</div>
          </el-form-item>

          <div style="display:flex;gap:8px">
            <el-button type="primary" :loading="twitterSaving" @click="handleTwitterSave">保存</el-button>
            <el-button v-if="twitter.api_key_configured" type="danger" plain :loading="twitterClearing" @click="handleTwitterClearKey">
              清除 Key
            </el-button>
          </div>
        </el-form>
      </el-card>

      <!-- 时区设置 -->
      <el-card shadow="never">
        <template #header>
          <div style="display:flex;align-items:center;gap:8px">
            <el-icon style="font-size:18px;color:#67c23a"><Clock /></el-icon>
            <span style="font-weight:600">时区设置</span>
          </div>
        </template>
        <el-form label-position="top" @submit.prevent>
          <el-form-item label="显示时区">
            <el-select v-model="tz" style="width:100%" filterable>
              <el-option
                v-for="t in tzOptions"
                :key="t.value"
                :label="t.label"
                :value="t.value"
              />
            </el-select>
            <div class="hint">影响推文时间的显示，不影响数据存储（数据库统一存 UTC）。</div>
          </el-form-item>
          <el-button type="primary" :loading="tzSaving" @click="handleTzSave">保存</el-button>
        </el-form>
      </el-card>

      <!-- 采集间隔 -->
      <el-card shadow="never">
        <template #header>
          <div style="display:flex;align-items:center;gap:8px">
            <el-icon style="font-size:18px;color:#e6a23c"><Timer /></el-icon>
            <span style="font-weight:600">采集间隔</span>
          </div>
        </template>
        <el-form label-position="top" @submit.prevent>
          <el-form-item label="轮询间隔（分钟）">
            <el-input-number v-model="intervalMinutes" :min="1" :max="60" style="width:160px" />
            <div class="hint" style="margin-top:6px">
              每隔多少分钟检查一次博主新推文。twitterapi.io 无 webhook，只能轮询。<br>
              建议 5 分钟，最低 1 分钟（注意 API 用量）。
            </div>
          </el-form-item>
          <el-button type="primary" :loading="intervalSaving" @click="handleIntervalSave">保存并立即生效</el-button>
        </el-form>
      </el-card>

      <!-- Bark 推送设备 -->
      <el-card shadow="never">
        <template #header>
          <div style="display:flex;align-items:center;gap:8px;flex:1">
            <el-icon style="font-size:18px;color:#ff6900"><Bell /></el-icon>
            <span style="font-weight:600">Bark 推送设备（iOS）</span>
            <el-tag v-if="enabledDevices > 0" type="success" size="small">{{ enabledDevices }} 个已启用</el-tag>
            <el-tag v-else type="info" size="small">未配置</el-tag>
            <el-button type="primary" size="small" style="margin-left:auto" @click="openDialog()">
              <el-icon><Plus /></el-icon> 添加设备
            </el-button>
          </div>
        </template>

        <div v-if="devices.length === 0" style="color:#909399;font-size:13px;padding:4px 0">
          还没有 Bark 设备。监控到新推文时将推送到所有已启用的设备。
        </div>

        <div v-else class="device-list">
          <div v-for="d in devices" :key="d.id" class="device-item">
            <div class="device-info">
              <div class="device-name">
                {{ d.name }}
                <el-tag :type="d.enabled ? 'success' : 'info'" size="small">{{ d.enabled ? '启用' : '停用' }}</el-tag>
              </div>
              <div class="device-meta">
                {{ d.server_url }} · Key: {{ d.device_key_masked }}
                <span v-if="d.sound"> · 铃声: {{ d.sound }}</span>
              </div>
            </div>
            <div class="device-actions">
              <el-button size="small" :loading="d._testing" @click="testDevice(d)">测试</el-button>
              <el-button size="small" @click="openDialog(d)">编辑</el-button>
              <el-button size="small" type="danger" plain @click="handleDelete(d)">删除</el-button>
            </div>
          </div>
        </div>

        <el-alert
          v-if="feedback.msg"
          :title="feedback.msg"
          :type="feedback.ok ? 'success' : 'error'"
          show-icon closable style="margin-top:12px"
          @close="feedback.msg = ''"
        />
      </el-card>

    </div>

    <!-- Bark 设备 Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="editId ? '编辑设备' : '添加 Bark 设备'"
      width="460px"
      :close-on-click-modal="false"
    >
      <el-form :model="form" label-position="top">
        <el-form-item label="设备名称">
          <el-input v-model="form.name" placeholder="如：我的 iPhone" clearable />
        </el-form-item>
        <el-form-item label="Bark 服务地址">
          <el-input v-model="form.server_url" placeholder="https://api.day.app" clearable />
          <div class="hint">官方：https://api.day.app，或自建服务地址</div>
        </el-form-item>
        <el-form-item :label="editId ? 'Device Key（留空则不修改）' : 'Device Key'">
          <el-input
            v-model="form.device_key"
            type="password"
            show-password
            :placeholder="editId ? '留空则不修改' : '打开 Bark App 复制 Key'"
            clearable
          />
          <div class="hint">Bark App 首页显示的那段 Key</div>
        </el-form-item>
        <el-form-item label="通知铃声（可选）">
          <el-input v-model="form.sound" placeholder="如：alarm、glass（留空用默认）" clearable />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getTwitterSettings, saveTwitterSettings, clearTwitterApiKey,
  listBarkDevices, createBarkDevice, updateBarkDevice,
  deleteBarkDevice as apiDelete, testBarkDevice as apiTest,
  getTimezone, saveTimezone,
  getInterval, saveInterval,
} from '../api'
import { timezone as globalTz } from '../lib/timezone'

// ── Twitter ──────────────────────────────────────────────────────────────────
const twitter = ref({ api_key_configured: false, api_key_masked: '' })
const twitterForm = reactive({ api_key: '' })
const twitterSaving = ref(false)
const twitterClearing = ref(false)

const loadTwitter = async () => {
  try {
    const { data } = await getTwitterSettings()
    twitter.value = data
    twitterForm.api_key = ''
  } catch { ElMessage.error('加载 Twitter 配置失败') }
}

const handleTwitterSave = async () => {
  twitterSaving.value = true
  try {
    await saveTwitterSettings({ api_key: twitterForm.api_key })
    ElMessage.success('保存成功')
    await loadTwitter()
  } catch { ElMessage.error('保存失败') }
  finally { twitterSaving.value = false }
}

const handleTwitterClearKey = async () => {
  try {
    await ElMessageBox.confirm('确认清除 API Key？', '确认', { type: 'warning', confirmButtonText: '清除', cancelButtonText: '取消' })
  } catch { return }
  twitterClearing.value = true
  try {
    await clearTwitterApiKey()
    ElMessage.success('已清除')
    await loadTwitter()
  } catch { ElMessage.error('清除失败') }
  finally { twitterClearing.value = false }
}

// ── Bark 设备 ────────────────────────────────────────────────────────────────
const devices = ref([])
const saving = ref(false)
const feedback = reactive({ msg: '', ok: false })
const dialogVisible = ref(false)
const editId = ref(null)
const form = reactive({ name: '', server_url: 'https://api.day.app', device_key: '', sound: '', enabled: true })

const enabledDevices = computed(() => devices.value.filter(d => d.enabled).length)

const loadDevices = async () => {
  try {
    const { data } = await listBarkDevices()
    devices.value = data.items
  } catch { ElMessage.error('加载设备失败') }
}

const openDialog = (d = null) => {
  if (d) {
    editId.value = d.id
    form.name = d.name
    form.server_url = d.server_url
    form.device_key = ''
    form.sound = d.sound || ''
    form.enabled = d.enabled
  } else {
    editId.value = null
    form.name = ''
    form.server_url = 'https://api.day.app'
    form.device_key = ''
    form.sound = ''
    form.enabled = true
  }
  dialogVisible.value = true
}

const handleSave = async () => {
  if (!form.name.trim()) { ElMessage.warning('请填写设备名称'); return }
  if (!editId.value && !form.device_key.trim()) { ElMessage.warning('请填写 Device Key'); return }
  saving.value = true
  try {
    if (editId.value) {
      await updateBarkDevice(editId.value, { ...form })
    } else {
      await createBarkDevice({ ...form })
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await loadDevices()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '保存失败') }
  finally { saving.value = false }
}

const testDevice = async (d) => {
  d._testing = true
  feedback.msg = ''
  try {
    const { data } = await apiTest(d.id)
    feedback.ok = data.ok
    feedback.msg = `「${d.name}」${data.message}`
  } catch { feedback.ok = false; feedback.msg = '请求失败' }
  finally { d._testing = false }
}

const handleDelete = async (d) => {
  try {
    await ElMessageBox.confirm(`确认删除「${d.name}」？`, '确认', { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' })
  } catch { return }
  try {
    await apiDelete(d.id)
    ElMessage.success('已删除')
    await loadDevices()
  } catch { ElMessage.error('删除失败') }
}

// ── 时区 ─────────────────────────────────────────────────────────────────────
const tz = ref('Asia/Shanghai')
const tzSaving = ref(false)
const tzOptions = [
  { label: 'UTC+8 北京/上海 (Asia/Shanghai)', value: 'Asia/Shanghai' },
  { label: 'UTC+8 香港 (Asia/Hong_Kong)', value: 'Asia/Hong_Kong' },
  { label: 'UTC+8 台北 (Asia/Taipei)', value: 'Asia/Taipei' },
  { label: 'UTC+9 东京 (Asia/Tokyo)', value: 'Asia/Tokyo' },
  { label: 'UTC+0 伦敦 (Europe/London)', value: 'Europe/London' },
  { label: 'UTC-5 纽约 (America/New_York)', value: 'America/New_York' },
  { label: 'UTC-8 洛杉矶 (America/Los_Angeles)', value: 'America/Los_Angeles' },
  { label: 'UTC (UTC)', value: 'UTC' },
]

const loadTz = async () => {
  try {
    const { data } = await getTimezone()
    tz.value = data.timezone || 'Asia/Shanghai'
  } catch {}
}

const handleTzSave = async () => {
  tzSaving.value = true
  try {
    await saveTimezone({ timezone: tz.value })
    globalTz.value = tz.value
    ElMessage.success('时区已保存')
  } catch { ElMessage.error('保存失败') }
  finally { tzSaving.value = false }
}

// ── 采集间隔 ─────────────────────────────────────────────────────────────────
const intervalMinutes = ref(5)
const intervalSaving = ref(false)

const loadInterval = async () => {
  try {
    const { data } = await getInterval()
    intervalMinutes.value = data.interval_minutes
  } catch {}
}

const handleIntervalSave = async () => {
  intervalSaving.value = true
  try {
    await saveInterval({ interval_minutes: intervalMinutes.value })
    ElMessage.success(`已设为每 ${intervalMinutes.value} 分钟采集一次，立即生效`)
  } catch { ElMessage.error('保存失败') }
  finally { intervalSaving.value = false }
}

onMounted(() => {
  loadTwitter()
  loadTz()
  loadInterval()
  loadDevices()
})
</script>

<style scoped>
.settings-layout { display: flex; flex-direction: column; gap: 16px; max-width: 640px; }
.hint { font-size: 12px; color: #909399; margin-top: 4px; line-height: 1.6; }

.device-list { display: flex; flex-direction: column; gap: 8px; }
.device-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 12px; border-radius: 6px;
  background: var(--el-fill-color-lighter); gap: 12px; flex-wrap: wrap;
}
.device-info { display: flex; flex-direction: column; gap: 4px; flex: 1; min-width: 0; }
.device-name { display: flex; align-items: center; gap: 6px; font-weight: 500; font-size: 14px; }
.device-meta { font-size: 12px; color: #909399; }
.device-actions { display: flex; gap: 6px; flex-shrink: 0; }
</style>
