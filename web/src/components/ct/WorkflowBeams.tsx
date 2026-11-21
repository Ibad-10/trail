"use client";
import { forwardRef, useRef } from "react";
import { ArrowRightLeft, Building2, FileText, Landmark, ListX, Siren, Check, HelpCircle, ShieldAlert } from "lucide-react";
import { AnimatedBeam } from "@/components/ui/animated-beam";
import { cn } from "@/lib/utils";

const Node = forwardRef<HTMLDivElement, { className?: string; children: React.ReactNode; label: string }>(({ className, children, label }, ref) => (
  <div className="flex flex-col items-center gap-1.5">
    <div ref={ref} className={cn("z-10 flex size-12 items-center justify-center rounded-full border-2 bg-card shadow-sm", className)}>{children}</div>
    <span className="text-[11px] font-medium text-muted-foreground">{label}</span>
  </div>
));
Node.displayName = "Node";

export function WorkflowBeams() {
  const box = useRef<HTMLDivElement>(null);
  const ins = [useRef<HTMLDivElement>(null), useRef<HTMLDivElement>(null), useRef<HTMLDivElement>(null), useRef<HTMLDivElement>(null), useRef<HTMLDivElement>(null)];
  const core = useRef<HTMLDivElement>(null);
  const outs = [useRef<HTMLDivElement>(null), useRef<HTMLDivElement>(null), useRef<HTMLDivElement>(null)];
  const IN = [
    { Icon: Siren, l: "Alert" }, { Icon: ArrowRightLeft, l: "Transactions" }, { Icon: FileText, l: "Documents" },
    { Icon: Building2, l: "Registers" }, { Icon: ListX, l: "Internal list" },
  ];
  const OUT = [
    { Icon: Check, l: "Close", c: "var(--close)" }, { Icon: HelpCircle, l: "Ask (RFI)", c: "var(--rfi)" }, { Icon: ShieldAlert, l: "Escalate", c: "var(--esc)" },
  ];
  return (
    <div ref={box} className="relative flex w-full items-center justify-between gap-6 overflow-hidden rounded-2xl border bg-card/60 p-6 backdrop-blur md:p-10" aria-label="Workflow: alert, transactions, documents, registers and internal list flow into Trail, which decides close, RFI or escalate">
      <div className="flex flex-col gap-3">
        {IN.map(({ Icon, l }, i) => <Node key={l} ref={ins[i]} label={l}><Icon className="size-5" aria-hidden="true" /></Node>)}
      </div>
      <div className="flex flex-col items-center gap-2">
        <div ref={core} className="z-10 flex size-20 flex-col items-center justify-center rounded-2xl border-2 border-foreground bg-foreground text-background shadow-lg">
          <Landmark className="size-7" aria-hidden="true" />
        </div>
        <span className="text-xs font-semibold">Firm policy as code</span>
      </div>
      <div className="flex flex-col gap-6">
        {OUT.map(({ Icon, l, c }, i) => (
          <Node key={l} ref={outs[i]} label={l} className="border-[3px]"><Icon className="size-5" style={{ color: c }} aria-hidden="true" /></Node>
        ))}
      </div>
      {ins.map((r, i) => <AnimatedBeam key={i} containerRef={box} fromRef={r} toRef={core} curvature={(2 - i) * 18} duration={4} delay={i * 0.2} />)}
      {outs.map((r, i) => <AnimatedBeam key={i} containerRef={box} fromRef={core} toRef={r} curvature={(1 - i) * 20} duration={4} delay={1 + i * 0.3}
        gradientStartColor={OUT[i].c} gradientStopColor={OUT[i].c} />)}
    </div>
  );
}
