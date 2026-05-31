import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import LineCollection
from src.candidates import build_candidates
from src.visibility import compute_visibility
from main import load_polygon
import argparse


def plot(poly, candidates, V, title="AGP Visualization"):
    fig, ax = plt.subplots(figsize=(7, 7))

    mpl_poly = MplPolygon(poly, closed=True, facecolor="#E5E9EE", edgecolor="#1D345B", linewidth=2)
    ax.add_patch(mpl_poly)

    n = len(candidates)
    lines = []
    for i in range(n):
        for j in range(i + 1, n):
            if V[i][j]:
                lines.append([candidates[i], candidates[j]])
    lc = LineCollection(lines, colors="#66B1F8", linewidths=0.4, alpha=0.3, zorder=2)
    ax.add_collection(lc)

    vx = [p[0] for p in poly]
    vy = [p[1] for p in poly]
    ax.scatter(vx, vy, color="#1D345B", s=40, zorder=4)

    n_verts = len(poly)
    if len(candidates) > n_verts:
        cx = [p[0] for p in candidates[n_verts:]]
        cy = [p[1] for p in candidates[n_verts:]]
        ax.scatter(cx, cy, color="#9A1F89", s=40, zorder=4, marker="^")

    for i, p in enumerate(candidates):
        ax.annotate(f"p{i + 1}", xy=p, xytext=(4, 4), textcoords="offset points", fontsize=7)

    ax.autoscale()
    ax.set_aspect("equal")
    ax.set_title(title)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGP Visualizer")
    parser.add_argument("polygon", help="CSV file with polygon vertices")
    parser.add_argument("--rounds", type=int, default=3, help="max rounds for candidates")
    args = parser.parse_args()

    poly = load_polygon(args.polygon)
    pts = build_candidates(poly, poly, max_rounds=args.rounds)
    V = compute_visibility(pts, poly)
    plot(poly, pts, V, title=args.polygon)
