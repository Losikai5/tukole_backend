import { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../api/client'

const ACCESS_TOKEN_KEY = 'tukole.access_token'
const REFRESH_TOKEN_KEY = 'tukole.refresh_token'
const USER_KEY = 'tukole.user'

const AuthContext = createContext(null)

function readStoredUser() {
  const rawUser = localStorage.getItem(USER_KEY)

  if (!rawUser) {
    return null
  }

  try {
    return JSON.parse(rawUser)
  } catch {
    localStorage.removeItem(USER_KEY)
    return null
  }
}

export function AuthProvider({ children }) {
  const [accessToken, setAccessToken] = useState(localStorage.getItem(ACCESS_TOKEN_KEY))
  const [refreshToken, setRefreshToken] = useState(localStorage.getItem(REFRESH_TOKEN_KEY))
  const [user, setUser] = useState(readStoredUser())
  const [authReady, setAuthReady] = useState(false)

  function persistSession(nextAccessToken, nextRefreshToken, nextUser = user) {
    if (nextAccessToken) {
      localStorage.setItem(ACCESS_TOKEN_KEY, nextAccessToken)
    } else {
      localStorage.removeItem(ACCESS_TOKEN_KEY)
    }

    if (nextRefreshToken) {
      localStorage.setItem(REFRESH_TOKEN_KEY, nextRefreshToken)
    } else {
      localStorage.removeItem(REFRESH_TOKEN_KEY)
    }

    if (nextUser) {
      localStorage.setItem(USER_KEY, JSON.stringify(nextUser))
    } else {
      localStorage.removeItem(USER_KEY)
    }

    setAccessToken(nextAccessToken || null)
    setRefreshToken(nextRefreshToken || null)
    setUser(nextUser || null)
  }

  function clearSession() {
    persistSession(null, null, null)
  }

  async function restoreSession() {
    if (!accessToken) {
      setAuthReady(true)
      return
    }

    try {
      const profile = await api.getMe(accessToken)
      persistSession(accessToken, refreshToken, profile.user)
    } catch (error) {
      if (error.status === 401 && refreshToken) {
        try {
          const refreshed = await api.refreshToken(refreshToken)
          const profile = await api.getMe(refreshed.access_token)
          persistSession(refreshed.access_token, refreshToken, profile.user)
        } catch {
          clearSession()
        }
      } else {
        clearSession()
      }
    } finally {
      setAuthReady(true)
    }
  }

  useEffect(() => {
    restoreSession()
  }, [])

  async function authorizedRequest(callback) {
    if (!accessToken) {
      const error = new Error('Please log in to continue.')
      error.status = 401
      throw error
    }

    try {
      return await callback(accessToken)
    } catch (error) {
      if (error.status !== 401 || !refreshToken) {
        throw error
      }

      const refreshed = await api.refreshToken(refreshToken)
      persistSession(refreshed.access_token, refreshToken, user)
      return callback(refreshed.access_token)
    }
  }

  async function login(credentials) {
    const response = await api.login(credentials)
    persistSession(response.access_token, response.refresh_token, response.user)
    return response
  }

  async function register(payload) {
    return api.register(payload)
  }

  async function refreshProfile() {
    const profile = await authorizedRequest((token) => api.getMe(token))
    localStorage.setItem(USER_KEY, JSON.stringify(profile.user))
    setUser(profile.user)
    return profile.user
  }

  async function logout() {
    try {
      if (accessToken) {
        await api.logout(accessToken)
      }
    } catch {
      // Local cleanup still matters even if the API call fails.
    } finally {
      clearSession()
    }
  }

  const value = {
    accessToken,
    refreshToken,
    user,
    authReady,
    isAuthenticated: Boolean(accessToken && user),
    authorizedRequest,
    login,
    logout,
    refreshProfile,
    register,
    setUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const value = useContext(AuthContext)

  if (!value) {
    throw new Error('useAuth must be used within AuthProvider')
  }

  return value
}
