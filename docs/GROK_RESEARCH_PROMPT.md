# Research prompt for Grok Bot (paste as-is)

You are researching how to improve **Trail**, a deterministic transaction-monitoring alert-triage engine built for the Grok Bot London Financial Crime Hackathon (Track 1, designed by Diligent).

Repo: https://github.com/Ibad-10/trail. Read these first:
- `HANDOVER.md`
- `system/README.md`
- `system/trail.py` (the whole engine, one file)
- `docs/SUBMISSION.md`
- `docs/FEATURES.md`

**What it does.** For each case it reads:
- alerts (rules TM01–TM08, TM10, TM22)
- the customer profile
- transactions
- Markdown evidence documents (invoices, statements, chats, staff notes, company registers, PSC registers, fraud reports, device exports)
- the internal list

It then outputs CLOSE, RFI or ESCALATE, with one of 26 reason codes, a 2–4 sentence reason and the evidence IDs it relied on.

**Scoring:**
- It is run five times on 800 unseen cases (same 4 institutions, same format and policies, new customers, possibly new wording).
- Cost per case: wrongful CLOSE = 10; RFI on an ESCALATE case = 3; ESCALATE on an RFI case = 2; not closing a closable case = 3.
- Reasons are scored on citing the deciding documents and naming case-specific facts.
- 20% of the score is reproducibility.

**Constraints:**
- Python standard library only.
- It reads only the institution folder.
- An LLM is allowed only via OpenRouter, and we use none today.

## Research questions (answer each with sources)
1. **Typologies we might miss.** Using 2025–2026 UK sources (UK Finance Annual Fraud Report 2026, FCA sanctions review May 2026, NCA, Cifas, Home Office/Ipsos money-muling reports July 2026, FATF, Europol, OFSI/OFAC advisories) plus news, Reddit (r/Scams, r/UKPersonalFinance, r/AMLCompliance) and X posts by fraud analysts: list the concrete **observable signals** in transactions and documents for each of these:
   - money-mule recruitment (job, student, "payment agent")
   - APP scams (romance, investment, purchase, impersonation)
   - invoice redirection / BEC
   - cuckoo smurfing
   - structuring
   - trade-based laundering
   - proxies, nominees and family members for listed people
   - control without majority ownership
   - account takeover
   - crypto off-ramps
   - gambling layering
   - refund and overpayment scams
   - dormant-account takeover

   For each signal, say whether it can be detected from the files described above, and which file and field.
2. **Rule gaps.** Compare those signals with what `system/trail.py` checks (functions `suspicion`, `explain`, `resolve_list`, `fallback`). List signals we don't check, ranked by how likely they are to appear in the unseen cases and how costly a miss is. Remember the asymmetry: a wrongful CLOSE costs 10.
3. **Wording robustness.** The unseen chats and notes may be worded differently. Give paraphrase lists, synonyms, negations and hedges for each free-text signal (mule script, structuring question, evasive director, "loan from a friend", "family support", "investing for others", mistaken transfer, cash returned after a failed purchase). Suggest stdlib-only matching techniques (normalisation, stemming, `difflib`).
4. **Engines others built.** Find open-source projects (GitHub), papers (arXiv, ACL, IEEE, SSRN) and hackathon winners for:
   - AML alert triage or disposition
   - SOP / policy-as-code decision engines (OPA/Rego, json-logic, durable rules)
   - rule + LLM cascades (e.g. Fed FEDS 2025-092)
   - counterfactual explanation of decisions (arXiv 2604.19755)

   For each, give the URL, what it does, and one idea we could copy.
5. **Reproducibility with an LLM.** If we add an OpenRouter fallback only for unmatched free text, what makes it repeatable across 5 runs? Cover temperature 0 limits, provider pinning, seeds, caching by prompt hash, and a constrained JSON enum. Cite sources and be clear about what is verified.
6. **Account-level history.** Which signals need a customer's whole transaction history (about 70% of transactions predate the review window)? Examples: earlier cash withdrawals matching later deposits, pass-through ratio over months, new payees in a burst, round-tripping between the same parties, repeated corridors. How would a deterministic engine compute them?

## Output format
- A ranked list of the 15 most valuable rule additions. For each:
  - signal
  - verdict and reason code
  - the exact files and fields it reads
  - a pseudo-check (5–10 lines)
  - false-positive risk
  - source URL
- A paraphrase table for question 3.
- The 10 best sources with URLs, each marked as primary / regulator, research, vendor marketing, or forum.
- Be explicit about what you verified versus what you inferred. Don't invent links.
