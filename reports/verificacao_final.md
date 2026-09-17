# Verificação final da entrega

Regenerável por `python src/verificar_entrega.py`.

Início UTC: 2026-09-17T13:59:57.598760+00:00. Fim UTC: 2026-09-17T14:00:13.317764+00:00.

Comando: `python src/verificar_entrega.py`.

| Verificação | Resultado |
| --- | --- |
| testes_exit_code | 0 |
| fontes_conferidas | 13 |
| hashes_fontes_auditoria_e_preparacao | True |
| hashes_scripts_e_testes | True |
| hashes_saidas | True |
| documentos_manuais_preservados | True |
| referencias_reproduzidas | True |
| auditoria_e_preparacao_mesmos_agregados | True |
| diretorios_ignorados | ['DATATHON/probe.txt', 'local_data/base_longitudinal.jsonl', 'local_recovery/probe.txt'] |
| arquivos_individuais_rastreados | 0 |
| dados_individuais_fora_versionamento | True |
| registros_conferidos_na_origem | 3030 |
| celulas_originais_conferidas | 142592 |
| correspondencia_integral_origem | True |
| enderecos_origem_unicos | True |
| contagens_por_ano | {2022: 860, 2023: 1014, 2024: 1156} |
| ra_ano_unico | True |
| registros_com_ra_invalido | 0 |
| jsonl_reaberto_identico | True |
| csv_reaberto_campos_conferidos | True |
| campos_derivados_csv | 90 |
| linhas_jsonl | 3030 |
| amostras_individuais_em_documentos_publicos | 0 |
| sem_amostras_individuais_detectadas | True |

## Comparação histórica opcional

| Etapa | Baseline disponível | Coincide com fontes atuais |
| --- | --- | --- |
| auditoria | True | True |
| preparacao | True | True |

A comparação histórica usa os hashes transportados nos metadados. Sem baseline, consta como não disponível; não é requisito para verificar a integridade atual. Nenhuma pasta histórica local é necessária.

Testes executados: `python -m unittest discover -s tests -p "test_*.py" -v`. Saída completa local: `local_data/verificacao/testes.txt`. SHA-256: `78b7ec143da81471a5a117c29d2a1d27dfa07f6f22a6dc37f32a2f1077e791a7`.

```text
test_phase_labels_and_year (test_auditoria_regressao.AuditoriaRegressionTests.test_phase_labels_and_year) ... ok
test_ra_states_and_ian_expectation (test_auditoria_regressao.AuditoriaRegressionTests.test_ra_states_and_ian_expectation) ... ok
test_repeated_headers_keep_original_metadata (test_auditoria_regressao.AuditoriaRegressionTests.test_repeated_headers_keep_original_metadata) ... ok
test_transition_rejects_duplicate_destination_ra (test_auditoria_regressao.AuditoriaRegressionTests.test_transition_rejects_duplicate_destination_ra) ... ok
test_absolute_path_detector_and_portable_command (test_portabilidade_regressao.PortabilidadeRegressionTests.test_absolute_path_detector_and_portable_command) ... ok
test_final_verification_runs_without_local_recovery (test_portabilidade_regressao.PortabilidadeRegressionTests.test_final_verification_runs_without_local_recovery) ... ok
test_history_is_optional_and_metadata_only (test_portabilidade_regressao.PortabilidadeRegressionTests.test_history_is_optional_and_metadata_only) ... ok
test_manual_mutation_during_run_is_detected (test_portabilidade_regressao.PortabilidadeRegressionTests.test_manual_mutation_during_run_is_detected) ... ok
test_new_run_portable_reports_and_manual_documents_preserved (test_portabilidade_regressao.PortabilidadeRegressionTests.test_new_run_portable_reports_and_manual_documents_preserved) ... ok
test_phase_counts_include_eligible_missing_destination (test_portabilidade_regressao.PortabilidadeRegressionTests.test_phase_counts_include_eligible_missing_destination) ... ok
test_public_language_accepts_academic_acronym_and_rejects_editorial_context (test_portabilidade_regressao.PortabilidadeRegressionTests.test_public_language_accepts_academic_acronym_and_rejects_editorial_context) ... ok
test_ra_outside_first_column_and_tampered_association (test_portabilidade_regressao.PortabilidadeRegressionTests.test_ra_outside_first_column_and_tampered_association) ... ok
test_absent_target_is_not_negative_outcome_and_join_uses_ra (test_preparacao_regressao.PreparacaoRegressionTests.test_absent_target_is_not_negative_outcome_and_join_uses_ra) ... ok
test_all_indicator_ranges_and_extreme_preserved (test_preparacao_regressao.PreparacaoRegressionTests.test_all_indicator_ranges_and_extreme_preserved) ... ok
test_cell_states_do_not_fill_unavailable_with_zero (test_preparacao_regressao.PreparacaoRegressionTests.test_cell_states_do_not_fill_unavailable_with_zero) ... ok
test_dates_ambiguous_remain_unavailable (test_preparacao_regressao.PreparacaoRegressionTests.test_dates_ambiguous_remain_unavailable) ... ok
test_duplicates_kept_but_join_blocked_and_ra_states_separate (test_preparacao_regressao.PreparacaoRegressionTests.test_duplicates_kept_but_join_blocked_and_ra_states_separate) ... ok
test_excel_errors_and_types_survive_disk_roundtrip (test_preparacao_regressao.PreparacaoRegressionTests.test_excel_errors_and_types_survive_disk_roundtrip) ... ok
test_header_suffix_cannot_overwrite_real_column (test_preparacao_regressao.PreparacaoRegressionTests.test_header_suffix_cannot_overwrite_real_column) ... ok
test_inventory_changes_distinguish_added_removed_changed (test_preparacao_regressao.PreparacaoRegressionTests.test_inventory_changes_distinguish_added_removed_changed) ... ok
test_observed_phase_codes_and_parentheses (test_preparacao_regressao.PreparacaoRegressionTests.test_observed_phase_codes_and_parentheses) ... ok
test_original_rows_and_all_fields_remain_associated (test_preparacao_regressao.PreparacaoRegressionTests.test_original_rows_and_all_fields_remain_associated) ... ok
test_phase_rejects_fraction_and_unanchored_digits (test_preparacao_regressao.PreparacaoRegressionTests.test_phase_rejects_fraction_and_unanchored_digits) ... ok
test_type_after_first_twenty_rows_is_counted (test_preparacao_regressao.PreparacaoRegressionTests.test_type_after_first_twenty_rows_is_counted) ... ok

----------------------------------------------------------------------
Ran 24 tests in 1.897s

OK
```

Os dados foram relidos e comparados célula a célula com a fonte após serialização. Os testes cobrem regressões técnicas; não confirmam regras curriculares ou decisões de negócio. A busca por amostras é uma checagem suplementar, não uma prova geral de anonimização.

Verificação de conteúdo público: caminhos relativos e linguagem acadêmica, sem identificadores locais de usuário.
