import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';

test('HTTPS proxy: register, cookies, financial flow, files, refresh and logout', async ({ page, context }) => {
  const unexpected = [];
  page.on('pageerror', error => unexpected.push(error.message));
  page.on('request', request => {
    if (request.url().startsWith('http') && new URL(request.url()).origin !== 'https://localhost:8443') unexpected.push(request.url());
  });
  await page.goto('/register');
  await page.getByLabel('Usuário', { exact: true }).fill('cloud_ci');
  await page.getByLabel('E-mail', { exact: true }).fill('cloud-ci@example.com');
  await page.getByLabel('Senha', { exact: true }).fill('CloudTestPassword123');
  await page.getByRole('button', { name: 'Criar conta', exact: true }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  const cookies = await context.cookies();
  for (const name of ['workmy_access', 'workmy_refresh']) {
    const cookie = cookies.find(item => item.name === name);
    expect(cookie).toMatchObject({ secure: true, httpOnly: true, sameSite: 'Strict', domain: 'localhost' });
  }
  expect(await page.evaluate(() => document.cookie)).not.toContain('workmy_');
  const api = context.request;
  async function post(path, data) {
    const response = await api.post('/api' + path, { data });
    expect(response.ok(), `${path} ${await response.text()}`).toBeTruthy();
    return response.json();
  }
  const client = await post('/clientes/', { nome: 'Cliente Cloud CI' });
  const image = Buffer.alloc(5 * 1024 * 1024, 0);
  // Valid PNG header with padding: API accepts a Base64 image payload up to 5 MiB.
  Buffer.from('89504e470d0a1a0a', 'hex').copy(image);
  const service = await post('/servicos/', { nome: 'Serviço Cloud CI', imagem_base64: `data:image/png;base64,${image.toString('base64')}` });
  // Remove the synthetic upload before PDF rendering, which requires a real image.
  const plainService = await post('/servicos/', { nome: 'Serviço PDF CI' });
  const project = await post('/projetos/', { cliente_id: client.id, servico_id: service.id, valor: '100' });
  await post('/pagamentos/', { projeto_id: project.id, valor: '100', data_pagamento: '2026-01-01' });
  const redirect = await api.get('/api/clientes', { maxRedirects: 0 });
  expect(redirect.status()).toBe(307);
  expect(redirect.headers().location).toBe('/api/clientes/');
  const pdf = await api.post(`/api/servicos/${plainService.id}/pdf`, { data: { nome_profissional: 'Cloud CI', email: 'ci@example.com' } });
  expect(pdf.status()).toBe(200);
  expect((await pdf.body()).subarray(0, 5).toString()).toBe('%PDF-');
  await page.goto('/dashboard');
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Baixar planilhas' }).click();
  const zip = await download;
  expect((await readFile(await zip.path())).subarray(0, 2).toString()).toBe('PK');
  await page.goto('/financeiro');
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Financeiro', exact: true })).toBeVisible();
  await context.clearCookies({ name: 'workmy_access' });
  const refreshed = await api.get('/api/auth/me');
  expect(refreshed.status()).toBe(200);
  expect((await context.cookies()).some(cookie => cookie.name === 'workmy_access')).toBe(true);
  await page.getByRole('button', { name: 'Sair', exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  expect((await context.cookies()).filter(cookie => cookie.name.startsWith('workmy_'))).toHaveLength(0);
  expect(unexpected).toEqual([]);
});

test('readiness exposes version and disables caching through HTTPS proxy', async ({ request }) => {
  const response = await request.get('/api/health/ready');
  expect(response.status()).toBe(200);
  expect(response.headers()['cache-control']).toContain('no-store');
  expect(await response.json()).toMatchObject({ status: 'ready', commit: process.env.APP_COMMIT_SHA || 'ci' });
});
