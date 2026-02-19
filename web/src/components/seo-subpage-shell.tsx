import React from "react";
import Link from "next/link";
import { BookOpen, ChevronRight, Cpu, HelpCircle, Home, Map, Rss, Shield, Users } from "lucide-react";
import { VocalinuxLogo } from "@/components/optimized-image";

interface SeoSubpageShellProps {
  children: React.ReactNode;
}

const navLinks = [
  {
    href: "/",
    label: "Home",
    icon: Home,
  },
  {
    href: "/install/",
    label: "Install Guides",
    icon: BookOpen,
  },
  {
    href: "/compare/",
    label: "Engine Compare",
    icon: Cpu,
  },
  {
    href: "/use-cases/",
    label: "Use Cases",
    icon: Users,
  },
  {
    href: "/faq/",
    label: "FAQ",
    icon: HelpCircle,
  },
  {
    href: "/changelog/",
    label: "Changelog",
    icon: Rss,
  },
  {
    href: "/privacy/",
    label: "Privacy",
    icon: Shield,
  },
  {
    href: "/alternatives/",
    label: "Alternatives",
    icon: Map,
  },
];

export function SeoSubpageShell({ children }: SeoSubpageShellProps) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-zinc-50 to-white dark:from-zinc-900 dark:to-zinc-950">
      <header className="border-b border-zinc-200/80 bg-background/80 backdrop-blur-md dark:border-zinc-800/80">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
          <Link href="/" className="group flex items-center gap-2">
            <VocalinuxLogo width={30} height={30} className="h-7 w-7 transition-transform group-hover:scale-110" />
            <span className="text-base font-bold sm:text-lg">Vocalinux</span>
          </Link>

          <nav className="hidden items-center gap-2 sm:flex">
            {navLinks.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-zinc-100 hover:text-foreground dark:hover:bg-zinc-800"
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="mx-auto flex max-w-6xl gap-2 overflow-x-auto px-4 pb-4 sm:hidden scrollbar-thin">
          {navLinks.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                title={item.label}
                className="inline-flex items-center justify-center rounded-lg border border-zinc-200 bg-white p-2 text-muted-foreground transition-colors hover:bg-zinc-50 hover:text-foreground dark:border-zinc-700 dark:bg-zinc-800 dark:hover:bg-zinc-700"
                aria-label={item.label}
              >
                <Icon className="h-4 w-4" />
              </Link>
            );
          })}
        </div>
      </header>

      <div className="mx-auto w-full max-w-6xl px-4 pb-16 pt-10 sm:px-6 sm:pt-12">{children}</div>

      <footer className="border-t border-zinc-200 bg-white/70 dark:border-zinc-800 dark:bg-zinc-900/60">
        <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-5 px-4 py-8 sm:flex-row sm:items-center sm:px-6">
          <div>
            <p className="text-sm font-semibold">Want the full product overview?</p>
            <p className="text-sm text-muted-foreground">Go back to the homepage for the live demo and one-command installer.</p>
          </div>
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
          >
            Home Page
            <ChevronRight className="h-4 w-4" />
          </Link>
        </div>
      </footer>
    </div>
  );
}
