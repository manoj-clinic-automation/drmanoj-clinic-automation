@echo off
REM ===========================================================================
REM open_vitals.bat  -  Dr. Manoj Agarwal Clinic  -  Vitals & Plan tool
REM
REM   Double-click this file to open the Vitals & Plan page in your browser.
REM   It starts a small local program (on THIS PC only) and opens:
REM         http://127.0.0.1:5057/vitals
REM
REM   Nothing goes to the internet. The live follow-up tracker is NOT touched.
REM
REM   To STOP it: close this black window.
REM ===========================================================================

title Vitals & Plan tool  (leave running - safe to minimize)

cd /d "D:\clinic_writer"

REM Loop so a one-off glitch cannot silently leave it dead.
:loop
python vitals_app.py
echo.
echo [vitals tool stopped - restarting in 10 seconds; close this window to quit]
timeout /t 10 /nobreak >nul
goto loop
