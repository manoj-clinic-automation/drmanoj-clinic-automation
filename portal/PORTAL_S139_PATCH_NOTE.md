# portal.py — S139 live patch record
The repo's portal/portal.py is STALE against the live /root/portal/portal.py (tile absent from repo).
Live change applied S139 (guarded, count==1, backup portal_BACKUP_S139_pre_https.py on the VPS):
  OLD line 80 url: http://93.127.195.49:8042
  NEW line 80 url: https://attendance.dr-manoj.in   (D224)
To sync the repo: copy /root/portal/portal.py from the VPS into portal/ via WinSCP before commit.
