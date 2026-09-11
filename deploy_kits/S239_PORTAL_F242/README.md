# S239_PORTAL_F242 — the login loop ends

**The owner, 11-Sep-2026:** "followup.dr-manoj.in keeps on hanging because of the cookie matter; staff face problems;
Amir could not do his entries that day."

**Cause (F-242 / AF-12, reproduced offline):** every login also planted a 10-year "trusted device" cookie. When the
real sign-in ended — after 30 days, or the moment anyone pressed **"Sign out everywhere"**, which was on every
**staff** home screen too — `/portal` said "sign in" and `/portal/login` said "you are signed in", forever.

**Fix (portal.py 7bc59115 → ed558b36):** the login page shows the form and clears the old cookie; logins stop
planting it; the old cookie alone opens nothing (case pack, WhatsApp — AF-12); new `/portal/logout`; "Forget all
devices" and "Sign out everywhere" are doctor-only, on screen and on the server.

**Proven offline on the live code (old vs new):** old loops (302→302), a staff login could sign everyone out
(epoch bumped), no logout (404); new: login page 200 and clears the cookie, staff buttons gone and refused (403),
logout 302, doctor unchanged.

```
bash /root/deploy/vps_deploy.sh S239_PORTAL_F242
```
