#!/usr/bin/env python3
"""Rename-and-shuffle test.

Renumbers every document, transaction, alert, list entry, customer and case ID, shuffles the order of
every record file except cases.jsonl, then checks each case gets the same verdict and reason code.
Proves the engine reads the evidence rather than memorising the development cases.

usage: python tests/perturb_test.py <institution folder>
"""
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile

src = os.path.abspath(sys.argv[1])
here = os.path.dirname(os.path.abspath(__file__))
run = [sys.executable, os.path.join(here, "..", "system", "trail.py")]
tmp = tempfile.mkdtemp()
dst = os.path.join(tmp, os.path.basename(src.rstrip("/\\")))
rng = random.Random(7)
ID = re.compile(r"\b([A-Z]{2,3})-([A-Z]{1,2})(\d{3,})\b|\b([A-Z]{3})-(\d{2,})\b")


def remap(text):
    def f(m):
        if m.group(1):
            return "%s-%s9%s" % (m.group(1), m.group(2), m.group(3))
        return "%s-7%s" % (m.group(4), m.group(5))
    return ID.sub(f, text)


# Write into a fresh tree so a renamed file can never overwrite an original.
for root, _, files in os.walk(src):
    rel = os.path.relpath(root, src)
    os.makedirs(os.path.join(dst, rel), exist_ok=True)
    for fn in sorted(files):
        p = os.path.join(root, fn)
        np = os.path.join(dst, rel, remap(fn))
        if not (fn.endswith(".jsonl") or fn.endswith(".md")) or fn == "POLICY.md":
            shutil.copyfile(p, np)
            continue
        with open(p, encoding="utf-8") as f:
            t = remap(f.read())
        if fn.endswith(".jsonl") and fn != "cases.jsonl":
            lines = [l for l in t.splitlines() if l.strip()]
            rng.shuffle(lines)
            t = "\n".join(lines) + "\n"
        with open(np, "w", encoding="utf-8") as f:
            f.write(t)

a, b = os.path.join(tmp, "orig.jsonl"), os.path.join(tmp, "pert.jsonl")
subprocess.check_call(run + [src, a])
subprocess.check_call(run + [dst, b])
orig = [json.loads(l) for l in open(a, encoding="utf-8")]
pert = [json.loads(l) for l in open(b, encoding="utf-8")]
diff = [(o["case_id"], o["verdict"], o["reason_code"], p["verdict"], p["reason_code"])
        for o, p in zip(orig, pert) if (o["verdict"], o["reason_code"]) != (p["verdict"], p["reason_code"])]
print("%s: %d cases, %d changed after renaming IDs and shuffling records" % (os.path.basename(src), len(orig), len(diff)))
for d in diff[:10]:
    print("  ", d)
shutil.rmtree(tmp)
sys.exit(1 if diff or len(orig) != len(pert) else 0)
