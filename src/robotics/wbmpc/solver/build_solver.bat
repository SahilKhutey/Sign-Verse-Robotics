@echo off
setlocal enabledelayedexpansion

echo [Sign-Verse] Searching for Visual Studio Build Tools...
for /f "usebackq tokens=*" %%i in (`"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do (
  set "VS_PATH=%%i"
)

if not defined VS_PATH (
    echo [ERROR] Visual Studio Build Tools not found.
    exit /b 1
)

set "VCVARS=%VS_PATH%\VC\Auxiliary\Build\vcvarsall.bat"
if not exist "%VCVARS%" (
    echo [ERROR] vcvarsall.bat not found at "%VCVARS%"
    exit /b 1
)

echo [Sign-Verse] Configuring environment via %VCVARS%...
call "%VCVARS%" x64

echo [Sign-Verse] Compiling optimized solver...
cl /O2 /LD optimizer.cpp /Fe:optimizer.dll /EHsc

echo [Sign-Verse] Compiling optimized solver...
cl /O2 /LD optimizer.cpp /Fe:optimizer.dll /EHsc

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Compilation failed with status %ERRORLEVEL%.
    exit /b %ERRORLEVEL%
)

echo [SUCCESS] optimizer.dll generated.
