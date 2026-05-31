import argparse
import csv
import os
from src.candidates import build_candidates
from src.visibility import compute_visibility
from src.encoding import coverage_clauses, sequential_counter, write_dimacs


def load_polygon(filepath):
    with open(filepath) as f:
        reader = csv.reader(f)
        return [(float(row[0]), float(row[1])) for row in reader]


def main():
    parser = argparse.ArgumentParser(description="AGP SAT-Encoding")
    parser.add_argument("polygon", help="CSV file with polygon vertices")
    parser.add_argument("-k", type=int, default=1, help="maximum number of guards")
    parser.add_argument("-o", "--output", default=None, help="output file (default: output/<name>_k<k>.cnf)")
    parser.add_argument("--rounds", type=int, default=3, help="max rounds for candidate generation")
    args = parser.parse_args()

    poly = load_polygon(args.polygon)

    if args.output is None:
        name = os.path.splitext(os.path.basename(args.polygon))[0]
        os.makedirs("output", exist_ok=True)
        args.output = f"output/{name}_k{args.k}.cnf"

    pts = build_candidates(poly, poly, max_rounds=args.rounds)
    V = compute_visibility(pts, poly)
    n = len(pts)

    cov = coverage_clauses(V)
    cnt, num_vars = sequential_counter(n, args.k, first_aux=n + 1)
    all_clauses = cov + cnt

    comments = [
        f"AGP SAT-Encoding: {args.polygon}",
        f"candidates: {n}, k={args.k}",
    ]
    write_dimacs(all_clauses, num_vars, args.output, comments=comments)
    print(f"CNF written: {args.output}  ({num_vars} vars, {len(all_clauses)} clauses)")


if __name__ == "__main__":
    main()