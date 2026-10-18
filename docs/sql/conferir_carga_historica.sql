-- Apenas leitura. Esperado: 10000 clientes, 53 serviços, 12000 projetos, 200000 pagamentos.
WITH dono AS (SELECT id FROM usuarios WHERE username = 'workmy_carga')
SELECT 'clientes' AS entidade, COUNT(*) AS quantidade FROM clientes WHERE usuario_id IN (SELECT id FROM dono)
UNION ALL SELECT 'servicos', COUNT(*) FROM servicos WHERE usuario_id IN (SELECT id FROM dono)
UNION ALL SELECT 'projetos', COUNT(*) FROM projetos WHERE usuario_id IN (SELECT id FROM dono)
UNION ALL SELECT 'pagamentos', COUNT(*) FROM pagamentos pg JOIN projetos p ON p.id=pg.projeto_id WHERE p.usuario_id IN (SELECT id FROM dono);

-- Esperado: 23 clientes, 23 projetos, 30000.00 por mês.
SELECT COUNT(DISTINCT p.cliente_id) AS clientes, COUNT(*) AS projetos, SUM(p.valor_mensal) AS mensalidades
FROM projetos p JOIN usuarios u ON u.id=p.usuario_id
WHERE u.username='workmy_carga' AND p.recorrencia_ativa AND p.deletado_em IS NULL;

SELECT EXTRACT(YEAR FROM pg.data_vencimento) AS ano, pg.tipo_pagamento, pg.status, COUNT(*), SUM(pg.valor)
FROM pagamentos pg JOIN projetos p ON p.id=pg.projeto_id JOIN usuarios u ON u.id=p.usuario_id
WHERE u.username='workmy_carga'
GROUP BY 1,2,3 ORDER BY 1,2,3;

-- Ambas as consultas abaixo devem retornar 0.
SELECT COUNT(*) AS vinculos_inconsistentes
FROM projetos p JOIN clientes c ON c.id=p.cliente_id JOIN servicos s ON s.id=p.servico_id JOIN usuarios u ON u.id=p.usuario_id
WHERE u.username='workmy_carga' AND (c.usuario_id<>p.usuario_id OR s.usuario_id<>p.usuario_id);

SELECT COUNT(*) AS referencias_duplicadas FROM (
 SELECT pg.projeto_id, pg.referencia_mes FROM pagamentos pg
 JOIN projetos p ON p.id=pg.projeto_id JOIN usuarios u ON u.id=p.usuario_id
 WHERE u.username='workmy_carga' AND pg.referencia_mes IS NOT NULL
 GROUP BY pg.projeto_id, pg.referencia_mes HAVING COUNT(*)>1
) duplicadas;
