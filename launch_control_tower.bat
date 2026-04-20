@echo off
TITLE SIGN-VERSE | CONTROL TOWER LAUNCHER
COLOR 0B
CLS

echo.
echo  #################################################################
echo  #                                                               #
echo  #          SIGN-VERSE ROBOTICS : CONTROL TOWER V5.1             #
echo  #          -----------------------------------------            #
echo  #             INITIALIZING HIGH-FREQUENCY UPLINK                #
echo  #                                                               #
echo  #################################################################
echo.

:: Check for Python environment
IF NOT EXIST ".venv_312\Scripts\python.exe" (
    echo [ERROR] Virtual environment .venv_312 not found.
    pause
    exit /b
)

echo [1/3] ACTIVATING INTELLIGENCE CORE (BACKEND)...
start "SIGN-VERSE BACKEND" cmd /k ".\.venv_312\Scripts\python.exe -m src.core.main"

echo [2/3] INITIALIZING KINETIC OBSIDIAN HUD (FRONTEND)...
cd dashboard
start "SIGN-VERSE DASHBOARD" cmd /k "npm run dev"
cd ..

echo [3/3] OPENING COMMAND INTERFACE...
timeout /t 5 >nul
start http://localhost:3001

echo.
echo #################################################################
echo #              SYSTEMS NOMINAL - UPLINK STABLE                  #
echo #################################################################
echo.
echo Keep this window open to monitor launch sequence status.
pause
