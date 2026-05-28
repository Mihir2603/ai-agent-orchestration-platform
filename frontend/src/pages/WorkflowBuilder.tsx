import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  ReactFlow, Background, Controls, MiniMap,
  addEdge, useNodesState, useEdgesState,
  type Node, type Edge, type Connection,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Plus, Play, Save, ArrowLeft, Trash2, X, ChevronRight } from 'lucide-react'
import { workflowsApi, agentsApi, executionsApi } from '@/api/client'
import type { Agent, Workflow } from '@/types'
import AgentNode from '@/components/AgentNode'
import ExecutionLog from '@/components/ExecutionLog'
import { useWebSocket } from '@/hooks/useWebSocket'
import type { WSEvent } from '@/types'

const nodeTypes = { agentNode: AgentNode }

const defaultEdgeOptions = {
  style: { stroke: '#6366f1', strokeWidth: 2 },
  markerEnd: { type: 'arrowclosed' as const },
}

export default function WorkflowBuilder() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isNew = !id || id === 'new'

  const [workflow, setWorkflow] = useState<Workflow | null>(null)
  const [name, setName] = useState('New Workflow')
  const [description, setDescription] = useState('')
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [showAgentPicker, setShowAgentPicker] = useState(false)
  const [saving, setSaving] = useState(false)
  const [taskInput, setTaskInput] = useState('')
  const [runPanelOpen, setRunPanelOpen] = useState(false)
  const [running, setRunning] = useState(false)
  const [execId, setExecId] = useState<string | null>(null)
  const [execEvents, setExecEvents] = useState<WSEvent[]>([])

  const handleWsEvent = useCallback((ev: WSEvent) => {
    if (execId && ev.execution_id === execId) {
      setExecEvents((prev) => [...prev, ev])
      if (
        ev.type === 'execution_complete' || ev.type === 'execution_error' ||
        ev.status === 'completed' || ev.status === 'failed'
      ) {
        setRunning(false)
      }
    }
  }, [execId])

  useWebSocket({ channel: execId ? `exec:${execId}` : 'global', onEvent: handleWsEvent })

  useEffect(() => {
    agentsApi.list().then(setAgents).catch(console.error)
    if (!isNew && id) {
      workflowsApi.get(id).then((wf: Workflow) => {
        setWorkflow(wf)
        setName(wf.name)
        setDescription(wf.description)
        const g = wf.graph
        setNodes((g.nodes || []).map((n) => ({ ...n })) as Node[])
        setEdges((g.edges || []).map((e) => ({ ...e })) as Edge[])
      }).catch(console.error)
    }
  }, [id])

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  )

  function addAgentNode(agent: Agent) {
    const newNode: Node = {
      id: `node-${Date.now()}`,
      type: 'agentNode',
      position: { x: 150 + nodes.length * 220, y: 200 },
      data: {
        agentId: agent.id,
        label: agent.name,
        role: agent.role,
        description: agent.description,
        color: agent.avatar_color,
      },
    }
    setNodes((nds) => [...nds, newNode])
    setShowAgentPicker(false)
  }

  async function handleSave() {
    setSaving(true)
    const graph = {
      nodes: nodes.map((n) => ({ id: n.id, type: n.type, position: n.position, data: n.data })),
      edges: edges.map((e) => ({ id: e.id, source: e.source, target: e.target, data: (e as Edge & { data?: unknown }).data || {} })),
      entryNode: nodes[0]?.id || '',
    }
    try {
      if (isNew) {
        const wf = await workflowsApi.create({ name, description, graph })
        navigate(`/workflows/${wf.id}`, { replace: true })
      } else {
        await workflowsApi.update(id!, { name, description, graph })
      }
    } finally {
      setSaving(false)
    }
  }

  async function handleRun() {
    if (!taskInput.trim() || !id || isNew) return
    setRunning(true)
    setExecEvents([])
    setRunPanelOpen(true)
    try {
      const exec = await workflowsApi.execute(id, taskInput)
      setExecId(exec.id)
    } catch (e) {
      setRunning(false)
      console.error(e)
    }
  }

  return (
    <div className="flex h-full">
      {/* Left panel */}
      <div className="w-64 flex-shrink-0 bg-surface-900 border-r border-slate-700/50 flex flex-col">
        <div className="p-4 border-b border-slate-700/50">
          <Link to="/workflows" className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white mb-3">
            <ArrowLeft size={12} /> All Workflows
          </Link>
          <input
            className="input text-sm font-medium"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Workflow name"
          />
          <textarea
            className="input mt-2 text-xs resize-none" rows={2}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description…"
          />
        </div>

        {/* Add node */}
        <div className="p-3 border-b border-slate-700/50">
          <button onClick={() => setShowAgentPicker(true)} className="btn-secondary w-full text-xs">
            <Plus size={12} /> Add Agent Node
          </button>
        </div>

        {/* Node list */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
          <p className="text-xs text-slate-500 font-medium mb-2">Nodes ({nodes.length})</p>
          {nodes.map((n) => (
            <div key={n.id} className="flex items-center justify-between bg-surface-800 rounded-lg px-3 py-2">
              <div className="min-w-0">
                <p className="text-xs font-medium text-white truncate">{String(n.data.label ?? '')}</p>
                <p className="text-[10px] text-slate-500 truncate">{String(n.data.role ?? '')}</p>
              </div>
              <button
                onClick={() => setNodes((nds) => nds.filter((nn) => nn.id !== n.id))}
                className="text-slate-500 hover:text-red-400 ml-2"
              >
                <Trash2 size={11} />
              </button>
            </div>
          ))}
          {nodes.length === 0 && (
            <p className="text-xs text-slate-600 text-center py-4">No nodes yet</p>
          )}
        </div>

        {/* Actions */}
        <div className="p-3 border-t border-slate-700/50 space-y-2">
          <button onClick={handleSave} disabled={saving} className="btn-primary w-full text-xs">
            <Save size={12} /> {saving ? 'Saving…' : 'Save Workflow'}
          </button>
          {!isNew && (
            <button onClick={() => setRunPanelOpen(true)} className="btn-secondary w-full text-xs">
              <Play size={12} /> Run Workflow
            </button>
          )}
        </div>
      </div>

      {/* Canvas */}
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          defaultEdgeOptions={defaultEdgeOptions}
          fitView
          className="bg-surface-950"
        >
          <Background color="#1e293b" gap={20} />
          <Controls />
          <MiniMap nodeColor={(n) => String(n.data?.color ?? '#6366f1')} />
        </ReactFlow>

        {nodes.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="text-center">
              <p className="text-slate-600 text-sm">Add agent nodes from the left panel</p>
              <p className="text-slate-700 text-xs mt-1">Then connect them by dragging between handles</p>
            </div>
          </div>
        )}
      </div>

      {/* Agent picker modal */}
      {showAgentPicker && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="card w-full max-w-md">
            <div className="px-4 py-3 border-b border-slate-700/50 flex items-center justify-between">
              <h3 className="font-medium text-white text-sm">Select Agent</h3>
              <button onClick={() => setShowAgentPicker(false)} className="text-slate-400 hover:text-white"><X size={16} /></button>
            </div>
            <div className="p-2 max-h-80 overflow-y-auto">
              {agents.map((a) => (
                <button
                  key={a.id}
                  onClick={() => addAgentNode(a)}
                  className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-slate-700/50 transition-colors text-left"
                >
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${a.avatar_color}22` }}>
                    <span className="text-sm font-bold" style={{ color: a.avatar_color }}>{a.name[0]}</span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white">{a.name}</p>
                    <p className="text-xs text-slate-400">{a.role || a.model}</p>
                  </div>
                  <ChevronRight size={14} className="ml-auto text-slate-500" />
                </button>
              ))}
              {agents.length === 0 && (
                <p className="text-sm text-slate-500 text-center py-6">
                  No agents yet. <Link to="/agents" className="text-indigo-400">Create one first</Link>
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Run Panel */}
      {runPanelOpen && (
        <div className="w-96 flex-shrink-0 bg-surface-900 border-l border-slate-700/50 flex flex-col">
          <div className="px-4 py-3 border-b border-slate-700/50 flex items-center justify-between">
            <h3 className="font-semibold text-white text-sm">Run Workflow</h3>
            <button onClick={() => setRunPanelOpen(false)} className="text-slate-400 hover:text-white"><X size={16} /></button>
          </div>
          <div className="p-4 border-b border-slate-700/50">
            <label className="label">Task / Input</label>
            <textarea
              className="input resize-none" rows={4}
              value={taskInput}
              onChange={(e) => setTaskInput(e.target.value)}
              placeholder="Describe the task for the agents…"
            />
            <button
              onClick={handleRun}
              disabled={running || !taskInput.trim()}
              className="btn-primary w-full mt-3"
            >
              <Play size={14} />
              {running ? 'Running…' : 'Execute'}
            </button>
          </div>
          <div className="flex-1 overflow-y-auto">
            <ExecutionLog events={execEvents} />
          </div>
        </div>
      )}
    </div>
  )
}
