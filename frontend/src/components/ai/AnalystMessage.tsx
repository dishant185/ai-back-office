/**
 * AnalystMessage — Conversational message bubble with natural Markdown,
 * tables, lists, and subtle source indicators.
 */
import { Bot, Check, ChevronDown, ChevronUp, Copy, ShieldCheck, User } from 'lucide-react'
import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { ChatMessage } from '../../types/ai'
import { VerificationBadge } from '../ui/VerificationBadge'

interface AnalystMessageProps {
  message: ChatMessage
}

export function AnalystMessage({ message }: AnalystMessageProps) {
  const [copied, setCopied] = useState(false)
  const [showSources, setShowSources] = useState(false)
  const isUser = message.role === 'user'

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const hasSources = Boolean(message.sources && message.sources.length > 0 && !isUser)

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-white ${
          isUser
            ? 'bg-slate-800 shadow-sm'
            : 'bg-gradient-to-tr from-brand-600 to-indigo-500 shadow-sm'
        }`}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      {/* Message Box */}
      <div className={`space-y-1.5 max-w-[85%] ${isUser ? 'items-end' : ''}`}>
        <div
          className={`rounded-2xl p-4 text-sm leading-relaxed ${
            isUser
              ? 'bg-brand-600 text-white shadow-sm'
              : 'border border-border bg-surface-raised text-text-primary shadow-xs'
          }`}
        >
          {isUser ? (
            <div className="whitespace-pre-line font-normal">{message.content}</div>
          ) : (
            <>
              <div className="mb-2.5 flex items-center justify-between gap-2 border-b border-border pb-2">
                <VerificationBadge status={message.ai_status} size="sm" />
              </div>
              <div className="prose prose-sm max-w-none text-text-primary dark:prose-invert prose-headings:font-semibold prose-headings:text-text-primary prose-headings:mt-3 prose-headings:mb-1.5 prose-p:my-1.5 prose-ul:my-1.5 prose-li:my-0.5 prose-table:my-2.5 prose-th:bg-surface-sunken prose-th:px-3 prose-th:py-1.5 prose-td:px-3 prose-td:py-1.5 prose-table:border prose-table:border-border">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              </div>
            </>
          )}

          {/* Subtle Verified Source Indicator (Modern AI style) */}
          {hasSources && (
            <div className="mt-3 pt-2.5 border-t border-slate-100 flex flex-col gap-1.5">
              <button
                type="button"
                onClick={() => setShowSources((prev) => !prev)}
                className="inline-flex items-center gap-1.5 text-[11px] font-medium text-emerald-700 hover:text-emerald-800 transition w-fit"
              >
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                <span>✓ Based on verified dataset data</span>
                {showSources ? (
                  <ChevronUp className="h-3 w-3 text-emerald-500" />
                ) : (
                  <ChevronDown className="h-3 w-3 text-emerald-500" />
                )}
              </button>

              {showSources && (() => {
                const firstSrc = typeof message.sources![0] === 'object' ? message.sources![0] : null
                const datasetName = firstSrc?.dataset || 'Dataset'
                const operationName = firstSrc?.operation || 'Analytical Query'
                const statusName = firstSrc?.status || 'Verified'
                const fieldNames = message.sources!.map((s) => {
                  if (typeof s === 'string') return s
                  return s.field || s.metric || s.label
                }).filter(Boolean).join(', ') || 'Dataset attributes'

                return (
                  <div className="mt-1.5 rounded-lg border border-emerald-200/70 bg-emerald-50/60 p-3 text-xs text-slate-700 animate-fade-in space-y-2">
                    <div className="grid grid-cols-2 gap-2 text-[11px]">
                      <div>
                        <span className="font-semibold text-slate-500 block">Dataset:</span>
                        <span className="text-slate-800 font-medium">{datasetName}</span>
                      </div>
                      <div>
                        <span className="font-semibold text-slate-500 block">Fields:</span>
                        <span className="text-slate-800 font-medium">{fieldNames}</span>
                      </div>
                      <div>
                        <span className="font-semibold text-slate-500 block">Operation:</span>
                        <span className="font-mono text-[10px] text-emerald-800 font-semibold bg-emerald-100/60 px-1.5 py-0.5 rounded inline-block">
                          {operationName}
                        </span>
                      </div>
                      <div>
                        <span className="font-semibold text-slate-500 block">Status:</span>
                        <span className="text-emerald-700 font-semibold inline-flex items-center gap-1">
                          <Check className="h-3 w-3" /> {statusName}
                        </span>
                      </div>
                    </div>
                  </div>
                )
              })()}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center gap-3 px-1 text-[11px] text-slate-400">
          <span>{message.timestamp}</span>
          {!isUser && (
            <button
              type="button"
              onClick={handleCopy}
              className="ml-auto flex items-center gap-1 hover:text-slate-600 transition"
              title="Copy answer"
            >
              {copied ? (
                <>
                  <Check className="h-3 w-3 text-emerald-600" />
                  <span className="text-emerald-600">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="h-3 w-3" />
                  <span>Copy</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

