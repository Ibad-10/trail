#!/usr/bin/env python3
"""Check an output file against its institution folder: one line per case, codes valid, cited IDs exist."""
import json, os, re, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trail import VERDICT_OF, load_jsonl

folder, out = sys.argv[1], sys.argv[2]
cases = {c["case_id"]: c for c in load_jsonl(os.path.join(folder, "cases.jsonl"))}
ids = set()
for f, k in (("alerts.jsonl", "alert_id"), ("transactions.jsonl", "transaction_id"), ("evidence.jsonl", "doc_id"),
             ("internal_list.jsonl", "entry_id"), ("previous_reviews.jsonl", "review_id")):
    ids |= {r[k] for r in load_jsonl(os.path.join(folder, f))}
rows = load_jsonl(out)
errs = []
seen = collections.Counter(r["case_id"] for r in rows)
errs += ["missing case %s" % c for c in cases if c not in seen]
errs += ["duplicate case %s" % c for c, n in seen.items() if n > 1]
for r in rows:
    c = cases.get(r["case_id"])
    if not c:
        errs.append("unknown case %s" % r["case_id"]); continue
    if r["alert_ids"] != c["alert_ids"]: errs.append("%s alert_ids differ" % r["case_id"])
    if VERDICT_OF.get(r["reason_code"]) != r["verdict"]: errs.append("%s code/verdict mismatch" % r["case_id"])
    bad = [e for e in r["evidence"] if e not in ids]
    if bad or not r["evidence"]: errs.append("%s bad evidence %s" % (r["case_id"], bad))
    n = len([s for s in re.split(r"(?<=[.!?])\s+", r["reason"].strip()) if s])
    if not 2 <= n <= 4: errs.append("%s reason has %d sentences" % (r["case_id"], n))
print("%s: %d cases, %d errors" % (os.path.basename(out), len(rows), len(errs)))
print("  verdicts:", dict(collections.Counter(r["verdict"] for r in rows)))
for e in errs[:15]: print("  ", e)
sys.exit(1 if errs else 0)
