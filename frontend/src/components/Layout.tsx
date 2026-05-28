import { NavLink, Link } from 'react-router-dom'
import {
  Bot, GitBranch, Activity, MessageSquare, LayoutDashboard,
  Zap, Circle
} from 'lucide-react'
import clsx from 'clsx'
import { useWebSocket } from '@/hooks/useWebSocket'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/agents', icon: Bot, label: 'Agents' },
  { to: '/workflows', icon: GitBranch, label: 'Workflows' },
  { to: '/monitor', icon: Activity, label: 'Monitor' },
  { to: '/channels', icon: MessageSquare, label: 'Channels' },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  const { connected } = useWebSocket()

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 flex-shrink-0 bg-surface-900 border-r border-slate-700/50 flex flex-col">
        {/* Logo */}
        <div className="px-4 py-5 flex items-center gap-2.5 border-b border-slate-700/50">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
            <Zap size={16} className="text-white" />
          </div>
          <div>
            <p className="text-sm font-semibold text-white leading-none">AgentForge</p>
            <p className="text-xs text-slate-500 mt-0.5">Orchestration Platform</p>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-2 py-4 space-y-0.5">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-700/50'
                )
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-slate-700/50">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Circle
              size={6}
              className={connected ? 'fill-emerald-400 text-emerald-400' : 'fill-red-400 text-red-400'}
            />
            {connected ? 'Live' : 'Disconnected'}
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">{children}</main>
    </div>
  )
}
