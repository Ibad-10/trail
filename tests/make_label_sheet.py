#!/usr/bin/env python3
"""Write labels/to_label.csv: 2 cases from every group of similar cases (same rules + same extra document types),
across all four institutions, with the engine's answer hidden. Label each by reading the case against POLICY.md
(the web app's case page shows all the evidence). The sheet stays git-ignored and is never read by system/."""
import csv, json, os, sys, collections
root = sys.argv[1]
COMMON = {"due_diligence_summary", "proof_of_address", "contact_note", "company_register_extract", "bank_statement"}
rows = []
for inst in ("bank", "emoney", "investment", "payments_fx"):
    d = os.path.join(root, inst)
    L = lambda f: [json.loads(l) for l in open(os.path.join(d, f), encoding="utf-8")]
    al = {a["alert_id"]: a["rule_id"] for a in L("alerts.jsonl")}
    ev = collections.defaultdict(set)
    for e in L("evidence.jsonl"):
        if e["type"] not in COMMON:
            ev[e["customer_id"]].add(e["type"])
    g = collections.defaultdict(list)
    for c in L("cases.jsonl"):
        g[(tuple(sorted({al[a] for a in c["alert_ids"]})), tuple(sorted(ev[c["customer_id"]])))].append(c["case_id"])
    for (rules, docs), cs in sorted(g.items()):
        for cid in (cs[0], cs[len(cs) // 2]) if len(cs) > 1 else (cs[0],):
            rows.append({"case_id": cid, "institution": inst, "rules": " ".join(rules), "extra_documents": " ".join(docs),
                         "group_size": len(cs), "verdict": "", "reason_code": "", "notes": ""})
os.makedirs("labels", exist_ok=True)
with open("labels/to_label.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print("wrote labels/to_label.csv with %d cases" % len(rows))
