import fs from 'fs';
import path from 'path';

describe('_headers File - Cache and Security Headers', () => {
  const headersPath = path.join(process.cwd(), 'public', '_headers');
  let headersContent: string;

  beforeAll(() => {
    headersContent = fs.readFileSync(headersPath, 'utf-8');
  });

  it('exists in the public directory', () => {
    expect(fs.existsSync(headersPath)).toBe(true);
  });

  it('contains cache headers for static assets', () => {
    expect(headersContent).toContain('Cache-Control');
  });

  describe('Static Assets Caching', () => {
    it('sets long cache for _next/static files (1 year)', () => {
      expect(headersContent).toContain('/_next/static/*');
      expect(headersContent).toContain('max-age=31536000');
      expect(headersContent).toContain('immutable');
    });

    it('caches font files for 1 year', () => {
      expect(headersContent).toContain('.woff');
      expect(headersContent).toContain('.woff2');
      expect(headersContent).toContain('.ttf');
      expect(headersContent).toContain('.otf');
    });

    it('caches image files for 1 year', () => {
      expect(headersContent).toContain('.png');
      expect(headersContent).toContain('.jpg');
      expect(headersContent).toContain('.jpeg');
      expect(headersContent).toContain('.gif');
      expect(headersContent).toContain('.svg');
      expect(headersContent).toContain('.ico');
      expect(headersContent).toContain('.webp');
      expect(headersContent).toContain('.avif');
    });
  });

  describe('HTML and Dynamic Content', () => {
    it('sets short cache for HTML files with revalidation', () => {
      expect(headersContent).toContain('/*.html');
      expect(headersContent).toContain('max-age=0');
      expect(headersContent).toContain('must-revalidate');
    });

    it('sets 24-hour cache for JSON files', () => {
      expect(headersContent).toContain('/*.json');
      expect(headersContent).toContain('max-age=86400');
    });
  });

  describe('JavaScript and CSS', () => {
    it('caches JavaScript files for 1 year', () => {
      expect(headersContent).toContain('/*.js');
      expect(headersContent).toMatch(/\.js\s*\n\s*Cache-Control:[^\n]*max-age=31536000/);
    });

    it('caches CSS files for 1 year', () => {
      expect(headersContent).toContain('/*.css');
      expect(headersContent).toMatch(/\.css\s*\n\s*Cache-Control:[^\n]*max-age=31536000/);
    });
  });

  describe('Security Headers', () => {
    it('sets X-Content-Type-Options to nosniff', () => {
      expect(headersContent).toContain('X-Content-Type-Options: nosniff');
    });

    it('sets X-Frame-Options to DENY', () => {
      expect(headersContent).toContain('X-Frame-Options: DENY');
    });

    it('sets X-XSS-Protection', () => {
      expect(headersContent).toContain('X-XSS-Protection: 1; mode=block');
    });

    it('sets Referrer-Policy', () => {
      expect(headersContent).toContain('Referrer-Policy: strict-origin-when-cross-origin');
    });
  });

  describe('Favicon and App Icons', () => {
    it('caches favicon files', () => {
      expect(headersContent).toContain('/favicon.ico');
      expect(headersContent).toContain('/apple-touch-icon.png');
    });

    it('caches Android Chrome icons', () => {
      expect(headersContent).toContain('/android-chrome-');
    });
  });
});
