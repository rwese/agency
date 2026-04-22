import { Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AppLayout } from './components/layout'
import { useAuthStore } from './stores/authStore'

// Lazy load pages with explicit type assertion
const DashboardPage = React.lazy(() => import('./pages/DashboardPage') as any)
const TasksPage = React.lazy(() => import('./pages/TasksPage') as any)
const TaskDetailPage = React.lazy(() => import('./pages/TaskDetailPage') as any)
const EpicsPage = React.lazy(() => import('./pages/EpicsPage') as any)
const EpicDetailPage = React.lazy(() => import('./pages/EpicDetailPage') as any)
const KanbanPage = React.lazy(() => import('./pages/KanbanPage') as any)
const LoginPage = React.lazy(() => import('./pages/LoginPage') as any)
const RegisterPage = React.lazy(() => import('./pages/RegisterPage') as any)

import React from 'react'

// Loading fallback component
function PageLoader() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
  )
}

// Protected route wrapper - redirects to login if not authenticated
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

// Auth route wrapper - redirects to dashboard if already authenticated (for login/register pages)
function AuthRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  
  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }
  
  return <>{children}</>
}

// Temporary Coming Soon page component
function ComingSoonPage({ title }: { title: string }) {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <h2 className="text-2xl font-semibold text-gray-700">{title}</h2>
        <p className="text-gray-500 mt-2">Coming soon...</p>
      </div>
    </div>
  )
}

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Auth pages - only accessible when not logged in */}
          <Route
            path="/login"
            element={
              <AuthRoute>
                <LoginPage />
              </AuthRoute>
            }
          />
          <Route
            path="/register"
            element={
              <AuthRoute>
                <RegisterPage />
              </AuthRoute>
            }
          />

          {/* Protected routes with layout */}
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<DashboardPage />} />
            <Route path="/tasks" element={<TasksPage />} />
            <Route path="/tasks/:id" element={<TaskDetailPage />} />
            <Route path="/epics" element={<EpicsPage />} />
            <Route path="/epics/:id" element={<EpicDetailPage />} />
            <Route path="/kanban" element={<KanbanPage />} />
            <Route path="/teams" element={<ComingSoonPage title="Teams" />} />
            <Route path="/settings" element={<ComingSoonPage title="Settings" />} />
          </Route>

          {/* Catch all - redirect to dashboard */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </div>
  )
}

export default App
