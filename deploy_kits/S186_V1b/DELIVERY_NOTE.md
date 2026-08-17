# Kit S186_V1b — the regenerated pin list

**Session 186 close · one file · no code changes · read-only against everything live**

`/root/deploy/live_pins.txt`, regenerated from **KB Register v5.11** with **full manifest
verification**. The header now reads:

```
# source: KB_Register_v5_11_S186.md
# source_md5: d0da61a095435b1a3ef559c210788c37
# manifest: CANONICAL_MANIFEST.md
# register_pin_verified: yes
```

`yes` rather than `pending` — the F-110 gate passing for the first time. `verify_live_pins.py` should
now read **GREEN** instead of AMBER.

**What it holds the box to that the old list did not:**

```
finance_app.py                       c66bec2b9e  ->  d04167a848
finance_ingest.py                    2cd0f264fb  ->  1f730bcdf3
finance_yesbank.py                   (new)           5dcbdd3a41
finance_ui/finance_workbench.html    (new)           45cb85b353
+ three BLIND migration markers: S186_cash_close, S186_reserve_yesbank, S186_walkin
```

**Two of my own edits were caught by this generator while building the close**, both by the guards
added this morning: a duplicated `finance_workbench.html` row, and a `finance_ingest.py` pinned twice
because the S180 row had not been marked `*(superseded)*`. Either would have produced a red that could
never go green. The older rows are now retained as rollback references and dropped from the list
loudly, not silently.

## Install

```
bash /root/deploy/vps_deploy.sh S186_V1b
```
