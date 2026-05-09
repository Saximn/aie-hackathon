export interface Position {
  x: number;
  y: number;
  z: number;
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

export interface BridgeRequest {
  id: string;
  method: "connect" | "runJs" | "getState" | "chat" | "disconnect" | "ping";
  params?: Record<string, unknown>;
}

export interface BridgeResponse {
  id: string;
  ok: boolean;
  result?: unknown;
  error?: { message: string; stack?: string };
}

export interface RunJsResult {
  ok: boolean;
  result?: unknown;
  error?: { message: string; stack?: string };
  stateAfter?: SymbolicObservation;
  durationMs: number;
}

export interface ConnectParams {
  host: string;
  port: number;
  username: string;
  version?: string;
}

export interface RunJsParams {
  code: string;
  timeoutMs?: number;
}
