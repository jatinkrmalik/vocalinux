"use client";

import React from "react";
import Image from "next/image";

/**
 * Vocalinux logo with WebP source and PNG fallback.
 */
export const VocalinuxLogo: React.FC<{
  className?: string;
  width?: number;
  height?: number;
  priority?: boolean;
}> = ({ className = "", width = 32, height = 32, priority = false }) => {
  return (
    <picture className={className}>
      <source srcSet="/vocalinux.webp" type="image/webp" />
      <Image
        src="/vocalinux.png"
        alt="Vocalinux"
        width={width}
        height={height}
        className={className}
        priority={priority}
      />
    </picture>
  );
};
