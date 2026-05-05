import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

// Twitter 设置
export const getTwitterSettings = () => api.get('/settings/twitter')
export const saveTwitterSettings = (data) => api.put('/settings/twitter', data)
export const clearTwitterApiKey = () => api.delete('/settings/twitter/api-key')

// 时区
export const getTimezone = () => api.get('/settings/timezone')
export const saveTimezone = (data) => api.put('/settings/timezone', data)

// 采集间隔
export const getInterval = () => api.get('/settings/interval')
export const saveInterval = (data) => api.put('/settings/interval', data)

// Bark 设备
export const listBarkDevices = () => api.get('/bark-devices')
export const createBarkDevice = (data) => api.post('/bark-devices', data)
export const updateBarkDevice = (id, data) => api.put(`/bark-devices/${id}`, data)
export const deleteBarkDevice = (id) => api.delete(`/bark-devices/${id}`)
export const testBarkDevice = (id) => api.post(`/bark-devices/${id}/test`)

// 推文
export const getTweets = (params) => api.get('/tweets', { params })

// 采集
export const triggerCollect = () => api.post('/collect/trigger')
export const getCollectStatus = () => api.get('/collect/status')
export const getCollectHistory = () => api.get('/collect/history')

export default api
