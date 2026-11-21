#!/usr/bin/env python3
"""Score output files against hand labels with the Track 1 cost matrix.

labels CSV columns: case_id,verdict[,reason_code]   (verdict = CLOSE | RFI | ESCALATE)
usage: python tests/score.py labels/gold.csv output/*.jsonl
Prints cost per case, wrongful closes, share of closable cases closed, and the verdict score
(share of the escalate-everything cost saved, as the brief defines it).
"""
import csv, json, sys

COST = {("CLOSE", "CLOSE"): 0, ("CLOSE", "RFI"): 3, ("CLOSE", "ESCALATE"): 3,
        ("RFI", "CLOSE"): 10, ("RFI", "RFI"): 0, ("RFI", "ESCALATE"): 2,
        ("ESCALATE", "CLOSE"): 10, ("ESCALATE", "RFI"): 3, ("ESCALATE", "ESCALATE"): 0}
gold = {}
with open(sys.argv[1], encoding="utf-8") as f:
    for r in csv.DictReader(f):
        v = (r.get("verdict") or "").strip().upper()
        if v in ("CLOSE", "RFI", "ESCALATE"):
            gold[r["case_id"].strip()] = (v, (r.get("reason_code") or "").strip())
pred = {}
for p in sys.argv[2:]:
    for l in open(p, encoding="utf-8"):
        r = json.loads(l); pred[r["case_id"]] = (r["verdict"], r["reason_code"])
ids = [c for c in gold if c in pred]
if not ids:
    sys.exit("no labelled cases found in the outputs")
cost = sum(COST[(gold[c][0], pred[c][0])] for c in ids)
base = sum(COST[(gold[c][0], "ESCALATE")] for c in ids)
wrong_close = [c for c in ids if pred[c][0] == "CLOSE" and gold[c][0] != "CLOSE"]
closable = [c for c in ids if gold[c][0] == "CLOSE"]
closed = [c for c in closable if pred[c][0] == "CLOSE"]
agree = sum(gold[c][0] == pred[c][0] for c in ids)
code_ids = [c for c in ids if gold[c][1] and gold[c][0] == pred[c][0]]
print("labelled cases scored: %d" % len(ids))
print("verdict agreement: %d/%d (%.0f%%)" % (agree, len(ids), 100 * agree / len(ids)))
print("cost per case: %.2f   (escalate-everything: %.2f)" % (cost / len(ids), base / len(ids)))
print("verdict score (share of escalate-everything cost saved): %.0f%%" % (100 * (1 - cost / base) if base else 100))
print("wrongful closes: %d %s" % (len(wrong_close), wrong_close[:10]))
print("closable cases closed: %d/%d" % (len(closed), len(closable)))
if code_ids:
    print("reason code agreement (where labelled): %d/%d" % (sum(gold[c][1] == pred[c][1] for c in code_ids), len(code_ids)))
for c in ids:
    if gold[c][0] != pred[c][0]:
        print("  disagree %s gold=%s ours=%s %s" % (c, gold[c][0], pred[c][0], pred[c][1]))
