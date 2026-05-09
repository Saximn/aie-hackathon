/**
 * Mineflayer runtime entrypoint.
 * TODO(Person A): create the Mineflayer bot, attach perception/action modules,
 * and start the HTTP server from routes.ts.
 */
export async function startRuntime(): Promise<void> {
  throw new Error("TODO: start Mineflayer runtime");
}

if (import.meta.url === `file://${process.argv[1]}`) {
  void startRuntime();
}
