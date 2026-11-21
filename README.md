# Trail

**Rules gather the evidence. The firm's policy decides. Every link has a source.**

Trail is a deterministic alert-triage engine for transaction monitoring. It was built solo at the Grok Bot London Financial Crime Hackathon (Sat 21 Nov 2026), Track 1, "Build a system that closes alerts safely", designed by Diligent.

For each case it reads the alerts, the customer, their transactions and every document on file, then follows the institution's own `POLICY.md`:
- **ESCALATE** when anything is suspicious. The customer is never asked, so there is no tipping off.
- **CLOSE** only when every alert is explained by a document that matches the money.
- **RFI** naming the one thing to ask for, when nothing is suspicious but something is unexplained.

Every reason names the case's own people, amounts and document IDs, and the same input always gives the same bytes.

## Run it

```bash
system/run institutions/bank output/bank.jsonl         # one institution
python system/validate.py institutions/bank output/bank.jsonl
system/repro.sh institutions/bank                       # 5 runs, prints the hashes
python tests/perturb_test.py institutions/bank          # rename every ID + shuffle: verdicts must not change
python tests/counterfactual_test.py institutions/bank output/bank.jsonl
```

Python 3 standard library only. No model, no network, $0. How it decides and the measured numbers are in [`system/README.md`](system/README.md).

| | Result on the 4,000 development cases |
|---|---|
| Validator | 0 errors |
| Repeatability | 5 of 5 identical hashes, every institution |
| Rename every ID and shuffle every file | 0 verdicts change |
| Delete each CLOSE's cited documents | 2,000 of 2,000 stop being CLOSE |
| Verdict mix | 500 CLOSE / 250 RFI / 250 ESCALATE per institution |

## The case desk (web app)

`web/` is a Next.js app built with shadcn/ui, Magic UI and motion:
- landing page
- overview
- searchable alert queue (works on phones)
- case page with the evidence trail: what fired → money moved → who is involved → documents → decision. Every box opens its source, with a text-path alternative.
- policies
- assurance

It reads case data built locally from the dataset, which is not committed:

```bash
python viewer/build.py <path to institutions> output    # writes web/public/data (git-ignored)
cd web && npm install && npm run dev
```

`viewer/index.html` is a single-file version of the same trail view.

## Docs
- [`docs/PLAN.md`](docs/PLAN.md): idea, business case, approaches, build plan.
- [`docs/FEATURES.md`](docs/FEATURES.md): the full feature list, ranked Must / Should / Nice / Wow / Later.

All data in the hackathon set is synthetic. Every customer, company and document is invented.
