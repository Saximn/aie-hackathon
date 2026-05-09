import mineflayer, { type Bot } from "mineflayer";
import type { Position, SymbolicObservation } from "../types.js";

interface AdapterConfig {
  host: string;
  port: number;
  username: string;
  version?: string;
}

class MinecraftAdapter {
  private bot: Bot | null = null;
  private connected = false;
  private connecting: Promise<void> | null = null;
  private lastError: string | null = null;
  private config: AdapterConfig | null = null;

  isReady(): boolean {
    return this.connected && this.bot !== null;
  }

  status(): { connected: boolean; lastError: string | null; config: AdapterConfig | null } {
    return { connected: this.connected, lastError: this.lastError, config: this.config };
  }

  async connect(config: AdapterConfig): Promise<void> {
    if (this.connecting) {
      return this.connecting;
    }
    this.config = config;
    this.connecting = new Promise<void>((resolve, reject) => {
      try {
        const bot = mineflayer.createBot({
          host: config.host,
          port: config.port,
          username: config.username,
          version: config.version,
          auth: "offline"
        });
        const onSpawn = () => {
          this.bot = bot;
          this.connected = true;
          this.lastError = null;
          bot.removeListener("error", onError);
          bot.removeListener("end", onEnd);
          bot.on("error", (err) => {
            this.lastError = err.message;
          });
          bot.on("end", () => {
            this.connected = false;
            this.bot = null;
          });
          resolve();
        };
        const onError = (err: Error) => {
          this.lastError = err.message;
          this.connected = false;
          this.bot = null;
          bot.removeListener("spawn", onSpawn);
          reject(err);
        };
        const onEnd = () => {
          this.connected = false;
          this.bot = null;
          bot.removeListener("spawn", onSpawn);
          reject(new Error("connection ended before spawn"));
        };
        bot.once("spawn", onSpawn);
        bot.once("error", onError);
        bot.once("end", onEnd);
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        this.lastError = message;
        reject(err instanceof Error ? err : new Error(message));
      }
    }).finally(() => {
      this.connecting = null;
    });
    return this.connecting;
  }

  disconnect(): void {
    if (this.bot) {
      this.bot.quit("adapter disconnect");
      this.bot = null;
    }
    this.connected = false;
  }

  async readSymbolicState(): Promise<SymbolicObservation> {
    if (!this.bot || !this.connected) {
      throw new Error("minecraft adapter not connected");
    }
    const bot = this.bot;
    const inventory: Record<string, number> = {};
    for (const item of bot.inventory.items()) {
      inventory[item.name] = (inventory[item.name] ?? 0) + item.count;
    }

    const blockRadius = 5;
    const nearbyBlocks = this.collectNearbyBlocks(blockRadius);
    const nearbyEntities = Object.values(bot.entities)
      .filter((e) => e.id !== bot.entity.id && e.position.distanceTo(bot.entity.position) < 16)
      .map((e) => e.name ?? e.username ?? e.displayName ?? "unknown")
      .filter((name): name is string => typeof name === "string")
      .slice(0, 30);

    const position: Position = {
      x: bot.entity.position.x,
      y: bot.entity.position.y,
      z: bot.entity.position.z
    };

    let biome: string | undefined;
    try {
      const biomeId = bot.world.getBiome(bot.entity.position);
      const registry = (bot as unknown as { registry?: { biomes?: Record<number, { name: string }> } }).registry;
      biome = registry?.biomes?.[biomeId as unknown as number]?.name;
    } catch {
      biome = undefined;
    }

    return {
      health: bot.health,
      hunger: bot.food,
      inventory,
      nearby_blocks: nearbyBlocks,
      nearby_entities: nearbyEntities,
      position,
      biome,
      raw_state: {
        adapter: "minecraft",
        gameMode: bot.game.gameMode,
        timeOfDay: bot.time.timeOfDay,
        isRaining: bot.isRaining,
        username: bot.username
      }
    };
  }

  private collectNearbyBlocks(radius: number): string[] {
    if (!this.bot) return [];
    const bot = this.bot;
    const counts: Record<string, number> = {};
    const origin = bot.entity.position.floored();
    for (let dx = -radius; dx <= radius; dx++) {
      for (let dy = -radius; dy <= radius; dy++) {
        for (let dz = -radius; dz <= radius; dz++) {
          const block = bot.blockAt(origin.offset(dx, dy, dz));
          if (block && block.name !== "air" && block.name !== "cave_air") {
            counts[block.name] = (counts[block.name] ?? 0) + 1;
          }
        }
      }
    }
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 20)
      .map(([name, count]) => `${name}:${count}`);
  }

  async collectBlock(_block: string, _count: number, _radius: number, _timeoutMs: number): Promise<Record<string, unknown>> {
    throw new Error("collect_block not implemented; use generic_input actions or install mineflayer-pathfinder + mineflayer-collectblock");
  }

  async craftItem(_item: string, _count: number, _timeoutMs: number): Promise<Record<string, unknown>> {
    throw new Error("craft_item not implemented; use generic_input actions to navigate crafting UI");
  }

  async buildShelter(_material: string, _width: number, _depth: number, _height: number, _timeoutMs: number): Promise<Record<string, unknown>> {
    throw new Error("build_shelter not implemented");
  }
}

const adapter = new MinecraftAdapter();

export function getMinecraftAdapter(): MinecraftAdapter {
  return adapter;
}

export function isMinecraftAdapterReady(): boolean {
  return adapter.isReady();
}

export async function tryConnectMinecraft(config: AdapterConfig): Promise<boolean> {
  try {
    await adapter.connect(config);
    return true;
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.error(`[minecraft adapter] connect failed: ${message}`);
    return false;
  }
}
