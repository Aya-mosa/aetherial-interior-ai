'use client'
import { useStore } from '@/store/useStore'
import type { Step } from '@/lib/types'

const STEPS: { id: Step; label: string }[] = [
  { id: 'upload',     label: 'Upload'    },
  { id: 'style',      label: 'Style'     },
  { id: 'furniture',  label: 'Furnish'   },
  { id: 'generating', label: 'Generate'  },
  { id: 'result',     label: 'Result'    },
]

const ORDER: Step[] = ['upload', 'style', 'furniture', 'generating', 'result']

export function Navbar() {
  const { step } = useStore()
  const currentIdx = ORDER.indexOf(step)

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 px-6 py-4">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 relative">
            <div className="absolute inset-0 rounded-full border border-gold/40 animate-spin-slow" />
            <div className="absolute inset-[3px] rounded-full bg-gold/10 flex items-center justify-center">
              <span className="text-gold text-xs">✦</span>
            </div>
          </div>
          <span className="font-display text-xl font-light tracking-widest text-marble">
            AETHERIAL
          </span>
        </div>

        {/* Step indicators */}
        <div className="hidden md:flex items-center gap-1">
          {STEPS.map((s, i) => {
            const done = i < currentIdx
            const active = i === currentIdx
            const future = i > currentIdx
            return (
              <div key={s.id} className="flex items-center gap-1">
                <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs transition-all duration-300 ${
                  active  ? 'bg-gold/15 text-gold border border-gold/30' :
                  done    ? 'text-marble/40 border border-transparent' :
                  'text-marble/20 border border-transparent'
                }`}>
                  <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] ${
                    done ? 'bg-gold/30 text-gold' : active ? 'bg-gold text-obsidian' : 'bg-white/5'
                  }`}>
                    {done ? '✓' : i + 1}
                  </span>
                  <span className="font-body">{s.label}</span>
                </div>
                {i < STEPS.length - 1 && (
                  <div className={`w-4 h-px transition-colors duration-300 ${done || active ? 'bg-gold/30' : 'bg-white/10'}`} />
                )}
              </div>
            )
          })}
        </div>

        {/* Right pill */}
        <div className="glass-card px-4 py-2 text-xs text-marble/40 font-body">
          AI Interior Architect
        </div>
      </div>
    </nav>
  )
}
