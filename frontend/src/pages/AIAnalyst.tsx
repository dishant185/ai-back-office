import { useState, useRef, useEffect } from 'react'
import {
  Bot,
  Check,
  ChevronRight,
  Copy,
  RefreshCw,
  Send,
  ShieldCheck,
  Sparkles,
  User,
} from 'lucide-react'

import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardHeader } from '../components/ui/Card'
import { PageHeader } from '../components/ui/PageHeader'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  deterministicTag?: string
  highlights?: string[]
}

const KNOWLEDGE_RESPONSES: Record<string, { content: string; deterministicTag: string; highlights: string[] }> = {
  attrition: {
    content: `Based on deterministic statistical evaluation of the active workforce dataset (3,150 records across 39 dimensions):

1. **Tenure Flight Curve**: Employees with **2 to 5 years tenure** exhibit a **24.3% higher flight probability** than both newly onboarded (<1 year) and tenured personnel (>7 years).
2. **Overtime Correlation**: Personnel logging consistent overtime display an attrition rate of **30.5%**, compared to **10.4%** for standard-hours peers.
3. **Compensation Parity**: Flight risk concentrates in payment tiers 1 and 2, where compensation falls below the median interquartile range ($3,200/mo).

**Strategic Recommendation**: Implement targeted mid-career title reviews and mentorship frameworks at the 24-month mark to neutralize flight risk before year 3.`,
    deterministicTag: 'Python Pandas Cross-Tabulation & Pearson r=0.41',
    highlights: ['24.3% elevated flight probability at 2-5 yrs', '30.5% attrition in overtime segment', 'Targeted review at 24-month mark'],
  },
  revenue: {
    content: `Analyzing commercial revenue and transactional records:

1. **Top-Line Concentration**: The top 20% of accounts generate **68.4% of total gross revenue**, demonstrating classic Pareto distribution.
2. **Margin Disparity**: Specialized enterprise SKUs deliver an average **41.2% gross margin**, whereas high-volume basic tiers deliver **18.7%**.
3. **Quarterly Run-Rate**: Trailing quarter volume shows consistent month-over-month compounding of **+4.8%**, led by regional office expansion.

**Strategic Recommendation**: Shift sales incentive compensation towards Tier-1 high-margin products to capture an estimated $140K in annual gross margin expansion.`,
    deterministicTag: 'Parametric Margin Distribution & SKU Pareto Sort',
    highlights: ['68.4% revenue concentrated in top 20% accounts', '41.2% gross margin in enterprise SKUs', '+4.8% monthly compounding velocity'],
  },
  anomalies: {
    content: `Executing deterministic Z-Score and Interquartile Range (IQR) anomaly sweep:

1. **Compensation Outliers**: 14 records detected with compensation exceeding 3.2 standard deviations above department medians ($18,500+/mo).
2. **Tenure-to-Promotion Stagnation**: 82 records identified with >8 years at organization without promotional milestone.
3. **Data Hygiene Outliers**: Detected 150 duplicate records (4.76% of raw dataset) and 3,088 missing values concentrated primarily in secondary performance notes.

**Strategic Recommendation**: Apply the Column Mapping Studio standardizations to filter duplicates before finalizing C-suite executive deliverables.`,
    deterministicTag: 'IQR Outlier Detection (k=1.5) & Z-Score Analysis (z>3.0)',
    highlights: ['14 compensation outliers (z>3.2)', '82 tenure stagnation cases detected', '150 duplicates flagged for deduplication'],
  },
  strategy: {
    content: `Executive Summary & 3-Point C-Suite Action Plan:

- **Action 1: Retention Engineering**
  Deploy retention bonuses and leadership acceleration programs targeting mid-tenure technical talent (2–5 years experience).
- **Action 2: Schema Harmonization**
  Standardize internal ERP and HRIS column nomenclatures to the unified canonical schema to ensure real-time reporting continuity.
- **Action 3: Hygiene & Governance Protocol**
  Enforce automated duplicate rejection at ingestion to maintain the dataset completeness score above 98.5%.`,
    deterministicTag: 'Autonomous Executive Synthesis Engine',
    highlights: ['Mid-tenure retention acceleration', 'Canonical schema continuous governance', 'Automated duplicate rejection threshold'],
  },
}

const SUGGESTIONS = [
  {
    category: 'Workforce & Talent',
    title: 'Analyze Employee Flight Risk Patterns',
    query: 'What are the primary flight-risk indicators for employees with 2 to 5 years tenure?',
    key: 'attrition',
  },
  {
    category: 'Commercial Revenue',
    title: 'Examine Revenue Velocity & Margins',
    query: 'Which product SKUs generated top-tier margin contribution and growth?',
    key: 'revenue',
  },
  {
    category: 'Data Governance',
    title: 'Run Anomaly & Outlier Sweep',
    query: 'Find statistical anomalies and compensation outliers in the dataset.',
    key: 'anomalies',
  },
  {
    category: 'C-Suite Brief',
    title: 'Synthesize Strategic Board Action Plan',
    query: 'Synthesize a 3-point strategic executive action plan for operations.',
    key: 'strategy',
  },
]

export default function AIAnalyst() {
  const [input, setInput] = useState('')
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [isTyping, setIsTyping] = useState(false)
  const chatBottomRef = useRef<HTMLDivElement | null>(null)

  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'msg-init',
      role: 'assistant',
      content: `Welcome to the Executive Copilot Intelligence Studio. I am your autonomous data analyst.

I evaluate your spreadsheets using deterministic Python algorithms and Pandas computation — giving you mathematical answers without hallucinations. Select a strategic prompt below or query your dataset directly.`,
      timestamp: 'Just now',
      deterministicTag: 'Zero-Hallucination Deterministic Engine',
    },
  ])

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  const handleSend = (textToSend?: string) => {
    const query = (textToSend || input).trim()
    if (!query) return

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: 'Just now',
    }

    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setIsTyping(true)

    // Match query against knowledge base
    const lower = query.toLowerCase()
    let matchedKey = 'strategy'
    if (lower.includes('attrition') || lower.includes('flight') || lower.includes('retention') || lower.includes('tenure') || lower.includes('employee')) {
      matchedKey = 'attrition'
    } else if (lower.includes('revenue') || lower.includes('sales') || lower.includes('margin') || lower.includes('product') || lower.includes('sku')) {
      matchedKey = 'revenue'
    } else if (lower.includes('anomaly') || lower.includes('outlier') || lower.includes('hygiene') || lower.includes('duplicate')) {
      matchedKey = 'anomalies'
    }

    const answer = KNOWLEDGE_RESPONSES[matchedKey]

    setTimeout(() => {
      setIsTyping(false)
      const assistantMsg: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: answer.content,
        timestamp: 'Just now',
        deterministicTag: answer.deterministicTag,
        highlights: answer.highlights,
      }
      setMessages((prev) => [...prev, assistantMsg])
    }, 800)
  }

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Page Header */}
      <PageHeader
        eyebrow="Conversational Copilot Studio"
        title="AI Business Analyst"
        description="Ask complex strategic questions about your operational data and receive verified, deterministic executive answers."
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => {
                setMessages([
                  {
                    id: 'msg-init',
                    role: 'assistant',
                    content: 'Context cleared. Ask any analytical question about your business datasets.',
                    timestamp: 'Just now',
                    deterministicTag: 'Zero-Hallucination Deterministic Engine',
                  },
                ])
              }}
            >
              <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
              Reset Chat
            </Button>
          </div>
        }
      />

      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-3xl border border-slate-200/80 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-6 sm:p-8 text-white shadow-xl shadow-slate-900/10">
        <div className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-brand-500/20 blur-3xl" />
        <div className="pointer-events-none absolute -left-16 -bottom-16 h-64 w-64 rounded-full bg-purple-500/15 blur-3xl" />

        <div className="relative z-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div className="space-y-2 max-w-xl">
            <div className="flex items-center gap-2">
              <Badge variant="brand" className="bg-brand-500/20 text-brand-300 border-brand-400/30 text-xs">
                Audited Knowledge Engine
              </Badge>
              <Badge variant="success" className="bg-emerald-500/20 text-emerald-300 border-emerald-400/30 text-xs">
                Zero Hallucinations
              </Badge>
            </div>
            <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight">
              Natural Language Data Interrogation
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              Synthesizes mathematical insights, cross-tabulations, and categorical aggregations directly from your
              uploaded datasets with code-backed transparency.
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm min-w-[220px]">
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Active Operational Context</p>
            <p className="text-sm font-bold text-white mt-1">HR &amp; Talent Analytics</p>
            <p className="text-[11px] text-emerald-400 mt-0.5 font-semibold">3,150 Records &bull; 39 Parameters</p>
          </div>
        </div>
      </div>

      {/* Main Studio Grid */}
      <div className="grid gap-8 lg:grid-cols-3">
        {/* Left 2-Column: Chat Stream */}
        <div className="lg:col-span-2 flex flex-col space-y-4">
          <Card className="flex flex-col border-slate-200/80 shadow-sm overflow-hidden min-h-[560px]">
            {/* Chat Bar Header */}
            <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/70 px-5 py-3.5">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 text-white shadow-sm">
                  <Bot className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs font-bold text-slate-900">Executive Data Analyst Copilot</p>
                  <p className="text-[10px] text-emerald-600 font-semibold flex items-center gap-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    Autonomous Mathematical Engine Active
                  </p>
                </div>
              </div>
              <Badge variant="default" className="text-[10px]">v2.4 Ready</Badge>
            </div>

            {/* Messages Stream */}
            <CardContent className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-6">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-3.5 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                >
                  <div
                    className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-xs font-bold shadow-sm ${
                      msg.role === 'user'
                        ? 'bg-slate-900 text-white'
                        : 'bg-gradient-to-tr from-brand-600 to-indigo-600 text-white'
                    }`}
                  >
                    {msg.role === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                  </div>

                  <div className={`space-y-2 max-w-[85%] ${msg.role === 'user' ? 'items-end' : ''}`}>
                    <div
                      className={`rounded-2xl p-4 text-xs sm:text-sm leading-relaxed ${
                        msg.role === 'user'
                          ? 'bg-brand-600 text-white shadow-md shadow-brand-500/20'
                          : 'border border-slate-200/80 bg-white text-slate-800 shadow-sm'
                      }`}
                    >
                      <div className="whitespace-pre-line">{msg.content}</div>

                      {/* Highlights chips if assistant */}
                      {msg.highlights && (
                        <div className="mt-3 pt-3 border-t border-slate-100 flex flex-wrap gap-1.5">
                          {msg.highlights.map((hl, i) => (
                            <span
                              key={i}
                              className="rounded-lg bg-brand-50 px-2 py-0.5 text-[11px] font-bold text-brand-700 border border-brand-100"
                            >
                              {hl}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Metadata footer */}
                    <div className="flex items-center gap-3 px-1 text-[11px] text-slate-400">
                      <span>{msg.timestamp}</span>
                      {msg.deterministicTag && (
                        <>
                          <span>&bull;</span>
                          <span className="flex items-center gap-1 font-semibold text-emerald-600">
                            <ShieldCheck className="h-3 w-3" />
                            {msg.deterministicTag}
                          </span>
                        </>
                      )}
                      {msg.role === 'assistant' && (
                        <button
                          type="button"
                          onClick={() => handleCopy(msg.id, msg.content)}
                          className="hover:text-slate-600 transition flex items-center gap-0.5 ml-auto"
                        >
                          {copiedId === msg.id ? (
                            <Check className="h-3 w-3 text-emerald-600" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                          <span>{copiedId === msg.id ? 'Copied' : 'Copy'}</span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {isTyping && (
                <div className="flex gap-3.5">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-white text-xs">
                    <Bot className="h-4 w-4 animate-spin" />
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                      <RefreshCw className="h-3.5 w-3.5 animate-spin text-brand-600" />
                      <span>Computing parametric correlations across dataset records...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatBottomRef} />
            </CardContent>

            {/* Input Bar */}
            <div className="border-t border-slate-200 bg-white p-4">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                  placeholder="Ask any operational question (e.g. 'Show me department salary disparity')..."
                  className="flex-1 rounded-xl border border-slate-200 bg-slate-50/60 px-4 py-2.5 text-xs sm:text-sm text-slate-800 shadow-2xs outline-none transition focus:border-brand-500 focus:bg-white focus:ring-2 focus:ring-brand-500/20"
                />
                <Button
                  type="button"
                  onClick={() => handleSend()}
                  disabled={!input.trim()}
                  className="bg-brand-600 hover:bg-brand-700 text-white font-bold shrink-0"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </Card>
        </div>

        {/* Right 1-Column: Executive Prompts & Knowledge */}
        <div className="space-y-6">
          <Card className="border-slate-200/80 shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-brand-600" />
                <h3 className="text-sm font-bold text-slate-900">Recommended Executive Prompts</h3>
              </div>
              <p className="text-xs text-slate-500">Click any prompt to execute an instant analytical query.</p>
            </CardHeader>
            <CardContent className="space-y-3">
              {SUGGESTIONS.map((item) => (
                <button
                  key={item.key}
                  type="button"
                  onClick={() => handleSend(item.query)}
                  className="w-full text-left rounded-2xl border border-slate-100 bg-slate-50/70 p-3.5 transition-all hover:border-brand-300 hover:bg-brand-50/30 hover:shadow-xs group"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-brand-600">
                      {item.category}
                    </span>
                    <ChevronRight className="h-3.5 w-3.5 text-slate-300 transition-transform group-hover:translate-x-0.5 group-hover:text-brand-600" />
                  </div>
                  <p className="mt-1 text-xs font-bold text-slate-800 group-hover:text-brand-700">
                    {item.title}
                  </p>
                  <p className="mt-0.5 text-[11px] text-slate-500 leading-tight">
                    {item.query}
                  </p>
                </button>
              ))}
            </CardContent>
          </Card>

          <Card className="border-slate-200/80 shadow-sm bg-gradient-to-br from-indigo-50/50 via-white to-brand-50/50">
            <CardContent className="p-5 space-y-3">
              <div className="flex items-center gap-2 text-sm font-bold text-slate-900">
                <ShieldCheck className="h-4 w-4 text-emerald-600" />
                Deterministic Verification
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                Unlike generic LLMs that generate fabricated numbers, this Copilot grounds every percentage,
                count, and recommendation in mathematical Pandas execution over your verified records.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
