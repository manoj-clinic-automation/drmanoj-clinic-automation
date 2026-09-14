# S259_OFF_SWITCHES — Club C.2

*Session 256 · 14-Sep-2026 · D511 · the four PC-side jobs that had no way to be stopped*

## What this is

Every job on the two Windows PCs ran with no way to stop it short of killing a
scheduled task or a process. This gives each one the same OFF switch the server
already has (`/root/finance/AUTOAPPLY_OFF`, D488): **a file whose presence
stops the job, and whose absence starts it again.** Nothing is stopped,
uninstalled, unregistered or restarted in either direction — each job reads the
folder when it next comes round and does what it finds.

## The switches

### manojz — `D:\Downloads\margsync\_off\`

| file | stops |
|---|---|
| `ALL_OFF.txt` | everything on this PC that talks to the clinic server |
| `PULL_WATCHDOG_OFF.txt` | the 15-minute pull-asleep check |
| `PUSH_STOCK_OFF.txt` | the stock push — daily and the 22:30 nightly |

Two double-clicks do it without touching files by hand:

```
D:\Downloads\margsync\TURN_OFF_ALL.bat
```

```
D:\Downloads\margsync\TURN_ON_ALL.bat
```

### the medical PC — `D:\SendToClinic\_off\`

| file | stops |
|---|---|
| `ALL_OFF.txt` | the **sending** of captured exports. Capture keeps running. |
| `MARG_PUSH_OFF.txt` | the sending alone |
| `MARG_WATCH_OFF.txt` | **capture itself** — its own separate, deliberate marker |

**`ALL_OFF` does not stop capture, and that is the design.** Marg reuses one
file name for every export, so an export that is not captured in that instant
is gone for ever. Everything else in this system can be paused and caught up;
capture cannot. Stopping it therefore takes a file named for it, put there on
purpose.

## What changed in each file

| file | machine | change |
|---|---|---|
| `pull_watchdog.py` | manojz | `off_marker()`; `main()` exits 0 with one logged line before it reads or writes anything |
| `PUSH_STOCK_DAILY.bat` | manojz | both markers tested before the kit check; `:off` branch logs one line and exits 0 |
| `PUSH_STOCK_NIGHTLY.bat` | manojz | same, before step 1 — so none of the three steps runs |
| `marg_push.py` | medical | `off_marker()`; guarded in `run_once()` *and* at the top of every 60-second pass in `loop()`, logging only when the state changes |
| `marg_watch.py` | medical | `watch_off()`; the capture loop idles and drains the event queue while the marker is there |

Nothing else in any of the five files is touched. Each was built from the live
bytes and the from-pins are gated in the installer.

## From-pins and to-pins

| file | from | to |
|---|---|---|
| `pull_watchdog.py` | `f0eb9f40a0cd06875aba107b12151a73` | `8d7fc79d12e3f8bbbdeaeb04289e0787` |
| `PUSH_STOCK_DAILY.bat` | `73a0635ba6164ec8da8c8f61de9d3210` | `5c2a6c9098a783ef12f442e14697af34` |
| `PUSH_STOCK_NIGHTLY.bat` | `99d05e3f7f05d472413c864d1665ccea` | `c2492438c9f77169c418ac133513ad75` |
| `marg_push.py` | `630fc5efeac89513d5b0d057df9e0639` | `566e189e986128fa2ebb341a78b9ab65` |
| `marg_watch.py` | `581ff3a7bc9493602172ef9765af2f2f` | `9f0bf9c4c5fc285d339541ef3c76179f` |

The medical files were built from `D:\Downloads\margsync\medical_SendToClinic\`,
which was confirmed byte-exact against the S240 live pins before a line was
changed.

## Proof

`walk_s259.py` — **30 checks, all green**, on real copies, offline:
the watchdog stops and starts on either marker without a restart and writes
nothing while off; the pusher sends nothing and writes no state file while off;
capture really stops and really starts again without a restart; and `ALL_OFF`
really does leave capture running. The two `.bat` files' OFF branch is proved
here by reading (no `cmd.exe` off Windows — F-443) **and by running** inside
`install_s259.py` on manojz itself.

`marg_push.py --selftest` 11/11 · `marg_watch.py --selftest` 6/6.

## Installing

**manojz — one double-click:**

```
D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S259_OFF_SWITCHES\manojz\INSTALL_S259_MANOJZ.bat
```

It gates on the from-pins, backs up, installs, builds the `_off` folder, runs
the walk on the machine, and puts the old files back by itself if any part of
the walk fails. It leaves everything switched on.

**the medical PC** — `marg_push.py`, `marg_watch.py`, `TURN_OFF_ALL.bat`,
`TURN_ON_ALL.bat` and `_off_READ_ME.txt` (as `_off\READ_ME.txt`) go down the
agent's Drive kit channel into `D:\SendToClinic\`. Not installed by this kit.
