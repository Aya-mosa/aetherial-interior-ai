'use client'
import { useStore } from '@/store/useStore'
import { STYLE_OPTIONS } from '@/lib/types'
import type { DesignStyle, ColorPalette, AIMode } from '@/lib/types'

const COLOR_PALETTES: { id: ColorPalette; label: string; swatches: string[] }[] = [
  { id: 'Warm Woods & Neutrals', label: 'Warm Woods', swatches: ['#8B6F47', '#C4A97A', '#E8DDD0', '#6B5344'] },
  { id: 'Dark Obsidian & Neon',  label: 'Obsidian Neon', swatches: ['#0A0A0B', '#1A1A2E', '#FF0080', '#00FFE0'] },
  { id: 'Cool Coastal Blues',    label: 'Coastal Blue', swatches: ['#B8D4E8', '#7BA8C4', '#2C5F7A', '#E8F4F8'] },
  { id: 'Monochrome Slate',      label: 'Monochrome', swatches: ['#1C1C1E', '#3A3A3C', '#8E8E93', '#F2F2F7'] },
  { id: 'Earthy Tones',          label: 'Earthy', swatches: ['#6B4C2A', '#A0785A', '#C9A880', '#E8D5B7'] },
]

export function StyleStep() {
  const { style, colorPalette, aiMode, setStyle, setColorPalette, setAIMode, setStep } = useStore()

  return (
    <div className="min-h-screen pt-24 pb-16 px-6">
      <div className="max-w-5xl mx-auto">
        {/* Heading */}
        <div className="text-center mb-12" style={{ animation: 'slideUp 0.6s ease forwards' }}>
          <p className="text-gold/60 text-xs tracking-[0.3em] uppercase font-body mb-4">Step 2 of 3</p>
          <h1 className="font-display text-5xl md:text-6xl font-light text-marble leading-tight mb-4">
            Choose Your<br />
            <span className="text-gold-gradient italic">Design Language</span>
          </h1>
          <p className="text-marble/40 font-body text-sm">
            Each style carries its own spatial philosophy and material palette.
          </p>
        </div>

        {/* Style cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12" style={{ animation: 'slideUp 0.6s ease 0.1s both' }}>
          {STYLE_OPTIONS.map((s, i) => (
            <button
              key={s.id}
              onClick={() => setStyle(s.id)}
              className={`style-card text-left overflow-hidden transition-all duration-300 ${style === s.id ? 'selected' : ''}`}
              style={{ animationDelay: `${i * 0.05}s` }}
            >
              {/* Color block */}
              <div
                className="h-28 relative overflow-hidden"
                style={{ background: s.color }}
              >
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-4xl opacity-30">{s.emoji}</span>
                </div>
                <div
                  className="absolute bottom-0 left-0 right-0 h-12"
                  style={{ background: `linear-gradient(transparent, ${s.color})` }}
                />
                <div
                  className="absolute top-3 right-3 w-3 h-3 rounded-full"
                  style={{ background: s.accent, boxShadow: `0 0 10px ${s.accent}80` }}
                />
                {style === s.id && (
                  <div className="absolute top-3 left-3 w-5 h-5 rounded-full bg-gold flex items-center justify-center text-obsidian text-xs">
                    ✓
                  </div>
                )}
              </div>
              {/* Label */}
              <div className="p-3 bg-obsidian-700">
                <p className="font-body text-sm font-medium text-marble">{s.label}</p>
                <p className="font-body text-xs text-marble/40 mt-0.5">{s.description}</p>
              </div>
            </button>
          ))}
        </div>

        {/* Color Palette */}
        <div className="glass-card p-6 mb-8" style={{ animation: 'slideUp 0.6s ease 0.2s both' }}>
          <p className="text-marble/40 text-xs tracking-[0.2em] uppercase font-body mb-5">Color Palette</p>
          <div className="flex flex-wrap gap-3">
            {COLOR_PALETTES.map((cp) => (
              <button
                key={cp.id}
                onClick={() => setColorPalette(cp.id)}
                className={`flex items-center gap-3 px-4 py-2.5 rounded-xl border transition-all duration-200 ${
                  colorPalette === cp.id
                    ? 'border-gold/50 bg-gold/10'
                    : 'border-white/07 bg-white/02 hover:border-white/15'
                }`}
              >
                <div className="flex gap-1">
                  {cp.swatches.map((sw, i) => (
                    <div key={i} className="w-4 h-4 rounded-full" style={{ background: sw }} />
                  ))}
                </div>
                <span className="font-body text-xs text-marble/60">{cp.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* AI Mode */}
        <div className="glass-card p-6 mb-10" style={{ animation: 'slideUp 0.6s ease 0.25s both' }}>
          <p className="text-marble/40 text-xs tracking-[0.2em] uppercase font-body mb-5">AI Creativity Mode</p>
          <div className="flex gap-4">
            {(['strict', 'creative'] as AIMode[]).map((m) => (
              <button
                key={m}
                onClick={() => setAIMode(m)}
                className={`flex-1 py-4 px-5 rounded-xl border text-left transition-all duration-200 ${
                  aiMode === m
                    ? 'border-gold/50 bg-gold/10'
                    : 'border-white/07 bg-white/02 hover:border-white/15'
                }`}
              >
                <p className="font-body text-sm font-medium text-marble capitalize mb-1">{m}</p>
                <p className="font-body text-xs text-marble/40">
                  {m === 'strict' ? 'Only your selected furniture, no additions' : 'AI adds complementary décor & accents'}
                </p>
              </button>
            ))}
          </div>
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between" style={{ animation: 'slideUp 0.6s ease 0.3s both' }}>
          <button
            onClick={() => setStep('upload')}
            className="px-6 py-3 rounded-xl border border-white/10 text-marble/50 text-sm font-body hover:border-white/20 hover:text-marble/70 transition-all duration-200"
          >
            ← Back
          </button>
          <button
            onClick={() => setStep('furniture')}
            disabled={!style}
            className={`btn-gold px-10 py-4 rounded-2xl text-sm font-body tracking-wide transition-all duration-300 ${
              style ? 'opacity-100' : 'opacity-30 cursor-not-allowed'
            }`}
          >
            Select Furniture →
          </button>
        </div>
      </div>
    </div>
  )
}
