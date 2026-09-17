# S296_ATTENDANCE_NAMES

**One line on the VPS:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S296_ATTENDANCE_NAMES/install_S296_ATTENDANCE_NAMES.sh
```

The S295 map showed two logins that open nothing under *Meri attendance*: **sandeep** (staff row *Sandip*) and **vikky** (staff row *Vikki*). The spellings differ, so the register's two rules (username, then first name) find neither. This kit writes `staff.username` on those two rows only — guarded (active staff/manager login, exactly one active row with that first name, row's username empty, login not used elsewhere; one refusal writes nothing), backed up first with sqlite's backup API, read back, and proven by the attendance map. Red after the write clears exactly those two usernames again. No restart.

New logins for Pravesh, Arjun and Ranjeet need nothing from a kit: if the login is the first name, the register finds them by itself.

**Proof:** `set_usernames_s296.py --selftest` 11 checks (negative controls red at 2, 3, 11 and on a removed backup) · installer rehearsed on a fake root: install, ALREADY INSTALLED, guard refusal, restore.
