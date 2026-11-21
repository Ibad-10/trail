"use client";
import { useEffect, useState } from "react";

export type Verdict = "CLOSE" | "RFI" | "ESCALATE";
export type CaseSummary = { inst: string; case_id: string; customer: string; kind: string; rules: string[]; verdict: Verdict; code: string; held: string | null; reason: string };
export type GNode = { id: string; col: number; label: string; sub: string; kind: string; src: { id: string; text: string } | null; hot: boolean };
export type CaseFull = CaseSummary & { declared: Record<string, unknown>; evidence: string[]; window: { from: string; to: string } | null; nodes: GNode[]; edges: [string, string, string, string][] };
export type Policy = { title: string; intro: string; rules: { id: string; name: string; fires: string }[]; high_risk: string[]; own_account_multiple: number; policy: string };

export const INSTITUTIONS = [
  { id: "bank", name: "Bank" },
  { id: "emoney", name: "E-money firm" },
  { id: "investment", name: "Investment firm" },
  { id: "payments_fx", name: "Payments and FX firm" },
] as const;
export const instName = (id: string) => INSTITUTIONS.find((i) => i.id === id)?.name ?? id;

export const VERDICT = {
  CLOSE: { word: "Close", long: "Close: the evidence explains it", icon: "✓", cls: "text-close bg-close-bg", dot: "var(--close)" },
  RFI: { word: "Ask customer", long: "RFI: ask the customer for one thing", icon: "?", cls: "text-rfi bg-rfi-bg", dot: "var(--rfi)" },
  ESCALATE: { word: "Escalate", long: "Escalate to the MLRO", icon: "⚠", cls: "text-esc bg-esc-bg", dot: "var(--esc)" },
} as const;

export const RULES: Record<string, string> = {
  TM01: "Activity above profile", TM02: "Rapid movement", TM03: "Just under a threshold", TM04: "Many payers or payees",
  TM05: "Large cash", TM06: "Higher-risk country", TM07: "Dormant account", TM08: "Third-party funds", TM10: "Early fund sale", TM22: "Internal list match",
};

export const codeText = (c: string) => c.replace(/^ESC_|^RFI_/, "").toLowerCase().replace(/_/g, " ").replace(/^./, (x) => x.toUpperCase());

const cache = new Map<string, unknown>();
export function useJson<T>(url: string | null): { data: T | null; error: boolean } {
  const [state, set] = useState<{ data: T | null; error: boolean }>({ data: url ? (cache.get(url) as T) ?? null : null, error: false });
  useEffect(() => {
    if (!url) return;
    if (cache.has(url)) { set({ data: cache.get(url) as T, error: false }); return; }
    let live = true;
    fetch(url).then((r) => (r.ok ? r.json() : Promise.reject(r.status))).then((d) => { cache.set(url, d); if (live) set({ data: d, error: false }); })
      .catch(() => live && set({ data: null, error: true }));
    return () => { live = false; };
  }, [url]);
  return state;
}
