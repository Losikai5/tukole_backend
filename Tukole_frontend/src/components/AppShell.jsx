import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { StatusPill } from './StatusPill'

const navigation = [
  { to: '/', label: 'Discover' },
  { to: '/workspace', label: 'Workspace' },
]

export default function AppShell({ children }) {
  const navigate = useNavigate()
  const { isAuthenticated, logout, user } = useAuth()

  async function handleLogout() {
    await logout()
    navigate('/')
  }

  return (
    <div className="app-shell">
      <div className="shell-orb shell-orb--sun" />
      <div className="shell-orb shell-orb--sea" />
      <div className="shell-grid" />

      <header className="site-header">
        <Link className="brand" to="/">
          <span className="brand__mark">T</span>
          <span className="brand__copy">
            <strong>Tukole</strong>
            <small>Service marketplace</small>
          </span>
        </Link>

        <nav className="site-nav" aria-label="Primary">
          {navigation.map((item) => (
            <NavLink
              key={item.to}
              className={({ isActive }) =>
                `site-nav__link${isActive ? ' site-nav__link--active' : ''}`
              }
              to={item.to}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="site-header__actions">
          {isAuthenticated ? (
            <>
              <div className="header-user">
                <div>
                  <p>{user.first_name || user.username}</p>
                  <small>{user.email}</small>
                </div>
                <StatusPill status={user.role} />
              </div>
              <button className="button button--ghost" onClick={handleLogout} type="button">
                Log out
              </button>
            </>
          ) : (
            <Link className="button button--ghost" to="/auth">
              Sign in
            </Link>
          )}
        </div>
      </header>

      <main className="site-main">{children}</main>

      <footer className="site-footer">
        <p>Tukole pairs beautiful customer journeys with your FastAPI marketplace backend.</p>
      </footer>
    </div>
  )
}
