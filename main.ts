// news-image-20261123 — "23 November's world news in one image"
//
// The entry image (entry.png, a newspaper front page summing up Monday
// 23 November 2026) is produced ahead of time by build_image.py and
// shipped next to this file. This program's only job is to place that
// exact, pre-rendered image into the harness output directory and prove
// it is a valid PNG inside the competition limits.
//
// No network, no randomness, no timestamps: the same input bytes always
// produce the same output bytes, so repeated runs are bit-identical.

import { copyFileSync, mkdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const MAX_BYTES = 1_048_576; // 1 MiB — competition limit for entry.png
const PNG_MAGIC = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

const here = dirname(fileURLToPath(import.meta.url));
const sourcePath = join(here, "entry.png");

const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
const destPath = join(outDir, "entry.png");

function fail(message: string): never {
  console.error(`error: ${message}`);
  process.exit(1);
}

// 1. Read the bundled image and check it really is a PNG.
let bytes: Buffer;
try {
  bytes = readFileSync(sourcePath);
} catch {
  fail(`cannot read bundled image at ${sourcePath}`);
}

if (bytes.length < PNG_MAGIC.length || !bytes.subarray(0, 8).equals(PNG_MAGIC)) {
  fail("bundled entry.png does not start with the PNG magic bytes");
}

if (bytes.length > MAX_BYTES) {
  fail(`bundled entry.png is ${bytes.length} bytes, over the 1 MiB limit`);
}

// 1b. Parse the IHDR chunk and enforce the 1024x1024 dimension limit.
// PNG layout: 8-byte magic, then 4-byte length + "IHDR" + 13 bytes of
// header data, where the first 4 bytes are the width (big-endian) and
// the next 4 are the height.
const MAX_DIMENSION = 1024;
const ihdrLength = bytes.readUInt32BE(8);
const ihdrType = bytes.subarray(12, 16).toString("ascii");
if (ihdrType !== "IHDR" || ihdrLength !== 13 || bytes.length < 29) {
  fail("bundled entry.png has no valid IHDR chunk");
}
const width = bytes.readUInt32BE(16);
const height = bytes.readUInt32BE(20);
if (width > MAX_DIMENSION || height > MAX_DIMENSION) {
  fail(`bundled entry.png is ${width}x${height}, over the 1024x1024 limit`);
}

// 2. Copy it byte-for-byte into the output directory.
mkdirSync(outDir, { recursive: true });
copyFileSync(sourcePath, destPath);

// 3. Re-read what we wrote and confirm it matches the source exactly.
const written = readFileSync(destPath);
if (!written.equals(bytes)) {
  fail("output file differs from the bundled image after copy");
}

const size = statSync(destPath).size;
console.log(`wrote ${destPath} (${size} bytes, PNG ${width}x${height}, ${size <= MAX_BYTES ? "within" : "over"} the 1 MiB limit)`);
console.log("entry ready: 23 November 2026 world news, one image.");
