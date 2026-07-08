import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind class names, resolving conflicts deterministically. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Generate a RFC 4122 v4 UUID that works in every runtime.
 *
 * Prefers the native `crypto.randomUUID()`, but that API is only defined in a
 * secure context (localhost/HTTPS) and modern browsers — so it is `undefined`
 * when the app is opened over a plain-HTTP LAN/IP origin or an older browser.
 * Falls back to `crypto.getRandomValues`, then to `Math.random`, so correlation
 * ids and local ids are always available.
 */
export function generateUuid(): string {
  const cryptoObj: Crypto | undefined =
    typeof globalThis !== "undefined" ? globalThis.crypto : undefined;

  if (cryptoObj && typeof cryptoObj.randomUUID === "function") {
    return cryptoObj.randomUUID();
  }

  const bytes = new Uint8Array(16);
  if (cryptoObj && typeof cryptoObj.getRandomValues === "function") {
    cryptoObj.getRandomValues(bytes);
  } else {
    for (let i = 0; i < bytes.length; i += 1) {
      bytes[i] = Math.floor(Math.random() * 256);
    }
  }
  // Set the version (4) and variant (10xx) bits per RFC 4122.
  bytes[6] = ((bytes[6] ?? 0) & 0x0f) | 0x40;
  bytes[8] = ((bytes[8] ?? 0) & 0x3f) | 0x80;

  const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, "0"));
  return (
    `${hex[0]}${hex[1]}${hex[2]}${hex[3]}-${hex[4]}${hex[5]}-${hex[6]}${hex[7]}-` +
    `${hex[8]}${hex[9]}-${hex[10]}${hex[11]}${hex[12]}${hex[13]}${hex[14]}${hex[15]}`
  );
}
