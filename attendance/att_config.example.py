"""
att_config.py  —  Attendance system settings.

This is the ONLY file you normally edit.
After changing it, restart the dashboard:   systemctl restart attendance-dashboard
(The email job picks up changes automatically on its next run.)

Staff names, per-person timings, Sunday timings, base salary and allowed offs
do NOT live here — they come from staff_master.csv, which is rebuilt from your
salary workbook (Salary_System_2026.xlsx).  See build_staff_master.py.
"""
import os

# --- file locations (leave as-is on the VPS) -------------------------------
PUNCH_CSV    = os.environ.get("ATT_PUNCH_CSV", "/root/punches.csv")
STAFF_MASTER = os.environ.get("ATT_STAFF_MASTER", "/root/staff_master.csv")

# --- who to ignore ---------------------------------------------------------
EXCLUDE_IDS = {100}       # test / admin fingers — never counted

# --- timing rules (match your salary system's Settings sheet) --------------
GRACE_MIN           = 0   # minutes ignored before counting "late"
EARLY_THRESHOLD_MIN = 120 # leaving this many minutes before shift end = "left early"
FLAG_LATE_ON_SUNDAY = False  # Sunday is emergency/half-duty; don't flag late arrivals

# --- live mobile dashboard -------------------------------------------------
DASHBOARD_PORT     = 8042
DASHBOARD_USER     = "clinic"
DASHBOARD_PASSWORD = "change-this-password"    # <-- CHANGE THIS

# --- email reports ---------------------------------------------------------
EMAIL_TO   = ["drmka.ortho@gmail.com"]
EMAIL_FROM = "drmka.ortho@gmail.com"
SMTP_HOST  = "smtp.gmail.com"
SMTP_PORT  = 587
SMTP_USER  = "drmka.ortho@gmail.com"
SMTP_PASS  = ""           # Gmail APP PASSWORD (16 chars). Leave "" to preview to a file.
SEND_ON_SUNDAY = False    # clinic is emergency-only on Sundays; skip the auto-emails
