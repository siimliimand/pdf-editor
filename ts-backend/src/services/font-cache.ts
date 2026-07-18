/**
 * Font Cache — LRU in-memory cache for embedded font CSS,
 * backed by R2 for cross-request persistence.
 *
 * Keys are truncated SHA-256 hashes of the raw font bytes.
 * Values store the generated CSS, resolved family name, weight, and style.
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

/**
 * Cloudflare Worker env binding.
 * The FONT_CACHE R2 bucket must be declared in wrangler.toml.
 */
export interface Env {
  FONT_CACHE: R2Bucket;
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
// R2 persistence helpers
// ---------------------------------------------------------------------------

const R2_PREFIX = "font/";

/**
 * Build the R2 object key from a cache key.
 */
function r2Key(cacheKey: string): string {
  return `${R2_PREFIX}${cacheKey}`;
}

/**
 * Read a cached font entry from R2.
 * Returns `null` on miss or error.
 */
async function getFromR2(
  key: string,
  env: Env,
): Promise<FontCacheEntry | null> {
  try {
    const obj = await env.FONT_CACHE.get(r2Key(key));
    if (!obj) return null;
    return (await obj.json()) as FontCacheEntry;
  } catch {
    return null;
  }
}

/**
 * Write a cached font entry to R2.
 */
async function setInR2(
  key: string,
  entry: FontCacheEntry,
  env: Env,
): Promise<void> {
  await env.FONT_CACHE.put(r2Key(key), JSON.stringify(entry), {
    httpMetadata: { contentType: "application/json" },
  });
}

/**
 * Delete a cached font entry from R2.
 */
async function deleteFromR2(key: string, env: Env): Promise<void> {
  await env.FONT_CACHE.delete(r2Key(key));
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
 *
 * Pass `env` (from the Worker fetch handler) to enable R2 persistence.
 * Without `env`, only the in-memory LRU is used (backwards-compatible).
 */
export function getFontCache(env?: Env) {
  const lru = getLru();

  return {
    /**
     * Look up a cached entry by raw font bytes.
     * Checks LRU first (fast), then R2 on miss (persistent).
     * On R2 hit the entry is promoted back into the LRU cache.
     */
    async get(fontData: Uint8Array): Promise<FontCacheEntry | undefined> {
      const key = await hashFontData(fontData);

      // Fast path: LRU hit
      const lruHit = lru.get(key);
      if (lruHit) return lruHit;

      // Slow path: R2 miss
      if (!env) return undefined;
      const r2Hit = await getFromR2(key, env);
      if (r2Hit) {
        lru.set(key, r2Hit);
        return r2Hit;
      }

      return undefined;
    },

    /**
     * Store a font entry keyed by the SHA-256 hash of its raw bytes.
     * Writes to LRU immediately and to R2 asynchronously (fire-and-forget).
     */
    async set(
      fontData: Uint8Array,
      entry: FontCacheEntry,
    ): Promise<void> {
      const key = await hashFontData(fontData);
      lru.set(key, entry);

      // Persist to R2 in the background — don't block the caller
      if (env) {
        setInR2(key, entry, env).catch(() => {
          // R2 write failed silently; LRU still has the entry
        });
      }
    },

    /**
     * Check whether a font is already cached (by raw bytes).
     * Checks both LRU and R2.
     */
    async has(fontData: Uint8Array): Promise<boolean> {
      const key = await hashFontData(fontData);
      if (lru.has(key)) return true;
      if (!env) return false;
      const entry = await getFromR2(key, env);
      return entry !== null;
    },

    /**
     * Remove a specific font entry from both LRU and R2.
     */
    async delete(fontData: Uint8Array): Promise<void> {
      const key = await hashFontData(fontData);
      lru.delete(key);
      if (env) {
        await deleteFromR2(key, env);
      }
    },

    /** Number of entries currently in the LRU cache. */
    get size(): number {
      return lru.size;
    },

    /** Remove all entries from the in-memory LRU cache. */
    clear(): void {
      lru.clear();
    },
  };
}
