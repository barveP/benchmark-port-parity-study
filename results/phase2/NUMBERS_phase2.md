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
| RQ1 P(pass) for a 2-point gap by common SD, k=3 | `{"0.25": 0.0, "0.5": 0.02, "1": 0.38, "1.5": 0.62, "2": 0.74, "3": 0.82, "5": 0.87, "10": 0.89, "100": 0.9}` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 P(pass), port side noisier only | `{"0.25": 0.52, "0.5": 0.62, "1": 0.73, "2": 0.81, "4": 0.82, "8": 0.8, "32": 0.76, "100": 0.75}` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 discrete false alarm by n tasks (k=3, p=0.3) | `{"10": 0.049, "30": 0.067, "50": 0.072, "100": 0.08, "300": 0.089, "1000": 0.092}` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 realistic medians (light prior) | `{"light,k=3,gap=0": {"R": 0.07, "S1": 0.25, "S2": 0.37, "S3": 0.43, "W": 0.03, "T": 0.05, "E3": 0.08, "E5": 0.45}, "light,k=3,gap=2": {"R": 0.17, "S1": 0.43, "S2": 0.55, "S3": 0.61, "W": 0.09, "T": 0.12, "E3": 0.05, "E5": 0.3}, "light,k=3,gap=5": {"R": 0.57, "S1": 0.86, "S2": 0.93, "S3": 0.94, "W": 0.37, "T": 0.47, "E3": 0.0, "E5": 0.05}, "light,k=5,gap=5": {"R": 0.32, "S1": 0.96, "S2": 0.99, "S3": 0.99, "W": 0.78, "T": 0.8, "E3": 0.0, "E5": 0.05}, "beta11,k=3,gap=0": {"R": 0.08, "S1": 0.25, "S2": 0.37, "S3": 0.43, "W": 0.03, "T": 0.05, "E3": 0.01, "E5": 0.1}, "beta11,k=3,gap=5": {"R": 0.33, "S1": 0.63, "S2": 0.75, "S3": 0.79, "W": 0.18, "T": 0.23, "E3": 0.0, "E5": 0.03}}` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
| RQ1 realistic implied run SD quartiles | `{"light": [1.52, 2.07, 2.82], "beta11": [2.63, 3.26, 4.53]}` | `scripts/p2_rq1_rules.py` | `results/phase2/rq1_rules.json` |
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
| RQ2 selection check (expected, observed, p) | `{"R": [5.8, 1, 0.017], "S1": [14.8, 4, 0.0], "S2": [21.7, 12, 0.005], "S3": [25.4, 18, 0.032], "W": [2.0, 0, 0.129], "T": [2.9, 0, 0.052]}` | `scripts/p2_rq2_evidence.py` | `results/phase2/rq2_summary.json` |
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
| RQ3 per-comparison runs for ±3 at gap 0 (quartiles; share <=3, <=5, <=10) | `[[4.0, 7.0, 13.25], 0.21428571428571427, 0.4107142857142857, 0.6428571428571429]` | `scripts/p2_rq3_runs_needed.py` | `results/phase2/rq3_runs_needed.json` |
| RQ3 comparisons whose gap exceeds the margin (±2, ±3, ±5) | `{"m=2": 14, "m=3": 4, "m=5": 4}` | `scripts/p2_rq3_runs_needed.py` | `results/phase2/rq3_runs_needed.json` |
| RQ3 paired: n_adapters_with_both_sides | `32` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired: n_adapters_skipped | `12` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired: validation_both_match | `21` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired: sides_swapped_vs_published | `[]` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired: paired_margin_quartiles | `[3.16, 4.48, 5.73]` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired: run_margin_quartiles | `[2.21, 3.17, 5.9]` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired: width_ratio_quartiles | `[0.49, 0.71, 1.33]` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired: paired_within | `{"1": 1, "2": 3, "3": 7, "5": 21}` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired: run_within | `{"1": 1, "2": 5, "3": 15, "5": 21}` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 paired: paired_gap_distinguishable_95 | `0` | `scripts/p2_rq3_paired.py` | `results/phase2/rq3_paired.json` |
| RQ3 defects: adapters, replications | `[39, 2000]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects break,f=0.0,k=3: gap, R, S1, T, paired, E3, E5 | `[0.0, 0.07, 0.25, 0.05, 0.05, 0.21, 0.49]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects break,f=0.02,k=3: gap, R, S1, T, paired, E3, E5 | `[-1.1, 0.14, 0.36, 0.1, 0.1, 0.16, 0.45]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects break,f=0.05,k=3: gap, R, S1, T, paired, E3, E5 | `[-2.6, 0.34, 0.58, 0.29, 0.26, 0.05, 0.29]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects break,f=0.1,k=3: gap, R, S1, T, paired, E3, E5 | `[-5.4, 0.61, 0.8, 0.56, 0.52, 0.01, 0.08]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects break,f=0.2,k=3: gap, R, S1, T, paired, E3, E5 | `[-10.9, 0.85, 0.93, 0.83, 0.8, 0.0, 0.02]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects leak,f=0.1,k=3: gap, R, S1, T, paired, E3, E5 | `[4.6, 0.58, 0.78, 0.52, 0.48, 0.03, 0.15]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects break,f=0.1,k=5: gap, R, S1, T, paired, E3, E5 | `[-5.4, 0.47, 0.85, 0.72, 0.59, 0.02, 0.13]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects break,f=0.1,k=10: gap, R, S1, T, paired, E3, E5 | `[-5.5, 0.33, 0.9, 0.85, 0.66, 0.03, 0.2]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects break,f=0.0,k=5: gap, R, S1, T, paired, E3, E5 | `[0.0, 0.0, 0.21, 0.05, 0.05, 0.36, 0.71]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects break,f=0.0,k=10: gap, R, S1, T, paired, E3, E5 | `[0.0, 0.0, 0.18, 0.05, 0.05, 0.63, 0.92]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
| RQ3 defects beta11,break,f=0.1,k=3: gap, R, S1, T, paired, E3, E5 | `[-5.2, 0.42, 0.67, 0.33, 0.38, 0.0, 0.03]` | `scripts/p2_rq3_defects.py` | `results/phase2/rq3_defects.json` |
