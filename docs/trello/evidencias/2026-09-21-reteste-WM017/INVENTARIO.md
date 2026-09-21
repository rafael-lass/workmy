# Inventário da execução final

Nomes e status extraídos dos JUnit. Cada linha é uma instância de teste, incluindo parametrizações.

| ID | Suíte | Teste | Resultado |
| --- | --- | --- | --- |
| EX-001 | [backend](backend.xml) | `tests.domain.test_pagamento::test_mensalidade_pendente_valida` | APROVADO |
| EX-002 | [backend](backend.xml) | `tests.domain.test_pagamento::test_rejeita_valor_invalido` | APROVADO |
| EX-003 | [backend](backend.xml) | `tests.domain.test_pagamento::test_rejeita_referencia_mensal_invalida[26-05]` | APROVADO |
| EX-004 | [backend](backend.xml) | `tests.domain.test_pagamento::test_rejeita_referencia_mensal_invalida[2026-13]` | APROVADO |
| EX-005 | [backend](backend.xml) | `tests.domain.test_pagamento::test_rejeita_data_de_recebimento_futura` | APROVADO |
| EX-006 | [backend](backend.xml) | `tests.domain.test_pagamento::test_fluxo_pendente_pago_estornado_e_terminal` | APROVADO |
| EX-007 | [backend](backend.xml) | `tests.domain.test_pagamento::test_cancelamento_exige_pendencia_e_motivo` | APROVADO |
| EX-008 | [backend](backend.xml) | `tests.domain.test_pagamento::test_atraso_e_calculado_somente_para_pendencia` | APROVADO |
| EX-009 | [backend](backend.xml) | `tests.domain.test_projeto::test_projeto_entity_validation_success` | APROVADO |
| EX-010 | [backend](backend.xml) | `tests.domain.test_projeto::test_projeto_entity_validation_invalid_valor` | APROVADO |
| EX-011 | [backend](backend.xml) | `tests.domain.test_projeto::test_projeto_entity_validation_invalid_progresso` | APROVADO |
| EX-012 | [backend](backend.xml) | `tests.domain.test_projeto::test_projeto_entity_validation_invalid_dia_vencimento` | APROVADO |
| EX-013 | [backend](backend.xml) | `tests.domain.test_projeto::test_completed_project_cannot_keep_active_recurrence` | APROVADO |
| EX-014 | [backend](backend.xml) | `tests.domain.test_recorrencia::test_first_due_date_falls_back_to_today` | APROVADO |
| EX-015 | [backend](backend.xml) | `tests.domain.test_recorrencia::test_explicit_start_takes_precedence_over_creation` | APROVADO |
| EX-016 | [backend](backend.xml) | `tests.domain.test_service_document::test_rejects_unsupported_or_malformed_documents[node0]` | APROVADO |
| EX-017 | [backend](backend.xml) | `tests.domain.test_service_document::test_rejects_unsupported_or_malformed_documents[node1]` | APROVADO |
| EX-018 | [backend](backend.xml) | `tests.domain.test_service_document::test_rejects_unsupported_or_malformed_documents[node2]` | APROVADO |
| EX-019 | [backend](backend.xml) | `tests.domain.test_service_document::test_rejects_unsupported_or_malformed_documents[node3]` | APROVADO |
| EX-020 | [backend](backend.xml) | `tests.domain.test_service_document::test_rejects_unsupported_or_malformed_documents[node4]` | APROVADO |
| EX-021 | [backend](backend.xml) | `tests.domain.test_service_document::test_rejects_unsupported_or_malformed_documents[node5]` | APROVADO |
| EX-022 | [backend](backend.xml) | `tests.domain.test_service_document::test_rejects_unsupported_or_malformed_documents[node6]` | APROVADO |
| EX-023 | [backend](backend.xml) | `tests.domain.test_service_document::test_rejects_unsupported_or_malformed_documents[node7]` | APROVADO |
| EX-024 | [backend](backend.xml) | `tests.domain.test_service_document::test_rejects_unsupported_or_malformed_documents[node8]` | APROVADO |
| EX-025 | [backend](backend.xml) | `tests.domain.test_service_document::test_preserves_supported_formatting_and_sanitizes_link_attributes` | APROVADO |
| EX-026 | [backend](backend.xml) | `tests.integration.test_api::test_services_documents_tags_and_pdf_contract` | APROVADO |
| EX-027 | [backend](backend.xml) | `tests.integration.test_api::test_fastapi_health_check` | APROVADO |
| EX-028 | [backend](backend.xml) | `tests.integration.test_api::test_fastapi_create_projeto_flow` | APROVADO |
| EX-029 | [backend](backend.xml) | `tests.integration.test_api::test_fastapi_auth_register_and_login_flow` | APROVADO |
| EX-030 | [backend](backend.xml) | `tests.integration.test_api::test_fastapi_project_list_get_delete_flow` | APROVADO |
| EX-031 | [backend](backend.xml) | `tests.integration.test_api::test_payment_and_recurring_billing_contract` | APROVADO |
| EX-032 | [backend](backend.xml) | `tests.integration.test_dashboard_forecast::test_forecast_first_eligible_due_date[future-start]` | APROVADO |
| EX-033 | [backend](backend.xml) | `tests.integration.test_dashboard_forecast::test_forecast_first_eligible_due_date[before-due]` | APROVADO |
| EX-034 | [backend](backend.xml) | `tests.integration.test_dashboard_forecast::test_forecast_first_eligible_due_date[on-due]` | APROVADO |
| EX-035 | [backend](backend.xml) | `tests.integration.test_dashboard_forecast::test_forecast_first_eligible_due_date[after-due]` | APROVADO |
| EX-036 | [backend](backend.xml) | `tests.integration.test_dashboard_forecast::test_forecast_excludes_ineligible_contracts[paused]` | APROVADO |
| EX-037 | [backend](backend.xml) | `tests.integration.test_dashboard_forecast::test_forecast_excludes_ineligible_contracts[completed]` | APROVADO |
| EX-038 | [backend](backend.xml) | `tests.integration.test_dashboard_forecast::test_forecast_excludes_ineligible_contracts[archived]` | APROVADO |
| EX-039 | [backend](backend.xml) | `tests.integration.test_dashboard_forecast::test_forecast_excludes_ineligible_contracts[deleted]` | APROVADO |
| EX-040 | [backend](backend.xml) | `tests.integration.test_dashboard_forecast::test_forecast_excludes_ineligible_contracts[other-user]` | APROVADO |
| EX-041 | [backend](backend.xml) | `tests.integration.test_dashboard_forecast::test_forecast_excludes_ineligible_contracts[one-off]` | APROVADO |
| EX-042 | [backend](backend.xml) | `tests.integration.test_dashboard_forecast::test_forecast_falls_back_to_creation[creation-on-due]` | APROVADO |
| EX-043 | [backend](backend.xml) | `tests.integration.test_dashboard_forecast::test_forecast_falls_back_to_creation[creation-after-due]` | APROVADO |
| EX-044 | [backend](backend.xml) | `tests.integration.test_dashboard_forecast::test_forecast_year_boundary` | APROVADO |
| EX-045 | [backend](backend.xml) | `tests.integration.test_dashboard_forecast::test_forecast_empty` | APROVADO |
| EX-046 | [backend](backend.xml) | `tests.integration.test_service_migration::test_migration_preserves_legacy_services_and_deduplicates_tags` | APROVADO |
| EX-047 | [backend](backend.xml) | `tests.integration.test_service_pdf::test_pdf_covers_unicode_links_lists_and_long_descriptions` | APROVADO |
| EX-048 | [backend](backend.xml) | `tests.integration.test_use_cases::test_criar_projeto_use_case_success` | APROVADO |
| EX-049 | [backend](backend.xml) | `tests.integration.test_use_cases::test_criar_projeto_use_case_colisao` | APROVADO |
| EX-050 | [backend](backend.xml) | `tests.integration.test_use_cases::test_faturar_recorrencias_use_case` | APROVADO |
| EX-051 | [backend](backend.xml) | `tests.integration.test_use_cases::test_faturar_recorrencias_ignora_inicio_futuro_e_projeto_encerrado` | APROVADO |
| EX-052 | [backend](backend.xml) | `tests.integration.test_use_cases::test_pagamento_manual_e_sempre_avulso` | APROVADO |
| EX-053 | [backend](backend.xml) | `tests.integration.test_use_cases::test_atualizar_projeto_limpa_opcional_e_encerra_recorrencia` | APROVADO |
| EX-054 | [backend](backend.xml) | `tests.integration.test_use_cases::test_pausa_e_retomada_nao_geram_meses_pausados` | APROVADO |
| EX-055 | [backend](backend.xml) | `tests.integration.test_use_cases::test_nao_exclui_projeto_com_historico_financeiro` | APROVADO |
| EX-056 | [frontend](frontend.xml) | `src/lib/http.test.ts::downloads binary responses without trying JSON` | APROVADO |
| EX-057 | [frontend](frontend.xml) | `src/lib/http.test.ts::preserves JSON authentication errors during downloads` | APROVADO |
| EX-058 | [frontend](frontend.xml) | `src/pages/DashboardPage.test.tsx::ações rápidas do dashboard > leva ao formulário canônico de projeto pela URL` | APROVADO |
| EX-059 | [frontend](frontend.xml) | `src/pages/FinanceiroPage.test.tsx::ações financeiras por estado > oferece receber/cancelar somente para pendências` | APROVADO |
| EX-060 | [frontend](frontend.xml) | `src/pages/FinanceiroPage.test.tsx::ações financeiras por estado > oferece estorno somente para pagamentos confirmados` | APROVADO |
| EX-061 | [frontend](frontend.xml) | `src/state/AuthContext.test.tsx::AuthProvider > valida a sessão pelo servidor e não depende de localStorage` | APROVADO |
| EX-062 | [frontend](frontend.xml) | `src/features/projetos/ProjetoFormDialog.test.tsx::ProjetoFormDialog > exige os campos de recorrência apenas no modelo mensal` | APROVADO |
| EX-063 | [frontend](frontend.xml) | `src/features/financeiro/FinanceDialogs.test.tsx::ManualPaymentDialog > desabilita o envio e impede duplicação por clique repetido` | APROVADO |
| EX-064 | [frontend](frontend.xml) | `src/features/clientes/ClienteFormDialog.test.tsx::ClienteFormDialog > mostra erros próximos aos campos inválidos sem chamar a API` | APROVADO |
| EX-065 | [frontend](frontend.xml) | `src/features/clientes/ClienteFormDialog.test.tsx::ClienteFormDialog > mantém o diálogo aberto quando a API falha` | APROVADO |
| EX-066 | [frontend](frontend.xml) | `src/features/servicos/Services.test.tsx::Serviços > seleciona uma tag existente por Enter e cria uma nova sem duplicar envio` | APROVADO |
| EX-067 | [frontend](frontend.xml) | `src/features/servicos/Services.test.tsx::Serviços > reabre formatação salva, valida nome e preserva formulário após falha` | APROVADO |
| EX-068 | [frontend](frontend.xml) | `src/features/servicos/Services.test.tsx::Serviços > bloqueia exportação duplicada e preserva contatos se a API falha` | APROVADO |
| EX-069 | [frontend](frontend.xml) | `src/shared/ui/Dialog.test.tsx::Dialog > abre com título acessível, fecha por Esc e devolve o foco` | APROVADO |
| EX-070 | [frontend](frontend.xml) | `src/shared/ui/Dialog.test.tsx::Dialog > bloqueia fechamento durante o envio` | APROVADO |
