import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from '@/components/Layout'
import Dashboard from '@/pages/Dashboard'
import Agents from '@/pages/Agents'
import Workflows from '@/pages/Workflows'
import WorkflowBuilder from '@/pages/WorkflowBuilder'
import Monitor from '@/pages/Monitor'
import Channels from '@/pages/Channels'

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/workflows" element={<Workflows />} />
          <Route path="/workflows/:id" element={<WorkflowBuilder />} />
          <Route path="/monitor" element={<Monitor />} />
          <Route path="/channels" element={<Channels />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
