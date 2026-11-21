"use client";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useJson, type CaseSummary, INSTITUTIONS, instName, RULES } from "@/lib/ct";
import { VerdictBadge } from "@/components/ct/VerdictBadge";

const PAGE = 25;

export default function QueuePage() {
  const sp = useSearchParams();
  const router = useRouter();
  const inst = sp.get("inst") ?? "all";
  const verdict = sp.get("v") ?? "all";
  const rule = sp.get("rule") ?? "all";
  const [q, setQ] = useState("");
  const [page, setPage] = useState(0);
  const { data } = useJson<CaseSummary[]>("/data/cases.json");
  const set = (k: string, v: string) => {
    const p = new URLSearchParams(sp.toString());
    if (v === "all") p.delete(k); else p.set(k, v);
    setPage(0);
    router.replace(`/queue?${p.toString()}`);
  };
  const rows = useMemo(() => {
    if (!data) return [];
    const s = q.trim().toLowerCase();
    return data.filter((c) => (inst === "all" || c.inst === inst) && (verdict === "all" || c.verdict === verdict) &&
      (rule === "all" || c.rules.includes(rule)) && (!s || (c.case_id + " " + c.customer + " " + c.code + " " + c.reason).toLowerCase().includes(s)));
  }, [data, inst, verdict, rule, q]);
  const pages = Math.max(1, Math.ceil(rows.length / PAGE));
  const view = rows.slice(page * PAGE, page * PAGE + PAGE);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-serif text-3xl md:text-4xl">Alert queue</h1>
        <p className="mt-1 text-muted-foreground">Every case with its decision and the reason behind it. Open one to see the evidence trail.</p>
      </div>

      <Tabs value={inst} onValueChange={(v) => set("inst", String(v))}>
        <TabsList className="flex h-auto w-full flex-wrap justify-start">
          <TabsTrigger value="all">All</TabsTrigger>
          {INSTITUTIONS.map((i) => <TabsTrigger key={i.id} value={i.id}>{i.name}</TabsTrigger>)}
        </TabsList>
      </Tabs>

      <div className="flex flex-col gap-2 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
          <Input value={q} onChange={(e) => { setQ(e.target.value); setPage(0); }} placeholder="Search customer, case ID, reason…" className="pl-9" aria-label="Search the queue" />
        </div>
        <Select value={verdict} onValueChange={(v) => set("v", String(v))}>
          <SelectTrigger className="sm:w-44" aria-label="Filter by decision"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All decisions</SelectItem>
            <SelectItem value="CLOSE">✓ Close</SelectItem>
            <SelectItem value="RFI">? Ask customer</SelectItem>
            <SelectItem value="ESCALATE">⚠ Escalate</SelectItem>
          </SelectContent>
        </Select>
        <Select value={rule} onValueChange={(v) => set("rule", String(v))}>
          <SelectTrigger className="sm:w-56" aria-label="Filter by rule"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All rules</SelectItem>
            {Object.entries(RULES).map(([k, v]) => <SelectItem key={k} value={k}>{k} · {v}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      {!data ? (
        <div className="space-y-2">{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}</div>
      ) : (
        <>
          <p className="text-sm text-muted-foreground">{rows.length.toLocaleString()} cases</p>
          {/* Desktop table */}
          <div className="hidden overflow-hidden rounded-xl border md:block">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-36">Decision</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>Rules</TableHead>
                  <TableHead>Reason code</TableHead>
                  <TableHead className="w-40">Institution</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {view.map((c) => (
                  <TableRow key={c.case_id} className="cursor-pointer" onClick={() => router.push(`/case/${c.case_id}`)}>
                    <TableCell><VerdictBadge v={c.verdict} /></TableCell>
                    <TableCell>
                      <Link href={`/case/${c.case_id}`} className="font-medium hover:underline" onClick={(e) => e.stopPropagation()}>{c.customer}</Link>
                      <div className="font-mono text-xs text-muted-foreground">{c.case_id}</div>
                    </TableCell>
                    <TableCell className="text-xs">{c.rules.join(" ")}</TableCell>
                    <TableCell className="font-mono text-xs">{c.code}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{instName(c.inst)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          {/* Phone cards */}
          <div className="space-y-2 md:hidden">
            {view.map((c) => (
              <Link key={c.case_id} href={`/case/${c.case_id}`} className="block rounded-xl border bg-card p-3 active:bg-muted">
                <div className="flex items-center justify-between gap-2"><span className="font-medium">{c.customer}</span><VerdictBadge v={c.verdict} /></div>
                <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{c.reason}</p>
                <p className="mt-1 font-mono text-[11px] text-muted-foreground">{c.case_id} · {c.rules.join(" ")}</p>
              </Link>
            ))}
          </div>
          <div className="flex items-center justify-between">
            <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>Previous</Button>
            <span className="text-sm text-muted-foreground">Page {page + 1} of {pages}</span>
            <Button variant="outline" size="sm" disabled={page + 1 >= pages} onClick={() => setPage((p) => p + 1)}>Next</Button>
          </div>
        </>
      )}
    </div>
  );
}
