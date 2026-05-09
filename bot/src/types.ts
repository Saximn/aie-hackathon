export type VerificationStatus =
  | "success"
  | "incomplete"
  | "failed"
  | "stuck"
  | "unsafe"
  | "invalid_plan";

export type PrimitiveActionType =
  | "move_to"
  | "mine_block"
  | "craft"
  | "equip"
  | "eat"
  | "attack_nearest"
  | "sleep"
  | "place_block"
  | "chat"
  | "explore"
  | "look_around"
  | "call_skill";

export interface Position {
  x: number;
  y: number;
  z: number;
}

export interface InventoryItem {
  name: string;
  count: number;
}

export interface WorldState {
  position: Position;
  health: number;
  food: number;
  inventory: InventoryItem[];
  nearbyBlocks: string[];
  nearbyEntities: string[];
  biome?: string;
  timeOfDay?: string;
  isDay?: boolean;
}

export interface PrimitiveAction {
  id?: string;
  type: PrimitiveActionType;
  args: Record<string, unknown>;
  expectedResult?: Record<string, unknown>;
  timeoutS?: number;
  failurePolicy?: string;
}

export interface ExecutionResult {
  actionId?: string;
  success: boolean;
  result: string;
  evidence?: Record<string, unknown>;
}

export interface SupportedAction {
  type: PrimitiveActionType;
  description: string;
  requiredArgs: string[];
}
