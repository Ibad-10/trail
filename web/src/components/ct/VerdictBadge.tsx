import { VERDICT, type Verdict } from "@/lib/ct";
import { cn } from "@/lib/utils";

export function VerdictBadge({ v, long, className }: { v: Verdict; long?: boolean; className?: string }) {
  const m = VERDICT[v];
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold whitespace-nowrap", m.cls, className)}>
      <span aria-hidden="true">{m.icon}</span>
      {long ? m.long : m.word}
    </span>
  );
}
