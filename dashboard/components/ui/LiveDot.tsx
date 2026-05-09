import { cn } from "./cn";

export type LiveDotTone = "success" | "warning" | "danger" | "info" | "neutral";

export interface LiveDotProps {
  tone?: LiveDotTone;
  /** Subtle pulse animation — only when streaming/live. */
  pulse?: boolean;
  className?: string;
  ariaLabel?: string;
}

export function LiveDot({
  tone = "success",
  pulse = false,
  className,
  ariaLabel,
}: LiveDotProps) {
  return (
    <span
      role="status"
      aria-label={ariaLabel}
      className={cn("dot", `dot-${tone}`, pulse && "dot-pulse", className)}
    />
  );
}
