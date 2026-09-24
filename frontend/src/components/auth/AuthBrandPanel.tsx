import { ArrowDown, CheckCircle2, ShieldCheck, Sparkles } from 'lucide-react'
import { NoveraLogo } from '../brand/NoveraLogo'

export interface AuthBrandPanelProps {
  mode: 'login' | 'register' | 'forgot'
}

export function AuthBrandPanel({ mode }: AuthBrandPanelProps) {
  return (
    <div className="flex h-full w-full flex-col justify-between bg-[#11181B] p-8 sm:p-12 lg:p-14 text-[#EEF2EE] border-b lg:border-b-0 lg:border-r border-[#2B3538] select-none">
      {/* Top Brand Header */}
      <div>
        <div className="mb-8">
          <NoveraLogo variant="full" size="md" theme="dark" />
        </div>

        {mode === 'register' ? (
          <>
            <h1 className="font-sans text-2xl sm:text-3xl font-bold tracking-tight text-white leading-tight">
              Create your Novera workspace.
            </h1>
            <p className="mt-3 text-sm text-[#AAB5AF] leading-relaxed max-w-md">
              Bring your business data into one verified workspace for analysis, reporting, and decision-making.
            </p>
          </>
        ) : (
          <>
            <h1 className="font-sans text-2xl sm:text-3xl font-bold tracking-tight text-white leading-tight">
              Business intelligence
              <br />
              built on verified data.
            </h1>
            <p className="mt-3 text-sm text-[#AAB5AF] leading-relaxed max-w-md">
              Understand your business data, verify calculations through deterministic pipelines, and act with operational confidence.
            </p>
          </>
        )}
      </div>

      {/* Trust & Architecture Preview (Zero mock numerical data) */}
      <div className="my-8 max-w-md">
        {mode === 'register' ? (
          /* Register: Structured Data Flow Pipeline */
          <div className="rounded-[2px] border border-[#2B3538] bg-[#141C1F] p-4 text-xs font-sans">
            <div className="flex items-center justify-between border-b border-[#2B3538] pb-2.5 mb-3">
              <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-[#AAB5AF]">
                DATA PIPELINE
              </span>
              <span className="font-mono text-[10px] text-[#4FAF87] flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3 text-[#4FAF87]" />
                Automated Verification
              </span>
            </div>

            <div className="space-y-2 font-mono text-[11px]">
              <div className="flex items-center justify-between py-1.5 px-2.5 rounded-[2px] bg-white/[0.02] border border-[#2B3538]/50">
                <span className="text-[#AAB5AF]">DATA INTAKE</span>
                <span className="text-white font-medium">CSV / Excel Ingestion</span>
              </div>

              <div className="flex justify-center text-[#66716C] py-0.5">
                <ArrowDown className="h-3 w-3" />
              </div>

              <div className="flex items-center justify-between py-1.5 px-2.5 rounded-[2px] bg-[#176B50]/10 border border-[#176B50]/30">
                <span className="text-[#AAB5AF]">VERIFIED LEDGER</span>
                <span className="text-[#4FAF87] font-semibold">Deterministic Math</span>
              </div>

              <div className="flex justify-center text-[#66716C] py-0.5">
                <ArrowDown className="h-3 w-3" />
              </div>

              <div className="flex items-center justify-between py-1.5 px-2.5 rounded-[2px] bg-white/[0.02] border border-[#2B3538]/50">
                <span className="text-[#AAB5AF]">AUDIT &amp; INSIGHTS</span>
                <span className="text-white font-medium">Variance Analysis</span>
              </div>

              <div className="flex justify-center text-[#66716C] py-0.5">
                <ArrowDown className="h-3 w-3" />
              </div>

              <div className="flex items-center justify-between py-1.5 px-2.5 rounded-[2px] bg-[#A8792E]/10 border border-[#A8792E]/30">
                <span className="text-[#AAB5AF]">NOVERA ANALYST</span>
                <span className="text-[#D0A45C] font-semibold">Executive Intelligence</span>
              </div>
            </div>
          </div>
        ) : (
          /* Login & Forgot: Trust Architecture Pillars (No fake numerical data) */
          <div className="rounded-[2px] border border-[#2B3538] bg-[#141C1F] divide-y divide-[#2B3538]">
            <div className="p-4 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-[#AAB5AF]">
                  VERIFIED DATA INTEGRITY
                </span>
                <ShieldCheck className="h-3.5 w-3.5 text-[#4FAF87]" />
              </div>
              <p className="text-xs text-[#EEF2EE] font-medium leading-snug">
                Deterministic mathematical computations natively executed without probabilistic hallucination.
              </p>
            </div>

            <div className="p-4 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-[#AAB5AF]">
                  TRACEABLE LINEAGE
                </span>
                <span className="h-1.5 w-1.5 rounded-[1px] bg-[#4FAF87]" />
              </div>
              <p className="text-xs text-[#EEF2EE] font-medium leading-snug">
                Every executive metric, chart, and analytical variance connects directly to verified source records.
              </p>
            </div>

            <div className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-mono text-[10px] font-bold uppercase tracking-wider text-[#AAB5AF]">
                    NOVERA ANALYST
                  </p>
                  <p className="text-xs text-[#EEF2EE] mt-0.5 font-medium">
                    Autonomous Executive Intelligence
                  </p>
                </div>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-[2px] bg-[#A8792E]/15 border border-[#A8792E]/30 text-[10px] font-mono font-medium text-[#D0A45C]">
                  <Sparkles className="h-2.5 w-2.5" />
                  AI-assisted
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer Statement */}
      <div className="pt-4 border-t border-[#2B3538]/60 text-[11px] font-mono text-[#66716C]">
        <span>Novera Intelligence Operating System &bull; SOC-2 Type II Verified</span>
      </div>
    </div>
  )
}
