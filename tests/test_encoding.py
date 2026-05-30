from src.candidates import build_candidates
from src.visibility import compute_visibility
from src.encoding import coverage_clauses, sequential_counter

L_POLY = [(0, 2), (1, 2), (1, 1), (2, 1), (2, 0), (0, 0)]


def load_dimacs(filepath):
    """Load CNF from DIMACS file, returns (num_vars, clauses)."""
    clauses = []
    num_vars = 0
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line.startswith("c") or not line:
                continue
            if line.startswith("p cnf"):
                num_vars = int(line.split()[2])
            else:
                lits = list(map(int, line.split()))
                clauses.append(lits[:-1])
    return num_vars, clauses


def test_coverage_clauses():
    pts = build_candidates(L_POLY, L_POLY, max_rounds=1)
    V = compute_visibility(pts, L_POLY)
    clauses = coverage_clauses(V)
    print(f"Coverage clauses: {len(clauses)}")
    for i, c in enumerate(clauses):
        print(f"  p{i+1}: {c}")


def test_sequential_counter():
    pts = build_candidates(L_POLY, L_POLY, max_rounds=1)
    n = len(pts)
    clauses, last_var = sequential_counter(n, k=1, first_aux=n + 1)
    print(f"Sequential counter n={n}, k=1")
    print(f"  Last var : {last_var}  [expected: {2*n}]")
    print(f"  Clauses  : {len(clauses)}  [expected: {2 + 3*(n-1)}]")


def test_against_fixture():
    pts = build_candidates(L_POLY, L_POLY, max_rounds=1)
    V = compute_visibility(pts, L_POLY)
    n = len(pts)
    k = 1
    cov = coverage_clauses(V)
    cnt, num_vars = sequential_counter(n, k, first_aux=n + 1)
    all_clauses = cov + cnt

    ref_vars, ref_clauses = load_dimacs("tests/fixtures/l_polygon.cnf")
    print(f"Fixture check")
    print(f"  Vars match    : {'OK' if num_vars == ref_vars else 'FAILED'}")
    print(f"  Count match   : {'OK' if len(all_clauses) == len(ref_clauses) else 'FAILED'}")
    content_ok = sorted(sorted(c) for c in all_clauses) == sorted(sorted(c) for c in ref_clauses)
    print(f"  Content match : {'OK' if content_ok else 'FAILED'}")


if __name__ == "__main__":
    test_coverage_clauses()
    test_sequential_counter()
    test_against_fixture()