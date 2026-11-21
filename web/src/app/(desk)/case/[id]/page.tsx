"use client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { ArrowLeft, FileText } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from "@/components/ui/breadcrumb";
import { useJson, type CaseFull, type GNode, instName, RULES, codeText, VERDICT } from "@/lib/ct";
import { VerdictBadge } from "@/components/ct/VerdictBadge";
import { TrailGraph } from "@/components/ct/TrailGraph";

export default function CasePage() {
  const { id } = useParams<{ id: string }>();
  const { data: c, error } = useJson<CaseFull>(`/data/case/${id}.json`);
  const [src, setSrc] = useState<GNode | null>(null);
  if (error) return <p className="text-muted-foreground">Case {id} was not found. Build the data with <code>python viewer/build.py</code>.</p>;
  if (!c) return <div className="space-y-4"><Skeleton className="h-8 w-64" /><Skeleton className="h-28 w-full" /><Skeleton className="h-80 w-full" /></div>;
  const label = (nid: string) => { const n = c.nodes.find((x) => x.id === nid); return n ? (n.kind === "verdict" ? `${c.verdict} ${c.code}` : n.label) : nid; };
  const docs = c.nodes.filter((n) => n.kind === "doc");
  const open = (nid: string) => { const n = c.nodes.find((x) => x.id === nid); if (n) setSrc(n); };
  return (
    <div className="space-y-6">
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem><BreadcrumbLink render={<Link href="/queue" />}>Alert queue</BreadcrumbLink></BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem><BreadcrumbLink render={<Link href={`/queue?inst=${c.inst}`} />}>{instName(c.inst)}</BreadcrumbLink></BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem><BreadcrumbPage>{c.case_id}</BreadcrumbPage></BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="font-serif text-3xl leading-tight md:text-4xl">{c.customer}</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {c.kind === "business" ? "Business" : "Individual"} · {instName(c.inst)}
            {c.window && <> · review window {c.window.from} to {c.window.to}</>}
            {c.held && <> · held payment {c.held}</>}
          </p>
        </div>
        <Link href="/queue" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"><ArrowLeft className="size-4" />Back to queue</Link>
      </div>

      <Card className={c.verdict === "CLOSE" ? "bg-close-bg/40" : c.verdict === "RFI" ? "bg-rfi-bg/40" : "bg-esc-bg/40"}>
        <CardHeader>
          <div className="flex flex-wrap items-center gap-2">
            <VerdictBadge v={c.verdict} long />
            <Badge variant="outline">{c.code}</Badge>
            {c.rules.map((r) => <Badge key={r} variant="secondary">{r} · {RULES[r] ?? r}</Badge>)}
          </div>
          <CardTitle className="pt-2 text-base font-semibold">{codeText(c.code)}</CardTitle>
          <CardDescription className="text-base leading-relaxed text-foreground">{c.reason}</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="mb-2 text-xs font-semibold tracking-wider text-muted-foreground uppercase">Evidence relied on</p>
          <div className="flex flex-wrap gap-1.5">
            {c.evidence.map((e) => (
              <button key={e} onClick={() => open(e)} className="rounded-md border bg-muted/50 px-2 py-0.5 font-mono text-xs hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring">{e}</button>
            ))}
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="trail">
        <TabsList>
          <TabsTrigger value="trail">Evidence trail</TabsTrigger>
          <TabsTrigger value="docs">Documents ({docs.length})</TabsTrigger>
          <TabsTrigger value="path">Text path</TabsTrigger>
        </TabsList>
        <TabsContent value="trail" className="pt-3">
          <TrailGraph c={c} selected={src?.id ?? null} onSelect={setSrc} />
        </TabsContent>
        <TabsContent value="docs" className="grid gap-3 pt-3 md:grid-cols-2">
          {docs.map((d) => (
            <Card key={d.id} className={d.hot ? "ring-2 ring-hot/60" : ""}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-sm"><FileText className="size-4" aria-hidden="true" />{d.id} · <span className="capitalize">{d.label}</span>{d.hot && <Badge className="ml-auto bg-hot text-white">Cited</Badge>}</CardTitle>
                <CardDescription>{d.sub}</CardDescription>
              </CardHeader>
              <CardContent><button onClick={() => setSrc(d)} className="text-sm font-medium underline underline-offset-4">Read document</button></CardContent>
            </Card>
          ))}
        </TabsContent>
        <TabsContent value="path" className="pt-3">
          <Card><CardContent className="pt-6">
            <ol className="list-decimal space-y-1.5 pl-5 text-sm">
              {c.edges.map((e, i) => (
                <li key={i}><b>{label(e[0])}</b> <span className="text-muted-foreground">{e[2]}</span> → <b>{label(e[1])}</b> <span className="text-xs text-muted-foreground">(source {e[3]})</span></li>
              ))}
            </ol>
          </CardContent></Card>
        </TabsContent>
      </Tabs>

      <Sheet open={!!src} onOpenChange={(o) => !o && setSrc(null)}>
        <SheetContent className="w-full overflow-y-auto sm:max-w-xl">
          <SheetHeader>
            <SheetTitle>{src?.src?.id ?? src?.id}</SheetTitle>
            <SheetDescription>{src?.label}{src?.hot ? " · cited as evidence" : ""}</SheetDescription>
          </SheetHeader>
          <pre className="mx-4 mb-6 rounded-lg bg-muted p-4 font-mono text-[12.5px] leading-relaxed whitespace-pre-wrap">{src?.src?.text ?? "No source text."}</pre>
        </SheetContent>
      </Sheet>
    </div>
  );
}
