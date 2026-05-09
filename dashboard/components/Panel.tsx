import type { ReactNode } from "react";

export function Panel({
  title,
  subtitle,
  children,
  scroll = true
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
        border: "1px solid var(--panel-border)",
        borderRadius: 12,
        height: "100%",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden"
      }}
    >
      <header style={{ padding: "10px 14px", borderBottom: "1px solid var(--panel-border)" }}>
        <div style={{ fontWeight: 600, fontSize: 14 }}>{title}</div>
        {subtitle ? (
          <div style={{ color: "var(--muted)", fontSize: 12, marginTop: 2 }}>{subtitle}</div>
        ) : null}
      </header>
      <div style={{ padding: 14, flex: 1, overflow: scroll ? "auto" : "hidden" }}>{children}</div>
    </div>
  );
}
