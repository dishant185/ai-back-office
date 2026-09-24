import {
  AlertCircle,
  Check,
  CheckCircle2,
  Copy,
  Eye,
  EyeOff,
  Lock,
  LogOut,
  RefreshCw,
  Save,
  ShieldCheck,
  X,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { ProfileAvatar } from '../components/ui/ProfileAvatar'
import { useAuth, type AuthUser } from '../context/AuthContext'
import api from '../services/api'

interface ProfileFormData {
  name: string
  email: string
  title: string
  department: string
  organization: string
  location: string
  bio: string
  defaultDomain: string
  confidenceThreshold: number
  anomalySensitivity: string
  reportTone: string
}

export default function Profile() {
  const { user, updateUser, logout } = useAuth()
  const navigate = useNavigate()

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [savedSuccess, setSavedSuccess] = useState(false)
  const [saveError, setSaveError] = useState('')

  // Password modal state
  const [passwordModalOpen, setPasswordModalOpen] = useState(false)

  // API Key state
  const [apiKeyVisible, setApiKeyVisible] = useState(false)
  const [copiedKey, setCopiedKey] = useState(false)
  const [apiKey] = useState('ab_live_89f7a62d04bc912e847c3e551a0b38d')

  // Form data
  const [formData, setFormData] = useState<ProfileFormData>({
    name: '',
    email: '',
    title: '',
    department: '',
    organization: '',
    location: '',
    bio: '',
    defaultDomain: 'hr',
    confidenceThreshold: 85,
    anomalySensitivity: 'balanced',
    reportTone: 'executive',
  })

  // Initial snapshot to allow Cancel
  const [initialData, setInitialData] = useState<ProfileFormData>(formData)

  // Update browser document title
  useEffect(() => {
    document.title = 'Novera — Profile'
  }, [])

  // Load profile from API on mount
  useEffect(() => {
    const loadProfile = async () => {
      try {
        const response = await api.get<AuthUser & {
          default_domain?: string
          confidence_threshold?: number
          anomaly_sensitivity?: string
          report_tone?: string
        }>('/api/v1/auth/me')
        const u = response.data

        const loaded: ProfileFormData = {
          name: u.name || '',
          email: u.email || '',
          title: u.title || 'Business Analyst',
          department: u.department || 'Operations',
          organization: u.organization || 'Production Workspace',
          location: u.location || 'Remote',
          bio: u.bio || '',
          defaultDomain: u.default_domain || 'hr',
          confidenceThreshold: u.confidence_threshold ?? 85,
          anomalySensitivity: u.anomaly_sensitivity || 'balanced',
          reportTone: u.report_tone || 'executive',
        }

        setFormData(loaded)
        setInitialData(loaded)
      } catch {
        // Fallback to auth context
        if (user) {
          const fallback: ProfileFormData = {
            name: user.name || '',
            email: user.email || '',
            title: user.title || 'Business Analyst',
            department: user.department || 'Operations',
            organization: user.organization || 'Production Workspace',
            location: user.location || 'Remote',
            bio: user.bio || '',
            defaultDomain: 'hr',
            confidenceThreshold: 85,
            anomalySensitivity: 'balanced',
            reportTone: 'executive',
          }
          setFormData(fallback)
          setInitialData(fallback)
        }
      } finally {
        setLoading(false)
      }
    }
    void loadProfile()
  }, [user])

  const handleInputChange = (field: keyof ProfileFormData, value: unknown) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const handleCancel = () => {
    setFormData(initialData)
    setSaveError('')
    setSavedSuccess(false)
  }

  const handleSave = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    setSaving(true)
    setSaveError('')
    setSavedSuccess(false)

    try {
      const response = await api.put<AuthUser>('/api/v1/auth/profile', {
        name: formData.name,
        title: formData.title,
        department: formData.department,
        organization: formData.organization,
        location: formData.location,
        bio: formData.bio,
        default_domain: formData.defaultDomain,
        confidence_threshold: formData.confidenceThreshold,
        anomaly_sensitivity: formData.anomalySensitivity,
        report_tone: formData.reportTone,
      })

      updateUser(response.data)
      setInitialData(formData)
      setSavedSuccess(true)
      setTimeout(() => setSavedSuccess(false), 3500)
    } catch (err: any) {
      setSaveError(
        err?.response?.data?.detail || 'Failed to save changes. Please try again.'
      )
    } finally {
      setSaving(false)
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const handleCopyKey = () => {
    navigator.clipboard.writeText(apiKey)
    setCopiedKey(true)
    setTimeout(() => setCopiedKey(false), 2000)
  }

  const displayName = formData.name || user?.name || 'dishant kanani'
  const displayEmail = formData.email || user?.email || 'user@novera.ai'
  const displayWorkspace = formData.organization || user?.organization || 'Production Workspace'
  const displayRole = user?.role ? (user.role === 'admin' ? 'Workspace Admin' : 'Workspace Member') : 'Workspace Member'
  const displayCreated = user?.created_at
    ? new Date(user.created_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    : null

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="flex items-center gap-2.5 font-mono text-xs text-[#66716C]">
          <RefreshCw className="h-4 w-4 animate-spin text-[#176B50]" />
          <span>Loading identity ledger...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl space-y-8 pb-16">
      {/* 1. HEADER */}
      <div className="border-b border-[#C7CEC8] dark:border-[#2B3538] pb-5">
        <h1 className="font-sans text-2xl font-bold tracking-tight text-[#11181B] dark:text-[#EEF2EE]">
          Profile
        </h1>
        <p className="mt-1 text-xs text-[#66716C] dark:text-[#AAB5AF]">
          Manage your account information and workspace identity.
        </p>
      </div>

      {/* Save Notification */}
      {savedSuccess && (
        <div
          role="status"
          className="flex items-center gap-2 rounded-[2px] border border-[#176B50]/30 bg-[#176B50]/10 p-3 text-xs text-[#176B50] dark:text-[#4FAF87]"
        >
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>Changes saved successfully to your Novera profile.</span>
        </div>
      )}

      {saveError && (
        <div
          role="alert"
          className="flex items-center gap-2 rounded-[2px] border border-[#B33A3A]/30 bg-[#B33A3A]/10 p-3 text-xs text-[#B33A3A] dark:text-[#D06161]"
        >
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{saveError}</span>
        </div>
      )}

      {/* 2. ACCOUNT SUMMARY ROW */}
      <div className="rounded-[2px] border border-[#C7CEC8] dark:border-[#2B3538] bg-white dark:bg-[#141C1F] p-5 sm:p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            {/* Square 32x32 / 40x40 avatar with #176B50 */}
            <ProfileAvatar name={displayName} size="lg" />
            <div>
              <h2 className="font-sans text-base font-bold text-[#11181B] dark:text-[#EEF2EE]">
                {displayName}
              </h2>
              <p className="font-mono text-xs text-[#66716C] dark:text-[#AAB5AF]">
                {displayEmail}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleLogout}
              className="flex h-9 items-center gap-2 rounded-[2px] border border-[#B33A3A]/40 px-3 text-xs font-medium text-[#B33A3A] dark:text-[#D06161] hover:bg-[#B33A3A]/10 transition-colors cursor-pointer"
            >
              <LogOut className="h-3.5 w-3.5" />
              <span>Sign out</span>
            </button>
          </div>
        </div>
      </div>

      {/* 3. PERSONAL INFORMATION FORM */}
      <form
        onSubmit={handleSave}
        className="rounded-[2px] border border-[#C7CEC8] dark:border-[#2B3538] bg-white dark:bg-[#141C1F] p-5 sm:p-6 space-y-6"
      >
        <div className="border-b border-[#C7CEC8]/60 dark:border-[#2B3538]/60 pb-3">
          <h2 className="font-sans text-sm font-bold uppercase tracking-wider text-[#11181B] dark:text-[#EEF2EE]">
            Personal Information
          </h2>
          <p className="text-xs text-[#66716C] dark:text-[#AAB5AF] mt-0.5">
            Update your identity attributes displayed on synthesized reports.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div>
            <label className="block text-xs font-semibold text-[#11181B] dark:text-[#EEF2EE] mb-1.5">
              Full name
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              className="h-10 w-full rounded-[2px] border border-[#C7CEC8] dark:border-[#2B3538] bg-white dark:bg-[#1B2528] px-3 text-xs text-[#11181B] dark:text-[#EEF2EE] focus:border-[#176B50] focus:ring-1 focus:ring-[#176B50] outline-none"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#11181B] dark:text-[#EEF2EE] mb-1.5">
              Email
            </label>
            <input
              type="email"
              value={formData.email}
              readOnly
              className="h-10 w-full rounded-[2px] border border-[#C7CEC8]/60 dark:border-[#2B3538]/60 bg-[#F3F5F1] dark:bg-[#141C1F] px-3 text-xs text-[#66716C] dark:text-[#AAB5AF] cursor-not-allowed outline-none"
            />
            <p className="mt-1 text-[11px] text-[#66716C] dark:text-[#AAB5AF]">
              Email is tied to your enterprise identity and cannot be changed here.
            </p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#11181B] dark:text-[#EEF2EE] mb-1.5">
              Corporate Title
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => handleInputChange('title', e.target.value)}
              className="h-10 w-full rounded-[2px] border border-[#C7CEC8] dark:border-[#2B3538] bg-white dark:bg-[#1B2528] px-3 text-xs text-[#11181B] dark:text-[#EEF2EE] focus:border-[#176B50] focus:ring-1 focus:ring-[#176B50] outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#11181B] dark:text-[#EEF2EE] mb-1.5">
              Department
            </label>
            <input
              type="text"
              value={formData.department}
              onChange={(e) => handleInputChange('department', e.target.value)}
              className="h-10 w-full rounded-[2px] border border-[#C7CEC8] dark:border-[#2B3538] bg-white dark:bg-[#1B2528] px-3 text-xs text-[#11181B] dark:text-[#EEF2EE] focus:border-[#176B50] focus:ring-1 focus:ring-[#176B50] outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#11181B] dark:text-[#EEF2EE] mb-1.5">
              Enterprise Organization
            </label>
            <input
              type="text"
              value={formData.organization}
              onChange={(e) => handleInputChange('organization', e.target.value)}
              className="h-10 w-full rounded-[2px] border border-[#C7CEC8] dark:border-[#2B3538] bg-white dark:bg-[#1B2528] px-3 text-xs text-[#11181B] dark:text-[#EEF2EE] focus:border-[#176B50] focus:ring-1 focus:ring-[#176B50] outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#11181B] dark:text-[#EEF2EE] mb-1.5">
              Location & Timezone
            </label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => handleInputChange('location', e.target.value)}
              className="h-10 w-full rounded-[2px] border border-[#C7CEC8] dark:border-[#2B3538] bg-white dark:bg-[#1B2528] px-3 text-xs text-[#11181B] dark:text-[#EEF2EE] focus:border-[#176B50] focus:ring-1 focus:ring-[#176B50] outline-none"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-[#11181B] dark:text-[#EEF2EE] mb-1.5">
            Mission Bio / Notes
          </label>
          <textarea
            rows={3}
            value={formData.bio}
            onChange={(e) => handleInputChange('bio', e.target.value)}
            className="w-full rounded-[2px] border border-[#C7CEC8] dark:border-[#2B3538] bg-white dark:bg-[#1B2528] p-3 text-xs text-[#11181B] dark:text-[#EEF2EE] focus:border-[#176B50] focus:ring-1 focus:ring-[#176B50] outline-none resize-none"
          />
        </div>

        {/* Action buttons */}
        <div className="flex items-center justify-end gap-3 pt-3 border-t border-[#C7CEC8]/60 dark:border-[#2B3538]/60">
          <button
            type="button"
            onClick={handleCancel}
            disabled={saving}
            className="h-9 px-4 rounded-[2px] border border-[#C7CEC8] dark:border-[#2B3538] text-xs font-medium text-[#46524D] dark:text-[#AAB5AF] hover:bg-black/[0.03] dark:hover:bg-white/[0.04] transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving}
            className="flex h-9 items-center gap-2 rounded-[2px] bg-[#176B50] hover:bg-[#2D8A68] px-4 text-xs font-semibold text-white transition-colors cursor-pointer disabled:opacity-60"
          >
            {saving ? (
              <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Save className="h-3.5 w-3.5" />
            )}
            <span>{saving ? 'Saving changes...' : 'Save changes'}</span>
          </button>
        </div>
      </form>

      {/* 4. WORKSPACE IDENTITY */}
      <div className="rounded-[2px] border border-[#C7CEC8] dark:border-[#2B3538] bg-white dark:bg-[#141C1F] p-5 sm:p-6 space-y-4">
        <div className="border-b border-[#C7CEC8]/60 dark:border-[#2B3538]/60 pb-3">
          <h2 className="font-sans text-sm font-bold uppercase tracking-wider text-[#11181B] dark:text-[#EEF2EE]">
            Workspace Identity
          </h2>
          <p className="text-xs text-[#66716C] dark:text-[#AAB5AF] mt-0.5">
            Operational boundaries and deterministic audit scope.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="rounded-[2px] border border-[#C7CEC8]/60 dark:border-[#2B3538]/60 p-3.5 bg-[#F3F5F1]/50 dark:bg-[#1B2528]/40">
            <p className="font-mono text-[10px] uppercase text-[#66716C] dark:text-[#AAB5AF]">
              Workspace
            </p>
            <p className="font-sans text-xs font-semibold text-[#11181B] dark:text-[#EEF2EE] mt-1">
              {displayWorkspace}
            </p>
          </div>

          <div className="rounded-[2px] border border-[#C7CEC8]/60 dark:border-[#2B3538]/60 p-3.5 bg-[#F3F5F1]/50 dark:bg-[#1B2528]/40">
            <p className="font-mono text-[10px] uppercase text-[#66716C] dark:text-[#AAB5AF]">
              Role
            </p>
            <p className="font-sans text-xs font-semibold text-[#176B50] dark:text-[#4FAF87] mt-1 flex items-center gap-1">
              <ShieldCheck className="h-3 w-3" />
              {displayRole}
            </p>
          </div>

          {displayCreated && (
            <div className="rounded-[2px] border border-[#C7CEC8]/60 dark:border-[#2B3538]/60 p-3.5 bg-[#F3F5F1]/50 dark:bg-[#1B2528]/40">
              <p className="font-mono text-[10px] uppercase text-[#66716C] dark:text-[#AAB5AF]">
                Created
              </p>
              <p className="font-mono text-xs font-medium text-[#11181B] dark:text-[#EEF2EE] mt-1 tabular-nums">
                {displayCreated}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* 5. SECURITY & CREDENTIALS */}
      <div className="rounded-[2px] border border-[#C7CEC8] dark:border-[#2B3538] bg-white dark:bg-[#141C1F] p-5 sm:p-6 space-y-5">
        <div className="border-b border-[#C7CEC8]/60 dark:border-[#2B3538]/60 pb-3">
          <h2 className="font-sans text-sm font-bold uppercase tracking-wider text-[#11181B] dark:text-[#EEF2EE]">
            Security
          </h2>
          <p className="text-xs text-[#66716C] dark:text-[#AAB5AF] mt-0.5">
            Credential protection and programmatic API authorization.
          </p>
        </div>

        {/* Password Row */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-[2px] border border-[#C7CEC8]/60 dark:border-[#2B3538]/60 bg-[#F3F5F1]/40 dark:bg-[#1B2528]/20">
          <div>
            <p className="text-xs font-semibold text-[#11181B] dark:text-[#EEF2EE]">Password</p>
            <p className="font-mono text-xs text-[#66716C] dark:text-[#AAB5AF] tracking-widest mt-0.5">
              ••••••••••••
            </p>
          </div>
          <button
            type="button"
            onClick={() => setPasswordModalOpen(true)}
            className="h-8 px-3 rounded-[2px] border border-[#C7CEC8] dark:border-[#2B3538] text-xs font-medium text-[#11181B] dark:text-[#EEF2EE] hover:bg-black/[0.03] dark:hover:bg-white/[0.04] transition-colors cursor-pointer self-start sm:self-auto"
          >
            Change password
          </button>
        </div>

        {/* API Credentials */}
        <div>
          <label className="block text-xs font-semibold text-[#11181B] dark:text-[#EEF2EE] mb-1.5">
            Production Secret API Key
          </label>
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <input
                type={apiKeyVisible ? 'text' : 'password'}
                readOnly
                value={apiKey}
                className="h-10 w-full rounded-[2px] border border-[#C7CEC8] dark:border-[#2B3538] bg-[#F3F5F1] dark:bg-[#1B2528] px-3 font-mono text-xs text-[#11181B] dark:text-[#EEF2EE] outline-none"
              />
              <button
                type="button"
                onClick={() => setApiKeyVisible(!apiKeyVisible)}
                className="absolute right-2.5 top-2.5 text-[#66716C] hover:text-[#11181B] dark:text-[#AAB5AF] dark:hover:text-white"
                aria-label={apiKeyVisible ? 'Hide API key' : 'Show API key'}
              >
                {apiKeyVisible ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
            <button
              type="button"
              onClick={handleCopyKey}
              className="flex h-10 items-center gap-1.5 rounded-[2px] border border-[#C7CEC8] dark:border-[#2B3538] px-3 text-xs font-medium text-[#11181B] dark:text-[#EEF2EE] hover:bg-black/[0.03] dark:hover:bg-white/[0.04] transition-colors cursor-pointer"
            >
              {copiedKey ? (
                <Check className="h-3.5 w-3.5 text-[#176B50] dark:text-[#4FAF87]" />
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
              <span>{copiedKey ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
          <p className="mt-1 text-[11px] text-[#66716C] dark:text-[#AAB5AF]">
            Authenticate external data pipelines and automated reporting webhooks.
          </p>
        </div>
      </div>

      {/* Change Password Dialog (Transparent Enterprise Status) */}
      {passwordModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-[2px] border border-[#C7CEC8] dark:border-[#2B3538] bg-white dark:bg-[#141C1F] p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-[#C7CEC8]/60 dark:border-[#2B3538]/60 pb-3">
              <div className="flex items-center gap-2">
                <Lock className="h-4 w-4 text-[#176B50]" />
                <h3 className="font-sans text-sm font-bold text-[#11181B] dark:text-[#EEF2EE]">
                  Password Governance
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setPasswordModalOpen(false)}
                className="text-[#66716C] hover:text-[#11181B] dark:hover:text-white"
                aria-label="Close dialog"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <p className="text-xs text-[#46524D] dark:text-[#AAB5AF] leading-relaxed">
              Your account credentials for <strong className="text-[#11181B] dark:text-white">{displayEmail}</strong> are managed under Novera Enterprise Authentication. Self-service password changes are handled by your workspace administrator or identity directory.
            </p>

            <div className="rounded-[2px] border border-[#A8792E]/30 bg-[#A8792E]/10 p-3 text-xs text-[#A8792E] dark:text-[#D0A45C]">
              To rotate your master credentials or request a security key refresh, contact your workspace administrator or submit an IT governance ticket.
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={() => setPasswordModalOpen(false)}
                className="h-9 px-4 rounded-[2px] bg-[#176B50] hover:bg-[#2D8A68] text-xs font-semibold text-white transition-colors cursor-pointer"
              >
                Understood
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
