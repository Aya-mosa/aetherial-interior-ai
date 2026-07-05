// ─── Enums ───────────────────────────────────────────────────────────────────

export type RoomType = 'Bedroom' | 'Living Room' | 'Office' | 'Gaming Room' | 'Bathroom' | 'Kitchen'
export type DesignStyle = 'Modern' | 'Minimal' | 'Scandinavian' | 'Luxury' | 'Japandi' | 'Industrial' | 'Cyberpunk'
export type FurnitureItem = 'Bed' | 'Sofa' | 'Desk' | 'Wardrobe' | 'TV Unit' | 'Lighting' | 'Coffee Table' | 'Nightstand' | 'Dining Table' | 'Armchair'
export type ColorPalette = 'Warm Woods & Neutrals' | 'Dark Obsidian & Neon' | 'Cool Coastal Blues' | 'Monochrome Slate' | 'Earthy Tones'
export type AIMode = 'strict' | 'creative'
export type TaskStatus = 'pending' | 'processing' | 'done' | 'failed'

// ─── API Schemas ──────────────────────────────────────────────────────────────

export interface RoomDimensions { width_cm: number; length_cm: number }

export interface FurniturePosition {
  id: string
  label: string
  position: { x: number; z: number }
  size: { width: number; depth: number }
  color?: string
}

export interface Agent1Output {
  session_id: string; room_type: string; style_preference: string
  dimensions: RoomDimensions; selected_furniture: string[]
  color_palette: string; ai_mode: AIMode; additional_notes: string
}

export interface Agent2Output {
  session_id: string; room_dimensions: { width: number; length: number }
  furniture: FurniturePosition[]; collision_detected: boolean; warnings: string[]
}

export interface Agent3Output {
  session_id: string
  openings: { windows_count: number; doors_count: number }
  lighting: { primary_source: string; ambient_mood: string }
  design_constraints: { focal_wall: string; avoid_blocking: string[] }
  image_dimensions: Record<string, unknown>
}

export interface ValidationIssue {
  item_id: string; issue_type: 'overlap' | 'out_of_bounds' | 'blocks_opening'
  description: string; suggested_fix?: string
}

export interface Agent4Output {
  session_id: string; is_valid: boolean
  issues: ValidationIssue[]; canvas_image_path?: string
}

export interface Agent5Output {
  session_id: string; positive_prompt: string; negative_prompt: string
  metadata: Record<string, unknown>
}

export interface RenderVariation { variation_id: number; image_url: string; thumbnail_url: string }

export interface Agent6Output {
  session_id: string; variations: RenderVariation[]; render_time_seconds: number
}

export interface PipelineStatus {
  session_id: string; status: TaskStatus; current_step?: string; progress_percent: number
  agent1?: Agent1Output; agent2?: Agent2Output; agent3?: Agent3Output
  agent4?: Agent4Output; agent5?: Agent5Output; agent6?: Agent6Output; error?: string
}

export interface SessionResponse { session_id: string; status: TaskStatus; message: string }

export interface ChatMessage { role: 'user' | 'assistant'; content: string; timestamp: number }

export interface ChatResponse {
  session_id: string; reply: string; action_taken?: string; updated_layout?: Agent2Output
}

// ─── UI State ─────────────────────────────────────────────────────────────────

export type Step = 'upload' | 'style' | 'furniture' | 'generating' | 'result'

export interface DesignSession {
  sessionId?: string
  step: Step
  roomImage?: File
  roomImageUrl?: string
  roomType: RoomType
  style?: DesignStyle
  furniture: FurnitureItem[]
  colorPalette: ColorPalette
  aiMode: AIMode
  dimensions: RoomDimensions
  pipeline?: PipelineStatus
  selectedVariation: number
  chatMessages: ChatMessage[]
  isAssistantOpen: boolean
}

// ─── UI config data ───────────────────────────────────────────────────────────

export interface StyleOption {
  id: DesignStyle; label: string; description: string
  color: string; accent: string; emoji: string
}

export interface FurnitureOption {
  id: FurnitureItem; label: string; icon: string; category: string
}

export interface LoadingStep {
  key: string; label: string; agentLabel: string; icon: string
}

export const STYLE_OPTIONS: StyleOption[] = [
  { id: 'Modern',      label: 'Modern',      description: 'Clean lines, bold forms',   color: '#1A1A2E', accent: '#4FC3F7', emoji: '◼' },
  { id: 'Minimal',     label: 'Minimal',     description: 'Pure space, pure calm',     color: '#1C1B18', accent: '#E8E0D5', emoji: '□' },
  { id: 'Scandinavian',label: 'Scandinavian',description: 'Warm, functional beauty',   color: '#1A1E1A', accent: '#8BA888', emoji: '❋' },
  { id: 'Luxury',      label: 'Luxury',      description: 'Opulent, refined grandeur', color: '#18140A', accent: '#C9A84C', emoji: '◈' },
  { id: 'Japandi',     label: 'Japandi',     description: 'Zen meets Scandinavian',    color: '#141412', accent: '#A09070', emoji: '⊕' },
  { id: 'Industrial',  label: 'Industrial',  description: 'Raw, urban, powerful',      color: '#141416', accent: '#9E9E9E', emoji: '⬡' },
  { id: 'Cyberpunk',   label: 'Cyberpunk',   description: 'Neon, futuristic chaos',    color: '#0A0010', accent: '#FF0080', emoji: '⬟' },
]

export const FURNITURE_OPTIONS: FurnitureOption[] = [
  { id: 'Bed',          label: 'Bed',          icon: '🛏', category: 'Sleep'    },
  { id: 'Sofa',         label: 'Sofa',         icon: '🛋', category: 'Seating'  },
  { id: 'Desk',         label: 'Desk',         icon: '🖥', category: 'Work'     },
  { id: 'Wardrobe',     label: 'Wardrobe',     icon: '🚪', category: 'Storage'  },
  { id: 'TV Unit',      label: 'TV Unit',      icon: '📺', category: 'Media'    },
  { id: 'Lighting',     label: 'Lighting',     icon: '💡', category: 'Light'    },
  { id: 'Coffee Table', label: 'Coffee Table', icon: '🪵', category: 'Seating'  },
  { id: 'Nightstand',   label: 'Nightstand',   icon: '🕯', category: 'Sleep'    },
  { id: 'Dining Table', label: 'Dining Table', icon: '🍽', category: 'Dining'   },
  { id: 'Armchair',     label: 'Armchair',     icon: '💺', category: 'Seating'  },
]

export const ROOM_TYPES: RoomType[] = ['Bedroom', 'Living Room', 'Office', 'Gaming Room', 'Bathroom', 'Kitchen']

export const LOADING_STEPS: LoadingStep[] = [
  { key: 'agent1', label: 'Analyzing your intent',       agentLabel: 'Agent 1 — Intent Analysis',   icon: '🧠' },
  { key: 'agent2', label: 'Mapping spatial layout',      agentLabel: 'Agent 2 — Spatial Planner',   icon: '📐' },
  { key: 'agent3', label: 'Reading light & geometry',    agentLabel: 'Agent 3 — Vision Analysis',   icon: '👁' },
  { key: 'agent4', label: 'Validating furniture logic',  agentLabel: 'Agent 4 — Spatial Validator', icon: '✔' },
  { key: 'agent5', label: 'Engineering the prompt',      agentLabel: 'Agent 5 — Prompt Engineer',   icon: '✍' },
  { key: 'agent6', label: 'Rendering your design',       agentLabel: 'Agent 6 — SDXL Renderer',     icon: '🎨' },
]
