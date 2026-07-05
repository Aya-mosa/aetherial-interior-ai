import type {
  PipelineStatus, SessionResponse, ChatResponse,
  DesignStyle, FurnitureItem, RoomType, ColorPalette,
  AIMode, RoomDimensions, FurniturePosition,
} from './types'
import type { HistoryEntry } from '@/store/useStore'

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init)
  if (!res.ok) { const err = await res.text(); throw new Error(err || `HTTP ${res.status}`) }
  return res.json()
}

export const api = {

  // ── Design ──────────────────────────────────────────────────────────────────
  async startDesign(params: {
    image: File; roomType: RoomType; style: DesignStyle
    furniture: FurnitureItem[]; dimensions: RoomDimensions
    colorPalette: ColorPalette; aiMode: AIMode
    numVariations?: number; userId?: string
  }): Promise<SessionResponse> {
    const form = new FormData()
    form.append('room_image',     params.image)
    form.append('room_type',      params.roomType)
    form.append('style',          params.style)
    form.append('furniture',      JSON.stringify(params.furniture))
    form.append('width_cm',       String(params.dimensions.width_cm))
    form.append('length_cm',      String(params.dimensions.length_cm))
    form.append('color_palette',  params.colorPalette)
    form.append('ai_mode',        params.aiMode)
    form.append('num_variations', String(params.numVariations ?? 3))
    form.append('user_id',        params.userId ?? 'anonymous')   // ← NEW
    return apiFetch<SessionResponse>('/api/design/start', { method: 'POST', body: form })
  },

  async getStatus(sessionId: string): Promise<PipelineStatus> {
    return apiFetch<PipelineStatus>(`/api/design/status/${sessionId}`)
  },

  async sendChat(sessionId: string, message: string): Promise<ChatResponse> {
    return apiFetch<ChatResponse>('/api/design/chat', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, message }),
    })
  },

  async updateCanvas(sessionId: string, positions: FurniturePosition[]): Promise<{
    session_id: string; is_valid: boolean; issues: unknown[]; updated_layout?: unknown
  }> {
    return apiFetch('/api/canvas/update', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, furniture_positions: positions }),
    })
  },

  async rerender(sessionId: string): Promise<SessionResponse> {
    return apiFetch<SessionResponse>('/api/design/rerender', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId }),
    })
  },

  // ── History ─────────────────────────────────────────────────────────────────
  async getHistory(userId: string): Promise<HistoryEntry[]> {
    return apiFetch<HistoryEntry[]>(`/api/history/${userId}`)
  },

  async deleteHistoryEntry(userId: string, sessionId: string): Promise<{ ok: boolean }> {
    return apiFetch<{ ok: boolean }>(`/api/history/${userId}/${sessionId}`, { method: 'DELETE' })
  },

  // ── Utils ───────────────────────────────────────────────────────────────────
  imageUrl(path: string): string {
    if (!path) return ''
    if (path.startsWith('http')) return path
    return `${BASE}${path.startsWith('/') ? '' : '/'}${path}`
  },
}