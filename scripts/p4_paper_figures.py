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
# Draw at IEEE column widths so label sizes carry through to the paper.
# Use Arial when installed and keep a portable sans-serif fallback for reproduction.
# Distinct markers and line styles keep series identifiable in greyscale.
COL1, COL2 = 3.5, 7.16
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
    "font.size": 9.5,
    "axes.titlesize": 9.5,
    "figure.labelsize": 9.5,
    "lines.linewidth": 1.2,
    "lines.markersize": 3.6,
    "pdf.fonttype": 42,
    "axes.spines.top": False,
    "axes.spines.right": False,
})
BLUE, ORANGE, GREEN, VERMILLION, PURPLE, GREY = "#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#7f7f7f"


def save_figure(fig, name):
    fig.savefig(os.path.join(figdir, f"{name}.pdf"))
    fig.savefig(os.path.join(figdir, f"{name}.png"), dpi=350)
    plt.close(fig)


rq1 = json.load(open(os.path.join(p2, "rq1_rules.json")))
runs = json.load(open(os.path.join(p2, "rq3_runs_needed.json")))
defects = json.load(open(os.path.join(p2, "rq3_defects.json")))
comps = list(csv.DictReader(open(os.path.join(p2, "rq2_comparisons.csv"))))
summ = rq1["summary"]
numbers = {}

# ---------- Figure 1: RQ1 ----------
KS = [2, 3, 4, 5, 6, 8, 10]
RULES = [("R", "Range overlap", "-", "o", BLUE), ("S1", "SEM bars overlap", "--", "s", ORANGE),
         ("T", "Pooled t-test", ":", "^", GREEN), ("W", "Welch t-test", "-.", "v", VERMILLION)]
fig, axes = plt.subplots(1, 3, figsize=(COL2, 2.15), layout="constrained")
ax = axes[0]
for rule, lab, ls, mk, col in RULES:
    ax.plot(KS, [summ["false_alarm_by_k"][rule][str(k)] for k in KS], ls, marker=mk, color=col, label=lab)
ax.set_xlabel("Runs per side (k)")
ax.set_ylabel("False-alarm rate")
ax.set_title("(a) False alarms")
ax.set_xticks([2, 4, 6, 8, 10])
ax.set_ylim(-0.01, 0.52)
ax.set_yticks([0, 0.1, 0.2, 0.3, 0.4, 0.5])
ax = axes[1]
normal = rq1["normal_sd_units"]
for rule, lab, ls, mk, col in RULES:
    key = "R_exact" if rule == "R" else rule
    ax.plot(KS, [normal[f"k={k},gap=2"][key] for k in KS], ls, marker=mk, color=col, label=lab)
ax.set_xlabel("Runs per side (k)")
ax.set_ylabel("Detection probability")
ax.set_title("(b) Detection")
ax.set_xticks([2, 4, 6, 8, 10])
ax.set_ylim(-0.025, 1.025)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1], labels=["0", "0.25", "0.5", "0.75", "1"])
ax = axes[2]
nc = rq1["pass_prob_fixed_gap2_common_sd_k3"]
sds = [float(s) for s in nc]
ax.plot(sds, [nc[s]["R"] for s in nc], "-", marker="o", color=BLUE)
ax.plot(sds, [nc[s]["T_pass"] for s in nc], ":", marker="^", color=GREEN)
tost, = ax.plot(sds, [nc[s]["E3"] for s in nc], "--", marker="D", color=PURPLE, label="TOST")
for q in runs["headline_sd_quartiles"]:
    ax.axvline(q, color=GREY, lw=0.6, ls="--")
ax.set_xscale("log")
ax.set_xlim(0.2, 40)
ax.set_xticks([0.25, 1, 5, 20], labels=["0.25", "1", "5", "20"])
ax.set_ylim(-0.025, 1.025)
ax.set_yticks([0, 0.25, 0.5, 0.75, 1], labels=["0", "0.25", "0.5", "0.75", "1"])
ax.set_xlabel("Run-to-run SD (points)")
ax.set_ylabel("Probability")
ax.set_title("(c) Noise sensitivity")
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles + [tost], labels + [tost.get_label()], loc="outside upper center", ncols=5, frameon=False)
save_figure(fig, "fig1_rules")

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
fig, ax = plt.subplots(figsize=(COL1, 2.05), layout="constrained")
xs = list(range(1, n + 1))
ax.scatter([x for x, f in zip(xs, fails) if not f], [m for m, f in zip(margins, fails) if not f],
           s=12, color=BLUE, label="Overlap", zorder=3)
ax.scatter([x for x, f in zip(xs, fails) if f], [m for m, f in zip(margins, fails) if f],
           s=22, color=VERMILLION, marker="D", label="No overlap", zorder=4)
ax.axhline(3, color=GREY, lw=0.8, ls="--")
ax.axhline(5, color=GREY, lw=0.8, ls=":")
ax.set_yscale("log")
ax.set_ylim(0.8, 70)
ax.set_xlim(0, n + 3)
ax.set_yticks([1, 2, 3, 5, 10, 20, 50], labels=["1", "2", "3", "5", "10", "20", "50"])
ax.set_xlabel("Comparison rank")
ax.set_ylabel("Smallest margin (points)")
gap_labels = {"frontier-cs-algorithm": "Frontier-CS", "rexbench": "RexBench",
              "pixiu": "PIXIU", "gdb": "GDB"}
largest_gaps = sorted(enumerate(head, 1), key=lambda item: abs(float(item[1]["gap"])), reverse=True)[:4]
for (rank, row), offset in zip(largest_gaps, (4, -4, -3, -3)):
    label = gap_labels.get(row["adapter"], row["adapter"])
    ax.annotate(label, (rank, margins[rank - 1]), xytext=(-9, offset), textcoords="offset points",
                ha="right", va="center", arrowprops={"arrowstyle": "-", "color": GREY, "lw": 0.7})
fig.legend(loc="outside upper center", ncols=2, frameon=False)
save_figure(fig, "fig2_margins")

# ---------- Figure 3: RQ3 defects ----------
A = defects["aggregate"]["primary_binary_light"]
FS = defects["summary"]["fractions"]
nad = defects["summary"]["n_binary"]
fig, axes = plt.subplots(1, 3, figsize=(COL2, 1.92), sharey=True, layout="constrained")
panels = [("break", 3, "(a) Break, k = 3"), ("leak", 3, "(b) Leak, k = 3"), ("break", 10, "(c) Break, k = 10")]
methods = [("R", "Range overlap", "-", "o", BLUE), ("T", "Pooled t-test", ":", "^", GREEN),
           ("P", "Paired t-test", "-.", "s", VERMILLION), ("CMH", "Stratified test", "--", "D", PURPLE)]
for ax, (kind, k, title) in zip(axes, panels):
    for rule, lab, ls, mk, col in methods:
        ys = [A[f"{kind},f={fr},k={k}"][rule]["mean"] for fr in FS]
        ax.plot(FS, ys, ls, marker=mk, color=col, label=lab,
                markerfacecolor="none" if rule == "CMH" else col,
                markersize=5 if rule == "CMH" else 3.6)
        if rule in ("T", "CMH"):
            ax.fill_between(FS, [A[f"{kind},f={fr},k={k}"][rule]["q25"] for fr in FS], [A[f"{kind},f={fr},k={k}"][rule]["q75"] for fr in FS], color=col, alpha=0.17, lw=0)
    ax.set_xticks([0, 0.05, 0.10, 0.15, 0.20], labels=["0", "5", "10", "15", "20"])
    ax.set_title(title)
    ax.set_ylim(-0.025, 1.025)
axes[0].set_yticks([0, 0.5, 1], labels=["0", "0.5", "1"])
axes[0].set_ylabel("Mismatch probability")
fig.supxlabel("Affected tasks on port side (%)")
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="outside upper center", ncols=4, frameon=False)
save_figure(fig, "fig3_defects")
numbers["fig3_n_adapters"] = nad

# ---------- Table 1: RQ1 rules at k = 3 ----------
names = {"R": "range overlap (Harbor)", "S1": "(S1) SEM bars overlap", "S2": "(S2) gap within difference SE", "S3": "(S3) gap within one SEM",
         "T": "pooled $t$-test, 5\\%", "W": "Welch $t$-test, 5\\%"}
rows = []
for rule in ("R", "S1", "S2", "S3", "T", "W"):
    fa = summ["k3_normal_false_alarm"][rule]; d1 = summ["k3_normal_detect_1sd"][rule]; d2 = summ["k3_normal_detect_2sd"][rule]
    tm = summ["k3_t_at_matched_false_alarm_detect_2sd"][rule]
    rows.append(f"{names[rule]} & {fa:.2f} & {d1:.2f} & {d2:.2f} & {tm:.2f} \\\\")
open(os.path.join(out, "tab1_rules.tex"), "w").write("\\begin{tabular}{lcccc}\n\\toprule\nrule & \\shortstack{false\\\\alarm} & 1 SD & 2 SD & \\shortstack{$t$ at\\\\same FA} \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
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
