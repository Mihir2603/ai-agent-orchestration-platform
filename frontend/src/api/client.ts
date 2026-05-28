import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    console.error('API error:', err.response?.data || err.message)
    return Promise.reject(err)
  },
)

export default api

// ─── Agents ───────────────────────────────────────────────────────────────────
export const agentsApi = {
  list: () => api.get('/agents').then((r) => r.data),
  get: (id: string) => api.get(`/agents/${id}`).then((r) => r.data),
  create: (d: unknown) => api.post('/agents', d).then((r) => r.data),
  update: (id: string, d: unknown) => api.put(`/agents/${id}`, d).then((r) => r.data),
  delete: (id: string) => api.delete(`/agents/${id}`),
  listTools: () => api.get('/agents/tools').then((r) => r.data),
}

// ─── Workflows ────────────────────────────────────────────────────────────────
export const workflowsApi = {
  list: () => api.get('/workflows').then((r) => r.data),
  templates: () => api.get('/workflows/templates').then((r) => r.data),
  get: (id: string) => api.get(`/workflows/${id}`).then((r) => r.data),
  create: (d: unknown) => api.post('/workflows', d).then((r) => r.data),
  update: (id: string, d: unknown) => api.put(`/workflows/${id}`, d).then((r) => r.data),
  delete: (id: string) => api.delete(`/workflows/${id}`),
  execute: (id: string, task: string) =>
    api.post(`/workflows/${id}/execute`, { task_input: task }).then((r) => r.data),
}

// ─── Executions ───────────────────────────────────────────────────────────────
export const executionsApi = {
  list: (workflowId?: string) =>
    api.get('/executions', { params: workflowId ? { workflow_id: workflowId } : {} }).then((r) => r.data),
  get: (id: string) => api.get(`/executions/${id}`).then((r) => r.data),
  messages: (id: string) => api.get(`/executions/${id}/messages`).then((r) => r.data),
  delete: (id: string) => api.delete(`/executions/${id}`),
}

// ─── Channels ─────────────────────────────────────────────────────────────────
export const channelsApi = {
  list: () => api.get('/channels').then((r) => r.data),
  get: (id: string) => api.get(`/channels/${id}`).then((r) => r.data),
  create: (d: unknown) => api.post('/channels', d).then((r) => r.data),
  update: (id: string, d: unknown) => api.put(`/channels/${id}`, d).then((r) => r.data),
  delete: (id: string) => api.delete(`/channels/${id}`),
}
