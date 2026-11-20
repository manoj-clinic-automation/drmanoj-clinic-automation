# S900_ENGINE_PY39 — the tracker's engine stands on the box's Python 3.9 (the parent, S493, 20-Nov-2026)

S899's import-check said it: `/root/wa/venv` is **Python 3.9.25**, and `processor.py` (the PC's engine, unchanged bytes f1c02736)
writes its type hints the 3.10 way (`str | None`) — evaluated at definition time on 3.9, refused (`TypeError: unsupported
operand type(s) for |`). `revenue.py` and `revenue_ingest.py` already carry `from __future__ import annotations` and fail only
because they import processor. **The fix is that one line**, as the engine's first statement after its docstring: hints stay
text, nothing is evaluated, and on the PC's Python the line changes no behaviour (the engine never reads its annotations).
Ten hints in processor.py, all annotations; no other 3.10-only construct (no `match`, no runtime unions) — checked by ast.

- `/root/followup_tracker/processor.py` f1c02736 → bade3c1a (the line at 6; `.bak_S900_f1c02736` beside)
- `/root/followup_tracker/replay/processor.py.bak_S777_0e7c129f` (seeded; the pre-10-Nov engine for Replay 2) 0e7c129f → 44adfff8, patched in place by `py39_future.py`
- then `replay2_s897.py --import-check` (must be 0 errors, else both files go back) and Replay 2 `--run`.

**The rule from here:** the box's engine = the PC's bytes + this one line, until the box has a Python ≥ 3.10 venv for the
tracker (then the line goes and the pins return to the PC's). The PC's file is untouched.

Install (server, one line):
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s900kit && cp -rp /root/deploy/repo/deploy_kits/S900_ENGINE_PY39 /tmp/s900kit && bash /tmp/s900kit/install_S900_ENGINE_PY39.sh
```
Undo: `bash /tmp/s900kit/install_S900_ENGINE_PY39.sh --undo`.
