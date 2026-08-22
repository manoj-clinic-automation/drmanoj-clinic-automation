"""Does every consumer of a correction row read only keys the producer builds?

Bug 1 in S195_SHARE: the Excel export read r["diff_p"], which _correction_rows
never put there. It passed an offline test because the test's fixture invented
the key. A fixture is not the shape. This compares the real producer's dict
literal against every r["..."] its consumers read -- no fixture involved.
"""
import ast, sys

src = open(sys.argv[1], encoding="utf-8").read()
tree = ast.parse(src)
fns = {n.name: n for n in ast.walk(tree)
       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

PRODUCER = "_correction_rows"
CONSUMERS = ["api_marg_corrections_xlsx", "api_marg_corrections_csv",
             "_corrections_text", "page_marg_worklist"]

built = set()
for n in ast.walk(fns[PRODUCER]):
    if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "dict":
        built.update(k.arg for k in n.keywords if k.arg)
print("%s builds %d keys: %s" % (PRODUCER, len(built), ", ".join(sorted(built))))

bad = 0
for name in CONSUMERS:
    fn = fns.get(name)
    if not fn:
        print("  !! consumer %s not found" % name); bad += 1; continue
    read = set()
    for n in ast.walk(fn):
        if (isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name)
                and n.value.id in ("r", "d")
                and isinstance(n.slice, ast.Constant)
                and isinstance(n.slice.value, str)):
            read.add(n.slice.value)
    missing = read - built
    print("  %-32s reads %2d, missing %s" % (name, len(read), sorted(missing) or "none"))
    bad += len(missing)
print("MISSING KEYS:", bad)
sys.exit(1 if bad else 0)
