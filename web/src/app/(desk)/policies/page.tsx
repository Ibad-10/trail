"use client";
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useJson, type Policy, INSTITUTIONS } from "@/lib/ct";

const STEPS = [
  { t: "1 · Look for suspicion", d: "Fraud reports, mule chat scripts, structuring questions, shared devices, a listed person in control on the payment date, conflicting stories. Any one of them escalates, and the customer is never asked (no tipping off)." },
  { t: "2 · Check every alert is explained", d: "A document on file must match the money: the amount to the penny, and the counterparty and date. A document type alone never closes a case." },
  { t: "3 · Otherwise ask for one thing", d: "If nothing is suspicious but something is unexplained, send an RFI that says exactly what to ask for." },
];

export default function Policies() {
  const { data } = useJson<Record<string, Policy>>("/data/policies.json");
  const [tab, setTab] = useState("bank");
  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-serif text-3xl md:text-4xl">Policies</h1>
        <p className="mt-1 max-w-2xl text-muted-foreground">Each institution&apos;s own SOP is the rulebook. ControlTrail reads the limits and country list from each POLICY.md and applies the same three steps.</p>
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        {STEPS.map((s) => (
          <Card key={s.t}><CardHeader><CardTitle className="text-base">{s.t}</CardTitle><CardDescription className="leading-relaxed">{s.d}</CardDescription></CardHeader></Card>
        ))}
      </div>
      {!data ? <Skeleton className="h-96" /> : (
        <Tabs value={tab} onValueChange={(v) => setTab(String(v))}>
          <TabsList className="flex h-auto w-full flex-wrap justify-start">
            {INSTITUTIONS.map((i) => <TabsTrigger key={i.id} value={i.id}>{i.name}</TabsTrigger>)}
          </TabsList>
          {INSTITUTIONS.map((i) => {
            const p = data[i.id];
            return (
              <TabsContent key={i.id} value={i.id} className="space-y-4 pt-4">
                <Card>
                  <CardHeader><CardTitle>{p.title}</CardTitle><CardDescription>{p.intro}</CardDescription></CardHeader>
                  <CardContent className="space-y-3 text-sm">
                    <p><b>Own-account limit:</b> own-account transfers at {p.own_account_multiple}× the declared income or volume or more get an RFI for an updated profile; below that, they close only with a statement in the customer&apos;s name.</p>
                    <div><b>Higher-risk countries:</b> <span className="mt-1 flex flex-wrap gap-1">{p.high_risk.map((c) => <Badge key={c} variant="secondary">{c}</Badge>)}</span></div>
                  </CardContent>
                </Card>
                <div className="overflow-hidden rounded-xl border">
                  <Table>
                    <TableHeader><TableRow><TableHead className="w-20">Rule</TableHead><TableHead className="w-56">Name</TableHead><TableHead>Fires when</TableHead></TableRow></TableHeader>
                    <TableBody>
                      {p.rules.map((r) => (
                        <TableRow key={r.id}><TableCell className="font-mono text-xs">{r.id}</TableCell><TableCell className="font-medium">{r.name}</TableCell><TableCell className="text-sm whitespace-normal text-muted-foreground">{r.fires}</TableCell></TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </TabsContent>
            );
          })}
        </Tabs>
      )}
    </div>
  );
}
