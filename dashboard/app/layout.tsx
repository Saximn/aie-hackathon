import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OmniPlay-MC Dashboard",
  description:
    "Live observability for the Voyager-style Minecraft agent: goals, plans, skills, and verdicts.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
