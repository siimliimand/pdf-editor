/**
 * Font Cache — LRU in-memory cache for embedded font CSS.
 *
 * Keys are truncated SHA-256 hashes of the raw font bytes.
 * Values store the generated CSS, resolved family name, weight, and style.
 *
 * R2 persistence will be layered on top in task 10.2.
 */

import { LRUCache } from "lru-cache";
import { CACHE } from "../models/constants";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface FontCacheEntry {
  /** The @font-face CSS for this font. */
  css: string;
  /** Resolved CSS font-family name. */
  family: string;
  /** CSS font-weight number. */
  weight: number;
  /** CSS font-style ("normal" | "italic"). */
  style: string;
}

// ---------------------------------------------------------------------------
// SHA-256 helper (Web Crypto API — available in Workers runtime)
// ---------------------------------------------------------------------------

/**
 * Compute a SHA-256 hex digest of arbitrary bytes, truncated to
 * `CACHE.HASH_LENGTH` characters.
 */
async function hashFontData(data: Uint8Array): Promise<string> {
  const buf = new ArrayBuffer(data.byteLength);
  new Uint8Array(buf).set(data);
  const digest = await crypto.subtle.digest("SHA-256", buf);
  const hex = [...new Uint8Array(digest)]
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  return hex.slice(0, CACHE.HASH_LENGTH);
}

// ---------------------------------------------------------------------------
// Singleton LRU cache
// ---------------------------------------------------------------------------

let _instance: LRUCache<string, FontCacheEntry> | null = null;

function getLru(): LRUCache<string, FontCacheEntry> {
  if (!_instance) {
    _instance = new LRUCache<string, FontCacheEntry>({
      max: CACHE.MAX_ENTRIES,
    });
  }
  return _instance;
}

/**
 * Access the process-wide font cache singleton.
 */
export function getFontCache() {
  const lru = getLru();

  return {
    /**
     * Look up a cached entry by raw font bytes.
     * Returns `undefined` on miss.
     */
    async get(fontData: Uint8Array): Promise<FontCacheEntry | undefined> {
      const key = await hashFontData(fontData);
      return lru.get(key);
    },

    /**
     * Store a font entry keyed by the SHA-256 hash of its raw bytes.
     */
    async set(
      fontData: Uint8Array,
      entry: FontCacheEntry,
    ): Promise<void> {
      const key = await hashFontData(fontData);
      lru.set(key, entry);
    },

    /**
     * Check whether a font is already cached (by raw bytes).
     */
    async has(fontData: Uint8Array): Promise<boolean> {
      const key = await hashFontData(fontData);
      return lru.has(key);
    },

    /** Number of entries currently in the cache. */
    get size(): number {
      return lru.size;
    },

    /** Remove all cached entries. */
    clear(): void {
      lru.clear();
    },
  };
}
