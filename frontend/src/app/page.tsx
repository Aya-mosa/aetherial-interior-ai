'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useStore } from '@/store/useStore'
import { api } from '@/lib/api'
import { Navbar } from '@/components/layout/Navbar'
import { AmbientBackground } from '@/components/layout/AmbientBackground'
import { UploadStep } from '@/components/panels/UploadStep'
import { StyleStep } from '@/components/panels/StyleStep'
import { FurnitureStep } from '@/components/panels/FurnitureStep'
import { GeneratingStep } from '@/components/panels/GeneratingStep'
import ResultStep from '@/components/panels/ResultStep'
import { AIAssistant } from '@/components/panels/AIAssistant'
import type { PipelineStatus } from '@/lib/types'


const POLL_INTERVAL = 2500

export default function Home() {
  const {
    step, sessionId, pipeline,
    setStep, setPipeline,
    roomImage, roomType, style, furniture, colorPalette, aiMode, dimensions,
    setSessionId, isAssistantOpen,
  } = useStore()

  // FIX 1: use a ref so the setInterval callback always sees the latest
  // sessionId even before React re-renders (avoids the race condition)
  const sessionIdRef = useRef<string | null>(sessionId ?? null)
  const pollRef      = useRef<NodeJS.Timeout | null>(null)
  const [startError, setStartError] = useState<string | null>(null)

  // Keep ref in sync with Zustand store
  useEffect(() => {
    sessionIdRef.current = sessionId ?? null
  }, [sessionId])

  // ── Poll pipeline status ─────────────────────────────────────
  const pollStatus = useCallback(async () => {
    const sid = sessionIdRef.current
    if (!sid) return   // session not created yet — skip this tick

    try {
      const status: PipelineStatus = await api.getStatus(sid)
      setPipeline(status)

      if (status.status === 'done') {
        if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
        setStep('result')
      } else if (status.status === 'failed') {
        if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
        setStep('result')   // ResultStep handles error display
      }
    } catch (e) {
      console.error('[poll] Error:', e)
    }
  }, [setPipeline, setStep])

  // FIX 2: start polling as soon as step becomes 'generating'
  // (session_id may arrive a moment later — that's fine, the ref catches it)
  useEffect(() => {
    if (step !== 'generating') return
    if (pollRef.current) clearInterval(pollRef.current)
    pollStatus()   // immediate first call
    pollRef.current = setInterval(pollStatus, POLL_INTERVAL)
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [step, pollStatus])

  // ── Start pipeline ───────────────────────────────────────────
  const handleStartGeneration = useCallback(async () => {
    if (!roomImage || !style || furniture.length === 0) return

    setStartError(null)
    setStep('generating')  // show loading UI immediately

    try {
      const session = await api.startDesign({
        image: roomImage, roomType, style, furniture,
        dimensions, colorPalette, aiMode, numVariations: 3,
      })

      // FIX 3: update the ref BEFORE setSessionId so the already-running
      // interval picks up the new ID without waiting for a React re-render
      sessionIdRef.current = session.session_id
      setSessionId(session.session_id)

    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e)
      console.error('[start] Failed:', msg)
      setStartError(msg)
      setStep('furniture')  // go back so user can retry
    }
  }, [roomImage, roomType, style, furniture, dimensions, colorPalette, aiMode, setStep, setSessionId])

  return (
    <main className="min-h-screen relative overflow-x-hidden">
      <AmbientBackground />
      <Navbar />

      <div className="relative z-10">
        {step === 'upload'     && <UploadStep />}
        {step === 'style'      && <StyleStep />}
        {step === 'furniture'  && (
          <FurnitureStep onGenerate={handleStartGeneration} startError={startError} />
        )}
        {step === 'generating' && <GeneratingStep />}
        {step === 'result'     && <ResultStep />}
      </div>

      {(step === 'generating' || step === 'result') && sessionId && isAssistantOpen && (
        <AIAssistant sessionId={sessionId} />
      )}

      {step === 'result' && sessionId && <AssistantToggle />}
    </main>
  )
}

function AssistantToggle() {
  const { isAssistantOpen, toggleAssistant } = useStore()
  return (
    <button
      onClick={toggleAssistant}
      className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full btn-gold shadow-gold-glow flex items-center justify-center text-xl transition-all duration-300 hover:scale-110"
      title={isAssistantOpen ? 'Close Assistant' : 'Open AI Assistant'}
    >
      {isAssistantOpen ? '✕' : '✦'}
    </button>
  )
}
