import { forwardRef } from "react";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "./cn";

export type ButtonVariant = "primary" | "secondary" | "ghost";
export type ButtonSize = "sm" | "md";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  /** Optional keyboard-shortcut hint rendered to the right of the label. */
  kbd?: ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "secondary", size = "md", kbd, className, children, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      className={cn(
        "btn",
        `btn-${variant}`,
        size === "sm" && "btn-sm",
        className,
      )}
      {...rest}
    >
      {children}
      {kbd ? <span className="kbd" aria-hidden>{kbd}</span> : null}
    </button>
  );
});
