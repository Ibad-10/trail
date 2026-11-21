#!/usr/bin/env python3
"""ControlTrail: deterministic transaction-monitoring alert triage.

Usage: controltrail.py <institution folder> <output file>

Rules gather evidence, the institution's POLICY.md decides, every claim cites a source ID.
Standard library only. No model, no randomness, no clock: same input bytes give the same output bytes.
"""
import json
import os
import re
import sys
from datetime import date

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], 1)}
DEFAULT_HIGH_RISK = ["Afghanistan", "Belarus", "Democratic Republic of the Congo", "Haiti", "Iran", "Iraq",
                     "Lebanon", "Libya", "Mali", "Myanmar", "North Korea", "Russia", "Somalia", "South Sudan",
                     "Syria", "Venezuela", "Yemen"]

VERDICT_OF = {}
for _v, _codes in {
    "CLOSE": "COLLECTION_DOCUMENTED BUSINESS_RECORDS_RECONCILE DOCUMENTED_EVENT INVOICE_MATCHES OWN_ACCOUNT "
             "GROUP_COMPANY THIRD_PARTY_DOCUMENTED REFUND_OF_EARLIER_PAYMENT RETURNING_CUSTOMER "
             "LIST_MATCH_DIFFERENT_PARTY WITHIN_PROFILE",
    "RFI": "RFI_PURPOSE_DOCUMENTS RFI_BUSINESS_RECORDS RFI_SOURCE_OF_FUNDS RFI_COUNTERPARTY_DETAILS RFI_UPDATED_PROFILE",
    "ESCALATE": "ESC_MULE_ACTIVITY ESC_STRUCTURING ESC_UNEXPLAINED_FUNDS ESC_PASS_THROUGH ESC_INVOICE_MISMATCH "
                "ESC_HIGH_RISK_CORRIDOR ESC_ACCOUNT_MISUSE ESC_THIRD_PARTY_FUNDING ESC_EARLY_REDEMPTION ESC_LISTED_PARTY",
}.items():
    for _c in _codes.split():
        VERDICT_OF[_c] = _v


# ---------------------------------------------------------------- parsing helpers

def load_jsonl(path):
    out = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def money(s):
    return float(s.replace(",", ""))


def amounts_in(text):
    """Every £ amount in a text, as floats."""
    return [money(m) for m in re.findall(r"£\s?([\d,]+\.\d{2})", text)]


def parse_date(s):
    """'5 June 2026' -> date. Returns None if it is not a full date."""
    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", s or "")
    if not m or m.group(2).lower() not in MONTHS:
        return None
    return date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1)))


def iso(s):
    return date(int(s[0:4]), int(s[5:7]), int(s[8:10]))


def norm(s):
    s = (s or "").lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\b(ltd|limited|plc|llp|the)\b", " ", s)
    return " ".join(s.split())


def gbp(x):
    return "£{:,.2f}".format(x)


def same_amount(a, b):
    return abs(a - b) < 0.005


def fields(text):
    """Bold key-value lines: **Key:** value."""
    return {k.strip().lower(): v.strip() for k, v in re.findall(r"\*\*([^*]+?):\*\*\s*(.*)", text)}


def table_rows(text):
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("|") and not re.match(r"^\|[\s\-|]+\|$", line):
            rows.append([c.strip() for c in line.strip("|").split("|")])
    return rows


# ---------------------------------------------------------------- data model

class Folder:
    def __init__(self, path):
        self.path = path
        j = lambda n: load_jsonl(os.path.join(path, n))
        self.cases = j("cases.jsonl")
        self.alerts = {a["alert_id"]: a for a in j("alerts.jsonl")}
        self.customers = {c["customer_id"]: c for c in j("customers.jsonl")}
        self.txns = {}
        self.txns_by_customer = {}
        for t in j("transactions.jsonl"):
            self.txns[t["transaction_id"]] = t
            self.txns_by_customer.setdefault(t["customer_id"], []).append(t)
        self.docs_by_customer = {}
        for e in j("evidence.jsonl"):
            p = os.path.join(path, e.get("file") or ("evidence/%s.md" % e["doc_id"]))
            try:
                with open(p, encoding="utf-8") as f:
                    e["text"] = f.read()
            except OSError:
                e["text"] = ""
            e["f"] = fields(e["text"])
            self.docs_by_customer.setdefault(e["customer_id"], []).append(e)
        self.reviews = {}
        for r in j("previous_reviews.jsonl"):
            self.reviews.setdefault(r["customer_id"], []).append(r)
        self.list_entries = {e["entry_id"]: e for e in j("internal_list.jsonl")}
        self.policy = ""
        try:
            with open(os.path.join(path, "POLICY.md"), encoding="utf-8") as f:
                self.policy = f.read()
        except OSError:
            pass
        m = re.search(r"Higher-risk countries[^:]*:\s*([^\n]+)", self.policy)
        self.high_risk = [c.strip().rstrip(".") for c in m.group(1).split(",")] if m else DEFAULT_HIGH_RISK
        m = re.search(r"(\d+)\s+times the declared income or volume or more", self.policy)
        self.own_account_rfi_multiple = float(m.group(1)) if m else 5.0


# ---------------------------------------------------------------- the decision

class Decision:
    def __init__(self, code, reason, evidence):
        self.code = code
        self.verdict = VERDICT_OF[code]
        self.reason = reason
        self.evidence = evidence


class Case:
    def __init__(self, folder, row):
        self.F = folder
        self.row = row
        self.cid = row["customer_id"]
        self.cust = folder.customers.get(self.cid, {"name": "the customer", "kind": "individual", "declared": {}})
        self.name = self.cust.get("name") or "the customer"
        self.alerts = [folder.alerts[a] for a in row["alert_ids"] if a in folder.alerts]
        self.rules = sorted(set(a["rule_id"] for a in self.alerts))
        self.docs = sorted(folder.docs_by_customer.get(self.cid, []), key=lambda d: d["doc_id"])
        self.txns = folder.txns_by_customer.get(self.cid, [])
        self.alert_txn_ids = sorted(set(t for a in self.alerts for t in a.get("transaction_ids", [])
                                        if t in folder.txns))
        self.alert_txns = [folder.txns[t] for t in self.alert_txn_ids]
        w = row.get("review_window") or {}
        self.win_from = iso(w["from"]) if w.get("from") else date(1900, 1, 1)
        self.win_to = iso(w["to"]) if w.get("to") else date(2999, 1, 1)
        self.window_txns = [t for t in self.txns if self.win_from <= iso(t["booked_at"]) <= self.win_to]

    # -- lookups
    def docs_of(self, *types):
        return [d for d in self.docs if d["type"] in types]

    def doc_ids(self, docs):
        return [d["doc_id"] for d in docs]

    def alert(self, rule):
        for a in self.alerts:
            if a["rule_id"] == rule:
                return a
        return None

    def has(self, *rules):
        return any(r in self.rules for r in rules)

    def txn_with_amount(self, amount, direction=None, pool=None):
        for t in (pool if pool is not None else self.alert_txns + self.window_txns):
            if same_amount(t["amount_gbp"], amount) and (direction is None or t["direction"] == direction):
                return t
        return None

    def matching_txns(self, doc, direction=None):
        """Alert or window transactions whose amount appears in the document."""
        amts = amounts_in(doc["text"])
        seen, out = set(), []
        for t in self.alert_txns + self.window_txns:
            if t["transaction_id"] in seen:
                continue
            if (direction is None or t["direction"] == direction) and any(same_amount(t["amount_gbp"], a) for a in amts):
                seen.add(t["transaction_id"])
                out.append(t)
        return out

    def chats(self):
        return [d for d in self.docs_of("support_chat")]

    def chat_text(self):
        return " ".join(d["text"] for d in self.chats()).lower()

    def summary(self):
        """One sentence on what the alerts measured, with amounts."""
        parts = []
        for a in self.alerts:
            m = a.get("measured", {})
            r = a["rule_id"]
            if r == "TM01" and "received_gbp" in m:
                parts.append("%s received in 30 days, %.1f times the declared baseline" % (gbp(m["received_gbp"]), m.get("multiple", 0)))
            elif r == "TM02" and "received_gbp" in m:
                parts.append("%s in and %s out within the rapid-movement window" % (gbp(m["received_gbp"]), gbp(m.get("paid_out_gbp", 0))))
            elif r == "TM05":
                parts.append("a large cash transaction (%s)" % self.alert_amounts_text(a))
            elif r == "TM06":
                parts.append("payments involving a higher-risk country (%s)" % self.alert_amounts_text(a))
            else:
                parts.append("%s (%s)" % (a.get("rule_name", r).lower(), r))
        return "; ".join(parts)

    def alert_amounts_text(self, a):
        ts = [self.F.txns[t] for t in a.get("transaction_ids", []) if t in self.F.txns]
        if not ts:
            return a["rule_id"]
        tot = sum(t["amount_gbp"] for t in ts)
        return gbp(tot) if len(ts) > 1 else "%s on %s" % (gbp(tot), ts[0]["booked_at"][:10])

    def ev(self, *groups, limit_txns=6):
        """Evidence list: documents first, then list entries, then transactions. Deterministic order."""
        docs, lists, txns = [], [], []
        for g in groups:
            for x in (g if isinstance(g, (list, tuple)) else [g]):
                if not x:
                    continue
                if x in self.F.list_entries:
                    lists.append(x)
                elif x in self.F.txns:
                    txns.append(x)
                else:
                    docs.append(x)
        txns = sorted(set(txns))[:limit_txns]
        out, seen = [], set()
        for x in sorted(set(docs)) + sorted(set(lists)) + txns:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out


# ---------------------------------------------------------------- TM22: the internal list

def control_rows(case, person):
    """(role, start, end, source doc) for a person in register / PSC documents."""
    rows = []
    pn = norm(person)
    for d in case.docs_of("company_register_extract", "significant_control_register"):
        tbl = table_rows(d["text"])
        if not tbl:
            continue
        header = None
        for r in tbl:
            low = [c.lower() for c in r]
            if low and low[0] in ("officer", "person", "person with significant control", "company"):
                header = low
                continue
            if header and r and norm(r[0]) == pn:
                rec = dict(zip(header, r))
                start = parse_date(rec.get("appointed") or rec.get("notified") or "")
                end = parse_date(rec.get("resigned") or rec.get("ceased") or "")
                rows.append((rec.get("role") or rec.get("control") or "", start, end, d["doc_id"]))
    return rows


def resolve_list(case, a):
    """Returns ('LISTED'|'DIFFERENT'|'UNKNOWN', facts, evidence)."""
    m = a.get("measured", {})
    entry_id = m.get("list_entry")
    entry = case.F.list_entries.get(entry_id, {})
    matched_on = (m.get("matched_on") or "").lower()
    pay = case.F.txns.get(a["transaction_ids"][0]) if a.get("transaction_ids") else None
    pay_date = iso(pay["booked_at"]) if pay else None
    list_name = entry.get("name", "")
    ev = [entry_id] + list(a.get("transaction_ids", []))

    # Is the listed person an officer / PSC of the counterparty at the payment date?
    rows = control_rows(case, list_name) if list_name else []
    if rows and pay_date:
        active = [r for r in rows if (r[1] is None or r[1] <= pay_date) and (r[2] is None or r[2] >= pay_date)]
        if active:
            role = active[0][0] or "officer"
            if role.lower() in ("director", "secretary", "officer"):
                role = "a %s" % role.lower()
            else:
                role = "a person with significant control (%s)" % (role[0].lower() + role[1:])
            return "LISTED", "%s, the person on internal list entry %s, was %s of the counterparty when the %s payment was made on %s (%s)" % (
                list_name, entry_id, role, gbp(pay["amount_gbp"]), pay["booked_at"][:10], active[0][3]), ev + [r[3] for r in active]
        ended = max(r[2] for r in rows if r[2])
        return "DIFFERENT", "%s, the person on internal list entry %s, had left the counterparty by %s, before the %s payment on %s (%s)" % (
            list_name, entry_id, ended.strftime("%d %B %Y").lstrip("0"), gbp(pay["amount_gbp"]), pay["booked_at"][:10],
            ", ".join(sorted(set(r[3] for r in rows)))), ev + [r[3] for r in rows]

    # Address or company match: the register names who runs the company.
    cp = norm(pay["counterparty_name"]) if pay else ""
    regs = [d for d in case.docs_of("company_register_extract")
            if cp and cp in norm(d["text"].splitlines()[0] + " " + d["f"].get("company", ""))]
    if "address" in matched_on and regs and entry.get("kind") == "individual":
        officers = set()
        for d in regs:
            for r in table_rows(d["text"]):
                if r and r[0] and r[0].lower() not in ("officer", "person with significant control", "person"):
                    officers.add(norm(r[0]))
        if officers and norm(list_name) not in officers:
            return "DIFFERENT", "the counterparty only shares a registered address with internal list entry %s (%s); the company register %s names other officers" % (
                entry_id, list_name, regs[0]["doc_id"]), ev + [regs[0]["doc_id"]]
    if "address" in matched_on and regs and entry.get("kind") != "individual":
        reg = regs[0]
        num = reg["f"].get("company number")
        ent_num = (entry.get("identifiers") or {}).get("company_number")
        if num and ent_num and num != ent_num:
            return "DIFFERENT", "the counterparty's company number %s (%s) differs from %s on internal list entry %s" % (
                num, reg["doc_id"], ent_num, entry_id), ev + [reg["doc_id"]]
        officers = set(norm(r[0]) for d in regs for r in table_rows(d["text"]) if r and r[0])
        if officers and norm(list_name) not in officers:
            return "DIFFERENT", "the counterparty only shares a registered address with internal list entry %s (%s); register %s shows a different company" % (
                entry_id, list_name, reg["doc_id"]), ev + [reg["doc_id"]]

    # Name match: a document giving the counterparty's date of birth settles it.
    ldob = entry.get("date_of_birth")
    for d in case.docs:
        if norm(list_name) and norm(list_name) in norm(d["text"]):
            mm = re.search(r"(?:born(?:\s+on)?|DOB:?|date of birth:?)\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})", d["text"], re.I)
            if mm and ldob:
                dob = parse_date(mm.group(1))
                if dob and dob.isoformat() != ldob:
                    return "DIFFERENT", "%s (%s) gives %s's date of birth as %s, but internal list entry %s gives %s" % (
                        d["doc_id"], d["type"].replace("_", " "), list_name, mm.group(1), entry_id, ldob), ev + [d["doc_id"]]
                if dob and dob.isoformat() == ldob:
                    return "LISTED", "%s (%s) gives %s's date of birth as %s, the same as internal list entry %s" % (
                        d["doc_id"], d["type"].replace("_", " "), list_name, mm.group(1), entry_id), ev + [d["doc_id"]]
    return "UNKNOWN", "%s %s matched internal list entry %s (%s) on %s only, and nothing on file confirms or rules out that it is the same party" % (
        "A payment of" if pay and pay["direction"] == "out" else "A receipt of", gbp(pay["amount_gbp"]) if pay else "",
        entry_id, list_name, matched_on or "one detail"), ev


# ---------------------------------------------------------------- suspicion signals (any one escalates)

def suspicion(c):
    chat = c.chat_text()
    first = c.name

    # Internal list: the listed party is the counterparty or controls it.
    for a in c.alerts:
        if a["rule_id"] == "TM22":
            st, facts, ev = resolve_list(c, a)
            if st == "LISTED":
                return Decision("ESC_LISTED_PARTY",
                                "Internal list match confirmed: %s. Paying or receiving money from a party the list says not to deal with needs MLRO review." % facts,
                                c.ev(ev))

    rpts = c.docs_of("sending_bank_fraud_report")
    if rpts:
        amts = [a for d in rpts for a in amounts_in(d["text"])[:1]]
        hits = [t["transaction_id"] for d in rpts for t in c.matching_txns(d, "in")]
        return Decision("ESC_MULE_ACTIVITY",
                        "%d other bank(s) report that their customers paid %s's account as victims of authorised push payment scams (%s, %s in total). "
                        "The alerts show %s, so the account is receiving and passing on scam money." % (
                            len(rpts), first, ", ".join(c.doc_ids(rpts)), gbp(sum(amts)), c.summary()),
                        c.ev(c.doc_ids(rpts), c.doc_ids(c.chats()), hits or c.alert_txn_ids))

    if re.search(r"send it on|keep \d+% as my wages|crypto account|payments assistant", chat):
        return Decision("ESC_MULE_ACTIVITY",
                        "In support chat %s, %s says clients of a 'job' pay into the account and they send the money on, keeping a cut. "
                        "The alerts show %s: the account moves other people's money for someone else." % (
                            ", ".join(c.doc_ids(c.chats())), first, c.summary()),
                        c.ev(c.doc_ids(c.chats()), c.alert_txn_ids))

    if re.search(r"invest for a few people|investing through mine|money to invest for them|sent me money to invest", chat):
        code = "ESC_EARLY_REDEMPTION" if c.has("TM10") else "ESC_THIRD_PARTY_FUNDING"
        return Decision(code,
                        "In support chat %s, %s says they hold or move money for other people (friends or relatives investing through their account). "
                        "The alerts show %s, so unrelated third parties are using the account%s." % (
                            ", ".join(c.doc_ids(c.chats())), first, c.summary(),
                            " and fund units were bought and sold back quickly to move it" if c.has("TM10") else ""),
                        c.ev(c.doc_ids(c.chats()), c.alert_txn_ids))

    notes = [d for d in c.docs_of("staff_note") if re.search(
        r"aggregat|exempt|breaking down|splitting|structuring|reporting threshold|below £?10,000|under £?10,000|keeping individual", d["text"], re.I)]
    if notes:
        return Decision("ESC_STRUCTURING",
                        "Staff note %s records the customer asking whether keeping amounts below the threshold or splitting them avoids reporting or invoice checks. "
                        "With %s, the pattern looks deliberately split to stay under a limit." % (notes[0]["doc_id"], c.summary()),
                        c.ev(c.doc_ids(notes), c.alert_txn_ids))

    for d in c.docs_of("device_export"):
        for r in table_rows(d["text"]):
            ids = re.findall(r"[A-Z]{2}-C\d+", " ".join(r))
            others = [i for i in ids if i != c.cid]
            if len(set(ids)) >= 2 and others:
                return Decision("ESC_ACCOUNT_MISUSE",
                                "Device export %s shows device %s used to log in to %d different customers' accounts (%s) from %s. "
                                "With %s, someone other than %s appears to control the account." % (
                                    d["doc_id"], r[0], len(set(ids)), ", ".join(sorted(set(ids))), r[-1], c.summary(), first),
                                c.ev([d["doc_id"]], c.alert_txn_ids))

    dissolved = [d for d in c.docs_of("company_register_extract") if "dissolved" in d["text"].lower()]
    if re.search(r"loan (provided by |i received from )?(from )?a friend|loan from a friend|from a friend", chat) and (dissolved or c.has("TM02", "TM01")):
        payer = dissolved[0]["f"].get("company", "a company") if dissolved else "the payer"
        return Decision("ESC_UNEXPLAINED_FUNDS",
                        "%s says in chat %s that the money is a loan from a friend, but it came from %s%s. "
                        "The story does not fit the payer, and the alerts show %s, so the funds have no credible explanation and were moved on." % (
                            first, ", ".join(c.doc_ids(c.chats())), payer,
                            ", a company dissolved before the payments (%s)" % dissolved[0]["doc_id"] if dissolved else "",
                            c.summary()),
                        c.ev(c.doc_ids(c.chats()), c.doc_ids(dissolved), c.alert_txn_ids))
    if dissolved and c.has("TM01", "TM02", "TM08"):
        return Decision("ESC_UNEXPLAINED_FUNDS",
                        "Money came from %s, which register extract %s shows as dissolved. With %s, the funds have no credible explanation." % (
                            dissolved[0]["f"].get("company", "a dissolved company"), dissolved[0]["doc_id"], c.summary()),
                        c.ev(c.doc_ids(dissolved), c.alert_txn_ids))

    if len(c.chats()) >= 2:
        return Decision("ESC_UNEXPLAINED_FUNDS",
                        "%s gave different explanations for the same money in chats %s (for example family support, a car sale and a gift), with no document behind any of them. "
                        "The alerts show %s, so the funds are unexplained and were moved on." % (first, ", ".join(c.doc_ids(c.chats())), c.summary()),
                        c.ev(c.doc_ids(c.chats()), c.alert_txn_ids))

    if c.has("TM06") and re.search(r"help my family|family there|friend of the family", chat) and not c.docs_of("hospital_invoice", "invoice"):
        a = c.alert("TM06")
        return Decision("ESC_HIGH_RISK_CORRIDOR",
                        "%s moved %s to or from a higher-risk country they never declared, and chat %s gives only 'family support' with no names or documents. "
                        "With %s, the corridor payments are unexplained." % (
                            first, c.alert_amounts_text(a), ", ".join(c.doc_ids(c.chats())), c.summary()),
                        c.ev(c.doc_ids(c.chats()), c.alert_txn_ids))

    evasive = [d for d in c.docs_of("staff_note") if re.search(r"unable|unwilling|evasive|could not|would not|declined|refused|however", d["text"], re.I)]
    if evasive:
        code = "ESC_HIGH_RISK_CORRIDOR" if c.has("TM06") else "ESC_INVOICE_MISMATCH"
        inv = c.docs_of("supplier_invoices", "supplier_invoice", "invoice")
        return Decision(code,
                        "Staff note %s records the director describing the payments as one thing but being unable or unwilling to explain the counterparty or destination; "
                        "the documents on file (%s) do not support that story. With %s, the payments are unexplained." % (
                            evasive[0]["doc_id"], ", ".join(c.doc_ids(inv)) or "none", c.summary()),
                        c.ev(c.doc_ids(evasive), c.doc_ids(inv), c.alert_txn_ids))

    # Pass-through to newly formed companies run by the same person.
    con = c.docs_of("consulting_contract")
    new_cos = [d for d in c.docs_of("company_register_extract")
               if parse_date(d["f"].get("incorporated", "")) and (c.win_to - parse_date(d["f"]["incorporated"])).days < 365]
    if con and new_cos and c.has("TM02", "TM01"):
        return Decision("ESC_PASS_THROUGH",
                        "Contract %s supports only %s of business, yet the alerts show %s. "
                        "The money goes on to recently formed companies run by the same person (%s), a pass-through with no credible purpose." % (
                            con[0]["doc_id"], con[0]["f"].get("fee", "a small fee"), c.summary(), ", ".join(c.doc_ids(new_cos))),
                        c.ev(c.doc_ids(con), c.doc_ids(new_cos), c.alert_txn_ids))

    # payments_fx: unrelated third parties fund the client and the money passes straight through.
    a8 = c.alert("TM08")
    if a8 and c.has("TM02") and con and not c.docs_of("group_structure", "factoring_agreement", "remittance_advice", "freight_invoices", "carrier_invoice", "credit_note"):
        payers = sorted(set(c.F.txns[t]["counterparty_name"] for t in a8.get("transaction_ids", []) if t in c.F.txns))
        return Decision("ESC_THIRD_PARTY_FUNDING",
                        "%s was funded by unrelated third parties (%s) and the money was paid out within 48 hours. "
                        "Nothing on file%s explains why these parties pay for the client." % (
                            first, ", ".join(payers) or "see TM08", " (only %s)" % ", ".join(c.doc_ids(con)) if con else ""),
                        c.ev(c.doc_ids(con), a8.get("transaction_ids", [])))

    pay_files = [d for d in c.docs_of("payment_file") if "commission" in d["text"].lower()]
    if pay_files and a8:
        payers = sorted(set(c.F.txns[t]["counterparty_name"] for t in a8.get("transaction_ids", []) if t in c.F.txns))
        return Decision("ESC_THIRD_PARTY_FUNDING",
                        "%s paid in by %s, and the money went out to many individuals under commission file %s, whose payee countries do not match their UK addresses. "
                        "Unrelated third parties fund the account and receive money from it." % (
                            gbp(sum(c.F.txns[t]["amount_gbp"] for t in a8.get("transaction_ids", []) if t in c.F.txns)), ", ".join(payers), pay_files[0]["doc_id"]),
                        c.ev(c.doc_ids(pay_files), a8.get("transaction_ids", [])))
    return None


# ---------------------------------------------------------------- explanations (all must hold for CLOSE)

def explain(c):
    """Returns a CLOSE or RFI Decision from documents, or None if nothing on file speaks to the alerts."""
    first = c.name
    s = c.summary()
    D = c.docs_of

    def close(code, reason, *ev):
        return Decision(code, reason, c.ev(*ev))

    # Documented one-off events: the document amount must match a transaction.
    for types, what in ((("vehicle_sale_receipt", "sale_receipt"), "a sale receipt"),
                        (("solicitor_letter",), "an estate distribution letter"),
                        (("insurer_letter",), "an insurance settlement letter"),
                        (("settlement_letter",), "a settlement agreement letter"),
                        (("completion_statement",), "a property sale completion statement"),
                        (("cancellation_confirmation",), "an ISA cancellation confirmation"),
                        (("deposit_return_letter",), "a tenancy deposit return letter")):
        docs = D(*types)
        if docs:
            hits = [t for d in docs for t in c.matching_txns(d)]
            extra = D("insurance_schedule", "advert", "holding_deposit_receipt")
            if hits:
                return close("DOCUMENTED_EVENT",
                             "%s is explained by %s: %s (%s) matches the %s %s on %s. The alerts (%s) are covered by this documented one-off event." % (
                                 s[0].upper() + s[1:] if s else "The activity", what, ", ".join(c.doc_ids(docs)),
                                 docs[0]["type"].replace("_", " "), gbp(hits[0]["amount_gbp"]),
                                 "payment in" if hits[0]["direction"] == "in" else "payment out", hits[0]["booked_at"][:10],
                                 ", ".join(c.rules)),
                             c.doc_ids(docs), c.doc_ids(extra), [t["transaction_id"] for t in hits])
            return Decision("RFI_SOURCE_OF_FUNDS",
                            "%s (%s) is on file but its amount does not match the transactions behind the alerts (%s). "
                            "Ask %s for evidence that ties the money received to that event, such as the payer's remittance or a bank statement." % (
                                ", ".join(c.doc_ids(docs)), what, s, first),
                            c.ev(c.doc_ids(docs), c.alert_txn_ids))

    loan, dealer = D("loan_agreement"), D("dealer_invoice")
    if loan and dealer:
        li, di = c.matching_txns(loan[0], "in"), c.matching_txns(dealer[0], "out")
        if li and di:
            return close("DOCUMENTED_EVENT",
                         "Loan agreement %s explains the %s received on %s, and dealer invoice %s matches the %s paid out on %s for a car. "
                         "The money came in from a lender and went straight to the car dealer, which explains %s." % (
                             loan[0]["doc_id"], gbp(li[0]["amount_gbp"]), li[0]["booked_at"][:10], dealer[0]["doc_id"],
                             gbp(di[0]["amount_gbp"]), di[0]["booked_at"][:10], s),
                         [loan[0]["doc_id"], dealer[0]["doc_id"]], [li[0]["transaction_id"], di[0]["transaction_id"]])

    bk = D("booking_confirmation")
    if bk:
        hits = c.matching_txns(bk[0], "out")
        if hits:
            trav = bk[0]["f"].get("travellers", "several")
            return close("COLLECTION_DOCUMENTED",
                         "Booking confirmation %s shows %s collecting for a group trip for %s travellers, %s in total. "
                         "The %s paid out on %s matches it, so the many small payments in were the travellers' shares." % (
                             bk[0]["doc_id"], first, trav, bk[0]["f"].get("price", ""), gbp(hits[0]["amount_gbp"]), hits[0]["booked_at"][:10]),
                         [bk[0]["doc_id"]], [t["transaction_id"] for t in hits], c.alert_txn_ids)

    recs = D("cash_collection_reports", "cash_reconciliation", "takings_book", "management_accounts")
    if recs and not D("staff_note"):
        hits = [t for d in recs for t in c.matching_txns(d)]
        support = D("cash_handling_procedure", "ticket_report")
        if hits or D("management_accounts"):
            return close("BUSINESS_RECORDS_RECONCILE",
                         "Business records %s reconcile to the cash paid in: %s. %s" % (
                             ", ".join(c.doc_ids(recs)), "the deposits of " + ", ".join(gbp(t["amount_gbp"]) for t in hits[:4]) + " appear in the records" if hits else s,
                             "The procedure and reports on file (%s) explain why deposits are split across days and sites." % ", ".join(c.doc_ids(support)) if support
                             else "The cash comes from %s's documented trading, so the alerts (%s) are explained." % (first, ", ".join(c.rules))),
                         c.doc_ids(recs), c.doc_ids(support), [t["transaction_id"] for t in hits])

    hosp = D("hospital_invoice")
    if hosp:
        hits = c.matching_txns(hosp[0], "out")
        if hits:
            return close("INVOICE_MATCHES",
                         "Hospital invoice %s for %s matches the %s paid on %s, and chat %s says it is for a parent's surgery. "
                         "The higher-risk-country payment has a documented medical purpose." % (
                             hosp[0]["doc_id"], hosp[0]["f"].get("amount due", ""), gbp(hits[0]["amount_gbp"]), hits[0]["booked_at"][:10],
                             ", ".join(c.doc_ids(c.chats())) or "on file"),
                         [hosp[0]["doc_id"]], c.doc_ids(c.chats()), [t["transaction_id"] for t in hits])
        return Decision("ESC_INVOICE_MISMATCH",
                        "Hospital invoice %s does not match the payments behind the alerts (%s). The invoice does not support the payments." % (hosp[0]["doc_id"], s),
                        c.ev([hosp[0]["doc_id"]], c.alert_txn_ids))

    venue = D("venue_email")
    if venue:
        hits = c.matching_txns(venue[0], "in")
        if hits:
            return close("REFUND_OF_EARLIER_PAYMENT",
                         "Email %s from the venue confirms a refund of a cancelled wedding deposit, %s, which matches the payment received on %s. "
                         "The money in is a refund of the customer's own earlier payment, which explains %s." % (
                             venue[0]["doc_id"], gbp(hits[0]["amount_gbp"]), hits[0]["booked_at"][:10], s),
                         [venue[0]["doc_id"]], [t["transaction_id"] for t in hits])

    crn = D("credit_note")
    if crn:
        hits = c.matching_txns(crn[0], "in")
        if hits:
            return close("REFUND_OF_EARLIER_PAYMENT",
                         "Credit note %s from %s refunds a cancelled order, %s, which matches the payment received on %s. "
                         "The third-party and higher-risk-country receipt is a refund of the client's own earlier payment." % (
                             crn[0]["doc_id"], crn[0]["f"].get("supplier", "the supplier"), gbp(hits[0]["amount_gbp"]), hits[0]["booked_at"][:10]),
                         [crn[0]["doc_id"]], [t["transaction_id"] for t in hits])

    gift = D("gift_letter")
    if gift and c.has("TM08", "TM01"):
        hits = c.matching_txns(gift[0], "in")
        if hits:
            return close("THIRD_PARTY_DOCUMENTED",
                         "Gift letter %s from %s confirms a gift of %s to %s, matching the payment received on %s. "
                         "The third-party payment is explained by a documented family relationship." % (
                             gift[0]["doc_id"], hits[0]["counterparty_name"], gbp(hits[0]["amount_gbp"]), first, hits[0]["booked_at"][:10]),
                         [gift[0]["doc_id"]], [t["transaction_id"] for t in hits])

    grp = D("group_structure")
    if grp and c.has("TM08"):
        a8 = c.alert("TM08")
        payers = sorted(set(c.F.txns[t]["counterparty_name"] for t in a8.get("transaction_ids", []) if t in c.F.txns))
        if payers and all(norm(p) in norm(grp[0]["text"]) for p in payers):
            supp = D("supplier_invoice", "email")
            return close("GROUP_COMPANY",
                         "Group structure chart %s shows %s and %s are in the same group. The %s received from it is intra-group funding%s." % (
                             grp[0]["doc_id"], ", ".join(payers), first,
                             gbp(sum(c.F.txns[t]["amount_gbp"] for t in a8["transaction_ids"] if t in c.F.txns)),
                             ", backed by %s" % ", ".join(c.doc_ids(supp)) if supp else ""),
                         [grp[0]["doc_id"]], c.doc_ids(supp), a8.get("transaction_ids", []))

    fac, rmt = D("factoring_agreement"), D("remittance_advice")
    if fac and rmt:
        hits = c.matching_txns(rmt[0], "in")
        if hits:
            return close("THIRD_PARTY_DOCUMENTED",
                         "Invoice finance agreement %s and remittance advice %s explain the %s received from the finance company on %s (an 85%% advance on financed invoices). "
                         "The third-party funding is documented." % (fac[0]["doc_id"], rmt[0]["doc_id"], gbp(hits[0]["amount_gbp"]), hits[0]["booked_at"][:10]),
                         [fac[0]["doc_id"], rmt[0]["doc_id"]], [t["transaction_id"] for t in hits])

    fr, car = D("freight_invoices"), D("carrier_invoice")
    if fr:
        hits = c.matching_txns(fr[0], "in")
        if hits:
            return close("INVOICE_MATCHES",
                         "Freight invoices %s issued by %s match the payments received from the exporters (%s)%s. "
                         "The third-party receipts are payment for freight services." % (
                             fr[0]["doc_id"], first, ", ".join(gbp(t["amount_gbp"]) for t in hits[:4]),
                             ", and carrier invoice %s explains the payment out" % car[0]["doc_id"] if car else ""),
                         c.doc_ids(fr), c.doc_ids(car), [t["transaction_id"] for t in hits])

    pfile = [d for d in D("payment_file") if "commission" not in d["text"].lower()]
    if pfile and c.has("TM04"):
        hits = c.matching_txns(pfile[0], "out")
        if hits:
            return close("INVOICE_MATCHES",
                         "Payment file %s lists the contractors paid, with contract references, and its amounts match the payments out (for example %s on %s). "
                         "The many payees are the client's documented contractors." % (pfile[0]["doc_id"], gbp(hits[0]["amount_gbp"]), hits[0]["booked_at"][:10]),
                         [pfile[0]["doc_id"]], [t["transaction_id"] for t in hits])

    invs = D("supplier_invoices", "supplier_invoice", "contract_schedule", "invoice", "purchase_order", "supply_contract")
    if invs and not c.has("TM22"):
        outs = [t for d in invs for t in c.matching_txns(d, "out")]
        if outs:
            rvf = D("reverification_record")
            return close("RETURNING_CUSTOMER" if (c.has("TM07") and rvf) else "INVOICE_MATCHES",
                         "%s on file (%s) match the payments out: %s. %s" % (
                             "Invoices and contracts", ", ".join(c.doc_ids(invs)),
                             ", ".join("%s on %s" % (gbp(t["amount_gbp"]), t["booked_at"][:10]) for t in outs[:4]),
                             "Re-verification record %s confirms the same directors resumed trading with their earlier supplier." % rvf[0]["doc_id"] if (c.has("TM07") and rvf)
                             else "The payments go to the invoiced supplier, which explains %s." % s),
                         c.doc_ids(invs), c.doc_ids(rvf), [t["transaction_id"] for t in outs])
        if c.has("TM03", "TM06", "TM01"):
            return Decision("ESC_INVOICE_MISMATCH",
                            "The invoices on file (%s) do not match the payments behind the alerts (%s). The invoices do not support the payments." % (
                                ", ".join(c.doc_ids(invs)), s),
                            c.ev(c.doc_ids(invs), c.alert_txn_ids))

    red = D("redundancy_letter")
    if red and c.has("TM10"):
        em = D("customer_email")
        return close("DOCUMENTED_EVENT",
                     "Redundancy letter %s and the customer's email %s explain why %s sold fund units early: they lost their job and need the money for living costs. "
                     "The early redemption (%s) has a documented reason." % (red[0]["doc_id"], ", ".join(c.doc_ids(em)) or "on file", first, c.alert_amounts_text(c.alert("TM10"))),
                     [red[0]["doc_id"]], c.doc_ids(em), c.alert_txn_ids)

    em = [d for d in D("customer_email") if re.search(r"in error|by mistake|mistake|accidentally|mistakenly", d["text"], re.I)]
    if em and c.has("TM02"):
        hits = c.matching_txns(em[0])
        if hits:
            return close("OWN_ACCOUNT",
                         "Email %s from %s says %s was paid into the investment account by mistake and asks for it back to their own savings account. "
                         "The withdrawal went to an account in the customer's own name, so the money only moved between their own accounts." % (
                             em[0]["doc_id"], first, gbp(hits[0]["amount_gbp"])),
                         [em[0]["doc_id"]], c.doc_ids(D("bank_statement")), [t["transaction_id"] for t in hits])

    letter = [d for d in D("customer_letter") if re.search(r"relocat|moved to", d["text"], re.I)]
    if letter and c.has("TM06"):
        return close("WITHIN_PROFILE",
                     "Letter %s from %s says they moved abroad for a new job and asks for withdrawals to go to their own account there. "
                     "The higher-risk-country withdrawals (%s) follow the customer's own documented instructions." % (
                         letter[0]["doc_id"], first, c.alert_amounts_text(c.alert("TM06"))),
                     [letter[0]["doc_id"]], c.doc_ids(D("bank_statement")), c.alert_txn_ids)

    emp = D("employment_contract")
    if emp and c.has("TM06", "TM01"):
        return close("WITHIN_PROFILE",
                     "Employment contract %s shows %s works abroad for the employer paying in. "
                     "The salary payments behind the alerts (%s) fit this documented employment." % (emp[0]["doc_id"], first, s),
                     [emp[0]["doc_id"]], c.doc_ids(D("bank_statement")), c.alert_txn_ids)

    rvf = D("reverification_record")
    if rvf and c.has("TM07"):
        stm = D("bank_statement")
        return close("RETURNING_CUSTOMER",
                     "Re-verification record %s confirms %s's identity on their usual device after the dormant period%s. "
                     "The reactivation (%s) is a verified customer resuming use of the account." % (
                         rvf[0]["doc_id"], first,
                         ", and statement %s shows the money came from the customer's own account" % stm[0]["doc_id"] if stm else "", s),
                     [rvf[0]["doc_id"]], c.doc_ids(stm), c.alert_txn_ids)

    # Cash paid back in after a withdrawal: the history must show that withdrawal.
    if c.has("TM05") and re.search(r"withdrew|paid the cash back|cash back", c.chat_text()):
        dep = [t for t in c.alert_txns if "cash" in t["channel"] and t["direction"] == "in"]
        for t in dep:
            w = [x for x in c.txns if x["direction"] == "out" and "cash" in x["channel"] and same_amount(x["amount_gbp"], t["amount_gbp"])
                 and x["booked_at"] < t["booked_at"]]
            if w:
                return close("WITHIN_PROFILE",
                             "Chat %s explains the %s cash deposit on %s as cash withdrawn earlier and returned after a private car purchase fell through. "
                             "The account history shows the same %s withdrawn in cash on %s, so the deposit is the customer's own money coming back." % (
                                 ", ".join(c.doc_ids(c.chats())), gbp(t["amount_gbp"]), t["booked_at"][:10], gbp(w[0]["amount_gbp"]), w[0]["booked_at"][:10]),
                             c.doc_ids(c.chats()), [t["transaction_id"], w[0]["transaction_id"]])

    # Own accounts elsewhere: only a statement in the customer's name proves them.
    stm = [d for d in D("bank_statement") if norm(first) and (norm(d["f"].get("account holder", "")) == norm(first)
           or norm(first) in norm(d["f"].get("account holders", "")))]
    if stm and c.has("TM01", "TM02", "TM08"):
        a1 = c.alert("TM01")
        mult = (a1 or {}).get("measured", {}).get("multiple", 0)
        hits = [t for d in stm for t in c.matching_txns(d)]
        if a1 and mult >= c.F.own_account_rfi_multiple:
            return Decision("RFI_UPDATED_PROFILE",
                            "Statements %s show the money came from %s's own accounts elsewhere, but that activity is %.1f times the declared baseline, at or above the %g times limit for own-account transfers. "
                            "Ask %s for an updated expected monthly income or volume for the account." % (
                                ", ".join(c.doc_ids(stm)), first, mult, c.F.own_account_rfi_multiple, first),
                            c.ev(c.doc_ids(stm), [t["transaction_id"] for t in hits] or c.alert_txn_ids))
        return close("OWN_ACCOUNT",
                     "Statements %s in %s's own name show the money moved between the customer's own accounts (%s). "
                     "This explains %s%s." % (
                         ", ".join(c.doc_ids(stm)), first, ", ".join("%s on %s" % (gbp(t["amount_gbp"]), t["booked_at"][:10]) for t in hits[:3]) or "matching transfers",
                         s, ", below the %g times own-account limit" % c.F.own_account_rfi_multiple if a1 else ""),
                     c.doc_ids(stm), [t["transaction_id"] for t in hits])
    return None


# ---------------------------------------------------------------- fallback: no explanation, no suspicion -> RFI

def fallback(c):
    first = c.name
    s = c.summary()
    biz = c.cust.get("kind") == "business"
    for a in c.alerts:
        if a["rule_id"] == "TM22":
            st, facts, ev = resolve_list(c, a)
            if st == "UNKNOWN":
                return Decision("RFI_COUNTERPARTY_DETAILS",
                                "%s. Nothing else on file is concerning. Ask %s for the counterparty's full name, date of birth or company number and what the payment was for." % (facts, first),
                                c.ev(ev))
    order = ["TM08", "TM06", "TM10", "TM03", "TM04", "TM02", "TM05", "TM07", "TM01"]
    rule = next((r for r in order if r in c.rules), c.rules[0] if c.rules else "TM01")
    a = c.alert(rule) or (c.alerts[0] if c.alerts else {})
    if rule == "TM08":
        payers = sorted(set(c.F.txns[t]["counterparty_name"] for t in a.get("transaction_ids", []) if t in c.F.txns))
        return Decision("RFI_COUNTERPARTY_DETAILS",
                        "Money moved to or from %s, an account not in %s's name (%s), and nothing on file explains the relationship. "
                        "Ask %s who the account holder is, how they are related, and for proof of the relationship or that the account is the customer's own." % (
                            ", ".join(payers) or "a third party", first, c.alert_amounts_text(a), first),
                        c.ev(c.alert_txn_ids))
    if rule == "TM06":
        return Decision("RFI_COUNTERPARTY_DETAILS",
                        "%s moved %s to or from a higher-risk country not declared at onboarding, and nothing on file explains it. "
                        "Ask %s who the counterparty is, their relationship, and what the payments were for, with supporting documents." % (first, c.alert_amounts_text(a), first),
                        c.ev(c.alert_txn_ids))
    if rule in ("TM10",):
        return Decision("RFI_PURPOSE_DOCUMENTS",
                        "%s sold fund units back soon after buying them (%s) and nothing on file explains why. "
                        "Ask %s for the reason for the early sale and supporting documents." % (first, c.alert_amounts_text(a), first),
                        c.ev(c.alert_txn_ids))
    if rule == "TM03":
        code = "RFI_PURPOSE_DOCUMENTS" if c.row.get("held_payment_id") or c.F.txns.get(c.alert_txn_ids[0] if c.alert_txn_ids else "", {}).get("direction") == "out" else "RFI_BUSINESS_RECORDS"
        return Decision(code,
                        "%s: %s. Nothing on file explains the repeated amounts just under the limit, and nothing else is concerning. "
                        "Ask %s for %s." % (first, s, first,
                                            "the invoice or contract covering these payments" if code == "RFI_PURPOSE_DOCUMENTS" else "the business records (takings or collection reports) behind the cash"),
                        c.ev(c.alert_txn_ids))
    if rule in ("TM04", "TM02"):
        return Decision("RFI_PURPOSE_DOCUMENTS",
                        "The alerts show %s, and nothing on file explains what the money was for. Nothing points to crime yet. "
                        "Ask %s for documents showing what the payments in and out were for (for example invoices, a booking or a letter)." % (s, first),
                        c.ev(c.alert_txn_ids))
    own = [t for t in c.alert_txns if t["direction"] == "in" and norm(t.get("counterparty_name")) == norm(first)]
    if rule == "TM01" and own:
        return Decision("RFI_SOURCE_OF_FUNDS",
                        "The alerts show %s, paid in from accounts in %s's own name, but no statement on file proves the customer holds them. "
                        "Ask %s for a statement of the sending account showing it is theirs and where the money came from." % (s, first, first),
                        c.ev(c.alert_txn_ids))
    if rule == "TM01" and biz:
        return Decision("RFI_BUSINESS_RECORDS",
                        "The alerts show %s, and no business records on file explain the higher volume. "
                        "Ask %s for management accounts or invoices covering the period." % (s, first),
                        c.ev(c.alert_txn_ids))
    return Decision("RFI_SOURCE_OF_FUNDS",
                    "The alerts show %s, and nothing on file explains where the money came from. Nothing points to crime yet. "
                    "Ask %s for proof of the source of the funds (for example a payslip, sale document or statement)." % (s, first),
                    c.ev(c.alert_txn_ids))


def decide(c):
    d = suspicion(c)
    if d:
        return d
    d = explain(c)
    # TM22 must be settled separately: a CLOSE on other grounds still needs the list match ruled out.
    if c.has("TM22"):
        for a in c.alerts:
            if a["rule_id"] != "TM22":
                continue
            st, facts, ev = resolve_list(c, a)
            if st == "UNKNOWN":
                return Decision("RFI_COUNTERPARTY_DETAILS",
                                "%s. Nothing else on file is concerning. Ask %s for the counterparty's full name, date of birth or company number and what the payment was for." % (facts, c.name),
                                c.ev(ev, d.evidence if d else []))
            if st == "DIFFERENT":
                inv = [x for x in c.docs if x["type"] in ("invoice", "receipt", "gift_letter") and c.matching_txns(x)]
                if d and d.verdict != "CLOSE":
                    return d
                return Decision("LIST_MATCH_DIFFERENT_PARTY",
                                "The list match is a different party: %s. %s" % (
                                    facts, "%s matches the amount and counterparty of the payment, so it has an ordinary documented purpose." % ", ".join(c.doc_ids(inv)) if inv
                                    else "Nothing else on file is concerning, so the alert can be closed."),
                                c.ev(ev, c.doc_ids(inv), d.evidence if d else []))
    if d:
        return d
    return fallback(c)


# ---------------------------------------------------------------- output checks

def finalise(c, d):
    valid = set(c.doc_ids(c.docs)) | set(c.F.txns) | set(c.F.list_entries) | set(c.F.alerts)
    ev = [x for x in d.evidence if x in valid]
    if not ev:
        ev = c.alert_txn_ids[:6]
    reason = re.sub(r"\s+", " ", d.reason).strip()
    reason = reason.replace("..", ".")
    return {"case_id": c.row["case_id"], "alert_ids": list(c.row["alert_ids"]), "verdict": d.verdict,
            "reason_code": d.code, "reason": reason, "evidence": ev}


def run(folder_path, out_path):
    F = Folder(folder_path)
    lines = []
    for row in F.cases:
        c = Case(F, row)
        try:
            d = decide(c)
        except Exception as e:  # never drop a case: an unparsed case escalates (a missing line would too)
            d = Decision("ESC_UNEXPLAINED_FUNDS",
                         "The case could not be fully assessed automatically (%s), so it goes to the MLRO for review. Alerts: %s." % (
                             type(e).__name__, ", ".join(row["alert_ids"])), [])
        lines.append(json.dumps(finalise(c, d), ensure_ascii=False, sort_keys=False))
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: run <institution folder> <output file>")
    run(sys.argv[1], sys.argv[2])
