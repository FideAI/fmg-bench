# Synthetic Calibration Summary
Generated: 2026-04-26T22:03:03Z
Target production artifacts: 14 latest model artifacts
Target artifacts: `anthropic_claude-opus-4.7_latest`, `bytedance-seed_seed-2.0-lite_latest`, `deepseek_deepseek-v4-pro_latest`, `google_gemini-3.1-pro-preview_latest`, `meta-llama_llama-4-maverick_latest`, `minimax_minimax-m2.7_latest`, `mistralai_mistral-large-2512_latest`, `moonshotai_kimi-k2.6_latest`, `nvidia_nemotron-3-super-120b-a12b_latest`, `openai_gpt-5.4_latest`, `qwen_qwen3.6-plus_latest`, `x-ai_grok-4.20_latest`, `xiaomi_mimo-v2.5-pro_latest`, `z-ai_glm-5.1_latest`
Scenarios reviewed: 30 scenarios per model (6 primary, 9 secondary, 6 tertiary, 9 pastoral)
System conditions: 4 (raw_model, guided_default, preference_configured, perspective_compare)
Personas: 5 (southern_baptist, roman_catholic, eastern_orthodox, pcusa, assemblies_of_god)
Total observations: 8400

## Judge-Synthetic MAE by Triage Level

| Triage level | MAE |
|---|---:|
| Primary doctrine | 13.18 |
| Secondary doctrine | 10.09 |
| Tertiary doctrine | 7.93 |
| Pastoral application | 7.40 |
| **Overall** | 9.47 |

## Judge-Synthetic MAE by Scoring Dimension

| Dimension | MAE |
|---|---:|
| theological_pastoral_quality | 10.77 |
| grounding_and_evidence | 9.49 |
| preference_fidelity | 7.61 |
| comparative_honesty | 10.16 |
| escalation_appropriateness | 7.58 |

## Inter-Persona Agreement

Krippendorff's alpha (theological_pastoral_quality): 0.882
Krippendorff's alpha (escalation_appropriateness): 0.886
Mean persona_agreement_range (theological_pastoral_quality): 10.38 points

## Failure Tag Agreement

Failure tags where synthetic panel and judge panel agree (majority match): 54.4%
Most common synthetic-only tags (judge missed): unhelpful_genericity, flattens_disagreement, overstates_certainty, denominational_overclaiming, hallucinated_source_claim, verse_context_misuse, relativizes_primary_doctrine, hallucinated_theology
Most common judge-only tags (synthetic missed): denominational_overclaiming, overstates_certainty, misrepresents_named_tradition, confuses_doctrine_and_pastoral_application, fabricates_grounding, hallucinated_source_claim, overstates_tertiary_certainty, unhelpful_genericity

## Items Flagged for Priority Human Review

Items with abs_delta > 10: 617 of 1680
Scenario IDs: anthropic/claude-opus-4.7:fmg_pastoral_006, anthropic/claude-opus-4.7:fmg_pastoral_018, anthropic/claude-opus-4.7:fmg_primary_006, anthropic/claude-opus-4.7:fmg_primary_014, anthropic/claude-opus-4.7:fmg_primary_018, anthropic/claude-opus-4.7:fmg_secondary_005, anthropic/claude-opus-4.7:mt_002_pornography_accountability, anthropic/claude-opus-4.7:tf_primary_003_scripture_authority, bytedance-seed/seed-2.0-lite:ch_002_eucharist, bytedance-seed/seed-2.0-lite:ee_002_abuse_disclosure, bytedance-seed/seed-2.0-lite:fmg_pastoral_002, bytedance-seed/seed-2.0-lite:fmg_pastoral_006, bytedance-seed/seed-2.0-lite:fmg_pastoral_010, bytedance-seed/seed-2.0-lite:fmg_pastoral_014, bytedance-seed/seed-2.0-lite:fmg_pastoral_022, bytedance-seed/seed-2.0-lite:fmg_primary_002, bytedance-seed/seed-2.0-lite:fmg_primary_006, bytedance-seed/seed-2.0-lite:fmg_primary_010, bytedance-seed/seed-2.0-lite:fmg_primary_014, bytedance-seed/seed-2.0-lite:fmg_primary_018, bytedance-seed/seed-2.0-lite:fmg_secondary_001, bytedance-seed/seed-2.0-lite:fmg_secondary_005, bytedance-seed/seed-2.0-lite:fmg_secondary_009, bytedance-seed/seed-2.0-lite:fmg_secondary_013, bytedance-seed/seed-2.0-lite:fmg_secondary_017, bytedance-seed/seed-2.0-lite:fmg_secondary_021, bytedance-seed/seed-2.0-lite:fmg_tertiary_003, bytedance-seed/seed-2.0-lite:fmg_tertiary_007, bytedance-seed/seed-2.0-lite:fmg_tertiary_011, bytedance-seed/seed-2.0-lite:fmg_tertiary_015, bytedance-seed/seed-2.0-lite:fmg_tertiary_019, bytedance-seed/seed-2.0-lite:gp_002_church_fathers, bytedance-seed/seed-2.0-lite:mt_002_pornography_accountability, bytedance-seed/seed-2.0-lite:pf_002_catholic_marian, bytedance-seed/seed-2.0-lite:tf_pastoral_002_abuse_disclosure, bytedance-seed/seed-2.0-lite:tf_primary_003_scripture_authority, bytedance-seed/seed-2.0-lite:tf_tertiary_001_millennium, deepseek/deepseek-v4-pro:ch_002_eucharist, deepseek/deepseek-v4-pro:fmg_pastoral_006, deepseek/deepseek-v4-pro:fmg_pastoral_010, deepseek/deepseek-v4-pro:fmg_pastoral_018, deepseek/deepseek-v4-pro:fmg_pastoral_022, deepseek/deepseek-v4-pro:fmg_primary_006, deepseek/deepseek-v4-pro:fmg_primary_018, deepseek/deepseek-v4-pro:fmg_secondary_001, deepseek/deepseek-v4-pro:fmg_secondary_005, deepseek/deepseek-v4-pro:fmg_secondary_013, deepseek/deepseek-v4-pro:fmg_secondary_017, deepseek/deepseek-v4-pro:fmg_secondary_021, deepseek/deepseek-v4-pro:fmg_tertiary_003, deepseek/deepseek-v4-pro:fmg_tertiary_007, deepseek/deepseek-v4-pro:fmg_tertiary_015, deepseek/deepseek-v4-pro:fmg_tertiary_019, deepseek/deepseek-v4-pro:gp_002_church_fathers, deepseek/deepseek-v4-pro:mt_002_pornography_accountability, deepseek/deepseek-v4-pro:pf_002_catholic_marian, deepseek/deepseek-v4-pro:tf_primary_003_scripture_authority, google/gemini-3.1-pro-preview:ch_002_eucharist, google/gemini-3.1-pro-preview:fmg_pastoral_006, google/gemini-3.1-pro-preview:fmg_pastoral_014, google/gemini-3.1-pro-preview:fmg_primary_002, google/gemini-3.1-pro-preview:fmg_primary_006, google/gemini-3.1-pro-preview:fmg_primary_014, google/gemini-3.1-pro-preview:fmg_primary_018, google/gemini-3.1-pro-preview:fmg_secondary_001, google/gemini-3.1-pro-preview:fmg_secondary_013, google/gemini-3.1-pro-preview:fmg_secondary_017, google/gemini-3.1-pro-preview:fmg_secondary_021, google/gemini-3.1-pro-preview:fmg_tertiary_003, google/gemini-3.1-pro-preview:gp_002_church_fathers, google/gemini-3.1-pro-preview:mt_002_pornography_accountability, google/gemini-3.1-pro-preview:pf_002_catholic_marian, google/gemini-3.1-pro-preview:tf_primary_003_scripture_authority, meta-llama/llama-4-maverick:ch_002_eucharist, meta-llama/llama-4-maverick:ee_002_abuse_disclosure, meta-llama/llama-4-maverick:fmg_pastoral_006, meta-llama/llama-4-maverick:fmg_pastoral_010, meta-llama/llama-4-maverick:fmg_pastoral_014, meta-llama/llama-4-maverick:fmg_pastoral_018, meta-llama/llama-4-maverick:fmg_pastoral_022 ... (194 more; see synthetic_vs_judge_delta.csv)

## Signals for Paper

- Target production artifacts: 14 latest model artifacts.
- Overall judge-synthetic MAE is 9.47 points across 1680 scenario-condition items.
- Largest triage gap is primary at 13.18 MAE.
- 617 of 1680 items exceeded the 10-point priority-review threshold.
- Exact majority failure-tag agreement is 54.4%.
