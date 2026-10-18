#!/usr/bin/env python3
"""Phase 4: draw the two README diagrams with matplotlib.

docs/parity-rule.svg   : what a parity experiment is, and the overlap rule applied to two real records
                         (USACO and RexBench). Run scores are read from the pinned parity files; the gap and the
                         smallest provable margin from results/phase2/rq2_comparisons.csv.
docs/study-overview.svg: the study in one picture. Every number is read from the data and results files.

Layout is done in inches (one data unit = one inch) so that text spacing does not depend on the figure size.
Usage: python -I scripts/p4_readme_diagrams.py <repo_root> <out_dir> [<png_preview_dir>]
"""
import csv
import json
import os
import re
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

root, out = sys.argv[1], sys.argv[2]
preview = sys.argv[3] if len(sys.argv) > 3 else None
os.makedirs(out, exist_ok=True)
P = lambda *p: os.path.join(root, *p)  # noqa: E731
J = lambda *p: json.load(open(P(*p)))  # noqa: E731

plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "path", "svg.hashsalt": "parity"})
INK, MUTED, GRID = "#1f2937", "#4b5563", "#9ca3af"
ORIG, ORIG_DARK, ORIG_FILL = "#2563eb", "#1e40af", "#eff6ff"
PORT, PORT_DARK, PORT_FILL = "#d97706", "#9a3412", "#fff7ed"
NEUTRAL_FILL, FAIL, PASS = "#f9fafb", "#b91c1c", "#15803d"
LINE = 1.4 / 72      # line height per point of font size, in inches
CHAR = 0.52 / 72     # average character width per point of font size, in inches


def canvas(w, h):
    """A figure whose single full-size axes uses inches as data units, origin at the bottom left."""
    fig = plt.figure(figsize=(w, h))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis("off")
    return fig, ax


def save(fig, name):
    fig.savefig(os.path.join(out, name), format="svg", metadata={"Date": None})
    if preview:
        os.makedirs(preview, exist_ok=True)
        fig.savefig(os.path.join(preview, name.replace(".svg", ".png")), dpi=150)
    plt.close(fig)


def wrap(text, width_in, fs):
    return textwrap.wrap(text, max(10, int(width_in / (CHAR * fs))))


def box(ax, x, top, w, fill, edge, title, paras, title_color=INK, fs=10, pad=0.14, gap=0.04):
    """Draw a rounded box at (x, top) of width w that grows to fit a bold title and wrapped paragraphs.
    Returns the y of its bottom edge."""
    inner = w - 2 * pad
    lines = [(title, True)] if title else []
    for p in paras:
        lines += [(ln, False) for ln in wrap(p, inner, fs - 1)]
    h = 2 * pad + sum(LINE * (fs if bold else fs - 1) for _, bold in lines) + (gap if title else 0)
    ax.add_patch(FancyBboxPatch((x, top - h), w, h, boxstyle="round,pad=0,rounding_size=0.08", fc=fill, ec=edge, lw=1.2))
    y = top - pad
    for i, (ln, bold) in enumerate(lines):
        size = fs if bold else fs - 1
        ax.text(x + pad, y, ln, fontsize=size, fontweight="bold" if bold else "normal", color=title_color if bold else INK, va="top")
        y -= LINE * size + (gap if bold and i == 0 else 0)
    return top - h


def arrow(ax, x0, y0, x1, y1):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.4, mutation_scale=12))


# ---------------------------------------------------------------- diagram 1: the rule on two real records
def runs(adapter):
    m = json.load(open(P("data", "raw", "harbor_parity", f"{adapter}.json")))[0]["metrics"][0]
    return m["metric"], [float(v) for v in m["original_runs"]], [float(v) for v in m["harbor_runs"]]


comps = {(r["adapter"], r["exp"]): r for r in csv.DictReader(open(P("results", "phase2", "rq2_comparisons.csv")))}
W, H = 10.4, 5.75
fig, ax = canvas(W, H)
ax.text(0.25, H - 0.22, "A parity experiment, and the rule that decides it", fontsize=15, fontweight="bold", color=INK, va="top")
left, lw = 0.25, 3.3
y = box(ax, left, H - 0.85, lw, ORIG_FILL, ORIG, "Original harness", ["same agent, same model, 3 runs"], ORIG_DARK, fs=11)
y = box(ax, left, y - 0.2, lw, PORT_FILL, PORT, "Harbor port", ["same agent, same model, 3 runs"], PORT_DARK, fs=11)
arrow(ax, left + lw / 2, y - 0.04, left + lw / 2, y - 0.34)
y = box(ax, left, y - 0.38, lw, NEUTRAL_FILL, GRID, "The matching criterion",
        ["Do the two ranges of run scores overlap?", "yes: the port passes", "no: treat as an adaptation error"], fs=11)
for i, ln in enumerate(wrap('Source: Harbor adapter guide, Step 5: "The two sides match if and only if their run-score ranges overlap."', lw, 9)):
    ax.text(left, y - 0.25 - i * LINE * 9, ln, fontsize=9, color=MUTED, va="top")

px, pw = 4.35, 5.75            # plot column, inches
for slot, adapter in enumerate(("usaco", "rexbench")):
    metric, a, b = runs(adapter)
    c = comps[(adapter, "0")]
    gap, margin = float(c["gap"]), float(c["smallest_margin"])
    overlap = max(a) >= min(b) and max(b) >= min(a)
    sep = max(min(b) - max(a), min(a) - max(b))
    lo, hi = min(a + b), max(a + b); span = hi - lo
    top = H - 0.85 - slot * 2.2
    name = {"usaco": "USACO", "rexbench": "RexBench"}[adapter]
    ax.text(px, top, f"{name}, {metric.lower()}", fontsize=11, fontweight="bold", color=INK, va="top")
    axp = fig.add_axes([px / W, (top - 1.35) / H, pw / W, 0.95 / H])
    axp.set_xlim(lo - 0.08 * span, hi + 0.08 * span); axp.set_ylim(-0.6, 1.9)
    for yy, vals, col, dark, side in ((1, a, ORIG, ORIG_DARK, "original"), (0, b, PORT, PORT_DARK, "port")):
        axp.plot([min(vals), max(vals)], [yy, yy], color=col, lw=7, alpha=0.3, solid_capstyle="round")
        axp.plot(vals, [yy] * len(vals), "o", color=col, ms=7, zorder=3)
        txt = f"{side}: {vals[0]!r} in all three runs" if len(set(vals)) == 1 else f"{side}: " + ", ".join(repr(v) for v in vals)
        axp.text(min(vals), yy + 0.42, txt, fontsize=9, color=dark, va="center")
    for s in ("left", "right", "top"):
        axp.spines[s].set_visible(False)
    axp.spines["bottom"].set_color(GRID); axp.tick_params(axis="x", colors=MUTED, labelsize=9); axp.set_yticks([])
    verdict = "PASS: the ranges overlap." if overlap else f"FAIL: the ranges miss by {sep:.1f} point."
    ax.text(px, top - 1.62, verdict, fontsize=10, fontweight="bold", color=PASS if overlap else FAIL, va="top")
    ax.text(px, top - 1.62 - LINE * 10, f"Gap between means {abs(gap):.1f} points; smallest provable margin {margin:.1f} points.",
            fontsize=9.5, color=INK, va="top")
for i, ln in enumerate(wrap("Same rule, opposite verdicts. The comparison it rejects is the one whose runs pin the gap down "
                            "more tightly.", pw, 9.5)):
    ax.text(px, 0.42 - i * LINE * 9.5, ln, fontsize=9.5, color=MUTED, va="top")
save(fig, "parity-rule.svg")

# ---------------------------------------------------------------- diagram 2: the study in one picture
inv, raw = J("results", "phase0", "inventory.json"), J("data", "raw", "MANIFEST.json")
sel, rq1 = J("results", "phase2", "selection_log.json"), J("results", "phase2", "rq1_rules.json")
h = J("results", "phase2", "rq2_summary.json")["summaries"]["headline_k3"]
need = J("results", "phase2", "rq3_runs_needed.json")["table"]
paired = J("results", "phase2", "rq3_paired.json")["summary"]["primary"]
defects = J("results", "phase2", "rq3_defects.json")["aggregate"]["primary_binary_light"]
pertask = J("data", "pertask", "MANIFEST.json")["adapters"]
n_both = sum(1 for v in pertask.values() if v.get("status") == "both_sides")
n_amend = len(re.findall(r"^-? ?Amendment \d", open(P("memos", "phase-2-preregistration.md")).read(), flags=re.M))
fa3, det = rq1["closed_form_false_alarm"]["3"], rq1["summary"]["R_detect_2sd_by_k"]
cmh = defects["break,f=0.1,k=3"]["CMH"]["mean"]
pct = lambda x: f"{100 * x:.0f}%"  # noqa: E731
words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}

W, H = 10.4, 9.0  # trimmed to the content below
fig, ax = canvas(W, H)
ax.text(0.25, H - 0.22, "What this study did", fontsize=15, fontweight="bold", color=INK, va="top")
top, cw = H - 0.8, 2.45
b1 = box(ax, 0.25, top, cw, NEUTRAL_FILL, GRID, "Public data only",
         [f"{inv['n_files']} parity files from Harbor (commit {raw['commit'][:7]}, {raw['commit_date'][:10]})",
          f"{inv['n_experiments']} experiments; per-task results for {n_both} adapters", "No benchmark rerun."])
b2 = box(ax, 0.25 + cw + 0.4, top, cw, NEUTRAL_FILL, GRID, "Plan fixed in advance",
         ["One comparison per experiment; metric and exclusions written down first, with "
          f"{words.get(n_amend, n_amend)} dated amendments.", f"{h['n']} of {sel['n_comparisons']} comparisons have three runs per side."])
mid = top - 0.5
arrow(ax, 0.25 + cw + 0.04, mid, 0.25 + cw + 0.36, mid)
rx = 0.25 + 2 * cw + 0.8
arrow(ax, rx - 0.36, mid, rx - 0.04, mid)
rq = [("RQ1  What does the overlap rule guarantee?",
       f"False alarm 2(k!)²/(2k)!, {pct(fa3)} at three runs, chosen by no one. Detection of a 2 SD gap falls from "
       f"{pct(det['2'])} to {pct(det['10'])} between 2 and 10 runs. Noisier ports pass more easily."),
      ("RQ2  What do the published runs establish?",
       f"Ports look close (median gap {h['median_abs_gap']:.1f} points), but equivalence within 3 points is shown for "
       f"{h['within_margin_tost']['3']} of {h['n']} and within 5 for {h['within_margin_tost']['5']}. "
       f"The rule passes gaps up to {abs(h['largest_gaps'][0][2]):.1f} points."),
      ("RQ3  What would a better check cost?",
       f"About {need['sd_p50,gap=0.0,m=3']['k_power80']} runs per side for a 3-point margin. Per-task outcomes show "
       f"task-level disagreement in {paired['n_sd_task_diff_exceeds_noise_p05']} of {paired['n']} adapters. "
       f"A stratified test catches a 10% defect {pct(cmh)} of the time at three runs.")]
y = top
for title, body in rq:
    y = box(ax, rx, y, W - 0.25 - rx, ORIG_FILL, ORIG, title, [body], ORIG_DARK) - 0.12
arrow(ax, rx + (W - 0.25 - rx) / 2, y + 0.06, rx + (W - 0.25 - rx) / 2, y - 0.16)
bottom = box(ax, 0.25, y - 0.2, W - 0.5, PORT_FILL, PORT, "The five-line protocol",
    ["  ".join(f"{i}.\u00a0{s}" for i, s in enumerate((  # no-break space keeps each number with its item
        "State the margin first.", "Choose the run count from the noise.",
        "Report the gap, its 90% interval and the smallest provable margin.",
        "Publish per-task outcomes and run a stratified test.", "Keep range overlap as a sanity check at most."), 1))], PORT_DARK)
bottom -= 0.25
ax.set_ylim(bottom, H); fig.set_size_inches(W, H - bottom)  # keep one data unit equal to one inch
save(fig, "study-overview.svg")
print("wrote", os.path.join(out, "parity-rule.svg"), "and", os.path.join(out, "study-overview.svg"))
