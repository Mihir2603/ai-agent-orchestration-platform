// ─── Agent ────────────────────────────────────────────────────────────────────
export interface Agent {
  id: string
  name: string
  role: string
  description: string
  system_prompt: string
  model: string
  temperature: number
  max_tokens: number
  tools: string[]
  memory_enabled: boolean
  memory_window: number
  guardrails: Record<string, unknown>
  schedule_enabled: boolean
  schedule_cron: string
  schedule_task: string
  avatar_color: string
  created_at: string | null
  updated_at: string | null
}

export interface AgentCreate extends Omit<Agent, 'id' | 'created_at' | 'updated_at'> {}

// ─── Workflow ─────────────────────────────────────────────────────────────────
export interface WorkflowGraph {
  nodes: FlowNode[]
  edges: FlowEdge[]
  entryNode: string
  viewport?: { x: number; y: number; zoom: number }
}

export interface FlowNode {
  id: string
  type?: string
  position: { x: number; y: number }
  data: {
    agentId: string
    label: string
    role?: string
    description?: string
    color?: string
    templateRole?: string
  }
}

export interface FlowEdge {
  id: string
  source: string
  target: string
  data?: {
    condition?: string
    label?: string
  }
}

export interface Workflow {
  id: string
  name: string
  description: string
  is_template: boolean
  template_type: string
  graph: WorkflowGraph
  max_iterations: number
  timeout_seconds: number
  created_at: string | null
  updated_at: string | null
}

// ─── Execution ────────────────────────────────────────────────────────────────
export type ExecutionStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

export interface Execution {
  id: string
  workflow_id: string
  status: ExecutionStatus
  task_input: string
  result: string
  error: string
  total_tokens: number
  channel_source: string
  channel_user_id: string
  started_at: string | null
  completed_at: string | null
  created_at: string | null
}

export interface Message {
  id: string
  execution_id: string | null
  agent_id: string | null
  role: 'user' | 'assistant' | 'tool' | 'system'
  content: string
  tool_name: string
  tokens_used: number
  meta: Record<string, unknown>
  created_at: string | null
}

// ─── Channel ──────────────────────────────────────────────────────────────────
export interface Channel {
  id: string
  agent_id: string
  channel_type: string
  name: string
  is_active: boolean
  config: Record<string, string>
  created_at: string | null
  updated_at: string | null
}

// ─── WebSocket Events ─────────────────────────────────────────────────────────
export interface WSEvent {
  type: string
  execution_id?: string
  node_id?: string
  agent_id?: string
  agent_name?: string
  content?: string
  tool?: string
  result?: string
  error?: string
  status?: string
  output?: string
  timestamp?: string
  iteration?: number
}

// ─── Tool ─────────────────────────────────────────────────────────────────────
export interface Tool {
  name: string
  description: string
}
