"use client";

import { ConvexReactClient } from "convex/react";

const url = process.env.NEXT_PUBLIC_CONVEX_URL;

if (!url) {
  // eslint-disable-next-line no-console
  console.warn(
    "NEXT_PUBLIC_CONVEX_URL is not set; the dashboard will render in placeholder mode."
  );
}

export const convexClient = new ConvexReactClient(url ?? "https://placeholder.convex.cloud");
