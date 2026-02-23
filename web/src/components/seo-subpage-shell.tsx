"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  ChevronDown,
  ChevronRight,
  Code2,
  Cpu,
  Globe,
  Heart,
  HelpCircle,
  Home,
  Menu,
  Monitor,
  Power,
  Shield,
  X,
  Zap,
} from "lucide-react";
import { VocalinuxLogo } from "@/components/optimized-image";

interface SeoSubpageShellProps {
  children: React.ReactNode;
}

const navCategories = [
  {
    label: "Get Started",
    items: [
      { href: "/", label: "Home", icon: Home },
      { href: "/install/", label: "Install Guides", icon: BookOpen },
      { href: "/changelog/", label: "Changelog", icon: Zap },
    ],
  },
  {
    label: "Features",
    items: [
      { href: "/compare/", label: "Engine Comparison", icon: Cpu },
      { href: "/languages/", label: "Multilingual", icon: Globe },
      { href: "/wayland/", label: "Wayland Support", icon: Monitor },
      { href: "/gpu-acceleration/", label: "GPU Acceleration", icon: Cpu },
      { href: "/autostart/", label: "Autostart", icon: Power },
    ],
  },
  {
    label: "Use Cases",
    items: [
      { href: "/for-developers/", label: "For Developers", icon: Code2 },
      { href: "/rsi-prevention/", label: "RSI Prevention", icon: Heart },
      { href: "/use-cases/", label: "All Use Cases", icon: Zap },
    ],
  },
  {
    label: "Privacy & Ethics",
    items: [
      { href: "/offline/", label: "100% Offline", icon: Shield },
      { href: "/open-source/", label: "Open Source", icon: Code2 },
      { href: "/privacy/", label: "Privacy Policy", icon: Shield },
    ],
  },
  {
    label: "Support",
    items: [
      { href: "/faq/", label: "FAQ", icon: HelpCircle },
      { href: "/troubleshooting/", label: "Troubleshooting", icon: Zap },
      { href: "/shortcuts/", label: "Voice Commands", icon: BookOpen },
      { href: "/alternatives/", label: "Alternatives", icon: BookOpen },
    ],
  },
];

function DropdownMenu({
  category,
  isOpen,
  onToggle,
}: {
  category: (typeof navCategories)[0];
  isOpen: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="relative">
      <button
        onClick={onToggle}
        className={`inline-flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
          isOpen
            ? "bg-zinc-100 text-foreground dark:bg-zinc-800"
            : "text-muted-foreground hover:bg-zinc-100 hover:text-foreground dark:hover:bg-zinc-800"
        }`}
      >
        {category.label}
        <ChevronDown
          className={`h-3.5 w-3.5 transition-transform ${isOpen ? "rotate-180" : ""}`}
        />
      </button>

      {isOpen && (
        <div className="absolute left-0 top-full z-50 mt-1 w-56 rounded-xl border border-zinc-200 bg-white p-2 shadow-lg dark:border-zinc-700 dark:bg-zinc-800">
          {category.items.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-zinc-100 hover:text-foreground dark:hover:bg-zinc-700"
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}

function Breadcrumbs() {
  const pathname = usePathname();

  if (pathname === "/") return null;

  const segments = pathname.split("/").filter(Boolean);
  const breadcrumbs = segments.map((segment, index) => {
    const href = "/" + segments.slice(0, index + 1).join("/");
    const label = segment
      .replace(/-/g, " ")
      .replace(/\b\w/g, (l) => l.toUpperCase());
    return { href, label };
  });

  const getPageTitle = (path: string): string => {
    for (const category of navCategories) {
      for (const item of category.items) {
        if (item.href === path || item.href === path + "/") {
          return item.label;
        }
      }
    }
    return (
      path
        .split("/")
        .pop()
        ?.replace(/-/g, " ")
        .replace(/\b\w/g, (l) => l.toUpperCase()) || ""
    );
  };

  return (
    <nav className="mb-6 flex items-center gap-2 text-sm text-muted-foreground">
      <Link href="/" className="hover:text-foreground transition-colors">
        Home
      </Link>
      {breadcrumbs.map((crumb, index) => (
        <React.Fragment key={crumb.href}>
          <ChevronRight className="h-4 w-4" />
          {index === breadcrumbs.length - 1 ? (
            <span className="text-foreground font-medium">
              {getPageTitle(crumb.href)}
            </span>
          ) : (
            <Link
              href={crumb.href}
              className="hover:text-foreground transition-colors"
            >
              {crumb.label}
            </Link>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
}

export function SeoSubpageShell({ children }: SeoSubpageShellProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);

  const handleDropdownToggle = (label: string) => {
    setOpenDropdown(openDropdown === label ? null : label);
  };

  // Close dropdowns when clicking outside
  const handleClickOutside = () => {
    setOpenDropdown(null);
  };

  return (
    <div
      className="min-h-screen bg-gradient-to-b from-zinc-50 to-white dark:from-zinc-900 dark:to-zinc-950"
      onClick={handleClickOutside}
    >
      <header className="sticky top-0 z-50 border-b border-zinc-200/80 bg-background/95 backdrop-blur-md dark:border-zinc-800/80">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
          <Link href="/" className="group flex items-center gap-2">
            <VocalinuxLogo
              width={30}
              height={30}
              className="h-7 w-7 transition-transform group-hover:scale-110"
            />
            <span className="text-base font-bold sm:text-lg">Vocalinux</span>
          </Link>

          {/* Desktop nav with dropdowns */}
          <nav className="hidden items-center gap-1 md:flex">
            {navCategories.map((category) => (
              <DropdownMenu
                key={category.label}
                category={category}
                isOpen={openDropdown === category.label}
                onToggle={() => handleDropdownToggle(category.label)}
              />
            ))}
          </nav>

          {/* Mobile menu button */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              setMobileMenuOpen(!mobileMenuOpen);
            }}
            className="flex items-center justify-center rounded-lg p-2 text-muted-foreground transition-colors hover:bg-zinc-100 hover:text-foreground dark:hover:bg-zinc-800 md:hidden"
            aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
          >
            {mobileMenuOpen ? (
              <X className="h-6 w-6" />
            ) : (
              <Menu className="h-6 w-6" />
            )}
          </button>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="border-t border-zinc-200 bg-white dark:border-zinc-700 dark:bg-zinc-900 md:hidden">
            <nav className="max-h-[calc(100vh-4rem)] overflow-y-auto px-4 py-4">
              {navCategories.map((category) => (
                <div key={category.label} className="mb-4">
                  <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    {category.label}
                  </h3>
                  <div className="space-y-1">
                    {category.items.map((item) => {
                      const Icon = item.icon;
                      return (
                        <Link
                          key={item.href}
                          href={item.href}
                          onClick={() => setMobileMenuOpen(false)}
                          className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-zinc-100 hover:text-foreground dark:hover:bg-zinc-800"
                        >
                          <Icon className="h-4 w-4" />
                          {item.label}
                        </Link>
                      );
                    })}
                  </div>
                </div>
              ))}
            </nav>
          </div>
        )}
      </header>

      <div className="mx-auto w-full max-w-6xl px-4 pb-16 pt-6 sm:px-6 sm:pt-10">
        <Breadcrumbs />
        {children}
      </div>

      <footer className="border-t border-zinc-200 bg-white/70 dark:border-zinc-800 dark:bg-zinc-900/60">
        <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
          <div className="mb-6 flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
            <div>
              <p className="text-sm font-semibold">Want the full product overview?</p>
              <p className="text-sm text-muted-foreground">
                Go back to the homepage for the live demo and one-command installer.
              </p>
            </div>
            <Link
              href="/"
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
            >
              Home Page
              <ChevronRight className="h-4 w-4" />
            </Link>
          </div>

          {/* Footer links - all pages organized */}
          <div className="grid gap-6 border-t border-zinc-200 pt-6 dark:border-zinc-700 sm:grid-cols-2 lg:grid-cols-5">
            {navCategories.map((category) => (
              <div key={category.label}>
                <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  {category.label}
                </h4>
                <ul className="space-y-1.5">
                  {category.items.map((item) => (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                      >
                        {item.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
