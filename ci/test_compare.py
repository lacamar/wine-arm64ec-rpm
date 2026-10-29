#!/usr/bin/python3
import importlib.machinery
import importlib.util
from pathlib import Path

loader = importlib.machinery.SourceFileLoader("ci_run", str(Path(__file__).with_name("run")))
spec = importlib.util.spec_from_loader("ci_run", loader)
run = importlib.util.module_from_spec(spec)
loader.exec_module(run)


def r(status, failures=0):
    return {"status": status, "failures": failures, "detail": ""}


base = {"a": r("pass"), "b": r("fail", 3), "c": r("fail", 3), "d": r("fail", 3), "e": r("pass"), "f": r("timeout"), "g": r("fail", 2)}
cand = {"a": r("fail", 1), "b": r("fail", 5), "c": r("fail", 3), "d": r("pass"), "e": r("pass"), "f": r("timeout"), "g": r("crash"), "new": r("fail", 9)}

assert run.compare(base, cand) == {"a": "pass -> fail", "b": "3 -> 5 failures", "g": "fail -> crash"}
assert run.compare(base, base) == {}
assert run.compare(base, {"a": r("skip")}) == {"a": "pass -> skip", "e": "pass -> missing"}
assert run.compare(base, {}) == {"a": "pass -> missing", "e": "pass -> missing"}
assert run.fixed(base, cand) == ["d"]
lines = lambda st, *l: {"status": st, "failures": 0, "failed": list(l), "detail": ""}
assert run.compare({"x": lines("crash", "a.c:1")}, {"x": lines("crash", "a.c:1", "a.c:9")}) == {"x": "new failures at a.c:9"}
assert run.compare({"x": lines("crash", "a.c:1", "a.c:9")}, {"x": lines("crash", "a.c:1")}) == {}
assert run.compare({"x": lines("timeout", "a.c:1")}, {"x": lines("timeout", "a.c:5")}) == {}
print("ok")
