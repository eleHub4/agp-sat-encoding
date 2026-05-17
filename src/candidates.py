from geometry import cross, sub, add, scale, points_equal, segment_in_polygon, point_in_polygon

EPS = 1e-6


def visible_pairs(candidates, poly):
    """All index pairs (i,j) with a visible connection."""
    pairs = []
    n = len(candidates)
    for i in range(n):
        for j in range(i + 1, n):
            if segment_in_polygon(candidates[i], candidates[j], poly):
                pairs.append((i, j))
    return pairs


def line_edge_intersection(pa, pb, ea, eb):
    """Intersection of line through pa->pb with segment ea->eb."""
    d = sub(pb, pa)
    e = sub(eb, ea)
    f = sub(ea, pa)
    denom = cross(d, e)
    if abs(denom) < EPS:
        return None  # parallel
    t = cross(f, e) / denom  # parameter on line (unconstrained)
    s = cross(f, d) / denom  # parameter on edge (must be in (0,1))
    if not (EPS < s < 1 - EPS):
        return None
    return add(pa, scale(d, t))


def build_candidates(vertices, poly, max_rounds=3):
    """
    Round 1: vertices + intersections of visibility lines with edges.
    Round 2+: repeat with all current candidates.
    """
    n_edges = len(poly)
    candidates = list(vertices)

    for r in range(max_rounds):
        new_pts = []
        for i, j in visible_pairs(candidates, poly):
            for k in range(n_edges):
                p = line_edge_intersection(candidates[i], candidates[j], poly[k], poly[(k + 1) % n_edges])
                if p is None:
                    continue
                if any(points_equal(p, q) for q in candidates + new_pts):
                    continue  # duplicate
                if point_in_polygon(p, poly):
                    new_pts.append(p)

        if not new_pts:
            print(f"Converged after {r + 1} round(s)")
            break
        candidates.extend(new_pts)
        print(f"Round {r + 1}: +{len(new_pts)} candidates, total {len(candidates)}")

    return candidates
