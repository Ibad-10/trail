import { Suspense } from "react";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/ct/AppSidebar";
import { TopBar } from "@/components/ct/TopBar";
import { DotPattern } from "@/components/ui/dot-pattern";

export default function DeskLayout({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider>
      <Suspense fallback={null}>
        <AppSidebar />
      </Suspense>
      <SidebarInset className="relative">
        <DotPattern className="pointer-events-none text-foreground/10 [mask-image:linear-gradient(to_bottom,white,transparent_420px)]" />
        <Suspense fallback={null}>
          <TopBar />
        </Suspense>
        <main className="relative mx-auto w-full max-w-6xl flex-1 px-4 py-6 md:px-8">
          <Suspense fallback={null}>{children}</Suspense>
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
