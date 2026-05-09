export type AdapterKind = "generic_input" | "minecraft";

export type TrackStatus = "ready" | "degraded" | "unavailable" | "unknown";

export type VerificationStatus =
  | "success"
  | "incomplete"
  | "failed"
  | "stuck"
  | "unsafe"
  | "invalid_plan";

export type PrimitiveActionType =
  | "press_key"
  | "hold_key"
  | "move_mouse"
  | "click"
  | "wait"
  | "open_menu"
  | "select_hotbar_slot"
  | "move_toward_visible_object"
  | "interact_primary"
  | "collect_block"
  | "craft_item"
  | "build_shelter";

export interface Position {
  x: number;
  y: number;
  z: number;
}

export interface GameProfile {
  game_name: string;
  genre: string;
  controls: Record<string, string>;
  core_mechanics: string[];
  early_game_objectives: string[];
  benchmark_goals: string[];
  adapter_hints: AdapterKind[];
  source: "static" | "researched" | "user" | "fallback";
  confidence: number;
}

export interface VisualObservation {
  scene_summary: string;
  visible_objects: string[];
  risk_level: "low" | "medium" | "high" | "unknown";
  time_of_day: "day" | "night" | "dawn" | "dusk" | "unknown";
  ui_state: "gameplay" | "menu" | "inventory" | "unknown";
  confidence: number;
}

export interface SymbolicObservation {
  health?: number;
  hunger?: number;
  inventory: Record<string, number>;
  nearby_blocks: string[];
  nearby_entities: string[];
  position?: Position;
  biome?: string;
  raw_state: Record<string, unknown>;
}

export interface DerivedRisks {
  night_risk: "low" | "medium" | "high" | "unknown";
  combat_risk: "low" | "medium" | "high" | "unknown";
  food_risk: "low" | "medium" | "high" | "unknown";
}

export interface WorldSnapshot {
  snapshot_id: string;
  cycle: number;
  game: string;
  goal: string;
  visual: VisualObservation;
  symbolic: SymbolicObservation;
  derived_risks: DerivedRisks;
  screenshot_b64?: string;
}

export interface PrimitiveAction {
  id: string;
  type: PrimitiveActionType;
  args: Record<string, unknown>;
  expected_result: Record<string, unknown>;
  timeout_ms: number;
  adapter: AdapterKind;
}

export interface ExecutionResult {
  action_id: string;
  success: boolean;
  result: string;
  evidence: Record<string, unknown>;
}

export interface SupportedAction {
  type: PrimitiveActionType;
  adapter: AdapterKind;
  description: string;
  required_args: string[];
}

export interface RuntimeHealth {
  runtime: TrackStatus;
  adapters: AdapterKind[];
  screenshot_available: boolean;
  symbolic_state_available: boolean;
  version: string;
}

export interface RuntimeState {
  available: boolean;
  game?: string;
  symbolic: SymbolicObservation;
}

export interface RuntimeScreenshot {
  screenshot_b64?: string;
  media_type: "image/png";
  captured_at?: string;
  width?: number;
  height?: number;
}

export interface RuntimeActions {
  actions: SupportedAction[];
}

export interface BrainHealth {
  brain: TrackStatus;
  runtime: TrackStatus;
  memory: TrackStatus;
  features: Record<string, boolean>;
}

export interface StartAgentLoopRequest {
  game: string;
  goal: string;
  user_constraints: string[];
  max_cycles: number;
  research_allowed: boolean;
}

export interface AgentLoopStatus {
  running: boolean;
  game?: string;
  goal?: string;
  cycle: number;
  transition?: string;
  tracks: Record<string, TrackStatus>;
  last_event_id?: string;
}

export interface StartAgentLoopResponse {
  accepted: boolean;
  status: AgentLoopStatus;
}

export interface StopAgentLoopResponse {
  stopped: boolean;
  status: AgentLoopStatus;
}
