import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2 } from "lucide-react";

// Measured on the 4,000 development cases on Sat 21 Nov 2026 (see README for the commands).
const CHECKS = [
  { t: "Same answer every run", m: "5 runs → 1 hash", d: "system/repro.sh runs the engine five times per institution. Every run gives byte-identical output, so the verdict and reason code never change." },
  { t: "No memorising", m: "0 of 4,000 changed", d: "tests/perturb_test.py renumbers every case, customer, document, transaction and list ID and shuffles every file. No verdict or reason code changes." },
  { t: "Every CLOSE rests on its evidence", m: "2,000 of 2,000", d: "tests/counterfactual_test.py deletes the documents each CLOSE cited and runs again. Every one of them stops being a CLOSE (they become RFIs)." },
  { t: "Valid output", m: "0 errors", d: "system/validate.py checks one line per case, codes that belong to the verdict, cited IDs that exist in the case files, and 2 to 4 sentence reasons." },
  { t: "Cost and speed", m: "$0 · seconds", d: "Standard-library Python with no network and no model. 1,000 cases take about 20 seconds on a laptop." },
  { t: "Balanced as designed", m: "500 / 250 / 250", d: "Each institution splits into exactly 500 close, 250 RFI and 250 escalate. This appeared once the rules followed the policies. It suggests the data was built 50/25/25; it isn't proof that each case is right." },
];

export default function Assurance() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-serif text-3xl md:text-4xl">Assurance</h1>
        <p className="mt-1 max-w-2xl text-muted-foreground">What an independent tester would ask first, and what we measured. Deterministic rules fall outside the &quot;model&quot; definition in the US interagency guidance SR 26-2.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {CHECKS.map((c) => (
          <Card key={c.t}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base"><CheckCircle2 className="size-4 text-hot" aria-hidden="true" />{c.t}</CardTitle>
              <CardDescription className="leading-relaxed">{c.d}</CardDescription>
            </CardHeader>
            <CardContent><Badge variant="secondary" className="font-mono">{c.m}</Badge></CardContent>
          </Card>
        ))}
      </div>
      <Card>
        <CardHeader><CardTitle className="text-base">What we can&apos;t claim</CardTitle></CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>The development cases have no answers, so we can&apos;t report accuracy. The organisers score the unseen cases.</p>
          <p>The engine reads fields and amounts, not sentences. Free text worded in a way it has never seen falls to RFI or ESCALATE, never to CLOSE.</p>
        </CardContent>
      </Card>
    </div>
  );
}
