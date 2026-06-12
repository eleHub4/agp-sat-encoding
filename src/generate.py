import argparse
import csv
import math
import os
import random


def comb_polygon(n_teeth):
    pts = []
    pts.append((0, 0))
    pts.append((2 * n_teeth - 1, 0))
    pts.append((2 * n_teeth - 1, 3))
    # only n_teeth - 1 notches
    for i in range(n_teeth - 2, -1, -1):
        x = i * 2 + 1
        pts.append((x + 1, 3))
        pts.append((x + 1, 1))
        pts.append((x, 1))
        pts.append((x, 3))

    pts.append((0, 3))
    return pts

def random_polygon(n, width=10, height=10, seed=None):
    if seed is not None:
        random.seed(seed)
    pts = [(random.uniform(0, width), random.uniform(0, height)) for _ in range(n)]
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    pts.sort(key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
    return [(round(p[0], 4), round(p[1], 4)) for p in pts]
    


def save_polygon(poly, filepath):
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        for p in poly:
            writer.writerow(p)
    print(f"Saved: {filepath}  ({len(poly)} vertices)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGP Polygon Generator")
    subparsers = parser.add_subparsers(dest="command")

    comb_parser = subparsers.add_parser("comb", help="generate comb polygon")
    comb_parser.add_argument("n", type=int, help="number of teeth")
    comb_parser.add_argument("-o", "--output", default=None)

    rand_parser = subparsers.add_parser("random", help="generate random polygon")
    rand_parser.add_argument("n", type=int, help="number of vertices")
    rand_parser.add_argument("--seed", type=int, default=None)
    rand_parser.add_argument("--width", type=float, default=10.0)
    rand_parser.add_argument("--height", type=float, default=10.0)
    rand_parser.add_argument("-o", "--output", default=None)

    args = parser.parse_args()

    if args.command == "comb":
        poly = comb_polygon(args.n)
        filepath = args.output or f"data/comb_{args.n}.csv"
        save_polygon(poly, filepath)

    elif args.command == "random":
        poly = random_polygon(args.n, width=args.width, height=args.height, seed=args.seed)
        filepath = args.output or f"data/random_{args.n}.csv"
        save_polygon(poly, filepath)

    else:
        parser.print_help()