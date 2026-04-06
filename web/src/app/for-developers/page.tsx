import Link from "next/link";
import { type Metadata } from "next";
import {
  Braces,
  CheckCircle2,
  ChevronRight,
  Code2,
  FileCode2,
  FileText,
  MessageSquare,
  Terminal,
  Zap,
} from "lucide-react";
import { SeoSubpageShell } from "@/components/seo-subpage-shell";
import { absoluteUrl, buildPageMetadata } from "@/lib/seo";

const useCases = [
  {
    title: "Code Comments & Documentation",
    description:
      "Dictate inline comments, JSDoc, docstrings, and README sections without leaving your editor.",
    example: "This function validates user input and returns true if valid",
    icon: FileCode2,
    iconColor: "text-blue-500",
    iconBg: "bg-blue-100 dark:bg-blue-900/30",
  },
  {
    title: "Git Commit Messages",
    description:
      "Speak your commit messages naturally—no more brief, unhelpful commits because typing is slow.",
    example: "fix authentication timeout when server is under heavy load",
    icon: Terminal,
    iconColor: "text-orange-500",
    iconBg: "bg-orange-100 dark:bg-orange-900/30",
  },
  {
    title: "Pull Request Descriptions",
    description:
      "Write detailed PR descriptions explaining your changes, rationale, and testing approach.",
    example: "This PR refactors the user service to improve testability and adds error handling",
    icon: FileText,
    iconColor: "text-purple-500",
    iconBg: "bg-purple-100 dark:bg-purple-900/30",
  },
  {
    title: "Technical Documentation",
    description:
      "Create API docs, architecture guides, and technical specifications at speaking speed.",
    example: "The API accepts a JSON payload with the following fields",
    icon: FileText,
    iconColor: "text-emerald-500",
    iconBg: "bg-emerald-100 dark:bg-emerald-900/30",
  },
  {
    title: "Code Review Comments",
    description:
      "Write thorough code review feedback without the fatigue of typing detailed explanations.",
    example: "Consider extracting this logic into a separate function for reusability",
    icon: MessageSquare,
    iconColor: "text-rose-500",
    iconBg: "bg-rose-100 dark:bg-rose-900/30",
  },
  {
    title: "Pair Programming Notes",
    description:
      "Dictate notes while pairing—keep your hands on the keyboard for code, use voice for meta.",
    example: "Remember to add unit tests for the edge case we just discussed",
    icon: Zap,
    iconColor: "text-amber-500",
    iconBg: "bg-amber-100 dark:bg-amber-900/30",
  },
];

const voiceCommands = [
  { command: "new line", action: "Insert line break" },
  { command: "tab", action: "Insert tab character" },
  { command: "open parenthesis", action: "Type (" },
  { command: "close parenthesis", action: "Type )" },
  { command: "open bracket", action: "Type [" },
  { command: "close bracket", action: "Type ]" },
  { command: "open brace", action: "Type {" },
  { command: "close brace", action: "Type }" },
  { command: "equals", action: "Type =" },
  { command: "semicolon", action: "Type ;" },
  { command: "colon", action: "Type :" },
  { command: "quote", action: "Type \"" },
  { command: "single quote", action: "Type '" },
  { command: "underscore", action: "Type _" },
  { command: "slash", action: "Type /" },
  { command: "backslash", action: "Type \\" },
  { command: "period / dot", action: "Type ." },
  { command: "comma", action: "Type ," },
];

const benefits = [
  {
    title: "Reduce RSI Risk",
    description: "Developers type 8+ hours daily. Voice dictation lets you rest your hands while staying productive.",
  },
  {
    title: "Maintain Flow State",
    description: "Speak your thoughts as they come—no context switching to the keyboard for comments and docs.",
  },
  {
    title: "Better Documentation",
    description: "When documentation is easy to write, you write more of it. Thorough docs become the default.",
  },
  {
    title: "Universal Compatibility",
    description: "Works in VS Code, JetBrains IDEs, Vim, terminal, browser—every Linux application.",
  },
];

export const metadata: Metadata = buildPageMetadata({
  title: "Voice Dictation for Developers & Coders | Vocalinux",
  description:
    "Dictate code comments, documentation, and commit messages hands-free. Voice dictation for Linux developers—works in VS Code, JetBrains, terminal, and all apps.",
  path: "/for-developers",
  keywords: [
    "voice dictation for developers",
    "voice coding Linux",
    "dictate code comments",
    "hands-free programming",
    "developer productivity voice",
    "code documentation voice",
    "Linux voice programming",
    "VS Code voice dictation",
  ],
});

export default function ForDevelopersPage() {
  const articleJsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: "Voice Dictation for Developers & Coders",
    description:
      "How Linux developers use Vocalinux for code comments, documentation, and commit messages.",
    dateModified: "2026-02-22",
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
    mainEntityOfPage: absoluteUrl("/for-developers"),
  };

  return (
    <SeoSubpageShell>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(articleJsonLd) }}
      />

      <section>
        <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-1.5 text-sm font-medium text-primary">
          <Code2 className="h-4 w-4" />
          For Developers
        </p>
        <h1 className="mb-5 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
          Voice Dictation for Developers
        </h1>
        <p className="mb-8 max-w-4xl text-lg text-muted-foreground">
          Write code comments, documentation, commit messages, and more—hands-free. Keep your hands
          on the keyboard for code, use your voice for everything else.
        </p>
      </section>

      <section className="mb-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {benefits.map((benefit) => (
          <div
            key={benefit.title}
            className="rounded-xl border border-zinc-200 bg-white p-5 text-center dark:border-zinc-700 dark:bg-zinc-800"
          >
            <h3 className="mb-2 font-semibold">{benefit.title}</h3>
            <p className="text-sm text-muted-foreground">{benefit.description}</p>
          </div>
        ))}
      </section>

      <section className="mb-12">
        <h2 className="mb-6 text-2xl font-bold">Developer Use Cases</h2>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {useCases.map((useCase) => {
            const Icon = useCase.icon;
            return (
              <article
                key={useCase.title}
                className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-700 dark:bg-zinc-800"
              >
                <div className="mb-3 flex items-center gap-3">
                  <div className={`rounded-lg p-2 ${useCase.iconBg}`}>
                    <Icon className={`h-4 w-4 ${useCase.iconColor}`} />
                  </div>
                  <h3 className="font-semibold">{useCase.title}</h3>
                </div>
                <p className="mb-3 text-sm text-muted-foreground">{useCase.description}</p>
                <div className="rounded-lg bg-zinc-950 p-3">
                  <code className="text-xs text-green-400">&quot;{useCase.example}&quot;</code>
                </div>
              </article>
            );
          })}
        </div>
      </section>

      <section className="mb-12 rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800">
        <h2 className="mb-4 text-2xl font-bold">Helpful Voice Commands for Coding</h2>
        <p className="mb-4 text-sm text-muted-foreground">
          Use these voice commands for punctuation and symbols commonly used in code:
        </p>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {voiceCommands.map((cmd) => (
            <div
              key={cmd.command}
              className="flex items-center justify-between rounded-lg border border-zinc-100 bg-zinc-50 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-900"
            >
              <kbd className="rounded bg-zinc-200 px-2 py-0.5 text-xs font-mono dark:bg-zinc-700">
                &quot;{cmd.command}&quot;
              </kbd>
              <span className="text-xs text-muted-foreground">{cmd.action}</span>
            </div>
          ))}
        </div>
        <p className="mt-4 text-sm text-muted-foreground">
          See the <Link href="/shortcuts/" className="text-primary hover:underline">full voice commands reference</Link> for more.
        </p>
      </section>

      <section className="mb-12 rounded-2xl border border-blue-200 bg-blue-50 p-6 dark:border-blue-800 dark:bg-blue-900/20">
        <h2 className="mb-3 text-xl font-bold text-blue-800 dark:text-blue-300">
          Not Voice Coding—Voice Documentation
        </h2>
        <p className="text-sm text-blue-700 dark:text-blue-400">
          Vocalinux is designed for <strong>dictating text</strong>, not writing code syntax. For
          actual code, your keyboard is still faster. But for comments, docs, messages, and
          notes—voice is a game-changer. Use both together for maximum productivity.
        </p>
      </section>

      <section className="mb-12 rounded-2xl border border-zinc-200 bg-white p-6 dark:border-zinc-700 dark:bg-zinc-800">
        <h2 className="mb-4 text-2xl font-bold">Works in Every IDE</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          {[
            "VS Code",
            "JetBrains (IntelliJ, PyCharm, WebStorm)",
            "Vim / Neovim",
            "Emacs",
            "Sublime Text",
            "Terminal / Shell",
            "GitHub Web",
            "GitLab",
            "Jupyter Notebooks",
          ].map((ide) => (
            <div
              key={ide}
              className="flex items-center gap-2 rounded-lg border border-zinc-100 bg-zinc-50 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-900"
            >
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <span className="text-sm">{ide}</span>
            </div>
          ))}
        </div>
        <p className="mt-4 text-sm text-muted-foreground">
          Vocalinux works system-wide. If the app accepts text input, Vocalinux can dictate into it.
        </p>
      </section>

      <section className="rounded-2xl border border-zinc-200 bg-zinc-50 p-8 dark:border-zinc-700 dark:bg-zinc-900/60">
        <h2 className="mb-4 text-2xl font-bold">Start Dictating Your Docs</h2>
        <p className="mb-6 text-muted-foreground">
          Install Vocalinux and start writing better documentation with less effort. Your future
          self (and your team) will thank you.
        </p>
        <div className="flex flex-wrap gap-4">
          <Link
            href="/install/"
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground dark:text-black hover:bg-primary/90"
          >
            Install Now
            <ChevronRight className="h-4 w-4" />
          </Link>
          <Link
            href="/rsi-prevention/"
            className="inline-flex items-center gap-2 rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm font-semibold hover:bg-zinc-50 dark:border-zinc-600 dark:bg-zinc-800 dark:hover:bg-zinc-700"
          >
            RSI Prevention
          </Link>
        </div>
      </section>
    </SeoSubpageShell>
  );
}
