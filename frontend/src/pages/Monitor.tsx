import { useEffect, useState, useRef } from 'react'
import { executionsApi, workflowsApi } from '@/api/client'
import type { Execution, Message, Workflow } from '@/types'
import { useWebSocket } from '@/hooks/useWebSocket'
import ExecutionLog from '@/components/ExecutionLog'
import { Activity, RefreshCw, Trash2, ChevronRight, MessageSquare } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'

export default function Monitor() {
  const [executions, setExecutions] = useState<Execution[]>([])
  const [workflows, setWorkflows] = useState<Record<string, Workflow>>({})
  const [selected, setSelected] = useState<Execution | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const { connected, events, clearEvents } = useWebSocket()
  const bottomRef = useRef<HTMLDivElement>(null)

  const load = async () => {
    const execs: Execution[] = await executionsApi.list()
    setExecutions(execs)
    // Load workflow names
    const ids = [...new Set(execs.map((e) => e.workflow_id))]
    const wfMap: Record<string, Workflow> = {}
    await Promise.all(
      ids.map(async (id) => {
        try { wfMap[id] = await workflowsApi.get(id) } catch {}
      })
    )
    setWorkflows(wfMap)
  }

  useEffect(() => { load() }, [])

  useEffect(() => {
    // Refresh list when a status event arrives
    const statusEvents = events.filter((e) => e.type === 'execution_status')
    if (statusEvents.length > 0) load()
  }, [events])

  async function selectExecution(ex: Execution) {
    setSelected(ex)
    const msgs: Message[] = await executionsApi.messages(ex.id)
    setMessages(msgs)
  }

  async function deleteExecution(id: string) {
    if (!confirm('Delete this execution?')) return
    await executionsApi.delete(id)
    if (selected?.id === id) setSelected(null)
    load()
  }

  const liveEvents = selected
    ? events.filter((e) => e.execution_id === selected.id)
    : events

  return (
    <div className="flex h-full">
      {/* Execution list */}
      <div className="w-72 flex-shrink-0 bg-surface-900 border-r border-slate-700/50 flex flex-col">
        <div className="px-4 py-3 border-b border-slate-700/50 flex items-center justify-between">
          <h2 className="font-semibold text-white text-sm flex items-center gap-2">
            <Activity size={14} className="text-indigo-400" /> Executions
          </h2>
          <button onClick={load} className="text-slate-400 hover:text-white transition-colors">
            <RefreshCw size={13} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto divide-y divide-slate-700/30">
          {executions.map((ex) => (
            <button
              key={ex.id}
              onClick={() => selectExecution(ex)}
              className={clsx(
                'w-full px-4 py-3 text-left hover:bg-slate-700/30 transition-colors',
                selected?.id === ex.id && 'bg-indigo-600/10 border-r-2 border-indigo-500'
              )}
            >
              <div className="flex items-center justify-between mb-1">
                <span className={clsx('badge', {
                  'badge-green':  ex.status === 'completed',
                  'badge-blue':   ex.status === 'running',
                  'badge-red':    ex.status === 'failed',
                  'badge-yellow': ex.status === 'pending',
                  'badge-gray':   ex.status === 'cancelled',
                })}>{ex.status}</span>
                <button
                  onClick={(e) => { e.stopPropagation(); deleteExecution(ex.id) }}
                  className="text-slate-600 hover:text-red-400 transition-colors"
                >
                  <Trash2 size={11} />
                </button>
              </div>
              <p className="text-xs text-slate-300 truncate">{ex.task_input.slice(0, 50)}</p>
              <p className="text-[10px] text-slate-500 mt-0.5">
                {workflows[ex.workflow_id]?.name || 'Unknown workflow'}
              </p>
              {ex.created_at && (
                <p className="text-[10px] text-slate-600 mt-0.5">
                  {formatDistanceToNow(new Date(ex.created_at), { addSuffix: true })}
                </p>
              )}
            </button>
          ))}
          {executions.length === 0 && (
            <p className="px-4 py-6 text-sm text-slate-500 text-center">No executions yet</p>
          )}
        </div>
      </div>

      {/* Detail panel */}
      {selected ? (
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <div className="px-5 py-3 border-b border-slate-700/50 bg-surface-900 flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-white">{selected.task_input.slice(0, 60)}</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                {workflows[selected.workflow_id]?.name} · {selected.channel_source}
                {selected.total_tokens > 0 && ` · ${selected.total_tokens} tokens`}
              </p>
            </div>
            <span className={clsx('badge', {
              'badge-green':  selected.status === 'completed',
              'badge-blue':   selected.status === 'running',
              'badge-red':    selected.status === 'failed',
              'badge-yellow': selected.status === 'pending',
            })}>{selected.status}</span>
          </div>

          <div className="flex-1 flex overflow-hidden">
            {/* Live events */}
            <div className="flex-1 overflow-y-auto">
              <div className="px-4 py-3 border-b border-slate-700/30 flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">Live Event Stream</span>
                <div className="flex items-center gap-1.5 text-xs text-emerald-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  {connected ? 'Live' : 'Offline'}
                </div>
              </div>
              <ExecutionLog events={liveEvents} />
            </div>

            {/* Messages */}
            <div className="w-80 border-l border-slate-700/50 flex flex-col">
              <div className="px-4 py-3 border-b border-slate-700/30 flex items-center gap-2">
                <MessageSquare size={13} className="text-slate-400" />
                <span className="text-xs font-medium text-slate-400">Persisted Messages</span>
              </div>
              <div className="flex-1 overflow-y-auto p-3 space-y-2">
                {messages.map((m) => (
                  <div key={m.id} className={clsx(
                    'rounded-lg p-2.5 text-xs',
                    m.role === 'user' ? 'bg-blue-500/10 border border-blue-500/20' :
                    m.role === 'tool' ? 'bg-amber-500/10 border border-amber-500/20' :
                    'bg-surface-800 border border-slate-700/50'
                  )}>
                    <div className="flex items-center gap-1.5 mb-1">
                      <span className="font-medium text-slate-300">{m.role}</span>
                      {m.tool_name && <span className="text-amber-400">({m.tool_name})</span>}
                    </div>
                    <p className="text-slate-400 line-clamp-4">{m.content}</p>
                  </div>
                ))}
                {messages.length === 0 && (
                  <p className="text-xs text-slate-600 text-center py-4">No messages persisted</p>
                )}
              </div>
            </div>
          </div>

          {/* Result */}
          {selected.result && (
            <div className="border-t border-slate-700/50 p-4 bg-emerald-500/5">
              <p className="text-xs font-medium text-emerald-400 mb-1">Final Result</p>
              <p className="text-sm text-slate-300 whitespace-pre-wrap">{selected.result.slice(0, 1000)}</p>
            </div>
          )}
          {selected.error && (
            <div className="border-t border-slate-700/50 p-4 bg-red-500/5">
              <p className="text-xs font-medium text-red-400 mb-1">Error</p>
              <p className="text-sm text-red-300 font-mono">{selected.error}</p>
            </div>
          )}
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Activity size={48} className="text-slate-700 mx-auto mb-3" />
            <p className="text-slate-500">Select an execution to view details</p>
          </div>
        </div>
      )}
    </div>
  )
}
