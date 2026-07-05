'use client'
import { useState, useRef, useCallback, useEffect } from 'react'
import { useStore } from '@/store/useStore'
import { api } from '@/lib/api'
import type { Agent2Output, FurniturePosition } from '@/lib/types'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

// ── Download helper (fixes cross-origin bug) ──────────────────────────────────
async function downloadBlob(url: string, filename: string) {
  try {
    // Ensure full URL (fix: relative paths like /outputs/... fail cross-origin)
    const fullUrl = url.startsWith('http') ? url : `${API_URL}${url}`
    const resp = await fetch(fullUrl, { mode: 'cors' })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const blob = await resp.blob()
    const a = Object.assign(document.createElement('a'), {
      href: URL.createObjectURL(blob),
      download: filename,
    })
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(a.href)
  } catch (e) {
    console.error('[Download] Failed:', e)
    // Fallback: open in new tab
    const fullUrl = url.startsWith('http') ? url : `${API_URL}${url}`
    window.open(fullUrl, '_blank')
  }
}

// ── Before/After slider (fixed: mouse + touch) ───────────────────────────────
function BeforeAfterSlider({ before, after }: { before: string; after: string }) {
  const [pos, setPos]   = useState(50)
  const ref             = useRef<HTMLDivElement>(null)
  const dragging        = useRef(false)

  const update = useCallback((clientX: number) => {
    const rect = ref.current?.getBoundingClientRect()
    if (!rect) return
    const pct = Math.max(0, Math.min(100, ((clientX - rect.left) / rect.width) * 100))
    setPos(pct)
  }, [])

  return (
    <div
      ref={ref}
      className="compare-container relative cursor-col-resize select-none"
      style={{ height: '420px' }}
      onMouseMove={(e) => { if (dragging.current) update(e.clientX) }}
      onMouseUp={()    => { dragging.current = false }}
      onMouseLeave={()  => { dragging.current = false }}
      // ── Touch events (mobile fix) ─────────────────────────────────────────
      onTouchStart={(e) => { dragging.current = true;  update(e.touches[0].clientX) }}
      onTouchMove={(e)  => {
        if (!dragging.current) return
        e.preventDefault()
        update(e.touches[0].clientX)
      }}
      onTouchEnd={()   => { dragging.current = false }}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={after}  alt="After"  className="absolute inset-0 w-full h-full object-cover" />
      <div
        className="absolute inset-0 overflow-hidden"
        style={{ clipPath: `inset(0 ${100 - pos}% 0 0)` }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={before} alt="Before" className="absolute inset-0 w-full h-full object-cover" />
      </div>
      <div
        className="absolute top-0 bottom-0 w-0.5 bg-white/80"
        style={{ left: `${pos}%`, transform: 'translateX(-50%)' }}
        onMouseDown={() => { dragging.current = true }}
        onTouchStart={() => { dragging.current = true }}
      >
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-white shadow-lg flex items-center justify-center">
          <span className="text-obsidian text-xs">⇔</span>
        </div>
      </div>
      <div className="absolute top-4 left-4 glass-card px-3 py-1 text-xs font-body text-marble/70">Before</div>
      <div className="absolute top-4 right-4 glass-card px-3 py-1 text-xs font-body text-gold/80">After</div>
    </div>
  )
}

// ── FloorPlanImage ─────────────────────────────────────────────────────────────
function FloorPlanImage({ canvasImagePath }: { canvasImagePath: string }) {
  const [state, setState] = useState<'loading' | 'ok' | 'error'>('loading')
  const src = `${API_URL}${canvasImagePath}`
  return (
    <div className="relative w-full min-h-[180px] flex items-center justify-center">
      {state === 'loading' && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-6 h-6 border border-gold/30 border-t-gold rounded-full animate-spin" />
        </div>
      )}
      {state === 'error' && (
        <div className="absolute inset-0 flex items-center justify-center text-marble/30 text-xs font-body">
          Floor plan unavailable
        </div>
      )}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={src}
        alt="Floor Plan"
        className={`w-full rounded transition-opacity duration-300 ${state === 'ok' ? 'opacity-100' : 'opacity-0'}`}
        onLoad={()  => setState('ok')}
        onError={() => setState('error')}
      />
    </div>
  )
}

// ── InteractiveCanvas (drag & drop) ───────────────────────────────────────────
interface DragState { id: string; startMouseX: number; startMouseY: number; startItemX: number; startItemZ: number }

function InteractiveCanvas({ layout }: { layout?: Agent2Output | null }) {
  const { sessionId, setPipeline, pipeline } = useStore()
  const [furniture, setFurniture]   = useState<FurniturePosition[]>([])
  const [selected,  setSelected]    = useState<string | null>(null)
  const [status, setStatus]         = useState<{saving:boolean; valid:boolean|null; issues:string[]}>({ saving:false, valid:null, issues:[] })
  const containerRef  = useRef<HTMLDivElement>(null)
  const dragRef       = useRef<DragState | null>(null)
  const saveTimer     = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [rerendering, setRerendering] = useState(false)

  useEffect(() => { if (layout?.furniture) setFurniture([...layout.furniture]) }, [layout])

  const W = layout?.room_dimensions?.width  || 400
  const L = layout?.room_dimensions?.length || 500
  const CANVAS_W = 380
  const CANVAS_H = Math.round((L / W) * CANVAS_W)
  const scaleX   = CANVAS_W / W
  const scaleY   = CANVAS_H / L

  const saveToBackend = useCallback((items: FurniturePosition[]) => {
    if (!sessionId) return
    if (saveTimer.current) clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(async () => {
      setStatus(v => ({ ...v, saving: true }))
      try {
        const res = await api.updateCanvas(sessionId, items)
        setStatus({ saving: false, valid: res.is_valid, issues: (res.issues as {description:string}[]).map(i=>i.description) })
        if (pipeline && res.updated_layout) setPipeline({ ...pipeline, agent2: res.updated_layout as Agent2Output })
      } catch { setStatus(v => ({ ...v, saving: false })) }
    }, 600)
  }, [sessionId, pipeline, setPipeline])

  const onItemMouseDown  = (e: React.MouseEvent,  id: string, ix: number, iz: number) => { e.stopPropagation(); setSelected(id); dragRef.current = { id, startMouseX:e.clientX, startMouseY:e.clientY, startItemX:ix, startItemZ:iz } }
  const onItemTouchStart = (e: React.TouchEvent,  id: string, ix: number, iz: number) => { e.stopPropagation(); setSelected(id); const t=e.touches[0]; dragRef.current = { id, startMouseX:t.clientX, startMouseY:t.clientY, startItemX:ix, startItemZ:iz } }

  const onMove = useCallback((clientX: number, clientY: number) => {
    const drag = dragRef.current; if (!drag) return
    const dx = (clientX - drag.startMouseX) / scaleX
    const dz = (clientY - drag.startMouseY) / scaleY
    setFurniture(prev => prev.map(f => {
      if (f.id !== drag.id) return f
      return { ...f, position: { x: Math.round(Math.max(0, Math.min(drag.startItemX+dx, W-f.size.width))), z: Math.round(Math.max(0, Math.min(drag.startItemZ+dz, L-f.size.depth))) } }
    }))
  }, [scaleX, scaleY, W, L])

  const onEnd = useCallback(() => { if (dragRef.current) { saveToBackend(furniture); dragRef.current = null } }, [furniture, saveToBackend])

  const handleRerender = async () => {
    if (!sessionId) return
    setRerendering(true)
    await fetch(`${API_URL}/api/design/rerender`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ session_id: sessionId }) })
    setRerendering(false)
  }

  if (!layout) return <div className="h-80 flex items-center justify-center text-marble/30 text-sm font-body">Canvas not available</div>

  const sel = furniture.find(f => f.id === selected)

  return (
    <div className="p-6 bg-obsidian-700 flex flex-col items-center gap-4">
      <div className="w-full flex items-center justify-between" style={{ maxWidth: CANVAS_W }}>
        <p className="text-marble/30 text-xs font-body tracking-widest uppercase">Floor Plan · Interactive</p>
        <div className="flex gap-2">
          <button onClick={() => { if (layout?.furniture) { setFurniture([...layout.furniture]); setStatus({saving:false,valid:null,issues:[]}); saveToBackend([...layout.furniture]) } }} className="text-marble/30 hover:text-marble/60 text-[10px] font-body border border-white/07 hover:border-white/15 px-2 py-1 rounded-lg transition-all duration-150">↺ Reset</button>
          {sessionId && (
            <button onClick={handleRerender} disabled={rerendering} className={`text-[10px] font-body px-3 py-1 rounded-lg border transition-all duration-200 ${rerendering ? 'opacity-50 cursor-wait border-gold/20 text-gold/40' : 'bg-gold/15 text-gold border-gold/30 hover:bg-gold/25'}`}>
              {rerendering ? '⟳ Re-rendering…' : '✦ Re-render'}
            </button>
          )}
        </div>
      </div>

      <div ref={containerRef} className="relative select-none" style={{ width: CANVAS_W, height: CANVAS_H }}
        onMouseMove={(e) => onMove(e.clientX, e.clientY)} onMouseUp={onEnd} onMouseLeave={onEnd}
        onTouchMove={(e) => { e.preventDefault(); onMove(e.touches[0].clientX, e.touches[0].clientY) }}
        onTouchEnd={onEnd} onClick={() => setSelected(null)}
      >
        <svg width={CANVAS_W} height={CANVAS_H} className="rounded border border-gold/20" style={{ background: 'rgba(201,168,76,0.03)' }}>
          <rect x={0} y={0} width={CANVAS_W} height={CANVAS_H} fill="none" stroke="rgba(201,168,76,0.3)" strokeWidth={2} rx={4} />
          {Array.from({ length: 3 }).map((_, i) => (
            <g key={i}>
              <line x1={(CANVAS_W/4)*(i+1)} y1={0} x2={(CANVAS_W/4)*(i+1)} y2={CANVAS_H} stroke="rgba(255,255,255,0.04)" strokeWidth={1} />
              <line x1={0} y1={(CANVAS_H/4)*(i+1)} x2={CANVAS_W} y2={(CANVAS_H/4)*(i+1)} stroke="rgba(255,255,255,0.04)" strokeWidth={1} />
            </g>
          ))}
          {furniture.map(f => {
            const x = f.position.x * scaleX, z = f.position.z * scaleY
            const w = Math.max(f.size.width * scaleX, 14), d = Math.max(f.size.depth * scaleY, 14)
            const isSel = selected === f.id, isDrag = dragRef.current?.id === f.id
            const col = f.color ?? '#C9A84C'
            return (
              <g key={f.id}>
                <rect x={x+2} y={z+2} width={w} height={d} fill="rgba(0,0,0,0.35)" rx={3} />
                <rect x={x} y={z} width={w} height={d} fill={`${col}33`} stroke={isSel ? col : `${col}88`} strokeWidth={isSel ? 2 : 1} rx={3}
                  style={{ cursor: isDrag ? 'grabbing' : 'grab', filter: isDrag ? `drop-shadow(0 0 6px ${col}66)` : 'none' }}
                  onMouseDown={e => onItemMouseDown(e, f.id, f.position.x, f.position.z)}
                  onTouchStart={e => onItemTouchStart(e, f.id, f.position.x, f.position.z)}
                  onClick={e => e.stopPropagation()} />
                {w > 30 && d > 16 && (
                  <text x={x+w/2} y={z+d/2+4} textAnchor="middle" fontSize={9} fill={isSel ? col : `${col}99`} style={{ pointerEvents:'none', fontFamily:'sans-serif' }}>
                    {f.label.slice(0, 8)}
                  </text>
                )}
                {isSel && <rect x={x-3} y={z-3} width={w+6} height={d+6} fill="none" stroke={col} strokeWidth={1} strokeDasharray="4 2" rx={5} opacity={0.6} />}
              </g>
            )
          })}
        </svg>

        {selected && sel && (() => {
          const tx = Math.max(0, Math.min(sel.position.x * scaleX, CANVAS_W - 160))
          const ty = Math.max(4, sel.position.z * scaleY - 88)
          return (
            <div className="absolute z-10 pointer-events-none" style={{ left: tx, top: ty }}>
              <div className="bg-obsidian border border-gold/30 rounded-xl px-3 py-2 shadow-xl" style={{ minWidth:148 }}>
                <p className="text-gold text-xs font-body font-medium mb-1">{sel.label}</p>
                <p className="text-marble/50 text-[10px] font-body">{sel.size.width} × {sel.size.depth} cm</p>
                <p className="text-marble/35 text-[10px] font-body mt-0.5">Pos: ({sel.position.x}, {sel.position.z})</p>
                <p className="text-marble/20 text-[10px] font-body mt-1 italic">drag to reposition</p>
              </div>
            </div>
          )
        })()}
      </div>

      <div className="flex items-center gap-2 h-5">
        {status.saving && <><div className="w-3 h-3 border border-gold/40 border-t-gold rounded-full animate-spin" /><span className="text-marble/30 text-[10px] font-body">Saving…</span></>}
        {!status.saving && status.valid === true  && <><div className="w-1.5 h-1.5 rounded-full bg-sage" /><span className="text-sage  text-[10px] font-body">Layout valid</span></>}
        {!status.saving && status.valid === false && <><div className="w-1.5 h-1.5 rounded-full bg-rust" /><span className="text-rust  text-[10px] font-body">{status.issues[0] ?? 'Layout has conflicts'}</span></>}
      </div>

      <div className="flex flex-wrap gap-x-4 gap-y-1 justify-center" style={{ maxWidth: CANVAS_W }}>
        {furniture.map(f => (
          <button key={f.id} onClick={() => setSelected(selected===f.id ? null : f.id)} className="flex items-center gap-1.5 transition-opacity duration-150" style={{ opacity: selected && selected!==f.id ? 0.3 : 1 }}>
            <div className="w-2 h-2 rounded-sm flex-shrink-0" style={{ background: f.color ?? '#C9A84C' }} />
            <span className="text-marble/50 text-[10px] font-body">{f.label}</span>
          </button>
        ))}
      </div>
      <p className="text-marble/20 text-[10px] font-body">{W} × {L} cm — drag to rearrange · auto-saves</p>
    </div>
  )
}

// ── Main ResultStep ────────────────────────────────────────────────────────────
export default function ResultStep() {
  const {
    roomImageUrl, pipeline, selectedVariation,
    setSelectedVariation, setStep, reset, sessionId,
  } = useStore()

  const [view, setView] = useState<'compare' | 'canvas' | 'details'>('compare')

  const agent1 = pipeline?.agent1
  const agent2 = pipeline?.agent2
  const agent3 = pipeline?.agent3
  const agent4 = pipeline?.agent4
  const agent6 = pipeline?.agent6

  const current   = agent6?.variations?.[selectedVariation]
  const afterUrl  = current ? api.imageUrl(current.image_url) : null
  const beforeUrl = roomImageUrl ?? ''

  return (
    <div className="min-h-screen pt-24 pb-16 px-6">
      <div className="max-w-6xl mx-auto">

        {/* Header */}
        <div className="flex items-center justify-between mb-8" style={{ animation: 'slideUp 0.6s ease forwards' }}>
          <div>
            <p className="text-gold/60 text-xs tracking-[0.3em] uppercase font-body mb-1">Your Design</p>
            <h1 className="font-display text-4xl font-light text-marble">
              {agent1?.style_preference ?? 'Interior'}{' '}
              <span className="italic text-gold">Complete</span>
            </h1>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => { setStep('upload'); reset() }}
              className="px-5 py-2.5 rounded-xl border border-white/10 text-marble/50 text-sm font-body hover:border-white/20 hover:text-marble/70 transition-all duration-200"
            >
              New Design
            </button>
            {afterUrl && (
              <button
                onClick={() => downloadBlob(afterUrl, `aetherial-design-${selectedVariation + 1}.jpg`)}
                className="btn-gold px-5 py-2.5 rounded-xl text-sm font-body tracking-wide"
              >
                ↓ Download
              </button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Main area */}
          <div className="lg:col-span-2 space-y-4">

            {/* View toggle */}
            <div className="flex gap-2 mb-4">
              {(['compare', 'canvas', 'details'] as const).map((v) => (
                <button
                  key={v}
                  onClick={() => setView(v)}
                  className={`px-4 py-2 rounded-xl text-xs font-body tracking-wide transition-all duration-200 ${
                    view === v
                      ? 'bg-gold/15 text-gold border border-gold/30'
                      : 'text-marble/40 border border-white/07 hover:text-marble/60 hover:border-white/15'
                  }`}
                >
                  {v === 'compare' ? '⇔ Compare' : v === 'canvas' ? '○ Canvas' : '+ Details'}
                </button>
              ))}
            </div>

            {/* Compare view */}
            {view === 'compare' && (
              <div className="glass-card overflow-hidden" style={{ animation: 'slideUp 0.5s ease both' }}>
                {beforeUrl && afterUrl ? (
                  <BeforeAfterSlider before={beforeUrl} after={afterUrl} />
                ) : afterUrl ? (
                  // No original image — just show the generated design
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={afterUrl} alt="Generated Design" className="w-full object-cover" style={{ height: '420px' }} />
                ) : (
                  <div className="flex items-center justify-center" style={{ height: '420px' }}>
                    <p className="text-marble/30 text-sm font-body">
                      {agent6 ? 'Loading design…' : 'No design generated yet'}
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Canvas view */}
            {view === 'canvas' && (
              <div className="glass-card overflow-hidden" style={{ animation: 'slideUp 0.5s ease both' }}>
                <InteractiveCanvas layout={agent2} />
              </div>
            )}

            {/* Details view */}
            {view === 'details' && agent3 && (
              <div className="glass-card p-5" style={{ animation: 'slideUp 0.5s ease both' }}>
                <p className="text-marble/40 text-xs tracking-[0.2em] uppercase font-body mb-4">Vision Analysis</p>
                <div className="grid grid-cols-2 gap-3 text-sm font-body">
                  <div><p className="text-marble/30 text-xs mb-1">Light Source</p><p className="text-marble/70">{agent3.lighting?.primary_source ?? '—'}</p></div>
                  <div><p className="text-marble/30 text-xs mb-1">Ambient Mood</p><p className="text-marble/70">{agent3.lighting?.ambient_mood ?? '—'}</p></div>
                  <div><p className="text-marble/30 text-xs mb-1">Focal Wall</p><p className="text-marble/70">{agent3.design_constraints?.focal_wall ?? '—'}</p></div>
                  <div><p className="text-marble/30 text-xs mb-1">Room Shape</p><p className="text-marble/70">{(agent3.image_dimensions as {estimated_room_shape?: string})?.estimated_room_shape ?? '—'}</p></div>
                </div>
              </div>
            )}

            {/* Variations */}
            {agent6 && agent6.variations.length > 1 && (
              <div style={{ animation: 'slideUp 0.5s ease 0.1s both' }}>
                <p className="text-marble/30 text-xs tracking-[0.2em] uppercase font-body mb-3">Variations</p>
                <div className="flex gap-3 overflow-x-auto pb-2">
                  {agent6.variations.map((v, idx) => (
                    <button
                      key={v.variation_id}
                      onClick={() => setSelectedVariation(idx)}
                      className={`flex-shrink-0 w-40 h-24 rounded-xl overflow-hidden border-2 transition-all duration-200 ${selectedVariation === idx ? 'border-gold' : 'border-white/10 hover:border-white/25'}`}
                    >
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={api.imageUrl(v.thumbnail_url || v.image_url)} alt={`Variation ${idx+1}`} className="w-full h-full object-cover" />
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Floor Plan */}
            {agent4?.canvas_image_path ? (
              <div className="glass-card p-5 mt-2" style={{ animation: 'slideUp 0.5s ease 0.2s both' }}>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <p className="text-marble/40 text-xs tracking-[0.2em] uppercase font-body">📐 Floor Plan Layout</p>
                    <p className="text-marble/25 text-[10px] font-body mt-0.5">Generated by spatial validator (Agent 4)</p>
                  </div>
                  <button
                    onClick={() => downloadBlob(`${API_URL}${agent4.canvas_image_path}`, 'floor-plan.png')}
                    className="px-3 py-1.5 rounded-lg border border-gold/25 text-gold/70 text-xs font-body hover:border-gold/50 hover:text-gold transition-all duration-200"
                  >
                    ↓ Save
                  </button>
                </div>
                <div className="rounded-xl overflow-hidden border border-gold/10 bg-obsidian/40">
                  <FloorPlanImage canvasImagePath={agent4.canvas_image_path} />
                </div>
                <div className="mt-3 flex items-center gap-2">
                  <div className={`w-1.5 h-1.5 rounded-full ${agent4.is_valid ? 'bg-sage' : 'bg-rust'}`} />
                  <span className="text-marble/35 text-[10px] font-body">
                    {agent4.is_valid ? 'Layout validated — no conflicts' : `${agent4.issues?.length ?? 0} layout warning(s)`}
                  </span>
                </div>
              </div>
            ) : (
              agent4 && (
                <div className="glass-card p-5 mt-2">
                  <p className="text-marble/25 text-xs font-body text-center py-4">Floor plan unavailable for this session</p>
                </div>
              )
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-4">

            {/* Design Brief */}
            <div className="glass-card p-5" style={{ animation: 'slideUp 0.5s ease 0.15s both' }}>
              <p className="text-marble/40 text-xs tracking-[0.2em] uppercase font-body mb-4">Design Brief</p>
              <div className="space-y-3">
                {[
                  ['Room Type',  agent1?.room_type],
                  ['Style',      agent1?.style_preference],
                  ['Palette',    agent1?.color_palette],
                  ['Mode',       agent1?.ai_mode ? agent1.ai_mode.charAt(0).toUpperCase() + agent1.ai_mode.slice(1) : null],
                  ['Dimensions', agent1?.dimensions ? `${agent1.dimensions.width_cm} × ${agent1.dimensions.length_cm} Cm` : null],
                ].map(([label, value]) => (
                  <div key={label as string} className="flex justify-between items-center">
                    <span className="text-marble/40 text-xs font-body">{label}</span>
                    <span className="text-marble/80 text-xs font-body text-right">{value ?? '—'}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Room Analysis */}
            {agent3 && (
              <div className="glass-card p-5" style={{ animation: 'slideUp 0.5s ease 0.2s both' }}>
                <p className="text-marble/40 text-xs tracking-[0.2em] uppercase font-body mb-4">Room Analysis</p>
                <div className="space-y-3">
                  {[
                    ['Windows',      agent3.openings?.windows_count],
                    ['Doors',        agent3.openings?.doors_count],
                    ['Light Source', agent3.lighting?.primary_source],
                    ['Ambient Mood', agent3.lighting?.ambient_mood],
                    ['Focal Wall',   agent3.design_constraints?.focal_wall],
                    ['Room Shape',   (agent3.image_dimensions as {estimated_room_shape?: string})?.estimated_room_shape],
                  ].map(([label, value]) => (
                    <div key={label as string} className="flex justify-between items-center">
                      <span className="text-marble/40 text-xs font-body">{label}</span>
                      <span className="text-marble/80 text-xs font-body text-right">{value ?? '—'}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Furniture */}
            {agent2?.furniture && agent2.furniture.length > 0 && (
              <div className="glass-card p-5" style={{ animation: 'slideUp 0.5s ease 0.25s both' }}>
                <p className="text-marble/40 text-xs tracking-[0.2em] uppercase font-body mb-4">
                  Furniture Placed ({agent2.furniture.length})
                </p>
                <div className="space-y-2">
                  {agent2.furniture.map((f) => (
                    <div key={f.id} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: f.color ?? '#C9A84C' }} />
                        <span className="text-marble/70 text-xs font-body">{f.label}</span>
                      </div>
                      <span className="text-marble/30 text-[10px] font-body">{f.size.width}×{f.size.depth}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Render time */}
            {agent6 && (
              <div className="glass-card p-5" style={{ animation: 'slideUp 0.5s ease 0.3s both', background: 'linear-gradient(135deg, rgba(201,168,76,0.08), rgba(201,168,76,0.03))' }}>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-gold/10 flex items-center justify-center text-gold text-sm">⚡</div>
                  <div>
                    <p className="text-marble/40 text-[10px] uppercase tracking-wider font-body">Render time</p>
                    <p className="text-gold text-lg font-body">{agent6.render_time_seconds}s</p>
                  </div>
                </div>
              </div>
            )}

          </div>
        </div>
      </div>
    </div>
  )
}