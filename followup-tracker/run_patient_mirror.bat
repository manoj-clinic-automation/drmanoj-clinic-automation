@echo off
REM ---------------------------------------------------------------------------
REM run_patient_mirror.bat
REM Nightly one-way push of patient_master.csv -> Patient_Master tab.
REM Keeps a running log in patient_mirror_log.txt so you can confirm it ran.
REM ---------------------------------------------------------------------------

cd /d C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker

echo ==================================================>> patient_mirror_log.txt
echo Run started: %date% %time%>> patient_mirror_log.txt
python push_patient_mirror.py --push >> patient_mirror_log.txt 2>&1
echo Run ended:   %date% %time%>> patient_mirror_log.txt
echo.>> patient_mirror_log.txt
