declare module 'tailwindcss/lib/util/flattenColorPalette' {
	function flattenColorPalette(colors: object): { [key: string]: string };
	export = flattenColorPalette;
}