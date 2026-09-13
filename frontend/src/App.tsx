import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router-dom'

import { DashboardLayout } from './components/layout/DashboardLayout'
import AIAnalyst from './pages/AIAnalyst'
import Dashboard from './pages/Dashboard'
import Reports from './pages/Reports'
import UploadPage from './pages/Upload'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route
            path="/"
            element={
              <DashboardLayout>
                <Dashboard />
              </DashboardLayout>
            }
          />
          <Route
            path="/dashboard"
            element={
              <DashboardLayout>
                <Dashboard />
              </DashboardLayout>
            }
          />
          <Route
            path="/upload"
            element={
              <DashboardLayout>
                <UploadPage />
              </DashboardLayout>
            }
          />
          <Route
            path="/reports"
            element={
              <DashboardLayout>
                <Reports />
              </DashboardLayout>
            }
          />
          <Route
            path="/ai-analyst"
            element={
              <DashboardLayout>
                <AIAnalyst />
              </DashboardLayout>
            }
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
