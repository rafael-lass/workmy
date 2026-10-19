import { test, expect } from '@playwright/test';

test('public deployment: authenticated session on canonical HTTPS origin', async ({ page, context }) => {
  const { SMOKE_USERNAME: username, SMOKE_PASSWORD: password, APP_URL: origin, EXPECTED_SHA: sha } = process.env;
  test.skip(!username && !password, 'Bootstrap: configure SMOKE_USERNAME e SMOKE_PASSWORD para validar sessão.');
  if (!username || !password) throw new Error('Configure os dois secrets SMOKE_USERNAME e SMOKE_PASSWORD.');
  const violations = [];
  page.on('pageerror', error => violations.push(error.message));
  page.on('request', request => { if (new URL(request.url()).origin !== origin) violations.push(request.url()); });
  await page.goto('/login');
  await page.getByLabel('Usuário ou e-mail', { exact: true }).fill(username);
  await page.getByLabel('Senha', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Entrar', exact: true }).click();
  await expect(page).toHaveURL(origin + '/dashboard');
  const cookies = await context.cookies();
  expect(cookies.filter(cookie => cookie.name.startsWith('workmy_'))).toHaveLength(2);
  expect(cookies.filter(cookie => cookie.name.startsWith('workmy_')).every(cookie => cookie.secure && cookie.httpOnly && cookie.sameSite === 'Strict')).toBe(true);
  const ready = await context.request.get('/api/health/ready');
  expect((await ready.json()).commit).toBe(sha);
  await page.goto('/financeiro');
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Financeiro', exact: true })).toBeVisible();
  await context.clearCookies({ name: 'workmy_access' });
  expect((await context.request.get('/api/auth/me')).status()).toBe(200);
  await page.getByRole('button', { name: 'Sair', exact: true }).click();
  await expect(page).toHaveURL(origin + '/login');
  expect(violations).toEqual([]);
});
