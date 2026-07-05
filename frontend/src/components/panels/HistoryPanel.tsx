'use client'
import { useEffect, useState } from 'react'
import { useStore, type HistoryEntry } from '@/store/useStore'
import { api } from '@/lib/api'

export default function HistoryPanel({ onClose }: { onClose: () => void }) {
  const { userId, history, setHistory } = useStore()
  const [loading, setLoading]   = useState(true)
  const [deleting, setDeleting] = useState<string | null>(null)

  useEffect(() => {
    if (!userId) { setLoading(false); return }
    api.getHistory(userId)
      .then(setHistory)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [userId, setHistory])

  const handleDelete = async (sessionId: string) => {
    if (!userId) return
    setDeleting(sessionId)
    try {
      await api.deleteHistoryEntry(userId, sessionId)
      setHistory(history.filter(h => h.session_id !== sessionId))
    } catch (e) { console.error(e) }
    finally { setDeleting(null) }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-end">
      {/* backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* Panel */}
      <div className="relative w-full max-w-sm h-full bg-obsidian border-l border-white/07 flex flex-col shadow-2xl" style={{ animation: 'slideRight 0.3s ease' }}>

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/07">
          <div>
            <p className="text-marble/40 text-[10px] tracking-[0.2em] uppercase font-body">Your Designs</p>
            <p className="text-marble/80 text-sm font-body font-medium mt-0.5">History</p>
          </div>
          <button onClick={onClose} className="w-8 h-8 rounded-lg border border-white/07 flex items-center justify-center text-marble/40 hover:text-marble/70 hover:border-white/15 transition-all duration-200 text-sm">✕</button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">

          {loading && (
            <div className="flex items-center justify-center h-40">
              <div className="w-6 h-6 border border-gold/30 border-t-gold rounded-full animate-spin" />
            </div>
          )}

          {!loading && !userId && (
            <div className="text-center py-12">
              <p className="text-marble/30 text-sm font-body">No user ID found.</p>
              <p className="text-marble/20 text-xs font-body mt-1">Reload the page to generate one.</p>
            </div>
          )}

          {!loading && userId && history.length === 0 && (
            <div className="text-center py-12">
              <p className="text-marble/30 text-2xl mb-3">✦</p>
              <p className="text-marble/30 text-sm font-body">No designs yet.</p>
              <p className="text-marble/20 text-xs font-body mt-1">Your designs will appear here after generation.</p>
            </div>
          )}

          {!loading && history.map((entry) => (
            <HistoryCard
              key={entry.session_id}
              entry={entry}
              onDelete={() => handleDelete(entry.session_id)}
              isDeleting={deleting === entry.session_id}
            />
          ))}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-white/07">
          <p className="text-marble/20 text-[10px] font-body text-center">
            {history.filter(h => h.status === 'done').length} completed design{history.filter(h => h.status === 'done').length !== 1 ? 's' : ''}
          </p>
        </div>
      </div>
    </div>
  )
}

// ── HistoryCard ────────────────────────────────────────────────────────────────
function HistoryCard({
  entry, onDelete, isDeleting,
}: { entry: HistoryEntry; onDelete: () => void; isDeleting: boolean }) {
  const date = new Date(entry.created_at * 1000)
  const dateStr = date.toLocaleDateString('en-GB', { day:'numeric', month:'short', hour:'2-digit', minute:'2-digit' })
  const thumbUrl = entry.thumbnail_url ? `${process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'}${entry.thumbnail_url}` : null

  const statusColor = entry.status === 'done' ? 'bg-sage' : entry.status === 'failed' ? 'bg-rust' : 'bg-gold/50'

  return (
    <div className="rounded-xl border border-white/07 bg-obsidian-700/50 overflow-hidden hover:border-white/12 transition-all duration-200 group">
      <div className="flex gap-3 p-3">
        {/* Thumbnail */}
        <div className="w-20 h-16 rounded-lg overflow-hidden flex-shrink-0 bg-white/04">
          {thumbUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={thumbUrl} alt="Design" className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-marble/20 text-xs font-body">
              {entry.status === 'pending' ? '⟳' : entry.status === 'failed' ? '✕' : '✦'}
            </div>
          )}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 mb-1">
            <div className={`w-1.5 h-1.5 rounded-full ${statusColor}`} />
            <p className="text-marble/70 text-xs font-body font-medium truncate">{entry.style ?? 'Design'}</p>
          </div>
          <p className="text-marble/35 text-[10px] font-body capitalize">{entry.room_type ?? 'Room'}</p>
          <p className="text-marble/20 text-[10px] font-body mt-1">{dateStr}</p>
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          {entry.image_url && (
            <button
              onClick={async () => {
                const url = `${process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'}${entry.image_url}`
                const resp = await fetch(url)
                const blob = await resp.blob()
                const a = Object.assign(document.createElement('a'), { href: URL.createObjectURL(blob), download: `aetherial-${entry.session_id.slice(0,8)}.jpg` })
                a.click(); URL.revokeObjectURL(a.href)
              }}
              className="w-7 h-7 rounded-lg border border-gold/20 text-gold/60 hover:text-gold hover:border-gold/40 flex items-center justify-center text-xs transition-all duration-150"
              title="Download"
            >↓</button>
          )}
          <button
            onClick={onDelete}
            disabled={isDeleting}
            className="w-7 h-7 rounded-lg border border-white/07 text-marble/25 hover:text-rust/60 hover:border-rust/20 flex items-center justify-center text-xs transition-all duration-150 disabled:opacity-50"
            title="Delete"
          >{isDeleting ? '…' : '✕'}</button>
        </div>
      </div>
    </div>
  )
}