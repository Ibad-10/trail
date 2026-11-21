"use client";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Moon, Search, Sun } from "lucide-react";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { Command, CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { useJson, type CaseSummary, instName } from "@/lib/ct";
import { VerdictBadge } from "./VerdictBadge";

export function TopBar() {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const router = useRouter();
  const { data } = useJson<CaseSummary[]>(open ? "/data/cases.json" : null);
  useEffect(() => {
    const k = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); setOpen((o) => !o); }
    };
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, []);
  const hits = useMemo(() => {
    if (!data) return [];
    const s = q.trim().toLowerCase();
    return (s ? data.filter((c) => (c.case_id + " " + c.customer + " " + c.code).toLowerCase().includes(s)) : data).slice(0, 30);
  }, [data, q]);
  const toggleTheme = () => {
    const d = document.documentElement.classList.toggle("dark");
    try { localStorage.setItem("ct-theme", d ? "dark" : "light"); } catch {}
  };
  return (
    <header className="sticky top-0 z-20 flex h-14 items-center gap-2 border-b bg-background/85 px-3 backdrop-blur md:px-5">
      <SidebarTrigger aria-label="Open navigation" />
      <div className="flex-1" />
      <Button variant="outline" size="sm" onClick={() => setOpen(true)} className="gap-2 text-muted-foreground" aria-label="Search cases">
        <Search className="size-4" aria-hidden="true" />
        <span className="hidden sm:inline">Search cases</span>
        <kbd className="hidden rounded border bg-muted px-1.5 text-[10px] sm:inline">Ctrl K</kbd>
      </Button>
      <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label="Toggle dark mode">
        <Sun className="size-4 dark:hidden" aria-hidden="true" /><Moon className="hidden size-4 dark:block" aria-hidden="true" />
      </Button>
      <CommandDialog open={open} onOpenChange={setOpen} title="Search cases" description="Search by case ID, customer or reason code">
        <Command shouldFilter={false}>
        <CommandInput placeholder="Case ID, customer or reason code" value={q} onValueChange={setQ} />
        <CommandList>
          <CommandEmpty>{data ? "No matching cases." : "Loading cases"}</CommandEmpty>
          <CommandGroup heading="Cases">
            {hits.map((c) => (
              <CommandItem key={c.case_id} value={c.case_id + " " + c.customer + " " + c.code}
                onSelect={() => { setOpen(false); router.push(`/case/${c.case_id}`); }}>
                <VerdictBadge v={c.verdict} />
                <span className="truncate font-medium">{c.customer}</span>
                <span className="ml-auto truncate text-xs text-muted-foreground">{c.case_id} · {instName(c.inst)}</span>
              </CommandItem>
            ))}
          </CommandGroup>
        </CommandList>
        </Command>
      </CommandDialog>
    </header>
  );
}
