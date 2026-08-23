#!/usr/bin/env python3
"""S198_P2 gate — the Forms & Downloads surface, served-HTML + behaviour, with
URL preservation against the S198_P1 live baseline.
Run: python3 gate_S198_P2.py <candidate.py> [--baseline <live.py>]"""
import importlib.util
import os
import sys
import tempfile

PASS = FAIL = 0


def check(label, ok):
    global PASS, FAIL
    if ok:
        PASS += 1
    else:
        FAIL += 1
        print("FAIL: " + label)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def as_user(mod, user, role):
    mod._usable = lambda: True
    mod._authed = lambda req: True
    mod._sso_ready = lambda: True
    mod._sso_user = lambda req: {"user": user, "role": role}
    mod._is_clinic_pc = lambda req: False
    # _is_doctor reads the request itself; align it with the stubbed identity
    mod._is_doctor = lambda req: role == "doctor"


def main():
    cand_path = sys.argv[1]
    base_path = sys.argv[sys.argv.index("--baseline") + 1] if "--baseline" in sys.argv else None

    tmp = tempfile.mkdtemp(prefix="forms_gate_")
    os.environ["PORTAL_FORMS_DIR"] = tmp
    cand = load(cand_path, "cand_portal_p2")
    check("FORMS_DIR honours the env override", cand.FORMS_DIR == tmp)

    # seed two forms
    pdf = b"%PDF-1.4 fake-but-bytes"
    open(os.path.join(tmp, "Consent Form (Hindi).pdf"), "wb").write(pdf)
    open(os.path.join(tmp, "Xray Requisition.png"), "wb").write(b"\\x89PNG fake")

    # ---- staff view -----------------------------------------------------------
    as_user(cand, "alisha", "staff")
    with cand.app.test_client() as c:
        h = c.get("/portal/forms").get_data(as_text=True)
        check("staff: both forms listed",
              "Consent Form (Hindi).pdf" in h and "Xray Requisition.png" in h)
        check("staff: Open/Print + Download offered",
              "Open / Print" in h and "Download" in h)
        check("staff: NO upload form, NO remove",
              "/portal/forms/upload" not in h and "/portal/forms/delete" not in h)
        r = c.get("/portal/forms/file/Consent%20Form%20(Hindi).pdf")
        check("staff: file serves inline, exact bytes",
              r.status_code == 200 and r.data == pdf
              and "attachment" not in (r.headers.get("Content-Disposition") or ""))
        r = c.get("/portal/forms/file/Consent%20Form%20(Hindi).pdf?dl=1")
        check("staff: ?dl=1 downloads (attachment)",
              r.status_code == 200
              and "attachment" in (r.headers.get("Content-Disposition") or ""))
        check("staff: traversal name is refused",
              c.get("/portal/forms/file/..%2Fportal.py").status_code == 404
              and c.get("/portal/forms/file/portal.py").status_code == 404)
        check("staff: upload POST is 403",
              c.post("/portal/forms/upload").status_code == 403)
        check("staff: delete POST is 403",
              c.post("/portal/forms/delete",
                     data={"name": "Xray Requisition.png"}).status_code == 403)
        check("staff: home shows the live Forms tile",
              'href="/portal/forms"' in c.get("/portal").get_data(as_text=True))

    # ---- doctor management ----------------------------------------------------
    as_user(cand, "manoj", "doctor")
    with cand.app.test_client() as c:
        h = c.get("/portal/forms").get_data(as_text=True)
        check("doctor: upload + remove visible",
              "/portal/forms/upload" in h and "/portal/forms/delete" in h)
        import io
        r = c.post("/portal/forms/upload", data={
            "f": (io.BytesIO(b"NEWPDFBYTES"), "OPD Slip.pdf")},
            content_type="multipart/form-data", follow_redirects=False)
        ok_up = r.status_code == 302 and os.path.isfile(os.path.join(tmp, "OPD Slip.pdf"))
        check("doctor: good upload lands, byte-exact",
              ok_up and open(os.path.join(tmp, "OPD Slip.pdf"), "rb").read() == b"NEWPDFBYTES")
        r = c.post("/portal/forms/upload", data={
            "f": (io.BytesIO(b"EVIL"), "shell.php")},
            content_type="multipart/form-data")
        check("doctor: disallowed extension refused, nothing written",
              not os.path.exists(os.path.join(tmp, "shell.php")))
        r = c.post("/portal/forms/upload", data={
            "f": (io.BytesIO(b"OTHER"), "OPD Slip.pdf")},
            content_type="multipart/form-data")
        check("doctor: duplicate name refused, original untouched",
              open(os.path.join(tmp, "OPD Slip.pdf"), "rb").read() == b"NEWPDFBYTES")
        c.post("/portal/forms/delete", data={"name": "OPD Slip.pdf"})
        check("doctor: remove works",
              not os.path.exists(os.path.join(tmp, "OPD Slip.pdf")))
        check("doctor: remove of a traversal name is a no-op",
              c.post("/portal/forms/delete",
                     data={"name": "../portal.py"}).status_code == 302
              and os.path.exists(cand_path))

    # ---- anonymous ------------------------------------------------------------
    cand._authed = lambda req: False
    with cand.app.test_client() as c:
        r = c.get("/portal/forms")
        check("no login -> redirected to login",
              r.status_code == 302 and "/portal/login" in r.headers.get("Location", ""))
        r = c.get("/portal/forms/file/Consent%20Form%20(Hindi).pdf")
        check("no login -> file refused too", r.status_code == 302)

    # ---- URL preservation vs the live baseline --------------------------------
    if base_path:
        base = load(base_path, "base_portal_p2")
        burl = {t["name"]: t["url"] for t in base.TILES}
        curl = {t["name"]: t["url"] for t in cand.TILES}
        changed = {n for n in burl if curl.get(n) != burl[n]}
        check("only the Forms tile changed vs live baseline",
              changed == {"Forms & Downloads"} and set(curl) == set(burl))
        cf = next(t for t in cand.TILES if t["name"] == "Forms & Downloads")
        check("Forms tile: live, /portal/forms, all three roles",
              cf["live"] and cf["url"] == "/portal/forms"
              and set(cf["roles"]) == {"doctor", "manager", "staff"})

    print("GATE %d/%d %s" % (PASS, PASS + FAIL, "GREEN" if FAIL == 0 else "RED"))
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
