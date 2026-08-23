# S196_ATT2 — PWA install kit (delivery note)

Makes the staff "My Biometric" page installable as a phone app. One file
changes: `staff_register.py` v0.3 → v0.4 (`c2059ea1…` → `9087954c…`).

- `/register/manifest.webmanifest` + two app icons built from the REAL clinic
  logo (the exact artwork already on the Sanjeevni Hub, extracted from the
  S187_H1c bytes — Canva's download host is not reachable from the build
  sandbox; the Hub copy is pixel-identical).
- Manifest + icons are public on purpose: the browser's install machinery
  fetches them outside the login session; they contain a name and a picture,
  nothing else.
- Head links are injected on `/register/me` ONLY — maker/checker pages are
  byte-wise re-rendered exactly as before.
- **NO service worker.** Nothing is cached offline; every view is live; the
  mark-me-present request still requires the network (server time = punch).
- No schema change, no data change, service restart only.

Install (after PUBLISH_ALL):
```
cd /root/deploy/repo && git pull && bash deploy_kits/S196_ATT2/INSTALL_S196_ATT2.sh
```

Staff instruction (once per phone): open
`attendance.dr-manoj.in/register/me` in Chrome → sign in → menu →
**Add to Home screen** → the clinic-logo icon opens full-screen like an app.
