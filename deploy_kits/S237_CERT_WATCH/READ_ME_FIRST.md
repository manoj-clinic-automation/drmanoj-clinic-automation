# S237_CERT_WATCH — the certificate night-watchman

**Built 10-Sep-2026. Answers F-387: nothing in the estate watches a certificate expiry date.**
On 08-Sep the public website served an expired certificate to patients for a full day and the first
signal was Dr Manoj opening the site by chance on his phone.

**This kit is PUBLISHED, NOT INSTALLED. It changes nothing until you run the install line.**

---

## WHAT IT DOES

Once a day it opens each of the clinic's nine sites **the way a patient's browser does**, and looks
at the certificate that actually comes back. If everything is fine it says nothing. If something
needs attention it sends one phone push and one email — once per problem, not once per day — and one
note when it is fixed.

It never renews, installs, restarts or edits anything. It only looks.

**It does not ask acme.sh anything, and reads no file acme.sh writes.** That is deliberate: at S236
acme.sh reported a clean successful renewal every night while the live certificate sat expired.

> **The rule this is built on (F-386): a job that reports success is not evidence.
> Assert the thing the world can see.**

## WHAT IT CATCHES

| verdict | meaning |
|---|---|
| **EXPIRED** | the site is serving an expired certificate right now — the 08-Sep outage |
| **STAGING** | a certificate from Let's Encrypt's *test* authority. Looks issued and valid to acme.sh; **every browser rejects it.** This was the root cause on 08-Sep |
| **MISMATCH** | a valid certificate, but not for this hostname |
| **UNTRUSTED** | a browser refuses the site for some other reason — never reported as OK |
| **URGENT** | 7 days or fewer left |
| **WARN** | 21 days or fewer left. 21 is deliberate: acme.sh renews at 30, so 21 means a renewal **has already failed once** |
| **ERROR** | the site could not be reached at all — said out loud, never a silence |
| **SKIP** | `drmanojagarwal.in` only, which is being retired on purpose |

A site a browser refuses **now** always outranks one expiring **later**.

## HOW IT WAS PROVEN

- `py_compile` clean.
- **70 self-test checks, 0 failures** — offline, no network, nothing sent.
- **A live-shape walk of the watchman: 19 checks, 0 failures.** Seven real certificates — healthy,
  20 days out, 4 days out, expired, expired-and-staging, staging, and wrong-name — served over a real
  TLS socket and read by the shipped code, end to end. (`_proof/walk.py`, output in `WALK_PROOF.md`.)
- **A live-shape walk of THIS INSTALLER: 19 checks, 0 failures** — the green path, the green path over
  an existing file, and both red paths. (`_proof/install_walk.sh`.)

> ⚠ **Both walks earned their place, and each caught something the green gates could not.**
>
> **The watchman.** The first version passed all 50 unit checks and was **wrong about every one of the
> seven live sites**: `ssl.getpeercert()` returns an empty dict on an unverified connection, so the
> whole watch would have reported every site unreachable, for ever.
>
> **The installer.** The first version removed `/root/wa/cert_watch.py` on *any* gate failure —
> including the gates that run **before anything is touched**. A refused install would have **deleted
> a working file it had never written.** The red path now undoes only what that run actually did.

## INSTALL — one line, on the VPS

The kit deploys through the project's own deployer, which pulls the repository, verifies `SUMS.md5`
and `KIT_ID.txt`, and hands off to this kit's installer:

```
bash /root/deploy/vps_deploy.sh S237_CERT_WATCH
```

**That line requires the kit to have been published first** — `PUBLISH_ALL.bat` on the PC.

The installer places the file and the systemd units, proves them, and then **prints the live table
for all nine sites**. It deliberately **does NOT start the daily watch** — so the table is seen
before anything begins running on a schedule.

**That table is the point.** It is the first honest measurement of all nine certificates the estate
has ever had, and it answers §4 of `S236_SSL_EXPIRY_AND_THE_RENEWAL_THAT_LIED`: which of the nine are
missing from the renewal run, and what those six are actually serving.

Then, only if the table looks right, turn the daily watch on:

```
systemctl enable --now clinic-certwatch.timer && systemctl list-timers clinic-certwatch.timer --no-pager
```

## TO LOOK AGAIN LATER, ANY TIME — read-only, sends nothing

```
/root/wa/venv/bin/python3 /root/wa/cert_watch.py --dry-run
```

## TO CHECK ITS OWN HEALTH

```
/root/wa/venv/bin/python3 /root/wa/cert_watch.py --selftest
```

```
tail -20 /root/wa/cert_watch.log
```

## TO REMOVE IT

```
systemctl disable --now clinic-certwatch.timer
```

Nothing else on the server depends on it.

---
*S237_CERT_WATCH · 10-Sep-2026 · standard library only; `cryptography` is used if present and
`openssl` if not, and it works with neither. Nothing live was touched to build this.*
