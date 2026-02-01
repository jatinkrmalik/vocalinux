// @ts-ignore
/** @type {import("next").NextConfig} */
const config = {
	output: 'export',
	trailingSlash: true,
	// Configuration for custom domain deployment
	distDir: 'out',

	// Configure cache headers for static assets
	// This generates a _headers file for platforms like Netlify/Vercel
	async headers() {
		return [
			{
				source: '/_next/static/:path*',
				headers: [
					{
						key: 'Cache-Control',
						value: 'public, max-age=31536000, immutable',
					},
				],
			},
			{
				source: '/:all*(svg|jpg|jpeg|png|webp|avif|ico|woff|woff2)',
				headers: [
					{
						key: 'Cache-Control',
						value: 'public, max-age=31536000, immutable',
					},
				],
			},
		];
	},
	images: {
		unoptimized: true,
		formats: ['image/avif', 'image/webp'],
		remotePatterns: [
			{
				protocol: 'https',
				hostname: '*',
				pathname: '**',
			},
		],
	},
	eslint: {
		ignoreDuringBuilds: true,
	},
	typescript: {
		ignoreBuildErrors: true,
	},
	// Disable source maps in production to reduce bundle size
	productionBrowserSourceMaps: false,
	// Use modern JavaScript for better performance and smaller bundle sizes
	experimental: {
		optimizePackageImports: ['lucide-react', 'framer-motion'],
	},
	webpack: (config, { isServer, dev }) => {
		// Only use source maps in development
		if (!dev) {
			config.devtool = false;
		}
		// Use verbose stats for build analysis
		config.stats = "verbose";
		// Enhanced node polyfills for postgres and other modules
		if (!isServer) {
			config.resolve.fallback = {
				...config.resolve.fallback,
				// File system - never needed in browser
				fs: false,
				net: false,
				tls: false,
				crypto: false,
				stream: false,
				'perf_hooks': false,

				// Definitely not needed in browser
				child_process: false,
				dns: false,
			};

			// Configure swc to output modern JavaScript (ES2022) instead of ES5
			// This eliminates unnecessary polyfills and reduces bundle size
			if (config.optimization && config.optimization.minimizer) {
				config.optimization.minimizer.forEach((minimizer) => {
					if (minimizer.constructor.name === 'TerserPlugin') {
						minimizer.options.compress = {
							...minimizer.options.compress,
							pure_funcs: ['console.log', 'console.debug'],
						};
					}
				});
			}
		}
		return config;
	},
};
export default config;
