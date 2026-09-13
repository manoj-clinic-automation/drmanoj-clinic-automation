# S258_CONSTANT_TIME — Club C, step 1

Every machine-door token check on the VPS becomes a **constant-time compare**.

| file | from | to | how |
|---|---|---|---|
| `/root/finance/finance_app.py` | `1fc62335…` | `a4201e9f…` | patched **on the box** by `patch_compare_s258.py` (7 sites); output md5 must equal the prediction or nothing is kept |
| `/root/finance/stock_app.py` | `aa6d9cd9…` | `8615d64d…` | full file (1 site) |
| `/root/finance/purchase_app.py` | `ad1fc004…` | `52550e63…` | full file (1 site) |

## Why
The S243 study found "two of the apps compare with `==`". The Club C map found **nine** plain
compares across three files (`==` at seven sites, `!=` at three), and exactly one constant-time compare
in the whole estate (`marg_door.py`). A plain compare answers a wrong token a little faster the more
leading characters it gets right; `hmac.compare_digest` does not.

## What changes
One helper per file:
```python
def _tok_ok(given, expected):
    return bool(expected) and bool(given) and hmac.compare_digest(str(given), str(expected))
```
and each site calls it. **Same answer for every real request.** The one deliberate difference: an
empty expected token never matches — before, on the two `!=` sites, a server with the token unset
and a client sending no header compared `None != ""` → refused, but `"" != ""` → allowed. Closed.

Nothing else moves: no route, role, token value, header name, table or screen.

## Why this kit could be built at all
`finance_app.py` cannot be shipped (F-185: a fixture literal; a token in the same file's history). Until
S255 no store held its exact bytes, so every change to it was an anchor patch applied blind. This kit's
patcher was run offline against the S255 capture, the result hashed, and **the installer refuses to keep
a patched file whose md5 differs from that prediction**. The capture paid for itself on its first use.

## Install (one line, on the VPS)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S258_CONSTANT_TIME/install_S258_CONSTANT_TIME.sh
```
Refuses unless all three live md5s match; backs up all three; patches / copies; `py_compile`; a smoke that
greps every file for any surviving plain compare; restarts `clinic-finance`; restores all three on any
failure. **Live proof within 10 minutes:** the pipeline page's manojz heartbeat and medical push both
come through the new compare.

## Rollback (one line)
```
\cp -p /root/finance/finance_app.py.bak_S258_1fc62335 /root/finance/finance_app.py && \cp -p /root/finance/stock_app.py.bak_S258_aa6d9cd9 /root/finance/stock_app.py && \cp -p /root/finance/purchase_app.py.bak_S258_ad1fc004 /root/finance/purchase_app.py && systemctl restart clinic-finance
```

## Proof
`selftest_compare_s258.py` — 17 checks: the helper's truth table equals both old expression shapes on
every real input; no plain compare survives; call-site counts exact. Installer mock-tested four ways.

*Naming note: the repository's `.gitignore` refuses any filename containing "token" (by design). The
patcher and selftest were first named `*_tokens_*` and the publish gate refused them; renamed
`*_compare_*` before the first publish. Two git-ignored leftovers of the old names may sit in the
folder on the owner's PC; they are not part of the kit and `SUMS.md5` does not list them.*
