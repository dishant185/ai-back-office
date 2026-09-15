import './Auth.css'

import {
  ArrowRight,
  Building,
  Eye,
  EyeOff,
  Lock,
  Mail,
  Sparkles,
  User,
  Zap,
  Shield,
  Database,
  ChevronRight,
  Activity,
  Layers,
} from 'lucide-react'
import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

type Mode = 'login' | 'register'

export default function Auth() {
  const { login, register } = useAuth()
  const [mode, setMode] = useState<Mode>('login')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  // Form fields
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [department, setDepartment] = useState('')
  const [organization, setOrganization] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      if (mode === 'login') {
        await login(email, password)
      } else {
        await register({
          email,
          password,
          name,
          department: department || undefined,
          organization: organization || undefined,
        })
      }
    } catch (err: any) {
      const message =
        err.response?.data?.detail ||
        err.message ||
        'Something went wrong. Please try again.'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const toggleMode = () => {
    setMode(mode === 'login' ? 'register' : 'login')
    setError('')
  }

  return (
    <div className="auth-page">
      {/* Animated background */}
      <div className="auth-bg">
        <div className="auth-bg-orb auth-bg-orb--1" />
        <div className="auth-bg-orb auth-bg-orb--2" />
        <div className="auth-bg-orb auth-bg-orb--3" />
        <div className="auth-bg-grid" />
      </div>

      <div className="auth-container">
        {/* Left panel — Branding */}
        <div className="auth-branding">
          <div className="auth-branding-content">
            <div className="auth-logo-row">
              <div className="auth-logo-icon">
                <Zap className="h-7 w-7 text-white" />
              </div>
              <div>
                <h1 className="auth-logo-title">Back-Office</h1>
                <p className="auth-logo-subtitle">AI COPILOT</p>
              </div>
            </div>

            <h2 className="auth-hero-title">
              Intelligent Data
              <br />
              <span className="auth-hero-accent">Operations Hub</span>
            </h2>

            <p className="auth-hero-desc">
              Transform raw data into actionable intelligence with AI-powered analytics,
              automated column mapping, and comprehensive reporting — all secured per user.
            </p>

            <div className="auth-features">
              {[
                { icon: Database, label: 'Smart Dataset Ingestion', desc: 'CSV & Excel auto-profiling' },
                { icon: Layers, label: 'AI Column Mapping', desc: 'Intelligent field standardization' },
                { icon: Activity, label: 'Analytics Reports', desc: 'One-click deep insights' },
                { icon: Shield, label: 'User-Isolated Data', desc: 'Enterprise-grade security' },
              ].map(({ icon: Icon, label, desc }) => (
                <div key={label} className="auth-feature-card">
                  <div className="auth-feature-icon">
                    <Icon className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="auth-feature-label">{label}</p>
                    <p className="auth-feature-desc">{desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Floating decorative elements */}
          <div className="auth-deco-ring auth-deco-ring--1" />
          <div className="auth-deco-ring auth-deco-ring--2" />
        </div>

        {/* Right panel — Form */}
        <div className="auth-form-panel">
          <div className="auth-form-wrapper">
            <div className="auth-form-header">
              <div className="auth-form-badge">
                <Sparkles className="h-3.5 w-3.5" />
                <span>Enterprise Platform</span>
              </div>

              <h2 className="auth-form-title">
                {mode === 'login' ? 'Welcome back' : 'Create your account'}
              </h2>
              <p className="auth-form-subtitle">
                {mode === 'login'
                  ? 'Sign in to access your datasets and analytics'
                  : 'Start transforming your data operations today'}
              </p>
            </div>

            {error && (
              <div className="auth-error">
                <p>{error}</p>
              </div>
            )}

            <form onSubmit={handleSubmit} className="auth-form">
              {mode === 'register' && (
                <div className="auth-field">
                  <label className="auth-label" htmlFor="auth-name">Full Name</label>
                  <div className="auth-input-wrap">
                    <User className="auth-input-icon" />
                    <input
                      id="auth-name"
                      type="text"
                      className="auth-input"
                      placeholder="Enter your full name"
                      value={name}
                      onChange={e => setName(e.target.value)}
                      required
                      minLength={2}
                    />
                  </div>
                </div>
              )}

              <div className="auth-field">
                <label className="auth-label" htmlFor="auth-email">Email Address</label>
                <div className="auth-input-wrap">
                  <Mail className="auth-input-icon" />
                  <input
                    id="auth-email"
                    type="email"
                    className="auth-input"
                    placeholder="you@company.com"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="auth-field">
                <label className="auth-label" htmlFor="auth-password">Password</label>
                <div className="auth-input-wrap">
                  <Lock className="auth-input-icon" />
                  <input
                    id="auth-password"
                    type={showPassword ? 'text' : 'password'}
                    className="auth-input"
                    placeholder={mode === 'register' ? 'Min 6 characters' : 'Enter your password'}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    required
                    minLength={6}
                  />
                  <button
                    type="button"
                    className="auth-eye-btn"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {mode === 'register' && (
                <div className="auth-field-row">
                  <div className="auth-field">
                    <label className="auth-label" htmlFor="auth-dept">Department</label>
                    <div className="auth-input-wrap">
                      <Building className="auth-input-icon" />
                      <input
                        id="auth-dept"
                        type="text"
                        className="auth-input"
                        placeholder="e.g. Operations"
                        value={department}
                        onChange={e => setDepartment(e.target.value)}
                      />
                    </div>
                  </div>
                  <div className="auth-field">
                    <label className="auth-label" htmlFor="auth-org">Organization</label>
                    <div className="auth-input-wrap">
                      <Building className="auth-input-icon" />
                      <input
                        id="auth-org"
                        type="text"
                        className="auth-input"
                        placeholder="e.g. Acme Corp"
                        value={organization}
                        onChange={e => setOrganization(e.target.value)}
                      />
                    </div>
                  </div>
                </div>
              )}

              <button
                type="submit"
                className="auth-submit"
                disabled={loading}
              >
                {loading ? (
                  <span className="auth-spinner" />
                ) : (
                  <>
                    <span>{mode === 'login' ? 'Sign In' : 'Create Account'}</span>
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </form>

            <div className="auth-divider">
              <span className="auth-divider-line" />
              <span className="auth-divider-text">
                {mode === 'login' ? "Don't have an account?" : 'Already have an account?'}
              </span>
              <span className="auth-divider-line" />
            </div>

            <button type="button" className="auth-toggle" onClick={toggleMode}>
              <span>{mode === 'login' ? 'Create a new account' : 'Sign in instead'}</span>
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
