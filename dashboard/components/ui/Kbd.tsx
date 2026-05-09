import type { ReactNode } from "react";
import { cn } from "./cn";

export function Kbd({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <span className={cn("kbd", className)}>{children}</span>;
}
