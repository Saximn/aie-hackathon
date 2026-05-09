import type { ReactNode } from "react";

export interface EmptyStateProps {
  /** Single short, helpful sentence. */
  title: ReactNode;
  /** Optional secondary nudge action description. */
  hint?: ReactNode;
  /** Optional CTA slot (Button, link). */
  action?: ReactNode;
}

export function EmptyState({ title, hint, action }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <div className="empty-state__title">{title}</div>
      {hint && <div className="empty-state__hint">{hint}</div>}
      {action && <div style={{ marginTop: 8 }}>{action}</div>}
    </div>
  );
}
