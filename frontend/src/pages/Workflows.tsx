import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Plus, GitBranch, Play, Trash2, Edit3, Layers, Clock } from 'lucide-react'
import { workflowsApi } from '@/api/client'
import type { Workflow } from '@/types'
import { formatDistanceToNow } from 'date-fns'

export default function Workflows() {
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [templates, setTemplates] = useState<Workflow[]>([])
  const navigate = useNavigate()

  const load = () => {
    workflowsApi.list().then((wfs: Workflow[]) => setWorkflows(wfs.filter((w) => !w.is_template))).catch(console.error)
    workflowsApi.templates().then(setTemplates).catch(console.error)
  }

  useEffect(() => { load() }, [])

  async function createFromTemplate(tpl: Workflow) {
    const wf = await workflowsApi.create({
      name: `${tpl.name} (copy)`,
      description: tpl.description,
      graph: tpl.graph,
    })
    navigate(`/workflows/${wf.id}`)
  }

  async function handleDelete(id: string) {
    if (!confirm('Delete this workflow?')) return
    await workflowsApi.delete(id)
    load()
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Workflows</h1>
          <p className="text-sm text-slate-400 mt-1">Build and manage multi-agent pipelines</p>
        </div>
        <Link to="/workflows/new" className="btn-primary">
          <Plus size={14} /> New Workflow
        </Link>
      </div>

      {/* Templates */}
      {templates.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-slate-400 mb-3 flex items-center gap-2">
            <Layers size={14} /> Pre-built Templates
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {templates.map((tpl) => (
              <div key={tpl.id} className="card p-4 border-dashed hover:border-indigo-500/50 transition-colors">
                <div className="flex items-start gap-3 mb-3">
                  <div className="w-9 h-9 bg-indigo-500/10 rounded-xl flex items-center justify-center flex-shrink-0">
                    <Layers size={16} className="text-indigo-400" />
                  </div>
                  <div>
                    <h3 className="font-medium text-white">{tpl.name}</h3>
                    <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">{tpl.description}</p>
                  </div>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-500 mb-3">
                  <span>{tpl.graph.nodes?.length || 0} agents</span>
                  <span>{tpl.graph.edges?.length || 0} connections</span>
                </div>
                <button onClick={() => createFromTemplate(tpl)} className="btn-secondary w-full text-xs">
                  Use Template
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Workflows */}
      <div>
        <h2 className="text-sm font-semibold text-slate-400 mb-3 flex items-center gap-2">
          <GitBranch size={14} /> My Workflows
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {workflows.map((wf) => (
            <div key={wf.id} className="card overflow-hidden group">
              <div className="h-1 bg-gradient-to-r from-indigo-600 to-violet-600" />
              <div className="p-4">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <h3 className="font-semibold text-white truncate">{wf.name}</h3>
                    {wf.description && (
                      <p className="text-xs text-slate-400 mt-0.5 line-clamp-2">{wf.description}</p>
                    )}
                  </div>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                    <Link to={`/workflows/${wf.id}`} className="p-1.5 rounded hover:bg-slate-700 text-slate-400 hover:text-white transition-colors">
                      <Edit3 size={13} />
                    </Link>
                    <button onClick={() => handleDelete(wf.id)} className="p-1.5 rounded hover:bg-red-500/10 text-slate-400 hover:text-red-400 transition-colors">
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>

                <div className="flex items-center gap-3 mt-3 text-xs text-slate-500">
                  <span>{wf.graph.nodes?.length || 0} nodes</span>
                  <span>{wf.graph.edges?.length || 0} edges</span>
                  {wf.updated_at && (
                    <span className="flex items-center gap-1">
                      <Clock size={10} />
                      {formatDistanceToNow(new Date(wf.updated_at), { addSuffix: true })}
                    </span>
                  )}
                </div>

                <div className="flex gap-2 mt-3">
                  <Link to={`/workflows/${wf.id}`} className="btn-secondary flex-1 justify-center text-xs">
                    <Edit3 size={11} /> Edit
                  </Link>
                  <Link to={`/workflows/${wf.id}`} state={{ runNow: true }} className="btn-primary flex-1 justify-center text-xs">
                    <Play size={11} /> Run
                  </Link>
                </div>
              </div>
            </div>
          ))}
          {workflows.length === 0 && (
            <div className="col-span-full card p-12 flex flex-col items-center text-center">
              <GitBranch size={40} className="text-slate-600 mb-3" />
              <p className="text-slate-400 font-medium">No workflows yet</p>
              <p className="text-sm text-slate-600 mt-1">Start from a template or build your own</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
