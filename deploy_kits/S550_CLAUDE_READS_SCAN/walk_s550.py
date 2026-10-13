#!/usr/bin/env python3
"""walk_s550.py -- the S550_CLAUDE_READS_SCAN walk. The app with the built files on a COPY of a database (the live one on the
box, copied under the session's home and removed after; or --fresh), made-up rows dated 2031, made-up names, no person.
The call to Claude is never made: the HTTPS step is replaced by made-up answers (success, a model not found, the key refused,
the credit run out, busy), and Sarvam by a stand-in, so the walk spends nothing and sends nothing.

    python3 walk_s550.py <dir with asset_register.py, clinic_papers.py, claude_reader.py, claude_reread.py> <assets.db | --fresh> [--expect-red]

GREEN/RED per check; exit 1 on any RED (--expect-red: exit 0 only if some check is RED -- the control on the live files)."""
import importlib.util, json, os, re, shutil, sqlite3, sys, tempfile, time
_REAL_SLEEP = time.sleep                                                         # the reader's back-off is cut short below; the walk's own waits are real

D = os.path.abspath(sys.argv[1])
SRC = sys.argv[2]
EXPECT_RED = "--expect-red" in sys.argv
R = []
FAKE_KEY = "sk-ant-walk-made-up-" + "0" * 12


def check(name, ok, detail=""):
    R.append(bool(ok)); print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(detail)[:220]) if (detail and not ok) else ""))


def tiny_pdf(tag):
    body = ("%PDF-1.1\n%% " + tag + "\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            "3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 300]>>endobj\ntrailer<</Size 4/Root 1 0 R>>\n%%EOF\n")
    return body.encode()


READING = {"doc_kind": "estimate", "vendor": "Made-Up Cast Supplies 2031", "bill_no": "E-31", "bill_date": "2025-01-05",
           "total_amount": "1,250", "made_out_to": "clinic", "handwritten": True,
           "addressed_to": "Made-Up Person Name 2031", "notes": "Made-Up Person Name 2031 named on it",
           "items": [{"name": "Fibre cast 4 in", "qty": 10, "unit": "roll", "rate": 100, "amount": 1000},
                     {"name": "Roller bandage", "qty": 25, "unit": None, "rate": 10, "amount": 250, "serial": "SN-2031-7", "model": "M-31"}]}


def ok_answer(reading=None):
    t = json.dumps(reading or READING)
    return 200, {"content": [{"type": "text", "text": "```json\n" + t + "\n```"}]}, t


class Mock:
    """Stands in for claude_reader._post: a queue of answers; records each call (the model asked, the key's presence)."""
    def __init__(self, cr):
        self.cr, self.q, self.calls = cr, [], []
        cr._post = self.post
    def post(self, body, key):
        self.calls.append((body.get("model"), key == FAKE_KEY, [c.get("type") for c in body["messages"][0]["content"]]))
        if not self.q:
            return ok_answer()
        a = self.q.pop(0)
        return a() if callable(a) else a
    def set(self, *answers):
        self.q = list(answers); self.calls = []


class SarvamStub:
    def __init__(self):
        self.on, self.calls = True, 0
    def available(self):
        return self.on
    def extract(self, path, schema=None):
        self.calls += 1
        return {"vendor": "Made-Up Sarvam Vendor 2031", "bill_no": "S-9-%d" % self.calls, "total_amount": "77", "items": []}, "done"


def main():
    wd = tempfile.mkdtemp(prefix="s550_walk_", dir=os.path.expanduser("~"))
    try:
        for f in ("asset_register.py", "clinic_papers.py", "claude_reader.py", "claude_reread.py", "scanner_widget.js"):
            if os.path.exists(os.path.join(D, f)):
                shutil.copy(os.path.join(D, f), wd)
        dbc = os.path.join(wd, "assets.db")
        if SRC != "--fresh":
            src = sqlite3.connect("file:%s?mode=ro" % os.path.abspath(SRC), uri=True); dst = sqlite3.connect(dbc); src.backup(dst); src.close(); dst.close()
        up = os.path.join(wd, "uploads"); os.makedirs(up)
        keyf = os.path.join(wd, "key", "anthropic.key"); os.makedirs(os.path.dirname(keyf))
        with open(keyf, "w") as fh:
            fh.write(FAKE_KEY + "\n")
        os.environ.update({"ASSETS_DB": dbc, "ASSETS_UPLOADS": up, "SCANAPP_ANTHROPIC_KEY_FILE": keyf,
                           "SCANAPP_ANTHROPIC_URL": "https://made-up.invalid/v1/messages"})
        for k in ("SARVAM_API_KEY", "ANTHROPIC_API_KEY"):
            os.environ.pop(k, None)
        sys.path.insert(0, wd)
        spec = importlib.util.spec_from_file_location("asset_register", os.path.join(wd, "asset_register.py"))
        try:
            m = importlib.util.module_from_spec(spec); sys.modules["asset_register"] = m; spec.loader.exec_module(m)
        except Exception as e:                                                    # noqa: BLE001
            check("W1 the app imports with the built files", False, repr(e)); return
        CR = getattr(m, "CLAUDE", None)
        check("W1 the app imports and carries the Claude reader S550.2", CR is not None and getattr(CR, "VERSION", "") == "S550.2",
              getattr(CR, "VERSION", None))
        if CR is None:                                                            # the control: go on with the module alone,
            try:                                                                  # so the app's own checks show what is missing
                import claude_reader as CR
            except Exception:                                                     # noqa: BLE001
                return
        CR.time = type("T", (), {"sleep": staticmethod(lambda s: None), "time": staticmethod(time.time)})                                            # the walk does not wait out the back-off
        mk = Mock(CR)
        stub = SarvamStub(); m.SARVAM = stub

        db = sqlite3.connect(dbc); db.row_factory = sqlite3.Row
        CR.ensure(db)
        for k in ("read.claude", "read.claude_model", "read.claude_daily_cap", "read.reread_progress"):
            db.execute("DELETE FROM settings WHERE key=?", (k,))
        db.commit()

        # ---------------------------------------------------------------- the reader itself
        p = os.path.join(up, "walk_2031_a.pdf"); open(p, "wb").write(tiny_pdf("a"))
        mk.set(ok_answer())
        r = CR.read(p, bid=None, db_path=dbc)
        check("C1 a good answer is read; the paper goes as a PDF document; the key is sent in the header only",
              r and r.get("vendor") == READING["vendor"] and mk.calls and mk.calls[0][1] and mk.calls[0][2][0] == "document", mk.calls)
        check("C2 the first model that answers is kept", CR.setting(db, "read.claude_model") == CR.MODELS[0], CR.setting(db, "read.claude_model"))
        db.execute("DELETE FROM settings WHERE key='read.claude_model'"); db.commit()
        mk.set((404, {"error": {"type": "not_found_error", "message": "model: %s" % CR.MODELS[0]}}, ""), ok_answer())
        r = CR.read(p, bid=None, db_path=dbc)
        check("C3 a model not found -> the next model is asked and kept", r is not None and [c[0] for c in mk.calls] == list(CR.MODELS[:2])
              and CR.setting(db, "read.claude_model") == CR.MODELS[1], (mk.calls, CR.setting(db, "read.claude_model")))
        mk.set((429, None, "busy"), (529, None, "overloaded"), ok_answer())
        r = CR.read(p, bid=None, db_path=dbc)
        check("C4 busy twice, then read (three tries)", r is not None and len(mk.calls) == 3, mk.calls)
        hdr, items = CR.to_bill(dict(READING, bill_date="1952-03-04", total_amount="1,250"))
        check("C5 an impossible date (1952) is dropped; the amount 1,250 reads 1250; units go to the pack",
              hdr["bill_date"] is None and hdr["total_amount"] == 1250.0 and items[0]["pack"] == "roll" and items[0]["qty"] == 10, (hdr, items[0]))
        hdr, _ = CR.to_bill(dict(READING, bill_date="05/01/2031"))
        check("C6 a date not given as YYYY-MM-DD is not guessed", hdr["bill_date"] is None, hdr)
        check("C7 the instruction forbids copying a patient's name and forbids guessing",
              "NEVER write any person" in CR.PROMPT and "never guess" in CR.PROMPT)
        n0 = CR.calls_today(db)
        db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude_daily_cap',?)", (str(n0),)); db.commit()
        mk.set(ok_answer())
        r = CR.read(p, bid=None, db_path=dbc)
        check("C8 the day's limit (counted per CALL, retries included) reached -> no call, nothing read",
              r is None and not mk.calls and n0 >= 6, (mk.calls, n0))
        db.execute("DELETE FROM settings WHERE key='read.claude_daily_cap'"); db.commit()
        db.execute("DELETE FROM settings WHERE key='read.claude_model'"); db.commit()
        mk.set((529, None, ""), (529, None, ""), (529, None, ""), ok_answer())
        r = CR.read(p, bid=None, db_path=dbc)
        check("C8b the first model busy three times -> the second answers, but the first stays the model (no lasting downgrade)",
              r is not None and [c[0] for c in mk.calls] == [CR.MODELS[0]] * 3 + [CR.MODELS[1]] and not CR.setting(db, "read.claude_model"), mk.calls)
        r = CR.clean({"vendor": 123, "bill_no": 77, "items": [{"name": 5, "qty": "x"}, "junk", {"name": None}], "made_out_to": "Some Name"})
        check("C8c numbers where words were expected (and junk) do not break the reading", r and r["vendor"] == "123"
              and r["items"] == [dict(r["items"][0], name="5")] and r["made_out_to"] is None, r)
        mk.set((400, {"error": {"type": "invalid_request_error", "message": "Your credit balance is too low to access the API."}}, ""))
        r = CR.read(p, bid=None, db_path=dbc)
        check("C9 the credit run out -> Claude stops itself (Sarvam carries on)", r is None and CR.state(db).startswith("stopped"), CR.state(db))
        mk.set(ok_answer())
        r = CR.read(p, bid=None, db_path=dbc)
        check("C10 once stopped, nothing more is sent", r is None and not mk.calls, mk.calls)
        db.execute("UPDATE settings SET value='on' WHERE key='read.claude'"); db.commit()
        mk.set((401, {"error": {"type": "authentication_error", "message": "invalid x-api-key"}}, ""))
        r = CR.read(p, bid=None, db_path=dbc)
        check("C11 the key refused -> stopped", r is None and CR.state(db) == "stopped:the key was refused", CR.state(db))
        db.execute("UPDATE settings SET value='on' WHERE key='read.claude'"); db.commit()
        jp = os.path.join(up, "walk_2031_b.jpg"); open(jp, "wb").write(b"\xff\xd8\xff\xe0" + b"0" * 64)
        mk.set(ok_answer())
        CR.read(jp, bid=None, db_path=dbc)
        check("C12 a photo goes as an image", mk.calls and mk.calls[0][2][0] == "image", mk.calls)

        # ---------------------------------------------------------------- the app's background reading
        def mkbill(stamp, lane="clinic", vendor=None, status="draft", stored=None):
            cur = db.execute("INSERT INTO bills(kind, vendor, stamp_no, status, lane, submitted_by, source_stored) VALUES(?,?,?,?,?,?,?)",
                             ("Consumable", vendor, stamp, status, lane, "Walk", stored))
            db.commit(); return cur.lastrowid
        made = []
        def scan(tag):
            fn = "walk_2031_%s.pdf" % tag; open(os.path.join(up, fn), "wb").write(tiny_pdf(tag)); return fn
        b1 = mkbill("Z-2031-C1", stored=scan("c1")); made.append(b1)
        stub.calls = 0; mk.set(ok_answer())
        st = m._bg_extract(b1, os.path.join(up, "walk_2031_c1.pdf"))
        row = db.execute("SELECT vendor, bill_no, bill_date, total_amount, ocr_status FROM bills WHERE id=?", (b1,)).fetchone()
        nit = db.execute("SELECT COUNT(*) FROM bill_items WHERE bill_id=?", (b1,)).fetchone()[0]
        check("A1 a new clinic scan: Claude fills supplier, number, date, amount and the two items; Sarvam is not asked",
              st == "read" and row["vendor"] == READING["vendor"] and row["bill_no"] == "E-31" and row["bill_date"] == "2025-01-05"
              and row["total_amount"] == 1250 and nit == 2 and stub.calls == 0, (st, dict(row), nit, stub.calls))
        cr = db.execute("SELECT ok, doc_kind, data FROM claude_reading WHERE bill_id=?", (b1,)).fetchone()
        check("A2 the reading is kept beside the paper (kind: estimate)", cr and cr["ok"] == 1 and cr["doc_kind"] == "estimate")
        check("A2b no person's name is kept: not the made-out-to name, not a note; only the kind", cr and "Made-Up Person" not in (cr["data"] or "")
              and json.loads(cr["data"]).get("made_out_to") == "clinic" and "notes" not in json.loads(cr["data"]), cr and cr["data"])
        sn = db.execute("SELECT serial_no, model FROM bill_items WHERE bill_id=? AND serial_no IS NOT NULL", (b1,)).fetchone()
        check("A2c a serial number and model read off the paper reach the item (the asset register keeps getting them)",
              sn and sn[0] == "SN-2031-7" and sn[1] == "M-31", sn and tuple(sn))
        mk.set((400, {"error": {"type": "invalid_request_error", "message": "Could not process the document"}}, ""))
        CR.read(os.path.join(up, "walk_2031_c1.pdf"), bid=b1, db_path=dbc)
        cr2 = db.execute("SELECT ok, data FROM claude_reading WHERE bill_id=?", (b1,)).fetchone()
        check("A2d a later failure never replaces a good reading; a refused paper is not sent to the next model",
              cr2["ok"] == 1 and cr2["data"] == cr["data"] and len(mk.calls) == 1, (cr2["ok"], len(mk.calls)))
        b2 = mkbill("Z-2031-C2", vendor="Typed By Shavez 2031", stored=scan("c2")); made.append(b2)
        mk.set(ok_answer())
        m._bg_extract(b2, os.path.join(up, "walk_2031_c2.pdf"))
        check("A3 what a person typed is never overwritten", db.execute("SELECT vendor FROM bills WHERE id=?", (b2,)).fetchone()[0] == "Typed By Shavez 2031")
        b3 = mkbill("Z-2031-C3", stored=scan("c3")); made.append(b3)
        stub.calls = 0; mk.set((500, None, "x"), (500, None, "x"), (500, None, "x"), (500, None, "x"), (500, None, "x"), (500, None, "x"))
        m._bg_extract(b3, os.path.join(up, "walk_2031_c3.pdf"))
        check("A4 Claude cannot read -> Sarvam reads, exactly as before", stub.calls == 1 and
              db.execute("SELECT vendor FROM bills WHERE id=?", (b3,)).fetchone()[0] == "Made-Up Sarvam Vendor 2031")
        b4 = mkbill("Z-2031-P1", lane=None, stored=scan("p1")); made.append(b4)
        db.execute("UPDATE bills SET kind='Pharmacy' WHERE id=?", (b4,)); db.commit()       # an old row: no lane, its kind says pharmacy
        stub.calls = 0; mk.set(ok_answer())
        m._bg_extract(b4, os.path.join(up, "walk_2031_p1.pdf"))
        for _ in range(100):                                                      # Claude reads beside Sarvam: wait for it (10 s at most)
            if db.execute("SELECT 1 FROM claude_reading WHERE bill_id=?", (b4,)).fetchone():
                break
            _REAL_SLEEP(0.1)
        check("A5 a pharmacy paper (lane from its kind): Claude reads beside Sarvam and the reading is kept; Sarvam fills it",
              stub.calls == 1 and db.execute("SELECT vendor FROM bills WHERE id=?", (b4,)).fetchone()[0] == "Made-Up Sarvam Vendor 2031"
              and db.execute("SELECT ok FROM claude_reading WHERE bill_id=?", (b4,)).fetchone()[0] == 1)
        for tag, lane, sg in (("o1", "other_doc", None), ("o2", "clinic", "personal"), ("o3", "clinic", "resume")):
            bx = mkbill("Z-2031-" + tag.upper(), lane=lane, stored=scan(tag)); made.append(bx)
            if sg:
                db.execute("UPDATE bills SET subgroup=? WHERE id=?", (sg, bx)); db.commit()
            stub.calls = 0; mk.set(ok_answer())
            m._bg_extract(bx, os.path.join(up, "walk_2031_%s.pdf" % tag))
            check("A5%s %s: never sent to Claude; Sarvam as before" % (tag, sg or lane), not mk.calls and stub.calls == 1)
        db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')"); db.commit()
        b5 = mkbill("Z-2031-C5", stored=scan("c5")); made.append(b5)
        stub.calls = 0; mk.set(ok_answer())
        m._bg_extract(b5, os.path.join(up, "walk_2031_c5.pdf"))
        check("A6 the owner's switch OFF -> nothing sent to Claude, Sarvam reads", stub.calls == 1 and not mk.calls)
        stub.on = False
        check("A7 Sarvam absent and Claude OFF -> no reader (the intake starts nothing, as before)", m._reader_on() is False)
        db.execute("UPDATE settings SET value='on' WHERE key='read.claude'"); db.commit()
        check("A8 Sarvam absent and Claude ON -> a reader (the intake and the re-read start Claude)", m._reader_on() is True)
        stub.on = True

        # ---------------------------------------------------------------- the owner's card
        ep = db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone()
        if not db.execute("SELECT 1 FROM users WHERE role='owner' AND active=1").fetchone():
            db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES('walk_owner_2031','Walk Owner','owner','x',1)"); db.commit()
        own = m.app.test_client()
        u = db.execute("SELECT id FROM users WHERE role='owner' AND active=1 ORDER BY id LIMIT 1").fetchone()
        with own.session_transaction() as s:
            s["uid"] = u[0]; s["epoch"] = ep[0] if ep else None
        t = own.get("/admin").get_data(as_text=True)
        check("P1 /admin shows the Claude card, ON, with today's count and a Switch OFF", "Reading the scans" in t and "Now: <b>ON</b>" in t
              and "read today" in t and "set_read_claude" in t, re.findall(r"Now: <b>[^<]*</b>", t))
        check("P2 the page never carries the key", FAKE_KEY not in t and "sk-ant-" not in t)
        own.post("/admin", data={"action": "set_read_claude", "on": "0"})
        check("P3 Switch OFF is kept", CR.setting(db, "read.claude") == "off")
        t = own.get("/admin").get_data(as_text=True)
        check("P4 the card then reads OFF with Switch ON", "Now: <b>OFF</b>" in t and "Switch ON" in t)
        own.post("/admin", data={"action": "set_read_claude", "on": "1"})
        os.rename(keyf, keyf + ".away")
        t = own.get("/admin").get_data(as_text=True)
        check("P5 no key on the server -> the card says so and offers no switch", "no key on the server yet" in t
              and "set_read_claude" not in t.split("Reading the scans")[1].split("</div>")[0])
        os.rename(keyf + ".away", keyf)
        os.environ["ANTHROPIC_API_KEY"] = "sk-ant-some-other-key"
        check("P5b the stored key file is used even when the environment carries another key", CR._key() == FAKE_KEY)
        os.environ.pop("ANTHROPIC_API_KEY", None)
        sv = [r[0] for r in db.execute("SELECT value FROM settings").fetchall()] + \
             [r[0] or "" for r in db.execute("SELECT data FROM claude_reading").fetchall()] + \
             [r[0] or "" for r in db.execute("SELECT error FROM claude_reading").fetchall()]
        check("P6 the key is stored nowhere in the database", not any(FAKE_KEY in str(v) for v in sv))

        # ---------------------------------------------------------------- the re-read of the older scans
        import claude_reread as RR
        c1 = mkbill("Z-2031-R1", stored=scan("r1")); c2 = mkbill("Z-2031-R2", vendor="Typed 2031", stored=scan("r2"))
        c3 = mkbill("Z-2031-R3", lane="pharmacy", stored=scan("r3")); c4 = mkbill("Z-2031-R4", status="rejected", stored=scan("r4"))
        c5 = mkbill("Z-2031-R5", stored=scan("r5")); c8 = mkbill("Z-2031-R8", status="approved", stored=scan("r8"))
        made += [c1, c2, c3, c4, c5, c8]
        db.execute("UPDATE bills SET lane=NULL, kind='Pharmacy' WHERE id=?", (c3,)); db.commit()
        CR._record(db, c5, "x", True, "bill", {"vendor": "already"}, None)
        db.execute("UPDATE bills SET bill_date='2031-02-02' WHERE id=?", (c1,)); db.commit()
        mk.set()
        RR.main(["--db", dbc, "--uploads", up, "--gap", "0", "--ids", ",".join(str(x) for x in (c1, c2, c3, c4, c5, c8))])
        g = lambda bid, col: db.execute("SELECT %s FROM bills WHERE id=?" % col, (bid,)).fetchone()[0]
        check("R1 an older paper: the empty supplier, number and amount filled, and its items", g(c1, "vendor") == READING["vendor"]
              and g(c1, "total_amount") == 1250 and db.execute("SELECT COUNT(*) FROM bill_items WHERE bill_id=?", (c1,)).fetchone()[0] == 2)
        check("R2 its date is never touched", g(c1, "bill_date") == "2031-02-02")
        check("R3 what a person typed stays", g(c2, "vendor") == "Typed 2031")
        check("R4 a pharmacy paper: the reading kept, nothing written", g(c3, "vendor") is None
              and db.execute("SELECT ok FROM claude_reading WHERE bill_id=?", (c3,)).fetchone()[0] == 1)
        check("R5 a rejected paper and one already read are not sent again", len(mk.calls) == 4, len(mk.calls))
        check("R5b an approved paper: the reading kept, nothing written on it", g(c8, "vendor") is None
              and db.execute("SELECT ok FROM claude_reading WHERE bill_id=?", (c8,)).fetchone()[0] == 1)
        pr = CR.setting(db, "read.reread_progress", "")
        check("R6 the progress line is kept for the owner's card", pr.startswith("finished") and "4 of 4 read" in pr, pr)
        c6 = mkbill("Z-2031-R6", stored=scan("r6")); c7 = mkbill("Z-2031-R7", stored=scan("r7")); made += [c6, c7]
        mk.set((401, {"error": {"message": "invalid x-api-key"}}, ""))
        RR.main(["--db", dbc, "--uploads", up, "--gap", "0", "--ids", "%d,%d" % (c6, c7)])
        check("R7 the key refused mid-way -> the re-read stops at once", len(mk.calls) == 1 and "stopped" in CR.setting(db, "read.reread_progress", ""),
              (len(mk.calls), CR.setting(db, "read.reread_progress", "")))

        for bid in made:
            db.execute("DELETE FROM bill_items WHERE bill_id=?", (bid,)); db.execute("DELETE FROM claude_reading WHERE bill_id=?", (bid,))
            db.execute("DELETE FROM bills WHERE id=?", (bid,))
        db.commit()
        check("Z1 the made-up rows are gone from the copy", db.execute("SELECT COUNT(*) FROM bills WHERE stamp_no LIKE 'Z-2031-%'").fetchone()[0] == 0)
        db.close()
    finally:
        shutil.rmtree(wd, ignore_errors=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:                                                        # noqa: BLE001
        check("the walk ran to its end", False, repr(e))
    reds = R.count(False)
    print("%d checks: %d GREEN, %d RED" % (len(R), R.count(True), reds))
    if EXPECT_RED:
        sys.exit(0 if reds else 1)
    sys.exit(1 if reds or not R else 0)
