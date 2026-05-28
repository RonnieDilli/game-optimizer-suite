@echo off
setlocal EnableDelayedExpansion
net session >nul 2>&1
if %errorLevel% neq 0 exit /b 1

net stop NVDisplay.ContainerLocalSystem /y >nul 2>&1
timeout /t 1 >nul

RD /S /Q "%LocalAppData%\NVIDIA\DXCache" >nul 2>&1
RD /S /Q "%LocalAppData%\NVIDIA\GLCache" >nul 2>&1
RD /S /Q "%LocalAppData%\AMD\DxCache" >nul 2>&1

net start NVDisplay.ContainerLocalSystem >nul 2>&1
exit /b 0
