const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
let upstream, gateway, base;
let lastHeaders, mutationCalls = 0;
const listen = server => new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const close = server => new Promise(resolve => { server.closeAllConnections(); server.close(resolve); });
const json = (res, status, data) => { res.writeHead(status, { 'Content-Type': 'application/json' }); res.end(JSON.stringify(data)); };

before(async () => {
  upstream = http.createServer((req, res) => {
    lastHeaders = req.headers;
    if (req.url === '/api/auth/login' || req.url === '/api/auth/register') return json(res, 200, { access: 'access', refresh: 'refresh', user: { username: 'demo' } });
    if (req.url === '/api/auth/refresh') return json(res, 200, { access: 'renewed' });
    if (req.url === '/api/auth/logout') return json(res, 200, { message: 'bye' });
    if (req.url === '/api/health/ready') return json(res, 200, { status: 'ready', commit: 'test' });
    if (req.url === '/api/binary') { res.writeHead(200, { 'Content-Type': 'application/zip', 'Content-Disposition': 'attachment; filename=test.zip' }); return res.end(Buffer.from([80, 75, 0, 255])); }
    if (req.url === '/api/html') { res.writeHead(503, { 'Content-Type': 'text/html' }); return res.end('<html>Sleeping</html>'); }
    if (req.url === '/api/mutation') { mutationCalls++; return json(res, 500, { detail: 'Failure' }); }
    if (req.url === '/api/redirect') { res.writeHead(307, { Location: `http://127.0.0.1:${upstream.address().port}/api/redirect/` }); return res.end(); }
    if (req.headers.authorization === 'Bearer expired') return json(res, 401, { detail: 'Expired' });
    return json(res, 200, { ok: true });
  });
  await listen(upstream);
  process.env.FASTAPI_URL = `http://127.0.0.1:${upstream.address().port}`;
  process.env.NODE_ENV = 'production';
  process.env.APP_PUBLIC_URL = 'https://workmy.test';
  process.env.CORS_ORIGIN = 'https://workmy.test';
  const { app } = require('./server');
  gateway = http.createServer(app);
  await listen(gateway);
  base = `http://127.0.0.1:${gateway.address().port}`;
});
after(async () => { await close(gateway); await close(upstream); });

test('login keeps both secure host-only cookies and never exposes tokens', async () => {
  const response = await fetch(base + '/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json', Origin: 'https://workmy.test' }, body: JSON.stringify({ username: 'demo', password: 'test' }) });
  const cookies = response.headers.getSetCookie();
  assert.equal(cookies.length, 2);
  for (const cookie of cookies) {
    assert.match(cookie, /HttpOnly/); assert.match(cookie, /Secure/); assert.match(cookie, /SameSite=Strict/);
    assert.doesNotMatch(cookie, /Domain=/i);
  }
  assert.deepEqual(await response.json(), { user: { username: 'demo' } });
  assert.equal(response.headers.get('cache-control'), 'no-store');
});
test('ready is public but business APIs require cookies', async () => {
  assert.equal((await fetch(base + '/api/health/ready')).status, 200);
  assert.equal((await fetch(base + '/api/clientes/')).status, 401);
  assert.equal((await fetch(base + '/api/auth/refresh', { method: 'POST' })).status, 404);
});

test('all protected API routes reject unauthenticated probes with and without trailing slash', async () => {
  const { checkProtectedApiRouting } = await import('../../deploy/api-proxy-checks.mjs');
  await checkProtectedApiRouting(base);
});
test('refresh works with absent or expired access cookie', async () => {
  for (const cookie of ['workmy_refresh=refresh', 'workmy_access=expired; workmy_refresh=refresh']) {
    const response = await fetch(base + '/api/clientes/', { headers: { Cookie: cookie } });
    assert.equal(response.status, 200);
    assert.match(response.headers.getSetCookie()[0], /workmy_access=renewed/);
    assert.equal(lastHeaders.authorization, 'Bearer renewed');
    assert.equal(lastHeaders.host, 'workmy.test');
    assert.equal(lastHeaders['x-forwarded-proto'], 'https');
    assert.equal(lastHeaders.cookie, undefined);
  }
});
test('logout clears both cookies', async () => {
  const response = await fetch(base + '/api/auth/logout', { method: 'POST', headers: { Cookie: 'workmy_access=access' } });
  assert.equal(response.headers.getSetCookie().length, 2);
  assert.ok(response.headers.getSetCookie().every(value => /Expires=Thu, 01 Jan 1970/.test(value)));
});
test('binary response and attachment survive the proxy', async () => {
  const response = await fetch(base + '/api/binary', { headers: { Cookie: 'workmy_access=access' } });
  assert.deepEqual(Buffer.from(await response.arrayBuffer()), Buffer.from([80, 75, 0, 255]));
  assert.equal(response.headers.get('content-disposition'), 'attachment; filename=test.zip');
});
test('wrong origins are rejected; redirects remain relative', async () => {
  assert.equal((await fetch(base + '/api/clientes/', { headers: { Origin: 'https://preview.vercel.app' } })).status, 403);
  const response = await fetch(base + '/api/redirect', { redirect: 'manual', headers: { Cookie: 'workmy_access=access' } });
  assert.equal(response.headers.get('location'), '/api/redirect/');
});
test('HTML is not passed as successful data and failed writes are not retried', async () => {
  const headers = { Cookie: 'workmy_access=access' };
  const response = await fetch(base + '/api/html', { headers });
  assert.equal(response.status, 502); assert.match(response.headers.get('content-type'), /json/);
  assert.equal((await fetch(base + '/api/mutation', { method: 'POST', headers })).status, 500);
  assert.equal(mutationCalls, 1);
});
