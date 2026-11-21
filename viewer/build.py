#!/usr/bin/env python3
"""Build viewer/data.js from the dataset and ControlTrail's output (outside the scored system).

usage: python viewer/build.py <institutions root> <output dir>
The data file quotes the development data, so it is git-ignored and built locally.
"""
import json
import os
import re
import sys

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, "..", "system"))
from controltrail import Folder, Case, table_rows, norm  # noqa: E402

root, outdir = sys.argv[1], sys.argv[2]
cases = []
for inst in ("bank", "emoney", "investment", "payments_fx"):
    F = Folder(os.path.join(root, inst))
    out = {}
    with open(os.path.join(outdir, inst + ".jsonl"), encoding="utf-8") as f:
        for l in f:
            r = json.loads(l)
            out[r["case_id"]] = r
    for row in F.cases:
        r = out.get(row["case_id"])
        if not r:
            continue
        c = Case(F, row)
        cited = set(r["evidence"])
        docs = {d["doc_id"]: d for d in c.docs}
        nodes, edges = [], []

        def node(nid, col, label, sub="", kind="", src=None, hot=False):
            nodes.append({"id": nid, "col": col, "label": label, "sub": sub, "kind": kind, "src": src, "hot": hot})

        # Column 0: what fired
        for a in c.alerts:
            node(a["alert_id"], 0, a["rule_id"] + " " + a.get("rule_name", ""), a.get("message", "")[:160], "alert",
                 {"id": a["alert_id"], "text": a.get("message", "")}, True)
        # Column 1: money moved (alert transactions first, then cited ones)
        tx_ids = list(dict.fromkeys(c.alert_txn_ids + [e for e in r["evidence"] if e in F.txns]))[:8]
        for t in tx_ids:
            tx = F.txns[t]
            node(t, 1, "%s £%s" % ("In" if tx["direction"] == "in" else "Out", "{:,.2f}".format(tx["amount_gbp"])),
                 "%s · %s · %s" % (tx["booked_at"][:10], tx["channel"].replace("_", " "), tx.get("counterparty_country") or ""),
                 "txn", {"id": t, "text": json.dumps(tx, indent=1, ensure_ascii=False)}, t in cited)
            for a in c.alerts:
                if t in a.get("transaction_ids", []):
                    edges.append([a["alert_id"], t, "fired on", t])
        # Column 2: who is involved (counterparties, list entries, officers named in registers)
        parties = {}
        for t in tx_ids:
            nm = F.txns[t].get("counterparty_name")
            if nm:
                pid = "P:" + norm(nm)
                if pid not in parties:
                    parties[pid] = nm
                    node(pid, 2, nm, F.txns[t].get("counterparty_account") or "", "party",
                         {"id": t, "text": "Counterparty on transaction %s" % t})
                edges.append([t, pid, "paid" if F.txns[t]["direction"] == "out" else "received from", t])
        for a in c.alerts:
            le = a.get("measured", {}).get("list_entry")
            if le and le in F.list_entries:
                e = F.list_entries[le]
                node(le, 2, "List: " + e.get("name", ""), (e.get("reason") or "")[:120], "list",
                     {"id": le, "text": json.dumps(e, indent=1, ensure_ascii=False)}, le in cited)
                edges.append([a["alert_id"], le, "matched on " + a["measured"].get("matched_on", ""), a["alert_id"]])
        # Column 3: documents (cited first, then the rest of the file, capped)
        doc_order = [d for d in r["evidence"] if d in docs] + [d for d in sorted(docs) if d not in cited
                                                               and docs[d]["type"] not in ("due_diligence_summary", "proof_of_address", "contact_note")]
        for did in doc_order[:7]:
            d = docs[did]
            node(did, 3, d["type"].replace("_", " "), d.get("title", ""), "doc", {"id": did, "text": d["text"]}, did in cited)
            for t in tx_ids:
                amt = F.txns[t]["amount_gbp"]
                if "£{:,.2f}".format(amt) in d["text"]:
                    edges.append([t, did, "amount matches", did])
            for pid, nm in parties.items():
                if nm and norm(nm) in norm(d["text"]) and len(norm(nm)) > 3:
                    edges.append([pid, did, "named in", did])
            if d["type"] in ("company_register_extract", "significant_control_register"):
                for row_ in table_rows(d["text"]):
                    for a in c.alerts:
                        le = a.get("measured", {}).get("list_entry")
                        if le in F.list_entries and row_ and norm(row_[0]) == norm(F.list_entries[le].get("name")):
                            edges.append([le, did, "officer/PSC row", did])
        # Column 4: verdict
        node("V", 4, r["verdict"], r["reason_code"], "verdict", {"id": r["case_id"], "text": r["reason"]}, True)
        for e in r["evidence"]:
            if any(n["id"] == e for n in nodes):
                edges.append([e, "V", "relied on", e])
        cust = c.cust
        cases.append({
            "inst": inst, "case_id": r["case_id"], "customer": c.name, "kind": cust.get("kind"),
            "declared": cust.get("declared", {}), "rules": c.rules, "verdict": r["verdict"], "code": r["reason_code"],
            "reason": r["reason"], "evidence": r["evidence"], "held": row.get("held_payment_id"),
            "window": row.get("review_window"), "nodes": nodes, "edges": edges,
        })

with open(os.path.join(here, "data.js"), "w", encoding="utf-8") as f:
    f.write("window.CT_DATA=")
    json.dump(cases, f, ensure_ascii=False, separators=(",", ":"))
    f.write(";\n")
print("wrote %d cases to viewer/data.js" % len(cases))
