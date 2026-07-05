'use client'
import { useStore } from '@/store/useStore'
import { LOADING_STEPS } from '@/lib/types'

export function GeneratingStep() {
  const { pipeline, roomImageUrl, sessionId } = useStore()
  const progress    = pipeline?.progress_percent ?? 0
  const currentStep = pipeline?.current_step ?? ''
  const hasError    = pipeline?.status === 'failed'

  // Determine active agent index from progress or current_step label
  const activeByStep = LOADING_STEPS.findIndex(
    (s) => currentStep.toLowerCase().includes(s.key)
  )
  const activeByProgress = Math.min(
    Math.floor((progress / 100) * LOADING_STEPS.length),
    LOADING_STEPS.length - 1
  )
  const effectiveIdx = activeByStep >= 0 ? activeByStep : (progress > 0 ? activeByProgress : 0)

  return (
    <div className="min-h-screen pt-24 pb-16 px-6 flex flex-col items-center justify-center">
      <div className="max-w-xl w-full">

        {/* Pulsing ring */}
        <div className="flex justify-center mb-12">
          <div className="relative w-24 h-24">
            <div className="absolute inset-0 rounded-full border border-gold/20 animate-spin-slow" />
            <div className="absolute inset-2 rounded-full border border-gold/15"
              style={{ animation: 'spin-slow 5s linear infinite reverse' }} />
            <div className="absolute inset-4 rounded-full border border-gold/10 animate-spin-slow"
              style={{ animationDuration: '3s' }} />
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-8 h-8 rounded-full bg-gold/20 flex items-center justify-center"
                style={{ animation: 'pulse 2s ease-in-out infinite' }}>
                <span className="text-gold text-lg">✦</span>
              </div>
            </div>
          </div>
        </div>

        {/* Title */}
        <div className="text-center mb-10">
          <h2 className="font-display text-4xl font-light text-marble mb-3">
            {hasError ? 'Something went wrong' : 'Crafting Your Space'}
          </h2>
          <p className="text-marble/40 font-body text-sm">
            {hasError
              ? pipeline?.error ?? 'An error occurred in the pipeline.'
              : sessionId
                ? 'Six AI agents are working on your design.'
                : 'Connecting to the design pipeline…'
            }
          </p>
        </div>

        {/* Error detail */}
        {hasError && (
          <div className="mb-8 px-5 py-4 rounded-xl border border-red-500/30 bg-red-500/10 text-red-400 font-body text-sm">
            {pipeline?.error}
          </div>
        )}

        {/* Progress bar */}
        {!hasError && (
          <div className="mb-10">
            <div className="flex justify-between mb-2">
              <span className="font-body text-xs text-marble/40">Progress</span>
              <span className="font-body text-xs text-gold">{progress}%</span>
            </div>
            <div className="h-1 bg-white/5 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700 ease-out"
                style={{
                  width: `${Math.max(progress, sessionId ? 3 : 0)}%`,
                  background: 'linear-gradient(90deg, #9A7830, #C9A84C, #E8C96A)',
                  boxShadow: '0 0 12px rgba(201,168,76,0.5)',
                }}
              />
            </div>
          </div>
        )}

        {/* Agent steps */}
        {!hasError && (
          <div className="space-y-3">
            {LOADING_STEPS.map((step, i) => {
              const done    = i < effectiveIdx
              const active  = i === effectiveIdx
              return (
                <div
                  key={step.key}
                  className={`flex items-center gap-4 px-5 py-4 rounded-xl transition-all duration-500 ${
                    active ? 'glass-card-gold' : done ? 'glass-card opacity-40' : 'opacity-20'
                  }`}
                  style={{ transitionDelay: `${i * 0.05}s` }}
                >
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm flex-shrink-0 transition-all duration-300 ${
                    done   ? 'bg-gold/20 text-gold' :
                    active ? 'bg-gold text-obsidian' :
                    'bg-white/4 text-marble/20'
                  }`}>
                    {active ? (
                      <span style={{ animation: 'spin-slow 1s linear infinite', display: 'inline-block' }}>⟳</span>
                    ) : done ? (
                      <span>✓</span>
                    ) : (
                      <span>{step.icon}</span>
                    )}
                  </div>

                  <div className="flex-1">
                    <p className={`font-body text-sm font-medium transition-colors duration-300 ${
                      active ? 'text-gold' : done ? 'text-marble/40' : 'text-marble/20'
                    }`}>
                      {step.label}
                    </p>
                    <p className={`font-body text-xs transition-colors duration-300 ${
                      active ? 'text-gold/50' : 'text-marble/20'
                    }`}>
                      {step.agentLabel}
                    </p>
                  </div>

                  {active && (
                    <div className="flex gap-1">
                      {[0, 1, 2].map((d) => (
                        <div
                          key={d}
                          className="w-1.5 h-1.5 rounded-full bg-gold"
                          style={{ animation: `pulse 1.2s ease-in-out ${d * 0.2}s infinite` }}
                        />
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}

        {/* Room thumbnail */}
        {roomImageUrl && (
          <div className="mt-10 flex justify-center">
            <div className="glass-card p-2 rounded-xl">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={roomImageUrl}
                alt="Your room"
                className="w-32 h-20 object-cover rounded-lg opacity-60"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
