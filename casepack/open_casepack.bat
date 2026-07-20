@echo off
REM ===========================================================================
REM open_casepack.bat  -  Dr. Manoj Agarwal Clinic  -  Surgical Case Pack tool
REM
REM   Double-click this file to open the Case Pack page in your browser.
REM   It starts a small local program (on THIS PC only) and opens:
REM         http://127.0.0.1:5058/case
REM
REM   Nothing goes to the internet. The follow-up tracker and the Vitals
REM   tool are NOT touched.
REM
REM   To STOP it: close this black window.
REM ===========================================================================

title Surgical Case Pack tool  (leave running - safe to minimize)

cd /d "D:\surgical_casepack"

REM Loop so a one-off glitch cannot silently leave it dead.
:loop
python casepack_app.py
echo.
echo [case pack tool stopped - restarting in 10 seconds; close this window to quit]
timeout /t 10 /nobreak >nul
goto loop
