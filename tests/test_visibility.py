from src.candidates import build_candidates
from src.visibility import compute_visibility

POLYGONS = {
    "L-Polygon": [(0, 2), (1, 2), (1, 1), (2, 1), (2, 0), (0, 0)],
    "S-Polygon": [(0, 1), (0, 3), (1, 3), (1, 2), (3, 2), (3, 0), (2, 0), (2, 1)],
}


def test_visibility(name, poly, max_rounds=3):
    pts = build_candidates(poly, poly, max_rounds=max_rounds)
    V = compute_visibility(pts, poly)
    n = len(pts)

    # print matrix
    print(f"Candidates: {n}")
    print("Visibility matrix (1=visible, 0=not):")
    print("    " + " ".join(f"{i:2}" for i in range(n)))
    for i in range(n):
        row = "  ".join("1" if V[i][j] else "0" for j in range(n))
        print(f"{i:2}:  {row}")

    # symmetry check
    sym_ok = all(V[i][j] == V[j][i] for i in range(n) for j in range(n))
    print(f"Symmetry check: {'OK' if sym_ok else 'FAILED'}")

    # diagonal check
    diag_ok = all(V[i][i] for i in range(n))
    print(f"Diagonal check: {'OK' if diag_ok else 'FAILED'}")

    # visible pairs
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n) if V[i][j]]
    print(f"Visible pairs : {len(pairs)}")
    for i, j in pairs:
        print(f"  {i:2} <-> {j:2}:  ({pts[i][0]:.1f},{pts[i][1]:.1f}) <-> ({pts[j][0]:.1f},{pts[j][1]:.1f})")
    print()


if __name__ == "__main__":
    for name, poly in POLYGONS.items():
        test_visibility(name, poly)
