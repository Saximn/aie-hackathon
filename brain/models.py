"""Shared SkillForge AI Brain contracts.

These models define the module boundaries before implementation. Keep this file
as the source of truth for Python-side contracts.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class PrimitiveActionType(StrEnum):
    MOVE_TO = "move_to"
    MINE_BLOCK = "mine_block"
    CRAFT = "craft"
    EQUIP = "equip"
    EAT = "eat"
    ATTACK_NEAREST = "attack_nearest"
    SLEEP = "sleep"
    PLACE_BLOCK = "place_block"
    CHAT = "chat"
    EXPLORE = "explore"
    LOOK_AROUND = "look_around"
    CALL_SKILL = "call_skill"


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
    CRAFTING_FAILURE = "crafting_failure"
    COMBAT_RISK = "combat_risk"
    ENVIRONMENT_CHANGED = "environment_changed"
    BAD_PLAN_ORDERING = "bad_plan_ordering"
    AMBIGUOUS_ACTION = "ambiguous_action"
    UNSUPPORTED_ACTION = "unsupported_action"
    MISSING_STRATEGY = "missing_strategy"
    TIMEOUT = "timeout"


class RecoveryTransition(StrEnum):
    CONTINUE = "continue"
    RETRY = "retry"
    REPLAN = "replan"
    RESEARCH = "research"
    ABORT = "abort"
    STORE_MEMORY = "store_memory"
    PROMOTE_SKILL = "promote_skill"
    DEMOTE_SKILL = "demote_skill"


class SkillSource(StrEnum):
    SEEDED = "seeded"
    LEARNED = "learned"
    RESEARCHED = "researched"
    USER = "user"


class DashboardEventType(StrEnum):
    STATE = "state"
    PLAN = "plan"
    ACTION = "action"
    EXECUTION = "execution"
    VERIFICATION = "verification"
    DIAGNOSIS = "diagnosis"
    RECOVERY = "recovery"
    RESEARCH = "research"
    SKILL = "skill"
    MEMORY = "memory"
    ERROR = "error"


class Position(BaseModel):
    x: float
    y: float
    z: float


class InventoryItem(BaseModel):
    name: str
    count: int


class WorldSnapshot(BaseModel):
    snapshot_id: str
    cycle: int
    raw_state: dict[str, Any] = Field(default_factory=dict)
    position: Position | None = None
    health: float | None = None
    food: float | None = None
    inventory: list[InventoryItem] = Field(default_factory=list)
    nearby_blocks: list[str] = Field(default_factory=list)
    nearby_entities: list[str] = Field(default_factory=list)
    biome: str | None = None
    time_of_day: str | None = None
    is_day: bool | None = None
    screenshot_b64: str | None = None


class PrimitiveAction(BaseModel):
    id: str
    type: PrimitiveActionType
    args: dict[str, Any] = Field(default_factory=dict)
    expected_result: dict[str, Any] = Field(default_factory=dict)
    timeout_s: int = 20
    failure_policy: str = "diagnose"


class Plan(BaseModel):
    goal: str
    snapshot_id: str
    used_skills: list[str] = Field(default_factory=list)
    actions: list[PrimitiveAction] = Field(default_factory=list)


class ExecutionResult(BaseModel):
    action_id: str
    success: bool
    result: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class VerificationResult(BaseModel):
    action_id: str
    status: VerificationStatus
    expected: dict[str, Any] = Field(default_factory=dict)
    actual: dict[str, Any] = Field(default_factory=dict)
    evidence: dict[str, Any] = Field(default_factory=dict)


class Diagnosis(BaseModel):
    action_id: str
    failure_type: FailureType | None = None
    confidence: float = 0.0
    reason: str = ""
    recommended_transition: RecoveryTransition = RecoveryTransition.REPLAN


class SkillActionTemplate(BaseModel):
    type: PrimitiveActionType
    args_template: dict[str, Any] = Field(default_factory=dict)


class Skill(BaseModel):
    name: str
    version: int = 1
    goal: str
    preconditions: list[str] = Field(default_factory=list)
    ordered_action_templates: list[SkillActionTemplate] = Field(default_factory=list)
    success_criteria: dict[str, Any] = Field(default_factory=dict)
    failure_modes: list[FailureType] = Field(default_factory=list)
    source: SkillSource = SkillSource.LEARNED
    confidence: float = 0.0
    last_verified_at: str | None = None


class DashboardEvent(BaseModel):
    id: str
    ts: float
    cycle: int
    snapshot_id: str | None = None
    type: DashboardEventType
    data: dict[str, Any] = Field(default_factory=dict)
