import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import api from '../services/api'

export interface AuthUser {
  id: string
  email: string
  name: string
  title: string
  department: string
  organization: string
  role: string
  location?: string | null
  bio?: string | null
  created_at?: string | null
}

interface AuthState {
  user: AuthUser | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
}

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => void
  updateUser: (user: AuthUser) => void
}

export interface RegisterData {
  email: string
  password: string
  name: string
  department?: string
  organization?: string
  title?: string
}

const TOKEN_KEY = 'ai_backoffice_token'
const USER_KEY = 'ai_backoffice_user'

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: true,
  })

  // Restore session from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem(TOKEN_KEY)
    const savedUser = localStorage.getItem(USER_KEY)

    if (savedToken && savedUser) {
      try {
        const user = JSON.parse(savedUser) as AuthUser
        setState({ user, token: savedToken, isAuthenticated: true, isLoading: false })
      } catch {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
        setState(prev => ({ ...prev, isLoading: false }))
      }
    } else {
      setState(prev => ({ ...prev, isLoading: false }))
    }
  }, [])

  // Set up axios interceptor to attach token
  useEffect(() => {
    const interceptorId = api.interceptors.request.use(config => {
      const token = localStorage.getItem(TOKEN_KEY)
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })

    return () => {
      api.interceptors.request.eject(interceptorId)
    }
  }, [])

  // Handle 401 responses globally
  useEffect(() => {
    const interceptorId = api.interceptors.response.use(
      response => response,
      error => {
        if (error.response?.status === 401 && state.isAuthenticated) {
          logout()
        }
        return Promise.reject(error)
      }
    )

    return () => {
      api.interceptors.response.eject(interceptorId)
    }
  }, [state.isAuthenticated])

  const login = async (email: string, password: string) => {
    const response = await api.post('/api/v1/auth/login', { email, password })
    const { access_token, user } = response.data

    localStorage.setItem(TOKEN_KEY, access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(user))
    setState({ user, token: access_token, isAuthenticated: true, isLoading: false })
  }

  const register = async (data: RegisterData) => {
    const response = await api.post('/api/v1/auth/register', data)
    const { access_token, user } = response.data

    localStorage.setItem(TOKEN_KEY, access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(user))
    setState({ user, token: access_token, isAuthenticated: true, isLoading: false })
  }

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setState({ user: null, token: null, isAuthenticated: false, isLoading: false })
  }

  const updateUser = (user: AuthUser) => {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
    setState(prev => ({ ...prev, user }))
  }

  return (
    <AuthContext.Provider value={{ ...state, login, register, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
