import type { ReactNode } from "react";

export function Panel({
  title,
  subtitle,
  children,
  scroll = true,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  scroll?: boolean;
}) {
  return (
    <div
      style={{
        background: "var(--panel)",
        /* shadow-as-border technique from DESIGN.md */
        boxShadow:
          "rgba(255,255,255,0.08) 0px 0px 0px 1px, rgba(0,0,0,0.3) 0px 2px 8px",
        borderRadius: 12,
        height: "100%",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      <header
        style={{
          padding: "10px 14px",
          borderBottom: "1px solid rgba(255,255,255,0.06)",
          flexShrink: 0,
        }}
      >
        <div
          style={{
            fontWeight: 600,
            fontSize: 13,
            letterSpacing: "-0.2px",
          }}
        >
          {title}
        </div>
        {subtitle ? (
          <div style={{ color: "var(--muted)", fontSize: 11, marginTop: 2 }}>
            {subtitle}
          </div>
        ) : null}
      </header>
      <div
        style={{
          padding: 14,
          flex: 1,
          overflow: scroll ? "auto" : "hidden",
          minHeight: 0,
        }}
      >
        {children}
      </div>
    </div>
  );
}
