# SEO Audit and Optimization Plan (Web)

## Scope

- Reviewed technical SEO, on-page SEO, schema markup, crawl directives, and internal linking across `web/`.
- Focused on production-impacting gaps that influence indexation, topical relevance, and click-through potential.

## Baseline Findings

1. **Thin crawlable surface area**
   - Only the homepage was represented in `sitemap.xml`.
   - No dedicated landing pages for high-intent distro queries (Ubuntu/Fedora/Arch install intent).

2. **Structured data was too homepage-specific at layout level**
   - FAQ/HowTo/SoftwareApplication JSON-LD lived in `layout.tsx`, causing it to render site-wide instead of page-specific.

3. **Internal link graph underused long-tail opportunities**
   - Homepage had strong conversion UX but limited keyword-targeted internal routes for search intent clusters.

4. **Robots directives were minimal**
   - `robots.txt` allowed everything without guardrails for technical paths and parameterized URL patterns.

5. **Metadata consistency opportunities**
   - Metadata quality was good overall, but canonical/language consistency and reusable metadata generation could be improved.

## Implemented Improvements

### 1) Technical SEO foundation

- Added reusable metadata utility: `src/lib/seo.ts`
  - canonical URL normalization
  - Open Graph + Twitter defaults
  - centralized site constants

- Updated `src/app/layout.tsx`
  - cleaner site-wide metadata defaults
  - stronger keyword coverage and canonical consistency
  - referrer and robots directives preserved/improved
  - site-wide JSON-LD reduced to Organization + WebSite only

### 2) Intent-focused landing page expansion

- Added install hub page: `src/app/install/page.tsx`
- Added static distro pages via dynamic route + `generateStaticParams`:
  - `src/app/install/[distro]/page.tsx`
  - Targets: Ubuntu, Fedora, Arch
  - Includes distro-specific prerequisites, setup notes, and checklist
  - Includes page-specific HowTo JSON-LD

- Added engine comparison page:
  - `src/app/compare/page.tsx`
  - Includes comparison table (whisper.cpp vs Whisper vs VOSK)
  - Includes Article JSON-LD

### 3) Homepage topical reinforcement + internal links

- Updated key headings in `src/app/page.tsx` to better align with search intent:
  - speech-to-text phrasing
  - Linux dictation terminology

- Added homepage guide hub section linking to:
  - `/install/ubuntu/`
  - `/install/fedora/`
  - `/install/arch/`
  - `/compare/`

- Added homepage-specific structured data (SoftwareApplication + FAQPage + HowTo)
  - keeps rich-result markup aligned with the page where content actually appears

### 4) Crawl and indexation updates

- Updated `public/robots.txt`
  - added disallow rules for `/api/`, `/_next/`, `/out/`, query-string duplicates
  - added `Host` and retained sitemap pointer

- Expanded `public/sitemap.xml`
  - includes new landing pages and updated `lastmod`

### 5) Regression coverage

- Added SEO asset tests: `src/app/__tests__/seo-assets.test.ts`
  - validates robots directives and sitemap URL coverage

## Expected SEO Impact

- Better indexing depth via dedicated landing pages mapped to high-intent Linux distro queries.
- Improved topical authority through intent clusters (install + engine comparison).
- Cleaner structured data semantics by aligning schema to relevant pages.
- Reduced crawl waste and duplicate URL risk from parameterized paths.
- Stronger internal link distribution from homepage to new SEO entry points.

## Recommended Monitoring (Post-deploy)

1. Track impressions/clicks for:
   - `ubuntu voice dictation`
   - `fedora speech to text`
   - `arch linux voice typing`
   - `whisper.cpp vs vosk`
2. Validate rich results and schema parsing in Search Console.
3. Watch Core Web Vitals on newly created pages for mobile and desktop.
4. Compare organic landing-page distribution before/after rollout.
