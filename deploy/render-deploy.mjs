import { appendFile } from 'node:fs/promises';
import { setTimeout as delay } from 'node:timers/promises';

const { RENDER_API_KEY: token, RENDER_SERVICE_ID: service, RENDER_URL: origin, EXPECTED_SHA: sha } = process.env;
if (!token || !/^srv-[a-z0-9]+$/i.test(service || '') || !/^[a-f0-9]{40}$/.test(sha || '')) {
  throw new Error('Configure RENDER_API_KEY, RENDER_SERVICE_ID e EXPECTED_SHA.');
}
const url = new URL(origin);
if (url.protocol !== 'https:' || url.origin !== origin) throw new Error('RENDER_URL deve ser uma origem HTTPS sem barra final.');
const endpoint = `https://api.render.com/v1/services/${encodeURIComponent(service)}/deploys`;
async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options, headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    signal: AbortSignal.timeout(30_000),
  });
  if (!response.ok) throw new Error(`Render API retornou HTTP ${response.status}. Consulte Deploys no painel.`);
  return response.json();
}

// A POST is deliberately not retried: a network error may occur after acceptance.
const created = await api(endpoint, { method: 'POST', body: JSON.stringify({ commitId: sha }) });
if (!created.id) throw new Error('A API não informou o ID do deploy.');
console.log(`Aguardando deploy ${created.id}, commit ${sha}.`);
const deadline = Date.now() + 30 * 60_000;
let live = false;
while (Date.now() < deadline) {
  const deploy = await api(`${endpoint}/${encodeURIComponent(created.id)}`);
  if (deploy.status === 'live') {
    if (deploy.commit?.id !== sha) throw new Error('O commit publicado no Render não corresponde ao commit testado.');
    live = true;
    break;
  }
  if (['build_failed', 'update_failed', 'canceled', 'deactivated', 'pre_deploy_failed'].includes(deploy.status)) {
    throw new Error(`Deploy Render terminou em ${deploy.status}. O frontend não será publicado.`);
  }
  console.log(`Render: ${deploy.status}`);
  await delay(10_000);
}
if (!live) throw new Error('Tempo limite aguardando o deploy Render. Confira o painel antes de repetir.');
let ready = false;
const readyDeadline = Date.now() + 120_000;
while (Date.now() < readyDeadline) {
  try {
    const response = await fetch(`${origin}/api/health/ready`, { signal: AbortSignal.timeout(10_000), cache: 'no-store' });
    if (response.ok && (await response.json()).commit === sha) { ready = true; break; }
  } catch { /* Only idempotent probes are retried. */ }
  await delay(2000);
}
if (!ready) throw new Error('Render não confirmou prontidão e SHA. O frontend não será publicado.');
if (process.env.GITHUB_STEP_SUMMARY) await appendFile(process.env.GITHUB_STEP_SUMMARY,
  `### Backend publicado\n- Commit: \`${sha}\`\n- URL: ${origin}\n- Deploy: \`${created.id}\`\n`);
