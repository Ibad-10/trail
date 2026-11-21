#!/usr/bin/env python3
"""Counterfactual test (idea from arXiv 2604.19755, "Explainable AML Triage with LLMs").

For every CLOSE, delete the documents it cited and run again. A CLOSE that survives without its own
evidence was not resting on that evidence. Reports how many CLOSEs stop being CLOSE.

usage: python tests/counterfactual_test.py <institution folder> <output file of a normal run>
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

src, out = os.path.abspath(sys.argv[1]), sys.argv[2]
here = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(out, encoding="utf-8")]
closes = {r["case_id"]: r for r in rows if r["verdict"] == "CLOSE"}
cited = set()
for r in closes.values():
    cited |= {e for e in r["evidence"] if not e.split("-")[1][:1] in ("T", "L")}

tmp = tempfile.mkdtemp()
dst = os.path.join(tmp, os.path.basename(src))
shutil.copytree(src, dst)
with open(os.path.join(src, "evidence.jsonl"), encoding="utf-8") as f:
    kept = [l for l in f if l.strip() and json.loads(l)["doc_id"] not in cited]
with open(os.path.join(dst, "evidence.jsonl"), "w", encoding="utf-8") as f:
    f.writelines(kept)

cf = os.path.join(tmp, "cf.jsonl")
subprocess.check_call([sys.executable, os.path.join(here, "..", "system", "controltrail.py"), dst, cf])
after = {json.loads(l)["case_id"]: json.loads(l) for l in open(cf, encoding="utf-8")}
survived = [c for c in closes if after[c]["verdict"] == "CLOSE"]
moved = {}
for c in closes:
    moved[after[c]["verdict"]] = moved.get(after[c]["verdict"], 0) + 1
print("%s: %d CLOSEs; without their cited documents -> %s; still CLOSE: %d" % (
    os.path.basename(src), len(closes), moved, len(survived)))
for c in survived[:10]:
    print("  ", c, after[c]["reason_code"])
shutil.rmtree(tmp)
sys.exit(1 if survived else 0)
