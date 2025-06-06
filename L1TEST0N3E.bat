@echo off
setlocal enabledelayedexpansion

set "TITLE=LiteStone"
title %TITLE%

:: DP0 TO SCRIPT BLOCK, DO NOT MODIFY or MOVE: START
set "ScriptDirectory=%~dp0"
set "ScriptDirectory=%ScriptDirectory:~0,-1%"
cd /d "%ScriptDirectory%"
echo Dp0'd to Script.
:: DP0 TO SCRIPT BLOCK, DO NOT MODIFY or MOVE: END

:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo Error: Admin Required!
    timeout /t 2 >nul
    echo Right Click, Run As Administrator.
    timeout /t 2 >nul
    goto :end_of_script
)
echo Status: Administrator
timeout /t 1 >nul

goto :SkipFunctions

:DisplaySeparatorThick
echo =======================================================================================================================
goto :eof

:DisplaySeparatorThin
echo -----------------------------------------------------------------------------------------------------------------------
goto :eof

:DisplayTitle
call :DisplaySeparatorThick
echo     LiteStone - Batch Menu
call :DisplaySeparatorThin
goto :eof

:MainMenu
cls
color 0F
call :DisplayTitle
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo     1. Run Main Program
echo.
echo     2. Run Installation
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
echo.
call :DisplaySeparatorThick
set /p "choice=Selection; Menu Options = 1-2, Exit Batch = X: "

if /i "%choice%"=="1" (
    echo Starting %TITLE%...
    timeout /t 1 >nul
	
    cls
	call :DisplaySeparatorThick
	echo     L1teSton3e - Launching Program
	call :DisplaySeparatorThick
	echo.
	
    :: Print current working directory
    echo Working Dir: %cd%
    
    :: Use correct venv path (venv instead of .venv)
    call .\venv\Scripts\activate.bat
    echo Activated: `venv`
    
    python.exe .\launcher.py
    
    if errorlevel 1 (
        echo Error launching %TITLE%
        pause
    )
    
    call .\venv\Scripts\deactivate.bat
    echo DeActivated: `venv`
    goto MainMenu
)

if /i "%choice%"=="2" (
    echo Running Installer...
    timeout /t 1 >nul
    cls
    python.exe .\installer.py
    if errorlevel 1 (
        echo Error during installation
        pause
    )
    goto MainMenu
)

if /i "%choice%"=="X" (
    cls
    echo Closing %TITLE%...
    timeout /t 2 >nul
    goto :end_of_script
)

echo Invalid selection. Please try again.
timeout /t 2 >nul
goto MainMenu

:SkipFunctions
goto MainMenu

:end_of_script
cls
color 0F
call :DisplayTitle
echo. 
echo Exit procedure initialized.
echo Exiting in 2 seconds...
timeout /t 2 >nul
exit