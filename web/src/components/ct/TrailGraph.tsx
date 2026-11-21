"use client";
import { useMemo, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import type { CaseFull, GNode } from "@/lib/ct";
import { VERDICT } from "@/lib/ct";

const COLS = ["What fired", "Money moved", "Who is involved", "Documents on file", "Decision"];
const W = 1080, COLW = W / 5, NW = COLW - 26, NH = 52, GAP = 12;

const trunc = (s: string, n: number) => (s.length > n ? s.slice(0, n - 1) + "…" : s);

export function TrailGraph({ c, selected, onSelect }: { c: CaseFull; selected: string | null; onSelect: (n: GNode) => void }) {
  const [hover, setHover] = useState<string | null>(null);
  const reduce = useReducedMotion();
  const { pos, H, edges } = useMemo(() => {
    const byCol: GNode[][] = [[], [], [], [], []];
    c.nodes.forEach((n) => byCol[n.col].push(n));
    const H = Math.max(...byCol.map((a) => a.length), 1) * (NH + GAP) + 24;
    const pos: Record<string, { x: number; y: number }> = {};
    byCol.forEach((arr, ci) => {
      const top = (H - arr.length * (NH + GAP)) / 2 + GAP / 2;
      arr.forEach((n, j) => (pos[n.id] = { x: ci * COLW + 13, y: top + j * (NH + GAP) }));
    });
    const seen = new Set<string>();
    const edges = c.edges.filter((e) => pos[e[0]] && pos[e[1]] && !seen.has(e[0] + ">" + e[1]) && seen.add(e[0] + ">" + e[1]));
    return { pos, H, edges };
  }, [c]);
  const focus = hover ?? selected;
  const path = (a: string, b: string) => {
    const p = pos[a], q = pos[b];
    const x1 = p.x + NW, y1 = p.y + NH / 2, x2 = q.x, y2 = q.y + NH / 2, mx = (x1 + x2) / 2;
    return `M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`;
  };
  const vm = VERDICT[c.verdict];
  return (
    <div className="overflow-x-auto rounded-xl border bg-muted/30">
      <div style={{ width: W }} className="grid grid-cols-5 px-3 pt-3 text-[11px] font-semibold tracking-wider text-muted-foreground uppercase">
        {COLS.map((x) => <span key={x}>{x}</span>)}
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} role="img" aria-label="Evidence trail graph. The text path lists the same links.">
        {edges.map((e, i) => {
          const lit = focus && (e[0] === focus || e[1] === focus);
          return (
            <motion.path key={i} d={path(e[0], e[1])} fill="none"
              stroke={lit ? "currentColor" : "var(--muted-foreground)"} strokeOpacity={lit ? 1 : 0.45} strokeWidth={lit ? 2.4 : 1.5}
              initial={reduce ? false : { pathLength: 0, opacity: 0 }} animate={{ pathLength: 1, opacity: focus && !lit ? 0.25 : 1 }}
              transition={{ duration: 0.6, delay: reduce ? 0 : 0.15 + (pos[e[0]]?.x ?? 0) / 2400 }}>
              <title>{`${e[2]} (source ${e[3]})`}</title>
            </motion.path>
          );
        })}
        {c.nodes.map((n, i) => {
          const p = pos[n.id];
          const isV = n.kind === "verdict";
          const sel = selected === n.id;
          return (
            <g key={n.id} transform={`translate(${p.x},${p.y})`}>
            <motion.g tabIndex={0} role="button" aria-label={`${n.label}. ${n.sub}`} className="cursor-pointer outline-none"
              initial={reduce ? false : { opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: reduce ? 0 : n.col * 0.08 + i * 0.01 }}
              onMouseEnter={() => setHover(n.id)} onMouseLeave={() => setHover(null)} onFocus={() => setHover(n.id)} onBlur={() => setHover(null)}
              onClick={() => onSelect(n)} onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSelect(n); } }}>
              <rect width={NW} height={NH} rx={9}
                fill={isV ? `var(--${c.verdict === "CLOSE" ? "close" : c.verdict === "RFI" ? "rfi" : "esc"}-bg)` : "var(--card)"}
                stroke={sel ? "#ffb000" : isV ? vm.dot : n.hot ? "var(--hot)" : "var(--border)"} strokeWidth={sel ? 3 : n.hot || isV ? 2 : 1.2} />
              <text x={10} y={21} fontSize={12} fontWeight={600} fill="currentColor">{trunc(isV ? `${vm.icon} ${n.label}` : n.label, 28)}</text>
              <text x={10} y={38} fontSize={10.5} fill="var(--muted-foreground)">{trunc(n.sub || n.id, 34)}</text>
            </motion.g>
            </g>
          );
        })}
      </svg>
      <p className="px-3 pb-3 text-xs text-muted-foreground">Green outline: cited as evidence. Hover a box to trace its links, and click or press Enter to read the source.</p>
    </div>
  );
}
