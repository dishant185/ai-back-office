import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { AuthError } from '../components/auth/AuthError'
import { AuthInput } from '../components/auth/AuthInput'
import { AuthShell } from '../components/auth/AuthShell'
import { AuthSubmitButton } from '../components/auth/AuthSubmitButton'
import { PasswordInput } from '../components/auth/PasswordInput'
import { useAuth } from '../context/AuthContext'

export type AuthMode = 'login' | 'register' | 'forgot'

export default function Auth() {
  const { login, register, isAuthenticated } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  // Derive mode directly from current path
  const mode: AuthMode =
    location.pathname === '/register'
      ? 'register'
      : location.pathname === '/forgot-password'
      ? 'forgot'
      : 'login'

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [infoNotice, setInfoNotice] = useState('')

  // Form fields
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [name, setName] = useState('')
  const [organization, setOrganization] = useState('')

  // Update browser document title
  useEffect(() => {
    if (mode === 'login') {
      document.title = 'Novera — Sign in'
    } else if (mode === 'register') {
      document.title = 'Novera — Create workspace'
    } else {
      document.title = 'Novera — Reset password'
    }
  }, [mode])

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true })
    }
  }, [isAuthenticated, navigate])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setInfoNotice('')

    if (mode === 'forgot') {
      // Truthful representation: backend has no self-service reset mailer
      setInfoNotice(
        'Self-service password reset is managed by your workspace administrator. Please request an access token reset from your administrator.'
      )
      return
    }

    if (mode === 'register' && password !== confirmPassword) {
      setError('Passwords do not match. Please re-enter your password.')
      return
    }

    if (mode === 'register' && password.length < 6) {
      setError('Password must be at least 6 characters long.')
      return
    }

    setLoading(true)

    try {
      if (mode === 'login') {
        await login(email, password)
      } else {
        await register({
          email,
          password,
          name,
          organization: organization || undefined,
        })
      }
    } catch (err: any) {
      const message =
        err.response?.data?.detail ||
        err.message ||
        'The email or password could not be verified.'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const switchMode = (newMode: AuthMode) => {
    setError('')
    setInfoNotice('')
    if (newMode === 'login') navigate('/login', { replace: true })
    else if (newMode === 'register') navigate('/register', { replace: true })
    else if (newMode === 'forgot') navigate('/forgot-password', { replace: true })
  }

  return (
    <AuthShell mode={mode}>
      {/* LOGIN MODE */}
      {mode === 'login' && (
        <div className="space-y-6">
          {/* Header */}
          <div className="space-y-1">
            <h2 className="font-sans text-2xl font-bold tracking-tight text-[#11181B] dark:text-[#EEF2EE]">
              Welcome back
            </h2>
            <p className="text-xs text-[#66716C] dark:text-[#AAB5AF]">
              Sign in to your Novera workspace.
            </p>
          </div>

          {/* Error Message */}
          <AuthError message={error} />

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <AuthInput
              label="Email"
              type="email"
              id="login-email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@company.com"
              required
              autoComplete="email"
            />

            <PasswordInput
              label="Password"
              id="login-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••"
              required
              autoComplete="current-password"
              hint={
                <button
                  type="button"
                  onClick={() => switchMode('forgot')}
                  className="text-[11px] font-medium text-[#176B50] hover:text-[#2D8A68] dark:text-[#4FAF87] dark:hover:text-[#5EC498] hover:underline cursor-pointer"
                >
                  Forgot password
                </button>
              }
            />

            <div className="pt-1">
              <AuthSubmitButton
                loading={loading}
                loadingText="Signing in..."
              >
                Sign in
              </AuthSubmitButton>
            </div>
          </form>

          {/* Secondary Action */}
          <div className="pt-4 border-t border-[#C7CEC8] dark:border-[#2B3538] text-center">
            <p className="text-xs text-[#66716C] dark:text-[#AAB5AF]">
              Don&apos;t have a Novera workspace?{' '}
              <button
                type="button"
                onClick={() => switchMode('register')}
                className="font-semibold text-[#176B50] hover:text-[#2D8A68] dark:text-[#4FAF87] dark:hover:text-[#5EC498] hover:underline cursor-pointer ml-1"
              >
                Create workspace
              </button>
            </p>
          </div>
        </div>
      )}

      {/* REGISTER MODE */}
      {mode === 'register' && (
        <div className="space-y-6">
          {/* Header */}
          <div className="space-y-1">
            <h2 className="font-sans text-2xl font-bold tracking-tight text-[#11181B] dark:text-[#EEF2EE]">
              Create your workspace
            </h2>
            <p className="text-xs text-[#66716C] dark:text-[#AAB5AF]">
              Start organizing your business data in one verified workspace.
            </p>
          </div>

          {/* Error Message */}
          <AuthError message={error} />

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-3.5" noValidate>
            <AuthInput
              label="Full name"
              type="text"
              id="register-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Eleanor Vance"
              required
              autoComplete="name"
            />

            <AuthInput
              label="Company / Workspace name"
              type="text"
              id="register-org"
              value={organization}
              onChange={(e) => setOrganization(e.target.value)}
              placeholder="e.g. Acme Enterprises"
              autoComplete="organization"
            />

            <AuthInput
              label="Email"
              type="email"
              id="register-email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@company.com"
              required
              autoComplete="email"
            />

            <PasswordInput
              label="Password"
              id="register-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Minimum 6 characters"
              required
              autoComplete="new-password"
            />

            <PasswordInput
              label="Confirm password"
              id="register-confirm-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Re-enter your password"
              required
              autoComplete="new-password"
            />

            <div className="pt-2">
              <AuthSubmitButton
                loading={loading}
                loadingText="Creating workspace..."
              >
                Create workspace
              </AuthSubmitButton>
            </div>
          </form>

          {/* Secondary Action */}
          <div className="pt-4 border-t border-[#C7CEC8] dark:border-[#2B3538] text-center">
            <p className="text-xs text-[#66716C] dark:text-[#AAB5AF]">
              Already have a workspace?{' '}
              <button
                type="button"
                onClick={() => switchMode('login')}
                className="font-semibold text-[#176B50] hover:text-[#2D8A68] dark:text-[#4FAF87] dark:hover:text-[#5EC498] hover:underline cursor-pointer ml-1"
              >
                Sign in
              </button>
            </p>
          </div>
        </div>
      )}

      {/* FORGOT PASSWORD MODE */}
      {mode === 'forgot' && (
        <div className="space-y-6">
          {/* Header */}
          <div className="space-y-1">
            <h2 className="font-sans text-2xl font-bold tracking-tight text-[#11181B] dark:text-[#EEF2EE]">
              Reset your password
            </h2>
            <p className="text-xs text-[#66716C] dark:text-[#AAB5AF]">
              Enter your account email and we&apos;ll guide you through the password reset process.
            </p>
          </div>

          {/* Info/Notice */}
          {infoNotice && (
            <div className="rounded-[2px] border border-[#A8792E]/30 bg-[#A8792E]/10 p-3 text-xs text-[#A8792E] dark:text-[#D0A45C]">
              {infoNotice}
            </div>
          )}

          {/* Error Message */}
          <AuthError message={error} />

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <AuthInput
              label="Email"
              type="email"
              id="forgot-email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@company.com"
              required
              autoComplete="email"
            />

            <div className="pt-1">
              <AuthSubmitButton
                loading={loading}
                loadingText="Sending reset instructions..."
              >
                Send reset instructions
              </AuthSubmitButton>
            </div>
          </form>

          {/* Secondary Action */}
          <div className="pt-4 border-t border-[#C7CEC8] dark:border-[#2B3538] text-center">
            <button
              type="button"
              onClick={() => switchMode('login')}
              className="text-xs font-semibold text-[#176B50] hover:text-[#2D8A68] dark:text-[#4FAF87] dark:hover:text-[#5EC498] hover:underline cursor-pointer"
            >
              Back to sign in
            </button>
          </div>
        </div>
      )}
    </AuthShell>
  )
}
