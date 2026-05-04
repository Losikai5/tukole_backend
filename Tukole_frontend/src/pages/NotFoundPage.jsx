import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function NotFoundPage() {
  const { isAuthenticated } = useAuth()

  return (
    <section className="page-state">
      <div className="state-badge">404</div>
      <h1>Page not found.</h1>
      <p>The page you are looking for does not exist or has been moved.</p>
      <div style={{ display: 'flex', gap: '0.85rem', justifyContent: 'center', flexWrap: 'wrap' }}>
        <Link className="button" to="/">
          Go to home
        </Link>
        {isAuthenticated ? (
          <Link className="button button--ghost" to="/workspace">
            Open workspace
          </Link>
        ) : (
          <Link className="button button--ghost" to="/auth">
            Sign in
          </Link>
        )}
      </div>
    </section>
  )
}
