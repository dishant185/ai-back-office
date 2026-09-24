import { createContext, useContext, useState, type ReactNode } from 'react'
import { EvidenceDrawer, type EvidenceData } from '../components/ui/EvidenceDrawer'

interface EvidenceContextType {
  openEvidence: (data: EvidenceData) => void
  closeEvidence: () => void
  isOpen: boolean
  activeEvidence: EvidenceData | null
}

const EvidenceContext = createContext<EvidenceContextType | undefined>(undefined)

export function EvidenceProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false)
  const [activeEvidence, setActiveEvidence] = useState<EvidenceData | null>(null)

  const openEvidence = (data: EvidenceData) => {
    setActiveEvidence(data)
    setIsOpen(true)
  }

  const closeEvidence = () => {
    setIsOpen(false)
  }

  return (
    <EvidenceContext.Provider value={{ openEvidence, closeEvidence, isOpen, activeEvidence }}>
      {children}
      <EvidenceDrawer isOpen={isOpen} onClose={closeEvidence} evidence={activeEvidence} />
    </EvidenceContext.Provider>
  )
}

export function useEvidence() {
  const ctx = useContext(EvidenceContext)
  if (!ctx) {
    throw new Error('useEvidence must be used within an EvidenceProvider')
  }
  return ctx
}
