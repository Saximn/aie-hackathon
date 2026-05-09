export type AdapterKind = "generic_input" | "minecraft";

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
  gameName: string;
  genre: string;
  controls: Record<string, string>;
  coreMechanics: string[];
  earlyGameObjectives: string[];
  benchmarkGoals: string[];
  adapterHints: AdapterKind[];
  source: "static" | "researched" | "user";
  confidence: number;
}

export interface VisualObservation {
  sceneSummary: string;
  visibleObjects: string[];
  riskLevel: "low" | "medium" | "high" | "unknown";
  timeOfDay: "day" | "night" | "dawn" | "dusk" | "unknown";
  uiState: "gameplay" | "menu" | "inventory" | "unknown";
  confidence: number;
}

export interface SymbolicObservation {
  health?: number;
  hunger?: number;
  inventory: Record<string, number>;
  nearbyBlocks: string[];
  nearbyEntities: string[];
  position?: Position;
  biome?: string;
  rawState: Record<string, unknown>;
}

export interface DerivedRisks {
  nightRisk: "low" | "medium" | "high" | "unknown";
  combatRisk: "low" | "medium" | "high" | "unknown";
  foodRisk: "low" | "medium" | "high" | "unknown";
}

export interface WorldSnapshot {
  snapshotId: string;
  cycle: number;
  game: string;
  goal: string;
  visual: VisualObservation;
  symbolic: SymbolicObservation;
  derivedRisks: DerivedRisks;
  screenshotB64?: string;
}

export interface PrimitiveAction {
  id: string;
  type: PrimitiveActionType;
  args: Record<string, unknown>;
  expectedResult: Record<string, unknown>;
  timeoutMs: number;
  adapter: AdapterKind;
}

export interface ExecutionResult {
  actionId: string;
  success: boolean;
  result: string;
  evidence: Record<string, unknown>;
}

export interface SupportedAction {
  type: PrimitiveActionType;
  adapter: AdapterKind;
  description: string;
  requiredArgs: string[];
}
