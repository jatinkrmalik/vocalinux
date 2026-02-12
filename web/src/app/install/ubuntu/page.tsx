import { Metadata } from "next";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { CodeBlock } from "@/components/code-block";
import { 
  Check, 
  Terminal, 
  Shield, 
  Zap, 
  Monitor,
  Cpu,
  ChevronRight,
  Download,
  Github
} from "lucide-react";

export const metadata: Metadata = {
  title: "Voice Dictation for Ubuntu | 100% Offline & Private | Vocalinux",
  description: "Install Vocalinux voice dictation on Ubuntu 22.04, 24.04, and newer. 100% offline speech recognition with Whisper AI. Works on GNOME, KDE, and all Ubuntu flavors. Free & open-source.",
  keywords: [
    "ubuntu voice dictation",
    "speech to text ubuntu",
    "ubuntu voice typing",
    "whisper ubuntu",
    "offline dictation ubuntu",
    "ubuntu 22.04 voice recognition",
    "ubuntu 24.04 speech to text",
    "linux voice dictation ubuntu"
  ],
  alternates: {
    canonical: "https://vocalinux.com/install/ubuntu",
  },
  openGraph: {
    title: "Voice Dictation for Ubuntu | 100% Offline & Private | Vocalinux",
    description: "Install Vocalinux voice dictation on Ubuntu. 100% offline speech recognition with Whisper AI. Free & open-source.",
    url: "https://vocalinux.com/install/ubuntu",
  },
};

const features = [
  {
    icon: Shield,
    title: "100% Offline",
    description: "Your voice never leaves your Ubuntu machine. Complete privacy guaranteed."
  },
  {
    icon: Zap,
    title: "Double-Tap Ctrl",
    description: "Just double-tap Ctrl to start dictating in any Ubuntu application."
  },
  {
    icon: Cpu,
    title: "GPU Accelerated",
    description: "Works with NVIDIA, AMD, and Intel GPUs for lightning-fast transcription."
  },
  {
    icon: Monitor,
    title: "All Ubuntu Flavors",
    description: "Ubuntu, Kubuntu, Xubuntu, Ubuntu MATE - all fully supported."
  }
];

const installSteps = [
  {
    step: 1,
    title: "Open Terminal",
    description: "Press Ctrl+Alt+T or search for 'Terminal' in Activities",
    code: null
  },
  {
    step: 2,
    title: "Run the Installer",
    description: "Copy and paste this command (it's one line):",
    code: "curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/v0.6.1-beta/install.sh -o /tmp/vl.sh && bash /tmp/vl.sh"
  },
  {
    step: 3,
    title: "Follow the Prompts",
    description: "The interactive installer will guide you through choosing your speech engine (whisper.cpp recommended), model size, and other options. Takes about 1-2 minutes."
  },
  {
    step: 4,
    title: "Launch Vocalinux",
    description: "After installation, either:",
    code: "vocalinux"
  }
];

const testedVersions = [
  "Ubuntu 24.04 LTS (Noble Numbat)",
  "Ubuntu 22.04 LTS (Jammy Jellyfish)",
  "Ubuntu 23.10 (Mantic Minotaur)",
  "Kubuntu 24.04",
  "Xubuntu 22.04",
  "Ubuntu MATE 23.04"
];

export default function UbuntuInstallPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <section className="relative pt-20 pb-16 md:pt-32 md:pb-24 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent" />
        <div className="container mx-auto px-4 relative">
          <div className="max-w-4xl mx-auto text-center">
            <div className="inline-flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full text-sm font-medium mb-6">
              <Check className="h-4 w-4" />
              Optimized for Ubuntu
            </div>
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
              Voice Dictation for{" "}
              <span className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                Ubuntu
              </span>
            </h1>
            <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
              100% offline voice dictation for Ubuntu 22.04, 24.04, and newer. 
              Privacy-first speech recognition that works in any application.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" className="gap-2" asChild>
                <a href="#install">
                  <Download className="h-5 w-5" />
                  Install on Ubuntu
                </a>
              </Button>
              <Button size="lg" variant="outline" className="gap-2" asChild>
                <Link href="https://github.com/jatinkrmalik/vocalinux" target="_blank">
                  <Github className="h-5 w-5" />
                  View on GitHub
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-16 bg-muted/50">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <Card key={index} className="border-0 shadow-sm">
                <CardHeader>
                  <feature.icon className="h-10 w-10 text-primary mb-2" />
                  <CardTitle className="text-lg">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>{feature.description}</CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Installation Steps */}
      <section id="install" className="py-16 md:py-24">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-12">
              Install on Ubuntu in 4 Steps
            </h2>
            <div className="space-y-8">
              {installSteps.map((item, index) => (
                <div key={index} className="flex gap-4">
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                    {item.step}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold mb-2">{item.title}</h3>
                    <p className="text-muted-foreground mb-4">{item.description}</p>
                    {item.code && (
                      <CodeBlock code={item.code} />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Tested Versions */}
      <section className="py-16 bg-muted/50">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-2xl font-bold text-center mb-8">
              Tested on These Ubuntu Versions
            </h2>
            <div className="grid sm:grid-cols-2 gap-4">
              {testedVersions.map((version, index) => (
                <div key={index} className="flex items-center gap-3 bg-background p-4 rounded-lg">
                  <Check className="h-5 w-5 text-green-500 flex-shrink-0" />
                  <span>{version}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Why Vocalinux */}
      <section className="py-16 md:py-24">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-12">
              Why Ubuntu Users Choose Vocalinux
            </h2>
            <div className="grid md:grid-cols-2 gap-8">
              <Card>
                <CardHeader>
                  <CardTitle>Privacy First</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    Unlike cloud-based dictation tools, Vocalinux processes everything locally on your Ubuntu machine. 
                    Your voice data never leaves your computer, making it perfect for sensitive work, medical transcription, 
                    or any situation where privacy matters.
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Native Ubuntu Integration</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    Vocalinux integrates seamlessly with Ubuntu's desktop environment. It works with both X11 and Wayland, 
                    supports all desktop flavors (GNOME, KDE, XFCE), and follows Ubuntu's system conventions.
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Works Everywhere</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    Use voice dictation in any Ubuntu application - LibreOffice Writer, Firefox, Chrome, VS Code, 
                    Terminal, Thunderbird, and more. If it accepts text input, Vocalinux works with it.
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Open Source & Free</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    Licensed under GPL-3.0, Vocalinux is completely free with no premium tiers, no subscriptions, 
                    and no hidden costs. You get the full feature set without paying a cent.
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-primary text-primary-foreground">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">
            Ready to Start Dictating on Ubuntu?
          </h2>
          <p className="text-xl mb-8 opacity-90 max-w-2xl mx-auto">
            Join thousands of Ubuntu users who have discovered the power of offline voice dictation.
          </p>
          <Button size="lg" variant="secondary" className="gap-2" asChild>
            <a href="#install">
              <Download className="h-5 w-5" />
              Install Vocalinux Now
            </a>
          </Button>
        </div>
      </section>

      {/* Other Distros */}
      <section className="py-12 border-t">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto text-center">
            <p className="text-muted-foreground mb-4">
              Using a different Linux distribution?
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/install/fedora" className="text-primary hover:underline">
                Fedora <ChevronRight className="inline h-4 w-4" />
              </Link>
              <Link href="/install/arch" className="text-primary hover:underline">
                Arch Linux <ChevronRight className="inline h-4 w-4" />
              </Link>
              <Link href="/" className="text-primary hover:underline">
                All Distros <ChevronRight className="inline h-4 w-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
