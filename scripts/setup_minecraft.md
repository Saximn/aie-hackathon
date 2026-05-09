# Minecraft + Fabric Server Setup (Windows)

OmniPlay-MC needs a local Minecraft Java 1.20.4 client and a Fabric server running with `online-mode=false` so the Mineflayer bridge can connect without Microsoft authentication.

## 1. Install TLauncher (Minecraft Java client)

1. Download TLauncher from https://tlauncher.org/en/.
2. Run the installer; let it create `%APPDATA%\.minecraft`.
3. Launch TLauncher once, log in with any offline username (e.g. `Watcher`), pick **Vanilla 1.20.4**, and let it download.
4. Quit the client. We only needed it to populate `.minecraft\versions\1.20.4`.

## 2. Install the Fabric server

We use Fabric 1.20.4 because Mineflayer's protocol support is well-tested on it.

1. Create a server folder:
   ```
   mkdir C:\mc-server
   cd C:\mc-server
   ```
2. Download `fabric-server-mc.1.20.4-loader.<latest>-launcher.<latest>.jar` from https://fabricmc.net/use/server/. Place it in `C:\mc-server` and rename it to `fabric-server-launcher.jar` for convenience.
3. Run it once to generate config files (it will fail because of the EULA):
   ```
   java -Xmx2G -jar fabric-server-launcher.jar nogui
   ```
4. Open `eula.txt` and change `eula=false` to `eula=true`.
5. Open `server.properties` and ensure these values:
   ```
   online-mode=false
   server-port=25565
   level-name=omniplay-world
   gamemode=survival
   difficulty=easy
   spawn-protection=0
   max-players=4
   enable-rcon=false
   ```
6. (Optional) Pre-generate a small spawn area so the bot doesn't fall through unloaded chunks: leave the server running for a minute after first boot, or use `/forceload add ~ ~` from the server console.

## 3. Connect from the live MC client (spectator)

For the demo, we want a human spectator camera in the same world:

1. Launch TLauncher → Multiplayer → Add Server: `Direct connect localhost:25565`.
2. In-game, type `/op <your-username>` from the server console once.
3. From the client, run `/gamemode spectator` then `/spectate Voyager` after the bot connects.

## 4. Mineflayer bot username

In `.env`, the bot username defaults to `Voyager`. Because the server is `online-mode=false`, no password is needed — Mineflayer connects with `auth: "offline"` (already wired in [`bot/src/adapters/minecraft.ts`](../bot/src/adapters/minecraft.ts)).

## 5. Sanity check

Start the server with [`scripts/start_server.bat`](start_server.bat). You should see:

```
[Server thread/INFO]: Done (X.XXXs)! For help, type "help"
```

Leave it running while the bot bridge and brain run in other terminals.
