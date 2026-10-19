#!/usr/bin/env python3
"""Phase 4: paper figures and table rows, drawn from the Phase 2 output files only.
Usage: python -I scripts/p4_paper_figures.py <results/phase2 dir> <paper dir>
Writes paper/figures/fig1_rules.pdf, fig2_margins.pdf, fig3_defects.pdf (+ .png previews)
and paper/tab1_rules.tex, paper/tab2_runs.tex, paper/paper_numbers.json.
No number is computed here beyond reading, rounding and counting the Phase 2 outputs.
"""
import csv
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

p2, out = sys.argv[1], sys.argv[2]
figdir = os.path.join(out, "figures")
os.makedirs(figdir, exist_ok=True)
# Paper style: IEEE column widths (3.5 in, 7.16 in), a Times-like serif that matches the IEEEtran body (STIX, which
# ships with matplotlib), text no smaller than 6.5 pt at print size, embedded TrueType fonts, no top or right spines.
# Colours are Okabe-Ito, a colour-blind-safe set, with a fixed colour per test across figures; every series also has
# its own marker and line style so the figures read in greyscale.
COL1, COL2 = 3.5, 7.16
plt.rcParams.update({"font.family": "serif", "font.serif": ["STIXGeneral"], "mathtext.fontset": "stix",
                     "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 6.5,
                     "xtick.labelsize": 7, "ytick.labelsize": 7, "lines.linewidth": 1.1, "lines.markersize": 3,
                     "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
BLUE, ORANGE, GREEN, VERMILLION, PURPLE, GREY = "#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#7f7f7f"

rq1 = json.load(open(os.path.join(p2, "rq1_rules.json")))
runs = json.load(open(os.path.join(p2, "rq3_runs_needed.json")))
defects = json.load(open(os.path.join(p2, "rq3_defects.json")))
comps = list(csv.DictReader(open(os.path.join(p2, "rq2_comparisons.csv"))))
summ = rq1["summary"]
numbers = {}

# ---------- Figure 1: RQ1 ----------
KS = [2, 3, 4, 5, 6, 8, 10]
RULES = [("R", "range overlap (Harbor)", "-", "o", BLUE), ("S1", "SEM bars overlap", "--", "s", ORANGE),
         ("T", "pooled t-test, 5%", ":", "^", GREEN), ("W", "Welch t-test, 5%", "-.", "v", VERMILLION)]
fig, axes = plt.subplots(1, 3, figsize=(COL2, 1.66))
ax = axes[0]
for rule, lab, ls, mk, col in RULES:
    ax.plot(KS, [summ["false_alarm_by_k"][rule][str(k)] for k in KS], ls, marker=mk, color=col, label=lab)
ax.set_xlabel("runs per side $k$"); ax.set_ylabel("false-alarm rate"); ax.set_title("(a) false alarm by $k$")
ax.set_ylim(0, 0.52); ax.set_yticks([0, 0.1, 0.2, 0.3, 0.4]); ax.legend(frameon=False, loc="upper right")
ax = axes[1]
normal = rq1["normal_sd_units"]
for rule, lab, ls, mk, col in RULES:
    key = "R_exact" if rule == "R" else rule
    ax.plot(KS, [normal[f"k={k},gap=2"][key] for k in KS], ls, marker=mk, color=col, label=lab)
ax.set_xlabel("runs per side $k$"); ax.set_ylabel("P(detect a 2 SD gap)"); ax.set_title("(b) detection of a fixed gap by $k$"); ax.set_ylim(0, 1)
ax = axes[2]
nc = rq1["pass_prob_fixed_gap2_common_sd_k3"]
sds = [float(s) for s in nc]
ax.plot(sds, [nc[s]["R"] for s in nc], "-", marker="o", color=BLUE, label="overlap passes")
ax.plot(sds, [nc[s]["T_pass"] for s in nc], ":", marker="^", color=GREEN, label="t-test: no gap")
ax.plot(sds, [nc[s]["E3"] for s in nc], "--", marker="D", color=PURPLE, label="TOST: within $\\pm$3")
for q in runs["headline_sd_quartiles"]:
    ax.axvline(q, color=GREY, lw=0.6, ls="--")
ax.set_xscale("log"); ax.set_xlim(0.2, 40); ax.set_ylim(0, 1)  # x runs past the data to leave room for the legend
ax.set_xlabel("run-to-run SD, points (both sides)"); ax.set_ylabel("probability"); ax.set_title("(c) true gap 2 points, $k = 3$")
ax.legend(frameon=False, loc="center right", bbox_to_anchor=(1.0, 0.42), handlelength=1.6, borderaxespad=0.1)
fig.tight_layout(w_pad=1.0)
fig.savefig(os.path.join(figdir, "fig1_rules.pdf")); fig.savefig(os.path.join(figdir, "fig1_rules.png"), dpi=200); plt.close(fig)

# ---------- Figure 2: RQ2 ----------
head = [r for r in comps if r["k_original"] == "3" and r["k_harbor"] == "3"]
head.sort(key=lambda r: float(r["smallest_margin"]))
n = len(head)
margins = [float(r["smallest_margin"]) for r in head]
fails = [r["R_overlap"] in ("False", "0", "false") for r in head]
numbers["fig2_n"] = n
numbers["fig2_within_3"] = sum(m <= 3 for m in margins)
numbers["fig2_within_5"] = sum(m <= 5 for m in margins)
numbers["fig2_n_fail_overlap"] = sum(fails)
fig, ax = plt.subplots(figsize=(COL1, 1.92))
xs = list(range(1, n + 1))
ax.scatter([x for x, f in zip(xs, fails) if not f], [m for m, f in zip(margins, fails) if not f], s=9, color=BLUE, label="passes range overlap", zorder=3)
ax.scatter([x for x, f in zip(xs, fails) if f], [m for m, f in zip(margins, fails) if f], s=16, color=VERMILLION, marker="D", label="fails range overlap", zorder=4)
ax.axhline(3, color=GREY, lw=0.6, ls="--"); ax.axhline(5, color=GREY, lw=0.6, ls=":")
ax.text(1, 3 * 1.06, "3 points", va="bottom", fontsize=6.5, color=GREY); ax.text(1, 5 * 1.06, "5 points", va="bottom", fontsize=6.5, color=GREY)
ax.set_yscale("log"); ax.set_ylim(0.8, 60); ax.set_xlim(0, n + 3)
ax.set_yticks([1, 2, 3, 5, 10, 20, 50]); ax.set_yticklabels(["1", "2", "3", "5", "10", "20", "50"])
ax.set_xlabel(f"comparison, sorted ({n} with three runs per side)"); ax.set_ylabel("smallest provable\nmargin (points)")
LABELS = {"frontier-cs-algorithm": "Frontier-CS", "rexbench": "RexBench", "pixiu": "PIXIU", "gdb": "GDB", "usaco": "USACO"}
for x, r, m in zip(xs, head, margins):
    if r["adapter"] in LABELS:
        gap = float(r["gap"])
        ax.annotate(f"{LABELS[r['adapter']]} (gap {gap:+.1f})", (x, m), xytext={"frontier-cs-algorithm": (-5, 5), "rexbench": (-8, -2), "pixiu": (-4, -3)}.get(r["adapter"], (-4, 3 if r["adapter"] != "usaco" else 5)), textcoords="offset points", ha="right", fontsize=6)
ax.legend(frameon=False, loc="upper left")
fig.tight_layout()
fig.savefig(os.path.join(figdir, "fig2_margins.pdf")); fig.savefig(os.path.join(figdir, "fig2_margins.png"), dpi=200); plt.close(fig)

# ---------- Figure 3: RQ3 defects ----------
A = defects["aggregate"]["primary_binary_light"]
FS = defects["summary"]["fractions"]
nad = defects["summary"]["n_binary"]
fig, axes = plt.subplots(1, 3, figsize=(COL2, 1.64), sharey=True)
for ax, (kind, k, title) in zip(axes, (("break", 3, "(a) break defect, $k = 3$"), ("leak", 3, "(b) leak defect, $k = 3$"), ("break", 10, "(c) break defect, $k = 10$"))):
    for rule, lab, ls, mk, col in (("R", "range overlap", "-", "o", BLUE), ("T", "pooled t-test", ":", "^", GREEN), ("P", "paired t-test", "-.", "s", VERMILLION), ("CMH", "stratified test", "--", "D", PURPLE)):
        ys = [A[f"{kind},f={fr},k={k}"][rule]["mean"] for fr in FS]
        ax.plot(FS, ys, ls, marker=mk, color=col, label=lab)
        if rule in ("T", "CMH"):
            ax.fill_between(FS, [A[f"{kind},f={fr},k={k}"][rule]["q25"] for fr in FS], [A[f"{kind},f={fr},k={k}"][rule]["q75"] for fr in FS], color=col, alpha=0.08, lw=0)
    ax.set_xlabel(f"fraction of tasks {'broken' if kind == 'break' else 'leaked'} on the port side"); ax.set_title(title); ax.set_ylim(0, 1)
axes[0].set_ylabel("P(verdict = mismatch)"); h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, loc="upper center", ncol=4, frameon=False, handlelength=2.2, columnspacing=1.6, bbox_to_anchor=(0.5, 1.0))
fig.tight_layout(w_pad=0.8, rect=(0, 0, 1, 0.89))
fig.savefig(os.path.join(figdir, "fig3_defects.pdf")); fig.savefig(os.path.join(figdir, "fig3_defects.png"), dpi=200); plt.close(fig)
numbers["fig3_n_adapters"] = nad

# ---------- Table 1: RQ1 rules at k = 3 ----------
names = {"R": "range overlap (Harbor)", "S1": "SEM bars overlap", "S2": "gap within SE of difference", "S3": "gap within one SEM",
         "T": "pooled $t$-test, 5\\%", "W": "Welch $t$-test, 5\\%"}
rows = []
for rule in ("R", "S1", "S2", "S3", "T", "W"):
    fa = summ["k3_normal_false_alarm"][rule]; d1 = summ["k3_normal_detect_1sd"][rule]; d2 = summ["k3_normal_detect_2sd"][rule]
    tm = summ["k3_t_at_matched_false_alarm_detect_2sd"][rule]
    rows.append(f"{names[rule]} & {fa:.2f} & {d1:.2f} & {d2:.2f} & {tm:.2f} \\\\")
open(os.path.join(out, "tab1_rules.tex"), "w").write("\\begin{tabular}{lcccc}\n\\toprule\nrule & false alarm & 1 SD & 2 SD & $t$ at same FA \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
numbers["tab1"] = {rule: [round(summ["k3_normal_false_alarm"][rule], 3), round(summ["k3_normal_detect_1sd"][rule], 3), round(summ["k3_normal_detect_2sd"][rule], 3), round(summ["k3_t_at_matched_false_alarm_detect_2sd"][rule], 3)] for rule in names}

# ---------- Table 2: runs per side ----------
T = runs["table"]
q = runs["headline_sd_quartiles"]
rows = []
for m in (2, 3, 5):
    cells = []
    for sd in ("sd_p25", "sd_p50", "sd_p75"):
        c0 = T[f"{sd},gap=0.0,m={m}"]["k_power80"]; c6 = T[f"{sd},gap=0.6,m={m}"]["k_power80"]
        cells.append(f"{c0} ({c6})")
    rows.append(f"$\\pm{m}$ & " + " & ".join(cells) + " \\\\")
open(os.path.join(out, "tab2_runs.tex"), "w").write("\\begin{tabular}{lccc}\n\\toprule\nmargin & SD 1.1 & SD 1.7 & SD 2.7 \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
numbers["tab2_sd_quartiles"] = [round(x, 2) for x in q]
numbers["tab2"] = {f"m={m}": {sd: [T[f"{sd},gap=0.0,m={m}"]["k_power80"], T[f"{sd},gap=0.6,m={m}"]["k_power80"]] for sd in ("sd_p25", "sd_p50", "sd_p75")} for m in (2, 3, 5)}
json.dump(numbers, open(os.path.join(out, "paper_numbers.json"), "w"), indent=1)
print(json.dumps(numbers, indent=1))
