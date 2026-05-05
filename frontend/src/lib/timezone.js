/**
 * 全局时区状态，启动时从后端加载，Settings 页保存后更新
 */
import { ref } from 'vue'
import { getTimezone } from '../api'

export const timezone = ref('Asia/Shanghai')

export async function loadTimezone() {
  try {
    const { data } = await getTimezone()
    timezone.value = data.timezone || 'Asia/Shanghai'
  } catch {}
}

export function formatTime(iso, tz) {
  if (!iso) return ''
  try {
    // 后端返回无时区后缀的 UTC 时间，加 Z 确保按 UTC 解析
    const utcIso = iso.endsWith('Z') || iso.includes('+') ? iso : iso + 'Z'
    const d = new Date(utcIso)
    const now = new Date()
    const diff = Math.floor((now - d) / 1000)
    const useTz = tz || timezone.value
    const localStr = new Intl.DateTimeFormat('zh-CN', {
      timeZone: useTz,
      month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit',
    }).format(d)
    if (diff < 60) return `${diff} 秒前（${localStr}）`
    if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前（${localStr}）`
    if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前（${localStr}）`
    return new Intl.DateTimeFormat('zh-CN', {
      timeZone: useTz,
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit',
    }).format(d)
  } catch { return iso }
}
