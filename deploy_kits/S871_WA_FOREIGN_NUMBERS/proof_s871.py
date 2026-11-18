#!/usr/bin/env python3
"""proof_s871.py -- kit S871: what the once-only move WOULD do on the live store, done on a COPY (read only).

Usage: python proof_s871.py NEW_INBOX_PY LIVE_INBOX_DB RAW_DIR SCRATCH
Copies the live inbox.db into SCRATCH, runs the new file's s871_rekey on the copy with the live raw pushes (read only),
prints counts only -- never a number, never a name. Last line: 'PROOF chats moved N; chats abroad after M'.
"""
import importlib.util
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != HERE]
NEW, LIVE, RAW, SCR = sys.argv[1:5]
store = os.path.join(SCR, "proof_store")
os.makedirs(store, exist_ok=True)
os.environ.update({"INBOX_STORE": store, "INBOX_RAW_DIR": RAW})
src = sqlite3.connect("file:%s?mode=ro" % LIVE, uri=True, timeout=20)
dst = sqlite3.connect(os.path.join(store, "inbox.db"))
src.backup(dst)
src.close()
dst.close()
spec = importlib.util.spec_from_file_location("portal_inbox_p871", NEW)
pi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pi)
before = pi.abroad_count()
names = sorted(n for n in os.listdir(RAW) if n.endswith(".jsonl") and len(n) == 16)
import time
t0 = time.time()
plan = pi.s871_plan(names)                                   # outside any lock, as ingest does it
t1 = time.time()
c = pi.db()
c.execute("BEGIN IMMEDIATE")
moved = pi.s871_apply(c, plan)
c.execute("COMMIT")
c.close()
t2 = time.time()
print("raw files read: %d in %.1f s (no lock held); the move itself %.2f s under the lock; chats abroad before: %d"
      % (len(names), t1 - t0, t2 - t1, before))
print("PROOF chats moved %d; chats abroad after %d" % (len(moved), pi.abroad_count()))
