import fs from "fs";
import path from "path";

describe("SEO Assets", () => {
  const robotsPath = path.join(process.cwd(), "public", "robots.txt");
  const sitemapPath = path.join(process.cwd(), "public", "sitemap.xml");

  let robotsContent: string;
  let sitemapContent: string;

  beforeAll(() => {
    robotsContent = fs.readFileSync(robotsPath, "utf-8");
    sitemapContent = fs.readFileSync(sitemapPath, "utf-8");
  });

  it("contains sitemap reference in robots.txt", () => {
    expect(robotsContent).toContain("Sitemap: https://vocalinux.com/sitemap.xml");
  });

  it("blocks crawler access to technical paths", () => {
    expect(robotsContent).toContain("Disallow: /api/");
    expect(robotsContent).toContain("Disallow: /_next/");
    expect(robotsContent).toContain("Disallow: /out/");
  });

  it("includes core landing pages in sitemap", () => {
    const expectedUrls = [
      "https://vocalinux.com/",
      "https://vocalinux.com/install/",
      "https://vocalinux.com/install/ubuntu/",
      "https://vocalinux.com/install/fedora/",
      "https://vocalinux.com/install/arch/",
      "https://vocalinux.com/compare/",
    ];

    expectedUrls.forEach((url) => {
      expect(sitemapContent).toContain(`<loc>${url}</loc>`);
    });
  });
});
