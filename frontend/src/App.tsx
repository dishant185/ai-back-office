import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { DashboardLayout } from './components/layout/DashboardLayout'
import { ErrorBoundary } from './components/ui/ErrorBoundary'
import { AuthProvider, useAuth } from './context/AuthContext'
import AIAnalyst from './pages/AIAnalyst'
import Auth from './pages/Auth'
import Dashboard from './pages/Dashboard'
import MappingPage from './pages/Mapping'
import Profile from './pages/Profile'
import Reports from './pages/Reports'
import UploadPage from './pages/Upload'

const queryClient = new QueryClient()

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center" style={{ background: '#0a0e1a' }}>
        <div className="flex flex-col items-center gap-4">
          <div style={{
            width: 40,
            height: 40,
            border: '3px solid rgba(99, 102, 241, 0.2)',
            borderTopColor: '#6366f1',
            borderRadius: '50%',
            animation: 'authSpin 0.6s linear infinite',
          }} />
          <p style={{ color: '#64748b', fontSize: '0.85rem' }}>Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function AppRoutes() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center" style={{ background: '#0a0e1a' }}>
        <div style={{
          width: 40,
          height: 40,
          border: '3px solid rgba(99, 102, 241, 0.2)',
          borderTopColor: '#6366f1',
          borderRadius: '50%',
          animation: 'authSpin 0.6s linear infinite',
        }} />
      </div>
    )
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={
          isAuthenticated ? <Navigate to="/dashboard" replace /> : <Auth />
        }
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <Dashboard />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <Dashboard />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/upload"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <UploadPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/mapping"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <MappingPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/mapping/:uploadId"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <MappingPage />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/reports"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <ErrorBoundary fallbackTitle="Reports Page Error">
                <Reports />
              </ErrorBoundary>
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/reports/:reportId"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <ErrorBoundary fallbackTitle="Reports Page Error">
                <Reports />
              </ErrorBoundary>
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/ai-analyst"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <AIAnalyst />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <DashboardLayout>
              <Profile />
            </DashboardLayout>
          </ProtectedRoute>
        }
      />
      {/* Catch-all redirect */}
      <Route path="*" element={<Navigate to={isAuthenticated ? '/dashboard' : '/login'} replace />} />
    </Routes>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
