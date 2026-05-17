import math

EPS = 1e-6


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def scale(v, t):
    return (v[0] * t, v[1] * t)


def midpoint(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def points_equal(a, b):
    return math.dist(a, b) < EPS


def point_on_segment(p, a, b):
    if abs(cross(sub(b, a), sub(p, a))) > EPS:
        return False
    # project onto longer axis for numerical stability
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    if abs(dx) > abs(dy):
        t = (p[0] - a[0]) / dx if abs(dx) > EPS else 0
    else:
        t = (p[1] - a[1]) / dy if abs(dy) > EPS else 0
    return -EPS <= t <= 1 + EPS


def point_in_polygon(p, poly):
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        a = poly[i]
        b = poly[(i + 1) % n]
        if point_on_segment(p, a, b):
            return True
        if (a[1] > y) != (b[1] > y):
            xcut = (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]
            if x < xcut:
                inside = not inside
    return inside


def proper_intersect(p, r, q, s):
    # returns (hit, t, u) -> only true if intersection is strictly interior
    denom = cross(r, s)
    if abs(denom) < EPS:
        return False, None, None
    diff = sub(q, p)
    t = cross(diff, s) / denom
    u = cross(diff, r) / denom
    if EPS < t < 1 - EPS and EPS < u < 1 - EPS:
        return True, t, u
    return False, None, None


def segment_in_polygon(a, b, poly):
    r = sub(b, a)
    n = len(poly)
    for i in range(n):
        p = poly[i]
        q = poly[(i + 1) % n]
        hit, _, _ = proper_intersect(a, r, p, sub(q, p))
        if hit:
            return False
    mid = midpoint(a, b)
    return point_in_polygon(mid, poly)
