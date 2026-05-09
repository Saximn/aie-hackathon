import type { ReactNode } from "react";
import { Button } from "./Button";

export interface ErrorStateProps {
  /** Human-readable error message. */
  message: ReactNode;
  /** Optional retry handler — renders a "Retry" button when provided. */
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="error-state" role="alert">
      <div className="row-tight">
        <span aria-hidden>⚠</span>
        <span style={{ flex: 1 }}>{message}</span>
        {onRetry && (
          <Button size="sm" variant="ghost" onClick={onRetry}>
            Retry
          </Button>
        )}
      </div>
    </div>
  );
}
