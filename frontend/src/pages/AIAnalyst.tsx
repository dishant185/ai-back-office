import { useState } from 'react'
import {
  Bot,
  Lightbulb,
  MessageSquare,
  Send,
  Sparkles,
  User,
} from 'lucide-react'

import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardContent } from '../components/ui/Card'
import { PageHeader } from '../components/ui/PageHeader'

const suggestedQuestions = [
  'What were our top revenue drivers last quarter?',
  'Show me expense anomalies in the data',
  'Compare monthly growth trends',
  'Which categories have the highest margins?',
]

interface Message {
  role: 'user' | 'assistant'
  content: string
}

function AIAnalyst() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content:
        "Hello! I'm your AI business analyst. Upload a dataset first, then ask me anything about your numbers — trends, anomalies, forecasts, and more.",
    },
  ])

  const handleSend = () => {
    if (!input.trim()) return

    setMessages((prev) => [
      ...prev,
      { role: 'user', content: input.trim() },
      {
        role: 'assistant',
        content:
          'AI analysis will be available once you upload a dataset. Head to the Upload page to import your business data, then come back to ask questions.',
      },
    ])
    setInput('')
  }

  const handleSuggestion = (question: string) => {
    setInput(question)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="AI Analyst"
        title="Ask Your Data"
        description="Chat with an AI analyst to uncover insights, trends, and recommendations from your business data."
        actions={
          <Badge variant="brand" dot>
            <Sparkles className="mr-1 h-3 w-3" />
            AI Powered
          </Badge>
        }
      />

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Chat area */}
        <Card className="flex flex-col overflow-hidden lg:col-span-2">
          <div className="flex items-center gap-3 border-b border-slate-100 bg-slate-50/80 px-5 py-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl gradient-brand shadow-sm">
              <Bot className="h-4 w-4 text-white" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-800">AI Business Analyst</p>
              <p className="text-xs text-slate-500">Powered by LLM · Phase 2</p>
            </div>
          </div>

          <CardContent className="flex flex-1 flex-col p-0">
            <div className="flex-1 space-y-4 overflow-y-auto p-5" style={{ minHeight: '360px' }}>
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                >
                  <div
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl ${
                      msg.role === 'user'
                        ? 'bg-slate-200 text-slate-600'
                        : 'gradient-brand text-white shadow-sm'
                    }`}
                  >
                    {msg.role === 'user' ? (
                      <User className="h-4 w-4" />
                    ) : (
                      <Bot className="h-4 w-4" />
                    )}
                  </div>
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-brand-600 text-white'
                        : 'border border-slate-100 bg-white text-slate-700 shadow-sm'
                    }`}
                  >
                    {msg.content}
                  </div>
                </div>
              ))}
            </div>

            <div className="border-t border-slate-100 p-4">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                  placeholder="Ask about your business data..."
                  className="flex-1 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700 shadow-sm outline-none transition focus:border-brand-300 focus:ring-2 focus:ring-brand-500/20"
                />
                <Button type="button" onClick={handleSend} disabled={!input.trim()}>
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Suggestions sidebar */}
        <div className="space-y-4">
          <Card>
            <CardContent className="p-5">
              <div className="mb-4 flex items-center gap-2">
                <Lightbulb className="h-4 w-4 text-amber-500" />
                <h3 className="text-sm font-bold text-slate-800">Suggested Questions</h3>
              </div>
              <div className="space-y-2">
                {suggestedQuestions.map((q) => (
                  <button
                    key={q}
                    type="button"
                    onClick={() => handleSuggestion(q)}
                    className="w-full rounded-xl border border-slate-100 bg-slate-50/80 px-3 py-2.5 text-left text-xs font-medium text-slate-600 transition hover:border-brand-200 hover:bg-brand-50/30 hover:text-brand-700"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-5">
              <div className="mb-3 flex items-center gap-2">
                <MessageSquare className="h-4 w-4 text-brand-500" />
                <h3 className="text-sm font-bold text-slate-800">How it works</h3>
              </div>
              <ol className="space-y-3 text-xs text-slate-500">
                <li className="flex gap-2">
                  <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-100 text-[10px] font-bold text-brand-700">
                    1
                  </span>
                  Upload your CSV or Excel data
                </li>
                <li className="flex gap-2">
                  <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-100 text-[10px] font-bold text-brand-700">
                    2
                  </span>
                  Ask natural language questions
                </li>
                <li className="flex gap-2">
                  <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-100 text-[10px] font-bold text-brand-700">
                    3
                  </span>
                  Get AI-generated insights & charts
                </li>
              </ol>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default AIAnalyst
