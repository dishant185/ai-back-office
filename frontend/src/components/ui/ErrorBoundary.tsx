import React, { Component, type ReactNode } from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'
import { Button } from './Button'
import { Card, CardContent } from './Card'

interface Props {
  children: ReactNode
  fallbackTitle?: string
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  public handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  public render() {
    if (this.state.hasError) {
      return (
        <Card className="border-rose-200 dark:border-rose-900/60 bg-rose-50/50 dark:bg-rose-950/20 p-6 shadow-xs my-6">
          <CardContent className="space-y-4 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-100 dark:bg-rose-900/40 text-rose-600 dark:text-rose-400">
              <AlertCircle className="h-6 w-6" />
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-bold text-rose-900 dark:text-rose-100">
                {this.props.fallbackTitle || 'Rendering Error'}
              </h3>
              <p className="text-xs text-rose-700 dark:text-rose-300 leading-relaxed max-w-md mx-auto">
                {this.state.error?.message || 'An unexpected rendering error occurred while rendering this section.'}
              </p>
            </div>
            <div className="pt-2 flex justify-center">
              <Button
                variant="secondary"
                size="sm"
                onClick={this.handleReset}
                className="gap-1.5"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                Try Reloading View
              </Button>
            </div>
          </CardContent>
        </Card>
      )
    }

    return this.props.children
  }
}
