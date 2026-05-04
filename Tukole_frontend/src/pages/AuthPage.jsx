import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const initialLoginForm = {
  email: '',
  password: '',
}

const initialRegisterForm = {
  username: '',
  first_name: '',
  last_name: '',
  role: 'user',
  email: '',
  password: '',
}

export default function AuthPage() {
  const navigate = useNavigate()
  const { isAuthenticated, login, register } = useAuth()
  const [mode, setMode] = useState('login')
  const [loginForm, setLoginForm] = useState(initialLoginForm)
  const [registerForm, setRegisterForm] = useState(initialRegisterForm)
  const [busy, setBusy] = useState(false)
  const [feedback, setFeedback] = useState(null)

  if (isAuthenticated) {
    return <Navigate to="/workspace" replace />
  }

  async function handleLogin(event) {
    event.preventDefault()
    setBusy(true)
    setFeedback(null)

    try {
      await login(loginForm)
      navigate('/workspace')
    } catch (error) {
      setFeedback({ tone: 'error', message: error.message })
    } finally {
      setBusy(false)
    }
  }

  async function handleRegister(event) {
    event.preventDefault()
    setBusy(true)
    setFeedback(null)

    try {
      await register(registerForm)
      setFeedback({
        tone: 'success',
        message: 'Account created. Check your email for verification before signing in.',
      })
      setMode('login')
      setLoginForm((current) => ({ ...current, email: registerForm.email }))
      setRegisterForm(initialRegisterForm)
    } catch (error) {
      setFeedback({ tone: 'error', message: error.message })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-shell">
      <section className="panel auth-shell__story">
        <p className="eyebrow">Get started</p>
        <h1>Make Tukole feel premium from the first screen.</h1>
        <p>
          This frontend keeps the entry flow simple: sign in fast, register in one place, and head
          straight into a role-aware workspace after authentication.
        </p>

        <div className="story-grid">
          <article className="story-card">
            <h3>Users</h3>
            <p>Book services, pay accurately, leave reviews, and keep track of notifications.</p>
          </article>
          <article className="story-card">
            <h3>Providers</h3>
            <p>Set up a provider profile and publish offers customers can book immediately.</p>
          </article>
          <article className="story-card">
            <h3>Admins</h3>
            <p>Oversee disputes, user management, platform health, and delivery metrics.</p>
          </article>
        </div>

        <Link className="button button--ghost" to="/">
          Back to landing page
        </Link>
      </section>

      <section className="panel auth-shell__form">
        <div className="auth-switch">
          <button
            className={mode === 'login' ? 'auth-switch__button auth-switch__button--active' : 'auth-switch__button'}
            onClick={() => setMode('login')}
            type="button"
          >
            Login
          </button>
          <button
            className={mode === 'register' ? 'auth-switch__button auth-switch__button--active' : 'auth-switch__button'}
            onClick={() => setMode('register')}
            type="button"
          >
            Register
          </button>
        </div>

        {feedback ? (
          <div className={`feedback feedback--${feedback.tone}`}>{feedback.message}</div>
        ) : null}

        {mode === 'login' ? (
          <form className="form-stack" onSubmit={handleLogin}>
            <label className="field">
              <span>Email</span>
              <input
                onChange={(event) =>
                  setLoginForm((current) => ({ ...current, email: event.target.value }))
                }
                placeholder="you@example.com"
                required
                type="email"
                value={loginForm.email}
              />
            </label>

            <label className="field">
              <span>Password</span>
              <input
                onChange={(event) =>
                  setLoginForm((current) => ({ ...current, password: event.target.value }))
                }
                placeholder="Enter your password"
                required
                type="password"
                value={loginForm.password}
              />
            </label>

            <button className="button button--block" disabled={busy} type="submit">
              {busy ? 'Signing in...' : 'Open workspace'}
            </button>
          </form>
        ) : (
          <form className="form-stack" onSubmit={handleRegister}>
            <div className="form-grid">
              <label className="field">
                <span>Username</span>
                <input
                  onChange={(event) =>
                    setRegisterForm((current) => ({ ...current, username: event.target.value }))
                  }
                  placeholder="tukole_user"
                  required
                  type="text"
                  value={registerForm.username}
                />
              </label>

              <label className="field">
                <span>Role</span>
                <select
                  onChange={(event) =>
                    setRegisterForm((current) => ({ ...current, role: event.target.value }))
                  }
                  value={registerForm.role}
                >
                  <option value="consumer">User</option>
                  <option value="provider">Provider</option>
                </select>
              </label>
            </div>

            <div className="form-grid">
              <label className="field">
                <span>First name</span>
                <input
                  onChange={(event) =>
                    setRegisterForm((current) => ({ ...current, first_name: event.target.value }))
                  }
                  placeholder="Amina"
                  required
                  type="text"
                  value={registerForm.first_name}
                />
              </label>

              <label className="field">
                <span>Last name</span>
                <input
                  onChange={(event) =>
                    setRegisterForm((current) => ({ ...current, last_name: event.target.value }))
                  }
                  placeholder="Nabirye"
                  required
                  type="text"
                  value={registerForm.last_name}
                />
              </label>
            </div>

            <label className="field">
              <span>Email</span>
              <input
                onChange={(event) =>
                  setRegisterForm((current) => ({ ...current, email: event.target.value }))
                }
                placeholder="you@example.com"
                required
                type="email"
                value={registerForm.email}
              />
            </label>

            <label className="field">
              <span>Password</span>
              <input
                minLength={6}
                onChange={(event) =>
                  setRegisterForm((current) => ({ ...current, password: event.target.value }))
                }
                placeholder="Create a strong password"
                required
                type="password"
                value={registerForm.password}
              />
            </label>

            <button className="button button--block" disabled={busy} type="submit">
              {busy ? 'Creating account...' : 'Create Tukole account'}
            </button>
          </form>
        )}
      </section>
    </div>
  )
}
