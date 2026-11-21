"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutGrid, ListChecks, ScrollText, ShieldCheck, Info } from "lucide-react";
import {
  Sidebar, SidebarContent, SidebarFooter, SidebarGroup, SidebarGroupContent, SidebarGroupLabel, SidebarHeader,
  SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarSeparator, useSidebar,
} from "@/components/ui/sidebar";
import { Logo } from "./Logo";
import { INSTITUTIONS } from "@/lib/ct";

const MAIN = [
  { href: "/overview", label: "Overview", Icon: LayoutGrid },
  { href: "/queue", label: "Alert queue", Icon: ListChecks },
  { href: "/policies", label: "Policies", Icon: ScrollText },
  { href: "/assurance", label: "Assurance", Icon: ShieldCheck },
];

export function AppSidebar() {
  const path = usePathname();
  const { setOpenMobile } = useSidebar();
  const close = () => setOpenMobile(false);
  return (
    <Sidebar>
      <SidebarHeader className="px-4 pt-5 pb-3">
        <Link href="/" aria-label="ControlTrail home"><Logo /></Link>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {MAIN.map(({ href, label, Icon }) => (
                <SidebarMenuItem key={href}>
                  <SidebarMenuButton isActive={path.startsWith(href) || (href === "/queue" && path.startsWith("/case"))}
                    render={<Link href={href} onClick={close} />}>
                    <Icon aria-hidden="true" />
                    <span>{label}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        <SidebarSeparator />
        <SidebarGroup>
          <SidebarGroupLabel>Institutions</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {INSTITUTIONS.map((i) => (
                <SidebarMenuItem key={i.id}>
                  <SidebarMenuButton size="sm" render={<Link href={`/queue?inst=${i.id}`} onClick={close} />}>
                    <span className="size-2 shrink-0 rounded-full bg-muted-foreground/50" aria-hidden="true" />
                    <span className="truncate">{i.name}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter className="px-4 pb-4">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="sm" render={<Link href="/" onClick={close} />}><Info aria-hidden="true" /><span>About</span></SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
        <p className="text-[11px] leading-4 text-muted-foreground">Synthetic hackathon data. Every customer, company and document is invented.</p>
      </SidebarFooter>
    </Sidebar>
  );
}
