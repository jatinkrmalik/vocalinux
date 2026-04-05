import Link from "next/link";
import { type Metadata } from "next";
import { CheckCircle2, ChevronRight, Keyboard, Monitor, Terminal, Zap } from "lucide-react";
import { SeoSubpageShell } from "@/components/seo-subpage-shell";
import { absoluteUrl, buildPageMetadata } from "@/lib/seo";

const waylandFeatures = [
  {
    title: "Native IBus Integration",
    description:
      "Text injection via IBus engine works seamlessly on Wayland compositors like GNOME, KDE, Sway, and Hyprland.",
    icon: Terminal,
  },
  {
    title: "Keyboard Layout Preservation",
    description:
      "v0.10.1+ preserves your XKB keyboard layout when activating IBus. No more switching to US layout unexpectedly.",
    icon: Keyboard,
  },
  {
    title: "X11 Fallback Support",
    description:
      "Automatic fallback to xdotool when running under XWayland or traditional X11 sessions.",
    icon: Monitor,
  },
  {
    title: "Desktop Agnostic",
    description:
      "Works with GNOME, KDE Plasma, Sway, Hyprland, river, and other Wayland compositors.",
    icon: Zap,
  },
];

const compositorSupport = [
  {
    name: "GNOME (mutter)",
    method: "IBus",
    status: "Full support",
    notes: "Default on Ubuntu, Fedora, Debian GNOME editions",
  },
  {
    name: "KDE Plasma (KWin)",
    method: "IBus",
    status: "Full support",
    notes: "Works with IBus input method framework",
  },
  {
    name: "Sway",
    method: "IBus / wtype",
    status: "Full support",
    notes: "i3-compatible Wayland compositor",
  },
  {
    name: "Hyprland",
    method: "IBus / wtype",
    status: "Full support",
    notes: "Dynamic tiling Wayland compositor",
  },
  {
    name: "river",
    method: "IBus / wtype",
    status: "Full support",
    notes: "Dynamic tiling Wayland compositor",
  },
  {
    name: "XWayland apps",
    method: "xdotool",
    status: "Full support",
    notes: "X11 apps running under Wayland",
  },
];

const setupSteps = [
  {
    step: 1,
    title: "Install IBus",
    description: "Most distributions include IBus by default. If not:",
    command: "sudo apt install ibus ibus-gtk ibus-gtk3",
  },
  {
    step: 2,
    title: "Start IBus Daemon",
    description: "Ensure the IBus daemon is running in your session:",
    command: "ibus-daemon -drx",
  },
  {
    step: 3,
    title: "Run Vocalinux",
    description: "Vocalinux will auto-detect Wayland and configure IBus:",
    command: "vocalinux",
  },
];

export const metadata: Metadata = buildPageMetadata({
  title: "Wayland Voice Dictation Support - GNOME, KDE, Sway | Vocalinux",
  description:
    "Full Wayland support for voice dictation on Linux. Works with GNOME, KDE Plasma, Sway, Hyprland, and other Wayland compositors via IBus integration.",
  path: "/wayland",
  keywords: [
    "wayland voice dictation",
    "GNOME voice typing",
    "KDE speech to text",
    "Sway voice recognition",
    "Hyprland dictation",
    "wayland text injection",
    "linux wayland speech recognition",
    "ibus voice input",
  ],
});

export default function WaylandPage() {
  const articleJsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: "Wayland Voice Dictation Support for Linux",
    description:
      "Complete guide to Vocalinux Wayland support. Voice dictation for GNOME, KDE, Sway, Hyprland, and other Wayland compositors.",
    dateModified: "2026-03-30",
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
    mainEntityOfPage: absoluteUrl("/wayland"),
  };

  return (
    <SeoSubpageShell>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleJsonLd) }}
      />

      <section>
        <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-sm font-medium text-primary">
          <Monitor className="h-4 w-4" />
          Wayland Support
        </p>
        <h1 className="mb-5 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
          Voice Dictation on Wayland
        </h1>
        <p className="mb-8 max-w-4xl text-lg text-muted-foreground">
          Full voice dictation support for modern Wayland compositors. Works with GNOME, KDE Plasma,
          Sway, Hyprland, and more. No X11 required.
        </p>
      </section>

      <section className="mb-12 grid gap-6 sm:grid-cols-3">
        {waylandFeatures.map((feature) => {
          const Icon = feature.icon;
          return (
            <div
              key={feature.title}
              className="rounded-xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800"
            >
              <Icon className="mb-3 h-8 w-8 text-primary" />
              <h3 className="mb-2 font-semibold">{feature.title}</h3>
              <p className="text-sm text-muted-foreground">{feature.description}</p>
            </div>
          );
        })}
      </section>

      <section className="mb-12 rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800">
        <h2 className="mb-6 text-2xl font-bold">Supported Wayland Compositors</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-zinc-200 dark:border-zinc-700">
                <th className="pb-3 pr-4 text-sm font-semibold">Compositor</th>
                <th className="pb-3 pr-4 text-sm font-semibold">Method</th>
                <th className="pb-3 pr-4 text-sm font-semibold">Status</th>
                <th className="pb-3 text-sm font-semibold">Notes</th>
              </tr>
            </thead>
            <tbody className="text-sm">
              {compositorSupport.map((item) => (
                <tr
                  key={item.name}
                  className="border-b border-zinc-100 dark:border-zinc-700/70"
                >
                  <td className="py-3 pr-4 font-medium">{item.name}</td>
                  <td className="py-3 pr-4 text-muted-foreground">{item.method}</td>
                  <td className="py-3 pr-4">
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400">
                      <CheckCircle2 className="h-3 w-3" />
                      {item.status}
                    </span>
                  </td>
                  <td className="py-3 text-muted-foreground">{item.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mb-12">
        <h2 className="mb-6 text-2xl font-bold">Quick Setup Guide</h2>
        <div className="space-y-4">
          {setupSteps.map((step) => (
            <div
              key={step.step}
              className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-700 dark:bg-zinc-800"
            >
              <div className="mb-2 flex items-center gap-3">
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-sm font-bold text-primary-foreground">
                  {step.step}
                </span>
                <h3 className="font-semibold">{step.title}</h3>
              </div>
              <p className="mb-3 ml-10 text-sm text-muted-foreground">{step.description}</p>
              <div className="ml-10 rounded-lg bg-zinc-950 p-3">
                <code className="text-sm text-green-400">{step.command}</code>
              </div>
            </div>
          ))}
        </div>
        <p className="mt-4 text-sm text-muted-foreground">
          If text doesn&apos;t appear, ensure IBus is your active input method (System Settings →
          Keyboard → Input Methods).
        </p>
      </section>

      <section className="mb-12 rounded-2xl border border-blue-200 bg-blue-50 p-6 dark:border-blue-800 dark:bg-blue-900/20">
        <h2 className="mb-3 text-xl font-bold text-blue-800 dark:text-blue-300">
          How Wayland Text Injection Works
        </h2>
        <p className="mb-4 text-sm text-blue-700 dark:text-blue-400">
          Unlike X11 where applications can simulate keyboard input globally, Wayland&apos;s security
          model requires a different approach. Vocalinux uses:
        </p>
        <ul className="space-y-2 text-sm text-blue-700 dark:text-blue-400">
          <li className="inline-flex items-start gap-2">
            <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0" />
            <strong>IBus Engine</strong> — A custom IBus input method that receives text from
            Vocalinux and types it into the focused application
          </li>
          <li className="inline-flex items-start gap-2">
            <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0" />
            <strong>wtype</strong> — Native Wayland typing tool for compositors that support the
            virtual keyboard protocol
          </li>
          <li className="inline-flex items-start gap-2">
            <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0" />
            <strong>X11 Fallback</strong> — xdotool for XWayland applications
          </li>
        </ul>
        <p className="mt-4 text-sm text-blue-700 dark:text-blue-400">
          v0.9.0+ includes clipboard fallback for Wayland compositors without virtual keyboard
          support. Copy-to-clipboard is now disabled by default for privacy - enable in Settings
          if needed.
        </p>
      </section>

      <section className="rounded-2xl border border-zinc-200 bg-zinc-50 p-8 dark:border-zinc-700 dark:bg-zinc-900/60">
        <h2 className="mb-4 text-2xl font-bold">Start Dictating on Wayland</h2>
        <p className="mb-6 text-muted-foreground">
          Vocalinux automatically detects your display server and configures the appropriate text
          injection method. Just install and run.
        </p>
        <div className="flex flex-wrap gap-4">
          <Link
            href="/install/"
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
          >
            Install Now
            <ChevronRight className="h-4 w-4" />
          </Link>
          <Link
            href="/troubleshooting/"
            className="inline-flex items-center gap-2 rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm font-semibold hover:bg-zinc-50 dark:border-zinc-600 dark:bg-zinc-800 dark:hover:bg-zinc-700"
          >
            Troubleshooting Guide
          </Link>
        </div>
      </section>
    </SeoSubpageShell>
  );
}
