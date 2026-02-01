"use client";

import React, { useState, useEffect } from "react";
import dynamic from "next/dynamic";

// Lazy load syntax highlighter to reduce initial bundle size (~84KB savings)
const SyntaxHighlighter = dynamic(
  () => import("react-syntax-highlighter").then(mod => mod.default),
  {
    ssr: false,
    loading: () => (
      <div className="bg-zinc-900 rounded-lg p-4 text-sm">
        <pre className="text-green-400 whitespace-pre-wrap">Loading...</pre>
      </div>
    ),
  }
);

interface CodeBlockProps {
  language: string;
  children: string;
  className?: string;
  customStyle?: React.CSSProperties;
  wrapLongLines?: boolean;
}

export function CodeBlock({
  language,
  children,
  className = "",
  customStyle,
  wrapLongLines = false,
}: CodeBlockProps) {
  const [style, setStyle] = useState<any>(null);

  useEffect(() => {
    // Lazy load the style
    import("react-syntax-highlighter/dist/esm/styles/hljs").then(mod => {
      setStyle(mod.atomOneDark);
    });
  }, []);

  if (!style) {
    return (
      <div className={`bg-zinc-900 rounded-lg p-4 text-sm ${className}`} style={customStyle}>
        <pre className="text-green-400 whitespace-pre-wrap">{children}</pre>
      </div>
    );
  }

  return (
    <SyntaxHighlighter
      language={language}
      style={style}
      className={className}
      customStyle={customStyle}
      wrapLongLines={wrapLongLines}
    >
      {children}
    </SyntaxHighlighter>
  );
}
