# ControlTrail feature list

Brainstormed on Sat 21 Nov 2026 during the Grok Bot London Financial Crime Hackathon (Track 1). Time limits are ignored on purpose: this is the long list for the product, not today's to-do list. Today's build order is in `docs/PLAN.md`.

**Tiers**
- **Must**: the product is not credible without it.
- **Should**: strong value, build next.
- **Nice**: useful, lower priority.
- **Wow**: the demo moment or the thing a buyer remembers.
- **Later**: needs data, partners or regulation work we don't have yet.

**Status**
- ✅ built today
- 🟡 partly built
- ⬜ not built

The scored engine (`system/run`) must stay deterministic and read only the institution folder. Anything that needs outside data or a model sits outside `system/` and never changes a scored verdict.

---

## 1. Decision engine (the scored core)

| # | Feature | Tier | Status | Why it matters |
|---|---|---|---|---|
| 1.1 | `system/run <folder> <out>`: one JSON line per case with verdict, reason code, reason and evidence IDs | Must | ✅ | The contract the organisers score |
| 1.2 | Three-step decision: any suspicion → ESCALATE; else every alert explained → CLOSE; else RFI naming what to ask | Must | ✅ | Mirrors the SOP. A wrongful close costs 10, so CLOSE needs proof |
| 1.3 | Document matching on amount (to the penny), counterparty and date before any CLOSE | Must | ✅ | A document type alone never closes a case |
| 1.4 | TM22 list resolution: officer and PSC dates checked at the payment date; date of birth on a document vs the list; register officers for address matches | Must | ✅ | The biggest wrongful-close and wrongful-escalate risk |
| 1.5 | Own-account rule: only a statement in the customer's name (joint holders included) proves another account; at 5× or more → RFI for an updated profile | Must | ✅ | Policy trap: an account "in your name elsewhere" isn't proof on its own |
| 1.6 | Suspicion signals: fraud reports, mule chat scripts, structuring questions in staff notes, shared devices, dissolved payers, conflicting stories, evasive directors, pass-through to new companies, unrelated third-party funding | Must | ✅ | Once there is suspicion, escalate; never send an RFI (tipping off) |
| 1.7 | Policy profile parsed from each `POLICY.md` (higher-risk country list, own-account multiple) with safe fallbacks | Must | 🟡 | The unseen policy might change a limit. Next: parse every rule limit |
| 1.8 | Deterministic output: no clock, no randomness, sorted evidence, input order kept | Must | ✅ | 20% of the score is reproducibility |
| 1.9 | Crash guard: a case that can't be parsed escalates with a stated reason rather than going missing | Must | ✅ | A missing line counts as ESCALATE anyway; this makes it explicit |
| 1.10 | Validator: every case once, code belongs to verdict, every cited ID exists, 2–4 sentences | Must | ✅ | Catches mistakes before submission |
| 1.11 | 5-run repeat check (`repro.sh`) | Must | ✅ | Proof of identical bytes |
| 1.12 | Rename-and-shuffle test: new IDs, names and line order must give the same verdicts | Must | ⬜ | Proves no memorisation of the dev cases |
| 1.13 | Counterfactual test: remove the deciding document and the verdict must stop being CLOSE (from arXiv 2604.19755) | Should | ⬜ | Shows each CLOSE rests on evidence |
| 1.14 | Per-alert findings (explained / unexplained / suspicious) shown alongside the case verdict | Should | ⬜ | Analysts see which alert held the case open |
| 1.15 | Severity order for reason codes, documented (listed party > mule > structuring > …) | Should | 🟡 | Consistent code choice when several apply |
| 1.16 | Confidence band per decision (how many independent facts back it) | Nice | ⬜ | Routes thin CLOSEs to QA |
| 1.17 | Rule coverage report: which cases fell to the fallback RFI and why | Should | ⬜ | Shows where the engine is guessing |
| 1.18 | Optional model labeller for free text it has never seen (OpenRouter, temperature 0, cached by prompt hash), off by default, rules win on conflict | Later | ⬜ | Handles new chat wording without breaking repeatability |
| 1.19 | Prompt-injection guard: document text is data only and never reaches a decision as an instruction | Must | ✅ | There is no model in the path, so there's nothing to inject into |

## 2. Policies and rules

| # | Feature | Tier | Status | Why |
|---|---|---|---|---|
| 2.1 | Policy compiler: `POLICY.md` → versioned JSON profile (limits, countries, which rules run), hash stamped into every decision | Should | 🟡 | "Codify your procedures, run as code" (Diligent's own pitch) |
| 2.2 | Policy diff run: change a limit and see which past decisions flip before it goes live | Wow | ⬜ | Compliance can test a policy change in seconds |
| 2.3 | Four-policy comparison: run every case under all four SOPs to find where they disagree | Nice | ⬜ | Finds gaps and contradictions between firms' policies |
| 2.4 | Jurisdiction packs (UK OFSI >50% ownership or control, US OFAC 50% aggregated, EU 50% plus control), reviewed JSON files | Later | ⬜ | Explains a listed-party escalation in the regulator's own terms |
| 2.5 | Policy editor UI: paste a policy, review the compiled rules, save a new version | Later | ⬜ | Self-serve for compliance teams |
| 2.6 | Rule simulation on history: how many alerts a new threshold would raise or close | Nice | ⬜ | Tuning without guesswork |
| 2.7 | Context-only signals kept separate (round amounts, shared IP, same-day payee, crypto, gambling): shown, never decisive | Must | ✅ | The policy says these never raise an alert alone |

## 3. Knowledge graph: people, money, places

| # | Feature | Tier | Status | Why |
|---|---|---|---|---|
| 3.1 | Per-case evidence graph: customer → accounts → transactions → counterparties → companies → officers/PSCs → list entries → documents; every edge carries a source ID | Must | ⬜ | The audit trail behind each verdict |
| 3.2 | Column layout (canary pattern): What fired → Money moved → Who is involved → Documents → Verdict; hover lights the path, click opens the source text | Wow | ⬜ | Readable in 3 seconds; no hairball |
| 3.3 | Hard and soft edges: hard edges (register, statement, transaction) can decide; soft ones (same name, same address, masked IBAN) only add context or push CLOSE to RFI | Must | 🟡 | Stops "same last four digits" false links |
| 3.4 | Control at a date: officer and PSC edges carry from/to dates; the graph answers "who controlled the payee on the payment day?" | Must | ✅ (engine) | The core TM22 question |
| 3.5 | Relationship map for a person: family (gift letters "my child", "my relative"), joint accounts, co-directors, shared devices, shared addresses | Should | ⬜ | Proxies and nominees are how listed people hide |
| 3.6 | Money-flow view: Sankey of where money came from and went in the window, by counterparty and country | Wow | ⬜ | Mule and pass-through patterns become obvious |
| 3.7 | Multi-account view: every account a customer holds or is shown to hold (statements), with flows between them | Should | ⬜ | Own-account explanations made visible |
| 3.8 | Country layer: map of corridors with the higher-risk list highlighted | Nice | ⬜ | TM06 at a glance |
| 3.9 | Hop limit and caps (max nodes, "+N more"), like canary | Must | ⬜ | Keeps it readable |
| 3.10 | Cross-case links within one institution on hard identifiers only (same full account number, device ID or company number) | Nice | ⬜ | Finds mule rings; never links on masked IBANs |
| 3.11 | Text path for screen readers ("Payment £2,400 → Stanford Consulting Ltd → director Robin Ferndale until 4 Aug → list entry …") | Must | ⬜ | Accessibility and clear explanation |
| 3.12 | Timeline view: alerts, transactions, documents, register changes on one time axis | Should | ⬜ | Shows "director resigned the day before the payment" |
| 3.13 | Graph export (JSON / GraphML) for Quantexa- or Neo4j-style tools | Later | ⬜ | Fits existing investigation tools |

## 4. Analyst interface

| # | Feature | Tier | Status | Why |
|---|---|---|---|---|
| 4.1 | Queue view: all cases with verdict (colour + icon + word), code, amount, filters by institution, rule and verdict | Must | ⬜ | Where an L1 analyst starts |
| 4.2 | Case view: reason, evidence list (click to read the document), graph, alerts | Must | ⬜ | One screen, one decision |
| 4.3 | Run dashboard: verdict mix per institution, close rate, run time, 5-run hash | Should | ⬜ | Speaks to judges and team leads |
| 4.4 | RFI drafter: the reason becomes a customer message that never mentions the alert or any list (no tipping off) | Should | ⬜ | Saves the analyst a step, safely |
| 4.5 | Escalation pack for the MLRO: reason, path, all source documents in one printable page | Should | ⬜ | Hand-off ready |
| 4.6 | Analyst override with a required reason; overrides are logged and re-tested against the policy | Nice | ⬜ | Human stays in charge |
| 4.7 | QA sampler: random 10% of CLOSEs plus 100% of TM22 CLOSEs for a second look | Should | ⬜ | Standard bank practice for auto-closures |
| 4.8 | Keyboard-first navigation (j/k, Enter, Esc) | Nice | ⬜ | Analysts live in queues |
| 4.9 | Read-aloud reason and large-text toggle | Nice | ⬜ | Accessibility |
| 4.10 | Offline mode: everything runs from local files | Must | ✅ | No wifi risk; no data leaves the bank |

## 5. Bank integration

| # | Feature | Tier | Status | Why |
|---|---|---|---|---|
| 5.1 | Batch CLI over the case export the TM system already produces (the 8 files) | Must | ✅ | Zero integration work for a pilot |
| 5.2 | Write-back adapter: verdict + reason + evidence as a case note in the case manager (Actimize, Unit21, Hummingbird, Salesforce) | Should | ⬜ | No new screen for L1 |
| 5.3 | REST API: POST a case bundle, get the decision and graph | Should | ⬜ | Real-time use for held payments (payments/FX) |
| 5.4 | Held-payment release flow: CLOSE releases, RFI keeps it held with the message drafted, ESCALATE freezes | Should | ⬜ | Payments firms measure release time |
| 5.5 | Webhook on new evidence: re-decide when a document arrives (an RFI answered) | Nice | ⬜ | Closes the RFI loop automatically |
| 5.6 | Decision log: append-only, hash-chained, with policy version and engine version | Should | ⬜ | Replay for auditors and testers |
| 5.7 | Data stays in the bank: runs on-prem, standard library only, no outbound calls | Must | ✅ | Procurement and data-protection friendly |
| 5.8 | SAR/STR draft for the MLRO from an escalation (NCA format fields) | Later | ⬜ | The next step after escalation |

## 6. Assurance and testing (for model-risk and independent testing teams)

| # | Feature | Tier | Status | Why |
|---|---|---|---|---|
| 6.1 | Reproducibility certificate: 5-run hashes per institution in the README | Must | ✅ | Judges and testers ask first |
| 6.2 | Mutation tests: change one fact (an amount, a date, a resignation date) and check the verdict flips as the policy says | Should | ⬜ | Proves rules react to the right facts |
| 6.3 | Hand-labelled sample with agreement and wrongful-close counts | Should | ⬜ | Honest accuracy number without official labels |
| 6.4 | Template coverage report: groups of similar cases and the decision each got | Should | 🟡 | Showed the 500/250/250 split |
| 6.5 | Scenario generator: build new synthetic cases from rules for regression tests | Later | ⬜ | Tests beyond the dev set |
| 6.6 | Lookback: re-check past CLOSE reviews against later evidence (e.g. a later fraud report) | Nice | ⬜ | Axle sells this; useful feature, not the pitch |
| 6.7 | Model-risk note: deterministic rules fall outside the "model" definition in SR 26-2; any optional model is listed separately | Should | ⬜ | Answers the UBS-style question |

## 7. Wow ideas (future, ambitious)

| # | Feature | Tier | Why |
|---|---|---|---|
| 7.1 | "Why not CLOSE?" button: shows the single missing fact that would have closed it, and the single fact that would escalate it | Wow | Every decision becomes a checklist |
| 7.2 | Live Companies House + OpenSanctions check for a real UK company: same graph, same TM22 logic, clearly badged "live public data" | Wow | Real-world proof outside the synthetic data |
| 7.3 | Mule-ring radar: accounts in one institution connected by hard links, ranked by pass-through ratio and fraud reports | Wow | Moves from one case to the network |
| 7.4 | Policy playground: drag a slider (e.g. own-account multiple 5× → 4×) and watch the queue re-sort live | Wow | Makes "policy as code" tangible |
| 7.5 | Explain to the customer: a plain-English RFI letter, checked for tipping-off words | Nice | Customer experience |
| 7.6 | Regulator replay pack: zip of inputs, policy version, engine version and outputs that re-runs to the same hashes | Wow | What an independent tester wants |
| 7.7 | Agent sidecar: an LLM agent (e.g. via Banyan or a Grok Bot skill) proposes, and ControlTrail's rules accept or reject with reasons | Later | Combines agent flexibility with deterministic control |
| 7.8 | Peer benchmark: anonymised close rates by rule across firms (needs a data-sharing agreement) | Later | Industry view |

## 8. Accessibility (applies to every screen)
- Verdict always shown as colour + icon + word: CLOSE ✓ (blue), RFI ? (amber), ESCALATE ⚠ (purple). Colour-blind safe, never red/green alone.
- WCAG AA contrast, visible focus, full keyboard use, `prefers-reduced-motion` respected.
- Every graph has a text path alternative; every box is focusable and opens its source.
- Plain-English reasons; jargon has a tooltip.

## 9. What we deliberately won't do
- Let a model decide a verdict or reason code in the scored engine (repeatability, auditability).
- Link people or accounts on masked IBANs or names alone.
- Relabel the internal list as a sanctions list (it holds earlier investigations, exited customers and blocked banks).
- Send anything outside the institution folder during a scored run.
