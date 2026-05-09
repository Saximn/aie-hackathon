/**
 * OmniForge runtime entrypoint.
 *
 * TODO(Person A): start the HTTP server and attach the selected adapters.
 */
export async function startRuntime(): Promise<void> {
  throw new Error("TODO: start OmniForge runtime");
}

if (import.meta.url === `file://${process.argv[1]}`) {
  void startRuntime();
}
