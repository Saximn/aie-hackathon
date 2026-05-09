"use client";

import { useEffect, useRef, useState } from "react";
import { BRAIN_WS_URL, type AgentEvent } from "./brain";

export type ConnectionState = "connecting" | "open" | "reconnecting" | "closed";

export interface UseEventStreamOptions {
  /** Cap retained events (per UI/UX spec — keep last 500). */
  bufferSize?: number;
  /** Optional URL override (testing). */
  url?: string;
}

export interface UseEventStreamReturn {
  events: AgentEvent[];
  state: ConnectionState;
  /** Forcibly drop and reconnect (used by retry buttons). */
  reconnect: () => void;
}

export function useEventStream(
  opts: UseEventStreamOptions = {},
): UseEventStreamReturn {
  const bufferSize = opts.bufferSize ?? 500;
  const url = opts.url ?? BRAIN_WS_URL;

  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [state, setState] = useState<ConnectionState>("connecting");
  const counterRef = useRef(0);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTickRef = useRef(0);

  useEffect(() => {
    let cancelled = false;
    let retry: ReturnType<typeof setTimeout> | undefined;

    function connect() {
      if (cancelled) return;
      setState((s) => (s === "open" ? "open" : "connecting"));
      let ws: WebSocket;
      try {
        ws = new WebSocket(url);
      } catch {
        if (!cancelled) {
          setState("reconnecting");
          retry = setTimeout(connect, 3000);
        }
        return;
      }
      wsRef.current = ws;

      ws.onopen = () => {
        if (cancelled) return;
        setState("open");
      };

      ws.onmessage = (msg: MessageEvent) => {
        try {
          const evt = JSON.parse(msg.data as string) as AgentEvent;
          evt._localId = String(++counterRef.current);
          if (!cancelled) {
            setEvents((prev) => {
              const next = prev.length >= bufferSize
                ? prev.slice(prev.length - bufferSize + 1)
                : prev;
              return [...next, evt];
            });
          }
        } catch {
          /* drop malformed frames */
        }
      };

      ws.onclose = () => {
        if (cancelled) return;
        setState("reconnecting");
        retry = setTimeout(connect, 3000);
      };

      ws.onerror = () => {
        try {
          ws.close();
        } catch {
          /* noop */
        }
      };
    }

    connect();
    return () => {
      cancelled = true;
      if (retry) clearTimeout(retry);
      try {
        wsRef.current?.close();
      } catch {
        /* noop */
      }
    };
    // reconnectTickRef.current change re-runs effect via deps
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, bufferSize, reconnectTickRef.current]);

  return {
    events,
    state,
    reconnect: () => {
      reconnectTickRef.current++;
      try {
        wsRef.current?.close();
      } catch {
        /* noop */
      }
    },
  };
}
