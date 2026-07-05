'use client'
import { useStore } from '@/store/useStore'
import { FURNITURE_OPTIONS } from '@/lib/types'

const CATEGORIES = ['Sleep', 'Seating', 'Work', 'Storage', 'Media', 'Light', 'Dining']

// FIX: accept startError prop to show API errors inline
export function FurnitureStep({
  onGenerate,
  startError,
}: {
  onGenerate: () => void
  startError?: string | null
}) {
  const { furniture, dimensions, setStep, toggleFurniture, setDimensions } = useStore()

  const canGenerate = furniture.length > 0

  return (
    <div className="min-h-screen pt-24 pb-16 px-6">
      <div className="max-w-4xl mx-auto">

        {/* Heading */}
        <div className="text-center mb-12" style={{ animation: 'slideUp 0.6s ease forwards' }}>
          <p className="text-gold/60 text-xs tracking-[0.3em] uppercase font-body mb-4">Step 3 of 3</p>
          <h1 className="font-display text-5xl md:text-6xl font-light text-marble leading-tight mb-4">
            Select Your<br />
            <span className="text-gold-gradient italic">Furniture</span>
          </h1>
          <p className="text-marble/40 font-body text-sm">
            Choose pieces to place. Our spatial AI prevents collisions automatically.
          </p>
        </div>

        {/* Error banner — shown if API call fails */}
        {startError && (
          <div
            className="mb-8 px-5 py-4 rounded-xl border border-red-500/30 bg-red-500/10 text-red-400 font-body text-sm"
            style={{ animation: 'fadeIn 0.3s ease forwards' }}
          >
            <span className="font-medium">Connection error: </span>{startError}
            <br />
            <span className="text-red-400/60 text-xs mt-1 block">
              Make sure the backend is running on port 8000 and try again.
            </span>
          </div>
        )}

        {/* Selected count */}
        {furniture.length > 0 && (
          <div className="flex justify-center mb-8" style={{ animation: 'fadeIn 0.3s ease forwards' }}>
            <div className="glass-card-gold px-5 py-2 flex items-center gap-3">
              <span className="w-6 h-6 rounded-full bg-gold text-obsidian text-xs flex items-center justify-center font-medium">
                {furniture.length}
              </span>
              <span className="text-gold/80 text-sm font-body">
                {furniture.join(' · ')}
              </span>
            </div>
          </div>
        )}

        {/* Furniture grid */}
        <div className="space-y-6 mb-10" style={{ animation: 'slideUp 0.6s ease 0.1s both' }}>
          {CATEGORIES.map((cat) => {
            const items = FURNITURE_OPTIONS.filter((f) => f.category === cat)
            if (!items.length) return null
            return (
              <div key={cat}>
                <p className="text-marble/25 text-xs tracking-[0.2em] uppercase font-body mb-3">{cat}</p>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
                  {items.map((item) => {
                    const selected = furniture.includes(item.id)
                    return (
                      <button
                        key={item.id}
                        onClick={() => toggleFurniture(item.id)}
                        className={`furniture-card py-4 px-3 flex flex-col items-center gap-2 group ${selected ? 'selected' : ''}`}
                      >
                        <span className={`text-3xl transition-transform duration-200 ${selected ? 'scale-110' : 'group-hover:scale-110'}`}>
                          {item.icon}
                        </span>
                        <span className="font-body text-xs text-marble/60">{item.label}</span>
                        {selected && <div className="w-1.5 h-1.5 rounded-full bg-gold" />}
                      </button>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </div>

        {/* Room Dimensions */}
        <div className="glass-card p-6 mb-10" style={{ animation: 'slideUp 0.6s ease 0.2s both' }}>
          <p className="text-marble/40 text-xs tracking-[0.2em] uppercase font-body mb-6">Room Dimensions</p>
          <div className="grid grid-cols-2 gap-8">
            <div>
              <div className="flex justify-between mb-2">
                <span className="font-body text-xs text-marble/50">Width</span>
                <span className="font-body text-xs text-gold">{dimensions.width_cm} cm</span>
              </div>
              <input
                type="range" min={150} max={1000} step={10}
                value={dimensions.width_cm}
                onChange={(e) => setDimensions(+e.target.value, dimensions.length_cm)}
              />
              <div className="flex justify-between mt-1">
                <span className="text-marble/20 text-[10px] font-body">1.5m</span>
                <span className="text-marble/20 text-[10px] font-body">10m</span>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-2">
                <span className="font-body text-xs text-marble/50">Length</span>
                <span className="font-body text-xs text-gold">{dimensions.length_cm} cm</span>
              </div>
              <input
                type="range" min={150} max={1000} step={10}
                value={dimensions.length_cm}
                onChange={(e) => setDimensions(dimensions.width_cm, +e.target.value)}
              />
              <div className="flex justify-between mt-1">
                <span className="text-marble/20 text-[10px] font-body">1.5m</span>
                <span className="text-marble/20 text-[10px] font-body">10m</span>
              </div>
            </div>
          </div>
          <div className="mt-6 flex justify-center">
            <div className="relative" style={{ width: '140px', height: `${Math.min(140, 140 * (dimensions.length_cm / dimensions.width_cm))}px` }}>
              <div className="absolute inset-0 border border-gold/30 rounded" style={{ background: 'rgba(201,168,76,0.04)' }} />
              <span className="absolute top-1 right-1 text-[9px] text-gold/30 font-body">{dimensions.width_cm}×{dimensions.length_cm}</span>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between" style={{ animation: 'slideUp 0.6s ease 0.3s both' }}>
          <button
            onClick={() => setStep('style')}
            className="px-6 py-3 rounded-xl border border-white/10 text-marble/50 text-sm font-body hover:border-white/20 hover:text-marble/70 transition-all duration-200"
          >
            ← Back
          </button>
          <button
            onClick={onGenerate}
            disabled={!canGenerate}
            className={`btn-gold px-12 py-4 rounded-2xl text-sm font-body tracking-wide transition-all duration-300 ${
              canGenerate ? 'opacity-100 hover:scale-105' : 'opacity-30 cursor-not-allowed'
            }`}
          >
            ✦ Generate Design
          </button>
        </div>
      </div>
    </div>
  )
}
