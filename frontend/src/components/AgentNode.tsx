import { Handle, Position } from '@xyflow/react'
import type { NodeProps, Node } from '@xyflow/react'
import { Bot } from 'lucide-react'

type AgentNodeData = {
  label?: string
  role?: string
  description?: string
  color?: string
  agentId?: string
}

type AgentNodeType = Node<AgentNodeData, 'agentNode'>

export default function AgentNode({ data, selected }: NodeProps<AgentNodeType>) {
  const color = data.color || '#6366f1'

  return (
    <div
      className={`relative bg-surface-800 rounded-xl border-2 shadow-xl min-w-[160px] max-w-[200px] transition-all ${
        selected ? 'border-indigo-400 shadow-indigo-500/20' : 'border-slate-600'
      }`}
      style={{ borderColor: selected ? color : undefined }}
    >
      <Handle type="target" position={Position.Left} className="!w-3 !h-3" />

      {/* Color bar */}
      <div
        className="h-1 rounded-t-xl"
        style={{ background: color }}
      />

      <div className="p-3">
        <div className="flex items-center gap-2 mb-1">
          <div
            className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0"
            style={{ background: `${color}33` }}
          >
            <Bot size={12} style={{ color }} />
          </div>
          <span className="text-xs font-semibold text-white truncate">{data.label}</span>
        </div>
        {data.role && (
          <p className="text-[10px] text-slate-400 truncate">{data.role}</p>
        )}
      </div>

      <Handle type="source" position={Position.Right} className="!w-3 !h-3" />
    </div>
  )
}
