# F-17 — the repo's `WebApp.gs` is the PRE-FIX file wearing the live file's name

**Not exploitable.** Repo code does not execute; the live deployment (version 64) has the two
key-setters deleted. **But anyone who opens `dashboard/WebApp.gs` believing the filename reads the
vulnerable source — including the next assistant.**

| | md5 | `setDashboardKey` / `setStaffKey` |
|---|---|---|
| `dashboard/WebApp.gs` **in the repo today** | `276dc197…` | **both still defined** |
| `dashboard/WebApp_v19_D189.gs` **in the repo today** | `5173c3c7…` | absent — **this is what is deployed** |

## Apply

```
git rm  dashboard/WebApp_v19_D189.gs
cp  dashboard_F17_fix/WebApp.gs                     dashboard/WebApp.gs
cp  dashboard_F17_fix/WebApp_PREFIX_ROLLBACK_S129.gs dashboard/WebApp_PREFIX_ROLLBACK_S129.gs
git mv dashboard/CallField.gs.gs dashboard/CallField.gs
git mv dashboard/Probe.gs.gs     dashboard/Probe.gs
```

`WebApp.gs` is now byte-identical to the deployed version 64 (md5 `5173c3c7a9d58e091fa8a49ee97522c9`,
1,647 lines). Verify before committing:

```
md5sum dashboard/WebApp.gs        # 5173c3c7a9d58e091fa8a49ee97522c9
grep -c 'function setDashboardKey(' dashboard/WebApp.gs   # 0  (exits 1 — that is correct)
```

**A filename is not provenance (D188). Assert the md5.**

*No live system is touched by this. It is a repo correction only.*
