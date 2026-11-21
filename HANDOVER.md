# Trail: handover (for Cursor, Mistral Vibe, Claude or a teammate)

Written Sat 21 Nov 2026 at about 14:35 London for the **Grok Bot London Financial Crime Hackathon, Track 1** ("Build a system that closes alerts safely", designed by Diligent).

**Code freeze is 17:00 London. Push by 16:30.** The organisers score the latest commit before the deadline.

Read sections 1, 2 and 5 before you change anything.

---

## 1. Where everything is
| What | Where |
|---|---|
| Repo (public) | https://github.com/Ibad-10/trail (local: `D:\Projects\controltrail`) |
| Live web app | https://trail-rose-one.vercel.app (Vercel project `trail`, team "Ibad's projects") |
| Track 1 dataset (local only, never commit) | `D:\Projects\Grok Bot finical hackathon\data\track1\x\hackathon\` → `institutions\{bank,emoney,investment,payments_fx}`, `README.md`, `BRIEF.html` |
| Submission rules and checklist | `docs/SUBMISSION.md` |
| Idea, business case, approaches | `docs/PLAN.md` |
| Full ranked feature list | `docs/FEATURES.md` |
| How the engine decides, measured numbers | `system/README.md` |
| Earlier research (competitors, papers, judges) | `D:\Projects\Grok Bot finical hackathon\New idea\CLAUDE.md` (private links inside; never commit it) |
| Submission portal | https://gb-fincrime-hackathon-11-2026.teamdeel.workers.dev/submit |

Set `D` to the dataset path (bash):
```bash
D="/d/Projects/Grok Bot finical hackathon/data/track1/x/hackathon/institutions"
```

## 2. Hard rules (break one and the submission fails)
- `system/run <institution folder> <output file>`:
  - It is run from inside `system/` with full paths.
  - It reads only that folder and writes only the output file (plus files inside `system/`).
  - Python 3 / Node standard library or shell only. No pip or npm packages at run time.
- A model only via OpenRouter (`OPENROUTER_API_KEY`). **We use no model**, so keep it that way unless you add a cache and a fallback (see 6.3).
- **No dev-case memorisation**: never put case IDs, names, amounts, document IDs or verdicts from the dev data into code. `tests/perturb_test.py` must keep showing 0 changes.
- `output/*.jsonl` must come from `system/run`. Re-run all four before the final commit.
- One line per case. `reason_code` must belong to the verdict. Reasons are 2–4 sentences. Every evidence ID must exist. Run `system/validate.py`.
- Never commit:
  - the dataset, `.env*` or keys
  - `viewer/data.js` or `web/public/data/` (all git-ignored)
  - Google Drive or Doc links
- Commit as `Ibad Ullah Zuberi <99681549+Ibad-10@users.noreply.github.com>`, with **no AI or Co-authored-by trailers**.
- `system/run` must keep LF endings and its executable bit (`.gitattributes` handles the endings; check with `git ls-files -s system/run` → `100755`).

## 3. What is done and verified
| Item | Status | Proof |
|---|---|---|
| Engine `system/trail.py` + `system/run` for all 4 institutions | ✅ | `validate.py`: 0 errors ×4 |
| Same answer every run | ✅ | `system/repro.sh`: 5/5 identical hashes for all 4 |
| No memorisation | ✅ | `tests/perturb_test.py`: 0 of 4,000 change after renumbering every ID and shuffling every file |
| Each CLOSE rests on its evidence | ✅ | `tests/counterfactual_test.py`: 2,000 of 2,000 CLOSEs stop being CLOSE without their cited documents |
| Runs as the organisers will (from inside `system/`, full paths, 200 cases) | ✅ | 4 s, 200 lines, data folder untouched |
| Verdict mix | ✅ | 500 CLOSE / 250 RFI / 250 ESCALATE in every institution (suggests a designed 50/25/25 split; not proof of per-case accuracy) |
| Blind gold sample (60 cases, independent labeller) | ✅ | 60/60 verdicts, 0 wrongful closes, 31/31 closable closed, codes 58/60 (`labels/blind_gold.csv`, git-ignored) |
| Wording robustness | 🟡 | Broader phrase patterns for mule, structuring, third-party, loan and family stories; dev output byte-identical. A paraphrase test suite is still to do (6.2) |
| `system/README.md`, repo README, docs | ✅ | |
| Web app (Next.js 16, shadcn base-nova, Magic UI, motion): landing, overview, queue, case trail, policies, assurance; Ctrl+K search; dark mode; phone layout | ✅ | Deployed; checked at desktop and phone widths |
| Single-file viewer `viewer/index.html` | ✅ | `python viewer/build.py "$D" output`, then serve `viewer/` |
| Public GitHub repo | ✅ | https://github.com/Ibad-10/trail |
| Vercel deploy | ✅ | https://trail-rose-one.vercel.app |
| 2-minute video | ⬜ | Ibad records with Clockbot (script in section 7) |
| Submission form | ⬜ | Ibad fills it in (section 8) |

**Reviewed so far:**
- Self-review through the tests above.
- A browser check of each page.
- A research pass (Fed FEDS 2025-092 cascade, arXiv 2604.19755 counterfactual triage, LLM non-determinism papers, vendor claims).

No independent code review has been run yet (6.6).

## 4. How the engine works (short)
`system/trail.py` is one file. Per case:
1. **Suspicion → ESCALATE**, checked in this order (any one escalates):
   - listed person in control on the payment date
   - fraud report
   - mule chat
   - third parties investing through the account
   - structuring note
   - shared device
   - "loan from a friend" or a dissolved payer
   - conflicting stories
   - "family support" to a higher-risk country with no document
   - evasive director
   - pass-through to new companies
   - unrelated third-party funding
2. **Explanation → CLOSE** only when a document's £ amount matches a transaction behind the alerts. Typed handlers cover:
   - sale, estate, insurance, settlement, completion, ISA, deposit return, loan plus dealer
   - booking, business records, hospital invoice, venue refund, credit note
   - gift letter, group structure, factoring, freight, contractor file, invoices
   - redundancy, mistaken transfer, relocation, employment, re-verification
   - cash returned
   - own-account statements, with the ≥5× rule → `RFI_UPDATED_PROFILE`
3. **TM22** is settled separately in `resolve_list()`:
   - officer or PSC dates at the payment date
   - the counterparty's own register for address matches
   - a date of birth in a document
4. **Fallback → RFI**, with the code chosen by the open rule (`fallback()`).
5. `finalise()` keeps only evidence IDs that exist and normalises whitespace. A crash in one case escalates that case instead of dropping it.

Main functions: `Folder`, `Case`, `resolve_list`, `suspicion`, `explain`, `fallback`, `decide`, `finalise`, `run`.

## 5. Commands
```bash
# all four, validate
for i in bank emoney investment payments_fx; do system/run "$D/$i" output/$i.jsonl; python system/validate.py "$D/$i" output/$i.jsonl; done
system/repro.sh "$D/bank"                                   # expect: "5 <hash>"
python tests/perturb_test.py "$D/bank"                       # expect: 0 changed
python tests/counterfactual_test.py "$D/bank" output/bank.jsonl   # expect: still CLOSE: 0
python viewer/build.py "$D" output                           # rebuilds viewer/data.js and web/public/data
cd web && npm install && npm run dev                         # http://localhost:3000
cd web && vercel deploy --prod --yes                         # redeploy; web/.vercelignore makes sure public/data is uploaded
```
**After any engine change:**
1. Re-run all four and validate.
2. Re-run repro, perturb and counterfactual.
3. Rebuild the data, redeploy, and commit the outputs.

**If the verdict mix moves away from 500/250/250, treat that as a warning sign and explain why before committing.**

## 6. Next steps, in priority order
1. **Final run and push before 16:30** (section 5). Then stop touching `system/`.
2. **Gold sample (the only accuracy measure available)**. The dev data has no answers, and public AML datasets (SAML-D, IBM, PaySim) label transactions, not alert outcomes, so they can't score this engine.
   - `python tests/make_label_sheet.py "$D"` writes `labels/to_label.csv`: 237 cases, 2 per group of similar cases. The file is git-ignored.
   - A person (not the engine's author) labels `verdict` from the case page and `POLICY.md`.
   - Then run `python tests/score.py labels/to_label.csv output/*.jsonl`. It prints the cost per case, wrongful closes and the share of closable cases closed, using the official cost table.
3. **Paraphrase test** (`tests/paraphrase_test.py`). Rewrite chat and staff-note sentences with synonyms, for example "send it on" → "forward the money", and check the same signals fire. This is the main risk on unseen cases, which may word free text differently.
4. **Optional LLM fallback (cascade)**, only for free text that no pattern matched:
   - Call OpenRouter at temperature 0 with a JSON enum reply (`MULE_SCRIPT`, `STRUCTURING_QUESTION`, `CONTRADICTION`, `EVASIVE`, `BENIGN`, `NOISE`).
   - Cache by SHA-256 of the prompt in `system/cache/`.
   - If there's no key or the call fails, behave exactly as today.
   - It may only push a case towards RFI or ESCALATE, never towards CLOSE.
   - Source idea: Fed FEDS 2025-092 cascade.
   - Risky this close to the deadline. Only do it if 6.3 shows real misses.
5. **Audit trace**: write `system/trace/<case>.json` (allowed, since it's inside `system/`) with the rule path, matched spans and evidence. It helps the "replay any decision" pitch. Keep it deterministic.
6. **Reason polish**:
   - Lead with the deciding document.
   - Keep 2–4 sentences.
   - Use UK date style ("15 September 2026") instead of ISO in reasons. Check the validator still passes.
7. **Independent review** of `system/trail.py` against `docs/SUBMISSION.md` (use a fresh reviewer, e.g. `/code-review`).
8. Web extras from `docs/FEATURES.md`:
   - money-flow Sankey (3.6)
   - relationship map (3.5)
   - "Why not CLOSE?" (7.1)
   - policy playground (7.4)

   Never let the web app change `system/` behaviour.

## 7. Demo video script (2 minutes, Clockbot)
1. **0:00–0:15**: Landing page, with the workflow animation. "Most alerts are explained, but every one needs a person. Closing the wrong one costs ten times more than asking."
2. **0:15–0:40**: The Problem and Gap sections. "Agents decide but can't replay. Graphs show but don't decide. Trail compiles the firm's own policy and cites a source for every link."
3. **0:40–1:10**: Alert queue. Open `BK-CS125943`: ESCALATE, because a listed person owned 60% of the payee on the payment day. Click the PSC box to show the register.
4. **1:10–1:30**: Ctrl+K → `BK-CS100551`: CLOSE, because sale receipt SAL-9402 matches the £13,000 cash deposit. Then an RFI that names exactly what to ask for.
5. **1:30–1:50**: The Assurance page, then the terminal: `system/repro.sh` shows 5 identical hashes, and `perturb_test` shows 0 changed.
6. **1:50–2:00**: "Same input, same answer, every link has a source. Trail."

## 8. Submission form (Ibad)
| Field | Value |
|---|---|
| Project name | Trail |
| Track | Track 1 (transaction monitoring) |
| Repo | https://github.com/Ibad-10/trail |
| Live demo | https://trail-rose-one.vercel.app |
| Video | (Clockbot link) |
| Team | Ibad Ullah Zuberi, his Cursor email, LinkedIn `linkedin.com/in/ibad-ullah-zuberi` |

"What did you build?" (under 1,200 characters):

> Trail is a deterministic alert-triage engine for transaction monitoring. For every case it reads the alerts, customer, transactions and documents on file, and applies the institution's own POLICY.md. It escalates on any sign of crime (fraud reports, mule scripts, structuring questions, a listed person controlling the payee on the payment date). It closes only when a document matches the money to the penny. Otherwise it sends an RFI that says exactly what to ask for. Every reason names the case's own people, amounts and document IDs. There is no model in the decision path: standard-library Python, $0, seconds per 1,000 cases. Five runs give identical bytes; renaming every ID and shuffling every file changes 0 of 4,000 verdicts; and removing each CLOSE's cited documents turns all 2,000 CLOSEs into RFIs. A web desk (queue, case evidence trail, policies, assurance) shows every decision with its sources.

## 9. Open questions for the organisers (15:00 office hours)
- Is the reason code scored as an exact match, or are several acceptable?
- Is the 50/25/25 split by design?
- For TM22 name-only matches, is an RFI right, or should it escalate?

## 10. Notes for another agent (Cursor, Mistral Vibe)
- Work in `D:\Projects\controltrail`. Never edit the dataset folder.
- Keep `system/` dependency-free and deterministic. Run section 5's checks after any change.
- The web app needs `web/public/data` (built by `viewer/build.py`) before `npm run dev` shows anything.
- Next.js 16 note: read `web/AGENTS.md`. shadcn here is the `base-nova` style on `@base-ui/react`, so components use `render={...}` instead of `asChild`, and a Link inside a Button needs `nativeButton={false}`.
