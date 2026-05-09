import { cn } from "./cn";

export interface SkeletonProps {
  height?: number | string;
  width?: number | string;
  className?: string;
  /** Stack of N rows, with the last one shorter. */
  rows?: number;
}

export function Skeleton({ height = 12, width, className, rows }: SkeletonProps) {
  if (rows && rows > 0) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {Array.from({ length: rows }).map((_, i) => (
          <div
            key={i}
            className={cn("skeleton", className)}
            style={{
              height,
              width: i === rows - 1 ? "60%" : width ?? "100%",
            }}
          />
        ))}
      </div>
    );
  }
  return (
    <div
      className={cn("skeleton", className)}
      style={{ height, width: width ?? "100%" }}
    />
  );
}
