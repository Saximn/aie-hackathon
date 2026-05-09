"""Shared OmniForge AI Brain contracts.

This file is a scaffold contract layer. It should stay implementation-light.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class AdapterKind(StrEnum):
    GENERIC_INPUT = "generic_input"
    MINECRAFT = "minecraft"


class PrimitiveActionType(StrEnum):
    PRESS_KEY = "press_key"
    HOLD_KEY = "hold_key"
    MOVE_MOUSE = "move_mouse"
    CLICK = "click"
    WAIT = "wait"
    OPEN_MENU = "open_menu"
    SELECT_HOTBAR_SLOT = "select_hotbar_slot"
    MOVE_TOWARD_VISIBLE_OBJECT = "move_toward_visible_object"
    INTERACT_PRIMARY = "interact_primary"
    COLLECT_BLOCK = "collect_block"
    CRAFT_ITEM = "craft_item"
    BUILD_SHELTER = "build_shelter"


class VerificationStatus(StrEnum):
    SUCCESS = "success"
    INCOMPLETE = "incomplete"
    FAILED = "failed"
    STUCK = "stuck"
    UNSAFE = "unsafe"
    INVALID_PLAN = "invalid_plan"


class FailureType(StrEnum):
    MISSING_PREREQUISITE = "missing_prerequisite"
    INSUFFICIENT_RESOURCES = "insufficient_resources"
    RESOURCE_UNAVAILABLE = "resource_unavailable"
    PATHFINDING_FAILURE = "pathfinding_failure"
    VISUAL_MISALIGNMENT = "visual_misalignment"
    BAD_PLAN_ORDERING = "bad_plan_ordering"
    UNSUPPORTED_ACTION = "unsupported_action"
    MISSING_STRATEGY = "missing_strategy"
    TIMEOUT = "timeout"
    UNSAFE_STATE = "unsafe_state"


class RecoveryTransition(StrEnum):
    CONTINUE = "continue"
    RETRY = "retry"
    REPLAN = "replan"
    RESEARCH = "research"
    ABORT = "abort"
    STORE_MEMORY = "store_memory"
    PROMOTE_SKILL = "promote_skill"


class SkillSource(StrEnum):
    SEEDED = "seeded"
    LEARNED = "learned"
    RESEARCHED = "researched"
    USER = "user"


class SkillStatus(StrEnum):
    CANDIDATE = "candidate"
    VERIFIED = "verified"
    TRUSTED = "trusted"


class AgentEventType(StrEnum):
    GOAL_RECEIVED = "goal_received"
    GAME_PROFILE_CREATED = "game_profile_created"
    WORLD_OBSERVED = "world_observed"
    MEMORY_RETRIEVED = "memory_retrieved"
    PLAN_CREATED = "plan_created"
    ACTION_STARTED = "action_started"
    ACTION_COMPLETED = "action_completed"
    VERIFICATION_COMPLETED = "verification_completed"
    FAILURE_DIAGNOSED = "failure_diagnosed"
    RESEARCH_STARTED = "research_started"
    RESEARCH_COMPLETED = "research_completed"
    SKILL_CANDIDATE_CREATED = "skill_candidate_created"
    SKILL_PROMOTED = "skill_promoted"
    USER_INSTRUCTION_RECEIVED = "user_instruction_received"


class TrackStatus(StrEnum):
    READY = "ready"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class Position(BaseModel):
    x: float
    y: float
    z: float


class GameProfile(BaseModel):
    game_name: str
    genre: str
    controls: dict[str, str] = Field(default_factory=dict)
    core_mechanics: list[str] = Field(default_factory=list)
    early_game_objectives: list[str] = Field(default_factory=list)
    benchmark_goals: list[str] = Field(default_factory=list)
    adapter_hints: list[AdapterKind] = Field(default_factory=list)
    source: Literal["static", "researched", "user", "fallback"] = "static"
    confidence: float = 0.0


class VisualObservation(BaseModel):
    scene_summary: str = ""
    visible_objects: list[str] = Field(default_factory=list)
    risk_level: Literal["low", "medium", "high", "unknown"] = "unknown"
    time_of_day: Literal["day", "night", "dawn", "dusk", "unknown"] = "unknown"
    ui_state: Literal["gameplay", "menu", "inventory", "unknown"] = "unknown"
    confidence: float = 0.0


class SymbolicObservation(BaseModel):
    health: float | None = None
    hunger: float | None = None
    inventory: dict[str, int] = Field(default_factory=dict)
    nearby_blocks: list[str] = Field(default_factory=list)
    nearby_entities: list[str] = Field(default_factory=list)
    position: Position | None = None
    biome: str | None = None
    raw_state: dict[str, Any] = Field(default_factory=dict)


class DerivedRisks(BaseModel):
    night_risk: Literal["low", "medium", "high", "unknown"] = "unknown"
    combat_risk: Literal["low", "medium", "high", "unknown"] = "unknown"
    food_risk: Literal["low", "medium", "high", "unknown"] = "unknown"


class WorldSnapshot(BaseModel):
    snapshot_id: str
    cycle: int
    game: str
    goal: str
    visual: VisualObservation = Field(default_factory=VisualObservation)
    symbolic: SymbolicObservation = Field(default_factory=SymbolicObservation)
    derived_risks: DerivedRisks = Field(default_factory=DerivedRisks)
    screenshot_b64: str | None = None


class PrimitiveAction(BaseModel):
    id: str
    type: PrimitiveActionType
    args: dict[str, Any] = Field(default_factory=dict)
    expected_result: dict[str, Any] = Field(default_factory=dict)
    timeout_ms: int = 3000
    adapter: AdapterKind = AdapterKind.GENERIC_INPUT


class Plan(BaseModel):
    plan_id: str
    goal: str
    snapshot_id: str
    used_skills: list[str] = Field(default_factory=list)
    actions: list[PrimitiveAction] = Field(default_factory=list)


class ExecutionResult(BaseModel):
    action_id: str
    success: bool
    result: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class SupportedAction(BaseModel):
    type: PrimitiveActionType
    adapter: AdapterKind
    description: str
    required_args: list[str] = Field(default_factory=list)


class RuntimeHealth(BaseModel):
    runtime: TrackStatus = TrackStatus.UNKNOWN
    adapters: list[AdapterKind] = Field(default_factory=list)
    screenshot_available: bool = False
    symbolic_state_available: bool = False
    version: str = "unknown"


class RuntimeState(BaseModel):
    available: bool = False
    game: str | None = None
    symbolic: SymbolicObservation = Field(default_factory=SymbolicObservation)


class RuntimeScreenshot(BaseModel):
    screenshot_b64: str | None = None
    media_type: str = "image/png"
    captured_at: str | None = None
    width: int | None = None
    height: int | None = None


class RuntimeActions(BaseModel):
    actions: list[SupportedAction] = Field(default_factory=list)


class VerificationResult(BaseModel):
    action_id: str
    status: VerificationStatus
    expected: dict[str, Any] = Field(default_factory=dict)
    observed: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0


class Diagnosis(BaseModel):
    action_id: str
    failure_type: FailureType | None = None
    confidence: float = 0.0
    cause: str = ""
    repair: str = ""
    should_research: bool = False
    recommended_transition: RecoveryTransition = RecoveryTransition.REPLAN


class ResearchNote(BaseModel):
    query: str
    summary: str
    source_urls: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class SkillActionTemplate(BaseModel):
    type: PrimitiveActionType
    args_template: dict[str, Any] = Field(default_factory=dict)
    adapter: AdapterKind = AdapterKind.GENERIC_INPUT


class SkillFailureMode(BaseModel):
    type: FailureType
    repair: str


class Skill(BaseModel):
    name: str
    version: int = 1
    goal: str
    preconditions: list[str] = Field(default_factory=list)
    ordered_actions: list[SkillActionTemplate] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    failure_modes: list[SkillFailureMode] = Field(default_factory=list)
    source: SkillSource = SkillSource.LEARNED
    confidence: float = 0.0
    status: SkillStatus = SkillStatus.CANDIDATE
    last_verified_at: str | None = None


class AgentEvent(BaseModel):
    id: str
    timestamp: str
    event_type: AgentEventType
    cycle: int = 0
    snapshot_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class BrainHealth(BaseModel):
    brain: TrackStatus = TrackStatus.READY
    runtime: TrackStatus = TrackStatus.UNKNOWN
    memory: TrackStatus = TrackStatus.UNKNOWN
    features: dict[str, bool] = Field(default_factory=dict)


class StartAgentLoopRequest(BaseModel):
    game: str
    goal: str
    user_constraints: list[str] = Field(default_factory=list)
    max_cycles: int = 1
    research_allowed: bool = True


class AgentLoopStatus(BaseModel):
    running: bool = False
    game: str | None = None
    goal: str | None = None
    cycle: int = 0
    transition: RecoveryTransition | None = None
    tracks: dict[str, TrackStatus] = Field(default_factory=dict)
    last_event_id: str | None = None


class StartAgentLoopResponse(BaseModel):
    accepted: bool
    status: AgentLoopStatus


class StopAgentLoopResponse(BaseModel):
    stopped: bool
    status: AgentLoopStatus
