import {
  Activity,
  AlertCircle,
  Building,
  Check,
  Clock,
  Copy,
  Cpu,
  Database,
  Eye,
  EyeOff,
  FileText,
  Key,
  Mail,
  RefreshCw,
  Save,
  Shield,
  ShieldCheck,
  Sparkles,
  Sliders,
  User as UserIcon,
  Zap,
} from 'lucide-react'
import { useEffect, useState } from 'react'

import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { PageHeader } from '../components/ui/PageHeader'
import { useAuth, type AuthUser } from '../context/AuthContext'
import api from '../services/api'

type TabType = 'general' | 'preferences' | 'security' | 'audit'

interface ProfileData {
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
  autoStandardize: boolean
}

interface DashboardStats {
  total_uploads: number
  total_reports: number
  total_mappings: number
  total_records: number
  recent_activity: Array<{
    type: string
    title: string
    description: string
    timestamp: string
    badge: string
  }>
}

function timeAgo(isoString: string | null | undefined): string {
  if (!isoString) return ''
  try {
    const date = new Date(isoString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`
    const diffHrs = Math.floor(diffMins / 60)
    if (diffHrs < 24) return `${diffHrs} hour${diffHrs > 1 ? 's' : ''} ago`
    const diffDays = Math.floor(diffHrs / 24)
    if (diffDays === 1) return 'Yesterday'
    return `${diffDays} days ago`
  } catch {
    return ''
  }
}

export default function Profile() {
  const { user, updateUser } = useAuth()
  const [activeTab, setActiveTab] = useState<TabType>('general')
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<DashboardStats | null>(null)

  const [profile, setProfile] = useState<ProfileData>({
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
    autoStandardize: true,
  })

  const [savedSuccess, setSavedSuccess] = useState(false)
  const [saveError, setSaveError] = useState('')
  const [saving, setSaving] = useState(false)
  const [apiKeyVisible, setApiKeyVisible] = useState(false)
  const [copiedKey, setCopiedKey] = useState(false)
  const [regenerating, setRegenerating] = useState(false)
  const [apiKey, setApiKey] = useState('ab_live_89f7a62d04bc912e847c3e551a0b38d')

  // Load profile from API on mount
  useEffect(() => {
    const loadProfile = async () => {
      try {
        const response = await api.get<AuthUser & {
          default_domain?: string
          confidence_threshold?: number
          anomaly_sensitivity?: string
          report_tone?: string
          auto_standardize?: boolean
        }>('/api/v1/auth/me')
        const u = response.data

        setProfile({
          name: u.name || '',
          email: u.email || '',
          title: u.title || 'Business Analyst',
          department: u.department || 'Operations',
          organization: u.organization || 'Enterprise Operations Hub',
          location: u.location || 'Remote',
          bio: u.bio || '',
          defaultDomain: u.default_domain || 'hr',
          confidenceThreshold: u.confidence_threshold ?? 85,
          anomalySensitivity: u.anomaly_sensitivity || 'balanced',
          reportTone: u.report_tone || 'executive',
          autoStandardize: u.auto_standardize ?? true,
        })
      } catch (err) {
        console.error('Failed to load profile from API:', err)
        // Fallback to auth context user
        if (user) {
          setProfile(prev => ({
            ...prev,
            name: user.name || '',
            email: user.email || '',
            title: user.title || '',
            department: user.department || '',
            organization: user.organization || '',
            location: user.location || '',
            bio: user.bio || '',
          }))
        }
      } finally {
        setLoading(false)
      }
    }
    void loadProfile()
  }, [])

  // Load dashboard stats for the profile stats banner
  useEffect(() => {
    const loadStats = async () => {
      try {
        const response = await api.get<DashboardStats>('/api/v1/dashboard/stats')
        setStats(response.data)
      } catch (err) {
        console.error('Failed to load dashboard stats:', err)
      }
    }
    void loadStats()
  }, [])

  const handleInputChange = (field: keyof ProfileData, value: unknown) => {
    setProfile((prev) => ({ ...prev, [field]: value }))
  }

  const handleSave = async () => {
    setSaving(true)
    setSaveError('')
    try {
      const response = await api.put<AuthUser>('/api/v1/auth/profile', {
        name: profile.name,
        title: profile.title,
        department: profile.department,
        organization: profile.organization,
        location: profile.location,
        bio: profile.bio,
        default_domain: profile.defaultDomain,
        confidence_threshold: profile.confidenceThreshold,
        anomaly_sensitivity: profile.anomalySensitivity,
        report_tone: profile.reportTone,
        auto_standardize: profile.autoStandardize,
      })

      // Update auth context so sidebar/header reflect changes immediately
      updateUser(response.data)
      setSavedSuccess(true)
      setTimeout(() => setSavedSuccess(false), 3000)
    } catch (err: any) {
      console.error('Failed to save profile:', err)
      setSaveError(err?.response?.data?.detail || 'Failed to save profile. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  const handleCopyKey = () => {
    navigator.clipboard.writeText(apiKey)
    setCopiedKey(true)
    setTimeout(() => setCopiedKey(false), 2500)
  }

  const handleRegenerateKey = () => {
    setRegenerating(true)
    setTimeout(() => {
      const randomHex = Array.from({ length: 32 }, () =>
        Math.floor(Math.random() * 16).toString(16)
      ).join('')
      setApiKey(`ab_live_${randomHex}`)
      setRegenerating(false)
    }, 600)
  }

  // Derive display values
  const nameParts = profile.name.split(' ')
  const firstName = nameParts[0] || ''
  const lastName = nameParts.slice(1).join(' ') || ''
  const initials = (firstName[0] || '') + (lastName[0] || firstName[1] || '')

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24 animate-fade-in">
        <div className="text-center space-y-3">
          <RefreshCw className="mx-auto h-8 w-8 animate-spin text-brand-500" />
          <p className="text-sm text-slate-500">Loading profile...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Top Header */}
      <PageHeader
        eyebrow="Account & Governance"
        title="Executive Profile"
        description="Manage your enterprise analytical identity, Copilot autonomous intelligence parameters, and API governance."
        actions={
          <div className="flex items-center gap-2">
            {savedSuccess && (
              <span className="flex items-center gap-1 text-xs font-semibold text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-xl border border-emerald-200 animate-fade-in">
                <Check className="h-3.5 w-3.5" />
                Settings Saved
              </span>
            )}
            {saveError && (
              <span className="flex items-center gap-1 text-xs font-semibold text-red-600 bg-red-50 px-3 py-1.5 rounded-xl border border-red-200 animate-fade-in">
                <AlertCircle className="h-3.5 w-3.5" />
                {saveError}
              </span>
            )}
            <Button variant="default" size="sm" onClick={handleSave} disabled={saving}>
              {saving ? (
                <RefreshCw className="mr-1.5 h-4 w-4 animate-spin" />
              ) : (
                <Save className="mr-1.5 h-4 w-4" />
              )}
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        }
      />

      {/* Hero Profile Banner */}
      <div className="relative overflow-hidden rounded-3xl border border-slate-200/80 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-6 sm:p-8 text-white shadow-xl shadow-slate-900/10">
        <div className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-brand-500/20 blur-3xl" />
        <div className="pointer-events-none absolute -left-16 -bottom-16 h-64 w-64 rounded-full bg-indigo-500/15 blur-3xl" />

        <div className="relative flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-5">
            <div className="relative">
              <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-tr from-brand-600 via-indigo-500 to-violet-400 text-2xl font-black text-white shadow-xl shadow-brand-500/30 border-2 border-white/20">
                {initials.toUpperCase()}
              </div>
              <span className="absolute -bottom-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full border-2 border-slate-900 bg-emerald-500 shadow-sm" title="Online & Synced">
                <Zap className="h-3 w-3 text-white fill-white" />
              </span>
            </div>

            <div className="space-y-1.5">
              <div className="flex flex-wrap items-center gap-2.5">
                <h1 className="text-2xl font-black tracking-tight text-white">
                  {profile.name}
                </h1>
                <Badge variant="brand" className="bg-brand-500/20 text-brand-300 border-brand-400/30">
                  {user?.role === 'admin' ? 'Admin' : 'Enterprise User'}
                </Badge>
                <Badge variant="success" className="bg-emerald-500/20 text-emerald-300 border-emerald-400/30">
                  Autonomous Mode
                </Badge>
              </div>
              <p className="text-sm font-medium text-slate-300">
                {profile.title} &bull; <span className="text-slate-400">{profile.organization}</span>
              </p>
              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 pt-0.5">
                <span className="flex items-center gap-1.5">
                  <Mail className="h-3.5 w-3.5 text-slate-400" />
                  {profile.email}
                </span>
                <span className="flex items-center gap-1.5">
                  <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
                  Role: {user?.role || 'user'}
                </span>
                <span className="flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5 text-slate-400" />
                  {profile.location}
                </span>
              </div>
            </div>
          </div>

          <div className="flex sm:flex-col items-center sm:items-end gap-3 w-full sm:w-auto pt-2 sm:pt-0 border-t sm:border-t-0 border-white/10">
            <div className="text-left sm:text-right">
              <p className="text-[10px] font-bold uppercase tracking-widest text-brand-300">Analytical Quota</p>
              <p className="text-lg font-extrabold text-white">Unlimited <span className="text-xs font-normal text-slate-400">/ Deterministic</span></p>
            </div>
            {user?.created_at && (
              <div className="rounded-xl border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300 backdrop-blur-sm">
                Joined: <span className="font-mono text-brand-300">{new Date(user.created_at).toLocaleDateString()}</span>
              </div>
            )}
          </div>
        </div>

        {/* Quick telemetry metrics — dynamic from DB */}
        <div className="mt-8 grid grid-cols-2 sm:grid-cols-4 gap-3 border-t border-white/10 pt-6">
          <div className="rounded-xl bg-white/5 p-3 backdrop-blur-sm">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Datasets Uploaded</p>
            <p className="text-lg font-bold text-white mt-0.5">{stats?.total_uploads ?? 0}</p>
          </div>
          <div className="rounded-xl bg-white/5 p-3 backdrop-blur-sm">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Generated Reports</p>
            <p className="text-lg font-bold text-white mt-0.5">{stats?.total_reports ?? 0}</p>
          </div>
          <div className="rounded-xl bg-white/5 p-3 backdrop-blur-sm">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Schema Mappings</p>
            <p className="text-lg font-bold text-emerald-400 mt-0.5">{stats?.total_mappings ?? 0}</p>
          </div>
          <div className="rounded-xl bg-white/5 p-3 backdrop-blur-sm">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Records Processed</p>
            <p className="text-lg font-bold text-indigo-300 mt-0.5">{stats?.total_records?.toLocaleString() ?? 0}</p>
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2 overflow-x-auto text-sm">
        <button
          type="button"
          onClick={() => setActiveTab('general')}
          className={`flex items-center gap-2 rounded-xl px-4 py-2.5 font-semibold transition shrink-0 ${
            activeTab === 'general'
              ? 'bg-brand-50 text-brand-700 border border-brand-200 shadow-sm'
              : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
          }`}
        >
          <UserIcon className="h-4 w-4" />
          Personal & Role
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('preferences')}
          className={`flex items-center gap-2 rounded-xl px-4 py-2.5 font-semibold transition shrink-0 ${
            activeTab === 'preferences'
              ? 'bg-brand-50 text-brand-700 border border-brand-200 shadow-sm'
              : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
          }`}
        >
          <Sliders className="h-4 w-4" />
          Copilot & Analytics Preferences
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('security')}
          className={`flex items-center gap-2 rounded-xl px-4 py-2.5 font-semibold transition shrink-0 ${
            activeTab === 'security'
              ? 'bg-brand-50 text-brand-700 border border-brand-200 shadow-sm'
              : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
          }`}
        >
          <Key className="h-4 w-4" />
          Enterprise API & Security
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('audit')}
          className={`flex items-center gap-2 rounded-xl px-4 py-2.5 font-semibold transition shrink-0 ${
            activeTab === 'audit'
              ? 'bg-brand-50 text-brand-700 border border-brand-200 shadow-sm'
              : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
          }`}
        >
          <Activity className="h-4 w-4" />
          Activity & Audit Trail
        </button>
      </div>

      {/* Tab 1: General Info */}
      {activeTab === 'general' && (
        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-2 border-slate-200/80 shadow-sm">
            <CardHeader>
              <h2 className="text-base font-bold text-slate-900">Personal & Organization Profile</h2>
              <p className="text-xs text-slate-500">Configure your identity details displayed on synthesized executive reports.</p>
            </CardHeader>
            <CardContent className="space-y-5">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                  Full Name
                </label>
                <input
                  type="text"
                  value={profile.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm font-medium text-slate-800 shadow-sm transition focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                  Official Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                  <input
                    type="email"
                    value={profile.email}
                    readOnly
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 pl-10 pr-3.5 py-2.5 text-sm font-medium text-slate-500 shadow-sm cursor-not-allowed"
                  />
                </div>
                <p className="mt-1 text-[11px] text-slate-400">Email cannot be changed after registration.</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                    Corporate Job Title
                  </label>
                  <input
                    type="text"
                    value={profile.title}
                    onChange={(e) => handleInputChange('title', e.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm font-medium text-slate-800 shadow-sm transition focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                    Department / Division
                  </label>
                  <input
                    type="text"
                    value={profile.department}
                    onChange={(e) => handleInputChange('department', e.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm font-medium text-slate-800 shadow-sm transition focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                    Enterprise Organization
                  </label>
                  <div className="relative">
                    <Building className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                    <input
                      type="text"
                      value={profile.organization}
                      onChange={(e) => handleInputChange('organization', e.target.value)}
                      className="w-full rounded-xl border border-slate-200 bg-white pl-10 pr-3.5 py-2.5 text-sm font-medium text-slate-800 shadow-sm transition focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                    Location & Timezone
                  </label>
                  <input
                    type="text"
                    value={profile.location}
                    onChange={(e) => handleInputChange('location', e.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm font-medium text-slate-800 shadow-sm transition focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                  Executive Brief / Mission Bio
                </label>
                <textarea
                  rows={3}
                  value={profile.bio}
                  onChange={(e) => handleInputChange('bio', e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 shadow-sm transition focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 leading-relaxed"
                />
              </div>

              <div className="pt-2 flex justify-end">
                <Button variant="default" onClick={handleSave} disabled={saving}>
                  {saving ? <RefreshCw className="mr-1.5 h-4 w-4 animate-spin" /> : <Save className="mr-1.5 h-4 w-4" />}
                  {saving ? 'Saving...' : 'Save Profile Information'}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Side Info */}
          <div className="space-y-6">
            <Card className="border-slate-200/80 shadow-sm">
              <CardHeader>
                <h3 className="text-sm font-bold text-slate-900">Governance Tier</h3>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="rounded-2xl border border-brand-200 bg-brand-50/50 p-4">
                  <div className="flex items-center gap-2 text-brand-900 font-bold text-sm">
                    <Shield className="h-4 w-4 text-brand-600" />
                    Tier 1: Master Orchestrator
                  </div>
                  <p className="mt-1 text-xs text-brand-700 leading-relaxed">
                    Full authority over automated report generation, schema standardizations, deterministic math verification, and data export.
                  </p>
                </div>

                <div className="space-y-2.5 text-xs text-slate-600">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                    <span className="text-slate-500">SSO Authentication</span>
                    <span className="font-semibold text-emerald-600 flex items-center gap-1">
                      <Check className="h-3 w-3" /> Active
                    </span>
                  </div>
                  <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                    <span className="text-slate-500">Security Clearance</span>
                    <span className="font-semibold text-slate-800">Confidential C-Suite</span>
                  </div>
                  <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                    <span className="text-slate-500">Compliance Audit</span>
                    <span className="font-semibold text-slate-800">SOC-2 Type II</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Data Residency</span>
                    <span className="font-semibold text-slate-800">Local Air-Gapped</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-200/80 shadow-sm bg-gradient-to-br from-indigo-50/40 via-white to-brand-50/40">
              <CardContent className="p-5 space-y-3">
                <div className="flex items-center gap-2.5 text-sm font-bold text-indigo-950">
                  <Cpu className="h-4 w-4 text-brand-600" />
                  Deterministic Engine
                </div>
                <p className="text-xs text-slate-600 leading-relaxed">
                  All intelligence metrics, percentages, and anomaly detections are computed natively via Python code and Pandas algorithms — without LLM hallucinations.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Tab 2: Copilot Preferences */}
      {activeTab === 'preferences' && (
        <Card className="border-slate-200/80 shadow-sm">
          <CardHeader>
            <h2 className="text-base font-bold text-slate-900">AI Copilot & Statistical Engine Preferences</h2>
            <p className="text-xs text-slate-500">Fine-tune how datasets are automatically categorized, mapped, and reported.</p>
          </CardHeader>
          <CardContent className="space-y-6 max-w-2xl">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                Primary Analytical Domain Focus
              </label>
              <select
                value={profile.defaultDomain}
                onChange={(e) => handleInputChange('defaultDomain', e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm font-medium text-slate-800 shadow-sm transition focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
              >
                <option value="hr">Human Resources & Talent Workforce Analytics</option>
                <option value="sales">Sales Performance, Commercial & Revenue</option>
                <option value="finance">Corporate Finance, Spend & Cost Accounting</option>
                <option value="inventory">Supply Chain, SKU & Warehouse Stock</option>
                <option value="generic">Universal Cross-Domain Business Intelligence</option>
              </select>
              <p className="mt-1 text-xs text-slate-400">
                Determines the default priority algorithms when multi-domain datasets are uploaded.
              </p>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Auto-Mapping Confidence Threshold
                </label>
                <span className="text-xs font-bold text-brand-600">{profile.confidenceThreshold}%</span>
              </div>
              <input
                type="range"
                min="50"
                max="95"
                step="5"
                value={profile.confidenceThreshold}
                onChange={(e) => handleInputChange('confidenceThreshold', Number(e.target.value))}
                className="w-full accent-brand-600"
              />
              <div className="flex justify-between text-[11px] text-slate-400 mt-1">
                <span>50% (Permissive)</span>
                <span>85% (Recommended)</span>
                <span>95% (Strict Exact Match)</span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                Anomaly Sensitivity Level
              </label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { id: 'conservative', label: 'Conservative', desc: 'Alerts only on extreme statistical outliers (> 3 std dev)' },
                  { id: 'balanced', label: 'Balanced', desc: 'Industry standard z-score & interquartile IQR audits' },
                  { id: 'aggressive', label: 'Aggressive', desc: 'Flags subtle skew, missing patterns, and variance shifts' },
                ].map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => handleInputChange('anomalySensitivity', item.id)}
                    className={`rounded-2xl p-3.5 text-left border transition ${
                      profile.anomalySensitivity === item.id
                        ? 'border-brand-500 bg-brand-50/60 ring-2 ring-brand-500/20'
                        : 'border-slate-200 bg-white hover:bg-slate-50'
                    }`}
                  >
                    <p className="text-xs font-bold text-slate-900">{item.label}</p>
                    <p className="mt-1 text-[11px] text-slate-500 leading-tight">{item.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                Executive Synthesis Style
              </label>
              <select
                value={profile.reportTone}
                onChange={(e) => handleInputChange('reportTone', e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm font-medium text-slate-800 shadow-sm transition focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
              >
                <option value="executive">C-Suite Executive Brief (Actionable KPIs, Strategic Findings)</option>
                <option value="technical">Technical Data Audit (Statistical Distributions, Null Counts)</option>
                <option value="operational">Operational Departmental (Action Items & Category Breakdowns)</option>
              </select>
            </div>

            <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50/60 p-4">
              <div>
                <p className="text-sm font-bold text-slate-800">Auto-Apply Confident Column Mappings</p>
                <p className="text-xs text-slate-500">Automatically standardize schema columns when matcher confidence exceeds {profile.confidenceThreshold}%.</p>
              </div>
              <input
                type="checkbox"
                checked={profile.autoStandardize}
                onChange={(e) => handleInputChange('autoStandardize', e.target.checked)}
                className="h-5 w-5 rounded-lg text-brand-600 focus:ring-brand-500"
              />
            </div>

            <div className="pt-2 flex justify-end">
              <Button variant="default" onClick={handleSave} disabled={saving}>
                {saving ? <RefreshCw className="mr-1.5 h-4 w-4 animate-spin" /> : <Save className="mr-1.5 h-4 w-4" />}
                {saving ? 'Saving...' : 'Save Preferences'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tab 3: Security & API */}
      {activeTab === 'security' && (
        <div className="space-y-6">
          <Card className="border-slate-200/80 shadow-sm">
            <CardHeader>
              <h2 className="text-base font-bold text-slate-900">API Credentials & External Integration</h2>
              <p className="text-xs text-slate-500">Authenticate external pipelines, scheduled ingestion jobs, and automated webhook triggers.</p>
            </CardHeader>
            <CardContent className="space-y-5 max-w-2xl">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                  Production Secret API Key
                </label>
                <div className="flex items-center gap-2">
                  <div className="relative flex-1">
                    <input
                      type={apiKeyVisible ? 'text' : 'password'}
                      readOnly
                      value={apiKey}
                      className="w-full rounded-xl border border-slate-200 bg-slate-50/80 px-3.5 py-2.5 font-mono text-xs text-slate-800 shadow-sm outline-none"
                    />
                    <button
                      type="button"
                      onClick={() => setApiKeyVisible(!apiKeyVisible)}
                      className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
                    >
                      {apiKeyVisible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  <Button variant="secondary" size="sm" onClick={handleCopyKey}>
                    {copiedKey ? <Check className="mr-1.5 h-3.5 w-3.5 text-emerald-600" /> : <Copy className="mr-1.5 h-3.5 w-3.5" />}
                    {copiedKey ? 'Copied' : 'Copy'}
                  </Button>
                  <Button variant="outline" size="sm" onClick={handleRegenerateKey} disabled={regenerating}>
                    <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${regenerating ? 'animate-spin' : ''}`} />
                    Roll Key
                  </Button>
                </div>
                <p className="mt-1.5 text-xs text-slate-400">
                  Keep this key confidential. Do not expose in client-side repositories or public repos.
                </p>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-slate-50/50 p-4 space-y-3">
                <p className="text-xs font-bold uppercase tracking-wider text-slate-700">Quick Integration Example (cURL)</p>
                <pre className="overflow-x-auto rounded-xl bg-slate-900 p-3.5 font-mono text-xs text-slate-200 leading-relaxed">
{`curl -X POST "http://127.0.0.1:8000/api/v1/reports/generate" \\
  -H "Authorization: Bearer ${apiKeyVisible ? apiKey : 'ab_live_••••••••••••'}" \\
  -H "Content-Type: application/json" \\
  -d '{"dataset_id": "dataset_id_here"}'`}
                </pre>
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-200/80 shadow-sm">
            <CardHeader>
              <h3 className="text-sm font-bold text-slate-900">Active Security Sessions</h3>
            </CardHeader>
            <CardContent>
              <div className="divide-y divide-slate-100">
                <div className="flex items-center justify-between py-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700">
                      <Zap className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-slate-800">Current Web Session (Windows / Chrome)</p>
                      <p className="text-xs text-slate-400">IP: 127.0.0.1 &bull; Active Now</p>
                    </div>
                  </div>
                  <Badge variant="success" dot>Current</Badge>
                </div>

                <div className="flex items-center justify-between py-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-100 text-slate-600">
                      <Database className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-slate-800">Local FastAPI Daemon</p>
                      <p className="text-xs text-slate-400">Port 8000 &bull; Bound to 127.0.0.1</p>
                    </div>
                  </div>
                  <Badge variant="default">Verified</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tab 4: Audit Activity Log — dynamic from DB */}
      {activeTab === 'audit' && (
        <Card className="border-slate-200/80 shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-slate-900">Governance & Activity Trail</h2>
                <p className="text-xs text-slate-500">Immutable ledger tracking automated reports, data loads, and schema mutations.</p>
              </div>
              <Badge variant="brand">{stats?.recent_activity?.length ?? 0} Events</Badge>
            </div>
          </CardHeader>
          <CardContent>
            {!stats?.recent_activity?.length ? (
              <div className="py-12 text-center">
                <Activity className="mx-auto h-10 w-10 text-slate-300 mb-3" />
                <p className="text-sm font-bold text-slate-700">No Activity Yet</p>
                <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                  Upload a dataset, generate a report, or apply schema mappings to see your activity trail here.
                </p>
              </div>
            ) : (
              <div className="relative pl-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200 space-y-6">
                {stats.recent_activity.map((item, idx) => {
                  const iconColor =
                    item.type === 'upload' ? 'bg-emerald-500' :
                    item.type === 'report' ? 'bg-brand-500' :
                    item.type === 'mapping' ? 'bg-indigo-500' :
                    'bg-slate-700'
                  const IconComp =
                    item.type === 'upload' ? Database :
                    item.type === 'report' ? FileText :
                    item.type === 'mapping' ? Sliders :
                    Sparkles

                  return (
                    <div key={idx} className="relative group">
                      <span className={`absolute -left-6 top-1.5 h-3 w-3 rounded-full border-2 border-white shadow-sm ${iconColor}`} />
                      <div className="rounded-2xl border border-slate-100 bg-slate-50/70 p-4 transition group-hover:border-brand-200 group-hover:bg-brand-50/20">
                        <div className="flex items-center justify-between gap-2">
                          <p className="text-xs font-bold text-slate-900">{item.title}</p>
                          <span className="text-[11px] font-medium text-slate-400">{timeAgo(item.timestamp)}</span>
                        </div>
                        <p className="mt-1 text-xs text-slate-600 leading-relaxed">{item.description}</p>
                        <div className="mt-2.5 flex items-center gap-2">
                          <Badge variant="default" className="text-[10px] px-2 py-0.5 inline-flex items-center gap-1">
                            <IconComp className="h-3 w-3" />
                            {item.badge}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
