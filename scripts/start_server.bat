@echo off
REM Launches the local Fabric Minecraft server for OmniPlay-MC.
REM Expects the server to be installed at %MC_SERVER_DIR% (default C:\mc-server).
REM See scripts\setup_minecraft.md for setup steps.

setlocal

if "%MC_SERVER_DIR%"=="" (
    set MC_SERVER_DIR=C:\mc-server
)

if not exist "%MC_SERVER_DIR%\fabric-server-launcher.jar" (
    echo [start_server] Could not find fabric-server-launcher.jar in %MC_SERVER_DIR%
    echo [start_server] Run scripts\setup_minecraft.md steps 1-2 first.
    exit /b 1
)

cd /d "%MC_SERVER_DIR%"

echo [start_server] Starting Fabric server in %MC_SERVER_DIR% on port 25565
java -Xms2G -Xmx4G -jar fabric-server-launcher.jar nogui

endlocal
