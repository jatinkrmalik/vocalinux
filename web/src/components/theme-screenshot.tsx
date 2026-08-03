"use client";

import Image, { type ImageProps } from "next/image";
import React from "react";

type CommonProps = {
  src: string;
  srcDark: string;
  alt: string;
  className?: string;
};

/**
 * Renders light and dark screenshot variants. Visibility follows the
 * `dark` class on `<html>` from next-themes, so the active theme's image
 * shows without a hydration flash.
 */
export function ThemeScreenshotImg({
  src,
  srcDark,
  alt,
  width,
  height,
  className = "",
  loading = "lazy",
}: CommonProps & {
  width: number;
  height: number;
  loading?: "lazy" | "eager";
}) {
  const shared = `${className}`.trim();
  return (
    <>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={src}
        alt={alt}
        width={width}
        height={height}
        className={`${shared} dark:hidden`.trim()}
        loading={loading}
        decoding="async"
      />
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={srcDark}
        alt={alt}
        width={width}
        height={height}
        className={`${shared} hidden dark:block`.trim()}
        loading={loading}
        decoding="async"
      />
    </>
  );
}

type ThemeScreenshotNextProps = CommonProps &
  Omit<ImageProps, "src" | "alt"> & {
    src: string;
    srcDark: string;
    alt: string;
  };

/** next/image twin for homepage embeds that already use Image. */
export function ThemeScreenshotImage({
  src,
  srcDark,
  alt,
  className = "",
  ...rest
}: ThemeScreenshotNextProps) {
  const shared = `${className}`.trim();
  return (
    <>
      <Image
        src={src}
        alt={alt}
        className={`${shared} dark:hidden`.trim()}
        {...rest}
      />
      <Image
        src={srcDark}
        alt={alt}
        className={`${shared} hidden dark:block`.trim()}
        {...rest}
      />
    </>
  );
}

/** Derive `/screenshots/dark/<file>` from a light `/screenshots/<file>` path. */
export function darkScreenshotPath(src: string): string {
  if (src.includes("/dark/")) {
    return src;
  }
  return src.replace("/screenshots/", "/screenshots/dark/");
}
