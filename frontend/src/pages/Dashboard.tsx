import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bot, GitBranch, Activity, TrendingUp, Plus, ArrowRight, Zap } from 'lucide-react'
import { agentsApi, workflowsApi, executionsApi } from '@/api/client'
import type { Agent, Workflow, Execution } from '@/types'
import { useWebSocket } from '@/hooks/useWebSocket'
import ExecutionLog from '@/components/ExecutionLog'

export default function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [executions, setExecutions] = useState<Execution[]>([])
  const { events } = useWebSocket()

  useEffect(() => {
    agentsApi.list().then(setAgents).catch(console.error)
    workflowsApi.list().then(setWorkflows).catch(console.error)
    executionsApi.list().then(setExecutions).catch(console.error)
  }, [])

  const running = executions.filter((e) => e.status === 'running').length
  const completed = executions.filter((e) => e.status === 'completed').length
  const failed = executions.filter((e) => e.status === 'failed').length

  const stats = [
    { label: 'Agents', value: agents.length, icon: Bot, color: 'text-indigo-400', bg: 'bg-indigo-500/10', href: '/agents' },
    { label: 'Workflows', value: workflows.length, icon: GitBranch, color: 'text-violet-400', bg: 'bg-violet-500/10', href: '/workflows' },
    { label: 'Running', value: running, icon: Activity, color: 'text-emerald-400', bg: 'bg-emerald-500/10', href: '/monitor' },
    { label: 'Total Executions', value: executions.length, icon: TrendingUp, color: 'text-blue-400', bg: 'bg-blue-500/10', href: '/monitor' },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-sm text-slate-400 mt-1">Overview of your AI agent platform</p>
        </div>
        <div className="flex gap-2">
          <Link to="/agents" className="btn-secondary">
            <Plus size={14} /> New Agent
          </Link>
          <Link to="/workflows" className="btn-primary">
            <Zap size={14} /> New Workflow
          </Link>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map(({ label, value, icon: Icon, color, bg, href }) => (
          <Link key={label} to={href} className="card p-4 hover:border-slate-600 transition-colors group">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-slate-500 font-medium">{label}</p>
                <p className="text-3xl font-bold text-white mt-1">{value}</p>
              </div>
              <div className={`${bg} p-2 rounded-lg`}>
                <Icon size={20} className={color} />
              </div>
            </div>
            <div className="flex items-center gap-1 mt-3 text-xs text-slate-500 group-hover:text-slate-400 transition-colors">
              View all <ArrowRight size={10} />
            </div>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Executions */}
        <div className="card">
          <div className="px-4 py-3 border-b border-slate-700/50 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white">Recent Executions</h2>
            <Link to="/monitor" className="text-xs text-indigo-400 hover:text-indigo-300">View all →</Link>
          </div>
          <div className="divide-y divide-slate-700/30">
            {executions.slice(0, 5).map((ex) => (
              <div key={ex.id} className="px-4 py-3 flex items-center justify-between">
                <div className="min-w-0">
                  <p className="text-sm text-slate-200 truncate">{ex.task_input.slice(0, 50)}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{ex.channel_source}</p>
                </div>
                <span className={`badge ml-3 ${
                  ex.status === 'completed' ? 'badge-green' :
                  ex.status === 'running'   ? 'badge-blue' :
                  ex.status === 'failed'    ? 'badge-red' : 'badge-gray'
                }`}>{ex.status}</span>
              </div>
            ))}
            {executions.length === 0 && (
              <p className="px-4 py-6 text-sm text-slate-500 text-center">No executions yet</p>
            )}
          </div>
        </div>

        {/* Live Event Feed */}
        <div className="card flex flex-col">
          <div className="px-4 py-3 border-b border-slate-700/50 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white">Live Events</h2>
            <span className="flex items-center gap-1.5 text-xs text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Live
            </span>
          </div>
          <div className="flex-1 overflow-y-auto max-h-64">
            <ExecutionLog events={events.slice(-20).reverse()} />
          </div>
        </div>
      </div>

      {/* Quick Start */}
      <div className="card p-5">
        <h2 className="text-sm font-semibold text-white mb-3">Quick Start</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <Link to="/agents" className="flex items-start gap-3 p-3 rounded-lg bg-surface-900 hover:bg-slate-700/50 transition-colors">
            <Bot size={18} className="text-indigo-400 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-white">Create Agent</p>
              <p className="text-xs text-slate-400 mt-0.5">Configure a new AI agent with tools and personality</p>
            </div>
          </Link>
          <Link to="/workflows" className="flex items-start gap-3 p-3 rounded-lg bg-surface-900 hover:bg-slate-700/50 transition-colors">
            <GitBranch size={18} className="text-violet-400 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-white">Build Workflow</p>
              <p className="text-xs text-slate-400 mt-0.5">Connect agents into a collaborative pipeline</p>
            </div>
          </Link>
          <Link to="/channels" className="flex items-start gap-3 p-3 rounded-lg bg-surface-900 hover:bg-slate-700/50 transition-colors">
            <Activity size={18} className="text-emerald-400 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-white">Connect Telegram</p>
              <p className="text-xs text-slate-400 mt-0.5">Link an agent to a Telegram bot for live chat</p>
            </div>
          </Link>
        </div>
      </div>
    </div>
  )
}
