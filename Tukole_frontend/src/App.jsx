import { Navigate, Route, Routes } from 'react-router-dom'
import AppShell from './components/AppShell'
import { useAuth } from './context/AuthContext'
import AuthPage from './pages/AuthPage'
import DashboardPage from './pages/DashboardPage'
import HomePage from './pages/HomePage'
import NotFoundPage from './pages/NotFoundPage'
import VerifyPage from './pages/VerifyPage'

function ProtectedRoute({ children }) {
  const { authReady, isAuthenticated } = useAuth()

  if (!authReady) {
    return (
      <AppShell>
        <section className="page-state">
          <div className="state-badge">Preparing</div>
          <h1>Your Tukole workspace is loading.</h1>
          <p>We are checking your session and getting your tools ready.</p>
        </section>
      </AppShell>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />
  }

  return <AppShell>{children}</AppShell>
}

function PublicRoute({ children }) {
  const { authReady, isAuthenticated } = useAuth()

  if (authReady && isAuthenticated) {
    return <Navigate to="/workspace" replace />
  }

  return <AppShell>{children}</AppShell>
}

export default function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <AppShell>
            <HomePage />
          </AppShell>
        }
      />
      <Route
        path="/auth"
        element={
          <PublicRoute>
            <AuthPage />
          </PublicRoute>
        }
      />
      <Route
        path="/verify/:token"
        element={
          <AppShell>
            <VerifyPage />
          </AppShell>
        }
      />
      <Route
        path="/workspace"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="*"
        element={
          <AppShell>
            <NotFoundPage />
          </AppShell>
        }
      />
    </Routes>
  )
}
