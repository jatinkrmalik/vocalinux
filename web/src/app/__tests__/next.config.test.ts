import fs from 'fs';
import path from 'path';

describe('Next.js Config - PageSpeed Optimizations', () => {
  const configPath = path.join(process.cwd(), 'next.config.js');
  let configContent: string;

  beforeAll(() => {
    configContent = fs.readFileSync(configPath, 'utf-8');
  });

  it('exists in the project root', () => {
    expect(fs.existsSync(configPath)).toBe(true);
  });

  describe('Image Configuration', () => {
    it('configures image formats for optimization', () => {
      expect(configContent).toContain("formats: ['image/avif', 'image/webp']");
    });

    it('has unoptimized images for static export', () => {
      expect(configContent).toContain('unoptimized: true');
    });

    it('configures remote patterns for external images', () => {
      expect(configContent).toContain('remotePatterns');
      expect(configContent).toContain('protocol:');
      expect(configContent).toContain('hostname:');
    });
  });

  describe('Experimental Optimizations', () => {
    it('enables optimizePackageImports for lucide-react', () => {
      expect(configContent).toContain('optimizePackageImports');
      expect(configContent).toContain('lucide-react');
    });

    it('enables optimizePackageImports for framer-motion', () => {
      expect(configContent).toContain('framer-motion');
    });
  });

  describe('Build Configuration', () => {
    it('outputs to distDir: out for static export', () => {
      expect(configContent).toContain("distDir: 'out'");
    });

    it('disables production browser source maps', () => {
      expect(configContent).toContain('productionBrowserSourceMaps: false');
    });

    it('configures static export', () => {
      expect(configContent).toContain("output: 'export'");
    });
  });

  describe('SWC Configuration', () => {
    it('has webpack configuration for custom optimizations', () => {
      expect(configContent).toContain('webpack:');
    });

    it('configures TerserPlugin for console removal', () => {
      expect(configContent).toContain('TerserPlugin');
      expect(configContent).toContain('pure_funcs');
      expect(configContent).toContain('console.log');
    });

    it('provides node polyfills for browser', () => {
      expect(configContent).toContain('resolve.fallback');
      expect(configContent).toContain('fs: false');
    });
  });

  describe('TypeScript Configuration', () => {
    it('ignores TypeScript build errors (for CI/CD compatibility)', () => {
      expect(configContent).toContain('typescript:');
      expect(configContent).toContain('ignoreBuildErrors: true');
    });
  });

  describe('ESLint Configuration', () => {
    it('ignores ESLint during builds', () => {
      expect(configContent).toContain('eslint:');
      expect(configContent).toContain('ignoreDuringBuilds: true');
    });
  });
});
