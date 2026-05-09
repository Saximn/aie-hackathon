import type { Metadata } from "next";
import { ConvexClientProvider } from "../components/ConvexClientProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "OmniPlay-MC Dashboard",
  description:
    "Live observability for the Voyager-Plus Minecraft agent: goals, code, skills, and narration."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ConvexClientProvider>{children}</ConvexClientProvider>
      </body>
    </html>
  );
}
