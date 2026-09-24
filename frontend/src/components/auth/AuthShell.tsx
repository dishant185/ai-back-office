import React from 'react'
import { AuthBrandPanel } from './AuthBrandPanel'

interface AuthShellProps {
  mode: 'login' | 'register' | 'forgot'
  children: React.ReactNode
}

export function AuthShell({ mode, children }: AuthShellProps) {
  return (
    <div className="min-h-screen w-full flex flex-col lg:flex-row bg-[#F3F5F1] dark:bg-[#0E1416] text-[#11181B] dark:text-[#EEF2EE]">
      {/* Left Brand Panel: 50% on desktop, dark ink background */}
      <div className="w-full lg:w-1/2 shrink-0">
        <AuthBrandPanel mode={mode} />
      </div>

      {/* Right Form Workspace: 50% on desktop, paper background, centered form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-10 lg:p-16 bg-[#F3F5F1] dark:bg-[#141C1F]">
        <div className="w-full max-w-[420px]">{children}</div>
      </div>
    </div>
  )
}
