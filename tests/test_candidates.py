from src.candidates import build_candidates

POLYGONS = {
    "L-Polygon": [(0, 2), (1, 2), (1, 1), (2, 1), (2, 0), (0, 0)],
    "S-Polygon": [(0, 1), (0, 3), (1, 3), (1, 2), (3, 2), (3, 0), (2, 0), (2, 1)],
}

EXPECTED = {
    "L-Polygon": 8,
    "S-Polygon": 16,
}


def test_candidates(name, poly, max_rounds=3):
    print(f"=== {name} ===")
    pts = build_candidates(poly, poly, max_rounds=max_rounds)
    print(f"Vertices  : {len(poly)}")
    print(f"Candidates: {len(pts)}", end="")
    if name in EXPECTED:
        status = "OK" if len(pts) == EXPECTED[name] else f"EXPECTED {EXPECTED[name]}"
        print(f"  [{status}]", end="")
    print()
    print("All candidates:")
    for i, p in enumerate(pts):
        tag = " (vertex)" if i < len(poly) else " (new)"
        print(f"  {i:2}: ({p[0]:.4f}, {p[1]:.4f}){tag}")
    print()
    return pts


if __name__ == "__main__":
    for name, poly in POLYGONS.items():
        test_candidates(name, poly)
