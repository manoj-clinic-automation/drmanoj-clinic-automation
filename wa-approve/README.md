# wa-approve — WABA follow-up "list → approve → send" bridge (Session 64)

Three files, all run on the VPS in /root/wa/ (alongside the reused `followup-tracker/waba.py`):

- **plan_followups_from_xlsx.py** — DRY-RUN planner. Reads today's Staff_Action_Today_*.xlsx from
  /root/wa/followup-inbox/, groups by STATUS section, maps to approved templates, prints the plan.
  Sends nothing (no --send flag).
- **wa_approve.py** — Flask approve/deselect page on 127.0.0.1:8101, exposed via OLS at /wa-approve.
  Key-gated (?k=), TEST-mode default (routes to WA_TEST_NUMBER until LIVE ticked), daily-cap check.
  Reuses waba.py to send. Config in wa_approve.env (chmod 600, NOT committed).
- **inspect_dupes.py** — read-only duplicate inspector (same-name+same-number diagnostic).

SECRETS: none in these files. wa_approve.env (WA_APPROVE_KEY, WA_TEST_NUMBER) and the MyOperator
send token (MYOP_AUTH_TOKEN in /root/wa/.env) stay on the VPS only, gitignored.

STATUS: bridge LIVE end-to-end; WABA sends blocked vendor-side by MyOperator
AuthorizerConfigurationException (500) — see KB D120.
