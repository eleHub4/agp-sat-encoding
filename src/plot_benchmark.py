"""
Usage:
    python3 -m src.plot_benchmark \
        --pre preprocessing_rounds.csv \
        --res results_rounds.csv \
        --out plots/
"""

import csv
import argparse
from pathlib import Path
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ── colours ───────────────────────────────────────────────────────────
C_MAXHS  = "#1A7A1A"
C_KISSAT = "#2E5090"
C_PRE    = "#854F0B"
SIZE_PALETTE = ["#1B4F72", "#117A65", "#B9770E", "#943126", "#5B2C6F", "#1A5276"]


# ── helpers ───────────────────────────────────────────────────────────

def load_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f))

def flt(s, fallback=None):
    try:
        return float(s)
    except (ValueError, TypeError):
        return fallback

def parse_per_k(s):
    out = []
    for part in s.split(";"):
        k, status, t = part.split(":")
        out.append((int(k[1:]), status, float(t)))
    return out

def size_color(idx):
    return SIZE_PALETTE[idx % len(SIZE_PALETTE)]


# ── comb: one line per size, x = rounds ────────────────────────────────

def plot_comb(pre_rows, res_rows, out_dir):
    pre_by_tag = {r["instance"]: r for r in pre_rows}
    comb_pre = [r for r in pre_rows if r["family"] == "comb"]
    comb_res = [r for r in res_rows if r["family"] == "comb"]

    sizes = sorted(set(int(r["size"]) for r in comb_pre))

    fig, (ax_pre, ax_solve) = plt.subplots(1, 2, figsize=(12, 5))

    # --- preprocessing subplot ---
    for i, size in enumerate(sizes):
        color = size_color(i)
        rows = sorted([r for r in comb_pre if int(r["size"]) == size],
                      key=lambda r: int(r["rounds"]))
        xs = [int(r["rounds"]) for r in rows]
        ys = [flt(r["total_preprocess_time"]) for r in rows]
        ns = [flt(r["n_candidates"]) for r in rows]

        ax_pre.plot(xs, ys, color=color, marker="o", markersize=6,
                    linewidth=1.6, label=f"size={size}", zorder=3)
        x_off = (i - (len(sizes) - 1) / 2) * 16
        for x, y, n in zip(xs, ys, ns):
            ax_pre.annotate(f"(n={int(n)})", xy=(x, y),
                            xytext=(x_off, 9), textcoords="offset points",
                            fontsize=6.5, color=color, ha="center")

    ax_pre.set_yscale("log")
    ax_pre.set_xticks([0, 1, 2])
    ax_pre.set_xlabel("rounds")
    ax_pre.set_ylabel("Vorverarbeitungszeit (s, log)")
    ax_pre.set_title("Preprocessing")
    ax_pre.grid(True, which="both", alpha=0.2)
    ax_pre.legend(fontsize=8)

    # --- solver subplot (MaxHS + Kissat) ---
    for i, size in enumerate(sizes):
        color = size_color(i)
        rows = sorted([r for r in comb_res if int(r["size"]) == size],
                      key=lambda r: int(r["rounds"]))
        xs = [int(r["rounds"]) for r in rows]
        y_maxhs = [flt(r["maxhs_time"]) for r in rows]
        y_kissat = [flt(r["kissat_total_time"]) for r in rows]
        timeout = [r["kissat_optimal_k"].strip() == "" for r in rows]
        ns = [flt(pre_by_tag[r["instance"]]["n_candidates"]) for r in rows]

        ax_solve.plot(xs, y_maxhs, color=color, marker="^", markersize=7,
                      linewidth=1.6, linestyle="-", zorder=3)
        # kissat: draw line through non-timeout points, mark timeouts separately
        kx, ky = [], []
        for x, y, to in zip(xs, y_kissat, timeout):
            if y is not None and not to:
                kx.append(x); ky.append(y)
        ax_solve.plot(kx, ky, color=color, marker="o", markersize=6,
                      linewidth=1.2, linestyle="--", zorder=3)
        for x, y, to in zip(xs, y_kissat, timeout):
            if to and y is not None:
                ax_solve.scatter([x], [y], color=color, marker="X", s=90,
                                 edgecolors="black", linewidths=0.8, zorder=4)

        x_off = (i - (len(sizes) - 1) / 2) * 16
        for x, n in zip(xs, ns):
            ax_solve.annotate(f"(n={int(n)})", xy=(x, max(filter(None, [
                                  y_maxhs[xs.index(x)], y_kissat[xs.index(x)]]))),
                              xytext=(x_off, 9), textcoords="offset points",
                              fontsize=6.5, color=color, ha="center")

    ax_solve.set_yscale("log")
    ax_solve.set_xticks([0, 1, 2])
    ax_solve.set_xlabel("rounds")
    ax_solve.set_ylabel("Solver-Zeit (s, log)")
    ax_solve.set_title("Solver (durchgezogen=MaxHS, gestrichelt=Kissat)")
    ax_solve.grid(True, which="both", alpha=0.2)

    legend_handles = [Line2D([0], [0], color=size_color(i), marker="o",
                              linestyle="-", label=f"size={s}")
                       for i, s in enumerate(sizes)] + [
        Line2D([0], [0], color="gray", marker="^", linestyle="-", label="MaxHS"),
        Line2D([0], [0], color="gray", marker="o", linestyle="--", label="Kissat"),
        Line2D([0], [0], color="gray", marker="X", linestyle="",
               markeredgecolor="black", label="Kissat Timeout"),
    ]
    ax_solve.legend(handles=legend_handles, fontsize=7.5, loc="upper left")

    fig.suptitle("comb: Zeit vs. rounds (eine Linie pro size, Kandidatenzahl in Klammern)")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    path = Path(out_dir) / "comb_vs_rounds.pdf"
    fig.savefig(path)
    print(f"saved {path}")
    return fig


# ── random: one line per size, x = rounds, aggregated over seeds ──────

def plot_random(pre_rows, res_rows, out_dir):
    pre_by_tag = {r["instance"]: r for r in pre_rows}
    rnd_pre = [r for r in pre_rows if r["family"] == "random"]
    rnd_res = [r for r in res_rows if r["family"] == "random"]

    sizes = sorted(set(int(r["size"]) for r in rnd_pre))

    fig, (ax_pre, ax_solve) = plt.subplots(1, 2, figsize=(12, 5))

    # --- preprocessing: aggregate by (size, rounds) ---
    for i, size in enumerate(sizes):
        color = size_color(i)
        groups = defaultdict(list)  # rounds -> [(t, n)]
        for r in rnd_pre:
            if int(r["size"]) != size:
                continue
            t = flt(r["total_preprocess_time"])
            n = flt(r["n_candidates"])
            if t is None or n is None:
                continue
            groups[int(r["rounds"])].append((t, n))

        xs_sorted = sorted(groups.keys())
        means, mins, maxs, n_means = [], [], [], []
        for rnd in xs_sorted:
            ts = [v[0] for v in groups[rnd]]
            ns = [v[1] for v in groups[rnd]]
            means.append(sum(ts) / len(ts))
            mins.append(min(ts))
            maxs.append(max(ts))
            n_means.append(sum(ns) / len(ns))

        ax_pre.plot(xs_sorted, means, color=color, marker="o", markersize=6,
                    linewidth=1.6, label=f"size={size}", zorder=3)
        for x, lo, hi in zip(xs_sorted, mins, maxs):
            ax_pre.plot([x, x], [lo, hi], color=color, alpha=0.35, linewidth=4, zorder=2)
        x_off = (i - (len(sizes) - 1) / 2) * 16
        for x, y, n in zip(xs_sorted, means, n_means):
            ax_pre.annotate(f"(n={int(n)})", xy=(x, y),
                            xytext=(x_off, 9), textcoords="offset points",
                            fontsize=6.5, color=color, ha="center")

    ax_pre.set_yscale("log")
    ax_pre.set_xticks([0, 1, 2])
    ax_pre.set_xlabel("rounds")
    ax_pre.set_ylabel("Vorverarbeitungszeit (s, log)")
    ax_pre.set_title("Preprocessing (Mittelwert ± Spannweite über Seeds)")
    ax_pre.grid(True, which="both", alpha=0.2)
    ax_pre.legend(fontsize=8)

    # --- solver: aggregate by (size, rounds), maxhs + kissat ---
    for i, size in enumerate(sizes):
        color = size_color(i)

        maxhs_groups = defaultdict(list)   # rounds -> [(t, n)]
        kissat_groups = defaultdict(list)  # rounds -> [(t, n)]
        kissat_timeout_rounds = set()

        for r in rnd_res:
            if int(r["size"]) != size:
                continue
            rnd = int(r["rounds"])
            pre = pre_by_tag.get(r["instance"])
            n = flt(pre["n_candidates"]) if pre else None

            t_maxhs = flt(r["maxhs_time"])
            if t_maxhs is not None and n is not None:
                maxhs_groups[rnd].append((t_maxhs, n))

            t_kissat = flt(r["kissat_total_time"])
            timeout = r["kissat_optimal_k"].strip() == ""
            if timeout:
                kissat_timeout_rounds.add(rnd)
            elif t_kissat is not None and n is not None:
                kissat_groups[rnd].append((t_kissat, n))

        def agg(groups):
            xs_sorted = sorted(groups.keys())
            means = [sum(v[0] for v in groups[r]) / len(groups[r]) for r in xs_sorted]
            mins = [min(v[0] for v in groups[r]) for r in xs_sorted]
            maxs = [max(v[0] for v in groups[r]) for r in xs_sorted]
            n_means = [sum(v[1] for v in groups[r]) / len(groups[r]) for r in xs_sorted]
            return xs_sorted, means, mins, maxs, n_means

        mx, mmean, mmin, mmax, mn = agg(maxhs_groups)
        ax_solve.plot(mx, mmean, color=color, marker="^", markersize=7,
                      linewidth=1.6, linestyle="-", zorder=3)
        for x, lo, hi in zip(mx, mmin, mmax):
            ax_solve.plot([x, x], [lo, hi], color=color, alpha=0.3, linewidth=4, zorder=2)
        x_off = (i - (len(sizes) - 1) / 2) * 16
        for x, y, n in zip(mx, mmean, mn):
            ax_solve.annotate(f"(n={int(n)})", xy=(x, y),
                              xytext=(x_off, 10), textcoords="offset points",
                              fontsize=6.5, color=color, ha="center")

        kx, kmean, kmin, kmax, kn = agg(kissat_groups)
        ax_solve.plot(kx, kmean, color=color, marker="o", markersize=6,
                      linewidth=1.2, linestyle="--", zorder=3)
        for x, lo, hi in zip(kx, kmin, kmax):
            ax_solve.plot([x, x], [lo, hi], color=color, alpha=0.3, linewidth=3, zorder=2)

        # mark rounds where kissat had a timeout (any seed), at top of axis range
        for rnd in kissat_timeout_rounds:
            # place marker slightly above the maxhs mean for that round, if available
            y_ref = mmean[mx.index(rnd)] if rnd in mx else (max(kmean) if kmean else 1)
            ax_solve.scatter([rnd], [y_ref * 1.3], color=color, marker="X", s=90,
                             edgecolors="black", linewidths=0.8, zorder=4)

    ax_solve.set_yscale("log")
    ax_solve.set_xticks([0, 1, 2])
    ax_solve.set_xlabel("rounds")
    ax_solve.set_ylabel("Solver-Zeit (s, log)")
    ax_solve.set_title("Solver (durchgezogen=MaxHS, gestrichelt=Kissat)")
    ax_solve.grid(True, which="both", alpha=0.2)

    legend_handles = [Line2D([0], [0], color=size_color(i), marker="o",
                              linestyle="-", label=f"size={s}")
                       for i, s in enumerate(sizes)] + [
        Line2D([0], [0], color="gray", marker="^", linestyle="-", label="MaxHS"),
        Line2D([0], [0], color="gray", marker="o", linestyle="--", label="Kissat"),
        Line2D([0], [0], color="gray", marker="X", linestyle="",
               markeredgecolor="black", label="Kissat Timeout (≥1 Seed)"),
    ]
    ax_solve.legend(handles=legend_handles, fontsize=7.5, loc="upper left")

    fig.suptitle("random: Zeit vs. rounds (eine Linie pro size, Kandidatenzahl in Klammern)")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    path = Path(out_dir) / "random_vs_rounds.pdf"
    fig.savefig(path)
    print(f"saved {path}")
    return fig


# ── Plot 3: Per-k time for comb (UNSAT explosion) — unchanged ─────────

def plot_comb_per_k(res_rows, rounds_filter=2, out_dir="."):
    rows = [r for r in res_rows
            if r["family"] == "comb"
            and int(r["rounds"]) == rounds_filter
            and r.get("kissat_per_k", "").strip()]
    rows.sort(key=lambda r: int(r["size"]))

    if not rows:
        print(f"No comb rows with rounds={rounds_filter}")
        return None

    palette = ["#2E5090", "#1A7A1A", "#854F0B", "#9A1F89"]
    fig, ax = plt.subplots(figsize=(7, 4.5))

    for idx, r in enumerate(rows):
        per_k = parse_per_k(r["kissat_per_k"])
        color = palette[idx % len(palette)]
        ks = [k for k, _, _ in per_k]
        ts = [t for _, _, t in per_k]

        ax.plot(ks, ts, color=color, alpha=0.4, zorder=1)
        for k, status, t in per_k:
            if status == "SATISFIABLE":
                ax.scatter(k, t, color=color, marker="o", s=60,
                           facecolors="white", linewidths=1.5, zorder=3)
            elif status == "UNSATISFIABLE":
                ax.scatter(k, t, color=color, marker="o", s=45, zorder=3)
            else:
                ax.scatter(k, t, color=color, marker="X", s=70, zorder=3)

        ax.annotate(r["instance"], xy=(ks[-1], ts[-1]),
                    xytext=(4, 0), textcoords="offset points",
                    fontsize=7, color=color, va="center")

    ax.set_yscale("log")
    ax.set_xlabel("k")
    ax.set_ylabel("Zeit pro Solver-Aufruf (s, log)")
    ax.set_title(f"Kissat: Zeit pro k (comb, rounds={rounds_filter})")

    legend_handles = [
        Line2D([0], [0], color=palette[i % len(palette)], marker="o",
               linestyle="-", label=rows[i]["instance"])
        for i in range(len(rows))
    ] + [
        Line2D([0], [0], color="gray", marker="o", markerfacecolor="white",
               linestyle="", label="SAT (Optimum)"),
        Line2D([0], [0], color="gray", marker="o", linestyle="", label="UNSAT"),
        Line2D([0], [0], color="gray", marker="X", linestyle="", label="Timeout"),
    ]
    ax.legend(handles=legend_handles, fontsize=8, loc="upper left")
    ax.grid(True, which="both", alpha=0.2)
    fig.tight_layout()
    path = Path(out_dir) / f"comb_per_k_r{rounds_filter}.pdf"
    fig.savefig(path)
    print(f"saved {path}")
    return fig


# ── main ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pre", default="preprocessing_rounds.csv")
    parser.add_argument("--res", default="results_rounds.csv")
    parser.add_argument("--out", default="plots")
    parser.add_argument("--rounds", type=int, default=2,
                        help="rounds filter for per-k plot (default: 2)")
    args = parser.parse_args()

    Path(args.out).mkdir(exist_ok=True)
    pre_rows = load_csv(args.pre)
    res_rows = load_csv(args.res)

    plot_comb(pre_rows, res_rows, args.out)
    plot_random(pre_rows, res_rows, args.out)
    plot_comb_per_k(res_rows, rounds_filter=args.rounds, out_dir=args.out)

    plt.show()