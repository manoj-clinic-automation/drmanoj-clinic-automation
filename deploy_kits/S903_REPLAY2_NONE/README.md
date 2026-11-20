# S903_REPLAY2_NONE -- Replay 2 S897.5 (the parent, S493, 20-Nov-2026)

S902 (18:41 IST): the set comparison of a sheet raised on empty cells beside text (`<` between NoneType and str) -- every run FAIL on that, not on the engine. `replay2_s897.py` 5c8afcfc -> S897.5 orders rows by a text key. Then Replay 2 runs again: pass / order-only (the same rows in another order) / fail.

Install (server, one line):
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s903kit && cp -rp /root/deploy/repo/deploy_kits/S903_REPLAY2_NONE /tmp/s903kit && bash /tmp/s903kit/install_S903_REPLAY2_NONE.sh
```
Undo: `bash /tmp/s903kit/install_S903_REPLAY2_NONE.sh --undo`.
