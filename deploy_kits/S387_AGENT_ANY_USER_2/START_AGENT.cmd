@echo off
REM S386/S387 -- starts the ONE medical agent for this machine, whichever Windows account signs in.
REM Put in the all-users start-up folder by INSTALL_S386.bat. agent_guard.py decides whether this
REM account runs the agent or stands by for another. Do not edit; do not copy elsewhere.
start "" /min "D:\SendToClinic\pyportable\pythonw.exe" "D:\SendToClinic\agent_guard.py"
