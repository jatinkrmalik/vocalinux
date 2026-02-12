import { Metadata } from "next";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CodeBlock } from "@/components/code-block";
import { 
  Check, 
  Terminal, 
  Shield, 
  Zap, 
  Cpu,
  ChevronRight,
  Download,
  Github
} from "lucide-react";

export const metadata: Metadata = {
  title: "Voice Dictation for Fedora | 100% Offline & Private | Vocalinux",
  description: "Install Vocalinux voice dictation on Fedora 39, 40, and newer. 100% offline speech recognition with Whisper AI. Native Wayland support. Free & open-source.",
  keywords: [
    "fedora voice dictation",
    "speech to text fedora",
    "fedora voice typing",
    "whisper fedora",
    "offline dictation fedora",
    "fedora 40 voice recognition",
    "wayland voice dictation fedora",
    "linux voice dictation fedora"
  ],
  alternates: {
    canonical: "https://vocalinux.com/install/fedora",
  },
};

const features = [
  {
    icon: Shield,
    title: "100% Offline",
    description: "Your voice stays on your Fedora system. Complete privacy with no cloud dependencies."
  },
  {
    icon: Zap,
    title: "Wayland Native",
    description: "Full Wayland support out of the box. Works perfectly on Fedora's default display server."
  },
  {
    icon: Cpu,
    title: "GPU Accelerated",
    description: "Leverage your AMD, NVIDIA, or Intel GPU for fast transcription with Vulkan support."
  },
  {
    icon: Terminal,
    title: "RPM Compatible",
    description: "Works with Fedora's RPM ecosystem. Easy installation via standard tools."
  }
];

const installSteps = [
  {
    step: 1,
    title: "Open Terminal",
    description: "Press Ctrl+Alt+T or search for 'Terminal' in Activities overview",
    code: null
  },
  {
    step: 2,
    title: "Run the Installer",
    description: "The installer will automatically detect Fedora and install the necessary dependencies:",
    code: "curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/v0.6.1-beta/install.sh -o /tmp/vl.sh && bash /tmp/vl.sh"
  },
  {
    step: 3,
    title: "Choose Your Engine",
    description: "Select whisper.cpp (recommended) for best performance, or VOSK for lightweight operation. The installer handles all dependencies automatically."
  },
  {
    step: 4,
    title: "Start Using Vocalinux",
    description: "Launch Vocalinux and start dictating:",
    code: "vocalinux"
  }
];

const testedVersions = [
  "Fedora 40 (Latest)",
  "Fedora 39",
  "Fedora 38",
  "Fedora Silverblue",
  "Fedora Kinoite"
];

export default function FedoraInstallPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Hero */}
      <section className="relative pt-20 pb-16 md:pt-32 md:pb-24 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 to-transparent" />
        <div className="container mx-auto px-4 relative">
          <div className="max-w-4xl mx-auto text-center">
            <div className="inline-flex items-center gap-2 bg-blue-500/10 text-blue-600 px-4 py-2 rounded-full text-sm font-medium mb-6">
              <Check className="h-4 w-4" />
              Optimized for Fedora
            </div>
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
              Voice Dictation for{" "}
              <span className="text-blue-600">Fedora</span>
            </h1>
            <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
              100% offline voice dictation for Fedora 39, 40, and newer. 
              Native Wayland support with GPU acceleration.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" className="gap-2 bg-blue-600 hover:bg-blue-700" asChild>
                <a href="#install">
                  <Download className="h-5 w-5" />
                  Install on Fedora
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

      {/* Features */}
      <section className="py-16 bg-muted/50">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <Card key={index} className="border-0 shadow-sm">
                <CardHeader>
                  <feature.icon className="h-10 w-10 text-blue-600 mb-2" />
                  <CardTitle className="text-lg">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">{feature.description}</p>
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
              Install on Fedora
            </h2>
            <div className="space-y-8">
              {installSteps.map((item, index) => (
                <div key={index} className="flex gap-4">
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold">
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
              Tested on Fedora Versions
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

      {/* Why Fedora Users Love It */}
      <section className="py-16 md:py-24">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-12">
              Perfect for Fedora's Philosophy
            </h2>
            <div className="grid md:grid-cols-2 gap-8">
              <Card>
                <CardHeader>
                  <CardTitle>Open Source Values</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    Just like Fedora, Vocalinux is 100% open source under GPL-3.0. 
                    No proprietary blobs, no hidden telemetry - just transparent, 
                    auditable code that respects your freedom.
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Bleeding Edge Performance</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    Vocalinux leverages whisper.cpp for cutting-edge speech recognition 
                    performance. Combined with Fedora's modern kernel and Mesa drivers, 
                    you get the best possible experience on AMD, Intel, and NVIDIA hardware.
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Wayland First</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    Fedora's default Wayland display server is fully supported. 
                    Vocalinux integrates seamlessly with GNOME on Wayland, 
                    providing smooth performance without XWayland workarounds.
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Enterprise Ready</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    Vocalinux works great on Fedora Workstation and Server. 
                    Perfect for documentation, writing reports, or any text input 
                    in enterprise environments where privacy is paramount.
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-blue-600 text-white">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">
            Ready to Try Voice Dictation on Fedora?
          </h2>
          <p className="text-xl mb-8 opacity-90 max-w-2xl mx-auto">
            Join the Fedora community using Vocalinux for private, offline voice dictation.
          </p>
          <Button size="lg" variant="secondary" className="gap-2" asChild>
            <a href="#install">
              <Download className="h-5 w-5" />
              Install on Fedora
            </a>
          </Button>
        </div>
      </section>

      {/* Other Distros */}
      <section className="py-12 border-t">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto text-center">
            <p className="text-muted-foreground mb-4">Using a different Linux distribution?</p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/install/ubuntu" className="text-primary hover:underline">
                Ubuntu <ChevronRight className="inline h-4 w-4" />
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
