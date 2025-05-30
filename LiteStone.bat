@echo off
setlocal

REM Get the directory of the batch script
set SCRIPT_DIR=%~dp0

REM Menu loop
:menu
echo.
echo LiteStone Launcher
echo ------------------
echo 1. Run Installer
echo 2. Run Launcher
echo 3. Quit
echo.

REM Get user choice
set /p CHOICE="Enter your choice: "

REM Process user choice
if "%CHOICE%"=="1" (
    echo Running Installer...
    python "%SCRIPT_DIR%installer.py"
    pause
    goto menu
) else if "%CHOICE%"=="2" (
    echo Running Launcher...
    python "%SCRIPT_DIR%launcher.py"
    pause
    goto menu
) else if "%CHOICE%"=="3" (
    echo Exiting...
    goto :eof
) else (
    echo Invalid choice. Please try again.
    pause
    goto menu
)

endlocal
:eof
