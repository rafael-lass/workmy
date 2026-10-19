// Public routing probes never carry cookies or Authorization. Business writes
// must stop at the BFF with 401, before reaching the application or database.
export const protectedApiRoutes = [
  ['GET', '/auth/me'],
  ['GET', '/clientes/'], ['POST', '/clientes/'],
  ['GET', '/clientes/2147483647'], ['PUT', '/clientes/2147483647'], ['DELETE', '/clientes/2147483647'],
  ['GET', '/servicos/'], ['POST', '/servicos/'],
  ['GET', '/servicos/tags'], ['POST', '/servicos/tags'],
  ['GET', '/servicos/2147483647'], ['PUT', '/servicos/2147483647'], ['DELETE', '/servicos/2147483647'],
  ['POST', '/servicos/2147483647/pdf'],
  ['GET', '/projetos/'], ['POST', '/projetos/'],
  ['GET', '/projetos/2147483647'], ['PUT', '/projetos/2147483647'], ['DELETE', '/projetos/2147483647'],
  ['PATCH', '/projetos/2147483647/status'], ['PATCH', '/projetos/2147483647/recorrencia'],
  ['GET', '/pagamentos/'], ['POST', '/pagamentos/'],
  ['PATCH', '/pagamentos/2147483647/receber'], ['PATCH', '/pagamentos/2147483647/cancelar'],
  ['PATCH', '/pagamentos/2147483647/estornar'], ['PATCH', '/pagamentos/2147483647/detalhes'],
  ['GET', '/dashboard/resumo'], ['GET', '/dashboard/exportar.zip'],
  ['POST', '/faturamento/recorrencias'],
];

export async function checkProtectedApiRouting(origin) {
  for (const [method, canonicalPath] of protectedApiRoutes) {
    const pathWithoutSlash = canonicalPath.replace(/\/$/, '');
    for (const suffix of ['', '/']) {
      const path = `/api${pathWithoutSlash}${suffix}`;
      const query = method === 'GET' ? '?page=1&page_size=10&periodo=mes_atual' : '';
      const response = await fetch(origin + path + query, {
        method, redirect: 'manual', signal: AbortSignal.timeout(15_000),
        ...(['POST', 'PUT', 'PATCH'].includes(method)
          ? { headers: { 'Content-Type': 'application/json' }, body: '{}' } : {}),
      });
      if (response.status !== 401 || !response.headers.get('content-type')?.includes('application/json') ||
          !response.headers.get('cache-control')?.includes('no-store')) {
        await response.body?.cancel();
        throw new Error(`Proxy inválido em ${method} ${path}: esperado 401 JSON sem cache, recebido ${response.status}.`);
      }
      const payload = await response.json();
      if (typeof payload.detail !== 'string') throw new Error(`Resposta inesperada do BFF em ${method} ${path}.`);
    }
  }
}
