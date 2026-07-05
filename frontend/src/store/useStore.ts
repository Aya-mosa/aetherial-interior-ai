'use client'
import { create } from 'zustand'
import type {
  DesignSession, DesignStyle, FurnitureItem,
  RoomType, ColorPalette, AIMode, PipelineStatus,
  ChatMessage, Step,
} from '@/lib/types'

export interface HistoryEntry {
  session_id:    string
  user_id:       string
  created_at:    number
  style?:        string
  room_type?:    string
  thumbnail_url?: string
  image_url?:    string
  status:        string
}

interface Actions {
  setStep(step: Step): void
  setRoomImage(file: File, url: string): void
  setRoomType(rt: RoomType): void
  setStyle(s: DesignStyle): void
  toggleFurniture(f: FurnitureItem): void
  setColorPalette(c: ColorPalette): void
  setAIMode(m: AIMode): void
  setDimensions(w: number, l: number): void
  setSessionId(id: string): void
  setPipeline(p: PipelineStatus): void
  setSelectedVariation(n: number): void
  addChatMessage(m: ChatMessage): void
  toggleAssistant(): void
  setUserId(id: string): void
  setHistory(h: HistoryEntry[]): void
  reset(): void
}

const INITIAL: DesignSession & { userId: string; history: HistoryEntry[] } = {
  step:              'upload',
  roomType:          'Bedroom',
  furniture:         [],
  colorPalette:      'Warm Woods & Neutrals',
  aiMode:            'strict',
  dimensions:        { width_cm: 400, length_cm: 500 },
  selectedVariation: 0,
  chatMessages:      [],
  isAssistantOpen:   false,
  userId:            '',
  history:           [],
}

export const useStore = create<typeof INITIAL & Actions>((set) => ({
  ...INITIAL,

  setStep:             (step)             => set({ step }),
  setRoomImage:        (file, url)        => set({ roomImage: file, roomImageUrl: url }),
  setRoomType:         (roomType)         => set({ roomType }),
  setStyle:            (style)            => set({ style }),
  toggleFurniture:     (f)               => set((s) => ({
    furniture: s.furniture.includes(f) ? s.furniture.filter(x => x !== f) : [...s.furniture, f],
  })),
  setColorPalette:     (colorPalette)     => set({ colorPalette }),
  setAIMode:           (aiMode)           => set({ aiMode }),
  setDimensions:       (w, l)            => set({ dimensions: { width_cm: w, length_cm: l } }),
  setSessionId:        (sessionId)        => set({ sessionId }),
  setPipeline:         (pipeline)         => set({ pipeline }),
  setSelectedVariation:(n)               => set({ selectedVariation: n }),
  addChatMessage:      (m)               => set((s) => ({ chatMessages: [...s.chatMessages, m] })),
  toggleAssistant:     ()                => set((s) => ({ isAssistantOpen: !s.isAssistantOpen })),
  setUserId:           (userId)           => set({ userId }),
  setHistory:          (history)          => set({ history }),
  reset:               ()                => set({ ...INITIAL }),
}))