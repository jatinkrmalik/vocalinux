import Link from "next/link";
import { type Metadata } from "next";
import { buildPageMetadata } from "@/lib/seo";

const installCommand =
  "curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh -o /tmp/vl.sh && bash /tmp/vl.sh --interactive";

const distroGuides = [
  {
    name: "Ubuntu",
    href: "/install/ubuntu/",
    description:
      "Install offline voice dictation on Ubuntu 22.04+ with GNOME, KDE, X11, or Wayland.",
  },
  {
    name: "Fedora",
    href: "/install/fedora/",
    description:
      "Set up speech-to-text on Fedora Workstation and Silverblue with distro-specific notes.",
  },
  {
    name: "Arch Linux",
    href: "/install/arch/",
    description:
      "Install Vocalinux on Arch, Manjaro, and EndeavourOS with package prerequisites and tips.",
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
    <main className="min-h-screen bg-gradient-to-b from-zinc-50 to-white px-4 pb-16 pt-24 dark:from-zinc-900 dark:to-zinc-950 sm:px-6 sm:pt-32">
      <section className="mx-auto max-w-5xl text-center">
        <p className="mb-4 inline-flex rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-sm font-medium text-primary">
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
          <p className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-400">
            Recommended interactive install
          </p>
          <code className="block overflow-x-auto whitespace-pre-wrap break-all text-sm text-green-400 sm:text-base">
            {installCommand}
          </code>
        </div>
      </section>

      <section className="mx-auto mt-14 grid max-w-5xl gap-6 md:grid-cols-3">
        {distroGuides.map((guide) => (
          <Link
            key={guide.href}
            href={guide.href}
            className="group rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm transition-all hover:-translate-y-1 hover:shadow-lg dark:border-zinc-700 dark:bg-zinc-800"
          >
            <h2 className="mb-3 text-2xl font-semibold">{guide.name}</h2>
            <p className="mb-5 text-sm text-muted-foreground">{guide.description}</p>
            <span className="text-sm font-semibold text-primary group-hover:underline">
              Read {guide.name} guide
            </span>
          </Link>
        ))}
      </section>

      <section className="mx-auto mt-16 max-w-5xl rounded-2xl border border-zinc-200 bg-zinc-50 p-8 dark:border-zinc-700 dark:bg-zinc-900/60">
        <h2 className="mb-4 text-2xl font-bold">After Installation</h2>
        <ul className="space-y-3 text-muted-foreground">
          <li>Launch with <code className="rounded bg-zinc-200 px-1.5 py-0.5 dark:bg-zinc-800">vocalinux</code>.</li>
          <li>Double-tap Ctrl to start or stop dictation in any text field.</li>
          <li>Choose whisper.cpp for speed, Whisper for maximum model compatibility, or VOSK for low-RAM systems.</li>
        </ul>
        <p className="mt-6 text-sm text-muted-foreground">
          Need help choosing an engine? See the <Link href="/compare/" className="font-semibold text-primary hover:underline">speech engine comparison</Link>.
        </p>
      </section>
    </main>
  );
}
