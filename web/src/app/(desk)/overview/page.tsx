"use client";
import Link from "next/link";
import { useMemo } from "react";
import { motion } from "motion/react";
import { ArrowRight } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useJson, type CaseSummary, INSTITUTIONS, VERDICT, type Verdict, codeText } from "@/lib/ct";

const VS: Verdict[] = ["CLOSE", "RFI", "ESCALATE"];

export default function Overview() {
  const { data } = useJson<CaseSummary[]>("/data/cases.json");
  const stats = useMemo(() => {
    if (!data) return null;
    return INSTITUTIONS.map((i) => {
      const rs = data.filter((c) => c.inst === i.id);
      const k = { CLOSE: 0, RFI: 0, ESCALATE: 0 } as Record<Verdict, number>;
      const codes: Record<string, number> = {};
      rs.forEach((c) => { k[c.verdict]++; codes[c.code] = (codes[c.code] ?? 0) + 1; });
      const top = Object.entries(codes).sort((a, b) => b[1] - a[1]).slice(0, 4);
      return { ...i, n: rs.length, k, top };
    });
  }, [data]);
  const total = data?.length ?? 0;
  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-serif text-3xl md:text-4xl">Overview</h1>
        <p className="mt-1 max-w-2xl text-muted-foreground">
          The development run: {total.toLocaleString()} cases across four institutions, each decided under its own policy.
          No AI model decides anything, so the same files always give the same answers.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        {VS.map((v) => {
          const n = data?.filter((c) => c.verdict === v).length ?? 0;
          return (
            <Link key={v} href={`/queue?v=${v}`}>
              <Card className="transition-colors hover:bg-muted/40">
                <CardHeader>
                  <CardDescription className="flex items-center gap-2"><span aria-hidden="true">{VERDICT[v].icon}</span>{VERDICT[v].long}</CardDescription>
                  <CardTitle className="font-serif text-4xl" style={{ color: VERDICT[v].dot }}>{data ? n.toLocaleString() : "…"}</CardTitle>
                </CardHeader>
              </Card>
            </Link>
          );
        })}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {!stats ? Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-48" />) : stats.map((s, idx) => (
          <motion.div key={s.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.06 }}>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">{s.name}<Link href={`/queue?inst=${s.id}`} className="inline-flex items-center gap-1 text-sm font-normal text-muted-foreground hover:text-foreground">Open queue <ArrowRight className="size-3.5" /></Link></CardTitle>
                <CardDescription>{s.n.toLocaleString()} cases</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex h-3 overflow-hidden rounded-full" role="img" aria-label={`${s.k.CLOSE} close, ${s.k.RFI} RFI, ${s.k.ESCALATE} escalate`}>
                  {VS.map((v) => <motion.span key={v} initial={{ width: 0 }} animate={{ width: `${(s.k[v] / s.n) * 100}%` }} transition={{ duration: 0.7 }} style={{ background: VERDICT[v].dot }} />)}
                </div>
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
                  {VS.map((v) => <span key={v}><span aria-hidden="true">{VERDICT[v].icon}</span> {s.k[v]} {VERDICT[v].word.toLowerCase()}</span>)}
                </div>
                <ul className="space-y-1 text-sm text-muted-foreground">
                  {s.top.map(([c, n]) => <li key={c} className="flex justify-between"><span>{codeText(c)}</span><span className="tabular-nums">{n}</span></li>)}
                </ul>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
