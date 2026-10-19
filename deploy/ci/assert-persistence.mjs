const origin = 'https://localhost:8443';
const login = await fetch(origin + '/api/auth/login', {
  method: 'POST', headers: { 'Content-Type': 'application/json', Origin: origin },
  body: JSON.stringify({ username: 'cloud_ci', password: 'CloudTestPassword123' }),
});
if (!login.ok) throw new Error('Conta não persistiu após recriar o container.');
const cookie = login.headers.getSetCookie().map(value => value.split(';')[0]).join('; ');
const response = await fetch(origin + '/api/pagamentos/', { headers: { Cookie: cookie } });
if (!response.ok || (await response.json()).total !== 1) throw new Error('Histórico financeiro não persistiu.');
console.log('Conta e pagamento preservados após recriação do container.');
