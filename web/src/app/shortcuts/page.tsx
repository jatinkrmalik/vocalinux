import Link from "next/link";
import { type Metadata } from "next";
import { ChevronRight, Command, Keyboard, Mouse, Settings, Space, Zap } from "lucide-react";
import { SeoSubpageShell } from "@/components/seo-subpage-shell";
import { absoluteUrl, buildPageMetadata } from "@/lib/seo";

const shortcutCategories = [
  {
    category: "Dictation Controls",
    icon: Mic,
    iconColor: "text-blue-500",
    shortcuts: [
      { keys: ["Ctrl", "Ctrl"], action: "Toggle dictation on/off (double-tap)", note: "Primary activation" },
      { keys: ["Ctrl", "Ctrl"], action: "Start/stop recording", note: "Same as toggle" },
    ],
  },
  {
    category: "Voice Commands",
    icon: Zap,
    iconColor: "text-amber-500",
    shortcuts: [
      { keys: ["\"new line\""], action: "Insert a new line", note: "Say this phrase" },
      { keys: ["\"new paragraph\""], action: "Insert a new paragraph", note: "Say this phrase" },
      { keys: ["\"delete that\""], action: "Delete last phrase", note: "Also: \"scratch that\"" },
      { keys: ["\"select all\""], action: "Select all text", note: "Voice command" },
      { keys: ["\"copy this\""], action: "Copy selection", note: "Voice command" },
      { keys: ["\"paste here\""], action: "Paste clipboard", note: "Voice command" },
      { keys: ["\"undo\""], action: "Undo last action", note: "Voice command" },
      { keys: ["\"redo\""], action: "Redo last action", note: "Voice command" },
    ],
  },
  {
    category: "Tray Icon Actions",
    icon: Mouse,
    iconColor: "text-green-500",
    shortcuts: [
      { keys: ["Left Click"], action: "Toggle dictation", note: "On tray icon" },
      { keys: ["Right Click"], action: "Open context menu", note: "Settings, quit, etc." },
    ],
  },
  {
    category: "Configuration",
    icon: Settings,
    iconColor: "text-violet-500",
    shortcuts: [
      { keys: ["Config File"], action: "~/.config/vocalinux/config.yaml", note: "Manual editing" },
    ],
  },
];

function Mic(props: { className?: string }) {
  return (
    <svg className={props.className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" x2="12" y1="19" y2="22" />
    </svg>
  );
}

export const metadata: Metadata = buildPageMetadata({
  title: "Keyboard Shortcuts & Voice Commands - Vocalinux",
  description:
    "Learn Vocalinux keyboard shortcuts and voice commands. Double-tap Ctrl to dictate, use voice commands for editing, and customize your workflow.",
  path: "/shortcuts",
  keywords: [
    "vocalinux shortcuts",
    "linux voice dictation commands",
    "speech to text keyboard shortcuts",
    "voice commands linux",
  ],
});

export default function ShortcutsPage() {
  const articleJsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: "Vocalinux Keyboard Shortcuts & Voice Commands",
    description:
      "Complete guide to Vocalinux keyboard shortcuts and voice commands for efficient Linux voice dictation.",
    dateModified: "2026-02-19",
    author: {
      "@type": "Person",
      name: "Jatin K Malik",
      url: "https://github.com/jatinkrmalik",
    },
    publisher: {
      "@type": "Organization",
      name: "Vocalinux",
      logo: {
        "@type": "ImageObject",
        url: absoluteUrl("/vocalinux.png"),
      },
    },
    mainEntityOfPage: absoluteUrl("/shortcuts"),
  };

  return (
    <SeoSubpageShell>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleJsonLd) }}
      />

      <section>
        <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-sm font-medium text-primary">
          <Keyboard className="h-4 w-4" />
          Quick Reference
        </p>
        <h1 className="mb-5 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
          Keyboard Shortcuts & Voice Commands
        </h1>
        <p className="mb-8 max-w-4xl text-lg text-muted-foreground">
          Master Vocalinux with keyboard shortcuts and voice commands. Double-tap Ctrl to start
          dictating, then use voice commands to edit and format.
        </p>
      </section>

      {/* Quick Start */}
      <section className="mb-12 rounded-2xl border border-primary/20 bg-primary/5 p-6">
        <h2 className="mb-4 text-xl font-bold">Quick Start</h2>
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <kbd className="rounded-lg border border-zinc-300 bg-zinc-100 px-3 py-1.5 font-mono text-sm font-semibold dark:border-zinc-600 dark:bg-zinc-800">
              Ctrl
            </kbd>
            <span className="text-muted-foreground">+</span>
            <kbd className="rounded-lg border border-zinc-300 bg-zinc-100 px-3 py-1.5 font-mono text-sm font-semibold dark:border-zinc-600 dark:bg-zinc-800">
              Ctrl
            </kbd>
          </div>
          <span className="text-muted-foreground">→</span>
          <span className="font-medium">Start/Stop Dictation</span>
        </div>
      </section>

      {/* Shortcut Categories */}
      <section className="space-y-8">
        {shortcutCategories.map((category) => {
          const Icon = category.icon;
          return (
            <article
              key={category.category}
              className="rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800"
            >
              <h2 className="mb-6 flex items-center gap-3 text-2xl font-bold">
                <span className={`rounded-xl bg-zinc-100 p-2 dark:bg-zinc-700`}>
                  <Icon className={`h-5 w-5 ${category.iconColor}`} />
                </span>
                {category.category}
              </h2>

              <div className="space-y-4">
                {category.shortcuts.map((shortcut, index) => (
                  <div
                    key={index}
                    className="flex flex-wrap items-center justify-between gap-4 rounded-xl bg-zinc-50 p-4 dark:bg-zinc-900/50"
                  >
                    <div className="flex items-center gap-3">
                      {shortcut.keys.map((key, keyIndex) => (
                        <span key={keyIndex} className="flex items-center gap-2">
                          <kbd className="rounded-lg border border-zinc-300 bg-zinc-100 px-3 py-1.5 font-mono text-sm font-semibold shadow-sm dark:border-zinc-600 dark:bg-zinc-800">
                            {key}
                          </kbd>
                          {keyIndex < shortcut.keys.length - 1 && (
                            <span className="text-muted-foreground">+</span>
                          )}
                        </span>
                      ))}
                    </div>
                    <div className="text-right">
                      <p className="font-medium">{shortcut.action}</p>
                      <p className="text-sm text-muted-foreground">{shortcut.note}</p>
                    </div>
                  </div>
                ))}
              </div>
            </article>
          );
        })}
      </section>

      {/* Customization */}
      <section className="mt-12 rounded-2xl border border-zinc-200 bg-zinc-50 p-8 dark:border-zinc-700 dark:bg-zinc-900/60">
        <h2 className="mb-4 text-2xl font-bold">Customizing Shortcuts</h2>
        <p className="mb-4 text-muted-foreground">
          You can customize the activation shortcut in the settings panel or by editing the
          configuration file directly:
        </p>
        <div className="rounded-lg bg-zinc-950 p-4">
          <code className="text-sm text-green-400">~/.config/vocalinux/config.yaml</code>
        </div>
        <p className="mt-4 text-sm text-muted-foreground">
          Open Vocalinux and access Settings from the tray icon to change keyboard shortcuts
          through the GUI.
        </p>
      </section>

      {/* Related Pages */}
      <section className="mt-12 grid gap-6 md:grid-cols-2">
        <Link
          href="/faq/"
          className="group rounded-2xl border border-zinc-200 bg-white p-6 transition-all hover:-translate-y-1 hover:shadow-lg dark:border-zinc-700 dark:bg-zinc-800"
        >
          <h3 className="mb-2 text-xl font-semibold">Frequently Asked Questions</h3>
          <p className="text-sm text-muted-foreground">
            Get answers to common questions about Vocalinux features and usage.
          </p>
          <span className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-primary">
            View FAQ
            <ChevronRight className="h-4 w-4" />
          </span>
        </Link>

        <Link
          href="/troubleshooting/"
          className="group rounded-2xl border border-zinc-200 bg-white p-6 transition-all hover:-translate-y-1 hover:shadow-lg dark:border-zinc-700 dark:bg-zinc-800"
        >
          <h3 className="mb-2 text-xl font-semibold">Troubleshooting</h3>
          <p className="text-sm text-muted-foreground">
            Having issues? Find solutions to common problems and fixes.
          </p>
          <span className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-primary">
            Get Help
            <ChevronRight className="h-4 w-4" />
          </span>
        </Link>
      </section>
    </SeoSubpageShell>
  );
}
