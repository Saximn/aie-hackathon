import screenshot from "screenshot-desktop";
import type { SymbolicObservation } from "./types.js";
import { getMinecraftAdapter, isMinecraftAdapterReady } from "./adapters/minecraft.js";

export async function readSymbolicState(): Promise<SymbolicObservation> {
  if (isMinecraftAdapterReady()) {
    return getMinecraftAdapter().readSymbolicState();
  }
  return {
    inventory: {},
    nearbyBlocks: [],
    nearbyEntities: [],
    rawState: { adapter: "generic_input", note: "no symbolic state available; brain must rely on VLM" }
  };
}

export async function readScreenshot(): Promise<Buffer> {
  return screenshot({ format: "png" });
}
