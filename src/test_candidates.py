from candidates import build_candidates

# L-Polygon
print("=== L-Polygon ===")
poly_l = [(0, 2), (1, 2), (1, 1), (2, 1), (2, 0), (0, 0)]
pts_l = build_candidates(poly_l, poly_l, max_rounds=3)
print(f"Original vertices: {len(poly_l)}")
print(f"Total candidates: {len(pts_l)}")  # 8
print("All candidates:")
for i, p in enumerate(pts_l):
    print(f"  {i}: ({p[0]:.4f}, {p[1]:.4f})")

# S-Polygon
print("\n=== S-Polygon ===")
poly_s = [(0, 1), (0, 3), (1, 3), (1, 2), (3, 2), (3, 0), (2, 0), (2, 1)]
pts_s = build_candidates(poly_s, poly_s, max_rounds=3)
print(f"Original vertices: {len(poly_s)}")
print(f"Total candidates: {len(pts_s)}")
print("All candidates:")
for i, p in enumerate(pts_s):
    print(f"  {i}: ({p[0]:.4f}, {p[1]:.4f})")
