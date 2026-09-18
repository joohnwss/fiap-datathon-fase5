# Verificação final da entrega

Regenerável por `python src/verificar_entrega.py`.

Início UTC: 2026-09-18T14:57:32.647058+00:00. Fim UTC: 2026-09-18T14:58:25.687517+00:00.

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
| coortes_serializadas_conferidas | True |
| X_sem_identificadores | True |
| X_somente_variaveis_origem | True |
| fase_categorica | True |
| desconhecidos_fora_matrizes_supervisionadas | True |
| separacao_temporal_preservada | True |
| hashes_coortes_conferidos | True |
| referencias_coortes_conferidas | 4 |
| modelagem_congelada_antes_teste | True |
| hashes_modelagem_conferidos | True |
| modelo_avaliado_treinado_apenas_desenvolvimento | True |
| metricas_modelagem_validas | True |
| amostras_individuais_em_documentos_publicos | 0 |
| sem_amostras_individuais_detectadas | True |

## Comparação histórica opcional

| Etapa | Baseline disponível | Coincide com fontes atuais |
| --- | --- | --- |
| auditoria | True | True |
| preparacao | True | True |

A comparação histórica usa os hashes transportados nos metadados. Sem baseline, consta como não disponível; não é requisito para verificar a integridade atual. Nenhuma pasta histórica local é necessária.

Testes executados: `python -m unittest discover -s tests -p "test_*.py" -v`. Saída completa local: `local_data/verificacao/testes.txt`. SHA-256: `8fbe6e5188b353bcffa15b0e51e87d31e5eeac98582ebe63740d7776155dbbc8`.

```text
test_phase_labels_and_year (test_auditoria_regressao.AuditoriaRegressionTests.test_phase_labels_and_year) ... ok
test_ra_states_and_ian_expectation (test_auditoria_regressao.AuditoriaRegressionTests.test_ra_states_and_ian_expectation) ... ok
test_repeated_headers_keep_original_metadata (test_auditoria_regressao.AuditoriaRegressionTests.test_repeated_headers_keep_original_metadata) ... ok
test_transition_rejects_duplicate_destination_ra (test_auditoria_regressao.AuditoriaRegressionTests.test_transition_rejects_duplicate_destination_ra) ... ok
test_alpha_is_categorical_zero (test_coortes_regressao.CoortesRegressionTests.test_alpha_is_categorical_zero) ... ok
test_destination_features_cannot_change_origin_predictors (test_coortes_regressao.CoortesRegressionTests.test_destination_features_cannot_change_origin_predictors) ... ok
test_duplicate_ra_blocks_both_sides (test_coortes_regressao.CoortesRegressionTests.test_duplicate_ra_blocks_both_sides) ... ok
test_fixed_temporal_split_and_stable_source_order (test_coortes_regressao.CoortesRegressionTests.test_fixed_temporal_split_and_stable_source_order) ... ok
test_generation_metadata_and_independent_validation (test_coortes_regressao.CoortesRegressionTests.test_generation_metadata_and_independent_validation) ... ok
test_identifiers_and_all_unapproved_columns_are_rejected (test_coortes_regressao.CoortesRegressionTests.test_identifiers_and_all_unapproved_columns_are_rejected) ... ok
test_missing_values_reasons_and_observed_zero_survive_serialization (test_coortes_regressao.CoortesRegressionTests.test_missing_values_reasons_and_observed_zero_survive_serialization) ... ok
test_origin_eligibility_and_phase_exclusions (test_coortes_regressao.CoortesRegressionTests.test_origin_eligibility_and_phase_exclusions) ... ok
test_positive_negative_and_unknown_outcomes (test_coortes_regressao.CoortesRegressionTests.test_positive_negative_and_unknown_outcomes) ... ok
test_real_source_counts_and_prepared_base_agree (test_coortes_regressao.CoortesRegressionTests.test_real_source_counts_and_prepared_base_agree) ... ok
test_recovery_only_copies_cohort_outputs (test_coortes_regressao.CoortesRegressionTests.test_recovery_only_copies_cohort_outputs) ... ok
test_references_fail_without_changing_counts (test_coortes_regressao.CoortesRegressionTests.test_references_fail_without_changing_counts) ... ok
test_tampered_csv_or_jsonl_is_detected (test_coortes_regressao.CoortesRegressionTests.test_tampered_csv_or_jsonl_is_detected) ... ok
test_bootstrap_invalid_replicates_explicit_and_reproducible (test_modelagem_regressao.ModelagemRegressionTests.test_bootstrap_invalid_replicates_explicit_and_reproducible) ... ok
test_closed_predictors_identifiers_and_future_rejected (test_modelagem_regressao.ModelagemRegressionTests.test_closed_predictors_identifiers_and_future_rejected) ... ok
test_completed_artifacts_counts_privacy_and_integrity_when_present (test_modelagem_regressao.ModelagemRegressionTests.test_completed_artifacts_counts_privacy_and_integrity_when_present) ... ok
test_empty_training_feature_fails_without_zero (test_modelagem_regressao.ModelagemRegressionTests.test_empty_training_feature_fails_without_zero) ... ok
test_full_synthetic_workflow_freezes_before_first_temporal_read (test_modelagem_regressao.ModelagemRegressionTests.test_full_synthetic_workflow_freezes_before_first_temporal_read) ... ok
test_median_learned_only_on_training (test_modelagem_regressao.ModelagemRegressionTests.test_median_learned_only_on_training) ... ok
test_metric_invalid_values_and_undefined_denominators (test_modelagem_regressao.ModelagemRegressionTests.test_metric_invalid_values_and_undefined_denominators) ... ok
test_oof_alignment_and_fold_local_fit (test_modelagem_regressao.ModelagemRegressionTests.test_oof_alignment_and_fold_local_fit) ... ok
test_pipeline_persistence_reproduces_probabilities (test_modelagem_regressao.ModelagemRegressionTests.test_pipeline_persistence_reproduces_probabilities) ... ok
test_random_state_reproducibility (test_modelagem_regressao.ModelagemRegressionTests.test_random_state_reproducibility) ... ok
test_real_development_counts_without_test_access (test_modelagem_regressao.ModelagemRegressionTests.test_real_development_counts_without_test_access) ... ok
test_repeated_temporal_evaluation_is_blocked (test_modelagem_regressao.ModelagemRegressionTests.test_repeated_temporal_evaluation_is_blocked) ... ok
test_schema_column_order (test_modelagem_regressao.ModelagemRegressionTests.test_schema_column_order) ... ok
test_selection_has_no_file_access (test_modelagem_regressao.ModelagemRegressionTests.test_selection_has_no_file_access) ... ok
test_small_groups_and_profiles_are_suppressed (test_modelagem_regressao.ModelagemRegressionTests.test_small_groups_and_profiles_are_suppressed) ... ok
test_stable_hash_and_configuration_mutation (test_modelagem_regressao.ModelagemRegressionTests.test_stable_hash_and_configuration_mutation) ... ok
test_tampered_cohort_hash_fails (test_modelagem_regressao.ModelagemRegressionTests.test_tampered_cohort_hash_fails) ... ok
test_temporal_access_requires_freeze (test_modelagem_regressao.ModelagemRegressionTests.test_temporal_access_requires_freeze) ... ok
test_threshold_deterministic_precision_tie (test_modelagem_regressao.ModelagemRegressionTests.test_threshold_deterministic_precision_tie) ... ok
test_threshold_recall_and_max_precision (test_modelagem_regressao.ModelagemRegressionTests.test_threshold_recall_and_max_precision) ... ok
test_unknown_phase_safe_and_no_new_category (test_modelagem_regressao.ModelagemRegressionTests.test_unknown_phase_safe_and_no_new_category) ... ok
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
Ran 58 tests in 24.146s

OK
```

Os dados foram relidos e comparados célula a célula com a fonte após serialização. Os testes cobrem regressões técnicas; não confirmam regras curriculares ou decisões de negócio. A busca por amostras é uma checagem suplementar, não uma prova geral de anonimização.

Verificação de conteúdo público: caminhos relativos e linguagem acadêmica, sem identificadores locais de usuário.
