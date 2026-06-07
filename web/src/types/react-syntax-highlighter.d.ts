declare module "react-syntax-highlighter" {
  import type { ComponentType, CSSProperties, ReactNode } from "react";

  export type SyntaxHighlighterStyle = Record<string, CSSProperties>;

  export interface SyntaxHighlighterProps {
    children?: ReactNode;
    language?: string;
    style?: SyntaxHighlighterStyle;
    className?: string;
    customStyle?: CSSProperties;
    wrapLongLines?: boolean;
  }

  const SyntaxHighlighter: ComponentType<SyntaxHighlighterProps>;

  export default SyntaxHighlighter;
}

declare module "react-syntax-highlighter/dist/esm/styles/hljs" {
  import type { SyntaxHighlighterStyle } from "react-syntax-highlighter";

  export const atomOneDark: SyntaxHighlighterStyle;
}
