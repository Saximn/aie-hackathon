import type { ReactNode } from "react";
import { cn } from "./cn";

export type PanelVariant = "default" | "primary" | "flat";

export interface PanelProps {
  title?: ReactNode;
  /** Slot rendered on the right of the header (subtitle, status pill, tabs). */
  trailing?: ReactNode;
  /** Optional sub-row rendered below the title row (e.g. filter tabs). */
  toolbar?: ReactNode;
  variant?: PanelVariant;
  /** Disable inner padding (use when child supplies its own padding). */
  flush?: boolean;
  className?: string;
  children: ReactNode;
}

/**
 * Surface container with shadow-as-border per DESIGN.md §6.
 * - `primary` is the dominant card shadow stack (use sparingly — one per page).
 * - `flat` is ring-only (no lift) for chrome (StatusBar, MetricsRibbon).
 */
export function Panel({
  title,
  trailing,
  toolbar,
  variant = "default",
  flush = false,
  className,
  children,
}: PanelProps) {
  return (
    <section
      className={cn(
        "panel",
        variant === "primary" && "panel-primary",
        variant === "flat" && "panel-flat",
        className,
      )}
    >
      {(title || trailing) && (
        <header className="panel__header">
          {title && <div className="panel__title">{title}</div>}
          {trailing && <div className="panel__subtitle">{trailing}</div>}
        </header>
      )}
      {toolbar && (
        <div
          className="panel__header"
          style={{ minHeight: 0, paddingTop: 0, paddingBottom: 12 }}
        >
          {toolbar}
        </div>
      )}
      <div className={cn("panel__body", flush && "panel__body--flush")}>
        {children}
      </div>
    </section>
  );
}
