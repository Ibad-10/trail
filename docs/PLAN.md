# ControlTrail: design and build plan (Sat 21 Nov 2026)

## The idea in one paragraph
ControlTrail is a deterministic alert-triage engine for transaction monitoring. For each case it gathers the evidence on file (transactions, documents, company registers, the internal list), checks it against the institution's own `POLICY.md`, and decides one of three things:
- **ESCALATE** when anything is suspicious.
- **CLOSE** only when every alert is explained by a document that matches the money.
- **RFI** naming the one thing to ask the customer, when nothing is suspicious but something is unexplained.

Every reason names the case's own people, amounts and document IDs. The same input always gives the same bytes. Tagline: *rules gather evidence, the firm's policy decides, every link has a source.*

## Who it's for and the business case
- **Users:** L1/L2 transaction-monitoring analysts and team leads at UK banks, e-money firms, payments/FX firms and investment platforms. Also MLROs, who receive escalations with the full path, and QA / independent-testing teams, who replay any decision.
- **Pain:** most alerts have an ordinary explanation, and every one still needs a person. A review takes 20–60 minutes across 5–6 systems (figure from Zomma's YC page).
- **Buyer:** Head of Financial Crime Operations. Pilot = run on last month's case export, compare with analyst outcomes, no integration needed.
- **Pricing idea:** per alert reviewed, or per seat. Assumption, not measured: a firm with 10,000 alerts a month closing half automatically saves several analyst FTEs.
- **Why us vs agents (Unit21, Axle, Zomma, Bretton):** they decide with LLM judgement, which can vary between runs. We are the deterministic, policy-compiled layer with a source on every link. We could also sit under their agents as the "evidence and rules" step.

## Approaches considered
1. **AI model reads each case and decides.** Rejected: runs disagree (20% of the score is reproducibility), it costs money, and it risks wrongful closes.
2. **Rules only, from the policy and the documents.** Chosen. Deterministic, free, fast and auditable. Risk: new wording in unseen cases. Mitigation: match on fields and amounts; anything unrecognised falls to RFI or ESCALATE, never CLOSE.
3. **Rules with an optional cached model for free text.** Kept for later (feature 1.18), off by default.

## What we measured (dev set, 4,000 cases)
- Every institution comes out at **500 CLOSE / 250 RFI / 250 ESCALATE**. This appeared once the rules followed the policies. It strongly suggests the dataset was built 50/25/25 and the engine sorts it as designed. It is not proof that each case is right.
- 0 validator errors. 5 runs give identical SHA-256 hashes. About 20 seconds per 1,000 cases on a laptop, $0, no network.

## How the engine decides
1. Load the 8 files and parse every evidence Markdown file (bold fields, tables, £ amounts, dates).
2. **Suspicion first**, in this order:
   - listed party controls the counterparty at the payment date
   - sending-bank fraud reports
   - mule chat script
   - third parties investing through the account
   - structuring questions
   - device used by several customers
   - "loan from a friend" from a company (dissolved)
   - conflicting stories
   - "family support" to a higher-risk country with no documents
   - evasive director
   - pass-through to new companies
   - unrelated third-party funding
3. **Explanations**: the document's amount must match a transaction behind the alert.
   - Documented events: sale, estate, insurance, settlement, property sale, ISA cancellation, deposit return, loan plus dealer invoice.
   - Collections, business records, invoices and contracts, refunds, gift letters, group structure, invoice finance, freight invoices, contractor payment files.
   - Own accounts proven by statements.
   - Re-verification of returning customers, relocation letters, employment contracts.
4. **TM22** must be settled separately. The person must have left before the payment, or a different date of birth or company must be shown, before a CLOSE.
5. Otherwise **RFI**, with a code and the exact ask chosen by the rule that's still open.
6. Validate and write one line per case in input order.

## Build plan for the rest of today
| # | Task | Done when |
|---|---|---|
| 1 | Engine, validator, repro script, outputs for all 4 | ✅ committed |
| 2 | Rename-and-shuffle test and counterfactual test (`tests/`) | Both pass and are in the README |
| 3 | `system/README.md`: how it decides, measured numbers, three worked cases | Written with real IDs from the output |
| 4 | Evidence graph export per case (`viewer/build.py` writes JSON from the output and the data folder, outside `system/`) | JSON for all cases |
| 5 | Case viewer (`viewer/index.html`, static, canary column layout, queue + case + graph + text path) | Opens locally, keyboard works |
| 6 | Repo README and pitch notes | Done |
| 7 | Push to public GitHub (Ibad approves), final run, submit | Pushed before 16:30 |

Dev data is never committed. The viewer's data file is git-ignored and is built locally from the dataset.
