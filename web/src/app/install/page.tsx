import Link from "next/link";
import { type Metadata } from "next";
import { ChevronRight, Cpu, Laptop, Sparkles, Terminal } from "lucide-react";
import { SeoSubpageShell } from "@/components/seo-subpage-shell";
import { buildPageMetadata } from "@/lib/seo";

const installCommand =
  "curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh -o /tmp/vl.sh && bash /tmp/vl.sh --interactive";

const distroGuides = [
  {
    name: "Ubuntu",
    href: "/install/ubuntu/",
    description:
      "Install offline voice dictation on Ubuntu 22.04+ with GNOME, KDE, X11, or Wayland.",
    icon: Laptop,
    accent: "from-orange-500/15 to-amber-500/10",
    iconColor: "text-orange-500",
  },
  {
    name: "Fedora",
    href: "/install/fedora/",
    description:
      "Set up speech-to-text on Fedora Workstation and Silverblue with distro-specific notes.",
    icon: Sparkles,
    accent: "from-blue-500/15 to-cyan-500/10",
    iconColor: "text-blue-500",
  },
  {
    name: "Arch Linux",
    href: "/install/arch/",
    description:
      "Install Vocalinux on Arch, Manjaro, and EndeavourOS with package prerequisites and tips.",
    icon: Cpu,
    accent: "from-emerald-500/15 to-teal-500/10",
    iconColor: "text-emerald-500",
  },
];

export const metadata: Metadata = buildPageMetadata({
  title: "Install Voice Dictation on Linux (Ubuntu, Fedora, Arch)",
  description:
    "Step-by-step Linux voice dictation installation guides for Ubuntu, Fedora, and Arch. Install Vocalinux in minutes and start offline speech-to-text.",
  path: "/install",
  keywords: [
    "install voice dictation linux",
    "linux speech to text setup",
    "ubuntu voice typing install",
    "fedora speech recognition",
    "arch linux dictation",
  ],
});

export default function InstallGuidesPage() {
  return (
    <SeoSubpageShell>
      <section className="text-center">
        <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-sm font-medium text-primary">
          <Sparkles className="h-4 w-4" />
          Linux Installation Guides
        </p>
        <h1 className="mb-6 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
          Install Voice Dictation on Linux
        </h1>
        <p className="mx-auto mb-8 max-w-3xl text-lg text-muted-foreground">
          Pick your distro guide and follow a proven setup flow for offline speech-to-text on Linux.
          Every guide is optimized for real desktop usage, not just terminal demos.
        </p>

        <div className="rounded-2xl border border-zinc-200 bg-zinc-950 p-6 text-left shadow-lg dark:border-zinc-700">
          <p className="mb-3 inline-flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-zinc-400">
            <Terminal className="h-4 w-4 text-green-400" />
            Recommended interactive install
          </p>
          <code className="block overflow-x-auto whitespace-pre-wrap break-all text-sm text-green-400 sm:text-base">
            {installCommand}
          </code>
        </div>

        <div className="mt-6 rounded-2xl border border-zinc-200 bg-white p-6 text-left shadow-sm dark:border-zinc-700 dark:bg-zinc-800">
          <h2 className="mb-2 text-xl font-semibold">AppImage (portable)</h2>
          <p className="mb-3 text-sm text-muted-foreground">
            Prefer a single file with no installer? Download{" "}
            <code className="rounded bg-zinc-100 px-1.5 py-0.5 text-xs dark:bg-zinc-900">
              Vocalinux-&lt;version&gt;-x86_64.AppImage
            </code>{" "}
            or{" "}
            <code className="rounded bg-zinc-100 px-1.5 py-0.5 text-xs dark:bg-zinc-900">
              Vocalinux-&lt;version&gt;-aarch64.AppImage
            </code>{" "}
            from{" "}
            <a
              href="https://github.com/jatinkrmalik/vocalinux/releases"
              className="font-semibold text-primary hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              GitHub Releases
            </a>{" "}
            (new tags and nightlies). Then:
          </p>
          <code className="mb-3 block overflow-x-auto whitespace-pre-wrap break-all rounded-lg border border-zinc-800 bg-zinc-950 p-4 text-sm text-green-400">
            chmod +x Vocalinux-&lt;version&gt;-x86_64.AppImage
            {"\n"}
            ./Vocalinux-&lt;version&gt;-x86_64.AppImage
          </code>
          <p className="text-sm text-muted-foreground">
            The host still needs text-injection tools (
            <code className="rounded bg-zinc-100 px-1 py-0.5 text-xs dark:bg-zinc-900">
              xdotool
            </code>
            ,{" "}
            <code className="rounded bg-zinc-100 px-1 py-0.5 text-xs dark:bg-zinc-900">
              wtype
            </code>
            , or{" "}
            <code className="rounded bg-zinc-100 px-1 py-0.5 text-xs dark:bg-zinc-900">
              ydotool
            </code>
            ), same as a PyPI install. Full guide:{" "}
            <a
              href="https://github.com/jatinkrmalik/vocalinux/blob/main/docs/INSTALL.md#appimage"
              className="font-semibold text-primary hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              INSTALL.md
            </a>
            .
          </p>
        </div>
      </section>

      <section className="mt-14 grid gap-6 md:grid-cols-3">
        {distroGuides.map((guide) => {
          const Icon = guide.icon;
          return (
            <Link
              key={guide.href}
              href={guide.href}
              className="group rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm transition-all hover:-translate-y-1 hover:shadow-lg dark:border-zinc-700 dark:bg-zinc-800"
            >
              <div
                className={`mb-4 inline-flex rounded-xl bg-gradient-to-br p-3 ${guide.accent}`}
              >
                <Icon className={`h-6 w-6 ${guide.iconColor}`} />
              </div>
              <h2 className="mb-3 text-2xl font-semibold">{guide.name}</h2>
              <p className="mb-5 text-sm text-muted-foreground">{guide.description}</p>
              <span className="inline-flex items-center gap-1 text-sm font-semibold text-primary group-hover:underline">
                Read {guide.name} guide
                <ChevronRight className="h-4 w-4" />
              </span>
            </Link>
          );
        })}
      </section>

      <section className="mt-16 rounded-2xl border border-zinc-200 bg-zinc-50 p-8 dark:border-zinc-700 dark:bg-zinc-900/60">
        <h2 className="mb-4 text-2xl font-bold">After Installation</h2>
        <ul className="space-y-3 text-muted-foreground">
          <li>
            Launch with
            <code className="ml-1.5 rounded bg-zinc-200 px-1.5 py-0.5 dark:bg-zinc-800">vocalinux</code>.
          </li>
          <li>Use toggle mode (double-tap Ctrl) or push-to-talk mode to control dictation in any text field.</li>
          <li>
            Choose whisper.cpp for speed, Whisper for maximum model compatibility, or VOSK for
            low-RAM systems.
          </li>
        </ul>
        <p className="mt-6 text-sm text-muted-foreground">
          Need help choosing an engine? See the
          <Link href="/compare/" className="ml-1 font-semibold text-primary hover:underline">
            speech engine comparison
          </Link>
          .
        </p>
      </section>
    </SeoSubpageShell>
  );
}
