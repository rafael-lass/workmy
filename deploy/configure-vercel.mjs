import { readFile, writeFile } from 'node:fs/promises';

const url = new URL(process.env.RENDER_URL || process.argv[2] || '');
if (url.protocol !== 'https:' || url.username || url.password || url.pathname !== '/' || url.search || url.hash ||
    url.hostname.endsWith('.invalid')) throw new Error('Informe a origem HTTPS real do Render, sem caminho.');
const path = new URL('../frontend/vercel.json', import.meta.url);
const config = JSON.parse(await readFile(path, 'utf8'));
config.rewrites[0] = { source: '/api/:path*', destination: `${url.origin}/api/:path*` };
await writeFile(path, JSON.stringify(config, null, 2) + '\n');
console.log(`Proxy /api configurado para ${url.origin}`);
