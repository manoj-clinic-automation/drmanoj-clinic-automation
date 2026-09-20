# S350_FRESHNESS_CLOCK — the freshness page's "written N ago" reads the real clock

*Session 276 (parent) · 20-Sep-2026 · over S349, which is frozen (F-512).*

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S350_FRESHNESS_CLOCK/install_S350_FRESHNESS_CLOCK.sh
```

S349 went live at 12:42 IST and the page was read at once in the owner's browser: 31 legs · 31 OK, the collector's
table served exactly — and the banner said **"0 min ago"** for a file the installer had just called **277 min old**.
Cause: `_banner()` took *now* from `datetime.utcnow().timestamp()`, which on a box whose local clock is IST is
5.5 hours behind the epoch, so the age came out negative and was clamped to zero. **S349's walk could not see it
because it handed `render()` its own clock** — the F-581 lesson in a new shape: a walk that supplies the very input
the defect lives in proves nothing about that input. One line changed: `time.time()`. `finance_app.py` is untouched.

**Proof:** the S349 module checks again (12) plus **the real clock under `TZ=Asia/Kolkata`**: a file 3 h old reads
"3.0 h ago", and the negative control — the S349 bytes on the same file and clock — reads "0 min ago". Installer:
the live module must be S349's (`dc60a4c6`) or already this kit's; backup `.bak_S350_*`; py_compile; restart;
healthz 200; any red puts S349's file back.
