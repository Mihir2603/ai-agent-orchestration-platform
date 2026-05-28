import { useEffect, useState } from 'react'
import { Plus, Bot, Trash2, Edit3, ChevronDown, ChevronUp, X } from 'lucide-react'
import { agentsApi } from '@/api/client'
import type { Agent, Tool } from '@/types'
import clsx from 'clsx'

const MODELS = [
  'gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo',
  'claude-3-5-sonnet-20241022', 'claude-3-haiku-20240307',
]

const DEFAULT_AGENT: Omit<Agent, 'id' | 'created_at' | 'updated_at'> = {
  name: '', role: '', description: '',
  system_prompt: 'You are a helpful assistant.',
  model: 'gpt-4o-mini', temperature: 0.7, max_tokens: 2048,
  tools: [], memory_enabled: false, memory_window: 10,
  guardrails: {}, schedule_enabled: false, schedule_cron: '', schedule_task: '',
  avatar_color: '#6366f1',
}

const COLORS = ['#6366f1','#8b5cf6','#06b6d4','#10b981','#f59e0b','#ef4444','#ec4899','#64748b']

export default function Agents() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [tools, setTools] = useState<Tool[]>([])
  const [showForm, setShowForm] = useState(false)
  const [editAgent, setEditAgent] = useState<Agent | null>(null)
  const [form, setForm] = useState({ ...DEFAULT_AGENT })
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const load = () => {
    agentsApi.list().then(setAgents).catch(console.error)
    agentsApi.listTools().then(setTools).catch(console.error)
  }

  useEffect(() => { load() }, [])

  function openCreate() {
    setEditAgent(null)
    setForm({ ...DEFAULT_AGENT })
    setShowForm(true)
  }

  function openEdit(a: Agent) {
    setEditAgent(a)
    setForm({
      name: a.name, role: a.role, description: a.description,
      system_prompt: a.system_prompt, model: a.model,
      temperature: a.temperature, max_tokens: a.max_tokens,
      tools: [...a.tools], memory_enabled: a.memory_enabled,
      memory_window: a.memory_window, guardrails: { ...a.guardrails },
      schedule_enabled: a.schedule_enabled, schedule_cron: a.schedule_cron,
      schedule_task: a.schedule_task, avatar_color: a.avatar_color,
    })
    setShowForm(true)
  }

  async function handleSave() {
    if (!form.name.trim()) return
    setSaving(true)
    try {
      if (editAgent) {
        await agentsApi.update(editAgent.id, form)
      } else {
        await agentsApi.create(form)
      }
      setShowForm(false)
      load()
    } catch (e) {
      console.error(e)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Delete this agent?')) return
    await agentsApi.delete(id)
    load()
  }

  function toggleTool(name: string) {
    setForm((f) => ({
      ...f,
      tools: f.tools.includes(name) ? f.tools.filter((t) => t !== name) : [...f.tools, name],
    }))
  }

  return (
    <div className="p-6 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Agents</h1>
          <p className="text-sm text-slate-400 mt-1">Create and configure AI agents</p>
        </div>
        <button onClick={openCreate} className="btn-primary">
          <Plus size={14} /> New Agent
        </button>
      </div>

      {/* Agent cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {agents.map((a) => (
          <div key={a.id} className="card overflow-hidden">
            <div className="h-1" style={{ background: a.avatar_color }} />
            <div className="p-4">
              <div className="flex items-start gap-3">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{ background: `${a.avatar_color}22` }}
                >
                  <Bot size={18} style={{ color: a.avatar_color }} />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="font-semibold text-white truncate">{a.name}</h3>
                  <p className="text-xs text-slate-400 truncate">{a.role || a.model}</p>
                </div>
                <div className="flex gap-1">
                  <button onClick={() => openEdit(a)} className="p-1.5 rounded hover:bg-slate-700 text-slate-400 hover:text-white transition-colors">
                    <Edit3 size={13} />
                  </button>
                  <button onClick={() => handleDelete(a.id)} className="p-1.5 rounded hover:bg-red-500/10 text-slate-400 hover:text-red-400 transition-colors">
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>

              {a.description && (
                <p className="text-xs text-slate-500 mt-2 line-clamp-2">{a.description}</p>
              )}

              <div className="flex flex-wrap gap-1 mt-3">
                <span className="badge badge-blue">{a.model}</span>
                {a.tools.slice(0, 2).map((t) => (
                  <span key={t} className="badge badge-gray">{t}</span>
                ))}
                {a.tools.length > 2 && (
                  <span className="badge badge-gray">+{a.tools.length - 2}</span>
                )}
              </div>

              <button
                onClick={() => setExpandedId(expandedId === a.id ? null : a.id)}
                className="mt-3 w-full flex items-center justify-center gap-1 text-xs text-slate-500 hover:text-slate-300 transition-colors"
              >
                {expandedId === a.id ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                {expandedId === a.id ? 'Less' : 'Details'}
              </button>

              {expandedId === a.id && (
                <div className="mt-3 pt-3 border-t border-slate-700/50 space-y-2 text-xs text-slate-400">
                  <div><span className="text-slate-500">Temp:</span> {a.temperature}</div>
                  <div><span className="text-slate-500">Max tokens:</span> {a.max_tokens}</div>
                  <div><span className="text-slate-500">Memory:</span> {a.memory_enabled ? `On (${a.memory_window} msgs)` : 'Off'}</div>
                  <div className="font-mono text-[10px] text-slate-500 bg-surface-900 rounded p-2 max-h-20 overflow-y-auto">
                    {a.system_prompt.slice(0, 200)}…
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        {agents.length === 0 && (
          <div className="col-span-full card p-12 flex flex-col items-center text-center">
            <Bot size={40} className="text-slate-600 mb-3" />
            <p className="text-slate-400 font-medium">No agents yet</p>
            <p className="text-sm text-slate-600 mt-1">Create your first AI agent to get started</p>
            <button onClick={openCreate} className="btn-primary mt-4"><Plus size={14} />Create Agent</button>
          </div>
        )}
      </div>

      {/* Modal / Form */}
      {showForm && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="card w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-surface-800 px-5 py-4 border-b border-slate-700/50 flex items-center justify-between z-10">
              <h2 className="font-semibold text-white">{editAgent ? 'Edit Agent' : 'New Agent'}</h2>
              <button onClick={() => setShowForm(false)} className="text-slate-400 hover:text-white"><X size={18} /></button>
            </div>
            <div className="p-5 space-y-4">

              {/* Color picker */}
              <div>
                <label className="label">Color</label>
                <div className="flex gap-2">
                  {COLORS.map((c) => (
                    <button
                      key={c} onClick={() => setForm((f) => ({ ...f, avatar_color: c }))}
                      className={`w-6 h-6 rounded-full border-2 transition-all ${form.avatar_color === c ? 'border-white scale-125' : 'border-transparent'}`}
                      style={{ background: c }}
                    />
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Name *</label>
                  <input className="input" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} placeholder="Research Agent" />
                </div>
                <div>
                  <label className="label">Role</label>
                  <input className="input" value={form.role} onChange={(e) => setForm((f) => ({ ...f, role: e.target.value }))} placeholder="Senior Researcher" />
                </div>
              </div>

              <div>
                <label className="label">Description</label>
                <input className="input" value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} placeholder="Brief description…" />
              </div>

              <div>
                <label className="label">System Prompt *</label>
                <textarea
                  className="input resize-none" rows={5}
                  value={form.system_prompt}
                  onChange={(e) => setForm((f) => ({ ...f, system_prompt: e.target.value }))}
                  placeholder="You are a helpful assistant…"
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="label">Model</label>
                  <select className="input" value={form.model} onChange={(e) => setForm((f) => ({ ...f, model: e.target.value }))}>
                    {MODELS.map((m) => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>
                <div>
                  <label className="label">Temperature ({form.temperature})</label>
                  <input type="range" min="0" max="2" step="0.1" className="w-full accent-indigo-500 mt-2"
                    value={form.temperature} onChange={(e) => setForm((f) => ({ ...f, temperature: parseFloat(e.target.value) }))} />
                </div>
                <div>
                  <label className="label">Max Tokens</label>
                  <input className="input" type="number" value={form.max_tokens}
                    onChange={(e) => setForm((f) => ({ ...f, max_tokens: parseInt(e.target.value) }))} />
                </div>
              </div>

              {/* Tools */}
              <div>
                <label className="label">Tools</label>
                <div className="flex flex-wrap gap-2">
                  {tools.map((t) => (
                    <button
                      key={t.name}
                      onClick={() => toggleTool(t.name)}
                      className={clsx(
                        'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all',
                        form.tools.includes(t.name)
                          ? 'bg-indigo-600/30 border-indigo-500 text-indigo-300'
                          : 'bg-surface-900 border-slate-600 text-slate-400 hover:border-slate-500'
                      )}
                      title={t.description}
                    >
                      {t.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Memory */}
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" className="accent-indigo-500 w-4 h-4"
                    checked={form.memory_enabled}
                    onChange={(e) => setForm((f) => ({ ...f, memory_enabled: e.target.checked }))} />
                  <span className="text-sm text-slate-300">Enable conversation memory</span>
                </label>
                {form.memory_enabled && (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500">Window:</span>
                    <input className="input w-16 text-center" type="number" min="1" max="50"
                      value={form.memory_window}
                      onChange={(e) => setForm((f) => ({ ...f, memory_window: parseInt(e.target.value) }))} />
                  </div>
                )}
              </div>
            </div>

            <div className="sticky bottom-0 bg-surface-800 px-5 py-4 border-t border-slate-700/50 flex justify-end gap-2">
              <button onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
              <button onClick={handleSave} disabled={saving || !form.name.trim()} className="btn-primary">
                {saving ? 'Saving…' : editAgent ? 'Update Agent' : 'Create Agent'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
