import clsx from 'clsx'
import { formatDistanceToNow } from 'date-fns'
import type { WSEvent } from '@/types'
import { Bot, Wrench, CheckCircle2, XCircle, Play, Loader2 } from 'lucide-react'

interface Props {
  events: WSEvent[]
  className?: string
}

function eventIcon(type: string) {
  if (type === 'agent_start')    return <Play size={12} className="text-indigo-400 mt-0.5 flex-shrink-0" />
  if (type === 'agent_message')  return <Bot size={12} className="text-violet-400 mt-0.5 flex-shrink-0" />
  if (type === 'agent_done')     return <CheckCircle2 size={12} className="text-emerald-400 mt-0.5 flex-shrink-0" />
  if (type === 'tool_result')    return <Wrench size={12} className="text-amber-400 mt-0.5 flex-shrink-0" />
  if (type === 'execution_complete') return <CheckCircle2 size={12} className="text-emerald-400 mt-0.5 flex-shrink-0" />
  if (type === 'execution_error')    return <XCircle size={12} className="text-red-400 mt-0.5 flex-shrink-0" />
  if (type === 'execution_start')    return <Loader2 size={12} className="text-blue-400 mt-0.5 flex-shrink-0 animate-spin" />
  return <div className="w-3 h-3 rounded-full bg-slate-600 mt-0.5 flex-shrink-0" />
}

function eventLabel(ev: WSEvent): string {
  switch (ev.type) {
    case 'execution_start':   return `Execution started — "${(ev as WSEvent & { task?: string }).task?.slice(0, 60) ?? ''}"`
    case 'agent_start':       return `[${ev.agent_name}] Starting (iteration ${ev.iteration})`
    case 'agent_message':     return `[${ev.agent_name}] ${ev.content?.slice(0, 120) || ''}`
    case 'agent_done':        return `[${ev.agent_name}] ✓ Done`
    case 'tool_result':       return `[${ev.agent_name}] Tool: ${ev.tool} → ${ev.result?.slice(0, 80)}`
    case 'execution_complete':return `Execution complete`
    case 'execution_error':   return `Error: ${ev.error?.slice(0, 120)}`
    case 'execution_status':  return `Status → ${ev.status}`
    default:                  return ev.type
  }
}

export default function ExecutionLog({ events, className }: Props) {
  return (
    <div className={clsx('flex flex-col gap-0.5 font-mono text-xs', className)}>
      {events.length === 0 && (
        <p className="text-slate-500 italic p-4">No events yet…</p>
      )}
      {events.map((ev, i) => (
        <div
          key={i}
          className={clsx(
            'flex items-start gap-2 px-3 py-1.5 rounded hover:bg-slate-800/50',
            ev.type === 'execution_error' ? 'bg-red-500/5' : '',
            ev.type === 'execution_complete' ? 'bg-emerald-500/5' : '',
          )}
        >
          {eventIcon(ev.type)}
          <span
            className={clsx(
              'break-all',
              ev.type === 'execution_error' ? 'text-red-300' : 'text-slate-300',
              ev.type === 'execution_complete' ? 'text-emerald-300' : '',
              ev.type === 'agent_message' ? 'text-slate-200' : '',
            )}
          >
            {eventLabel(ev)}
          </span>
          {ev.timestamp && (
            <span className="ml-auto text-slate-600 whitespace-nowrap text-[10px]">
              {new Date(ev.timestamp).toLocaleTimeString()}
            </span>
          )}
        </div>
      ))}
    </div>
  )
}
