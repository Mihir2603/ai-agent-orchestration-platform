import { useEffect, useState } from 'react'
import { MessageSquare, Plus, Trash2, Bot, CheckCircle2, XCircle, X } from 'lucide-react'
import { channelsApi, agentsApi } from '@/api/client'
import type { Channel, Agent } from '@/types'

const CHANNEL_TYPES = [
  { value: 'telegram', label: 'Telegram', color: '#26A5E4', icon: '✈️' },
  { value: 'slack', label: 'Slack', color: '#4A154B', icon: '💬' },
  { value: 'webhook', label: 'Webhook', color: '#10b981', icon: '🔗' },
]

const DEFAULT_FORM = {
  agent_id: '',
  channel_type: 'telegram',
  name: '',
  config: {} as Record<string, string>,
}

export default function Channels() {
  const [channels, setChannels] = useState<Channel[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ ...DEFAULT_FORM })
  const [botToken, setBotToken] = useState('')
  const [saving, setSaving] = useState(false)

  const load = () => {
    channelsApi.list().then(setChannels).catch(console.error)
    agentsApi.list().then(setAgents).catch(console.error)
  }

  useEffect(() => { load() }, [])

  async function handleSave() {
    if (!form.agent_id || !form.channel_type) return
    setSaving(true)
    const config: Record<string, string> = {}
    if (form.channel_type === 'telegram' && botToken) {
      config.bot_token = botToken
    }
    try {
      await channelsApi.create({ ...form, config })
      setShowForm(false)
      setForm({ ...DEFAULT_FORM })
      setBotToken('')
      load()
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Remove this channel?')) return
    await channelsApi.delete(id)
    load()
  }

  async function toggleActive(ch: Channel) {
    await channelsApi.update(ch.id, { is_active: !ch.is_active })
    load()
  }

  const agentMap = Object.fromEntries(agents.map((a) => [a.id, a]))

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Channels</h1>
          <p className="text-sm text-slate-400 mt-1">Connect agents to external messaging platforms</p>
        </div>
        <button onClick={() => setShowForm(true)} className="btn-primary">
          <Plus size={14} /> Connect Channel
        </button>
      </div>

      {/* Channel cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {channels.map((ch) => {
          const typeInfo = CHANNEL_TYPES.find((t) => t.value === ch.channel_type)
          const agent = agentMap[ch.agent_id]
          return (
            <div key={ch.id} className="card p-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
                    style={{ background: `${typeInfo?.color}22` }}
                  >
                    {typeInfo?.icon}
                  </div>
                  <div>
                    <h3 className="font-medium text-white">{typeInfo?.label || ch.channel_type}</h3>
                    <p className="text-xs text-slate-400">{ch.name || 'No name'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-1.5">
                  {ch.is_active ? (
                    <CheckCircle2 size={14} className="text-emerald-400" />
                  ) : (
                    <XCircle size={14} className="text-slate-500" />
                  )}
                </div>
              </div>

              {agent && (
                <div className="flex items-center gap-2 py-2 px-3 bg-surface-900 rounded-lg mb-3">
                  <div className="w-5 h-5 rounded flex items-center justify-center" style={{ background: `${agent.avatar_color}33` }}>
                    <Bot size={10} style={{ color: agent.avatar_color }} />
                  </div>
                  <span className="text-xs text-slate-300">{agent.name}</span>
                </div>
              )}

              <div className="flex gap-2">
                <button
                  onClick={() => toggleActive(ch)}
                  className={`flex-1 btn-secondary text-xs justify-center ${ch.is_active ? 'text-amber-400' : 'text-emerald-400'}`}
                >
                  {ch.is_active ? 'Disable' : 'Enable'}
                </button>
                <button onClick={() => handleDelete(ch.id)} className="btn-danger text-xs">
                  <Trash2 size={12} />
                </button>
              </div>
            </div>
          )
        })}
        {channels.length === 0 && (
          <div className="col-span-full card p-12 flex flex-col items-center text-center">
            <MessageSquare size={40} className="text-slate-600 mb-3" />
            <p className="text-slate-400 font-medium">No channels configured</p>
            <p className="text-sm text-slate-600 mt-1">Connect a Telegram bot to chat with your agents</p>
            <button onClick={() => setShowForm(true)} className="btn-primary mt-4">
              <Plus size={14} /> Connect Channel
            </button>
          </div>
        )}
      </div>

      {/* Info box */}
      <div className="card p-4 border-indigo-500/20 bg-indigo-500/5">
        <h3 className="text-sm font-medium text-indigo-300 mb-2">📱 How to connect Telegram</h3>
        <ol className="text-xs text-slate-400 space-y-1 list-decimal list-inside">
          <li>Open Telegram and search for <code className="text-indigo-300">@BotFather</code></li>
          <li>Send <code className="text-indigo-300">/newbot</code> and follow the instructions</li>
          <li>Copy the bot token (format: <code className="text-indigo-300">123456:ABC-DEF...</code>)</li>
          <li>Create an agent above, then connect it here with the token</li>
          <li>Start chatting with your bot on Telegram!</li>
        </ol>
      </div>

      {/* Form modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="card w-full max-w-lg">
            <div className="px-5 py-4 border-b border-slate-700/50 flex items-center justify-between">
              <h2 className="font-semibold text-white">Connect Channel</h2>
              <button onClick={() => setShowForm(false)} className="text-slate-400 hover:text-white"><X size={18} /></button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="label">Channel Type</label>
                <div className="flex gap-2">
                  {CHANNEL_TYPES.map((t) => (
                    <button
                      key={t.value}
                      onClick={() => setForm((f) => ({ ...f, channel_type: t.value }))}
                      className={`flex-1 py-2 px-3 rounded-lg border text-xs font-medium transition-all ${
                        form.channel_type === t.value
                          ? 'border-indigo-500 bg-indigo-500/10 text-indigo-300'
                          : 'border-slate-600 text-slate-400 hover:border-slate-500'
                      }`}
                    >
                      {t.icon} {t.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="label">Assign to Agent *</label>
                <select
                  className="input"
                  value={form.agent_id}
                  onChange={(e) => setForm((f) => ({ ...f, agent_id: e.target.value }))}
                >
                  <option value="">Select agent…</option>
                  {agents.map((a) => (
                    <option key={a.id} value={a.id}>{a.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="label">Channel Name</label>
                <input
                  className="input"
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  placeholder="My Telegram Bot"
                />
              </div>

              {form.channel_type === 'telegram' && (
                <div>
                  <label className="label">Bot Token</label>
                  <input
                    className="input font-mono text-xs"
                    type="password"
                    value={botToken}
                    onChange={(e) => setBotToken(e.target.value)}
                    placeholder="123456789:ABCDefgh..."
                  />
                  <p className="text-xs text-slate-500 mt-1">Get this from @BotFather on Telegram</p>
                </div>
              )}
            </div>
            <div className="px-5 py-4 border-t border-slate-700/50 flex justify-end gap-2">
              <button onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
              <button onClick={handleSave} disabled={saving || !form.agent_id} className="btn-primary">
                {saving ? 'Connecting…' : 'Connect Channel'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
