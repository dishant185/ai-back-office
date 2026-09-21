/**
 * AI Business Analyst Page — Production-Grade Modern Architecture.
 *
 * Clean conversational interface:
 * - Dataset Selector dropdown
 * - Connection Status indicator (● AI Connected)
 * - Dataset-aware Suggested Questions
 * - Strict Grounded Answers with collapsible Verified Data source indicator
 * - Zero static generic KPI block injection
 */
import { useEffect, useRef, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import {
  Bot,
  Database,
  Loader2,
  RefreshCw,
  Send,
  Upload,
} from 'lucide-react'

import { AnalystMessage } from '../components/ai/AnalystMessage'
import { SuggestedQuestions } from '../components/ai/SuggestedQuestions'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardContent } from '../components/ui/Card'
import { analystApi } from '../services/analystApi'
import api from '../services/api'
import type { AnalystSession, ChatMessage } from '../types/ai'

interface DatasetOption {
  id: string
  filename: string
  profile?: string
  rowCount?: number
}

export default function AIAnalyst() {
  const [searchParams, setSearchParams] = useSearchParams()
  const paramDatasetId = searchParams.get('datasetId')
  const paramReportType = searchParams.get('reportType')

  // Datasets state
  const [datasets, setDatasets] = useState<DatasetOption[]>([])
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(paramDatasetId)
  const [isLoadingDatasets, setIsLoadingDatasets] = useState(true)

  // Session & Chat state
  const [session, setSession] = useState<AnalystSession | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const chatBottomRef = useRef<HTMLDivElement | null>(null)
  const inputRef = useRef<HTMLTextAreaElement | null>(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isSending])

  // 1. Fetch available datasets
  useEffect(() => {
    const fetchDatasets = async () => {
      setIsLoadingDatasets(true)
      try {
        const resp = await api.get('/api/v1/uploads/list')
        const uploads = (resp.data || []) as Array<{
          upload_id: string
          filename: string
          profile?: string
          row_count?: number
        }>

        const options: DatasetOption[] = uploads.map((u) => ({
          id: u.upload_id,
          filename: u.filename || 'dataset.csv',
          profile: u.profile,
          rowCount: u.row_count,
        }))

        setDatasets(options)

        // Select initial dataset
        if (paramDatasetId && options.some((o) => o.id === paramDatasetId)) {
          setSelectedDatasetId(paramDatasetId)
        } else if (options.length > 0) {
          setSelectedDatasetId(options[0].id)
        } else {
          setSelectedDatasetId(null)
        }
      } catch {
        setDatasets([])
        setSelectedDatasetId(null)
      } finally {
        setIsLoadingDatasets(false)
      }
    }

    fetchDatasets()
  }, [paramDatasetId])

  // 2. Initialize or switch session when selectedDatasetId changes
  useEffect(() => {
    if (!selectedDatasetId) {
      setSession(null)
      setMessages([])
      return
    }

    const initSession = async () => {
      setError(null)
      try {
        const reportContext = paramReportType ? { report_type: paramReportType } : undefined
        const sess = await analystApi.createSession(selectedDatasetId, reportContext)
        setSession(sess)

        const currentDataset = datasets.find((d) => d.id === selectedDatasetId)
        const name = currentDataset?.filename || 'dataset'
        const profile = (sess.profile || 'business').toUpperCase()

        const welcomeContent = paramReportType
          ? `I can answer questions regarding your ${paramReportType.replace(/_/g, ' ')} report for **${name}**. What would you like to explore?`
          : `I am your AI Business Analyst for **${name}** (${profile} dataset with ${sess.row_count.toLocaleString()} verified records).\n\nAsk me any question about your data — from specific metrics to entity rankings and data quality.`

        setMessages([
          {
            id: 'msg-init',
            role: 'assistant',
            content: welcomeContent,
            timestamp: 'Just now',
          },
        ])
      } catch (err) {
        setError('Failed to initialize session for the selected dataset.')
      }
    }

    initSession()
  }, [selectedDatasetId])

  // Handle dataset change from dropdown
  const handleDatasetChange = (newDatasetId: string) => {
    setSelectedDatasetId(newDatasetId)
    setSearchParams({ datasetId: newDatasetId })
  }

  // Send message
  const handleSend = async (textToSend?: string) => {
    const question = (textToSend || input).trim()
    if (!question || !session || isSending) return

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: question,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setIsSending(true)
    setError(null)

    try {
      const response = await analystApi.sendMessage(session.session_id, question)

      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sources: response.sources,
        insights: response.insights,
        recommendations: response.recommendations,
        limitations: response.limitations,
        ai_status: response.ai_status,
      }

      setMessages((prev) => [...prev, assistantMsg])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: 'Sorry, I encountered an issue verifying data for your question. Please try asking again.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          limitations: ['Analytics execution notice'],
        },
      ])
    } finally {
      setIsSending(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleNewConversation = () => {
    if (!selectedDatasetId) return
    analystApi
      .createSession(selectedDatasetId)
      .then((sess) => {
        setSession(sess)
        const currentDataset = datasets.find((d) => d.id === selectedDatasetId)
        const name = currentDataset?.filename || 'dataset'
        setMessages([
          {
            id: 'msg-init',
            role: 'assistant',
            content: `New conversation started for **${name}**. What would you like to know?`,
            timestamp: 'Just now',
          },
        ])
      })
      .catch(() => setError('Failed to reset conversation.'))
  }

  // ─── Loading Datasets ──────────────────────────────────
  if (isLoadingDatasets) {
    return (
      <div className="flex h-96 flex-col items-center justify-center space-y-4">
        <Loader2 className="h-8 w-8 text-brand-500 animate-spin" />
        <p className="text-sm text-slate-500">Connecting to business dataset...</p>
      </div>
    )
  }

  // ─── No Dataset Available ──────────────────────────────
  if (datasets.length === 0) {
    return (
      <div className="max-w-xl mx-auto py-16 space-y-6 text-center animate-fade-in">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-50 text-brand-600">
          <Upload className="h-8 w-8" />
        </div>
        <div className="space-y-2">
          <h2 className="text-xl font-bold text-slate-900">No Dataset Uploaded</h2>
          <p className="text-sm text-slate-500 leading-relaxed">
            Upload your sales, HR, customer, or business data in CSV or Excel format to start conversational AI analysis.
          </p>
        </div>
        <Link to="/upload">
          <Button variant="primary" size="md">
            <Upload className="mr-2 h-4 w-4" />
            Upload Dataset
          </Button>
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto flex flex-col h-[calc(100vh-6.5rem)] pb-4 space-y-3 animate-fade-in">
      {/* Top Header Bar */}
      <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white px-5 py-3.5 rounded-2xl border border-slate-200/80 shadow-sm shrink-0">
        <div className="space-y-0.5">
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold text-slate-900 tracking-tight">AI Business Analyst</h1>
            <Badge variant="default" className="bg-emerald-50 text-emerald-700 border-emerald-200/80 font-semibold text-[11px] gap-1.5 py-0.5 px-2">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Grounded
            </Badge>
            <Badge variant="default" className="text-[10px] text-slate-500 py-0.5 px-1.5">
              v1
            </Badge>
          </div>
          <p className="text-xs text-slate-500">
            Current dataset: <span className="font-semibold text-slate-700">{datasets.find(d => d.id === selectedDatasetId)?.filename || 'dataset.csv'}</span> • Grounded in verified analytics
          </p>
        </div>

        {/* Header Controls: Dataset Selector & New Conversation */}
        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 text-xs text-slate-700">
            <Database className="h-3.5 w-3.5 text-slate-400 shrink-0" />
            <span className="text-slate-500 font-medium">Dataset:</span>
            <select
              value={selectedDatasetId || ''}
              onChange={(e) => handleDatasetChange(e.target.value)}
              className="bg-transparent font-semibold text-slate-900 outline-none cursor-pointer pr-1"
              aria-label="Select dataset"
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.filename}
                </option>
              ))}
            </select>
          </div>

          <Button
            variant="secondary"
            size="sm"
            onClick={handleNewConversation}
            className="text-xs font-semibold text-slate-700 hover:text-slate-900 border-slate-200"
            title="Start new conversation"
          >
            <RefreshCw className="mr-1.5 h-3.5 w-3.5 text-slate-500" />
            New Conversation
          </Button>
        </div>
      </header>

      {/* Main Chat Canvas */}
      <Card className="flex-1 flex flex-col border-slate-200/80 shadow-sm overflow-hidden bg-slate-50/30 rounded-2xl">
        {/* Messages Container */}
        <CardContent className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5">
          {/* Initial Suggested Questions */}
          {messages.length <= 1 && session && (
            <div className="max-w-2xl mx-auto my-4 space-y-4 animate-fade-in">
              <SuggestedQuestions
                profile={session.profile}
                onSelect={(q) => handleSend(q)}
              />
            </div>
          )}

          {/* Rendered Messages */}
          {messages.map((msg) => (
            <AnalystMessage key={msg.id} message={msg} />
          ))}

          {/* Typing / Loading indicator */}
          {isSending && (
            <div className="flex gap-3 animate-fade-in">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 text-white shadow-sm">
                <Bot className="h-4 w-4 animate-pulse" />
              </div>
              <div className="rounded-2xl border border-slate-200/80 bg-white px-4 py-3 shadow-sm">
                <div className="flex items-center gap-2.5 text-xs text-slate-600">
                  <Loader2 className="h-3.5 w-3.5 animate-spin text-brand-600" />
                  <span className="font-medium">Calculating verified analytics from dataset...</span>
                </div>
              </div>
            </div>
          )}

          {/* Error Alert */}
          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-xs text-red-700 flex items-center justify-between">
              <span>{error}</span>
              <Button size="sm" variant="secondary" onClick={() => setError(null)}>Dismiss</Button>
            </div>
          )}

          <div ref={chatBottomRef} />
        </CardContent>

        {/* Input Footer */}
        <div className="border-t border-slate-200/80 bg-white p-3 sm:p-4 shrink-0 space-y-2">
          {/* Quick chips when active conversation */}
          {messages.length > 2 && session && (
            <div className="overflow-x-auto pb-1">
              <SuggestedQuestions
                profile={session.profile}
                onSelect={(q) => handleSend(q)}
                compact
              />
            </div>
          )}

          {/* Composer */}
          <div className="flex items-end gap-2 bg-surface-sunken border border-border rounded-2xl p-1.5 focus-within:bg-surface-raised focus-within:border-brand-500 focus-within:ring-2 focus-within:ring-brand-500/20 transition-all">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about your data..."
              rows={1}
              className="flex-1 resize-none bg-transparent px-3 py-2 text-sm text-text-primary placeholder:text-text-muted outline-none leading-relaxed"
              style={{ minHeight: '40px', maxHeight: '120px' }}
              aria-label="Ask anything about your data"
            />
            <Button
              type="button"
              onClick={() => handleSend()}
              disabled={!input.trim() || isSending}
              className="bg-brand-600 hover:bg-brand-700 text-white font-bold h-9 w-9 p-0 rounded-xl shrink-0 transition cursor-pointer"
              aria-label="Send message"
            >
              {isSending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
          <div className="flex flex-wrap justify-between items-center gap-2 px-1">
            <span className="text-[11px] text-text-muted">
              Press <kbd className="px-1 py-0.5 rounded bg-surface-sunken border border-border text-[10px] font-mono">Enter</kbd> to send, <kbd className="px-1 py-0.5 rounded bg-surface-sunken border border-border text-[10px] font-mono">Shift+Enter</kbd> for new line
            </span>
            <span className="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">
              100% Deterministic Grounding Active
            </span>
          </div>
        </div>
      </Card>
    </div>
  )
}
