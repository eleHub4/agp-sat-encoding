import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import LineCollection
from pathlib import Path
from src.candidates import build_candidates
from src.visibility import compute_visibility
from main import load_polygon
import argparse


def plot(poly, candidates, V, guards=None, title="AGP Visualization"):
    fig, axes = plt.subplots(1, 2, figsize=(14, 8))
    _plot_visibility(axes[0], poly, candidates, V)
    _plot_solution(axes[1], poly, candidates, V, guards)
    fig.suptitle(title)
    plt.tight_layout()
    plt.show()
    return fig


def _plot_visibility(ax, poly, candidates, V):
    _draw_polygon(ax, poly)
    _draw_candidates(ax, poly, candidates)
    n = len(candidates)
    lines = [
        [candidates[i], candidates[j]]
        for i in range(n)
        for j in range(i + 1, n)
        if V[i][j]
    ]
    lc = LineCollection(lines, colors="#66B1F8", linewidths=0.5, alpha=0.3, zorder=2)
    ax.add_collection(lc)
    ax.set_title("visibility graph")


def _plot_solution(ax, poly, candidates, V, guards=None):
    _draw_polygon(ax, poly)
    _draw_candidates(ax, poly, candidates)
    if guards:
        guard_indices = [g - 1 for g in guards]
        lines = [
            [candidates[i], candidates[j]]
            for i in guard_indices
            for j in range(len(candidates))
            if V[i][j] and i != j
        ]
        lc = LineCollection(lines, colors="#FF8080", linewidths=0.8, alpha=0.3, zorder=2)
        ax.add_collection(lc)
        gx = [candidates[g][0] for g in guard_indices]
        gy = [candidates[g][1] for g in guard_indices]
        ax.scatter(gx, gy, color="#EE4D44", s=80, zorder=5, marker="*")
    label = f"solution — {len(guards)} guard(s)" if guards else "solution (no guards yet)"
    ax.set_title(label)


def _draw_polygon(ax, poly):
    mpl_poly = MplPolygon(poly, closed=True, facecolor="#E5E9EE", edgecolor="#1D345B", linewidth=2)
    ax.add_patch(mpl_poly)
    vx, vy = zip(*poly)
    ax.scatter(vx, vy, color="#1D345B", s=40, zorder=4)
    ax.autoscale()
    ax.set_aspect("equal")
    ax.tick_params(axis='x', pad=5)


def _draw_candidates(ax, poly, candidates):
    n_verts = len(poly)
    if len(candidates) > n_verts:
        cx = [p[0] for p in candidates[n_verts:]]
        cy = [p[1] for p in candidates[n_verts:]]
        ax.scatter(cx, cy, color="#9A1F89", s=40, zorder=4, marker="^")

    for i, p in enumerate(candidates):
        ax.annotate(f"p{i + 1}", xy=p, xytext=(4, 4), textcoords="offset points", fontsize=7)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGP Visualizer")
    parser.add_argument("polygon", help="CSV file with polygon vertices")
    parser.add_argument("--rounds", type=int, default=2, help="max rounds for candidates")
    parser.add_argument("--guards", type=int, nargs="*", default=None)
    parser.add_argument("--out", default=None, help="output image file")
    args = parser.parse_args()

    poly = load_polygon(args.polygon)
    pts = build_candidates(poly, poly, max_rounds=args.rounds)
    V = compute_visibility(pts, poly)

    fig = plot(poly, pts, V, guards=args.guards, title=args.polygon)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.out, dpi=300, bbox_inches="tight")
        print(f"saved {args.out}")

    plt.show()
