/**
 * Thin client for the FastAPI brain at `${NEXT_PUBLIC_BRAIN_URL}`.
 * Centralizes URL config so panels don't repeat the env-var dance.
 */

export const BRAIN_URL =
  process.env.NEXT_PUBLIC_BRAIN_URL ?? "http://localhost:8000";

export const BRAIN_WS_URL =
  process.env.NEXT_PUBLIC_BRAIN_WS_URL ?? "ws://localhost:8000/ws";

export interface StatusResponse {
  running: boolean;
  currentGoal: string | null;
  currentStatus: string;
  cycle: number;
  entrypoint?: string;
  event_count?: number;
}

export interface MetricsResponse {
  uptime_seconds: number;
  total_cycles: number;
  recent_skills: string[];
  last_verdict: string | null;
  last_cycle_ms: number | null;
  queued_tasks: number;
}

export interface AgentEvent {
  id?: string;
  event_type: string;
  cycle?: number | null;
  timestamp?: string;
  snapshot_id?: string | null;
  data: Record<string, unknown>;
  /** Local-only ordering id assigned client-side. */
  _localId?: string;
}

export async function fetchStatus(): Promise<StatusResponse> {
  const res = await fetch(`${BRAIN_URL}/status`);
  if (!res.ok) throw new Error(`status ${res.status}`);
  return res.json();
}

export async function fetchMetrics(): Promise<MetricsResponse> {
  const res = await fetch(`${BRAIN_URL}/metrics`);
  if (!res.ok) throw new Error(`metrics ${res.status}`);
  return res.json();
}

export async function postPrompt(task: string): Promise<{
  accepted: boolean;
  task: string;
  queued_position: number;
}> {
  const res = await fetch(`${BRAIN_URL}/prompt`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task }),
  });
  if (!res.ok) {
    const err = (await res.json().catch(() => ({}))) as { detail?: string };
    throw new Error(err.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}

export function narrationUrl(clipId: string): string {
  const safe = clipId.replace(/[^A-Za-z0-9_-]/g, "");
  return `${BRAIN_URL}/narration/${safe}`;
}
