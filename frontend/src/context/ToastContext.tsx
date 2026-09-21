import React, { createContext, useContext, useState, useCallback } from 'react'
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from 'lucide-react'
import { cn } from '../lib/utils'

export type ToastType = 'success' | 'error' | 'info' | 'warning'

export interface ToastItem {
  id: string
  type: ToastType
  title: string
  message?: string
  duration?: number
}

interface ToastContextType {
  toast: {
    success: (title: string, message?: string, duration?: number) => void
    error: (title: string, message?: string, duration?: number) => void
    info: (title: string, message?: string, duration?: number) => void
    warning: (title: string, message?: string, duration?: number) => void
  }
  dismiss: (id: string) => void
}

const ToastContext = createContext<ToastContextType | undefined>(undefined)

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const addToast = useCallback(
    (type: ToastType, title: string, message?: string, duration = 4000) => {
      const id = `${Date.now()}-${Math.random().toString(36).substring(2, 7)}`
      setToasts((prev) => [...prev, { id, type, title, message, duration }])

      if (duration > 0) {
        setTimeout(() => {
          setToasts((prev) => prev.filter((t) => t.id !== id))
        }, duration)
      }
    },
    []
  )

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const toast = {
    success: (title: string, message?: string, duration?: number) =>
      addToast('success', title, message, duration),
    error: (title: string, message?: string, duration?: number) =>
      addToast('error', title, message, duration),
    info: (title: string, message?: string, duration?: number) =>
      addToast('info', title, message, duration),
    warning: (title: string, message?: string, duration?: number) =>
      addToast('warning', title, message, duration),
  }

  return (
    <ToastContext.Provider value={{ toast, dismiss }}>
      {children}
      {/* Fixed Toast Container */}
      <div
        className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none px-4 sm:px-0"
        aria-live="polite"
        role="status"
      >
        {toasts.map((t) => {
          const isSuccess = t.type === 'success'
          const isError = t.type === 'error'
          const isWarning = t.type === 'warning'

          const Icon = isSuccess
            ? CheckCircle2
            : isError
            ? AlertCircle
            : isWarning
            ? AlertTriangle
            : Info

          const iconColor = isSuccess
            ? 'text-emerald-500'
            : isError
            ? 'text-rose-500'
            : isWarning
            ? 'text-amber-500'
            : 'text-brand-500'

          const borderColor = isSuccess
            ? 'border-emerald-200 dark:border-emerald-900/60'
            : isError
            ? 'border-rose-200 dark:border-rose-900/60'
            : isWarning
            ? 'border-amber-200 dark:border-amber-900/60'
            : 'border-border'

          return (
            <div
              key={t.id}
              className={cn(
                'pointer-events-auto flex items-start gap-3 rounded-2xl border p-4 shadow-lg backdrop-blur-md transition-all duration-300 animate-slide-up bg-surface-raised/95 text-text-primary',
                borderColor
              )}
            >
              <Icon className={cn('h-5 w-5 shrink-0 mt-0.5', iconColor)} />
              <div className="min-w-0 flex-1 space-y-0.5">
                <p className="text-sm font-semibold text-text-primary leading-snug">{t.title}</p>
                {t.message && (
                  <p className="text-xs text-text-secondary leading-relaxed">{t.message}</p>
                )}
              </div>
              <button
                type="button"
                onClick={() => dismiss(t.id)}
                className="shrink-0 rounded-lg p-1 text-text-muted hover:text-text-primary hover:bg-surface-sunken transition-colors cursor-pointer"
                aria-label="Dismiss notification"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}
