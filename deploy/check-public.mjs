import { appendFile } from 'node:fs/promises';
import { setTimeout as delay } from 'node:timers/promises';

const { APP_URL: origin, EXPECTED_SHA: sha } = process.env;
const url = new URL(origin);
if (url.protocol !== 'https:' || url.origin !== origin) throw new Error('APP_URL deve ser uma origem HTTPS sem barra final.');
let ready = false;
for (let attempt = 0; attempt < 12; attempt++) {
  try {
    const response = await fetch(`${origin}/api/health/ready`, { signal: AbortSignal.timeout(10_000), cache: 'no-store' });
    if (response.ok && response.headers.get('cache-control')?.includes('no-store') && (await response.json()).commit === sha) {
      ready = true; break;
    }
  } catch { /* DNS and cold starts can be transient. */ }
  await delay(2000);
}
if (!ready) throw new Error('A URL pública não confirmou o proxy /api e o SHA esperado.');
for (const path of ['/login', '/dashboard', '/financeiro']) {
  const response = await fetch(origin + path, { signal: AbortSignal.timeout(15_000) });
  if (!response.ok || !(await response.text()).includes('<div id="root"></div>')) throw new Error(`SPA inválida em ${path}`);
}
if (process.env.GITHUB_STEP_SUMMARY) await appendFile(process.env.GITHUB_STEP_SUMMARY,
  `### Frontend publicado\n- URL canônica: ${origin}\n- Commit: \`${sha}\`\n- Proxy, versão e rotas SPA: aprovados\n`);
