"""fixtures_s360.py -- the FAKE Yes Bank statement used by selftest_s360 and walk_s360.
No real account number, reference or figure is in this file."""
import zlib

# ---- B: a laid-out statement, FAKE figures ----------------------------------
HDR = (" Transaction\n"
       "                  Value Date             Cheque No/Reference No                "
       "                    Description                            Withdrawals              Deposits           Running Balance\n"
       "    Date\n\n")
hl = HDR.splitlines()[1]
C = {"wd": hl.find("Withdrawals") + len("Withdrawals"), "dep": hl.find("Deposits") + len("Deposits"),
     "bal": hl.find("Running Balance") + len("Running Balance")}

def row(d, ref, desc, wd, dep, bal, cont=None):
    s = " %s      %s       %s            %s" % (d, d, ref, desc)
    for key, v in (("wd", wd), ("dep", dep), ("bal", bal)):
        if v:
            s = s.ljust(C[key] - len(v)) + v
    return s + "\n" + ((" " * 77 + cont + "\n") if cont else "")

def statement(rows, opening="50,000.00", tw="12,000.00", td="30,000.00", closing="68,000.00",
              period="Period: 01 Aug 2026 - 20 Sep 2026"):
    top = ("   Statement of account: 5550011\n   " + period + "\n\n SOME SHOP\n\n"
           "        Transaction details for your account number 5550011 (CURRENT)\n\n")
    foot = ("\n\n\nOpening Balance: %s        Total Withdrawals: %s        Total Deposits: %s"
            "        Closing Balance: %s\n\nsome footer text 1,234.00 that is not a row\n"
            % (opening, tw, td, closing))
    return top + HDR + "".join(rows) + foot

GOOD = [
    row("15 Sep 2026", "REF0000000A", "NET TXN/SOMETHING/TAX", "12,000.00", "", "68,000.00", "INET/advance tax"),
    row("10 Sep 2026", "REF0000000B", "CASH DEP-SELF-SOME SHOP-", "", "20,000.00", "80,000.00", "BAREILLY"),
    row("02 Aug 2026", "REF0000000C", "CASH DEP-SELF-SOME SHOP-BAREILLY", "", "10,000.00", "60,000.00"),
]

def make_pdf(text):
    lines = text.splitlines()
    ops = ["BT", "/F1 5 Tf", "6 TL", "10 %d Td" % (20 + 6 * len(lines))]
    for ln in lines:
        esc = ln.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        ops.append("(%s) Tj T*" % esc)
    ops.append("ET")
    stream = zlib.compress("\n".join(ops).encode("latin-1"))
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 842 %d] /Contents 4 0 R "
            b"/Resources << /Font << /F1 5 0 R >> >> >>" % (40 + 6 * len(lines)),
            b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(stream) + stream + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>"]
    out, offs = bytearray(b"%PDF-1.4\n"), []
    for i, o in enumerate(objs, 1):
        offs.append(len(out)); out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    x = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for o in offs: out += b"%010d 00000 n \n" % o
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, x)
    return bytes(out)

