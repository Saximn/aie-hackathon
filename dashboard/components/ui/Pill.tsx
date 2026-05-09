import type { ReactNode } from "react";
import { cn } from "./cn";

export type PillTone =
  | "neutral"
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "develop"
  | "preview"
  | "ship";

export interface PillProps {
  tone?: PillTone;
  /** Optional leading icon glyph (must be paired with text — never icon-alone). */
  icon?: ReactNode;
  className?: string;
  children: ReactNode;
}

/**
 * Status pill — DESIGN.md §4.
 * Colors are paired with both icon AND text label so we never rely on color
 * alone for state (color-blind safety, per UI/UX accessibility mandate).
 */
export function Pill({ tone = "neutral", icon, className, children }: PillProps) {
  return (
    <span className={cn("pill", `pill-${tone}`, className)}>
      {icon && <span aria-hidden>{icon}</span>}
      {children}
    </span>
  );
}
