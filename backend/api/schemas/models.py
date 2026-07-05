"""
Pydantic schemas — the data contracts between agents and the API.

Each agent reads the previous agent's output schema and writes its own.
This enforces structure and makes debugging trivial.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from enum import Enum


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class RoomType(str, Enum):
    BEDROOM = "Bedroom"
    LIVING_ROOM = "Living Room"
    OFFICE = "Office"
    GAMING_ROOM = "Gaming Room"
    BATHROOM = "Bathroom"
    KITCHEN = "Kitchen"


class DesignStyle(str, Enum):
    MODERN = "Modern"
    MINIMAL = "Minimal"
    SCANDINAVIAN = "Scandinavian"
    LUXURY = "Luxury"
    JAPANDI = "Japandi"
    INDUSTRIAL = "Industrial"
    CYBERPUNK = "Cyberpunk"


class FurnitureItem(str, Enum):
    BED = "Bed"
    SOFA = "Sofa"
    DESK = "Desk"
    WARDROBE = "Wardrobe"
    TV_UNIT = "TV Unit"
    LIGHTING = "Lighting"
    COFFEE_TABLE = "Coffee Table"
    NIGHTSTAND = "Nightstand"
    DINING_TABLE = "Dining Table"
    ARMCHAIR = "Armchair"


class ColorPalette(str, Enum):
    WARM_WOODS = "Warm Woods & Neutrals"
    DARK_OBSIDIAN = "Dark Obsidian & Neon"
    COOL_COASTAL = "Cool Coastal Blues"
    MONOCHROME = "Monochrome Slate"
    EARTHY_TONES = "Earthy Tones"


class AIMode(str, Enum):
    STRICT = "strict"       # Only place exactly what the user selected
    CREATIVE = "creative"   # AI adds complementary decor


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


# ─────────────────────────────────────────────
# Request / Input schemas
# ─────────────────────────────────────────────

class RoomDimensions(BaseModel):
    width_cm: int = Field(..., ge=100, le=2000, description="Room width in centimetres")
    length_cm: int = Field(..., ge=100, le=2000, description="Room length in centimetres")


class DesignRequest(BaseModel):
    """POST /api/design/start — the full user input"""
    room_type: RoomType
    style: DesignStyle
    furniture: List[FurnitureItem] = Field(..., min_length=1)
    dimensions: RoomDimensions
    color_palette: ColorPalette = ColorPalette.WARM_WOODS
    ai_mode: AIMode = AIMode.STRICT
    session_id: Optional[str] = None     # Re-use existing session


class CanvasUpdateRequest(BaseModel):
    """POST /api/canvas/update — when user moves furniture on canvas"""
    session_id: str
    furniture_positions: List[Dict[str, Any]]  # Updated x,z,width,depth per item


class ChatCommandRequest(BaseModel):
    """POST /api/design/chat — AI assistant command"""
    session_id: str
    message: str


class RegenerateAreaRequest(BaseModel):
    """POST /api/design/regenerate-area — inpaint a specific zone"""
    session_id: str
    mask_base64: str    # Base64 PNG of the selected area mask
    prompt_override: Optional[str] = None


# ─────────────────────────────────────────────
# Agent 1: Preprocessing output
# ─────────────────────────────────────────────

class Agent1Output(BaseModel):
    """Structured room data extracted and enriched from user input"""
    session_id: str
    room_type: str
    style_preference: str
    dimensions: RoomDimensions
    selected_furniture: List[str]
    color_palette: str
    avoid_elements: List[str] = ["people", "text", "watermarks"]
    ai_mode: AIMode
    additional_notes: str = ""


# ─────────────────────────────────────────────
# Agent 2: Spatial planner output
# ─────────────────────────────────────────────

class FurniturePosition(BaseModel):
    id: str
    label: str
    position: Dict[str, float] = Field(..., description="x, z coordinates in cm")
    size: Dict[str, float] = Field(..., description="width, depth in cm")
    color: Optional[str] = None    # Hex for canvas rendering


class Agent2Output(BaseModel):
    """Spatial layout with collision-free coordinates"""
    session_id: str
    room_dimensions: Dict[str, float]   # {"width": 400, "length": 500}
    furniture: List[FurniturePosition]
    collision_detected: bool = False
    warnings: List[str] = []


# ─────────────────────────────────────────────
# Agent 3: Vision analysis output
# ─────────────────────────────────────────────

class OpeningsData(BaseModel):
    windows_count: int = 0
    doors_count: int = 0


class LightingData(BaseModel):
    primary_source: str = "Natural light"
    ambient_mood: str = "Neutral"


class DesignConstraints(BaseModel):
    focal_wall: str = "North wall"
    avoid_blocking: List[str] = []


class Agent3Output(BaseModel):
    """Vision analysis of the uploaded room image"""
    session_id: str
    openings: OpeningsData
    lighting: LightingData
    design_constraints: DesignConstraints
    image_dimensions: Dict[str, Any] = {}


# ─────────────────────────────────────────────
# Agent 4: Spatial validator output
# ─────────────────────────────────────────────

class ValidationIssue(BaseModel):
    item_id: str
    issue_type: Literal["overlap", "out_of_bounds", "blocks_opening"]
    description: str
    suggested_fix: Optional[str] = None


class Agent4Output(BaseModel):
    """Result of spatial validation"""
    session_id: str
    is_valid: bool
    issues: List[ValidationIssue] = []
    canvas_image_path: Optional[str] = None   # Path to generated floor plan PNG


# ─────────────────────────────────────────────
# Agent 5: Prompt engineering output
# ─────────────────────────────────────────────

class Agent5Output(BaseModel):
    """Optimised Stable Diffusion prompts"""
    session_id: str
    positive_prompt: str
    negative_prompt: str
    metadata: Dict[str, Any] = {}


# ─────────────────────────────────────────────
# Agent 6: Rendering output
# ─────────────────────────────────────────────

class RenderVariation(BaseModel):
    variation_id: int
    image_url: str          # Served at /outputs/<session>/<variation>.png
    thumbnail_url: str


class Agent6Output(BaseModel):
    """Final rendered images"""
    session_id: str
    variations: List[RenderVariation]
    render_time_seconds: float


# ─────────────────────────────────────────────
# API response wrappers
# ─────────────────────────────────────────────

class SessionResponse(BaseModel):
    session_id: str
    status: TaskStatus
    message: str


class PipelineStatusResponse(BaseModel):
    session_id: str
    status: TaskStatus
    current_step: Optional[str] = None
    progress_percent: int = 0
    agent1: Optional[Agent1Output] = None
    agent2: Optional[Agent2Output] = None
    agent3: Optional[Agent3Output] = None
    agent4: Optional[Agent4Output] = None
    agent5: Optional[Agent5Output] = None
    agent6: Optional[Agent6Output] = None
    error: Optional[str] = None


class CanvasValidationResponse(BaseModel):
    session_id: str
    is_valid: bool
    issues: List[ValidationIssue] = []
    updated_layout: Optional[Agent2Output] = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    action_taken: Optional[str] = None   # e.g. "moved_sofa", "changed_style"
    updated_layout: Optional[Agent2Output] = None
