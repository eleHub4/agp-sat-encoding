from src.candidates import build_candidates
from tests.polygons import POLYGONS

EXPECTED = {"l_polygon": 8, "s_polygon": 16}

def test_candidates(name, poly, max_rounds=3):
    pts = build_candidates(poly, poly, max_rounds=max_rounds)
    print(f"=== {name} ===")
    print(f"Vertices  : {len(poly)}")
    print(f"Candidates: {len(pts)}", end="")
    if name in EXPECTED:
        status = "OK" if len(pts) == EXPECTED[name] else f"EXPECTED {EXPECTED[name]}"
        print(f"  [{status}]", end="")
    print()
    for i, p in enumerate(pts):
        tag = " (vertex)" if i < len(poly) else " (new)"
        print(f"  {i:2}: ({p[0]:.4f}, {p[1]:.4f}){tag}")
    print()

if __name__ == "__main__":
    for name, (poly, _) in POLYGONS.items():
        test_candidates(name, poly)