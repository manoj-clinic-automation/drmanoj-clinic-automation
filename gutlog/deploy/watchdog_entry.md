# Watchdog integration (clinic-watchdog.service)

GutLog is registered in the always-on service monitor at
`/root/wa/clinic_watchdog.py`, which runs `systemctl is-active` on each
service, stays silent when all are healthy, and sends the morning all-ok
(and a down-alert via ntfy/email if any service stops).

## The line that was added
Inside the `SERVICES = [ ... ]` list, immediately after the `clinic-portal`
entry:

```python
    ("gutlog.service", "GutLog health diary (web)", "systemctl restart gutlog"),
```

Tuple shape is `(unit, human_label, fix_command)`. This brought the guarded
count from 9 to 10 services.

## How it was inserted (idempotent, paste-safe one-liner)
```bash
python3 -c 'f="/root/wa/clinic_watchdog.py"; s=open(f).read(); m="\"systemctl restart clinic-portal\"),\n"; n="    (\"gutlog.service\", \"GutLog health diary (web)\", \"systemctl restart gutlog\"),\n"; open(f,"w").write(s if "gutlog.service" in s else s.replace(m, m+n, 1)); print("gutlog present:", "gutlog.service" in open(f).read())'
```

## Verify + apply
```bash
python3 -m py_compile /root/wa/clinic_watchdog.py && echo OK   # must print OK
grep -cE '^\s+\("[a-z].*\.service"' /root/wa/clinic_watchdog.py # must print 10
systemctl restart clinic-watchdog
journalctl -u clinic-watchdog -n 15 --no-pager                 # "10 services healthy"
```
Backup of the watchdog before editing: `/root/wa/clinic_watchdog.py.bak`.
