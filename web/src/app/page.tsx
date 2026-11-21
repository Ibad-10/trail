import Link from "next/link";
import { ArrowRight, Bot, Network, ScrollText, UserCheck, Gavel, FlaskConical, Banknote, Fingerprint, Repeat2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DotPattern } from "@/components/ui/dot-pattern";
import { AnimatedShinyText } from "@/components/ui/animated-shiny-text";
import { NumberTicker } from "@/components/ui/number-ticker";
import { BorderBeam } from "@/components/ui/border-beam";
import { Marquee } from "@/components/ui/marquee";
import { BentoCard, BentoGrid } from "@/components/ui/bento-grid";
import { Logo } from "@/components/ct/Logo";
import { WorkflowBeams } from "@/components/ct/WorkflowBeams";
import { cn } from "@/lib/utils";

const REASONS = [
  { v: "Close", c: "var(--close)", t: "Sale receipt SAL-9402 matches the £13,000.00 cash deposit on 11 Aug." },
  { v: "Escalate", c: "var(--esc)", t: "Two banks report APP-scam payments into the account, then out within 48 hours." },
  { v: "Ask", c: "var(--rfi)", t: "Ask for the invoice behind four payments of just under £10,000 to one supplier." },
  { v: "Close", c: "var(--close)", t: "The listed director resigned on 14 Sep, the day before the £1,800.00 payment." },
  { v: "Escalate", c: "var(--esc)", t: "A listed person still owned 60% of the payee when the payment was made." },
  { v: "Ask", c: "var(--rfi)", t: "Ask for a statement proving the sending account is the customer's own." },
];

const GAP = [
  { Icon: Bot, t: "AI agents", who: "Unit21, Axle, Zomma, Bretton", d: "Read the case and decide with a language model. Fast, but runs can disagree and the reason is hard to replay." },
  { Icon: Network, t: "Graph tools", who: "Quantexa, Linkurious, Sayari", d: "Show who is connected to whom. A person still has to read it and decide." },
  { Icon: ScrollText, t: "Trail", who: "Policy as code", d: "Compiles the firm's own SOP into checks, decides, and cites a source for every link. Same input, same answer.", us: true },
];

const USERS = [
  { Icon: UserCheck, name: "L1 and L2 analysts", description: "Half the queue arrives closed with a reason naming the documents. The rest arrives with the one thing to ask, or the path to escalate.", href: "/queue", cta: "Open the queue", className: "col-span-3 lg:col-span-2" },
  { Icon: Gavel, name: "MLROs", description: "Escalations come with the trail: who controlled the payee on the payment day, which bank reported the scam.", href: "/queue?v=ESCALATE", cta: "See escalations", className: "col-span-3 lg:col-span-1" },
  { Icon: Banknote, name: "Payments and FX firms", description: "Held payments over £10,000 are released only when an invoice or contract on file matches.", href: "/queue?inst=payments_fx", cta: "Payments queue", className: "col-span-3 lg:col-span-1" },
  { Icon: FlaskConical, name: "QA and independent testers", description: "Replay any decision. Five runs give identical bytes; renaming every ID changes nothing.", href: "/assurance", cta: "See the tests", className: "col-span-3 lg:col-span-2" },
];

export default function Home() {
  return (
    <div className="relative flex min-h-screen flex-col overflow-x-hidden">
      <header className="sticky top-0 z-30 border-b bg-background/75 backdrop-blur">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-3 md:px-8">
          <Logo />
          <nav className="flex items-center gap-1 text-sm" aria-label="Main">
            <Button variant="ghost" size="sm" className="hidden sm:inline-flex" nativeButton={false} render={<Link href="#how" />}>How it works</Button>
            <Button variant="ghost" size="sm" className="hidden sm:inline-flex" nativeButton={false} render={<Link href="/policies" />}>Policies</Button>
            <Button size="sm" nativeButton={false} render={<Link href="/overview" />}>Open the desk</Button>
          </nav>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero */}
        <section className="relative">
          <DotPattern className={cn("text-foreground/15 [mask-image:radial-gradient(600px_circle_at_center,white,transparent)]")} />
          <div className="relative mx-auto grid max-w-6xl items-center gap-10 px-4 pt-16 pb-20 md:grid-cols-2 md:px-8 md:pt-24">
            <div>
              <div className="inline-flex rounded-full border bg-card/70 px-3 py-1 text-xs backdrop-blur">
                <AnimatedShinyText>Transaction-monitoring alert triage · Track 1</AnimatedShinyText>
              </div>
              <h1 className="mt-5 font-serif text-4xl leading-[1.08] md:text-6xl">
                Close what the evidence explains. <em className="text-muted-foreground">Escalate the rest with the path.</em>
              </h1>
              <p className="mt-5 max-w-lg text-base text-muted-foreground md:text-lg">
                Trail reads every alert the way a careful analyst would, under the firm&apos;s own policy, and cites a source for every claim.
              </p>
              <div className="mt-7 flex flex-wrap gap-3">
                <Button size="lg" nativeButton={false} render={<Link href="/queue" />}>Open the alert queue <ArrowRight className="size-4" /></Button>
                <Button size="lg" variant="outline" nativeButton={false} render={<Link href="#how" />}>How it works</Button>
              </div>
            </div>
            <WorkflowBeams />
          </div>
        </section>

        {/* Problem */}
        <section className="border-y bg-muted/40">
          <div className="mx-auto grid max-w-6xl gap-8 px-4 py-14 md:grid-cols-3 md:px-8">
            <div className="md:col-span-1">
              <p className="text-xs font-semibold tracking-widest text-muted-foreground uppercase">The problem</p>
              <h2 className="mt-2 font-serif text-3xl">Every alert needs a person. Most were never suspicious.</h2>
            </div>
            <div className="grid gap-4 sm:grid-cols-3 md:col-span-2">
              <Stat n={90} suffix="%+" l="of monitoring alerts turn out to be false positives (industry figure quoted by McKinsey)" />
              <Stat n={60} prefix="20–" suffix=" min" l="per alert review, across five or six systems (Zomma, YC)" />
              <Stat n={10} suffix="×" l="the cost of a wrongful close compared with asking the customer, in this track's scoring" />
            </div>
          </div>
        </section>

        {/* Gap */}
        <section className="mx-auto max-w-6xl px-4 py-16 md:px-8">
          <p className="text-xs font-semibold tracking-widest text-muted-foreground uppercase">The gap</p>
          <h2 className="mt-2 max-w-2xl font-serif text-3xl">Agents decide but can&apos;t replay. Graphs show but don&apos;t decide.</h2>
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {GAP.map(({ Icon, t, who, d, us }) => (
              <Card key={t} className={cn("relative overflow-hidden", us && "border-foreground/30")}>
                <CardHeader>
                  <Icon className="size-6" aria-hidden="true" />
                  <CardTitle className="pt-2">{t}</CardTitle>
                  <p className="text-xs text-muted-foreground">{who}</p>
                  <CardDescription className="pt-1 leading-relaxed">{d}</CardDescription>
                </CardHeader>
                {us && <BorderBeam size={120} duration={8} colorFrom="var(--close)" colorTo="var(--esc)" />}
              </Card>
            ))}
          </div>
        </section>

        {/* How */}
        <section id="how" className="border-y bg-muted/40">
          <div className="mx-auto max-w-6xl px-4 py-16 md:px-8">
            <p className="text-xs font-semibold tracking-widest text-muted-foreground uppercase">How it works</p>
            <h2 className="mt-2 font-serif text-3xl">Three checks, in the order the policy sets.</h2>
            <ol className="mt-8 grid gap-4 md:grid-cols-3">
              {[
                { n: "1", c: "var(--esc)", t: "Suspicion first", d: "Fraud reports, mule scripts, structuring questions, shared devices, a listed person in control on the payment day. Any one escalates, and the customer is never tipped off." },
                { n: "2", c: "var(--close)", t: "Proof for every alert", d: "A document must match the money to the penny, plus the payee and date. A document type alone never closes a case." },
                { n: "3", c: "var(--rfi)", t: "Ask for one thing", d: "Nothing suspicious but something unexplained: an RFI that says exactly what to ask the customer for." },
              ].map((s) => (
                <li key={s.n} className="rounded-xl border bg-card p-5">
                  <span className="flex size-8 items-center justify-center rounded-full text-sm font-bold text-white" style={{ background: s.c }}>{s.n}</span>
                  <h3 className="mt-3 font-semibold">{s.t}</h3>
                  <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{s.d}</p>
                </li>
              ))}
            </ol>
            <div className="relative mt-10 overflow-hidden">
              <Marquee pauseOnHover className="[--duration:40s]">
                {REASONS.map((r, i) => (
                  <div key={i} className="w-80 rounded-xl border bg-card p-4 text-sm">
                    <span className="text-xs font-bold" style={{ color: r.c }}>{r.v}</span>
                    <p className="mt-1 text-muted-foreground">{r.t}</p>
                  </div>
                ))}
              </Marquee>
              <div className="pointer-events-none absolute inset-y-0 left-0 w-16 bg-gradient-to-r from-muted/80" />
              <div className="pointer-events-none absolute inset-y-0 right-0 w-16 bg-gradient-to-l from-muted/80" />
            </div>
          </div>
        </section>

        {/* Who */}
        <section className="mx-auto max-w-6xl px-4 py-16 md:px-8">
          <p className="text-xs font-semibold tracking-widest text-muted-foreground uppercase">Who it&apos;s for</p>
          <h2 className="mt-2 font-serif text-3xl">Fits the queue a firm already runs.</h2>
          <p className="mt-2 max-w-2xl text-muted-foreground">It reads the case export the monitoring system already produces and writes back a decision, a reason and the evidence IDs. No new data leaves the bank.</p>
          <BentoGrid className="mt-8 auto-rows-[13rem]">
            {USERS.map((u) => <BentoCard key={u.name} {...u} background={<DotPattern className="text-foreground/10 [mask-image:linear-gradient(to_bottom,white,transparent)]" />} />)}
          </BentoGrid>
        </section>

        {/* Proof */}
        <section className="border-t">
          <div className="mx-auto grid max-w-6xl gap-6 px-4 py-14 sm:grid-cols-2 md:grid-cols-4 md:px-8">
            <Proof Icon={ScrollText} n={4000} l="development cases decided, four institutions" />
            <Proof Icon={Repeat2} n={5} suffix=" / 5" l="runs with byte-identical output" />
            <Proof Icon={Fingerprint} n={0} l="verdicts changed when every ID is renamed and shuffled" />
            <Proof Icon={FlaskConical} n={2000} l="closes, and every one fails without its cited documents" />
          </div>
          <div className="mx-auto max-w-6xl px-4 pb-16 md:px-8">
            <div className="relative overflow-hidden rounded-2xl border bg-card p-8 md:p-12">
              <h2 className="font-serif text-3xl">See a decision and its trail.</h2>
              <p className="mt-2 max-w-xl text-muted-foreground">Open any case: the alert, the money, the people, the documents, and the decision, each linked to its source.</p>
              <Button className="mt-6" size="lg" nativeButton={false} render={<Link href="/queue" />}>Open the alert queue <ArrowRight className="size-4" /></Button>
              <BorderBeam size={200} duration={10} colorFrom="var(--rfi)" colorTo="var(--close)" />
            </div>
          </div>
        </section>
      </main>
      <footer className="border-t py-6 text-center text-xs text-muted-foreground">Built at the Grok Bot London Financial Crime Hackathon. All data is synthetic.</footer>
    </div>
  );
}

function Stat({ n, prefix, suffix, l }: { n: number; prefix?: string; suffix?: string; l: string }) {
  return (
    <div className="rounded-xl border bg-card p-5">
      <div className="font-serif text-4xl">{prefix}<NumberTicker value={n} />{suffix}</div>
      <p className="mt-2 text-sm text-muted-foreground">{l}</p>
    </div>
  );
}

function Proof({ Icon, n, suffix, l }: { Icon: React.ElementType; n: number; suffix?: string; l: string }) {
  return (
    <div>
      <Icon className="size-5 text-muted-foreground" aria-hidden="true" />
      <div className="mt-2 font-serif text-4xl">{n === 0 ? "0" : <NumberTicker value={n} />}{suffix}</div>
      <p className="mt-1 text-sm text-muted-foreground">{l}</p>
    </div>
  );
}
