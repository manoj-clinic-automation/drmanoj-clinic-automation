"""Find names USED in a function before that same function later binds them.

Python decides a name is local for the WHOLE function body if it is assigned or
imported anywhere in it. So `io.BytesIO(...)` near the top of a function that
does `import io` two hundred lines further down is an UnboundLocalError at
runtime -- and neither py_compile nor pyflakes says a word.

Honest about its own blind spots: it ignores names declared global/nonlocal,
does not descend into nested functions or lambdas (their names are their own),
and skips comprehension targets (own scope since Python 3).
"""
import ast, sys

def _own(fn):
    """Nodes belonging to THIS function's scope, not a nested one."""
    out = []
    def walk(n, top=False):
        for ch in ast.iter_child_nodes(n):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                continue
            if isinstance(ch, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                continue
            out.append(ch)
            walk(ch)
    walk(fn, True)
    return out

def scan(path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    hits = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        nodes = _own(fn)
        skip = set()
        for n in nodes:
            if isinstance(n, (ast.Global, ast.Nonlocal)):
                skip.update(n.names)
        bound = {}
        for n in nodes:
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                for a in n.names:
                    nm = (a.asname or a.name).split(".")[0]
                    bound[nm] = min(bound.get(nm, n.lineno), n.lineno)
            elif isinstance(n, ast.Assign):
                for t in n.targets:
                    if isinstance(t, ast.Name):
                        bound[t.id] = min(bound.get(t.id, n.lineno), n.lineno)
        args = {a.arg for a in fn.args.args + fn.args.kwonlyargs}
        if fn.args.vararg: args.add(fn.args.vararg.arg)
        if fn.args.kwarg:  args.add(fn.args.kwarg.arg)
        seen = set()
        for n in nodes:
            if (isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
                    and n.id in bound and n.id not in skip and n.id not in args
                    and n.lineno < bound[n.id] and n.id not in seen):
                seen.add(n.id)
                hits.append((fn.name, n.id, n.lineno, bound[n.id]))
    return hits

for f, nm, used, b in scan(sys.argv[1]):
    print("%s(): '%s' used at line %d but only bound at line %d" % (f, nm, used, b))
print("USED-BEFORE-BOUND:", len(scan(sys.argv[1])))
