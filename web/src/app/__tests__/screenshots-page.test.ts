import fs from "fs";
import path from "path";

/**
 * Structural checks for the screenshots gallery: page source, public assets,
 * nav discoverability, and homepage link. Exercises the real shipped files
 * under web/ rather than re-implementing gallery data in the test.
 */
describe("Screenshots page and assets", () => {
  const webRoot = process.cwd();
  const pagePath = path.join(webRoot, "src/app/screenshots/page.tsx");
  const shellPath = path.join(webRoot, "src/components/seo-subpage-shell.tsx");
  const homePath = path.join(webRoot, "src/app/page.tsx");
  const publicScreenshotsDir = path.join(webRoot, "public/screenshots");

  const expectedAssets = [
    "00-transcription.png",
    "02-system-tray.png",
    "03-log-viewer.png",
    "05-about-view.png",
    "settings-speech-engine.png",
    "settings-recognition.png",
    "settings-audio.png",
    "settings-shortcuts.png",
    "settings-general.png",
    "settings-advanced.png",
  ];

  let pageSource: string;
  let shellSource: string;
  let homeSource: string;

  beforeAll(() => {
    pageSource = fs.readFileSync(pagePath, "utf-8");
    shellSource = fs.readFileSync(shellPath, "utf-8");
    homeSource = fs.readFileSync(homePath, "utf-8");
  });

  it("ships a dedicated /screenshots page module with lightbox gallery", () => {
    expect(fs.existsSync(pagePath)).toBe(true);
    expect(pageSource).toMatch(/export default function ScreenshotsPage/);
    expect(pageSource).toContain('path: "/screenshots"');
    expect(pageSource).toContain("Vocalinux Screenshots");
    expect(pageSource).toContain("ScreenshotGallery");
    const galleryPath = path.join(
      webRoot,
      "src/components/screenshot-gallery.tsx",
    );
    expect(fs.existsSync(galleryPath)).toBe(true);
    const gallerySource = fs.readFileSync(galleryPath, "utf-8");
    expect(gallerySource).toContain('role="dialog"');
    expect(gallerySource).toContain("aria-modal");
    expect(gallerySource).toContain("View larger");
  });

  it("references every public screenshot asset from the page source", () => {
    for (const file of expectedAssets) {
      const assetPath = path.join(publicScreenshotsDir, file);
      expect(fs.existsSync(assetPath)).toBe(true);
      expect(fs.statSync(assetPath).size).toBeGreaterThan(1000);
      expect(pageSource).toContain(`/screenshots/${file}`);
    }
  });

  it("does not embed a full homepage gallery (link-only on home)", () => {
    // Homepage should link to the gallery, not list every settings shot.
    expect(homeSource).toContain('href: "/screenshots/"');
    expect(homeSource).toContain('href="/screenshots/"');
    expect(homeSource).not.toContain("/screenshots/settings-speech-engine.png");
    expect(homeSource).not.toContain("/screenshots/05-about-view.png");
  });

  it("exposes Screenshots in the shared subpage shell nav", () => {
    expect(shellSource).toContain('href: "/screenshots/"');
    expect(shellSource).toContain('label: "Screenshots"');
  });

  it("includes captioned settings and product sections", () => {
    expect(pageSource).toContain("Speech Engine");
    expect(pageSource).toContain("Recognition");
    expect(pageSource).toContain("Audio");
    expect(pageSource).toContain("Shortcuts");
    expect(pageSource).toContain("General");
    expect(pageSource).toContain("Advanced");
    expect(pageSource).toContain("Transcription in action");
    expect(pageSource).toContain("About");
  });
});
