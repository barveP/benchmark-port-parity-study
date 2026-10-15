# Phase 2 numbers: value, script, output

| Number | Value | Script | Output |
|---|---|---|---|
| RQ1 false alarm at k=3, R | `0.099` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 detect 2 SD at k=3, R | `0.623` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 t-statistic at R's false alarm detects 2 SD | `0.642` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 false alarm at k=3, S1 | `0.254` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 detect 2 SD at k=3, S1 | `0.861` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 t-statistic at S1's false alarm detects 2 SD | `0.863` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 false alarm at k=3, S2 | `0.374` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 detect 2 SD at k=3, S2 | `0.924` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 t-statistic at S2's false alarm detects 2 SD | `0.924` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 false alarm at k=3, S3 | `0.439` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 detect 2 SD at k=3, S3 | `0.942` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 t-statistic at S3's false alarm detects 2 SD | `0.943` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 false alarm at k=3, T | `0.05` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 detect 2 SD at k=3, T | `0.462` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 t-statistic at T's false alarm detects 2 SD | `0.462` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 false alarm at k=3, W | `0.035` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 detect 2 SD at k=3, W | `0.367` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 t-statistic at W's false alarm detects 2 SD | `0.377` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 R false alarm by k | `{"2": 0.333, "3": 0.1, "4": 0.029, "5": 0.008, "6": 0.002, "8": 0.0, "10": 0.0}` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 R detects 2 SD by k | `{"2": 0.78, "3": 0.62, "4": 0.49, "5": 0.38, "6": 0.29, "8": 0.16, "10": 0.09}` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 T detects 2 SD by k | `{"2": 0.22, "3": 0.46, "4": 0.66, "5": 0.79, "6": 0.88, "8": 0.96, "10": 0.99}` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 P(pass) for a 2-point gap by common SD, k=3 | `{"0.25": 0.0, "0.5": 0.02, "1": 0.38, "1.5": 0.62, "1.7": 0.68, "2": 0.74, "3": 0.82, "5": 0.87, "10": 0.89, "100": 0.9}` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 P(pass), port side noisier only | `{"0": 0.4, "0.25": 0.51, "0.5": 0.61, "1": 0.74, "2": 0.81, "3": 0.82, "4": 0.82, "8": 0.8, "32": 0.77, "100": 0.76}` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 discrete false alarm by n tasks (k=3, p=0.3) | `{"10": 0.05, "30": 0.066, "50": 0.073, "100": 0.079, "300": 0.088, "1000": 0.093}` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 realistic medians (light prior) | `{"light,k=3,gap=0": {"R": 0.07, "S1": 0.25, "S2": 0.37, "S3": 0.43, "W": 0.03, "T": 0.05, "E3": 0.1, "E5": 0.5}, "light,k=3,gap=2": {"R": 0.17, "S1": 0.43, "S2": 0.56, "S3": 0.62, "W": 0.09, "T": 0.12, "E3": 0.05, "E5": 0.32}, "light,k=3,gap=5": {"R": 0.58, "S1": 0.87, "S2": 0.93, "S3": 0.95, "W": 0.38, "T": 0.47, "E3": 0.0, "E5": 0.05}, "light,k=5,gap=5": {"R": 0.33, "S1": 0.96, "S2": 0.99, "S3": 0.99, "W": 0.78, "T": 0.8, "E3": 0.0, "E5": 0.05}, "beta11,k=3,gap=0": {"R": 0.08, "S1": 0.25, "S2": 0.37, "S3": 0.43, "W": 0.03, "T": 0.05, "E3": 0.01, "E5": 0.09}, "beta11,k=3,gap=5": {"R": 0.32, "S1": 0.61, "S2": 0.73, "S3": 0.77, "W": 0.17, "T": 0.23, "E3": 0.0, "E5": 0.03}}` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 realistic model run SD quartiles (100 sqrt(sum p(1-p))/n) | `{"light": [1.72, 2.25, 3.14], "beta11": [2.95, 3.81, 5.0]}` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 expected smallest provable margin under parity, k=3 (SD units) | `2.29` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 runs/side for 80% TOST power at gap 0, margin in SD | `{"1": 18, "1.5": 9, "2": 6, "3": 3}` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ2 [k = 3 on both sides] n / median gap / median SD / margin quartiles / within 2,3,5 / fail overlap / S1,S2,S3 / passes with margin>5 | `[58, 0.67, 1.71, [2.4, 4.4, 6.0], [7, 22, 36], 1, [4, 12, 18], 21]` | `scripts/p2_rq2_evidence.py` | `results/phase2/rq2_summary.json` |
| RQ2 [all comparisons with >= 2 runs per side] n / median gap / median SD / margin quartiles / within 2,3,5 / fail overlap / S1,S2,S3 / passes with margin>5 | `[75, 0.67, 1.79, [2.4, 4.4, 6.2], [10, 29, 45], 1, [5, 14, 20], 29]` | `scripts/p2_rq2_evidence.py` | `results/phase2/rq2_summary.json` |
| RQ2 [one comparison per adapter] n / median gap / median SD / margin quartiles / within 2,3,5 / fail overlap / S1,S2,S3 / passes with margin>5 | `[66, 0.67, 1.74, [2.4, 4.4, 6.0], [9, 26, 40], 1, [5, 14, 20], 25]` | `scripts/p2_rq2_evidence.py` | `results/phase2/rq2_summary.json` |
| RQ2 [k = 3, row matches the paper table] n / median gap / median SD / margin quartiles / within 2,3,5 / fail overlap / S1,S2,S3 / passes with margin>5 | `[37, 0.58, 1.49, [2.2, 3.4, 5.8], [5, 17, 26], 1, [3, 9, 10], 10]` | `scripts/p2_rq2_evidence.py` | `results/phase2/rq2_summary.json` |
| RQ2 [k = 3, parity on a subset] n / median gap / median SD / margin quartiles / within 2,3,5 / fail overlap / S1,S2,S3 / passes with margin>5 | `[22, 0.67, 2.31, [3.2, 5.0, 6.9], [2, 5, 11], 0, [1, 5, 7], 11]` | `scripts/p2_rq2_evidence.py` | `results/phase2/rq2_summary.json` |
| RQ2 [k = 3, parity on the full set] n / median gap / median SD / margin quartiles / within 2,3,5 / fail overlap / S1,S2,S3 / passes with margin>5 | `[34, 0.6, 1.54, [2.3, 3.7, 5.8], [5, 16, 23], 1, [3, 6, 10], 10]` | `scripts/p2_rq2_evidence.py` | `results/phase2/rq2_summary.json` |
| RQ2 [k >= 2 including identical non-constant rows (zero-width intervals excluded)] n / median gap / median SD / margin quartiles / within 2,3,5 / fail overlap / S1,S2,S3 / passes with margin>5 | `[76, 0.67, 1.84, [2.4, 4.4, 6.4], [10, 29, 45], 1, [5, 14, 20], 30]` | `scripts/p2_rq2_evidence.py` | `results/phase2/rq2_summary.json` |
| RQ2 headline within-margin range under ±0.1 perturbation | `{"1": [0, 1], "2": [7, 8], "3": [21, 23], "5": [34, 37], "10": [53, 53]}` | `scripts/p2_rq2_evidence.py` | `results/phase2/rq2_summary.json` |
| RQ2 headline largest gaps (adapter, metric, gap, margin) | `[["frontier-cs-algorithm", "Partial Score (%) (mean over 10 per-group rows)", -15.56, 44.15], ["rexbench", "Final Success Rate", 8.34, 35.47], ["pixiu", "avg_f1", -4.94, 20.28], ["gdb", "macro_reward", 4.57, 11.6]]` | `scripts/p2_rq2_evidence.py` | `results/phase2/rq2_summary.json` |
| RQ2 overlap vs TOST agreement (headline) | `{"m=3": {"overlap_pass_equiv_shown": 22, "overlap_pass_equiv_not_shown": 35, "overlap_fail_equiv_shown": 0, "overlap_fail_equiv_not_shown": 1}, "m=5": {"overlap_pass_equiv_shown": 36, "overlap_pass_equiv_not_shown": 21, "overlap_fail_equiv_shown": 0, "overlap_fail_equiv_not_shown": 1}}` | `scripts/p2_rq2_evidence.py` | `results/phase2/rq2_summary.json` |
| RQ2 selection check (expected, observed, p) | `{"R": [5.8, 1, 0.017], "S1": [14.8, 4, 0.0], "S2": [21.7, 12, 0.005], "S3": [25.4, 18, 0.032], "W": [2.0, 0, 0.129], "T": [2.9, 0, 0.052], "R_ties": [3.9, 1, 0.089]}` | `scripts/p2_rq2_evidence.py` | `results/phase2/rq2_summary.json` |
| RQ2 by k: n and within 3 / 5 | `{"2v2": [7, 2, 2], "3v3": [58, 22, 36], "4v4": [2, 1, 1], "5v5": [5, 1, 3], "6v6": [2, 2, 2], "unequal": [1, 1, 1]}` | `scripts/p2_rq2_evidence.py` | `results/phase2/rq2_summary.json` |
| RQ3 observed pooled SD quartiles (k=3 set) | `[1.12, 1.71, 2.74]` | `scripts/p2_rq3_runs_needed.py` | `results/phase2/rq3_runs_needed.json` |
| RQ3 runs/side sd_p25,gap=0.0,m=2: 80% / 90% power (plug-in k, its power) | `[7, 8, 3, 0.278]` | `scripts/p2_rq3_runs_needed.py` | `results/phase2/rq3_runs_needed.json` |
| RQ3 runs/side sd_p25,gap=0.0,m=3: 80% / 90% power (plug-in k, its power) | `[4, 4, 3, 0.715]` | `scripts/p2_rq3_runs_needed.py` | `results/phase2/rq3_runs_needed.json` |
| RQ3 runs/side sd_p25,gap=0.0,m=5: 80% / 90% power (plug-in k, its power) | `[3, 3, 2, 0.779]` | `scripts/p2_rq3_runs_needed.py` | `results/phase2/rq3_runs_needed.json` |
| RQ3 runs/side sd_p25,gap=0.6,m=2: 80% / 90% power (plug-in k, its power) | `[9, 12, 5, 0.524]` | `scripts/p2_rq3_runs_needed.py` | `results/phase2/rq3_runs_needed.json` |
| RQ3 runs/side sd_p25,gap=0.6,m=3: 80% / 90% power (plug-in k, its power) | `[4, 5, 3, 0.649]` | `scripts/p2_rq3_runs_needed.py` | `results/phase2/rq3_runs_needed.json` |
| RQ3 runs/side sd_p25,gap=0.6,m=5: 80% / 90% power (plug-in k, its power) | `[3, 3, 2, 0.754]` | `scripts/p2_rq3_runs_needed.py` | `results/phase2/rq3_runs_needed.json` |
| RQ3 runs/side sd_p50,gap=0.0,m=2: 80% / 90% power (plug-in k, its power) | `[14, 17, 6, 0.242]` | `scripts/p2_rq3_runs_needed.py` | `results/phase2/rq3_runs_needed.json` |
| RQ3 runs/side sd_p50,gap=0.0,m=3: 80% / 90% power (plug-in k, its power) | `[7, 8, 3, 0.26]` | `scripts/p2_rq3_runs_needed.py` | `results/phase2/rq3_runs_needed.json` |
| RQ3 runs/side sd_p50,gap=0.0,m=5: 80% / 90% power (plug-in k, its power) | `[3, 4, 2, 0.416]` | `scripts/p2_rq3_runs_needed.py` | `results/phase2/rq3_runs_needed.json` |
| RQ3 runs/side sd_p50,gap=0.6,m=2: 80% / 90% power (plug-in k, its power) | `[20, 27, 10, 0.495]` | `scripts/p2_rq3_runs_needed.py` | `results/phase2/rq3_runs_needed.json` |
| RQ3 runs/side sd_p50,gap=0.6,m=3: 80% / 90% power (plug-in k, its power) | `[8, 10, 4, 0.409]` | `scripts/p2_rq3_runs_needed.py` | `results/phase2/rq3_runs_needed.json` |
| RQ3 runs/side sd_p50,gap=0.6,m=5: 80% / 90% power (plug-in k, its power) | `[4, 4, 3, 0.775]` | `scripts/p2_rq3_runs_needed.py` | `results/phase2/rq3_runs_needed.json` |
| RQ3 runs/side sd_p75,gap=0.0,m=2: 80% / 90% power (plug-in k, its power) | `[33, 42, 12, 0.12]` | `scripts/p2_rq3_runs_needed.py` | `results/phase2/rq3_runs_needed.json` |
| RQ3 runs/side sd_p75,gap=0.0,m=3: 80% / 90% power (plug-in k, its power) | `[16, 19, 6, 0.176]` | `scripts/p2_rq3_runs_needed.py` | `results/phase2/rq3_runs_needed.json` |
| RQ3 runs/side sd_p75,gap=0.0,m=5: 80% / 90% power (plug-in k, its power) | `[6, 8, 3, 0.292]` | `scripts/p2_rq3_runs_needed.py` | `results/phase2/rq3_runs_needed.json` |
| RQ3 runs/side sd_p75,gap=0.6,m=2: 80% / 90% power (plug-in k, its power) | `[49, 67, 22, 0.434]` | `scripts/p2_rq3_runs_needed.py` | `results/phase2/rq3_runs_needed.json` |
| RQ3 runs/side sd_p75,gap=0.6,m=3: 80% / 90% power (plug-in k, its power) | `[18, 24, 9, 0.401]` | `scripts/p2_rq3_runs_needed.py` | `results/phase2/rq3_runs_needed.json` |
| RQ3 runs/side sd_p75,gap=0.6,m=5: 80% / 90% power (plug-in k, its power) | `[7, 8, 4, 0.478]` | `scripts/p2_rq3_runs_needed.py` | `results/phase2/rq3_runs_needed.json` |
| RQ3 per-comparison runs for ±3 at gap 0 (quartiles; share <=3, <=5, <=10; n over 400) | `[[4.0, 7.0, 15.5], 0.20689655172413793, 0.39655172413793105, 0.6206896551724138, 2]` | `scripts/p2_rq3_runs_needed.py` | `results/phase2/rq3_runs_needed.json` |
| RQ3 comparisons whose gap exceeds the margin (±2, ±3, ±5) | `{"m=2": 10, "m=3": 4, "m=5": 2}` | `scripts/p2_rq3_runs_needed.py` | `results/phase2/rq3_runs_needed.json` |
| RQ3 paired [primary]: n | `27` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [primary]: n_with_run_interval | `26` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [primary]: validation_both_match | `21` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [primary]: paired_margin_quartiles | `[3.01, 4.54, 5.73]` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [primary]: run_margin_quartiles | `[2.2, 2.91, 5.93]` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [primary]: width_ratio_quartiles | `[0.49, 0.67, 1.27]` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [primary]: width_ratio_null_median_quartiles | `[1.19, 1.2, 1.22]` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [primary]: n_ratio_below_1 | `15` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [primary]: n_ratio_below_null_q25 | `15` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [primary]: paired_within | `{"1": 1, "2": 3, "3": 7, "5": 16}` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [primary]: run_within | `{"1": 1, "2": 4, "3": 14, "5": 17}` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [primary]: n_sd_task_diff_exceeds_noise_p05 | `14` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [primary]: n_sd_task_diff_exceeds_noise_p01 | `10` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [primary]: n_mean_gap_not_exchangeable_p05 | `0` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [primary]: n_cmh_reject | `0` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [primary]: n_binary | `21` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [primary]: paired_gap_distinguishable_95 | `0` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [primary]: dispersion_ratio_harbor_quartiles | `[0.11, 0.36, 1.04]` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [primary]: dispersion_ratio_original_quartiles | `[0.25, 0.5, 0.87]` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [primary]: under_dispersed_below_0.1 | `["adebench", "deepsynth", "kumo", "labbench", "ml_dev_bench", "spider2-dbt", "theagentcompany"]` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [primary]: tasks_always_pass_one_side_fail_other | `{"swebench": 36, "ds1000": 13, "crustbench": 6, "dacode": 6, "kumo": 6, "bfcl": 5, "multi-swe-bench": 5}` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [primary]: discordance_share_quartiles | `[0.25, 0.37, 0.41]` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [secondary_terminal_bench_legs]: n | `4` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [secondary_terminal_bench_legs]: n_with_run_interval | `4` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [secondary_terminal_bench_legs]: validation_both_match | `3` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [secondary_terminal_bench_legs]: paired_margin_quartiles | `[3.42, 4.25, 6.11]` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [secondary_terminal_bench_legs]: run_margin_quartiles | `[3.62, 4.48, 5.53]` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [secondary_terminal_bench_legs]: width_ratio_quartiles | `[0.72, 1.13, 1.42]` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [secondary_terminal_bench_legs]: width_ratio_null_median_quartiles | `[1.16, 1.18, 1.2]` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [secondary_terminal_bench_legs]: n_ratio_below_1 | `2` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [secondary_terminal_bench_legs]: n_ratio_below_null_q25 | `2` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [secondary_terminal_bench_legs]: paired_within | `{"1": 0, "2": 0, "3": 0, "5": 3}` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [secondary_terminal_bench_legs]: run_within | `{"1": 0, "2": 1, "3": 1, "5": 3}` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [secondary_terminal_bench_legs]: n_sd_task_diff_exceeds_noise_p05 | `1` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [secondary_terminal_bench_legs]: n_sd_task_diff_exceeds_noise_p01 | `1` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [secondary_terminal_bench_legs]: n_mean_gap_not_exchangeable_p05 | `0` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [secondary_terminal_bench_legs]: n_cmh_reject | `0` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [secondary_terminal_bench_legs]: n_binary | `4` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [secondary_terminal_bench_legs]: paired_gap_distinguishable_95 | `0` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [secondary_terminal_bench_legs]: dispersion_ratio_harbor_quartiles | `[0.63, 0.91, 1.07]` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [secondary_terminal_bench_legs]: dispersion_ratio_original_quartiles | `[0.71, 1.96, 3.09]` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [secondary_terminal_bench_legs]: under_dispersed_below_0.1 | `["quixbugs"]` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [secondary_terminal_bench_legs]: tasks_always_pass_one_side_fail_other | `{"deveval": 6}` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired [secondary_terminal_bench_legs]: discordance_share_quartiles | `[0.2, 0.3, 0.39]` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 verdict tool examples (USACO, RexBench): printed lines | `["Resolved Rate (%): k=3v3 \| ranges DO NOT overlap (separation +0.1) \| gap +2.63 pts [90%: -0.49, +5.76] [95%: -1.43, +6.70] \| run SD 1.79 \| smallest provable margin ±5.8 pts \| runs/side for 80% power at this noise: ±3 -> 7, ±5 -> 4", "Final Success Rate: k=3v3 \| ranges overlap (separation -16.7) \| gap +8.34 pts [90%: -18.80, +35.47] [95%: -27.00, +43.67] \| run SD 15.59 \| smallest provable margin ±35.5 pts \| runs/side for 80% power at this noise: ±3 -> 464, ±5 -> 168"]` | `scripts/parity_verdict.py` | `results/phase2/verdict_examples.txt` |
| RQ3 dispersion ratio below 0.1 under independent outcomes: n adapters / expected / observed / P(at least observed) / per-adapter prob quartiles | `[30, 2.64, 9, 0.0007, [0.068, 0.088, 0.101]]` | `scripts/p2_rq3_dispersion_null.py` | `results/phase2/rq3_dispersion_null.json` |
| RQ2 headline records dated before the overlap rule entered the guide (2026-04-19): n headline / n dated / n before / n on or after / named | `[58, 58, 51, 7, {"usaco#0": "2025-11-06", "gdb#0": "2026-04-21", "pixiu#0": "2026-03-01", "rexbench#0": "2026-02-28", "frontier-cs-algorithm#0": "2026-04-08"}]` | `scripts/p4_record_dates.py` | `results/phase2/record_dates.json` |
| RQ3 defects: binary adapters, fractional adapters, replications | `[30, 8, 2000]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects: dispersion ratio quartiles of the real Harbor runs (binary adapters) | `[0.1, 0.52, 1.26]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects: adapters with dispersion ratio below 0.1 | `["adebench", "bird_bench", "financeagent", "ineqmath", "kumo", "labbench", "ml_dev_bench", "quixbugs", "satbench"]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects: model run SD quartiles (light prior) | `[1.72, 2.25, 3.14]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects: paired t minus pooled t at break 10%, k=3 (n with P > T; quartiles) | `[6, [-0.053, -0.018, -0.0]]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects break,f=0.0,k=3: gap; mean (median) of R, S1, T, paired t, CMH, E3 shown, E5 shown | `[0.0, "0.07 (0.07)", "0.24 (0.24)", "0.05 (0.05)", "0.05 (0.05)", "0.05 (0.05)", "0.22 (0.10)", "0.51 (0.50)"]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects break,f=0.02,k=3: gap; mean (median) of R, S1, T, paired t, CMH, E3 shown, E5 shown | `[-1.1, "0.15 (0.10)", "0.38 (0.32)", "0.11 (0.07)", "0.10 (0.06)", "0.14 (0.09)", "0.17 (0.10)", "0.47 (0.48)"]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects break,f=0.05,k=3: gap; mean (median) of R, S1, T, paired t, CMH, E3 shown, E5 shown | `[-2.7, "0.37 (0.23)", "0.61 (0.53)", "0.32 (0.18)", "0.29 (0.15)", "0.39 (0.26)", "0.04 (0.03)", "0.29 (0.24)"]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects break,f=0.1,k=3: gap; mean (median) of R, S1, T, paired t, CMH, E3 shown, E5 shown | `[-5.4, "0.64 (0.68)", "0.82 (0.90)", "0.59 (0.58)", "0.54 (0.48)", "0.67 (0.74)", "0.01 (0.00)", "0.07 (0.04)"]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects break,f=0.2,k=3: gap; mean (median) of R, S1, T, paired t, CMH, E3 shown, E5 shown | `[-11.0, "0.87 (0.99)", "0.95 (1.00)", "0.85 (0.98)", "0.82 (0.97)", "0.90 (1.00)", "0.00 (0.00)", "0.02 (0.00)"]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects leak,f=0.05,k=3: gap; mean (median) of R, S1, T, paired t, CMH, E3 shown, E5 shown | `[2.3, "0.29 (0.27)", "0.55 (0.57)", "0.23 (0.20)", "0.21 (0.16)", "0.30 (0.27)", "0.11 (0.04)", "0.37 (0.24)"]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects leak,f=0.1,k=3: gap; mean (median) of R, S1, T, paired t, CMH, E3 shown, E5 shown | `[4.5, "0.58 (0.64)", "0.77 (0.88)", "0.51 (0.55)", "0.48 (0.47)", "0.61 (0.70)", "0.04 (0.00)", "0.18 (0.08)"]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects break,f=0.0,k=5: gap; mean (median) of R, S1, T, paired t, CMH, E3 shown, E5 shown | `[0.0, "0.00 (0.00)", "0.21 (0.21)", "0.05 (0.05)", "0.05 (0.05)", "0.05 (0.05)", "0.37 (0.28)", "0.75 (0.87)"]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects break,f=0.1,k=5: gap; mean (median) of R, S1, T, paired t, CMH, E3 shown, E5 shown | `[-5.4, "0.51 (0.48)", "0.87 (0.97)", "0.75 (0.87)", "0.60 (0.60)", "0.77 (0.91)", "0.02 (0.00)", "0.12 (0.05)"]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects break,f=0.0,k=10: gap; mean (median) of R, S1, T, paired t, CMH, E3 shown, E5 shown | `[0.0, "0.00 (0.00)", "0.18 (0.18)", "0.05 (0.05)", "0.05 (0.05)", "0.05 (0.05)", "0.66 (0.79)", "0.94 (1.00)"]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects break,f=0.1,k=10: gap; mean (median) of R, S1, T, paired t, CMH, E3 shown, E5 shown | `[-5.4, "0.36 (0.19)", "0.92 (1.00)", "0.86 (0.98)", "0.67 (0.78)", "0.86 (0.99)", "0.04 (0.00)", "0.19 (0.07)"]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects sensitivity [binary_dispersion_ratio_ge_0.1] break,f=0.1,k=3: n, mean of R, T, paired t, CMH, E5 | `[21, 0.64, 0.59, 0.56, 0.67, 0.09]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects sensitivity [beta11_break_k3] beta11,break,f=0.1,k=3: n, mean of R, T, paired t, CMH, E5 | `[30, 0.43, 0.34, 0.39, 0.45, 0.03]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects sensitivity [fractional_resample] resample,break,f=0.1,k=3: n, mean of R, T, paired t, CMH, E5 | `[8, 0.72, 0.67, 0.59, 0.53, 0.13]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
