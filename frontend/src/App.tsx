import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { DashboardLayout } from './components/layout/DashboardLayout'
import { ErrorBoundary } from './components/ui/ErrorBoundary'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import { ToastProvider } from './context/ToastContext'
import { EvidenceProvider } from './context/EvidenceContext'
import AIAnalyst from './pages/AIAnalyst'
import Auth from './pages/Auth'
import Dashboard from './pages/Dashboard'
import MappingPage from './pages/Mapping'
import Profile from './pages/Profile'
import Reports from './pages/Reports'
import UploadPage from './pages/Upload'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function LoadingScreen() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-novera-ink text-slate-100 font-sans">
      <div className="flex flex-col items-center gap-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-[2px] bg-novera-deep border border-white/20 font-mono text-base font-bold text-novera-green-light">
          N
        </div>
        <div className="flex items-center gap-2">
          <div className="h-3 w-3 animate-spin border-2 border-novera-green/30 border-t-novera-green rounded-full" />
          <p className="text-xs font-mono text-novera-muted tracking-tight">Initializing Novera Ledger...</p>
        </div>
      </div>
    </div>
  )
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <LoadingScreen />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function AppRoutes() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <LoadingScreen />
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
      <ThemeProvider>
        <ToastProvider>
          <AuthProvider>
            <EvidenceProvider>
              <BrowserRouter>
                <AppRoutes />
              </BrowserRouter>
            </EvidenceProvider>
          </AuthProvider>
        </ToastProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App
