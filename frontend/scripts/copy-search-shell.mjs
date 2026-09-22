// Vercel's Python functions need the same hashed asset shell as the static client.
import { copyFile } from 'node:fs/promises';
await copyFile(new URL('../dist/index.html', import.meta.url), new URL('../../backend/seo/client.html', import.meta.url));
