# LLM vs Physician Cause-of-Death Coding Agreement

## Evaluation Design

- Evaluation 1: EXP1 versus PHY, combined narrative.
- Evaluation 2: EXP3 versus PHY, original verbal narrative only.
- Evaluation 3: EXP2 versus EXP1 versus PHY, questionnaire data without verbal narrative.
- Evaluation 4: EXP2 versus EXP4 versus PHY, semantically restructured questionnaire text.

## Main Agreement Summary

| evaluation | metric_type | comparison | n_compared | n_agree | agreement_pct |
| --- | --- | --- | --- | --- | --- |
| Evaluation 1: EXP1 vs PHY | direct | EXP1_direct vs PHY_direct | 330 | 121 | 36.7 |
| Evaluation 1: EXP1 vs PHY | underlying | EXP1_underlying vs PHY_underlying | 3866 | 2127 | 55.0 |
| Evaluation 1: EXP1 vs PHY | contributory | EXP1_contrib_set contains PHY_contrib | 254 | 128 | 50.4 |
| Evaluation 2: EXP3 vs PHY | direct | EXP3_direct vs PHY_direct | 309 | 122 | 39.5 |
| Evaluation 2: EXP3 vs PHY | underlying | EXP3_underlying vs PHY_underlying | 3579 | 1827 | 51.0 |
| Evaluation 2: EXP3 vs PHY | contributory | EXP3_contrib_set contains PHY_contrib | 179 | 76 | 42.5 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | direct | EXP2_direct vs PHY_direct | 328 | 92 | 28.0 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | underlying | EXP2_underlying vs PHY_underlying | 3857 | 1730 | 44.9 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | contributory | EXP2_contrib_set contains PHY_contrib | 231 | 111 | 48.1 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | direct | EXP1_direct vs PHY_direct | 330 | 121 | 36.7 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | underlying | EXP1_underlying vs PHY_underlying | 3866 | 2127 | 55.0 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | contributory | EXP1_contrib_set contains PHY_contrib | 254 | 128 | 50.4 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | direct | EXP2_direct vs PHY_direct | 328 | 92 | 28.0 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | underlying | EXP2_underlying vs PHY_underlying | 3857 | 1730 | 44.9 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | contributory | EXP2_contrib_set contains PHY_contrib | 231 | 111 | 48.1 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | direct | EXP4_direct vs PHY_direct | 329 | 82 | 24.9 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | underlying | EXP4_underlying vs PHY_underlying | 3863 | 1729 | 44.8 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | contributory | EXP4_contrib_set contains PHY_contrib | 234 | 134 | 57.3 |

## LLM-to-LLM Agreement

| evaluation | metric_type | comparison | n_compared | n_agree | agreement_pct | n_exact_set_agree | exact_set_agreement_pct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Evaluation 3: EXP2 vs EXP1 vs PHY | direct_llm_pair | EXP2_direct vs EXP1_direct | 5133 | 2018 | 39.3 |  |  |
| Evaluation 3: EXP2 vs EXP1 vs PHY | underlying_llm_pair | EXP2_underlying vs EXP1_underlying | 5140 | 2799 | 54.5 |  |  |
| Evaluation 3: EXP2 vs EXP1 vs PHY | contributory_llm_pair | EXP2_contrib_set vs EXP1_contrib_set | 3837 | 2368 | 61.7 | 504.0 | 13.1 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | direct_llm_pair | EXP2_direct vs EXP4_direct | 5126 | 2729 | 53.2 |  |  |
| Evaluation 4: EXP2 vs EXP4 vs PHY | underlying_llm_pair | EXP2_underlying vs EXP4_underlying | 5135 | 3525 | 68.6 |  |  |
| Evaluation 4: EXP2 vs EXP4 vs PHY | contributory_llm_pair | EXP2_contrib_set vs EXP4_contrib_set | 3540 | 2684 | 75.8 | 776.0 | 21.9 |

## Kappa, Precision, Recall, F1

| evaluation | metric_type | level | comparison | accuracy | cohen_kappa | precision_macro | recall_macro | f1_macro | precision_weighted | recall_weighted | f1_weighted |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Evaluation 1: EXP1 vs PHY | direct | full | EXP1_direct vs PHY_direct | 0.3667 | 0.3414 | 0.2238 | 0.2713 | 0.203 | 0.5052 | 0.3667 | 0.3931 |
| Evaluation 1: EXP1 vs PHY | direct | level2 | EXP1_direct vs PHY_direct | 0.5515 | 0.4772 | 0.2929 | 0.3802 | 0.2672 | 0.6728 | 0.5515 | 0.5863 |
| Evaluation 1: EXP1 vs PHY | direct | level1 | EXP1_direct vs PHY_direct | 0.7364 | 0.5637 | 0.6046 | 0.5667 | 0.5809 | 0.7642 | 0.7364 | 0.741 |
| Evaluation 1: EXP1 vs PHY | underlying | full | EXP1_underlying vs PHY_underlying | 0.5502 | 0.5247 | 0.3538 | 0.3857 | 0.336 | 0.6201 | 0.5502 | 0.5537 |
| Evaluation 1: EXP1 vs PHY | underlying | level2 | EXP1_underlying vs PHY_underlying | 0.725 | 0.6884 | 0.4586 | 0.4974 | 0.4532 | 0.7516 | 0.725 | 0.7299 |
| Evaluation 1: EXP1 vs PHY | underlying | level1 | EXP1_underlying vs PHY_underlying | 0.8655 | 0.7972 | 0.6755 | 0.7178 | 0.683 | 0.8793 | 0.8655 | 0.8704 |
| Evaluation 1: EXP1 vs PHY | contributory | full | EXP1_contrib_set vs PHY_contrib | 0.1206 | 0.0743 | 0.0753 | 0.1116 | 0.0844 | 0.4002 | 0.4981 | 0.4337 |
| Evaluation 1: EXP1 vs PHY | contributory | level2 | EXP1_contrib_set vs PHY_contrib | 0.1907 | 0.1121 | 0.1098 | 0.2182 | 0.1345 | 0.4806 | 0.6498 | 0.5377 |
| Evaluation 1: EXP1 vs PHY | contributory | level1 | EXP1_contrib_set vs PHY_contrib | 0.537 | 0.1866 | 0.2371 | 0.3492 | 0.2757 | 0.7407 | 0.8833 | 0.7952 |
| Evaluation 2: EXP3 vs PHY | direct | full | EXP3_direct vs PHY_direct | 0.3697 | 0.3447 | 0.2657 | 0.2818 | 0.2247 | 0.5534 | 0.3697 | 0.41 |
| Evaluation 2: EXP3 vs PHY | direct | level2 | EXP3_direct vs PHY_direct | 0.4818 | 0.4061 | 0.3119 | 0.3585 | 0.2597 | 0.6611 | 0.4818 | 0.5336 |
| Evaluation 2: EXP3 vs PHY | direct | level1 | EXP3_direct vs PHY_direct | 0.6727 | 0.4902 | 0.5988 | 0.4819 | 0.5283 | 0.7789 | 0.6727 | 0.7088 |
| Evaluation 2: EXP3 vs PHY | underlying | full | EXP3_underlying vs PHY_underlying | 0.4726 | 0.4498 | 0.3443 | 0.3367 | 0.3075 | 0.6251 | 0.4726 | 0.5021 |
| Evaluation 2: EXP3 vs PHY | underlying | level2 | EXP3_underlying vs PHY_underlying | 0.6381 | 0.5964 | 0.4133 | 0.4077 | 0.3865 | 0.7331 | 0.6381 | 0.6691 |
| Evaluation 2: EXP3 vs PHY | underlying | level1 | EXP3_underlying vs PHY_underlying | 0.7853 | 0.6891 | 0.58 | 0.5553 | 0.5605 | 0.8658 | 0.7853 | 0.8209 |
| Evaluation 2: EXP3 vs PHY | contributory | full | EXP3_contrib_set vs PHY_contrib | 0.1323 | 0.0874 | 0.1034 | 0.1182 | 0.0972 | 0.425 | 0.2957 | 0.3332 |
| Evaluation 2: EXP3 vs PHY | contributory | level2 | EXP3_contrib_set vs PHY_contrib | 0.214 | 0.1487 | 0.1685 | 0.2117 | 0.1686 | 0.5371 | 0.4008 | 0.4417 |
| Evaluation 2: EXP3 vs PHY | contributory | level1 | EXP3_contrib_set vs PHY_contrib | 0.4475 | 0.1536 | 0.272 | 0.2561 | 0.2584 | 0.7396 | 0.572 | 0.6405 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | direct | full | EXP2_direct vs PHY_direct | 0.2788 | 0.2514 | 0.2525 | 0.2003 | 0.1858 | 0.4687 | 0.2788 | 0.3174 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | direct | level2 | EXP2_direct vs PHY_direct | 0.5 | 0.4224 | 0.3379 | 0.3008 | 0.2713 | 0.6521 | 0.5 | 0.5521 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | direct | level1 | EXP2_direct vs PHY_direct | 0.6364 | 0.4513 | 0.5884 | 0.396 | 0.4651 | 0.7823 | 0.6364 | 0.6926 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | underlying | full | EXP2_underlying vs PHY_underlying | 0.4475 | 0.4155 | 0.302 | 0.2651 | 0.2477 | 0.5589 | 0.4475 | 0.4666 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | underlying | level2 | EXP2_underlying vs PHY_underlying | 0.5975 | 0.5416 | 0.3698 | 0.3071 | 0.3052 | 0.6745 | 0.5975 | 0.6105 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | underlying | level1 | EXP2_underlying vs PHY_underlying | 0.8151 | 0.7185 | 0.571 | 0.5636 | 0.5593 | 0.8415 | 0.8151 | 0.8232 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | contributory | full | EXP2_contrib_set vs PHY_contrib | 0.0973 | 0.0406 | 0.0485 | 0.0751 | 0.0519 | 0.3658 | 0.4319 | 0.3774 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | contributory | level2 | EXP2_contrib_set vs PHY_contrib | 0.1595 | 0.0829 | 0.0895 | 0.1698 | 0.1084 | 0.4422 | 0.5914 | 0.494 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | contributory | level1 | EXP2_contrib_set vs PHY_contrib | 0.4669 | 0.0695 | 0.161 | 0.2224 | 0.1794 | 0.7105 | 0.7938 | 0.738 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | direct | full | EXP1_direct vs PHY_direct | 0.3667 | 0.3414 | 0.2238 | 0.2713 | 0.203 | 0.5052 | 0.3667 | 0.3931 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | direct | level2 | EXP1_direct vs PHY_direct | 0.5515 | 0.4772 | 0.2929 | 0.3802 | 0.2672 | 0.6728 | 0.5515 | 0.5863 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | direct | level1 | EXP1_direct vs PHY_direct | 0.7364 | 0.5637 | 0.6046 | 0.5667 | 0.5809 | 0.7642 | 0.7364 | 0.741 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | underlying | full | EXP1_underlying vs PHY_underlying | 0.5502 | 0.5247 | 0.3538 | 0.3857 | 0.336 | 0.6201 | 0.5502 | 0.5537 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | underlying | level2 | EXP1_underlying vs PHY_underlying | 0.725 | 0.6884 | 0.4586 | 0.4974 | 0.4532 | 0.7516 | 0.725 | 0.7299 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | underlying | level1 | EXP1_underlying vs PHY_underlying | 0.8655 | 0.7972 | 0.6755 | 0.7178 | 0.683 | 0.8793 | 0.8655 | 0.8704 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | contributory | full | EXP1_contrib_set vs PHY_contrib | 0.1206 | 0.0743 | 0.0753 | 0.1116 | 0.0844 | 0.4002 | 0.4981 | 0.4337 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | contributory | level2 | EXP1_contrib_set vs PHY_contrib | 0.1907 | 0.1121 | 0.1098 | 0.2182 | 0.1345 | 0.4806 | 0.6498 | 0.5377 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | contributory | level1 | EXP1_contrib_set vs PHY_contrib | 0.537 | 0.1866 | 0.2371 | 0.3492 | 0.2757 | 0.7407 | 0.8833 | 0.7952 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | direct | full | EXP2_direct vs PHY_direct | 0.2788 | 0.2514 | 0.2525 | 0.2003 | 0.1858 | 0.4687 | 0.2788 | 0.3174 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | direct | level2 | EXP2_direct vs PHY_direct | 0.5 | 0.4224 | 0.3379 | 0.3008 | 0.2713 | 0.6521 | 0.5 | 0.5521 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | direct | level1 | EXP2_direct vs PHY_direct | 0.6364 | 0.4513 | 0.5884 | 0.396 | 0.4651 | 0.7823 | 0.6364 | 0.6926 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | underlying | full | EXP2_underlying vs PHY_underlying | 0.4475 | 0.4155 | 0.302 | 0.2651 | 0.2477 | 0.5589 | 0.4475 | 0.4666 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | underlying | level2 | EXP2_underlying vs PHY_underlying | 0.5975 | 0.5416 | 0.3698 | 0.3071 | 0.3052 | 0.6745 | 0.5975 | 0.6105 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | underlying | level1 | EXP2_underlying vs PHY_underlying | 0.8151 | 0.7185 | 0.571 | 0.5636 | 0.5593 | 0.8415 | 0.8151 | 0.8232 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | contributory | full | EXP2_contrib_set vs PHY_contrib | 0.0973 | 0.0406 | 0.0485 | 0.0751 | 0.0519 | 0.3658 | 0.4319 | 0.3774 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | contributory | level2 | EXP2_contrib_set vs PHY_contrib | 0.1595 | 0.0829 | 0.0895 | 0.1698 | 0.1084 | 0.4422 | 0.5914 | 0.494 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | contributory | level1 | EXP2_contrib_set vs PHY_contrib | 0.4669 | 0.0695 | 0.161 | 0.2224 | 0.1794 | 0.7105 | 0.7938 | 0.738 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | direct | full | EXP4_direct vs PHY_direct | 0.2485 | 0.2215 | 0.1433 | 0.1332 | 0.1103 | 0.409 | 0.2485 | 0.2776 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | direct | level2 | EXP4_direct vs PHY_direct | 0.4424 | 0.3568 | 0.2138 | 0.1894 | 0.1735 | 0.5777 | 0.4424 | 0.4926 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | direct | level1 | EXP4_direct vs PHY_direct | 0.6242 | 0.4245 | 0.544 | 0.3614 | 0.4146 | 0.7392 | 0.6242 | 0.6708 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | underlying | full | EXP4_underlying vs PHY_underlying | 0.4472 | 0.4139 | 0.2957 | 0.252 | 0.2423 | 0.5483 | 0.4472 | 0.4625 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | underlying | level2 | EXP4_underlying vs PHY_underlying | 0.6009 | 0.544 | 0.3742 | 0.2911 | 0.2976 | 0.6746 | 0.6009 | 0.6121 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | underlying | level1 | EXP4_underlying vs PHY_underlying | 0.8099 | 0.7105 | 0.5768 | 0.5451 | 0.5554 | 0.8425 | 0.8099 | 0.8208 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | contributory | full | EXP4_contrib_set vs PHY_contrib | 0.0623 | 0.0497 | 0.0527 | 0.0928 | 0.0605 | 0.3775 | 0.5214 | 0.4136 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | contributory | level2 | EXP4_contrib_set vs PHY_contrib | 0.1051 | 0.0821 | 0.0866 | 0.1866 | 0.1065 | 0.4471 | 0.6381 | 0.5104 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | contributory | level1 | EXP4_contrib_set vs PHY_contrib | 0.4708 | 0.0912 | 0.3012 | 0.2404 | 0.2109 | 0.7263 | 0.8132 | 0.7455 |

## Flexible Any-Type Overlap

| evaluation | experiment | comparison | level | n_excluded_blank_reference | n_compared | n_exact_set_agree | exact_set_agreement | n_any_overlap | any_overlap | cohen_kappa | precision_micro | recall_micro | f1_micro | precision_macro | recall_macro | f1_macro | precision_weighted | recall_weighted | f1_weighted |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Evaluation 1: EXP1 vs PHY | EXP1 | EXP1_pooled_any_type vs PHY_pooled_any_type | full | 1268 | 3882 | 288 | 0.0742 | 2805 | 0.7226 | 0.2634 | 0.2548 | 0.7054 | 0.3743 | 0.2309 | 0.4428 | 0.2707 | 0.4642 | 0.7054 | 0.5205 |
| Evaluation 1: EXP1 vs PHY | EXP1 | EXP1_pooled_any_type vs PHY_pooled_any_type | level2 | 1268 | 3882 | 612 | 0.1577 | 3371 | 0.8684 | 0.3317 | 0.3458 | 0.8542 | 0.4923 | 0.2892 | 0.548 | 0.3434 | 0.5344 | 0.8542 | 0.6265 |
| Evaluation 1: EXP1 vs PHY | EXP1 | EXP1_pooled_any_type vs PHY_pooled_any_type | level1 | 1268 | 3882 | 1620 | 0.4173 | 3776 | 0.9727 | 0.459 | 0.6138 | 0.9679 | 0.7512 | 0.461 | 0.6797 | 0.5322 | 0.6798 | 0.9679 | 0.7882 |
| Evaluation 2: EXP3 vs PHY | EXP3 | EXP3_pooled_any_type vs PHY_pooled_any_type | full | 1268 | 3882 | 487 | 0.1255 | 2394 | 0.6167 | 0.2608 | 0.2813 | 0.5925 | 0.3815 | 0.2446 | 0.3896 | 0.2675 | 0.4979 | 0.5925 | 0.4937 |
| Evaluation 2: EXP3 vs PHY | EXP3 | EXP3_pooled_any_type vs PHY_pooled_any_type | level2 | 1268 | 3882 | 858 | 0.221 | 2906 | 0.7486 | 0.3162 | 0.387 | 0.7254 | 0.5047 | 0.2906 | 0.4763 | 0.3266 | 0.5742 | 0.7254 | 0.6063 |
| Evaluation 2: EXP3 vs PHY | EXP3 | EXP3_pooled_any_type vs PHY_pooled_any_type | level1 | 1268 | 3882 | 1821 | 0.4691 | 3371 | 0.8684 | 0.3901 | 0.6094 | 0.8555 | 0.7118 | 0.4175 | 0.5269 | 0.4474 | 0.7269 | 0.8555 | 0.7745 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | EXP2 | EXP2_pooled_any_type vs PHY_pooled_any_type | full | 1268 | 3882 | 351 | 0.0904 | 2287 | 0.5891 | 0.2089 | 0.2339 | 0.571 | 0.3319 | 0.2295 | 0.3007 | 0.2167 | 0.4652 | 0.571 | 0.4605 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | EXP2 | EXP2_pooled_any_type vs PHY_pooled_any_type | level2 | 1268 | 3882 | 661 | 0.1703 | 2833 | 0.7298 | 0.2583 | 0.322 | 0.716 | 0.4442 | 0.2975 | 0.3551 | 0.2704 | 0.5363 | 0.716 | 0.5652 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | EXP2 | EXP2_pooled_any_type vs PHY_pooled_any_type | level1 | 1268 | 3882 | 1577 | 0.4062 | 3577 | 0.9214 | 0.4074 | 0.5821 | 0.9134 | 0.711 | 0.439 | 0.5412 | 0.4745 | 0.6832 | 0.9134 | 0.7686 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | EXP1 | EXP1_pooled_any_type vs PHY_pooled_any_type | full | 1268 | 3882 | 288 | 0.0742 | 2805 | 0.7226 | 0.2634 | 0.2548 | 0.7054 | 0.3743 | 0.2309 | 0.4428 | 0.2707 | 0.4642 | 0.7054 | 0.5205 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | EXP1 | EXP1_pooled_any_type vs PHY_pooled_any_type | level2 | 1268 | 3882 | 612 | 0.1577 | 3371 | 0.8684 | 0.3317 | 0.3458 | 0.8542 | 0.4923 | 0.2892 | 0.548 | 0.3434 | 0.5344 | 0.8542 | 0.6265 |
| Evaluation 3: EXP2 vs EXP1 vs PHY | EXP1 | EXP1_pooled_any_type vs PHY_pooled_any_type | level1 | 1268 | 3882 | 1620 | 0.4173 | 3776 | 0.9727 | 0.459 | 0.6138 | 0.9679 | 0.7512 | 0.461 | 0.6797 | 0.5322 | 0.6798 | 0.9679 | 0.7882 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | EXP2 | EXP2_pooled_any_type vs PHY_pooled_any_type | full | 1268 | 3882 | 351 | 0.0904 | 2287 | 0.5891 | 0.2089 | 0.2339 | 0.571 | 0.3319 | 0.2295 | 0.3007 | 0.2167 | 0.4652 | 0.571 | 0.4605 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | EXP2 | EXP2_pooled_any_type vs PHY_pooled_any_type | level2 | 1268 | 3882 | 661 | 0.1703 | 2833 | 0.7298 | 0.2583 | 0.322 | 0.716 | 0.4442 | 0.2975 | 0.3551 | 0.2704 | 0.5363 | 0.716 | 0.5652 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | EXP2 | EXP2_pooled_any_type vs PHY_pooled_any_type | level1 | 1268 | 3882 | 1577 | 0.4062 | 3577 | 0.9214 | 0.4074 | 0.5821 | 0.9134 | 0.711 | 0.439 | 0.5412 | 0.4745 | 0.6832 | 0.9134 | 0.7686 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | EXP4 | EXP4_pooled_any_type vs PHY_pooled_any_type | full | 1268 | 3882 | 258 | 0.0665 | 2352 | 0.6059 | 0.2076 | 0.2302 | 0.5875 | 0.3308 | 0.2216 | 0.3087 | 0.2157 | 0.4452 | 0.5875 | 0.4575 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | EXP4 | EXP4_pooled_any_type vs PHY_pooled_any_type | level2 | 1268 | 3882 | 573 | 0.1476 | 2895 | 0.7457 | 0.2619 | 0.3179 | 0.7317 | 0.4432 | 0.2941 | 0.3672 | 0.275 | 0.5111 | 0.7317 | 0.5594 |
| Evaluation 4: EXP2 vs EXP4 vs PHY | EXP4 | EXP4_pooled_any_type vs PHY_pooled_any_type | level1 | 1268 | 3882 | 1563 | 0.4026 | 3595 | 0.9261 | 0.4049 | 0.5823 | 0.9178 | 0.7126 | 0.4353 | 0.5371 | 0.4724 | 0.6784 | 0.9178 | 0.769 |

## Data Quality

| item | value |
| --- | --- |
| records_in_master | 5150 |
| unique_idents_in_master | 5150 |
| EXP1_parse_methods | {'json': 5150} |
| EXP2_parse_methods | {'columns': 5150} |
| EXP3_parse_methods | {'columns': 5150} |
| EXP4_parse_methods | {'columns': 5150} |
| PHY_direct_missing | 4820 |
| PHY_underlying_missing | 1284 |
| PHY_contrib_missing | 4893 |

Notes: Blank PHY reference determinations are excluded from the kappa/precision/recall/F1 comparisons. Level 1 uses the first two digits of the code; Level 2 uses the first four digits (shown as NN-NN). Direct and underlying metrics are single-label multiclass metrics. Contributory metrics are multi-label because LLM contributory output can contain multiple codes; contributory kappa is the macro average of one-vs-rest label kappas. Flexible any-type overlap pools direct, underlying, and contributory codes within each case before comparison.
