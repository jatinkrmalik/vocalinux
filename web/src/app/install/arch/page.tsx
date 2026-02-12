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
  Github,
  Package
} from "lucide-react";

export const metadata: Metadata = {
  title: "Voice Dictation for Arch Linux | AUR Package Available | Vocalinux",
  description: "Install Vocalinux voice dictation on Arch Linux and Manjaro. Available in AUR. 100% offline speech recognition with Whisper AI. Free, open-source, and privacy-focused.",
  keywords: [
    "arch linux voice dictation",
    "speech to text arch",
    "arch voice typing",
    "whisper arch linux",
    "offline dictation arch",
    "manjaro voice recognition",
    "aur vocalinux",
    "linux voice dictation arch"
  ],
  alternates: {
    canonical: "https://vocalinux.com/install/arch",
  },
};

const features = [
  {
    icon: Package,
    title: "AUR Available",
    description: "Install via AUR helper (yay, paru) or manually. Rolling release updates."
  },
  {
    icon: Shield,
    title: "100% Offline",
    description: "Your voice stays local. Perfect for Arch's privacy-conscious users."
  },
  {
    icon: Zap,
    title: "Minimal & Fast",
    description: "Lightweight design aligns with Arch philosophy. Efficient resource usage."
  },
  {
    icon: Cpu,
    title: "GPU Acceleration",
    description: "Vulkan support for AMD, NVIDIA, Intel GPUs. Maximum performance on minimal systems."
  }
];

const installMethods = [
  {
    title: "Method 1: Using an AUR Helper (Recommended)",
    description: "If you use yay, paru, or another AUR helper:",
    code: "yay -S vocalinux"
  },
  {
    title: "Method 2: Manual Installation",
    description: "Clone the repository and install manually:",
    code: "curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/v0.6.1-beta/install.sh -o /tmp/vl.sh && bash /tmp/vl.sh"
  },
  {
    title: "Method 3: From Source (Development)",
    description: "For developers who want the latest git version:",
    code: "git clone https://github.com/jatinkrmalik/vocalinux.git \u0026\u0026 cd vocalinux \u0026\u0026 ./install.sh --dev"
  }
];

const testedVersions = [
  "Arch Linux (Latest)",
  "Manjaro Linux",
  "EndeavourOS",
  "Garuda Linux",
  "ArcoLinux"
];

export default function ArchInstallPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Hero */}
      <section className="relative pt-20 pb-16 md:pt-32 md:pb-24 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-cyan-500/5 to-transparent" />
        <div className="container mx-auto px-4 relative">
          <div className="max-w-4xl mx-auto text-center">
            <div className="inline-flex items-center gap-2 bg-cyan-500/10 text-cyan-600 px-4 py-2 rounded-full text-sm font-medium mb-6">
              <Check className="h-4 w-4" />
              AUR Package Available
            </div>
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
              Voice Dictation for{" "}
              <span className="text-cyan-600">Arch Linux</span>
            </h1>
            <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
              100% offline voice dictation for Arch, Manjaro, and derivatives. 
              Available in AUR. Minimal, fast, and privacy-focused.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" className="gap-2 bg-cyan-600 hover:bg-cyan-700" asChild>
                <a href="#install">
                  <Download className="h-5 w-5" />
                  Install on Arch
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
                  <feature.icon className="h-10 w-10 text-cyan-600 mb-2" />
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

      {/* Installation Methods */}
      <section id="install" className="py-16 md:py-24">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-12">
              Choose Your Installation Method
            </h2>
            <div className="space-y-8">
              {installMethods.map((method, index) => (
                <Card key={index} className="border-0 shadow-sm">
                  <CardHeader>
                    <CardTitle className="text-xl">{method.title}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-muted-foreground">{method.description}</p>
                    <CodeBlock code={method.code} />
                  </CardContent>
                </Card>
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
              Tested on Arch-Based Distros
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

      {/* Why Arch Users */}
      <section className="py-16 md:py-24">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-3xl font-bold text-center mb-12">
              Built for the Arch Philosophy
            </h2>
            <div className="grid md:grid-cols-2 gap-8">
              <Card>
                <CardHeader>
                  <CardTitle>Minimal Dependencies</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    Vocalinux uses whisper.cpp - a minimal, efficient C++ implementation 
                    that aligns with Arch's keep-it-simple philosophy. No bloated Python 
                    environments or unnecessary dependencies.
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Rolling Release Compatible</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    The AUR package stays current with upstream. Get the latest features 
                    and improvements as soon as they're released. No waiting for distribution 
                    maintainers.
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>DIY Configuration</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    Edit configuration files directly. Vocalinux stores settings in 
                    ~/.config/vocalinux/ where you can tweak every aspect. No GUI 
                    limitations - full control for power users.
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Window Manager Support</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    Works perfectly with i3, sway, dwm, bspwm, and any other window manager. 
                    System tray integration for those who use it, but fully functional 
                    without a traditional desktop environment.
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-cyan-600 text-white">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">
            Ready to Install on Arch?
          </h2>
          <p className="text-xl mb-8 opacity-90 max-w-2xl mx-auto">
            Join thousands of Arch users enjoying private, offline voice dictation.
          </p>
          <Button size="lg" variant="secondary" className="gap-2" asChild>
            <a href="#install">
              <Download className="h-5 w-5" />
              Install Vocalinux
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
              <Link href="/install/fedora" className="text-primary hover:underline">
                Fedora <ChevronRight className="inline h-4 w-4" />
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
