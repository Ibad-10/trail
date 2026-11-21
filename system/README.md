# Trail: how the system decides

```
system/run <institution folder> <output file>
```

`run` is a bash wrapper around `trail.py`, which uses only the Python 3 standard library. It reads only the institution folder it is given and writes only the output file. It doesn't depend on the working directory.

**No language model is used.** Verdicts, reason codes, reasons and evidence come from rules and templates, so there is no API key, no network call and no cost. `OPENROUTER_API_KEY` is not read.

## The decision, in policy order

For every case in `cases.jsonl`:

1. **Suspicion first → ESCALATE.** Any one of these escalates, and the customer is never sent an RFI, because asking would risk tipping them off.

   | Signal | Code |
   |---|---|
   | TM22: the internal-list person is an officer or person with significant control (PSC) of the counterparty **on the payment date**, read from the register or PSC table's appointed/notified and resigned/ceased dates. Or a document gives the same date of birth as the list entry | `ESC_LISTED_PARTY` |
   | A sending bank's APP-scam fraud report on the account | `ESC_MULE_ACTIVITY` |
   | A support chat describing a "job" receiving clients' money and sending it on for a cut | `ESC_MULE_ACTIVITY` |
   | The customer says they invest or hold money for other people | `ESC_THIRD_PARTY_FUNDING`, or `ESC_EARLY_REDEMPTION` when fund units were sold back early |
   | A staff note records the customer asking whether splitting amounts or staying under a limit avoids reporting or invoice checks | `ESC_STRUCTURING` |
   | A device export shows one device logging in to several customers' accounts | `ESC_ACCOUNT_MISUSE` |
   | "A loan from a friend" that came from a company, or a payer the register shows as dissolved | `ESC_UNEXPLAINED_FUNDS` |
   | Two or more chats giving different stories for the same money | `ESC_UNEXPLAINED_FUNDS` |
   | Undeclared higher-risk-country flows explained only as "family support", with no document | `ESC_HIGH_RISK_CORRIDOR` |
   | A director who can't or won't explain the counterparty or destination | `ESC_HIGH_RISK_CORRIDOR` / `ESC_INVOICE_MISMATCH` |
   | Activity far above a small contract, moved on to newly formed companies run by the same person | `ESC_PASS_THROUGH` |
   | Unrelated third parties fund the client and the money passes straight through | `ESC_THIRD_PARTY_FUNDING` |

2. **Explanations → CLOSE**, but only when a document on file matches the money. The amount must equal a transaction behind the alerts to the penny, and payee and date are checked where the document gives them. A document type alone never closes a case. A document whose amount doesn't match gives an RFI, or `ESC_INVOICE_MISMATCH` for invoices.
   - **Documented events** → `DOCUMENTED_EVENT`: sale receipts, estate letters, insurance settlements, settlement agreements, property completion statements, ISA cancellations, deposit returns, loan agreement plus dealer invoice, redundancy letter plus sale request.
   - **Business and payment records:**
     - Group bookings → `COLLECTION_DOCUMENTED`.
     - Takings, collection and reconciliation records → `BUSINESS_RECORDS_RECONCILE`.
     - Invoices, contracts, payment schedules, freight invoices, contractor payment files → `INVOICE_MATCHES`.
     - Venue refunds and supplier credit notes → `REFUND_OF_EARLIER_PAYMENT`.
   - **Third parties and other accounts:**
     - Gift letters, invoice-finance agreements with remittance advice → `THIRD_PARTY_DOCUMENTED`.
     - Group structure charts → `GROUP_COMPANY`.
     - Statements in the customer's own name, joint holders included → `OWN_ACCOUNT`.
   - **Customer circumstances:**
     - Re-verification after dormancy → `RETURNING_CUSTOMER`.
     - Relocation letters and employment contracts → `WITHIN_PROFILE`.
     - Cash paid back in, matched to an earlier cash withdrawal of the same amount → `WITHIN_PROFILE`.
   - **Own-account limit** (read from POLICY.md): own-account transfers at 5× the declared baseline or more → `RFI_UPDATED_PROFILE`, not CLOSE.
   - **TM22** must be settled on its own before any CLOSE. The listed person must have resigned or ceased before the payment, or a register must name other officers for an address match, or a document must give a different date of birth. That gives `LIST_MATCH_DIFFERENT_PARTY`.
3. **Otherwise → RFI.** The code and the request come from the rule still open:
   - Third party or corridor → `RFI_COUNTERPARTY_DETAILS`.
   - Rapid movement or many payers → `RFI_PURPOSE_DOCUMENTS`.
   - Cash or profile → `RFI_SOURCE_OF_FUNDS` / `RFI_BUSINESS_RECORDS`.
   - TM22 name-only match → `RFI_COUNTERPARTY_DETAILS`.

   The reason says exactly what to ask for.
4. **Write** one line per case in `cases.jsonl` order:
   - The evidence lists documents first, then list entries, then transactions, and only IDs that exist in the folder.
   - A case that throws an error is escalated with a stated reason rather than dropped.

The policy profile (higher-risk countries, own-account multiple) is parsed from each `POLICY.md` at run time, with the published values as a fallback.

## Measured on the 4,000 development cases (Sat 21 Nov 2026)

| Check | Command | Result |
|---|---|---|
| Valid output | `python system/validate.py <folder> <out>` | 0 errors in all 4 institutions |
| Same answer every run | `system/repro.sh <folder>` | 5 of 5 identical SHA-256 per institution (bank `dedad27c…`, emoney `14d3aaf6…`, investment `36179391…`, payments_fx `1a2f0f40…`) |
| No memorising | `python tests/perturb_test.py <folder>` | Renumber every ID and shuffle every record file: **0 of 4,000** verdicts or codes change |
| CLOSE rests on its evidence | `python tests/counterfactual_test.py <folder> <out>` | Delete each CLOSE's cited documents: **2,000 of 2,000** stop being CLOSE |
| Verdict mix | | Each institution: 500 CLOSE, 250 RFI, 250 ESCALATE |
| **Blind gold sample** | `python tests/score.py <labels> output/*.jsonl` | An independent labeller (a fresh session that never saw this code) labelled 60 cases, 15 per institution, from the brief and POLICY.md only. **60/60 verdicts agree, 0 wrongful closes, 31/31 closable cases closed** (no extra work for analysts), cost per case 0.00 vs 2.12 for escalating everything. Reason codes agree on 58/60 |
| Time and cost | | About 20–26 s per 1,000 cases on a Windows laptop, so a run of 200 cases takes well under a minute. **$0**: no model, no network |

The development cases have no answers, so we can't report accuracy. The identical 50/25/25 split in all four institutions appeared once the rules followed the policies. It suggests the dataset was built that way, but it isn't proof that each case is right.

## Three worked cases (from `output/`)

**CLOSE · `DOCUMENTED_EVENT`.** `BK-CS100551`: TM01 and TM05 fire on a £13,000.00 cash deposit. Vehicle sale receipt `SAL-9402` is for exactly £13,000.00, for a car the customer insured (`INS-5321`). Evidence: `INS-5321`, `SAL-9402`, `BK-T390363804`.

**RFI · `RFI_COUNTERPARTY_DETAILS`.** `PX-CS228948`: TM22 matched list entry `PX-L89987` on name only, and nothing on file settles it. The reason asks the client for the counterparty's full name, date of birth or company number and the payment's purpose. It never mentions the list.

**ESCALATE · `ESC_MULE_ACTIVITY`.** `EM-CS102434`: two sending banks report APP-scam payments into the account (`RPT-548`, `RPT-6939`), alongside TM01, TM02 and TM04. A support chat (`CHT-437`) describes a "payments assistant" job.

## Known limits
- The engine reads fields, tables and amounts, not meaning. Free text worded in a way it has never seen can be missed. The fallback is RFI or ESCALATE, which cost 3 or 2, never a CLOSE, which costs 10.
- Reason codes follow a fixed priority when several apply. The scoring may accept others.
